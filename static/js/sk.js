var objectCache = {}
var textureOpacityMapping = {}
let loadObjectToCache = function(modelId){
    if(modelId in objectCache){
        return;
    }
    let mtlurl = `/mtl/${modelId}`;
    let meshurl = `/mesh/${modelId}`;
    var objLoader = new THREE.OBJLoader2();
    objLoader.loadMtl(mtlurl, null, function (materials) {
        console.log('materials! ', materials)
        Object.keys(materials).forEach(mtrname => {
            let mtr = materials[mtrname];
            let newmtr_lowopa = mtr.clone();
            console.log(newmtr_lowopa);
            newmtr_lowopa.transparent = true;
            newmtr_lowopa.opacity = 0.6;
            mtr.newmtr_lowopa = newmtr_lowopa;
            newmtr_lowopa.origin_mtr = mtr;
        })
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
                child.material = child.material.newmtr_lowopa;
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
        "coarseSemantic": "_fromCache", 
        "translate": transform.translate,
        "scale": transform.scale,
        "roomId": currentRoomId,
        "rotate": transform.rotate,
        "orient": transform.rotate[1], 
        "key": THREE.Math.generateUUID()
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
        "coarseSemantic": ""
    };
    object3d.children.forEach(child => {
        if(child.material.origin_mtr) child.material = child.material.origin_mtr;
    });
    manager.renderManager.scene_json.rooms[currentRoomId].objList.push(objToInsert);
    manager.renderManager.instanceKeyCache[objToInsert.key] = object3d;
    //manager.renderManager.refresh_instances();
    scene.add(object3d)
    renderer.render(scene, camera);
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
        {material = new THREE.MeshBasicMaterial({color: 0x87ceeb});}
    else{material = new THREE.MeshBasicMaterial({color: 0xeeeeee});}
    material.transparent = true;
    material.opacity = 0.5
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

// the following function is modified from: https://discourse.threejs.org/t/collisions-two-objects/4125/3
function detectCollisionCubes(object1, object2){
    if(object1.geometry === undefined || object2.geometry === undefined) return false;
    // object1.geometry.computeBoundingBox(); //not needed if its already calculated
    // object2.geometry.computeBoundingBox();
    // object1.updateMatrixWorld();
    // object2.updateMatrixWorld();
    let box1 = object1.geometry.boundingBox.clone();
    box1.applyMatrix4(object1.matrixWorld);
    let box2 = object2.geometry.boundingBox.clone();
    box2.applyMatrix4(object2.matrixWorld);
    box1.expandByScalar(-0.04);
    box2.expandByScalar(-0.04);
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

var gameLoop = function () {
    render_update();
    orth_view_port_update();
    keyboard_update();

    camera.updateMatrixWorld();
    manager.renderManager.orthcamera.updateMatrixWorld();
    raycaster.setFromCamera(mouse, camera);
    renderer.render(scene, camera);
    manager.renderManager.orthrenderer.render(scene, manager.renderManager.orthcamera);

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
    if (!manager.renderManager.scene_json) {
        return;
    }
    //check if auto insert mode is on
    // if (Auto_Insert_Mode) {
    //     mage_auto_insert(e);
    //     return;
    // }
    On_ADD = true;
    scenecanvas.style.cursor = "crosshair";
    INSERT_OBJ = {
        "modelId": $(e.target).attr("objectName"),
        "coarseSemantic": $(e.target).attr("coarseSemantic"), 
        "translate": [
            0.0,
            0.0,
            0.0
        ],
        "scale": [
            1.0,
            1.0,
            1.0
        ],
        "rotate": [
            0.0,
            0.0,
            0.0
        ]
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

var addCatalogItem = function () {
    let vec = new THREE.Vector3();
    let pos = new THREE.Vector3();
    vec.set(mouse.x, mouse.y, 0.5);
    vec.unproject(camera);
    vec.sub(camera.position).normalize();
    let distance =
        (manager.renderManager.scene_json.rooms[currentRoomId].bbox.min[1]
            - camera.position.y) / vec.y;
    pos.copy(camera.position).add(vec.multiplyScalar(distance));
    INSERT_OBJ.translate[0] = pos.x;
    INSERT_OBJ.translate[1] = pos.y;
    INSERT_OBJ.translate[2] = pos.z;
    INSERT_OBJ.roomId = currentRoomId;
    manager.renderManager.scene_json.rooms[currentRoomId].objList.push(INSERT_OBJ);
    manager.renderManager.refresh_instances();
}

var onClickObj = function (event) {
    scenecanvas.style.cursor = "auto";
    // do raycasting, judge whether or not users choose a new object; 
    camera.updateMatrixWorld();
    raycaster.setFromCamera(mouse, camera);
    var intersects = raycaster.intersectObjects(manager.renderManager.cwfCache, true);
    if (manager.renderManager.cwfCache.length > 0 && intersects.length > 0) {
        currentRoomId = intersects[0].object.parent.userData.roomId;
        console.log(`Current room ID: ${currentRoomId} of room type ${manager.renderManager.scene_json.rooms[currentRoomId].roomTypes}`);
    } else {
        currentRoomId = undefined;
    }
    if (On_ADD) {
        On_ADD = false;
        if (currentRoomId != undefined) {
            addCatalogItem();
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
    if (On_Magic_ADD) {
        On_Magic_ADD = false;
        if (!manager.renderManager.scene_json) {
            return;
        }
        if (currentRoomId != undefined) {
            mage_add_object();
            return;
        }
    }
    var instanceKeyCache = manager.renderManager.instanceKeyCache;
    instanceKeyCache = Object.values(instanceKeyCache);
    intersects = raycaster.intersectObjects(instanceKeyCache, true);
    if (instanceKeyCache.length > 0 && intersects.length > 0) {
        console.log(intersects);
        INTERSECT_OBJ = intersects[0].object.parent; //currentRoomId = INTERSECT_OBJ.userData.roomId;
        console.log(INTERSECT_OBJ);
        console.log(INTERSECT_OBJ.userData);
        menu.style.left = (event.clientX - 63) + "px";
        menu.style.top = (event.clientY - 63) + "px";
        if (!isToggle) {
            radial.toggle();
            isToggle = !isToggle;
        }
        return;
    }else{
        console.log("object not intersected! ");
        INTERSECT_OBJ = undefined; //currentRoomId = undefined;
        if (isToggle) {
            radial.toggle();
            isToggle = !isToggle;
        }
    }

    if(AUXILIARY_MODE){
        let auxiliaryObj = scene.getObjectByName(AUXILIARY_NAME);
        if(!auxiliaryObj) return;
        addObjectFromCache(
            scene.getObjectByName(AUXILIARY_NAME).userData.modelId,
            {
                'translate': [auxiliaryObj.position.x, auxiliaryObj.position.y, auxiliaryObj.position.z], 
                'rotate': [auxiliaryObj.rotation.x, auxiliaryObj.rotation.y, auxiliaryObj.rotation.z],
                'scale': [auxiliaryObj.scale.x, auxiliaryObj.scale.y, auxiliaryObj.scale.z]
            }
        );
        auxiliaryMode();
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

function realTimeObjCache(objname, x, y, z, theta, scale=[1.0, 1.0, 1.0]){
    if(objectCache[objname] === undefined){
        return;
    }
    objectCache[objname].name = AUXILIARY_NAME;
    objectCache[objname].position.set(x, y, z);
    objectCache[objname].rotation.set(0, theta, 0, 'XYZ');
    objectCache[objname].scale.set(scale[0], scale[1], scale[2]);
    // detecting collisions between the pending object and other objects of the same room: 
    let olist = manager.renderManager.scene_json.rooms[currentRoomId].objList;
    for(let i = 0; i < olist.length; i++){
        let obj = olist[i];
        if(obj === undefined || obj === null) continue;
        if(!'key' in obj) continue;
        let objmesh = manager.renderManager.instanceKeyCache[obj.key];
        if(detectCollisionGroups(objectCache[objname], objmesh)){
            scene.remove(scene.getObjectByName(AUXILIARY_NAME));
            return;
        }
    }
    // detecting collisions between the pending objects and buffered door meshes; 
    for(let i = 0; i < door_mageAdd_set.length; i++){
        let doorMesh = door_mageAdd_set[i];
        if(detectCollisionGroups(doorMesh, objectCache[objname])){
            scene.remove(scene.getObjectByName(AUXILIARY_NAME));
            return;
        }
    }
    // detecting collisions between the pending objects and the wall: 
    let wallMeta = manager.renderManager.scene_json.rooms[currentRoomId].auxiliaryDomObj.room_meta; 
    if(detectCollisionWall(wallMeta, objectCache[objname])){
        scene.remove(scene.getObjectByName(AUXILIARY_NAME)); 
        return; 
    }
    if(!scene.getObjectByName(AUXILIARY_NAME)){
        scene.add(objectCache[objname]);
    }
    if(scene.getObjectByName(AUXILIARY_NAME).userData.modelId !== objname){
        scene.remove(scene.getObjectByName(AUXILIARY_NAME));
        scene.add(objectCache[objname]);
    }
}

function auxiliaryCG(theIntersects){
    // find the nearest distance to the nearest wall; ( np.abs(np.cross(p2-p1, p1-p3)) / norm(p2-p1) )
    let ado = manager.renderManager.scene_json.rooms[currentRoomId].auxiliaryDomObj;
    if(ado === undefined)
        return;
    let wallPointStart = manager.renderManager.scene_json.rooms[currentRoomId].auxiliaryDomObj.roomShapeTensor;
    let wallPointEnd = tf.concat([wallPointStart.slice([1], [wallPointStart.shape[0]-1]), wallPointStart.slice([0], [1])])
    
    let p3 = tf.tensor([theIntersects.point.x, theIntersects.point.z]);
    let a_square = tf.sum(tf.square(wallPointEnd.sub(wallPointStart)), axis=1);
    let b_square = tf.sum(tf.square(wallPointEnd.sub(p3)), axis=1);
    let c_square = tf.sum(tf.square(wallPointStart.sub(p3)), axis=1);
    let siafangbfang = a_square.mul(b_square).mul(4);
    let apbmcfang = tf.square(a_square.add(b_square).sub(c_square));
    let triangleArea = tf.sqrt(siafangbfang.sub(apbmcfang)).mul(0.5); // this is twice the area; 
    let wallDistances = triangleArea.div(tf.norm(wallPointEnd.sub(wallPointStart), 'euclidean', 1));
    let _indicesList = []; 
    let wallIndex;
    let secWallIndex; // the second nearest wall index; 
    let innerProducts = tf.sum((wallPointStart.sub(p3)).mul(wallPointStart.sub(wallPointEnd)), axis=1).arraySync();
    let wallIndices = tf.topk(wallDistances, wallDistances.shape[0], true).indices.arraySync().reverse();
    a_square = a_square.arraySync();
    for(let i = 0; i < wallIndices.length; i++){
        let wi = wallIndices[i];
        if( 0 <= innerProducts[wi] && innerProducts[wi] <= a_square[wi]){
            _indicesList.push(wi);
            // wallIndex = wi;
            if (_indicesList.length >= 2) break;
        }
    }
    wallIndex = _indicesList[0];
    secWallIndex = _indicesList[1]; 
    // let wallIndex = tf.argMin(wallDistances).arraySync();
    let minDis = wallDistances.slice([wallIndex], [1]).arraySync();
    let secMinDis = wallDistances.slice([secWallIndex], [1]); // the distance w.r.t the second nearest wall; 
    let vecSub;
    let secVecSub; 
    if(ado.tensor.shape[0] !== 0){
        vecSub = tf.abs(tf.transpose(tf.transpose(ado.tensor).slice([2], [1])).sub(minDis)).reshape([-1]);
        secVecSub = tf.transpose(tf.transpose(ado.tensor).slice([6], [1])).reshape([-1]); 
    }else{
        return;
    }
    // filter out priors exceed the second nearest wall; 
    vecSub = vecSub.where(secVecSub.less(secMinDis), Infinity); 
    let index = tf.argMin(vecSub).arraySync();
    // if the 'minimal distance sub' is still high, results in next level; 
    if(vecSub.slice([index], [1]).arraySync()[0] >= 0.48){
        scene.remove(scene.getObjectByName(AUXILIARY_NAME)); 
        return;
    }
    let objname = ado.index[index];
    let theprior = ado.prior[index];
    realTimeObjCache(objname, // object name
        theIntersects.point.x, 0, theIntersects.point.z, // x, y, z
        ado.room_orient[wallIndex] + theprior[1], // theta
        [theprior[3], theprior[4], theprior[5]]
    );
}

function auxiliaryMove(){
    // this may require a systematic optimization, since objList can be reduced to a single room; 
    let intersectObjList = Object.values(manager.renderManager.instanceKeyCache)
    .concat(Object.values(manager.renderManager.cwfCache));
    updateMousePosition();
    intersects = raycaster.intersectObjects(intersectObjList, true);
    if (intersectObjList.length > 0 && intersects.length > 0) {
        let intersectPoint = tf.tensor([intersects[0].point.x, intersects[0].point.y, intersects[0].point.z]);
        let vecSub;
        // if auxiliaryPiror.tensor.shape[0] equals to 0, then no context exists; 
        if(auxiliaryPrior.tensor.shape[0] !== 0){
            vecSub = tf.transpose(tf.transpose(auxiliaryPrior.tensor).slice([0], [3])).sub(intersectPoint);
        }else{
            auxiliaryCG(intersects[0]);
            return;
        }
        // transform priors
        let eucNorm = tf.norm(vecSub, 'euclidean', 1);
        let index = tf.argMin(eucNorm).arraySync();
        let eucDis = eucNorm.slice([index], [1]).arraySync();
        // console.log(`index: ${index}, dis: ${eucDis}, mouse: ${mouse.x}.`);
        let objname = auxiliaryPrior.index[index];
        let theprior = auxiliaryPrior.prior[index];
        if(eucDis >= 0.5){
            scene.remove(scene.getObjectByName(AUXILIARY_NAME)); 
            // if the intersection occurs at the floor, try suggest coherent groups; 
            if(manager.renderManager.cwfCache.includes(intersects[0].object.parent)){
                auxiliaryCG(intersects[0]);
            }
            return;
        }
        realTimeObjCache(objname, intersects[0].point.x, theprior[1], intersects[0].point.z, theprior[3]);
    }
}

function onDocumentMouseMove(event) {
    event.preventDefault();
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

var onWindowResize = function() { //改用画布的height width
    camera.aspect = scenecanvas.clientWidth / scenecanvas.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(scenecanvas.clientWidth, scenecanvas.clientHeight);
}

var reshuffleRoom = function () {
    if (currentRoomId === undefined) {
        console.log("No room is specified. ");
        return
    }
    $.ajax({
        type: "POST",
        contentType: "application/json; charset=utf-8",
        url: "/reshuffle",
        data: JSON.stringify(manager.renderManager.scene_json.rooms[currentRoomId]),
        success: function (data) {
            data = JSON.parse(data);
            temp = data;
            manager.renderManager.scene_json.rooms[currentRoomId].objList = data.objList;
            manager.renderManager.refresh_instances();
        }
    });
};

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

var temp;
var setting_up = function () {
    clear_panel();  // clear panel first before use individual functions.
    setUpCanvasDrawing();
    render_initialization();
    orth_initialization();
    searchPanelInitialization();
    radial_initialization();
    
    $(".btn").mousedown(function(e){e.preventDefault();})
    $("#sklayout").click(auto_layout);
    $("#layout_button").click(auto_layout);
    $("#reshuffle").click(reshuffleRoom);
    $("#mage_button").click(mage_add_control);
    $("#auxiliary_button").click(auxiliary_control);
    $("#download_button").click(function(){
        let json_to_dl = JSON.parse(JSON.stringify(manager.renderManager.scene_json));
        // delete unnecessary keys; 
        json_to_dl.rooms.forEach(function(room){
            room.objList.forEach(function(inst){
                if(inst === null || inst === undefined){
                    return
                }
                delete inst.key;
            })
        })
        var dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(json_to_dl));
        var dlAnchorElem = document.getElementById('downloadAnchorElem');
        dlAnchorElem.setAttribute("href",     dataStr     );
        dlAnchorElem.setAttribute("download", `${json_to_dl.origin}-l${json_to_dl.id}-dl.json`);
        dlAnchorElem.click();
    });
    $("#screenshot").click(function(){
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
    });

    scenecanvas.addEventListener('mousemove', onDocumentMouseMove, false);
    scenecanvas.addEventListener('mousedown', () => document.getElementById("searchinput").blur());
    window.addEventListener('resize', onWindowResize, false);
    // scenecanvas.addEventListener('click', onClickObj);
    document.addEventListener('keydown', onKeyDown, false);
    document.addEventListener('keyup', onKeyUp, false);
    orthcanvas.addEventListener('mousedown', orth_mousedown);
    orthcanvas.addEventListener('mouseup', orth_mouseup);
    orthcanvas.addEventListener('mousemove', orth_mousemove);
    orthcanvas.addEventListener('click', orth_mouseclick);

    gameLoop();
};
