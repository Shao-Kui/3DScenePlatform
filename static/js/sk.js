const objectCache = {}; 
const gatheringObjCat = {}; 
let loadObjectToCache = async function(modelId){
    if(modelId in objectCache){
        return;
    }
    let mtlurl = `/mtl/${modelId}`;
    let meshurl = `/mesh/${modelId}`;
    var objLoader = new THREE.OBJLoader2();
    objLoader.loadMtl(mtlurl, null, function (materials) {
        Object.keys(materials).forEach(mtrname => {
            let mtr = materials[mtrname];
            let newmtr_lowopa = mtr.clone();
            newmtr_lowopa.transparent = true;
            newmtr_lowopa.opacity = 0.6;
            mtr.newmtr_lowopa = newmtr_lowopa;
            newmtr_lowopa.origin_mtr = mtr;
            mtr.origin_mtr = mtr;
        });
        objLoader.setModelName(modelId);
        objLoader.setMaterials(materials);
        objLoader.load(meshurl, function (event) {
            let instance = event.detail.loaderRootNode;
            instance.userData = {
                "type": 'object',
                "roomId": currentRoomId,
                "modelId": modelId,
                "name": modelId,
                "coarseSemantic": ""
            };
            // enable shadowing of instances; 
            instance.castShadow = true;
            instance.receiveShadow = true;
            instance.coarseAABB = new THREE.Box3().setFromObject(instance);
            traverseObjSetting(instance);
            if('geometry' in instance){
                instance.geometry.computeBoundingBox();
            }
            instance.children.forEach(child => {
                if(child.material.newmtr_lowopa !== undefined) child.material = child.material.newmtr_lowopa;
                if('geometry' in child){
                    child.geometry.computeBoundingBox();
                }
            });
            objectCache[modelId] = instance;
        }, null, null, null, false);
    });
};

let addObjectFromCache = function(modelId, transform={'translate': [0,0,0], 'rotate': [0,0,0], 'scale': [1.0,1.0,1.0]}){
    if(!modelId in objectCache) return;
    let objToInsert = {
        "modelId": modelId,
        "coarseSemantic": gatheringObjCat[modelId], 
        "translate": transform.translate,
        "scale": transform.scale,
        "roomId": currentRoomId,
        "rotate": transform.rotate,
        "orient": transform.rotate[1], 
        "key": THREE.Math.generateUUID(),
        "mageAddDerive": objectCache[modelId].userData.mageAddDerive
    };
    let object3d = objectCache[modelId].clone();
    object3d.name = undefined;
    object3d.scale.set(objToInsert.scale[0],objToInsert.scale[1],objToInsert.scale[2]);
    object3d.rotation.set(objToInsert.rotate[0],objToInsert.rotate[1],objToInsert.rotate[2]);
    object3d.position.set(objToInsert.translate[0],objToInsert.translate[1],objToInsert.translate[2]);
    object3d.userData = {
        "type": 'object',
        "key": objToInsert.key,
        "roomId": currentRoomId,
        "modelId": modelId,
        "coarseSemantic": gatheringObjCat[modelId]
    };
    object3d.children.forEach(child => {
        if(child.material.origin_mtr) child.material = child.material.origin_mtr;
    });
    manager.renderManager.scene_json.rooms[currentRoomId].objList.push(objToInsert);
    manager.renderManager.instanceKeyCache[objToInsert.key] = object3d;
    //manager.renderManager.refresh_instances();
    scene.add(object3d)
    renderer.render(scene, camera);
    return object3d; 
};

const door_mageAdd_set = []; 
const window_factor = 0.5; 
const _addDoor_mageAdd = (doorMeta) => {
    let worldBbox = doorMeta.bbox; 
    let _minIndex = tf.argMin([
        worldBbox.max[0] - worldBbox.min[0], 
        worldBbox.max[1] - worldBbox.min[1], 
        worldBbox.max[2] - worldBbox.min[2]
    ]).arraySync(); 
    let scale = [1,1,1]; scale[_minIndex] = 6; 
    if(doorMeta.coarseSemantic === 'Window' || doorMeta.coarseSemantic === 'window'){
        scale[1] *= (1.0 - window_factor); 
    }
    let geometry = new THREE.BoxGeometry( 
        (worldBbox.max[0] - worldBbox.min[0]) * scale[0], 
        (worldBbox.max[1] - worldBbox.min[1]) * scale[1], 
        (worldBbox.max[2] - worldBbox.min[2]) * scale[2]
    ); 
    // bounding box should be computed before transformations; 
    geometry.computeBoundingBox();
    let material;
    if(doorMeta.coarseSemantic === 'Door' || doorMeta.coarseSemantic === 'door')
        {material = new THREE.MeshBasicMaterial({color: 0x00ff00});}
    else if(doorMeta.coarseSemantic === 'Window' || doorMeta.coarseSemantic === 'window')
        {material = new THREE.MeshBasicMaterial({color: 0x424bf5});}
    else{material = new THREE.MeshBasicMaterial({color: 0xeeeeee});}
    material.transparent = true;
    material.opacity = 0.0
    let cube = new THREE.Mesh( geometry, material );
    if(doorMeta.coarseSemantic === 'Window' || doorMeta.coarseSemantic === 'window'){
        cube.position.set(
            (worldBbox.max[0] + worldBbox.min[0]) / 2,
            (window_factor/2) * (worldBbox.max[1] - worldBbox.min[1]) + (worldBbox.max[1] + worldBbox.min[1]) / 2,
            (worldBbox.max[2] + worldBbox.min[2]) / 2
        ); 
    }else{
        cube.position.set(
            (worldBbox.max[0] + worldBbox.min[0]) / 2,
            (worldBbox.max[1] + worldBbox.min[1]) / 2,
            (worldBbox.max[2] + worldBbox.min[2]) / 2
        ); 
    }
    cube.name = doorMeta.modelId; 
    door_mageAdd_set.push(cube);
    scene.add(cube); 
}
const _refresh_mageAdd_wall = (json) => {
    door_mageAdd_set.forEach(o3d => {
        scene.remove(o3d); 
    }); 
    door_mageAdd_set.length = 0; 
    json.rooms.forEach(room => {
        room.objList.forEach(meta => {
            if(meta === undefined || meta === null) return; 
            if(!'coarseSemantic' in meta) return; 
            if(meta.coarseSemantic === 'Door' || meta.coarseSemantic === 'door'){
                _addDoor_mageAdd(meta); 
            }else if(meta.coarseSemantic === 'Window' || meta.coarseSemantic === 'widow'){
                _addDoor_mageAdd(meta);
            }
        })
    })
}
const showHide_door_mageAdd_set = function(){
    door_mageAdd_set.forEach(wd => {
        if(wd.material.opacity === 0.0) wd.material.opacity = 0.5;
        else wd.material.opacity = 0.0;
    })
}

// the following function is modified from: https://discourse.threejs.org/t/collisions-two-objects/4125/3
function detectCollisionCubes(object1, object2){
    if(object1.geometry === undefined || object2.geometry === undefined) return false;
    // object1.geometry.computeBoundingBox(); //not needed if its already calculated; 
    // object2.geometry.computeBoundingBox();
    // object1.updateMatrixWorld();
    // object2.updateMatrixWorld();
    let box1 = object1.geometry.boundingBox.clone();
    box1.applyMatrix4(object1.matrixWorld);
    let box2 = object2.geometry.boundingBox.clone();
    box2.applyMatrix4(object2.matrixWorld);
    box1.expandByScalar(-0.06);
    box2.expandByScalar(-0.06);
    return box1.intersectsBox(box2);
}

function detectCollisionGroups(group1, group2){
    if(group1 === undefined || group2 === undefined) return;
    let objlist1, objlist2;
    if('children' in group1){
        objlist1 = group1.children.concat([group1]);
    }else{
        objlist1 = [group1];
    }
    if('children' in group2){
        objlist2 = group2.children.concat([group2]);
    }else{
        objlist2 = [group2];
    }
    group1.updateMatrixWorld();
    group2.updateMatrixWorld();
    for(let i = 0; i < objlist1.length; i++){
        for(let j = 0; j < objlist2.length; j++){
            if(detectCollisionCubes(objlist1[i], objlist2[j])){
                return true;
            }
        }
    }
    return false;
}

const wallRayCaster = new THREE.Raycaster();
const detectCollisionWall = function(wallMeta, object){
    object.updateMatrixWorld();
    let box = object.coarseAABB.clone();
    box.applyMatrix4(object.matrixWorld);
    let halfHeight = (box.min.y + box.max.y) / 2; 
    for(let j = 0; j < wallMeta.length; j++){
        let start = new THREE.Vector3(wallMeta[j][0], halfHeight, wallMeta[j][1]);
        let end = new THREE.Vector3(
            wallMeta[(j+1)%(wallMeta.length)][0], 
            halfHeight, 
            wallMeta[(j+1)%(wallMeta.length)][1]
        );
        let direction = end.sub(start); 
        direction.normalize();
        wallRayCaster.set(start, direction); 
        var intersects = wallRayCaster.intersectObjects([object], true); 
        if(intersects.length > 0) return true; 
    }
    return false;
}

const gameLoop = function () {
    stats.begin();
    render_update();
    orth_view_port_update();
    keyboard_update();
    camera.updateMatrixWorld();
    manager.renderManager.orthcamera.updateMatrixWorld();
    raycaster.setFromCamera(mouse, camera);
    renderer.render(scene, camera);
    manager.renderManager.orthrenderer.render(scene, manager.renderManager.orthcamera);
    stats.end();
    requestAnimationFrame(gameLoop);
};

var screen_to_ground = function (mx, my, ground_y = 0) {
    var vec = new THREE.Vector3();
    var pos = new THREE.Vector3();
    vec.set(mx, my, 0.5);
    vec.unproject(camera);
    vec.sub(camera.position).normalize();
    var distance = (ground_y - camera.position.y) / vec.y;
    pos.copy(camera.position).add(vec.multiplyScalar(distance));
    return pos;
};

var radial_move_method = function (mx, my) {
    //from https://stackoverflow.com/questions/13055214/mouse-canvas-x-y-to-three-js-world-x-y-z
    var vec = new THREE.Vector3();
    var pos = new THREE.Vector3();
    vec.set(mx, my, 0.5);
    vec.unproject(camera);
    vec.sub(camera.position).normalize();
    var distance = (INTERSECT_OBJ.position.y - camera.position.y) / vec.y;
    pos.copy(camera.position).add(vec.multiplyScalar(distance));
    return pos;
};

var find_object_json = function (obj) {
    var key = obj.userData.key;
    var room = manager.renderManager.scene_json.rooms[obj.userData.roomId];
    for (var i = 0; i < room.objList.length; i++) {
        if (!room.objList[i]) {
            continue;
        }
        if (room.objList[i].key === key) {
            return i;
        }
    }
    return null;
};

var synchronize_json_object = function (object) {
    var i = find_object_json(object);
    var inst = manager.renderManager.scene_json.rooms[object.userData.roomId].objList[i];
    inst.scale[0] = object.scale.x;
    inst.scale[1] = object.scale.y;
    inst.scale[2] = object.scale.z;
    inst.translate[0] = object.position.x;
    inst.translate[1] = object.position.y;
    inst.translate[2] = object.position.z;
    inst.rotate[0] = object.rotation.x;
    inst.rotate[1] = object.rotation.y;
    inst.rotate[2] = object.rotation.z;
    // the core code for calculating orientations of objects; 
    inst.orient = Math.atan2(Math.sin(object.rotation.y), Math.cos(object.rotation.x) * Math.cos(object.rotation.y));
    if(AUXILIARY_MODE){
        auxiliaryMode();
    }
};

var synchronize_roomId = function (object) {
    if (currentRoomId === object.userData.roomId || currentRoomId === undefined) {
        return;
    }
    var i = find_object_json(object);
    var obj_json = manager.renderManager.scene_json.rooms[object.userData.roomId].objList[i];
    obj_json.roomId = currentRoomId;
    manager.renderManager.scene_json.rooms[currentRoomId].objList.push(obj_json);
    delete manager.renderManager.scene_json.rooms[object.userData.roomId].objList[i];
    manager.renderManager.scene_json.rooms[object.userData.roomId].objList = 
    manager.renderManager.scene_json.rooms[object.userData.roomId].objList.filter( item => item !== null && item !== undefined )
    object.userData.roomId = currentRoomId;
}

var updateMousePosition = function () {
    mouse.x = ((event.clientX - $(scenecanvas).offset().left) / scenecanvas.clientWidth) * 2 - 1;
    mouse.y = -((event.clientY - $(scenecanvas).offset().top) / scenecanvas.clientHeight) * 2 + 1;
}

var clickCatalogItem = function (e) {
    scene.remove(scene.getObjectByName(INSERT_NAME));
    // avoid confictions between ordinary insertions and the auxiliary mode; 
    if(!manager.renderManager.scene_json || AUXILIARY_MODE) return;    
    On_ADD = true;
    scenecanvas.style.cursor = "crosshair";
    loadObjectToCache($(e.target).attr("modelId")); 
    INSERT_OBJ = {
        "modelId": $(e.target).attr("objectName"),
        "coarseSemantic": $(e.target).attr("coarseSemantic"), 
        "translate": [0.0, 0.0, 0.0],"scale": [1.0, 1.0, 1.0],"rotate": [0.0, 0.0, 0.0]
    };
}

var findGroundTranslation = function () {
    if (currentRoomId === undefined) {
        return;
    }
    var vec = new THREE.Vector3();
    var pos = new THREE.Vector3();
    vec.set(mouse.x, mouse.y, 0.5);
    vec.unproject(camera);
    vec.sub(camera.position).normalize();
    var distance =
        (manager.renderManager.scene_json.rooms[currentRoomId].bbox.min[1]
            - camera.position.y) / vec.y;
    pos.copy(camera.position).add(vec.multiplyScalar(distance));
    return pos;
}

var onClickObj = function (event) {
    scenecanvas.style.cursor = "auto";
    // do raycasting, judge whether or not users choose a new object; 
    camera.updateMatrixWorld();
    raycaster.setFromCamera(mouse, camera);
    var intersects = raycaster.intersectObjects(manager.renderManager.cwfCache, true);
    if (manager.renderManager.cwfCache.length > 0 && intersects.length > 0) {
        currentRoomId = intersects[0].object.parent.userData.roomId;
        console.log(`
        Current room ID: ${currentRoomId} of 
        room type ${manager.renderManager.scene_json.rooms[currentRoomId].roomTypes}`);
        $('#tab_roomid').text(currentRoomId);
        $('#tab_roomtype').text(manager.renderManager.scene_json.rooms[currentRoomId].roomTypes);        
    } else {
        currentRoomId = undefined;
    }
    if (On_ADD) {
        On_ADD = false;
        if(scene.getObjectByName(INSERT_NAME)){
            let obj = scene.getObjectByName(INSERT_NAME);
            addObjectFromCache(
                modelId=INSERT_OBJ.modelId,
                transform={
                    'translate': [obj.position.x, obj.position.y, obj.position.z], 
                    'rotate': [0,0,0],
                    'scale': [1,1,1]
                }
            );
            scene.remove(scene.getObjectByName(INSERT_NAME)); 
            return; 
        }
    }
    if (On_MOVE) {
        On_MOVE = false;
        synchronize_json_object(INTERSECT_OBJ);
        synchronize_roomId(INTERSECT_OBJ);
        return;
    }
    if (On_LIFT) {
        On_LIFT = false;
        synchronize_json_object(INTERSECT_OBJ);
        return;
    }
    if (On_SCALE) {
        On_SCALE = false;
        synchronize_json_object(INTERSECT_OBJ);
        return;
    }
    if (On_ROTATE) {
        On_ROTATE = false;
        synchronize_json_object(INTERSECT_OBJ);
        return;

    }

    if(scene.getObjectByName(AUXILIARY_NAME)){
        let auxiliaryObj = scene.getObjectByName(AUXILIARY_NAME);
        let awo = manager.renderManager.scene_json.rooms[currentRoomId].auxiliaryWallObj;
        if(!auxiliaryObj || !awo) return;
        let ao = scene.getObjectByName(AUXILIARY_NAME)
        if(ao.userData.mageAddDerive !== "" && ao.userData.mageAddDerive){
            mad = ao.userData.mageAddDerive.split(' '); 
            if(mad[0] === 'wall'){
                if(mad[1] === 'empty') {awo.emptyChoice = 'null';}
                else{awo.mapping[mad[1]] = 'null';}
            }
        }
        addObjectFromCache(
            modelId=ao.userData.modelId,
            transform={
                'translate': [auxiliaryObj.position.x, auxiliaryObj.position.y, auxiliaryObj.position.z], 
                'rotate': [auxiliaryObj.rotation.x, auxiliaryObj.rotation.y, auxiliaryObj.rotation.z],
                'scale': [auxiliaryObj.scale.x, auxiliaryObj.scale.y, auxiliaryObj.scale.z]
            }
        );
        auxiliaryMode();
        return; 
    }

    // intersect objects; 
    var instanceKeyCache = manager.renderManager.instanceKeyCache;
    instanceKeyCache = Object.values(instanceKeyCache);
    intersects = raycaster.intersectObjects(instanceKeyCache, true);
    if (instanceKeyCache.length > 0 && intersects.length > 0) {
        INTERSECT_OBJ = intersects[0].object.parent; //currentRoomId = INTERSECT_OBJ.userData.roomId;
        console.log(INTERSECT_OBJ);
        $('#tab_modelid').text(INTERSECT_OBJ.userData.modelId);
        $('#tab_category').text(INTERSECT_OBJ.userData.coarseSemantic);   
        menu.style.left = (event.clientX - 63) + "px";
        menu.style.top = (event.clientY - 63) + "px";
        if (!isToggle) {
            radial.toggle();
            isToggle = !isToggle;
        }
        datguiObjectFolder(INTERSECT_OBJ);
        return;
    }else{
        // synchronize data to scene json; 
        datguiObjectFolderRemove(INTERSECT_OBJ); 
        console.log("object not intersected! ");
        $('#tab_modelid').text(" ");
        $('#tab_category').text(" ");  
        INTERSECT_OBJ = undefined; //currentRoomId = undefined;
        if (isToggle) {
            radial.toggle();
            isToggle = !isToggle;
        }
    }

    if (latent_space_mode == true && INTERSECT_OBJ) {
        manager.renderManager.add_latent_obj();
    }
    if (latent_space_mode == true) {
        manager.renderManager.refresh_latent();
    }

    if (Auto_Rec_Mode && manager.renderManager.scene_json && currentRoomId != undefined) {
        palette_recommendation();
    }
};

function onDocumentMouseMove(event) {
    event.preventDefault();
    if(On_ADD && INSERT_OBJ.modelId in objectCache){
        scene.remove(scene.getObjectByName(INSERT_NAME)); 
        let intersectObjList = Object.values(manager.renderManager.instanceKeyCache)
        .concat(Object.values(manager.renderManager.wfCache));
        intersects = raycaster.intersectObjects(intersectObjList, true);
        if(intersectObjList.length > 0 && intersects.length > 0){
            let ip = intersects[0].point
            objectCache[INSERT_OBJ.modelId].name = INSERT_NAME;
            objectCache[INSERT_OBJ.modelId].position.set(ip.x, ip.y, ip.z);
            objectCache[INSERT_OBJ.modelId].rotation.set(0, 0, 0, 'XYZ');
            objectCache[INSERT_OBJ.modelId].scale.set(1, 1, 1);
            scene.add(objectCache[INSERT_OBJ.modelId])
        }else{
            scene.remove(scene.getObjectByName(INSERT_NAME)); 
        }
    }
    if (On_ROTATE && INTERSECT_OBJ != null) {
        var rtt_pre = new THREE.Vector2();
        var rtt_nxt = new THREE.Vector2();
        rtt_pre.set(mouse.x, mouse.y);
        updateMousePosition();
        rtt_nxt.set(mouse.x, mouse.y);
        rtt_pre.sub(mouse.rotateBase);
        rtt_nxt.sub(mouse.rotateBase);
        INTERSECT_OBJ.rotateY(rtt_nxt.angle() - rtt_pre.angle());
    }
    if (On_MOVE && INTERSECT_OBJ != null) {
        var last_pos = radial_move_method(mouse.x, mouse.y);
        updateMousePosition();
        var pos = radial_move_method(mouse.x, mouse.y);
        pos.sub(last_pos);
        INTERSECT_OBJ.position.set(
            INTERSECT_OBJ.position.x + pos.x,
            INTERSECT_OBJ.position.y + pos.y,
            INTERSECT_OBJ.position.z + pos.z);
    }
    if (On_LIFT && INTERSECT_OBJ != null) {
        var last_y = mouse.y;
        updateMousePosition();
        var this_y = mouse.y;
        INTERSECT_OBJ.position.set(
            INTERSECT_OBJ.position.x,
            INTERSECT_OBJ.position.y + 2 * (this_y - last_y),
            INTERSECT_OBJ.position.z);
    }
    if (On_SCALE && INTERSECT_OBJ != null){
        var last_x = mouse.x;
        updateMousePosition();
        var this_x = mouse.x;
        s = 0.3;
        INTERSECT_OBJ.scale.set(
            INTERSECT_OBJ.scale.x + s * (this_x - last_x),
            INTERSECT_OBJ.scale.y + s * (this_x - last_x),
            INTERSECT_OBJ.scale.z + s * (this_x - last_x));
    }
    if(AUXILIARY_MODE && auxiliaryPrior !== undefined){
        auxiliaryMove();
    }
    updateMousePosition();
};

var onWindowResize = function(){
    $('#scenecanvas').width('100%'); 
    $('#scenecanvas').height('100%'); 
    camera.aspect = scenecanvas.clientWidth / scenecanvas.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(scenecanvas.clientWidth, scenecanvas.clientHeight); 
}

var saveFile = function (strData, filename) {
    var link = document.createElement('a');
    if (typeof link.download === 'string') {
        document.body.appendChild(link); //Firefox requires the link to be in the body
        link.download = filename;
        link.href = strData;
        link.click();
        document.body.removeChild(link); //remove the link when done
    } else {
        location.replace(uri);
    }
}

const render_function = function(){
    var imgData;
    try {
        var strMime = "image/jpeg";
        imgData = renderer.domElement.toDataURL(strMime);
        saveFile(imgData.replace(strMime, "image/octet-stream"), 
        `${manager.renderManager.scene_json.origin}-${manager.renderManager.scene_json.id}.jpg`);
    } catch (e) {
        console.log(e);
        return;
    }
}

const removeIntersectObject = function(){
    datguiObjectFolderRemove(INTERSECT_OBJ); 
    let roomId = INTERSECT_OBJ.userData.roomId;
    delete manager.renderManager.scene_json.rooms[roomId].objList[find_object_json(INTERSECT_OBJ)];
    delete manager.renderManager.instanceKeyCache[INTERSECT_OBJ.userData.key];
    scene.remove(INTERSECT_OBJ); 
    if(AUXILIARY_MODE){
        auxiliaryMode();
    }
}

const onAddOff = function(){
    scenecanvas.style.cursor = "auto";
    scene.remove(scene.getObjectByName(INSERT_NAME)); 
    On_ADD = false; 
}; 

const onRightClickObj = function(event){
    event.preventDefault();
    // note that we only swap instances that are NOT placed yet; 
    if(AUXILIARY_MODE){
        auxiliaryRightClick();
        return; 
    }
    if(On_ADD){
        onAddOff();
        return; 
    }
}

const onWheel = function(event){
    
}

const encodePerspectiveCamera = function(sceneJson){
    sceneJson.PerspectiveCamera = {}; 
    sceneJson.PerspectiveCamera.fov = camera.fov; 
    sceneJson.PerspectiveCamera.focalLength = camera.filmGauge; 
    sceneJson.PerspectiveCamera.origin = [camera.position.x, camera.position.y, camera.position.z];
    sceneJson.PerspectiveCamera.rotate = [camera.rotation.x, camera.rotation.y, camera.rotation.z];
    sceneJson.PerspectiveCamera.target = [orbitControls.target.x, orbitControls.target.y, orbitControls.target.z];
    let up = new THREE.Vector3()
    up.copy(camera.up)
    up.applyQuaternion(camera.quaternion)
    sceneJson.PerspectiveCamera.up = [up.x, up.y, up.z];
    sceneJson.canvas = {};
    sceneJson.canvas.width = scenecanvas.width;
    sceneJson.canvas.height = scenecanvas.height;
}

const datguiFolders = {} // (TBD) a dat.gui folder list for multiple objects; 
const datguiObjectFolder = function(objmesh){
    // activating dat.gui:
    if(datgui_intersectfolder){
        datgui.removeFolder(datgui_intersectfolder); 
        datgui_intersectfolder = undefined;
    } 
    datgui_intersectfolder = datgui.addFolder(objmesh.userData.modelId);
    datgui_intersectfolder.open();
    let ctrlScaleX = datgui_intersectfolder.add(objmesh.scale, 'x', 0.05, 3.0); 
    ctrlScaleX.domElement.parentElement.getElementsByClassName('property-name')[0].textContent = 'Scale-X';
    let ctrlScaleY = datgui_intersectfolder.add(objmesh.scale, 'y', 0.05, 3.0); 
    ctrlScaleY.domElement.parentElement.getElementsByClassName('property-name')[0].textContent = 'Scale-Y';
    let ctrlScaleZ = datgui_intersectfolder.add(objmesh.scale, 'z', 0.05, 3.0); 
    ctrlScaleZ.domElement.parentElement.getElementsByClassName('property-name')[0].textContent = 'Scale-Z';
    
    let ctrlOrient = datgui_intersectfolder.add(objmesh.rotation, 'y', -3.15, 3.15, 0.01); 
    ctrlOrient.domElement.parentElement.getElementsByClassName('property-name')[0].textContent = 'Orient';

    let rbb = manager.renderManager.scene_json.rooms[objmesh.userData.roomId].bbox; 
    let ctrlPosX = datgui_intersectfolder.add(objmesh.position, 'x', 
    rbb.min[0], rbb.max[0]); 
    ctrlPosX.domElement.parentElement.getElementsByClassName('property-name')[0].textContent = 'Pos-X';
    let ctrlPosY = datgui_intersectfolder.add(objmesh.position, 'y', 
    rbb.min[1], rbb.max[1]); 
    ctrlPosY.domElement.parentElement.getElementsByClassName('property-name')[0].textContent = 'Pos-Y'
    let ctrlPosZ = datgui_intersectfolder.add(objmesh.position, 'z', 
    rbb.min[2], rbb.max[2]); 
    ctrlPosZ.domElement.parentElement.getElementsByClassName('property-name')[0].textContent = 'Pos-Z'
};

const datguiObjectFolderRemove = function(objmesh){
    if(datgui_intersectfolder){
        datgui.removeFolder(datgui_intersectfolder); 
        datgui_intersectfolder = undefined; 
        synchronize_json_object(objmesh);
    }
}

let fpsCountMode = false;
let fpsAccumulate = 0;
let fpsInterval = 0;
let fpsCountMin = Infinity;
let fpsCountMax = 0;
const fpsCount = function(){
    if(fpsCountMode){
        fpsCountMode = !fpsCountMode;
        $('#tab_FPSavg').text((fpsAccumulate / fpsInterval).toFixed(2));
        $('#tab_minmax').text(`${fpsCountMin.toFixed(2)}-${fpsCountMax.toFixed(2)}`);  
        fpsAccumulate = 0
        fpsInterval = 0;
        fpsCountMin = Infinity;
        fpsCountMax = 0;
    }else{
        fpsCountMode = !fpsCountMode;
    }
}

var temp;
var setting_up = function () {
    // clear_panel();  // clear panel first before use individual functions.
    // setUpCanvasDrawing();
    render_initialization();
    orth_initialization();
    searchPanelInitialization();
    radial_initialization();

    // adding the `stats` panel for monitoring FPS; 
    stats = new Stats();
    stats.showPanel(0); // 0: fps, 1: ms, 2: mb, 3+: custom
    stats.dom.style.top = '5%'
    stats.dom.style.left = '25%'
    document.getElementById('scene').appendChild(stats.dom);

    // adding the `dat.gui` panel for modifying objects; 
    datgui = new dat.GUI(); // this initialization only conducts once; 
    datgui.domElement.style.marginRight = "0px"
    datgui.domElement.parentElement.style.top = "5%"; 
    datgui.domElement.parentElement.style.right = "0%"; 
    
    $(".btn").mousedown(function(e){e.preventDefault();})
    $("#sklayout").click(auto_layout);
    $("#layout2_button").click(mageAddSample);
    $("#clear_button").click(() => {
        if(currentRoomId === undefined) return;
        let objlist = manager.renderManager.scene_json.rooms[currentRoomId].objList; 
        for(let i = 0; i < objlist.length; i++){
            if(objlist[i] === undefined || objlist[i] === null) continue;
            if(['Window', 'window', 'door', 'Door'].includes(objlist[i].coarseSemantic)) continue; 
            scene.remove(manager.renderManager.instanceKeyCache[objlist[i].key]); 
            delete manager.renderManager.instanceKeyCache[objlist[i].key];
            delete objlist[i];
        }
        manager.renderManager.scene_json.rooms[currentRoomId].objList = objlist.filter(o => o!==undefined&&o!==null); 
    });
    $("#clearALL_button").click(() => {
        manager.renderManager.scene_json.rooms.forEach(room => {
            let objlist = room.objList; 
            for(let i = 0; i < objlist.length; i++){
                if(objlist[i] === undefined || objlist[i] === null) continue;
                if(['Window', 'window', 'door', 'Door'].includes(objlist[i].coarseSemantic)) continue; 
                scene.remove(manager.renderManager.instanceKeyCache[objlist[i].key]); 
                delete manager.renderManager.instanceKeyCache[objlist[i].key];
                delete objlist[i];
            }
            room.objList = objlist.filter(o => o!==undefined&&o!==null); 
        });
    });
    $("#windoor_button").click(showHide_door_mageAdd_set);
    if(auxiliary_control) $("#auxiliary_button").click(auxiliary_control);
    $("#download_button").click(function(){
        let json_to_dl = JSON.parse(JSON.stringify(manager.renderManager.scene_json));
        // delete unnecessary keys; 
        json_to_dl.rooms.forEach(function(room){
            room.objList = room.objList.filter( item => item !== null && item !== undefined )
            room.objList.forEach(function(inst){
                if(inst === null || inst === undefined){
                    return
                }
                delete inst.key;
            })
        })
        encodePerspectiveCamera(json_to_dl); 
        var dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(json_to_dl));
        var dlAnchorElem = document.getElementById('downloadAnchorElem');
        dlAnchorElem.setAttribute("href",     dataStr     );
        dlAnchorElem.setAttribute("download", `${json_to_dl.origin}-l${json_to_dl.id}-dl.json`);
        dlAnchorElem.click();
    });
    $("#screenshot").click(render_function);
    $("#axis_button").click(function(){
        let theaxis = scene.getObjectByName('axeshelper');
        if(theaxis === undefined){
            let axis = new THREE.AxesHelper(1000);
            axis.name = 'axeshelper'; 
            scene.add(axis);
        } 
        else{
            scene.remove(theaxis);
        }
    })

    scenecanvas.addEventListener('mousemove', onDocumentMouseMove, false);
    scenecanvas.addEventListener('mousedown', () => {
        document.getElementById("searchinput").blur();
        document.getElementById("utils_button").blur();
    });
    window.addEventListener('resize', onWindowResize, false);
    // scenecanvas.addEventListener('click', onClickObj);
    scenecanvas.addEventListener('wheel', onWheel);
    scenecanvas.addEventListener('contextmenu', onRightClickObj);
    document.addEventListener('keydown', onKeyDown, false);
    document.addEventListener('keyup', onKeyUp, false);
    orthcanvas.addEventListener('mousedown', orth_mousedown);
    orthcanvas.addEventListener('mouseup', orth_mouseup);
    orthcanvas.addEventListener('mousemove', orth_mousemove);
    orthcanvas.addEventListener('click', orth_mouseclick);

    var rapidSearches = document.getElementsByClassName("rapidSearch");
    const rapidSFunc = function() {
        document.getElementById('searchinput').value = this.textContent;
        $('#searchbtn').click();
    };
    for (let i = 0; i < rapidSearches.length; i++) {
        rapidSearches[i].addEventListener('click', rapidSFunc, false);
    }

    gameLoop();
};
