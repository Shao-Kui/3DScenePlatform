const objectCache = {}; 
const gatheringObjCat = {}; 
let loadObjectToCache = function(modelId, anchor=()=>{}, anchorArgs=[]){
    if(modelId in objectCache){
        anchor.apply(null, anchorArgs);
        return;
    }
    let mtlurl = `/mtl/${modelId}`;
    let meshurl = `/mesh/${modelId}`;
    let objLoader = new THREE.OBJLoader();
    let mtlLoader = new THREE.MTLLoader();
    mtlLoader.load(mtlurl, function (mCreator) {
        objLoader.setMaterials(mCreator);
        objLoader.load(meshurl, function (instance) {
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
            traverseMtlToOppacity(instance);
            objectCache[modelId] = instance;
            anchor.apply(null, anchorArgs);;
        });
    });
};

const traverseMtlToOppacity = function (object) {
    if(object instanceof THREE.Mesh){
        let newmtr_lowopa;
        if(Array.isArray(object.material)){
            newmtr_lowopa = [];
            for(let i = 0; i < object.material.length; i++){
                let mtl = object.material[i].clone()
                mtl.transparent = true;
                mtl.opacity = 0.6;
                newmtr_lowopa.push(mtl);
            }
        }else{
            newmtr_lowopa = object.material.clone();
            newmtr_lowopa.transparent = true;
            newmtr_lowopa.opacity = 0.6;
            
        }
        newmtr_lowopa.origin_mtr = object.material;
        newmtr_lowopa.newmtr_lowopa = newmtr_lowopa;
        object.material.origin_mtr = object.material;
        object.material.newmtr_lowopa = newmtr_lowopa;
        object.material = newmtr_lowopa;
        return;
    }
    if(object.children.length === 0){
        return;
    }
    object.children.forEach(function(child){
        traverseMtlToOppacity(child);
    });
};

let refreshObjectFromCache = function(objToInsert){
    if(!(objToInsert.modelId in objectCache)) return;
    let object3d = objectCache[objToInsert.modelId].clone();
    object3d.name = undefined;
    object3d.scale.set(objToInsert.scale[0],objToInsert.scale[1],objToInsert.scale[2]);
    object3d.rotation.set(objToInsert.rotate[0],objToInsert.rotate[1],objToInsert.rotate[2]);
    object3d.position.set(objToInsert.translate[0],objToInsert.translate[1],objToInsert.translate[2]);
    object3d.userData = {
        "type": 'object',
        "key": objToInsert.key,
        "roomId": objToInsert.roomId,
        "modelId": objToInsert.modelId,
        "coarseSemantic": objToInsert.coarseSemantic
    };
    object3d.children.forEach(child => {
        if(child.material.origin_mtr) child.material = child.material.origin_mtr;
    });
    manager.renderManager.instanceKeyCache[objToInsert.key] = object3d;
    // add reference from object3d to objectjson: 
    object3d.userData.json = objToInsert;
    if(['Ceiling Lamp', 'Pendant Lamp', 'Wall Lamp', 'chandelier'].includes(object3d.userData.coarseSemantic)){
        let light = new THREE.PointLight( 0xffffff, 10, 100 );
        light.name = SEMANTIC_POINTLIGHT;
        light.position.set(0,0,0);
        object3d.add(light);
    }
    scene.add(object3d)
    renderer.render(scene, camera);
    return object3d; 
}

const roomIDCaster = new THREE.Raycaster();
const calculateRoomID = function(translate){
    roomIDCaster.set(new THREE.Vector3(translate[0], 100, translate[2]), new THREE.Vector3(0, -1, 0)); 
    let intersects = roomIDCaster.intersectObjects(manager.renderManager.cwfCache, true);
    if (manager.renderManager.cwfCache.length > 0 && intersects.length > 0) { 
        return intersects[0].object.parent.userData.roomId;
    }
    else{
        return 0; 
    }
}

let addObjectFromCache = function(modelId, transform={'translate': [0,0,0], 'rotate': [0,0,0], 'scale': [1.0,1.0,1.0]}, uuid=undefined, origin=true){
    loadMoreServerUUIDs(1);
    if(!uuid) uuid = serverUUIDs.pop(); 
    commandStack.push({
        'funcName': 'removeObjectByUUID',
        'args': [uuid, true]
    });
    /*if(!(modelId in objectCache)){
        loadObjectToCache(modelId, anchor=addObjectFromCache, anchorArgs=[modelId, transform, uuid, origin]);
        return; 
    }
    // check room ID: 
    let roomID = calculateRoomID(transform.translate); 
    let objToInsert = {
        "modelId": modelId,
        "coarseSemantic": gatheringObjCat[modelId], 
        "translate": transform.translate,
        "scale": transform.scale,
        "roomId": roomID,
        "rotate": transform.rotate,
        "orient": transform.rotate[1], 
        // "key": serverUUIDs.pop(),
        "key": uuid,
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
        "roomId": roomID,
        "modelId": modelId,
        "coarseSemantic": gatheringObjCat[modelId]
    };
    object3d.children.forEach(child => {
        if(child.material.origin_mtr) child.material = child.material.origin_mtr;
    });
    manager.renderManager.scene_json.rooms[roomID].objList.push(objToInsert);
    manager.renderManager.instanceKeyCache[objToInsert.key] = object3d;
    // manager.renderManager.refresh_instances();
    object3d.userData.json = objToInsert; // add reference from object3d to objectjson. 
    scene.add(object3d)
    renderer.render(scene, camera);
    if(origin && onlineGroup !== 'OFFLINE'){emitFunctionCall('addObjectFromCache', [modelId, transform, uuid, false]);}*/
    let roomID = calculateRoomID(transform.translate)
    let object3d = addObjectByUUID(uuid, modelId, roomID, transform);
    emitFunctionCall('addObjectByUUID', [uuid, modelId, roomID, transform]);
    return object3d; 
};

const door_mageAdd_set = []; 
const window_factor = 0.5; 
const _addDoor_mageAdd = (doorMeta) => {
    if(doorMeta.bbox === undefined){
        return;
    }
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
            if(!('coarseSemantic' in meta)) return; 
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
        let direction = end.clone().sub(start); 
        let wallLength = direction.length();
        direction.normalize();
        wallRayCaster.set(start, direction); 
        let intersects = wallRayCaster.intersectObjects([object], true); 
        if(intersects.length > 0) {
            if(intersects[0].point.clone().sub(start).length() < wallLength){
                return true; 
            }
        }
    }
    return false;
}

const gameLoop = function () {
    stats.begin();
    render_update();
    // orth_view_port_update();
    keyboard_update();
    camera.updateMatrixWorld();
    manager.renderManager.orthcamera.updateMatrixWorld();
    raycaster.setFromCamera(mouse, camera);
    if(fpCtrlMode){
        firstPersonUpdate();
    }
    // renderer.render(scene, camera);
    composer.render();
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

const synchronizeObjectJsonByObject3D = function(object3d){
    let objectjson = object3d.userData.json;
    objectjson.scale[0] = object3d.scale.x;
    objectjson.scale[1] = object3d.scale.y;
    objectjson.scale[2] = object3d.scale.z;
    objectjson.translate[0] = object3d.position.x;
    objectjson.translate[1] = object3d.position.y;
    objectjson.translate[2] = object3d.position.z;
    objectjson.rotate[0] = object3d.rotation.x;
    objectjson.rotate[1] = object3d.rotation.y;
    objectjson.rotate[2] = object3d.rotation.z;
    objectjson.orient = Math.atan2(Math.sin(object3d.rotation.y), Math.cos(object3d.rotation.x) * Math.cos(object3d.rotation.y));
    let newRoomId = calculateRoomID(objectjson.translate);
    if(newRoomId !== objectjson.roomId){
        let index = find_object_json(object3d);
        manager.renderManager.scene_json.rooms[newRoomId].objList.push(objectjson);
        delete manager.renderManager.scene_json.rooms[objectjson.roomId].objList[index];
        manager.renderManager.scene_json.rooms[objectjson.roomId].objList = 
        manager.renderManager.scene_json.rooms[objectjson.roomId].objList.filter( item => item !== null && item !== undefined );
        objectjson.roomId = newRoomId;
        object3d.userData.roomId = newRoomId;
        object3d.roomId = newRoomId;
    }
}

const tCache = []; 
var fastTimeLine = gsap.timeline({repeat: 0});
var lastMovedTimeStamp = moment();
var currentMovedTimeStamp = moment();
const transformObject3DOnly = function(uuid, xyz, mode='position', smooth=false){
    currentMovedTimeStamp = moment();
    let object3d = manager.renderManager.instanceKeyCache[uuid]; 
    if(smooth){
        gsap.to(object3d[mode], {
            duration: 0.2,
            x: xyz[0],
            y: xyz[1],
            z: xyz[2]
        });
    }else{
        object3d[mode].x = xyz[0]; object3d[mode].y = xyz[1]; object3d[mode].z = xyz[2]; 
    }
    tCache.push({
        'uuid': uuid, 
        'xyz': xyz, 
        'duration': moment.duration(currentMovedTimeStamp.diff(lastMovedTimeStamp)).asSeconds(),
        'mode': mode,
        'smooth': smooth
    }); 
    // if(tCache.length >= 100) emitAnimationObject3DOnly(); 
    lastMovedTimeStamp = currentMovedTimeStamp; 
};

const synchronize_json_object = function (object) {
    object.rotation.y = object.rotation.y % (Math.PI * 2);
    let inst = object.userData.json;
    commandStack.push({
        'funcName': 'transformObjectByUUID',
        'args': [object.userData.key, {
            'translate': [...inst.translate],
            'scale': [...inst.scale],
            'rotate': [...inst.rotate]
        }, object.userData.roomId]
    });
    synchronize_roomId(object);
    if(fastTimeLine.isActive()){
        fastTimeLine.seek(fastTimeLine.endTime());
        fastTimeLine.kill();
    }
    fastTimeLine = gsap.timeline({repeat: 0}); 
    tCache.length = 0; 
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
    if(onlineGroup !== 'OFFLINE'){
        let transform = {
            'translate': inst.translate,
            'scale': inst.scale,
            'rotate': inst.rotate
        };
        emitFunctionCall('transformObjectByUUID', [object.userData.key, transform, object.userData.roomId]);
    }
};

const synchronize_roomId = function (object) {
    let rooms = manager.renderManager.scene_json.rooms;
    let oriRoomId = object.userData.json.roomId;
    let newRoomId = calculateRoomID([object.position.x, object.position.y, object.position.z]);
    object.userData.json.roomId = newRoomId; 
    object.userData.roomId = newRoomId; 
    rooms[newRoomId].objList.push(object.userData.json);
    let i = rooms[oriRoomId].objList.indexOf(object.userData.json);
    rooms[oriRoomId].objList.splice(i, 1);
}

var updateMousePosition = function () {
    mouse.x = ((event.clientX - $(scenecanvas).offset().left) / scenecanvas.clientWidth) * 2 - 1;
    mouse.y = -((event.clientY - $(scenecanvas).offset().top) / scenecanvas.clientHeight) * 2 + 1;
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

const cancelClickingObject3D = function(){
    // synchronize data to scene json; 
    if(INTERSECT_OBJ) if(INTERSECT_OBJ.userData.key) claimControlObject3D(INTERSECT_OBJ.userData.key, true); 
    datguiObjectFolderRemove(INTERSECT_OBJ); 
    $('#tab_modelid').text(" ");
    $('#tab_category').text(" ");  
    transformControls.detach();
    INTERSECT_OBJ = undefined; //currentRoomId = undefined;
    if (isToggle) {
        radial.toggle();
        isToggle = !isToggle;
    }
}

var onTouchTimes = 1;
const onTouchObj = function (event) {
    onTouchTimes -= 1;
    if(onTouchTimes > 0) return; 
    scenecanvas.style.cursor = "auto";
    // do raycasting, judge whether or not users choose a new object; 
    camera.updateMatrixWorld();
    let pos = new THREE.Vector2();
    pos.x = ((event.changedTouches[0].clientX - $(scenecanvas).offset().left) / scenecanvas.clientWidth) * 2 - 1;
    pos.y = -((event.changedTouches[0].clientY - $(scenecanvas).offset().top) / scenecanvas.clientHeight) * 2 + 1;
    raycaster.setFromCamera(pos, camera);
    var intersects = raycaster.intersectObjects(manager.renderManager.cwfCache, true);
    if (manager.renderManager.cwfCache.length > 0 && intersects.length > 0) {
        currentRoomId = intersects[0].object.parent.userData.roomId;
        $('#tab_roomid').text(currentRoomId);
        $('#tab_roomtype').text(manager.renderManager.scene_json.rooms[currentRoomId].roomTypes);        
    } else {
        currentRoomId = undefined;
    }
    if(On_ADD){
        On_ADD = false;
        let p = raycaster.intersectObjects(Object.values(manager.renderManager.instanceKeyCache).concat(Object.values(manager.renderManager.wfCache)), true)[0].point;
        addObjectFromCache(
            modelId=INSERT_OBJ.modelId,
            transform={
                'translate': [p.x, p.y, p.z], 
                'rotate': [0,0,0],
                'scale': [1,1,1]
            }
        );
        scene.remove(scene.getObjectByName(INSERT_NAME));
        applyLayoutViewAdjust();
        return;
    }
    if (On_MOVE) {
        On_MOVE = false;
        synchronize_json_object(INTERSECT_OBJ);
        applyLayoutViewAdjust();
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
        applyLayoutViewAdjust();
        return;
    }
    onClickIntersectObject(event.changedTouches[0]);
};

const onClickIntersectObject = function(event){
    var instanceKeyCache = manager.renderManager.instanceKeyCache;
    instanceKeyCache = Object.values(instanceKeyCache);
    intersects = raycaster.intersectObjects(instanceKeyCache, true);
    if (instanceKeyCache.length > 0 && intersects.length > 0) {
        if(INTERSECT_OBJ){
            if(intersects[0].object.parent.userData.key !== INTERSECT_OBJ.userData.key){
                claimControlObject3D(INTERSECT_OBJ.userData.key, true);
                synchronize_json_object(INTERSECT_OBJ);
            }
        }
        // if this is the online mode and the object is already controlled by other users...
        if(onlineGroup !== 'OFFLINE' && 
            intersects[0].object.parent.userData.controlledByID !== undefined && 
            intersects[0].object.parent.userData.controlledByID !== onlineUser.id
        ){
            console.log(`This object is already claimed by ${intersects[0].object.parent.userData.controlledByID}`);
            cancelClickingObject3D();return; 
        }
        INTERSECT_OBJ = intersects[0].object.parent; //currentRoomId = INTERSECT_OBJ.userData.roomId;
        claimControlObject3D(INTERSECT_OBJ.userData.key, false);
        transformControls.attach(INTERSECT_OBJ);
        $('#tab_modelid').text(INTERSECT_OBJ.userData.modelId);
        $('#tab_category').text(INTERSECT_OBJ.userData.coarseSemantic);   
        $('#tab_roomid').text(INTERSECT_OBJ.userData.roomId);
        $('#tab_roomtype').text(manager.renderManager.scene_json.rooms[INTERSECT_OBJ.userData.roomId].roomTypes);   
        menu.style.left = (event.clientX - 63) + "px";
        menu.style.top = (event.clientY - 63) + "px";
        if ((!isToggle) && event.pointerType === "mouse") {
            radial.toggle();
            isToggle = !isToggle;
        }
        datguiObjectFolder(INTERSECT_OBJ);
        if($("#scenePaletteSVG").css('display') === 'block')
        {paletteExpand([INTERSECT_OBJ.userData.json.modelId]);}

        if (INTERSECT_WALL != undefined)
            unselectWall();
        return;
    }else{
        cancelClickingObject3D();
        if (INTERSECT_WALL == undefined) {
            var newWallCache = manager.renderManager.newWallCache;
            intersects = raycaster.intersectObjects(newWallCache, true);
            if (intersects.length > 0) {
                INTERSECT_WALL = intersects[0].object;
                if (INTERSECT_WALL.parent instanceof THREE.Group)
                    INTERSECT_WALL = INTERSECT_WALL.parent;
                console.log('intersect wall', INTERSECT_WALL);
            }
        } else {
            if (INTERSECT_WALL != undefined)
                unselectWall();
        }
    }
}

var onClickObj = function (event) {
    scenecanvas.style.cursor = "auto";
    // do raycasting, judge whether or not users choose a new object; 
    camera.updateMatrixWorld();
    raycaster.setFromCamera(mouse, camera);
    var intersects = raycaster.intersectObjects(manager.renderManager.fCache, true);
    if (manager.renderManager.cwfCache.length > 0 && intersects.length > 0) {
        currentRoomId = intersects[0].object.parent.userData.roomId;
        $('#tab_roomid').text(currentRoomId);
        $('#tab_roomtype').text(manager.renderManager.scene_json.rooms[currentRoomId].roomTypes);        
    } else {
        // currentRoomId = undefined;
    }
    mageAddSinglePrior.enabled = false;
    if(On_MAGEADD){
        On_MAGEADD = false;
        if(scene.getObjectByName(AUXILIARY_NAME)){
            let obj = scene.getObjectByName(AUXILIARY_NAME);
            addObjectFromCache(
                modelId=INSERT_OBJ.modelId,
                transform={
                    'translate': [obj.position.x, obj.position.y, obj.position.z], 
                    'rotate': [obj.rotation.x, obj.rotation.y, obj.rotation.z],
                    'scale': [obj.scale.x, obj.scale.y, obj.scale.z]
                }
            );
            scene.remove(scene.getObjectByName(AUXILIARY_NAME)); 
            return; 
        }
    }
    if (On_ADD) {
        On_ADD = false;
        let p = raycaster.intersectObjects(Object.values(manager.renderManager.instanceKeyCache).concat(Object.values(manager.renderManager.wfCache)), true)[0].point;
        addObjectFromCache(
            modelId=INSERT_OBJ.modelId,
            transform={
                'translate': [p.x, p.y, p.z], 
                'rotate': [0,0,0],
                'scale': [1,1,1]
            }
        );
        scene.remove(scene.getObjectByName(INSERT_NAME));
        applyLayoutViewAdjust();
        return;
    }
    if (On_MOVE) {
        On_MOVE = false;
        synchronize_json_object(INTERSECT_OBJ);
        applyLayoutViewAdjust();
        return;
    }
    if (On_MAGEMOVE) {
        On_MAGEMOVE = false;
        synchronize_json_object(INTERSECT_OBJ);
        applyLayoutViewAdjust();
        return;
    }
    if (On_CGSeries) {
        On_CGSeries = false;
        CGSERIES_GROUP.clear();
        synchronize_json_object(INTERSECT_OBJ);
        applyLayoutViewAdjust();
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
        applyLayoutViewAdjust();
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
        if(ao.userData.mageAddDerive !== "" && ao.userData.mageAddDerive){
            if(ao.userData.mageAddDerive.includes('dom')){applyLayoutViewAdjust();}
        }
        return; 
    }
    onClickIntersectObject(event);
};

const castMousePosition = function(){
    let intersectObjList = Object.values(manager.renderManager.instanceKeyCache)
    .filter(d => d.userData.key !== INTERSECT_OBJ.userData.key)
    .concat(Object.values(manager.renderManager.wfCache));
    intersects = raycaster.intersectObjects(intersectObjList, true);
    if(intersectObjList.length > 0 && intersects.length > 0){
        return intersects[0].point; 
    }else{
        return undefined; 
    }
}

function onDocumentMouseMove(event) {
    event.preventDefault();
    // raycasting & highlight objects: 
    var instanceKeyCache = manager.renderManager.instanceKeyCache;
    instanceKeyCache = Object.values(instanceKeyCache);
    let intersects = raycaster.intersectObjects(
        instanceKeyCache
        .concat(Object.values(manager.renderManager.fCache))
        .concat(Object.values(manager.renderManager.wCache)), 
        true
    );
    if(intersects.length > 0){
        $('#tab_X').text(intersects[0].point.x.toFixed(3));
        $('#tab_Y').text(intersects[0].point.y.toFixed(3));
        $('#tab_Z').text(intersects[0].point.z.toFixed(3));
    }
    if (instanceKeyCache.length > 0 && intersects.length > 0 && INTERSECT_OBJ === undefined && instanceKeyCache.includes(intersects[0].object.parent)) {
        outlinePass.selectedObjects = [intersects[0].object.parent];
    }else{
        outlinePass.selectedObjects = []
    }  
    // currentMovedTimeStamp = moment();
    tf.engine().startScope();
    if(On_ADD && INSERT_OBJ.modelId in objectCache){
        scene.remove(scene.getObjectByName(INSERT_NAME)); 
        if(intersects.length > 0){
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
    if(On_MAGEADD && INSERT_OBJ.modelId in objectCache){
        scene.remove(scene.getObjectByName(INSERT_NAME)); 
        let args = mageAddSingle();
        if(args !== undefined){
            realTimeSingleCache.apply(null, [INSERT_OBJ['modelId']].concat(args));
        }
    }
    if(On_MAGEMOVE){
        let args = mageAddSingle();
        if(args != undefined){
            args[3] = Math.atan2(Math.sin(args[3]), Math.cos(args[3]));
            // args[3] = INTERSECT_OBJ.rotation.y - smallestSignedAngleBetween(INTERSECT_OBJ.rotation.y, args[3]);
            if(args !== undefined){
                transformObject3DOnly(INTERSECT_OBJ.userData.key, [args[0], args[1], args[2]], 'position', true); 
                if(args[5]){
                    transformObject3DOnly(INTERSECT_OBJ.userData.key, [0, args[3], 0], 'rotation', true); 
                    if(args[5] === 'dom'){
                        transformObject3DOnly(INTERSECT_OBJ.userData.key, args[4], 'scale', true);
                    }
                }
            }
        }
    }
    if(On_CGSeries){
        moveCGSeries();
    }
    if (On_ROTATE && INTERSECT_OBJ != null) {
        var rtt_pre = new THREE.Vector2();
        var rtt_nxt = new THREE.Vector2();
        rtt_pre.set(mouse.x, mouse.y);
        updateMousePosition();
        rtt_nxt.set(mouse.x, mouse.y);
        rtt_pre.sub(mouse.rotateBase);
        rtt_nxt.sub(mouse.rotateBase);
        // INTERSECT_OBJ.rotateY(rtt_nxt.angle() - rtt_pre.angle());
        transformObject3DOnly(INTERSECT_OBJ.userData.key, [
            INTERSECT_OBJ.rotation.x, 
            INTERSECT_OBJ.rotation.y + (rtt_nxt.angle() - rtt_pre.angle()), 
            INTERSECT_OBJ.rotation.z
        ], 'rotation')
    }
    if (On_MOVE && INTERSECT_OBJ != null) {
        let ip = castMousePosition();
        if(ip){
            transformObject3DOnly(INTERSECT_OBJ.userData.key, [ip.x, ip.y, ip.z]); 
        }
    }
    if (On_LIFT && INTERSECT_OBJ != null) {
        var last_y = mouse.y;
        updateMousePosition();
        var this_y = mouse.y;
        transformObject3DOnly(INTERSECT_OBJ.userData.key, [
            INTERSECT_OBJ.position.x, 
            INTERSECT_OBJ.position.y + 2 * (this_y - last_y),
            INTERSECT_OBJ.position.z                          
        ], 'position'); 
    }
    if (On_SCALE && INTERSECT_OBJ != null){
        var last_x = mouse.x;
        updateMousePosition();
        var this_x = mouse.x;
        s = 0.3;
        transformObject3DOnly(INTERSECT_OBJ.userData.key, [
            INTERSECT_OBJ.scale.x + s * (this_x - last_x), 
            INTERSECT_OBJ.scale.y + s * (this_x - last_x), 
            INTERSECT_OBJ.scale.z + s * (this_x - last_x)
        ], 'scale'); 
    }
    if(AUXILIARY_MODE && auxiliaryPrior !== undefined){
        auxiliaryMove();
    }
    if (INTERSECT_WALL != undefined) {
        let ip = castMousePositionForWall();
        if(ip){
            transformWall(INTERSECT_WALL, [ip.x, ip.y, ip.z]); 
        }
    }
    tf.engine().endScope();
    updateMousePosition();
};

const onWindowResize = function(){
    camera.aspect = scenecanvas.clientWidth / scenecanvas.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(scenecanvas.clientWidth, scenecanvas.clientHeight); 
    composer.setSize(scenecanvas.clientWidth, scenecanvas.clientHeight);
    $('#uibody').height($(document).height() - $('#menubar').outerHeight());
    $('#scenecanvas').width('100%'); 
    $('#scenecanvas').height($(document).height() - $('#menubar').outerHeight()); 

    fxaaPass.material.uniforms[ 'resolution' ].value.x = 1 / (scenecanvas.clientWidth);
	fxaaPass.material.uniforms[ 'resolution' ].value.y = 1 / (scenecanvas.clientHeight);
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
    commandStack.push({
        'funcName': 'addObjectByUUID',
        'args': [
            INTERSECT_OBJ.userData.key, 
            INTERSECT_OBJ.userData.json.modelId, 
            INTERSECT_OBJ.userData.json.roomId,
            {
                'translate': [INTERSECT_OBJ.position.x, INTERSECT_OBJ.position.y, INTERSECT_OBJ.position.z], 
                'rotate': [INTERSECT_OBJ.rotation.x, INTERSECT_OBJ.rotation.y, INTERSECT_OBJ.rotation.z], 
                'scale': [INTERSECT_OBJ.scale.x, INTERSECT_OBJ.scale.y, INTERSECT_OBJ.scale.z]
            }
        ]
    });
    datguiObjectFolderRemove(INTERSECT_OBJ); 
    if(AUXILIARY_MODE){
        auxiliaryMode();
    }
    applyLayoutViewAdjust();
    removeObjectByUUID(INTERSECT_OBJ.userData.key);
    INTERSECT_OBJ = undefined;
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
    if(On_MAGEADD){
        onAddOff();
        auxiliary_remove();
        On_MAGEADD = false;
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
    sceneJson.PerspectiveCamera.roomId = calculateRoomID([camera.position.x, camera.position.y, camera.position.z]);
    let up = new THREE.Vector3()
    up.copy(camera.up)
    up.applyQuaternion(camera.quaternion)
    sceneJson.PerspectiveCamera.up = [up.x, up.y, up.z];
    sceneJson.canvas = {};
    sceneJson.canvas.width = scenecanvas.width;
    sceneJson.canvas.height = scenecanvas.height;
}

const datguiFolders = {} // (TBD) a dat.gui folder list for multiple objects; dat.gui in the online mode; 
const controllerOnChangeGen = function(mode, axis, objmesh){
    return v => {
        transformObject3DOnly(objmesh.userData.key, [
            (axis === 'x') ? v : objmesh[mode].x,
            (axis === 'y') ? v : objmesh[mode].y,
            (axis === 'z') ? v : objmesh[mode].z
        ], mode); 
    }; 
}; 
const datguiObjectFolder = function(objmesh){
    // activating dat.gui:
    if(datgui_intersectfolder){
        datgui.removeFolder(datgui_intersectfolder); 
        datgui_intersectfolder = undefined;
    } 
    datgui_intersectfolder = datgui.addFolder(objmesh.userData.modelId);
    datgui_intersectfolder.open();
    let t = {
        'scale': {'x': objmesh.scale.x, 'y': objmesh.scale.y, 'z': objmesh.scale.z},
        'rotation': {'y': objmesh.rotation.y},
        'position': {'x': objmesh.position.x, 'y': objmesh.position.y, 'z': objmesh.position.z}
    };
    let ctrlScaleX = datgui_intersectfolder.add(t.scale, 'x', 0.05, 3.0); 
    ctrlScaleX.domElement.parentElement.getElementsByClassName('property-name')[0].textContent = 'Scale-X';
    let ctrlScaleY = datgui_intersectfolder.add(t.scale, 'y', 0.05, 3.0); 
    ctrlScaleY.domElement.parentElement.getElementsByClassName('property-name')[0].textContent = 'Scale-Y';
    let ctrlScaleZ = datgui_intersectfolder.add(t.scale, 'z', 0.05, 3.0); 
    ctrlScaleZ.domElement.parentElement.getElementsByClassName('property-name')[0].textContent = 'Scale-Z';
    
    let ctrlOrient = datgui_intersectfolder.add(t.rotation, 'y', -3.15, 3.15, 0.01); 
    ctrlOrient.domElement.parentElement.getElementsByClassName('property-name')[0].textContent = 'Orient';

    let rbb = manager.renderManager.scene_json.rooms[objmesh.userData.roomId].bbox; 
    let ctrlPosX = datgui_intersectfolder.add(t.position, 'x', 
    rbb.min[0], rbb.max[0]); 
    ctrlPosX.domElement.parentElement.getElementsByClassName('property-name')[0].textContent = 'Pos-X';
    let ctrlPosY = datgui_intersectfolder.add(t.position, 'y', 
    rbb.min[1], rbb.max[1]); 
    ctrlPosY.domElement.parentElement.getElementsByClassName('property-name')[0].textContent = 'Pos-Y';
    let ctrlPosZ = datgui_intersectfolder.add(t.position, 'z', 
    rbb.min[2], rbb.max[2]); 
    ctrlPosZ.domElement.parentElement.getElementsByClassName('property-name')[0].textContent = 'Pos-Z';

    ctrlPosX.onChange(controllerOnChangeGen('position', 'x', objmesh)); 
    ctrlPosY.onChange(controllerOnChangeGen('position', 'y', objmesh)); 
    ctrlPosZ.onChange(controllerOnChangeGen('position', 'z', objmesh)); 
    ctrlOrient.onChange(controllerOnChangeGen('rotation', 'y', objmesh)); 
    ctrlScaleX.onChange(controllerOnChangeGen('scale', 'x', objmesh)); 
    ctrlScaleY.onChange(controllerOnChangeGen('scale', 'y', objmesh)); 
    ctrlScaleZ.onChange(controllerOnChangeGen('scale', 'z', objmesh)); 
};

const datguiObjectFolderRemove = function(objmesh){
    if(datgui_intersectfolder){
        datgui.removeFolder(datgui_intersectfolder); 
        datgui_intersectfolder = undefined; 
    }
}

const getDownloadSceneJson = function(){
    let json_to_dl = JSON.parse(JSON.stringify(manager.renderManager.scene_json));
    json_to_dl.rooms.forEach( room => {
        room.auxiliaryDomObj = undefined;
        room.auxiliarySecObj = undefined;
        room.auxiliaryWallObj = undefined;
    })
    // delete unnecessary keys; 
    json_to_dl.rooms.forEach(function(room){
        room.objList = room.objList.filter( item => item !== null && item !== undefined )
        room.objList.forEach(function(inst){
            if(inst === null || inst === undefined){
                return
            }
            // delete inst.key;
        })
    })
    encodePerspectiveCamera(json_to_dl); 
    return json_to_dl;
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

const downloadSceneJson =  function(){
    let json_to_dl = getDownloadSceneJson();
    var dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(json_to_dl));
    var dlAnchorElem = document.getElementById('downloadAnchorElem');
    dlAnchorElem.setAttribute("href", dataStr);
    dlAnchorElem.setAttribute("download", `${json_to_dl.origin}-r${json_to_dl.PerspectiveCamera.roomId}.json`);
    dlAnchorElem.click();
}

var temp;
const setting_up = function () {
    // clear_panel();  // clear panel first before use individual functions.
    setUpCanvasDrawing();
    render_initialization();
    orth_initialization();
    searchPanelInitialization();
    radial_initialization();
    onlineInitialization();

    // adding the `stats` panel for monitoring FPS; 
    stats = new Stats();
    stats.showPanel(0); // 0: fps, 1: ms, 2: mb, 3+: custom
    // stats.dom.style.top = '5%'
    // stats.dom.style.left = '25%'
    stats.dom.style.position = "absolute";
    document.getElementById('scene').appendChild(stats.dom);

    // adding the `dat.gui` panel for modifying objects; 
    datgui = new dat.GUI(); // this initialization only conducts once; 
    datgui.domElement.style.marginRight = "0px"
    datgui.domElement.parentElement.style.top = "0%"; 
    datgui.domElement.parentElement.style.right = "0%"; 
    datgui.domElement.parentElement.style.position = "absolute";
    document.getElementById("uibody").appendChild(datgui.domElement.parentElement);

    autocollapse("#menubar", 52);
    $(window).on("resize", function () {
      autocollapse("#menubar", 52);
    });
    $("#sidebar").on("shown.bs.collapse", function () {
        autocollapse("#menubar", 52);
    });
    $("#sidebar").on("hidden.bs.collapse", function () {
        autocollapse("#menubar", 52);
    });
    $("#sidebar").on("shown.bs.collapse", onWindowResize);
    $("#sidebar").on("hidden.bs.collapse", onWindowResize);
    
    $(".btn").mousedown(function(e){e.preventDefault();})
    $("#sklayout").click(auto_layout);
    $("#btnPlanIT").click(auto_layout_PlanIT);
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
        refreshRoomByID(currentRoomId, manager.renderManager.scene_json.rooms[currentRoomId].objList);
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
    $("#auxiliary_button").click(auxiliary_control);
    $("#layoutviewadjust_button").click(layoutviewadjust_control);
    $("#bestview_button").click(() => {
        $.ajax({
            type: "POST",
            contentType: "application/json; charset=utf-8",
            url: `/bestviewroom/${currentRoomId}`,
            data: JSON.stringify(getDownloadSceneJson()),
            success: function (data) {
                pcam = JSON.parse(data);
                viewTransform(pcam);
            }
        });
    });
    $("#download_button").click(downloadSceneJson);
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
    });
    paletteInit();
    $("#scenePalette").click(function(){
        if($("#scenePaletteSVG").css('display') === 'block'){
            $("#scenePaletteSVG").css('display', 'none');
        }else{
            $("#scenePaletteSVG").css('display', 'block');
        }
    });
    $("#firstperson_button").click(function(){
        let button = document.getElementById("firstperson_button");
        fpCtrlMode = !fpCtrlMode;
        if(fpCtrlMode){
            button.style.backgroundColor = '#9400D3';
            firstPersonOn();
        }else{
            button.style.backgroundColor = 'transparent';
            firstPersonOff();
        }
    });
    $("#lighting_btn").click(function(){
        let button = document.getElementById("lighting_btn");
        lighting_Mode = !lighting_Mode;
        if(lighting_Mode){
            button.style.backgroundColor = '#9400D3';
            Object.values(manager.renderManager.instanceKeyCache).forEach(object3d => {
                if(['Ceiling Lamp', 'Pendant Lamp', 'Wall Lamp'].includes(object3d.userData.coarseSemantic)){
                    let light = new THREE.PointLight( 0xffffff, 5, 100 );
                    light.name = SEMANTIC_POINTLIGHT;
                    light.position.set(0,0,0);
                    // light.castShadow = true;
                    // light.shadow.mapSize.width = 16; // default
                    // light.shadow.mapSize.height = 16; // default
                    object3d.add(light);
                }
            });
        }else{
            button.style.backgroundColor = 'transparent';
            Object.values(manager.renderManager.instanceKeyCache).forEach(object3d => {
                if(['Ceiling Lamp', 'Pendant Lamp'].includes(object3d.userData.coarseSemantic)){
                    object3d.remove(object3d.getObjectByName(SEMANTIC_POINTLIGHT));
                }
            });
        }
    });
    
    $("#usercommitchange_button").click(() => {
        username = $("#username").val();
        if (username != "") {
            $.ajax({
                type: "POST",
                contentType: "application/json; charset=utf-8",
                url: `/usercommitchange/${username}`,
                data: JSON.stringify(getDownloadSceneJson()),
                success: function (msg) {
                    console.log(msg);
                }
            });
        }
    });

    scenecanvas.addEventListener('mousemove', onDocumentMouseMove, false);
    scenecanvas.addEventListener('mousedown', () => {
        document.getElementById("searchinput").blur();
        document.getElementById("utils_button").blur();
    });
    window.addEventListener('resize', onWindowResize, false);
    $(window).resize(onWindowResize);
    // scenecanvas.addEventListener('click', onClickObj);
    scenecanvas.addEventListener('touchend', onTouchObj);
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
    scene.add(CGSERIES_GROUP);
    onWindowResize();
    gameLoop();
};

var autocollapse = function (menu, maxHeight) {
  var nav = $(menu);
  var navHeight = nav.innerHeight();
  var menuBtns = $("#menuBtns");
  if (navHeight >= maxHeight) {
    $("#sidebar_button").removeClass("mr-auto").addClass("mr-5");

    while (navHeight > maxHeight) {
      //  add child to dropdown
      var children = menuBtns.children("button");
      var count = children.length;
      if (count == 0) {
        break;
      }
      $(children[count - 1])
        .removeClass("mx-2 btn-lg navbar-btn")
        .addClass("my-1 nav_sk_button");
      $(children[count - 1]).prependTo(menu + " .dropdown-menu");
      navHeight = nav.innerHeight();
    }

    $("#sidebar_button").removeClass("mr-5").addClass("mr-auto");
  } else {
    var collapsed = $(menu + " .dropdown-menu").children(menu + " button");

    while (navHeight < maxHeight && collapsed.length > 6) {
      //  remove child from dropdown
      $(collapsed[0]).removeClass("my-1 nav_sk_button").addClass("mx-2 btn-lg navbar-btn");
      $(collapsed[0]).appendTo(menuBtns);
      navHeight = nav.innerHeight();
      collapsed = $(menu + " .dropdown-menu").children("button");
    }

    if (navHeight > maxHeight) {
      var children = menuBtns.children("button");
      var count = children.length;
      if (count > 0) {
        $(children[count - 1])
          .removeClass("mx-2 btn-lg navbar-btn")
          .addClass("my-1 nav_sk_button");
        $(children[count - 1]).prependTo(menu + " .dropdown-menu");
      }
    }
  }
};

const transformWall = function(wall, xyz){
    let axis = wall.userData["axis"];
    let groupId = wall.userData["groupId"];
    let wg = manager.renderManager.wallGroup[groupId];
    let range = wg.idxRange;
    let pos = axis == "x" ? xyz[0] : xyz[2];
    for (let i = range[0]; i < range[1]; ++i) {
        if (axis == "x") {
            manager.renderManager.newWallCache[i].position.x = pos;
        } else {
            manager.renderManager.newWallCache[i].position.z = pos;
        }
    }
    let adjRoomShape = wg.adjRoomShape;
    const rooms = manager.renderManager.scene_json.rooms;
    for (let r of adjRoomShape) {
        const roomShape = rooms[r[0]].roomShape;
        for (let i of r[1][0]) {
            if (axis == "x")
                roomShape[i][0] = pos - wg.halfWidth;
            else
                roomShape[i][1] = pos - wg.halfWidth;
        }
        for (let i of r[1][1]) {
            if (axis == "x")
                roomShape[i][0] = pos + wg.halfWidth;
            else
                roomShape[i][1] = pos + wg.halfWidth;
        }
    }
    // if (currentRoomId != undefined)
    //     console.log(manager.renderManager.scene_json.rooms[currentRoomId].roomShape);
};

const castMousePositionForWall = function(){
    let infFloor = manager.renderManager.infFloor;
    intersects = raycaster.intersectObject(infFloor);
    if(intersects.length > 0)
        return intersects[0].point; 
    else
        return undefined; 
}

const unselectWall = function() {
    let wall = INTERSECT_WALL;
    let groupId = wall.userData["groupId"];
    let wg = manager.renderManager.wallGroup[groupId];

    let axis = wg.axis;
    let wallPos = axis == "x" ? wall.position.x : wall.position.z;
    
    let adjFloor = wg.adjFloor;
    const fCache = manager.renderManager.fCache;
    for (let f of adjFloor) {
        const pos = fCache[f[0]].children[0].geometry.attributes.position.array;
        for (let i of f[1][0]) {
            pos[i] = wallPos - wg.halfWidth;
        }
        for (let i of f[1][1]) {
            pos[i] = wallPos + wg.halfWidth;
        }
        fCache[f[0]].children[0].geometry.attributes.position.needsUpdate = true;
    }

    let adjWall = wg.adjWall;
    const nwCache = manager.renderManager.newWallCache;
    for (let w of adjWall) {
        const instance = nwCache[w[0]];
        const offset = axis == "x" ? instance.position.x : instance.position.z;
        const pos = instance.children[0].geometry.attributes.position.array;
        for (let i of w[1][0]) {
            pos[i] = wallPos - wg.halfWidth - offset;
        }
        for (let i of w[1][1]) {
            pos[i] = wallPos + wg.halfWidth - offset;
        }
        instance.children[0].geometry.attributes.position.needsUpdate = true;
    }

    INTERSECT_WALL = undefined;
}
