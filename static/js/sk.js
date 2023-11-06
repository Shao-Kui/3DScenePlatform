const roomIDCaster = new THREE.Raycaster();
const calculateRoomID = function(translate){
    roomIDCaster.set(new THREE.Vector3(translate[0], 100, translate[2]), new THREE.Vector3(0, -1, 0)); 
    let intersects = roomIDCaster.intersectObjects(manager.renderManager.cwfCache, true);
    if (manager.renderManager.cwfCache.length > 0 && intersects.length > 0) { 
        if(intersects[0].object.parent.userData.roomId === undefined){
            return 0;
        }else{
            return intersects[0].object.parent.userData.roomId;
        }
    }
    else{
        return 0; 
    }
}

const removeObjectsByUUID = function(uuids){
    uuids.forEach(uuid => {
        removeObjectByUUID(uuid, true);
    })
}

const door_mageAdd_set = []; 
// const window_factor = 0.5; 
const window_factor = 0; 
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
    // let scale = [1,1,1]; scale[_minIndex] = 6; 
    let scale = [1,1,1]; scale[_minIndex] = 1; 
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
    box1.expandByScalar(0.06);
    box2.expandByScalar(0.06);
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

const updateTimerTab = function(){
    $('#tab_Navigate').text(timeCounter.navigate.toFixed(3));
    $('#tab_Add').text(timeCounter.add.toFixed(3));
    $('#tab_Remove').text(timeCounter.remove.toFixed(3));
    $('#tab_Move').text(timeCounter.move.toFixed(3));
    $('#tab_Rotate').text(timeCounter.rotate.toFixed(3));
    $('#tab_Scale').text(timeCounter.scale.toFixed(3));
    $('#tab_CGS').text(timeCounter.cgs.toFixed(3));
    $('#tab_Clicks').text(timeCounter.clicks);
    $('#tab_Total').text(timeCounter.total.toFixed(3));
}

const toScreenPosition = function(obj, camera){
    let vector = new THREE.Vector3();
    let widthHalf = 0.5 * renderer.getContext().canvas.width;
    let heightHalf = 0.5 * renderer.getContext().canvas.height;
    obj.updateMatrixWorld();
    vector.setFromMatrixPosition(obj.matrixWorld);
    vector.project(camera);
    vector.x = ( vector.x * widthHalf ) + widthHalf + $(scenecanvas).offset().left;
    vector.y = - ( vector.y * heightHalf ) + heightHalf + $(scenecanvas).offset().top;
    return { 
        x: vector.x,
        y: vector.y
    };
};

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
    const mixerUpdateDelta = deltaClock.getDelta();
    animaMixers.forEach(animaMixer => {
        animaMixer.update(mixerUpdateDelta);
    })
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
const transformObject3DOnly = function(uuid, xyz, mode='position', smooth=false, duration=0.2, ease='power1'){
    currentMovedTimeStamp = moment();
    let object3d = manager.renderManager.instanceKeyCache[uuid]; 
    if(smooth){
        gsap.to(object3d[mode], {
            duration: duration,
            x: xyz[0],
            y: xyz[1],
            z: xyz[2],
            ease: ease
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
            'rotate': inst.rotate,
            'startState': inst.startState
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

const releaseGTRANSChildrens = function(){
    let released = [];
    while(GTRANS_GROUP.children.length != 0){
        let c = GTRANS_GROUP.children[0];
        c.updateWorldMatrix(true, true);
        let m = c.matrixWorld.clone();
        scene.add(c);
        c.position.set(0,0,0);c.rotation.set(0,0,0);c.scale.set(1,1,1);
        c.applyMatrix4(m)
        synchronize_json_object(c);
        released.push(c.name);
    }
    return released;
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
    releaseGTRANSChildrens();
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
        timeCounter.add += moment.duration(moment().diff(timeCounter.addStart)).asSeconds();
        return;
    }
    if (On_MOVE) {
        On_MOVE = false;
        synchronize_json_object(INTERSECT_OBJ);
        applyLayoutViewAdjust();
        timeCounter.move += moment.duration(moment().diff(timeCounter.moveStart)).asSeconds();
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
        timeCounter.rotate += moment.duration(moment().diff(timeCounter.rotateStart)).asSeconds();
        return;
    }
    updateTimerTab();
    onClickIntersectObject(event.changedTouches[0]);
};

const actionForthToTarget  = function(action, duration=1){
    // action.getMixer().addEventListener('finished', e => {action.reset();action.paused = true;action.time = action.getClip().duration;action.weight = 1;console.log('starting forth to target', action.time, action.getClip().name);});
    action.reset();
    action.paused = true;
    action.setDuration(duration);
    action.timeScale = Math.abs(action.timeScale);
    action.time = 0;
    action.paused = false;
    action.weight = 1;
}

const actionBackToOrigin = function(action, duration=1){
    // action.getMixer().addEventListener('finished', e => {action.reset();action.paused = true;action.time = 0;action.weight = 0;console.log('starting back to origin', action.time, action.getClip().name);});
    action.reset();
    action.paused = true;
    action.setDuration(duration);
    action.timeScale = -Math.abs(action.timeScale);
    action.time = action.getClip().duration;
    action.paused = false;
}

const objectToAction = function(object3d, actionName, duration=1){
    let isNeedBack = false;
    if(object3d.userData.json.startState === actionName){
        return;
    }
    if(actionName != 'origin' && object3d.userData.json.startState != 'origin'){
        duration = duration * 0.5;
    }
    object3d.userData.json.startState = actionName;
    
    Object.keys(object3d.actions).forEach(function(an){
        let action = object3d.actions[an]
        if(action.time === action.getClip().duration){ // if this action is performed already: 
            actionBackToOrigin(action, duration);
            action.afterCall = a => {a.weight = 0;a.time=0;}
            isNeedBack = true;
        }
    });
    if(actionName === 'origin'){
        return;
    }
    if(isNeedBack){
        setTimeout(actionForthToTarget, duration*1000, object3d.actions[actionName], duration);
    }
    else{
        actionForthToTarget(object3d.actions[actionName], duration);
    }
    if(actionName != 'origin'){
        console.log(actionName, 'origin')
        object3d.actions[actionName].afterCall = a => {a.weight = 1;a.time = a.getClip().duration;}
    }
}

const setNewIntersectObj = function(event = undefined){
    claimControlObject3D(INTERSECT_OBJ.userData.key, false);
    transformControls.attach(INTERSECT_OBJ);
    $('#tab_modelid').text(INTERSECT_OBJ.userData.modelId);
    $('#tab_category').text(INTERSECT_OBJ.userData.coarseSemantic);   
    $('#tab_roomid').text(INTERSECT_OBJ.userData.roomId);
    $('#tab_roomtype').text(manager.renderManager.scene_json.rooms[INTERSECT_OBJ.userData.roomId].roomTypes);   
    let radialPos = toScreenPosition(INTERSECT_OBJ, camera);
    menu.style.left = (radialPos.x - 63) + "px";
    menu.style.top = (radialPos.y - 63) + "px";
    if(event){
        if((!isToggle) && event.pointerType === "mouse"){
            radial.toggle();
            isToggle = !isToggle;
        }
    }
    datguiObjectFolder(INTERSECT_OBJ);
    if($("#scenePaletteSVG").css('display') === 'block'){paletteExpand([INTERSECT_OBJ.userData.json.modelId]);}
    // if the new intersected object is transformable: 
    if("actions" in INTERSECT_OBJ){
        while (catalogItems.firstChild) {
            catalogItems.firstChild.remove();
        }
        ['origin'].concat(Object.keys(INTERSECT_OBJ.actions)).forEach(function (actionName){
            let iDiv = document.createElement('div');
            iDiv.className = "catalogItem";
            // iDiv.textContent = actionName;
            iDiv.setAttribute('key', INTERSECT_OBJ.userData.key);
            iDiv.setAttribute('actionName', actionName);
            iDiv.style.backgroundImage = `url(/static/dataset/object/${INTERSECT_OBJ.userData.json.modelId}/render20${actionName}/render-${actionName}-10.png)`;
            iDiv.addEventListener('click', function(e){
                e.preventDefault();
                let object3d = manager.renderManager.instanceKeyCache[$(e.target).attr("key")];
                if(animaRecord_Mode && $(e.target).attr("actionName") != object3d.userData.json.startState){
                    let index = object3d.userData.json.sforder;
                    let startTime;
                    if(currentSeqs[index][0].length === 0){
                        startTime = 0;
                    }else{
                        startTime = currentSeqs[index][0].at(-1).t[1];
                    }
                    currentSeqs[index][0].push({
                        "action": "transform",
                        "s1": object3d.userData.json.startState,
                        "s2": $(e.target).attr("actionName"),
                        "t": [startTime, startTime+1]
                    });
                }
                objectToAction(object3d, $(e.target).attr("actionName"), 1);
                synchronize_json_object(object3d);
                console.log($(e.target).attr("actionName"), object3d.userData.json.startState);
            });
            catalogItems.appendChild(iDiv);
        });
    }
}

const addToGTRANS = function(so){
    if(GTRANS_GROUP.getObjectByName(so.userData.key)){
        so.updateWorldMatrix(true, true);
        let m = so.matrixWorld.clone();
        scene.add(so);
        so.position.set(0,0,0);so.rotation.set(0,0,0);so.scale.set(1,1,1);
        so.applyMatrix4(m)
        synchronize_json_object(so);
        return;
    }
    let orientDom = Math.atan2(Math.sin(INTERSECT_OBJ.rotation.y), Math.cos(INTERSECT_OBJ.rotation.x) * Math.cos(INTERSECT_OBJ.rotation.y));
    let orientSub = Math.atan2(Math.sin(so.rotation.y), Math.cos(so.rotation.x) * Math.cos(so.rotation.y));
    GTRANS_GROUP.position.set(INTERSECT_OBJ.position.x,INTERSECT_OBJ.position.y,INTERSECT_OBJ.position.z);
    GTRANS_GROUP.rotation.set(INTERSECT_OBJ.rotation.x,INTERSECT_OBJ.rotation.y,INTERSECT_OBJ.rotation.z);
    // GTRANS_GROUP.scale.set(INTERSECT_OBJ.scale.x,INTERSECT_OBJ.scale.y,INTERSECT_OBJ.scale.z);
    // GTRANS_GROUP.rotation.set(0, 0, 0);
    GTRANS_GROUP.scale.set(1, 1, 1);
    
    // let mw = INTERSECT_OBJ.matrixWorld.clone().invert().multiply(intersects[0].object.parent.matrixWorld.clone());
    let relativeTranslate = so.position.clone().sub(INTERSECT_OBJ.position);
    let rotationY = new THREE.Matrix4().makeRotationY(-orientDom);
    relativeTranslate.applyMatrix4(rotationY);
    // relativeTranslate.divide(INTERSECT_OBJ.scale);
    // let relativeScale = so.scale.clone().divide(INTERSECT_OBJ.scale);
    // let rx = Math.sin(orientSub - orientDom) * INTERSECT_OBJ.scale.x;
    // let rz = Math.cos(orientSub - orientDom) * INTERSECT_OBJ.scale.z;
    // let theta = Math.atan2(rx, rz);
    // let sz = Math.sqrt(Math.pow(INTERSECT_OBJ.scale.z * Math.cos(theta), 2) + Math.pow(INTERSECT_OBJ.scale.x * Math.sin(theta), 2));
    // let sx = Math.sqrt(Math.pow(INTERSECT_OBJ.scale.z * Math.sin(theta), 2) + Math.pow(INTERSECT_OBJ.scale.x * Math.cos(theta), 2));
    so.position.set(relativeTranslate.x, relativeTranslate.y, relativeTranslate.z);
    so.rotation.set(0, orientSub - orientDom, 0);
    // so.scale.set(so.scale.x / sx, relativeScale.y, so.scale.z / sz);
    // so.scale.set(1, relativeScale.y, 1);
    GTRANS_GROUP.add(so);
}

const toSceneObj = function(object3d){
    do{
        if(object3d.parent === null){
            break;
        }
        if(object3d.parent.parent === null){
            break;
        }
        if(!object3d.userData){
            object3d = object3d.parent;
            continue;
        }
        if(!object3d.userData.isSceneObj){
            object3d = object3d.parent;
            continue;
        }else{
            break;
        }
    }while(object3d.parent.type !== 'Scene')
    return object3d;
}

const onClickIntersectObject = function(event){
    duplicateTimes = 1;
    var instanceKeyCache = manager.renderManager.instanceKeyCache;
    instanceKeyCache = Object.values(instanceKeyCache);
    intersects = raycaster.intersectObjects(instanceKeyCache, true);
    if (instanceKeyCache.length > 0 && intersects.length > 0) {
        // start to count time consumed. 
        timeCounter.maniStart = moment();
        if(INTERSECT_OBJ){
            if(intersects[0].object.parent.userData.key !== INTERSECT_OBJ.userData.key){
                if(pressedKeys[16]){// entering group transformation mode: 
                    addToGTRANS(toSceneObj(intersects[0].object.parent));
                    return; 
                }else{
                    releaseGTRANSChildrens();
                    claimControlObject3D(INTERSECT_OBJ.userData.key, true);
                    synchronize_json_object(INTERSECT_OBJ);
                }
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
        INTERSECT_OBJ = toSceneObj(intersects[0].object);
        // INTERSECT_OBJ = intersects[0].object.parent; //currentRoomId = INTERSECT_OBJ.userData.roomId;
        setNewIntersectObj(event);
        menu.style.left = (event.clientX - 63) + "px";
        menu.style.top = (event.clientY - 63) + "px";
        if (INTERSECT_WALL != undefined)
            unselectWall();
        return;
    }else{
        cancelClickingObject3D();
        // return; // if you want to disable movable wall, just uncomment this line. 
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
    updateTimerTab();
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
                'scale': [1,1,1],
                'format': INSERT_OBJ.format,
                'startState': INSERT_OBJ.status
            }
        );
        scene.remove(scene.getObjectByName(INSERT_NAME));
        applyLayoutViewAdjust();
        timeCounter.add += moment.duration(moment().diff(timeCounter.addStart)).asSeconds();
        return;
    }
    if (On_MOVE) {
        On_MOVE = false;
        synchronize_json_object(INTERSECT_OBJ);
        applyLayoutViewAdjust();
        timeCounter.move += moment.duration(moment().diff(timeCounter.moveStart)).asSeconds();
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
        synchronize_json_object(INTERSECT_OBJ);
        synchronize_coherentGroup();
        CGSERIES_GROUP.clear();
        applyLayoutViewAdjust();
        timeCounter.cgs += moment.duration(moment().diff(timeCounter.cgsStart)).asSeconds();
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
        timeCounter.rotate += moment.duration(moment().diff(timeCounter.rotateStart)).asSeconds();
        if(animaRecord_Mode){
            let index = INTERSECT_OBJ.userData.json.sforder;
            let a = currentSeqs[index][0].at(-1);
            a.r2 = INTERSECT_OBJ.rotation.y;
            a.t[1] = a.t[0]+1;
        }
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
    updateTimerTab();
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
    instanceKeyCache = Object.values(instanceKeyCache).concat(manager.renderManager.newWallCache);
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
    if(manager.renderManager.islod){
        outlinePass.selectedObjects = [];
    }
    else if(instanceKeyCache.length > 0 && intersects.length > 0 && INTERSECT_OBJ === undefined && instanceKeyCache.includes(toSceneObj(intersects[0].object.parent))) {
        outlinePass.selectedObjects = [toSceneObj(intersects[0].object.parent), GTRANS_GROUP];
    }else{
        outlinePass.selectedObjects = [GTRANS_GROUP]
    }  
    // currentMovedTimeStamp = moment();
    tf.engine().startScope();
    if(On_ADD && INSERT_OBJ.modelId in objectCache && INSERT_OBJ.object3d !== undefined){
        scene.remove(scene.getObjectByName(INSERT_NAME)); 
        if(intersects.length > 0){
            let ip = intersects[0].point
            INSERT_OBJ.object3d.name = INSERT_NAME;
            INSERT_OBJ.object3d.position.set(ip.x, ip.y, ip.z);
            INSERT_OBJ.object3d.rotation.set(0, 0, 0, 'XYZ');
            if(trafficFlowObjList.includes(INSERT_OBJ.modelId)){
                let x = 0.9 / (INSERT_OBJ.object3d.boundingBox.max.x-INSERT_OBJ.object3d.boundingBox.min.x);
                let z = 0.45 / (INSERT_OBJ.object3d.boundingBox.max.z-INSERT_OBJ.object3d.boundingBox.min.z);
                INSERT_OBJ.object3d.scale.set(x, x, z);
            }else{
                INSERT_OBJ.object3d.scale.set(1, 1, 1);
            }
            if(INSERT_OBJ.status !== undefined && INSERT_OBJ.format === 'glb'){
                actionSet(INSERT_OBJ.object3d, INSERT_OBJ.status)
            }
            scene.add(INSERT_OBJ.object3d)
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
        mouse.lastOrient = mouse.lastOrient + (rtt_nxt.angle() - rtt_pre.angle());
        let resOri = mouse.lastOrient;
        let angle = (mouse.lastOrient + (rtt_nxt.angle() - rtt_pre.angle())) % (Math.PI/2);
        if(Math.abs(Math.PI/2 - angle) < Math.PI / 16){
            resOri += Math.PI/2 - angle;
        }else if(Math.abs(angle) < Math.PI / 16){
            resOri -= angle;
        }

        let resDir = new THREE.Vector2(Math.sin(resOri), Math.cos(resOri));
        let oSet = Object.values(manager.renderManager.instanceKeyCache).filter(d => d.userData.key !== INTERSECT_OBJ.userData.key);
        if(oSet.length > 0 && pressedKeys[17]){
            let closestDir = oSet.map(d => new THREE.Vector2(d.position.x - INTERSECT_OBJ.position.x, d.position.z - INTERSECT_OBJ.position.z).normalize())
            .reduce(function(prev, curr) {
                return (curr.dot(resDir) > prev.dot(resDir) ? curr : prev);
            });
            if(closestDir.dot(resDir) >= 0.975){
                resOri = Math.atan2(closestDir.x, closestDir.y);
            }
        }
        
        transformObject3DOnly(INTERSECT_OBJ.userData.key, [
            INTERSECT_OBJ.rotation.x, 
            resOri, 
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
    let GTRANSList = releaseGTRANSChildrens();
    if (MAIN_OBJ != undefined && INTERSECT_OBJ.uuid == MAIN_OBJ.uuid) {
        MAIN_OBJ = undefined;
        $("#mainObjDiv").text("Main Object: None");
    }
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
    GTRANSList.forEach(k => {
        removeObjectByUUID(k);
    })
    INTERSECT_OBJ = undefined;
    timeCounter.remove += moment.duration(moment().diff(timeCounter.maniStart)).asSeconds();
    timeCounter.maniStart = moment();
    updateTimerTab();
}

const onAddOff = function(){
    scenecanvas.style.cursor = "auto";
    scene.remove(scene.getObjectByName(INSERT_NAME)); 
    On_ADD = false; 
    timeCounter.add += moment.duration(moment().diff(timeCounter.addStart)).asSeconds();
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
    }if (On_CGSeries) {
        On_CGSeries = false;
        synchronize_json_object(INTERSECT_OBJ);
        CGSERIES_GROUP.clear();
        timeCounter.cgs += moment.duration(moment().diff(timeCounter.cgsStart)).asSeconds();
        return;
    }
    updateTimerTab();
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
    if(mode == 'position'){
        timeCounter.move += moment.duration(moment().diff(timeCounter.maniStart)).asSeconds();
    }else if(mode == 'rotation'){
        timeCounter.rotate += moment.duration(moment().diff(timeCounter.maniStart)).asSeconds();
    }else if(mode == 'scale'){
        timeCounter.scale += moment.duration(moment().diff(timeCounter.maniStart)).asSeconds();
    }
    timeCounter.maniStart = moment();
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
    let ctrlScaleX = datgui_intersectfolder.add(t.scale, 'x', 0.001, 3.0); 
    ctrlScaleX.domElement.parentElement.getElementsByClassName('property-name')[0].textContent = 'Scale-X';
    let ctrlScaleY = datgui_intersectfolder.add(t.scale, 'y', 0.001, 3.0); 
    ctrlScaleY.domElement.parentElement.getElementsByClassName('property-name')[0].textContent = 'Scale-Y';
    let ctrlScaleZ = datgui_intersectfolder.add(t.scale, 'z', 0.001, 3.0); 
    ctrlScaleZ.domElement.parentElement.getElementsByClassName('property-name')[0].textContent = 'Scale-Z';
    
    let ctrlOrient = datgui_intersectfolder.add(t.rotation, 'y', -3.15, 3.15, 0.01); 
    ctrlOrient.domElement.parentElement.getElementsByClassName('property-name')[0].textContent = 'Orient';

    let rbb = manager.renderManager.scene_json.rooms[objmesh.userData.roomId].bbox; 
    let ctrlPosX = datgui_intersectfolder.add(t.position, 'x', rbb.min[0], rbb.max[0]); 
    ctrlPosX.domElement.parentElement.getElementsByClassName('property-name')[0].textContent = 'Pos-X';
    let ctrlPosY = datgui_intersectfolder.add(t.position, 'y', 0, rbb.max[1]); 
    ctrlPosY.domElement.parentElement.getElementsByClassName('property-name')[0].textContent = 'Pos-Y';
    let ctrlPosZ = datgui_intersectfolder.add(t.position, 'z', rbb.min[2], rbb.max[2]); 
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
    timeCounter.totalStart = moment();
    $("#operationFuture").click(refreshSceneFutureRoomTypes);
    $("#operationTimer").click(function(){
        timeCounter.total += moment.duration(moment().diff(timeCounter.totalStart)).asSeconds();
        updateTimerTab();
        console.log(`
        timeCounter.navigate - ${timeCounter.navigate}\r\n
        timeCounter.add - ${timeCounter.add}\r\n
        timeCounter.remove - ${timeCounter.remove}\r\n
        timeCounter.move - ${timeCounter.move}\r\n
        timeCounter.rotate - ${timeCounter.rotate}\r\n
        timeCounter.scale - ${timeCounter.scale}\r\n
        timeCounter.cgs - ${timeCounter.cgs}\r\n
        timeCounter.total - ${timeCounter.total}
        `);
        $.ajax({
            type: "POST",
            contentType: "application/json; charset=utf-8",
            url: `/clickTimer`,
            async: false,
            data: JSON.stringify({methodName: $("#nameOSR").val(), usern: $("#userOSR").val(), homeType:$("#searchinput").val(), timeC: timeCounter, json: getDownloadSceneJson()}),
            success: function (msg) {
                alert(msg);
            }
        });
        timeCounter.navigate = 0;
        timeCounter.move = 0;
        timeCounter.rotate = 0;
        timeCounter.scale = 0;
        timeCounter.cgs = 0;
        timeCounter.total = 0;
        timeCounter.add = 0;
        timeCounter.remove = 0;
        timeCounter.clicks = 0;
        timeCounter.totalStart = moment();
    });
    document.addEventListener('click', function(){timeCounter.clicks+=1;});
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
                if(['Ceiling Lamp', 'Pendant Lamp', 'Wall Lamp', 'wall_lamp'].includes(object3d.userData.coarseSemantic)){
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
                if(['Ceiling Lamp', 'Pendant Lamp', 'wall_lamp'].includes(object3d.userData.coarseSemantic)){
                    object3d.remove(object3d.getObjectByName(SEMANTIC_POINTLIGHT));
                }
            });
        }
    });
    $("#animaRecord_button").click(function(){
        if(currentRoomId === undefined){
            return;
        }
        let button = document.getElementById("animaRecord_button");
        animaRecord_Mode = !animaRecord_Mode;
        if(animaRecord_Mode){
            currentSeqs = [...Array(manager.renderManager.scene_json.rooms[currentRoomId].objList.length)].map(e => [[]]);
            for(let i = 0; i < manager.renderManager.scene_json.rooms[currentRoomId].objList.length; i++){
                manager.renderManager.scene_json.rooms[currentRoomId].objList[i].sforder = i;
            }
            button.style.backgroundColor = '#9400D3';
        }else{
            button.style.backgroundColor = 'transparent';
        }
    });    
    $("#useNewWallCheckBox").prop('checked', USE_NEW_WALL)
    $("#useNewWallCheckBox").click(() => {
        window.sessionStorage.setItem('NotUseNewWall', USE_NEW_WALL)
        USE_NEW_WALL = !USE_NEW_WALL;
        console.log('clicked USE_NEW_WALL', USE_NEW_WALL);
        manager.renderManager.refresh_scene(manager.renderManager.scene_json, false);
    })
    $("#lodCheckBox").click(() => {
        manager.renderManager.islod = $("#lodCheckBox").prop('checked');
        manager.renderManager.scene_json.islod = $("#lodCheckBox").prop('checked');
        manager.renderManager.refresh_scene(manager.renderManager.scene_json, false);
    })
    initAttributes();

    $("#usercommitchange_button").click(() => {
        username = $("#username").val();
        alipay = $("#alipay").val();
        series = $("#series").val();
        if (username == "") {
            alert("请填写支付宝用户名");
            return;
        }
        if (alipay == "") {
            alert("请填写支付宝账号");
            return;
        }
        if (series == "") {
            alert("请填写风格系列名");
            return;
        }

        if (MAIN_OBJ != undefined) {
            let mainobjexists = false;
            for (let obj of manager.renderManager.scene_json.rooms[0].objList) {
                if (obj.modelId == MAIN_OBJ.userData.modelId) mainobjexists = true;
            }
            if (!mainobjexists) {
                MAIN_OBJ = undefined;
                $("#mainObjDiv").text("Main Object: None");
            }
        }
        if (MAIN_OBJ == undefined) {
            $('<div class="alert alert-danger">请点亮主物体上的小旗子按钮</div>')
            .insertBefore('#mainObjDiv').delay(5000).fadeOut(()=>{
                $(this).remove();
            });
            alert("请选择主物体");
            return;
        }
        
        const regex = /^([\u3400-\u4DBF\u4E00-\u9FFF_\-a-zA-Z0-9]){1,30}$/;
        if (regex.test(username)) {
            $.ajax({
                type: "POST",
                contentType: "application/json; charset=utf-8",
                url: `/usercommitchange/${username}`,
                data: JSON.stringify({mainobj: MAIN_OBJ.userData.modelId, series: series, alipay: alipay, username: username, json: getDownloadSceneJson()}),
                success: function (msg) {
                    let s = msg.split(' ');
                    $('#commitSuccessMessage').html(`您的提交已收到：${s[1]}<br/>提交次数：${s[0]}`);
                    $('#commitSuccessModal').modal('show');
                    let mainObjId = MAIN_OBJ.userData.modelId;
                    if (mainObjId in USED_OBJ_LIST) {
                        for (let obj of manager.renderManager.scene_json.rooms[0].objList) {
                            if (!USED_OBJ_LIST[mainObjId].includes(obj.modelId))
                                USED_OBJ_LIST[mainObjId].push(obj.modelId);
                        }
                    } else {
                        USED_OBJ_LIST[mainObjId] = [];
                        for (let obj of manager.renderManager.scene_json.rooms[0].objList) {
                            if (!USED_OBJ_LIST[mainObjId].includes(obj.modelId))
                                USED_OBJ_LIST[mainObjId].push(obj.modelId);
                        }
                    }
                    $('#usedObjDiv').text(`Used Object: ${USED_OBJ_LIST[mainObjId].filter((v, idx)=>{ return v != mainObjId}).join(';')}`)
                    window.sessionStorage.setItem('UsedObject', JSON.stringify(USED_OBJ_LIST));
                }
            });
        }
    });

    const tmpPriorClick = function(){
        $.ajax({
            type: "POST",
            contentType: "application/json; charset=utf-8",
            url: `/prior_catagory`,
            success: function (data) {
                searchResults = JSON.parse(data);
                floorPlanMapping.clear();
                while (osrCatalogItems.firstChild) {
                    osrCatalogItems.firstChild.remove();
                }
                searchResults.forEach(function (item) {
                    let iDiv = document.createElement('div');
                    let ip = document.createElement('p'); ip.style.color = 'black'; ip.style.fontSize = '15px'; ip.innerHTML = "(" + item.le + "-" + item.leng + ") " + item.mainObjects[0] + "%";
                    let up = document.createElement('p');
                    if(item.mainObjects.length == 2){
                        up.style.position = 'absolute'; up.style.bottom = '0px'; up.style.color = 'black'; up.style.fontSize = '15px'; up.innerHTML = item.mainObjects[1] + "%";
                    }
                    let image = new Image();
                    image.onload = function(){
                        iDiv.style.width = `${$(window).width() * 0.10}px`;
                        iDiv.style.height = `${$(window).width() * 0.10 / (image.width / image.height)}px`;
                    };
                    image.src = `/catimgs/${item.identifier}`;
                    iDiv.className = "mapping catalogItem";
                    iDiv.style.backgroundImage = `url(/catimgs/${item.identifier})`;
                    iDiv.style.backgroundSize = '100% 100%';
                    iDiv.style.visibility = 'visible';
                    iDiv.addEventListener('contextmenu', mappingHover);
                    iDiv.addEventListener('mouseout', mappingLeave);
                    iDiv.addEventListener('click', priorcatagoryClickMiddle);
                    iDiv.classList.add('tiler'); iDiv.appendChild(ip); if(item.mainObjects.length == 2){ iDiv.appendChild(up); }
                    osrCatalogItems.appendChild(iDiv);
                    $(iDiv).data('meta', item);
                    floorPlanMapping.set(item.identifier, image);
                });
                Splitting({
                    target: '.tiler',
                    by: 'cells',
                    rows: nrs,
                    columns: ncs,
                    image: true
                });
                $('.tiler .cell-grid .cell').each(function(index){
                    let meta = $(this).parent().parent().data("meta");
                    $(this).parent().attr('id', `grids-${meta.identifier}`);
                    $(this).attr('id', `grid-${meta.identifier}`);
                });
            }
        });
    };

    $("#priorsearchfullbtn").click(() => {
        tmpPriorClick();
    });

    let priorcatagoryClickMiddle = function(e){
        floorPlanMapping.clear();
        while (osrCatalogItems.firstChild) osrCatalogItems.firstChild.remove();
        let iDiv = document.createElement('div');
        let image = new Image();
        image.onload = function(){
            iDiv.style.width = `${$(window).width() * 0.10}px`;
            iDiv.style.height = `${$(window).width() * 0.10 / (image.width / image.height)}px`;
        };
        image.src = `/catimgs/back`;//`/catimgs/${$(e.target).data("meta").identifier}`;//
        iDiv.className = "mapping catalogItem";
        iDiv.style.backgroundImage = `url(/catimgs/back)`;//`url(/catimgs/${$(e.target).data("meta").identifier})`;//
        iDiv.style.backgroundSize = '100% 100%';
        iDiv.style.visibility = 'visible';
        osrCatalogItems.appendChild(iDiv);
        iDiv.addEventListener('click', tmpPriorClick);
        $(iDiv).data('meta', $(e.target).data("meta"));

        $.ajax({
            type: "POST",
            contentType: "application/json; charset=utf-8",
            url: `/catagory_prior_middle/${$(e.target).data("meta").identifier}`,
            success: function (data) {
                searchResults = JSON.parse(data);
                searchResults.forEach(function (item) {
                    let iDiv = document.createElement('div');
                    let ip = document.createElement('p'); ip.style.color = 'black'; ip.style.fontSize = '15px'; ip.innerHTML = item.leng + ' imgs';
                    let image = new Image();
                    image.onload = function(){
                        iDiv.style.width = `${$(window).width() * 0.10}px`;
                        iDiv.style.height = `${$(window).width() * 0.10 / (image.width / image.height)}px`;
                    };
                    image.src = `/ylimgs/${item.identifier}`;
                    iDiv.className = "mapping catalogItem";
                    iDiv.style.backgroundImage = `url(/ylimgs/${item.identifier})`;
                    iDiv.style.backgroundSize = '100% 100%';
                    iDiv.style.visibility = 'visible';
                    $(iDiv).data('meta', item);
                    iDiv.addEventListener('contextmenu', mappingHover);
                    iDiv.addEventListener('mouseout', mappingLeave);
                    iDiv.addEventListener('click', priorcatagoryClick);
                    iDiv.classList.add('tiler'); iDiv.appendChild(ip);
                    osrCatalogItems.appendChild(iDiv);
                    floorPlanMapping.set(item.identifier, image);
                });
                Splitting({
                    target: '.tiler',
                    by: 'cells',
                    rows: nrs,
                    columns: ncs,
                    image: true
                });
                $('.tiler .cell-grid .cell').each(function(index){
                    let meta = $(this).parent().parent().data("meta");
                    $(this).parent().attr('id', `grids-${meta.identifier}`);
                    $(this).attr('id', `grid-${meta.identifier}`);
                })
            }
        });
    };

    let priorcatagoryClick = function(e){
        floorPlanMapping.clear();
        while (osrCatalogItems.firstChild) osrCatalogItems.firstChild.remove();
        let iDiv = document.createElement('div');
        let image = new Image();
        image.onload = function(){
            iDiv.style.width = `${$(window).width() * 0.10}px`;
            iDiv.style.height = `${$(window).width() * 0.10 / (image.width / image.height)}px`;
        };
        image.src = `/catimgs/back`;//`/ylimgs/${$(e.target).data("meta").identifier}`;//
        iDiv.className = "mapping catalogItem";
        iDiv.id = `grid order 0`;
        iDiv.style.backgroundImage = `url(/catimgs/back)`;//`url(/ylimgs/${$(e.target).data("meta").identifier})`;//
        iDiv.style.backgroundSize = '100% 100%';
        iDiv.style.visibility = 'visible';
        osrCatalogItems.appendChild(iDiv);
        let newMeta = {};
        newMeta.identifier = $(e.target).data("meta").mother;
        newMeta.img = $(e.target).data("meta").mother + ".png";
        $(iDiv).data('meta', newMeta);
        iDiv.addEventListener('click', priorcatagoryClickMiddle);
        
        $.ajax({
            type: "POST",
            contentType: "application/json; charset=utf-8",
            url: `/catagory_prior/${$(e.target).data("meta").mother}/${$(e.target).data("meta").identifier}`,
            success: function (data) {
                searchResults = JSON.parse(data);
                searchResults.forEach(function (item) {
                    let iDiv = document.createElement('div');
                    let image = new Image();
                    image.onload = function(){
                        iDiv.style.width = `${$(window).width() * 0.10}px`;
                        iDiv.style.height = `${$(window).width() * 0.10 / (image.width / image.height)}px`;
                    };
                    image.src = `/ylimgs/${item.identifier}`;
                    iDiv.className = "mapping catalogItem";
                    iDiv.id = `grid order ${item.priorMeta.order}`;
                    iDiv.style.backgroundImage = `url(/ylimgs/${item.identifier})`;
                    iDiv.style.backgroundSize = '100% 100%';
                    iDiv.style.visibility = 'visible';
                    $(iDiv).data('meta', item);
                    iDiv.addEventListener('contextmenu', mappingHover);
                    iDiv.addEventListener('mouseout', mappingLeave);
                    iDiv.addEventListener('mouseenter', priorHover);
                    iDiv.addEventListener('click', priorClick);
                    iDiv.classList.add('tiler');
                    osrCatalogItems.appendChild(iDiv);
                    floorPlanMapping.set(item.identifier, image);
                });
                Splitting({
                    target: '.tiler',
                    by: 'cells',
                    rows: nrs,
                    columns: ncs,
                    image: true
                });
                $('.tiler .cell-grid .cell').each(function(index){
                    let meta = $(this).parent().parent().data("meta");
                    $(this).parent().attr('id', `grids-${meta.identifier}`);
                    $(this).attr('id', `grid-${meta.identifier}`);
                })
            }
        });
    };

    $("#priorsearchbtn").click(() => {
        if(INTERSECT_OBJ == null){
            alert("blankly recommendation is not allowed. Please select an object then search the prior about it.");
            return;
        }

        $.ajax({
            type: "POST",
            contentType: "application/json; charset=utf-8",
            url: `/usersearchOSR`,
            data: JSON.stringify({
                interjson: INTERSECT_OBJ.userData.json,
                json: getDownloadSceneJson()}),
            success: function (data) {
                aaa = JSON.parse(data);
                while (osrCatalogItems.firstChild) osrCatalogItems.firstChild.remove();
                aaa.forEach(function (item) {
                    let iDiv = document.createElement('div');
                    let image = new Image();
                    image.onload = function(){
                        iDiv.style.width = `${$(window).width() * 0.10}px`;
                        iDiv.style.height = `${$(window).width() * 0.10 / (image.width / image.height)}px`;
                    };
                    image.src = `/ylimgs/${item.priorMeta.identifier}`;
                    iDiv.className = "mapping catalogItem";
                    iDiv.style.backgroundImage = `url(/ylimgs/${item.priorMeta.identifier})`;
                    iDiv.style.backgroundSize = '100% 100%';
                    iDiv.style.visibility = 'visible';
                    iDiv.addEventListener('click', priorClick);
                    osrCatalogItems.appendChild(iDiv);
                    $(iDiv).data('meta', item);
                    //alert(item.priorMeta.identifier);
                });
                //alert(data);
            }
        });
        
    });

    let queryAABB = function(attachedObjId, currentState){
        var bbb = 0;
        $.ajax({
            type: "GET",
            contentType: "application/json; charset=utf-8",
            url: `queryAABB/${attachedObjId}/${currentState}`,
            async: false,
            success: function (data) {
                var aaa = JSON.parse(data);
                bbb = {"max":{"x":aaa.max[0], "y":aaa.max[0], "z":aaa.max[2] }, "min":{ "x":aaa.min[0], "y":aaa.min[0], "z":aaa.min[2] }};
            }
        });
        //console.log(bbb);
        return bbb;
    }

    let singleObjectBounding = function(itm){
        var realx = itm.objPosX;
        var realz = itm.objPosZ;
        //console.log(realx);
        //console.log(realz);
        //console.log(objectCache[itm.attachedObjId].boundingBox);
        var objBbox = objectCache[itm.attachedObjId].boundingBox;
        if(itm.currentState && isNaN(parseInt(itm.attachedObjId))) objBbox = queryAABB(itm.attachedObjId, itm.currentState);
        if(itm.attachedObjId == "desk2shelf") console.log(objBbox);
        var scaledBbox = {"max":{"x":itm.objScaleX * objBbox.max.x, "y":itm.objScaleY * objBbox.max.y, "z":itm.objScaleZ * objBbox.max.z}, "min":{"x":itm.objScaleX * objBbox.min.x, "y":itm.objScaleY * objBbox.min.y, "z":itm.objScaleZ * objBbox.min.z}}
        objBbox = scaledBbox;
        if(itm.attachedObjId == "desk2shelf") console.log(objBbox);
        var phi = itm.objOriY;
        var maxX = objBbox.max.x;
        var minX = objBbox.min.x;
        var maxZ = objBbox.max.z;
        var minZ = objBbox.min.z;
        while(phi < 0.00) phi += 6.2832
        while(phi >= 1.5708){
            phi -= 1.5708
            var aX = maxZ;
            var iZ =-maxX;
            var iX = minZ;
            var aZ =-minX;
            maxX = aX;
            maxZ = aZ;
            minX = iX;
            minZ = iZ;
        }

        //console.log(phi);
        var cosphi = Math.cos(phi);
        var sinphi = Math.sin(phi);
        var realMaxX = maxX * cosphi + maxZ * sinphi + realx;
        var realMinZ =-maxX * sinphi + minZ * cosphi + realz;
        var realMaxZ = maxZ * cosphi - minX * sinphi + realz;
        var realMinX = minZ * sinphi + minX * cosphi + realx;
        return {"max":{"x":realMaxX, "z":realMaxZ}, "min":{"x":realMinX, "z":realMinZ}};
    }

    let moveSinglePriorBbox = function(itm, currentLocation){
        if(itm.attachedObjId == "desk2shelf") console.log("desk2shelf");
        var priorBbox = singleObjectBounding(itm);
        console.log(priorBbox);
        if(itm.attachedObjId == "desk2shelf") console.log([itm.objPosX, itm.objPosZ, itm.objOriY]);
        var rbox = rotatePriorBbox(priorBbox, currentLocation[1]);
        console.log(rbox);
        var tbox = {"max":{"x":rbox.max.x + currentLocation[0][0], "z":rbox.max.z + currentLocation[0][2]}, "min":{"x":rbox.min.x + currentLocation[0][0], "z":rbox.min.z + currentLocation[0][2]}};
        console.log(tbox);
        return tbox;//currentLocation[0][0];  //currentLocation[0][2]
    }

    let singleObjectRelativeLocation = function(itm, mainTrans){
        var theta = mainTrans[1];//INTERSECT_OBJ.rotation.y;
        var costheta = Math.cos(theta);
        var sintheta = Math.sin(theta);

        var realx = itm.objPosX * costheta + itm.objPosZ * sintheta;
        var realz =-itm.objPosX * sintheta + itm.objPosZ * costheta;
            
        return [realx, realz];
    };

    let singleObjectInformation = function(itm){
        var theta = INTERSECT_OBJ.rotation.y;
        var costheta = Math.cos(theta);
        var sintheta = Math.sin(theta);

        var realx = itm.objPosX * costheta + itm.objPosZ * sintheta;
        var realz =-itm.objPosX * sintheta + itm.objPosZ * costheta;
            
        //console.log(objectCache[itm.attachedObjId].boundingBox);
        var objBbox = objectCache[itm.attachedObjId].boundingBox;
        if(itm.currentState && isNaN(parseInt(itm.attachedObjId))) objBbox = queryAABB(itm.attachedObjId, itm.currentState);
        //console.log(manager.renderManager.scene_json['rooms'][INTERSECT_OBJ.userData.json.roomId]);
        var roomBbox = manager.renderManager.scene_json['rooms'][INTERSECT_OBJ.userData.json.roomId].roomShapeBBox;

        var phi = INTERSECT_OBJ.rotation.y + itm.objOriY;
        var maxX = objBbox.max.x;
        var minX = objBbox.min.x;
        var maxZ = objBbox.max.z;
        var minZ = objBbox.min.z;
        while(phi < 0.00) phi += 6.2832
        while(phi >= 1.5708){
            phi -= 1.5708
            var aX = maxZ;
            var iZ =-maxX;
            var iX = minZ;
            var aZ =-minX;
            maxX = aX;
            maxZ = aZ;
            minX = iX;
            minZ = iZ;
        }

        //console.log(phi);
        var cosphi = Math.cos(phi);
        var sinphi = Math.sin(phi);
        var realMaxX = maxX * cosphi + maxZ * sinphi + INTERSECT_OBJ.position.x + realx;
        var realMinZ =-maxX * sinphi + minZ * cosphi + INTERSECT_OBJ.position.z + realz;
        var realMaxZ = maxZ * cosphi - minX * sinphi + INTERSECT_OBJ.position.z + realz;
        var realMinX = minZ * sinphi + minX * cosphi + INTERSECT_OBJ.position.x + realx;

        var overMaxX = Math.max(realMaxX - roomBbox.max[0], 0.0);
        var overMaxZ = Math.max(realMaxZ - roomBbox.max[1], 0.0);
        var overMinX = Math.min(realMinX - roomBbox.min[0], 0.0);
        var overMinZ = Math.min(realMinZ - roomBbox.min[1], 0.0);

        //console.log(overMaxX, overMaxZ, overMinX, overMinZ);
        return [realx, realz, overMaxX, overMaxZ, overMinX, overMinZ];

    };

    let clearSubsets = function(){
        var child = osrCatalogItems.firstChild;
        var last = osrCatalogItems.lastChild;
        while(child != last) {
            var delChild = child;
            child = child.nextSibling;
            if(delChild.id.match('__subsets')) delChild.remove();
        }
        if(child.id.match('__subsets')) child.remove();
    }

    const priorHover = function(e){
        clearSubsets();
        let iDiv = document.createElement('div');
        let meta = $(e.target).data("meta");
        thisId = meta.priorMeta.identifier + '__subsets';
        if(document.getElementById(thisId)) return;
        iDiv.id = thisId;
        let subsets = meta.priorMeta.subsets;
        //console.log(subsets);
        let subsetLen = subsets.length;
        if(subsetLen == 0) return;
        subsets.forEach(function(item){
            let jDiv = document.createElement('div');
            let image = new Image();
            image.onload = function(){
                jDiv.style.width = `${$(window).width() * 0.10}px`;
                jDiv.style.height = `${$(window).width() * 0.10 / (image.width / image.height)}px`;
            };
            image.src = `/ylimgs/${meta.priorMeta.identifier}____${item}`;
            jDiv.className = "mapping catalogItem";
            jDiv.style.backgroundImage = `url(/ylimgs/${meta.priorMeta.identifier}____${item})`;
            jDiv.style.backgroundSize = '100% 100%';
            jDiv.style.visibility = 'visible';
            jDiv.addEventListener('click', priorClick);
            thisMeta = JSON.parse(JSON.stringify(meta)); //deep copy
            thisGtrans = [];
            thisMeta.gtrans.forEach(function(itm){
                if(itm.attachedObjId != item) thisGtrans = thisGtrans.concat([itm]);
            });
            thisMeta.gtrans = thisGtrans;
            thisMeta.identifier = `${meta.priorMeta.identifier}____${item}`;
            thisMeta.priorMeta.identifier = `${meta.priorMeta.identifier}____${item}`;
            thisMeta.priorMeta.img = `${meta.priorMeta.identifier}____${item}.png`;
            jDiv.addEventListener('mouseover', mappingHover);
            jDiv.addEventListener('mouseout', mappingLeave);
            jDiv.classList.add('tiler');
            iDiv.appendChild(jDiv);
            $(jDiv).data('meta', thisMeta);
            floorPlanMapping.set(thisMeta.identifier, image);
        });

        iDiv.style.position = 'absolute';
        let order = meta.priorMeta.order;
        let startOrder = 0;
        if(order < 4){//?????????
            if(subsetLen == 1) startOrder = order + 2;
            else{
                startOrder = order + 2 - (order % 2);
            }
        }
        else{
            if(subsetLen == 1) startOrder = order - 2;
            else{
                startOrder = order - 2 - (order%2);
                if(subsetLen > 2) startOrder -= 2;
                if(subsetLen > 4) startOrder -= 2;
            }
        }
        startDiv = document.getElementById(`grid order ${startOrder}`);
        if(order < 4) iDiv.style.top = startDiv.offsetTop - 8;//
        else iDiv.style.top = startDiv.offsetTop + 8;//
        iDiv.style.left = startDiv.offsetLeft;
        iDiv.style.visibility = 'visible';
        iDiv.style.backgroundColor = 'skyblue';
        iDiv.addEventListener('mouseleave', priorLeave);
        osrCatalogItems.appendChild(iDiv);

        Splitting({
            target: '.tiler',
            by: 'cells',
            rows: nrs,
            columns: ncs,
            image: true
        });
        $('.tiler .cell-grid .cell').each(function(index){
            let meta = $(this).parent().parent().data("meta");
            $(this).parent().attr('id', `grids-${meta.identifier}`);
            $(this).attr('id', `grid-${meta.identifier}`);
        });
    }

    const priorLeave = function(e){
        while (e.target.firstChild) e.target.firstChild.remove();
        e.target.style.visibility = 'invisible';
        e.target.remove();//
    }

    let directionofWindoor = function(room, bbox){
        let center = [(bbox.max[0] + bbox.min[0])/2.0, 0.0, (bbox.max[2] + bbox.min[2])/2.0];
        let result = [0, 0];
        if( (bbox.max[0] - bbox.min[0]) > (bbox.max[2] - bbox.min[2]) ){
            for(var i = 0; i < room.roomShape.length; ++i){
                if(Math.abs(room.roomShape[i][1] - center[2]) < 0.15){
                    if((i == 0) && (Math.abs(room.roomShape[room.roomShape.length-1][1] - center[2]) < 0.15) ) i = room.roomShape.length-1;
                    if(Math.abs(room.roomOrient[i]) < 0.2) result = [[0,1],i];
                    else result = [[0,-1],i];
                    break;
                }
            }
        }
        else{
            for(var i = 0; i < room.roomShape.length; ++i){
                if(Math.abs(room.roomShape[i][0] - center[0]) < 0.15){
                    if((i == 0) && (Math.abs(room.roomShape[room.roomShape.length-1][0] - center[0]) < 0.15) ) i = room.roomShape.length-1;
                    if(room.roomOrient[i] > 0.0) result = [[1, 0],i];
                    else result = [[-1, 0],i];
                    break;
                }
            }
        }
        return result;
    }

    let windoorofRoom = function(room){
        result = {"window":[], "door":[]};
        //console.log(room);
        for(var i = 0; i < room.objList.length; ++i){
            let obj = room.objList[i];
            let bbox = obj.bbox;
            if(obj.coarseSemantic == "door" || obj.coarseSemantic == "Door"){
                if (bbox.max[1] > 0.1){
                    if(!(bbox in result.door)){
                        let t = directionofWindoor(room,bbox);
                        result.door = result.door.concat([[bbox, t[0], t[1]]]);
                    }
                }
            }
            else if(obj.coarseSemantic ==  "window" || obj.coarseSemantic == "Window"){
                if(!(bbox in result.window)){
                    let t = directionofWindoor(room,bbox);
                    result.window = result.window.concat([[bbox, t[0], t[1]]]);
                }
            }
        }
        for(var i = 0; i < room.blockList.length; ++i){
            let block = room.blockList[i];
            let bbox = block.bbox;
            if(block.coarseSemantic == "door" || block.coarseSemantic == "Door"){
                if (bbox.max[1] > 0.1){
                    if(!(bbox in result.door)){
                        let t = directionofWindoor(room,bbox);
                        result.door = result.door.concat([[bbox, t[0], t[1]]]);
                    }
                }
            }
            else if(block.coarseSemantic == "window" || block.coarseSemantic == "Window"){
                if(!(bbox in result.window)){
                    let t = directionofWindoor(room,bbox);
                    result.window = result.window.concat([[bbox, t[0], t[1]]]);
                }
            }
        }
        //console.log(result);
        return result;
    }

    let dirOfMetaWindoor = function(windoor){
        thisDirection = [0, 0];
        if(windoor.direction == "z"){
            if(windoor.objPosZ > 0) thisDirection = [0,-1];
            else thisDirection = [0,1];
        }
        else{
            if(windoor.objPosX > 0) thisDirection = [-1,0];
            else thisDirection = [1,0];
        }
        return thisDirection;
    }

    let rotateFromWindoor = function(metaWindoor, realWindoor){
        var dir1 = dirOfMetaWindoor(metaWindoor);
        //console.log(dir1);
        var OriginalOrient = -metaWindoor.objOriY;
        if(metaWindoor.direction == 'x') OriginalOrient += 1.57;
        var locX = - metaWindoor.objPosX;
        var locZ = - metaWindoor.objPosZ;
        var dir2 = realWindoor[1];
        var realCenter = [(realWindoor[0].max[0] + realWindoor[0].min[0])/2.0, 0.0, (realWindoor[0].max[2] + realWindoor[0].min[2])/2.0];
        //console.log(realCenter);console.log(dir1);console.log(dir2);console.log(locX);console.log(locZ);
        var translate = [0, 0, 0];
        var lst = [[0, 1], [1, 0], [0,-1], [-1,0]];
        var i = 0; for(; i < 4; ++i) if(lst[i][0] == dir1[0] && lst[i][1] == dir1[1]) break;
        var j = 0; for(; j < 4; ++j) if(lst[j][0] == dir2[0] && lst[j][1] == dir2[1]) break;
        var k = (j-i+4)%4;
        if(k == 1){
            translate = [realCenter[0] + locZ, 0.0, realCenter[2] - locX];
            OriginalOrient += Math.PI / 2.0;
        }else if(k == 2){
            translate = [realCenter[0] - locX, 0.0, realCenter[2] - locZ];
            OriginalOrient += Math.PI;
        }else if(k == 3){
            translate = [realCenter[0] - locZ, 0.0, realCenter[2] + locX];
            OriginalOrient -= Math.PI / 2.0;
        }else{
            translate = [realCenter[0] + locX, 0.0, realCenter[2] + locZ];
        }
        console.log(translate);
        return [translate, OriginalOrient, realWindoor[2]];//, thetaToDir(OriginalOrient, 0.2)];
    }

    let thetaToDir = function(theta, bound = 0.001){
        while(theta > Math.PI) theta -= 2*Math.PI;
        while(theta <-Math.PI) theta += 2*Math.PI;
        if(Math.abs(theta) < bound) return [0,1];
        else if(Math.abs(Math.abs(theta) - Math.PI) < bound) return [0,-1];
        else if(Math.abs(theta - Math.PI / 2.0) < bound) return [ 1,0];
        else if(Math.abs(theta + Math.PI / 2.0) < bound) return [-1,0];
        else console.log("error theta");
    }

    let wallInformDict = function(room, idx){
        let endIdx = (idx+1)%(room.roomShape.length);
        let dir = thetaToDir(room.roomOrient[idx]);
        let maxX = Math.max(room.roomShape[idx][0], room.roomShape[endIdx][0]);
        let minX = Math.min(room.roomShape[idx][0], room.roomShape[endIdx][0]);
        let maxZ = Math.max(room.roomShape[idx][1], room.roomShape[endIdx][1]);
        let minZ = Math.min(room.roomShape[idx][1], room.roomShape[endIdx][1]);
        let centerX = (room.roomShape[idx][0] + room.roomShape[endIdx][0]) / 2.0;
        let centerZ = (room.roomShape[idx][1] + room.roomShape[endIdx][1]) / 2.0;
        return {"dir": dir, "maxX": maxX, "maxZ": maxZ, "minX": minX, "minZ":minZ, "centerX":centerX, "centerZ":centerZ};
    }

    let rotatePriorBbox = function(priorBbox, spin){
        var t = spin;
        var result = priorBbox;
        while(t <-Math.PI) t += 2*Math.PI;
        while(t > Math.PI) t -= 2*Math.PI;
        if(Math.abs(t - Math.PI / 2.0) < 0.1){
            result = {"min":{"x":priorBbox.min.z, "z": -priorBbox.max.x},"max":{"x":priorBbox.max.z, "z":-priorBbox.min.x}};
        }
        else if(Math.abs(Math.abs(t) - Math.PI) < 0.1){
            result = {"min":{"x":-priorBbox.max.x, "z": -priorBbox.max.z},"max":{"x":-priorBbox.min.x, "z":-priorBbox.min.z}};
        }
        else if(Math.abs(t + Math.PI / 2.0) < 0.1){
            result = {"min":{"x":-priorBbox.max.z, "z": priorBbox.min.x},"max":{"x":-priorBbox.min.z, "z":priorBbox.max.x}};
        }
        else if(Math.abs(t) > 0.1){
            console.log(`error spin ${spin}`)
        }
        return result;
    }

    let compareCurrentLocation = function(currentLocation, currentLocationTmp, xscan, zscan, priorBbox){ 
        var tmpX = currentLocationTmp[0][0]; var spanZ = [];
        var tmpZ = currentLocationTmp[0][2]; var spanX = [];
        for(var tX in xscan){
            if(tX < tmpX) spanZ = xscan[tX];
            else break;
        }
        for(var tZ in zscan){
            if(tZ < tmpZ) spanX = zscan[tZ];
            else break;
        }

        var realPriorBbox = rotatePriorBbox(priorBbox,currentLocationTmp[1]);
        var ratioZ = (Math.max(0.0, spanZ[0] - (realPriorBbox.min.z + tmpZ)) + Math.max(0.0, (realPriorBbox.max.z + tmpZ) - spanZ[1])) / (realPriorBbox.max.z - realPriorBbox.min.z);
        var ratioX = (Math.max(0.0, spanX[0] - (realPriorBbox.min.x + tmpX)) + Math.max(0.0, (realPriorBbox.max.x + tmpX) - spanX[1])) / (realPriorBbox.max.x - realPriorBbox.min.x);
        var ratio = Math.max(ratioX, ratioZ);

        if(currentLocation.length == 0){
            if (ratio < 0.5) return ratio;
            else return -1;
        }
        else {
            if(ratio < currentLocation[3]) return ratio;
            else return -1;
        }
    }

    let scanRoom = function(room){  //console.log("here");
        //从xmin往xmax扫一下房间
        var xscan = {};
        let xmin = room.roomShapeBBox.min[0];
        let xmax = room.roomShapeBBox.max[0];
        //找到xmin的那面墙，
        var i = 0;
        for(; i < room.roomShape.length; ++i){
            if(Math.abs(room.roomShape[i][0] - xmin) < 0.1){
                if((i == 0) && (Math.abs(room.roomShape[room.roomShape.length-1][0] - xmin) < 0.1) ) i = room.roomShape.length-1;
                break;
            }
        }
        var wallAIdx = (i+1)%(room.roomShape.length);
        var wallAInfoDict = wallInformDict(room, wallAIdx);
        var wallBIdx = (i-1+room.roomShape.length)%(room.roomShape.length)
        var wallBInfoDict = wallInformDict(room, wallBIdx);
        //当前x为xmin
        var currX = xmin;
        while(true){
            //对于向前方向：
            while(wallAInfoDict.dir[0] != 0 || wallAInfoDict.maxX < currX + 0.001){ //如果这面墙方向不对或者终点并不晚于currX, 就需要继续找下一面墙，
                wallAIdx = (wallAIdx+1)%(room.roomShape.length); //要求这面墙的终点晚于currX
                wallAInfoDict = wallInformDict(room, wallAIdx);
            }
            //对于向后方向：
            while(wallBInfoDict.dir[0] != 0 || wallBInfoDict.maxX < currX + 0.001){ //如果这面墙方向不对或者终点并不晚于currX, 就需要继续找下一面墙，
                wallBIdx = (wallBIdx-1+room.roomShape.length)%(room.roomShape.length); //要求这面墙的终点晚于currX
                wallBInfoDict = wallInformDict(room, wallBIdx);
            }

            xscan[currX] = [Math.min(wallAInfoDict.maxZ,wallBInfoDict.maxZ),Math.max(wallAInfoDict.minZ,wallBInfoDict.minZ)];
            currX = Math.min(wallAInfoDict.maxX, wallBInfoDict.maxX);
            if(Math.abs(currX - xmax) < 0.0001) {xscan[xmax] = []; break;}
        }


        //从zmin往zmax扫一下房间
        var zscan = {};
        let zmin = room.roomShapeBBox.min[1];
        let zmax = room.roomShapeBBox.max[1];
        //找到zmin的那面墙，
        var i = 0;
        for(; i < room.roomShape.length; ++i){
            if(Math.abs(room.roomShape[i][1] - zmin) < 0.1){
                if((i == 0) && (Math.abs(room.roomShape[room.roomShape.length-1][1] - zmin) < 0.1) ) i = room.roomShape.length-1;
                break;
            }
        }
        var wallAIdx = (i+1)%(room.roomShape.length);
        var wallAInfoDict = wallInformDict(room, wallAIdx);
        var wallBIdx = (i-1+room.roomShape.length)%(room.roomShape.length)
        var wallBInfoDict = wallInformDict(room, wallBIdx);
        //当前x为xmin
        var currZ = zmin;
        while(true){
            //对于向前方向：
            while(wallAInfoDict.dir[1] != 0 || wallAInfoDict.maxZ < currZ + 0.001){ //如果这面墙方向不对或者终点并不晚于currX, 就需要继续找下一面墙，
                wallAIdx = (wallAIdx+1)%(room.roomShape.length); //要求这面墙的终点晚于currX
                wallAInfoDict = wallInformDict(room, wallAIdx);
            }
            //对于向后方向：
            while(wallBInfoDict.dir[1] != 0 || wallBInfoDict.maxZ < currZ + 0.001){ //如果这面墙方向不对或者终点并不晚于currX, 就需要继续找下一面墙，
                wallBIdx = (wallBIdx-1+room.roomShape.length)%(room.roomShape.length); //要求这面墙的终点晚于currX
                wallBInfoDict = wallInformDict(room, wallBIdx);
            }

            zscan[currZ] = [Math.min(wallAInfoDict.maxX,wallBInfoDict.maxX),Math.max(wallAInfoDict.minX,wallBInfoDict.minX)];
            currZ = Math.min(wallAInfoDict.maxZ, wallBInfoDict.maxZ);
            if(Math.abs(currZ - zmax) < 0.0001) {zscan[zmax] = []; break;}
        }

        return [xscan, zscan];
    }

    let calcPriorBbox = function(meta){
        var priorBbox = {"max":{"x":-100.0, "z":-100.0}, "min":{"x":100.0, "z":100.0}};
        var objBbox = objectCache[meta.mainObjId].boundingBox;
        if(meta.state && isNaN(parseInt(meta.mainObjId))) objBbox = queryAABB(meta.mainObjId, meta.state[0].currentState);
        var scl = [1.0, 1.0, 1.0]
        if("scale" in meta){
            scl = [meta.scale[0].objScaleX, meta.scale[0].objScaleY, meta.scale[0].objScaleZ];
        }

        priorBbox.max.x = Math.max(priorBbox.max.x, objBbox.max.x * scl[0]);
        priorBbox.max.z = Math.max(priorBbox.max.z, objBbox.max.z * scl[2]);
        priorBbox.min.x = Math.min(priorBbox.min.x, objBbox.min.x * scl[0]);
        priorBbox.min.z = Math.min(priorBbox.min.z, objBbox.min.z * scl[2]);
        if('gtrans' in meta){
            for(var i = 0; i < meta.gtrans.length; ++i){
                var itm = meta.gtrans[i];
                objBbox = singleObjectBounding(itm);
                //console.log(objBbox);
                priorBbox.max.x = Math.max(priorBbox.max.x, objBbox.max.x);
                priorBbox.max.z = Math.max(priorBbox.max.z, objBbox.max.z);
                priorBbox.min.x = Math.min(priorBbox.min.x, objBbox.min.x);
                priorBbox.min.z = Math.min(priorBbox.min.z, objBbox.min.z);
            }
        }
        return priorBbox;
    }

    let movePriorBbox = function(meta, currentLocation){
        var priorBbox = calcPriorBbox(meta);
        var rbox = rotatePriorBbox(priorBbox, currentLocation[1]);
        var tbox = {"max":{"x":rbox.max.x + currentLocation[0][0], "z":rbox.max.z + currentLocation[0][2]}, "min":{"x":rbox.min.x + currentLocation[0][0], "z":rbox.min.z + currentLocation[0][2]}};
        return tbox;//currentLocation[0][0];  //currentLocation[0][2]
    }

    let mainObjLocation = function(room, meta, xscan, zscan){
        
        var schemes = [];
        var priorBbox = calcPriorBbox(meta);

        var currentLocation = [];
        var roomLengthX = room.roomShapeBBox.max[0] - room.roomShapeBBox.min[0];
        var roomLengthZ = room.roomShapeBBox.max[1] - room.roomShapeBBox.min[1];

        //1, get a prior orientation            2, roughly locate the main object
        //consider window and door; which window? which door?
        console.log(room);
        var WindoorOfRoom = windoorofRoom(room);
        console.log(WindoorOfRoom);
        console.log(meta.priorId);
        console.log(priorBbox);
        console.log(meta.window);
        console.log(meta.door);

        if( ('window' in meta) || ('door' in meta) ){
            if('window' in meta){
                //thisDirection = dirOfMetaWindoor(meta.window[0]);
                //console.log(meta.window[0].direction);
                for(var t = 0; t < WindoorOfRoom.window.length; ++t){
                    //console.log(WindoorOfRoom.window[t]);
                    var currentLocationTmp = rotateFromWindoor(meta.window[0], WindoorOfRoom.window[t]);
                    var res = compareCurrentLocation(currentLocation, currentLocationTmp, xscan, zscan, priorBbox); 
                    if(res > -0.001) currentLocation = currentLocationTmp.concat([res]);
                }
                if(currentLocation.length) schemes = schemes.concat([JSON.parse(JSON.stringify(currentLocation))]);
            } currentLocation = [];
            if(('door' in meta)){//&& (currentLocation.length == 0)){
                //thisDirection = dirOfMetaWindoor(meta.door[0]);
                //console.log(meta.door[0].direction);
                for(var t = 0; t < WindoorOfRoom.door.length; ++t){
                    //console.log(WindoorOfRoom.door[0][1]);
                    var currentLocationTmp = rotateFromWindoor(meta.door[0], WindoorOfRoom.door[t]);
                    var res = compareCurrentLocation(currentLocation, currentLocationTmp, xscan, zscan, priorBbox);
                    if(res > -0.001) currentLocation = currentLocationTmp.concat([res]);
                }
                if(currentLocation.length) schemes = schemes.concat([JSON.parse(JSON.stringify(currentLocation))]);
            }
        }
        console.log(schemes);
        
        //关键就在于找两个侧（房间的某一侧墙，关联关系包围盒的某一侧边界），将他们match
        
        //首先找到包围盒最窄的一侧，我们利用它来决定靠哪一面墙？
        var boundingSign = 0;
        var boundingNearest = priorBbox.max.x;
        var boundingLength  = priorBbox.max.z - priorBbox.min.z;
        if( priorBbox.max.z< boundingNearest) { boundingNearest = priorBbox.max.z; boundingSign = 3; boundingLength = priorBbox.max.x - priorBbox.min.x;}
        if(-priorBbox.min.x< boundingNearest) { boundingNearest =-priorBbox.min.x; boundingSign = 2; boundingLength = priorBbox.max.z - priorBbox.min.z;}
        if(-priorBbox.min.z< boundingNearest) { boundingNearest =-priorBbox.min.z; boundingSign = 1; boundingLength = priorBbox.max.x - priorBbox.min.x;}
        if('wall' in meta){
            //console.log("here"); console.log(meta.priorId); console.log(meta.wall[0].nearestOrient0);
            let t = thetaToDir(meta.wall[0].nearestOrient0, bound = 0.02); console.log(t);
            if((t[0] == 0) && (t[1] == 1)){
                boundingNearest =-priorBbox.min.z; boundingSign = 3; boundingLength = priorBbox.max.x - priorBbox.min.x;
            }else if((t[0] ==-1) && (t[1] == 0)) {
                boundingNearest =-priorBbox.min.x; boundingSign = 2; boundingLength = priorBbox.max.z - priorBbox.min.z;
            }else if((t[0] == 0) && (t[1] ==-1)){
                boundingNearest = priorBbox.max.z; boundingSign = 1; boundingLength = priorBbox.max.x - priorBbox.min.x;
            }else if((t[0] == 1) && (t[1] == 0)){
                boundingNearest = priorBbox.max.x; boundingSign = 0; boundingLength = priorBbox.max.z - priorBbox.min.z;
            }
        }
        
        //从较短一侧的墙开始试一试。首先计算包围盒靠该墙时主物体位置上另一个维度的跨度是多大；移开门范围，看看包围盒在该维度上能否保持在房间的维度跨度以内。如果可以就保留，
            //对墙的长度依次排序
        var wallSigns = [];
        var dirSign = 0, wallLen = 0;
        var currentActualLength = boundingLength;
        //if(Math.abs(room.roomShape[0][1] - room.roomShape[1][1]) < 0.001){ dir = 1; wallLen = Math.abs(room.roomShape[0][0] - room.roomShape[1][0]);}
        //else { dir = 0; wallLen = Math.abs(room.roomShape[0][1] - room.roomShape[1][1]);}
        //wallSigns = [[0, dir, wallLen]];
        for(var i = 0; i < room.roomShape.length; ++i){
            var dir = thetaToDir(room.roomOrient[i]);
            dirSign = dir[1]*dir[1];//????????????????????????????????????????????????????????
            var j = (i+1)%(room.roomShape.length);
            wallLen = Math.abs(room.roomShape[i][1 - dirSign] - room.roomShape[j][1 - dirSign]);  //on the 'dirSign' dimension, the wall's location do not change
            var center = [(room.roomShape[i][0] + room.roomShape[j][0]) / 2.0, (room.roomShape[i][1] + room.roomShape[j][1]) / 2.0];
            var k = 0;
            for(; k < wallSigns.length; ++k){ if(wallSigns[k].wallLength > wallLen) break; }
            var wallInfoDict = {"idx":i, "dirSign":dirSign, "dir":dir, "wallLength":wallLen, "center":center};
            wallSigns.splice(k,0,wallInfoDict); 
        }
        console.log(wallSigns);

            //依次遍历这些墙，
        for(var i = wallSigns.length-1; i >= 0; --i){ console.log(i); console.log(boundingNearest);
            let wallIdx = wallSigns[i].idx;
            let spanDirSign = 1 - wallSigns[i].dirSign; let notSpanDirSign = 1 - spanDirSign;
            let dirSign = wallSigns[i].dir; 
            let center = wallSigns[i].center;
            let wallLen = wallSigns[i].wallLength;
            var span = [center[spanDirSign] - wallLen / 2.0, center[spanDirSign] + wallLen / 2.0];
            if(dirSign[0] == 1 && dirSign[1] == 0){
                let currentX = center[0] + boundingNearest;
                for(var j = wallIdx-1; true; --j){
                    if (j<0) j += room.roomShape.length;
                    var k = (j+1)%room.roomShape.length;
                    if(Math.abs(room.roomShape[j][0] - room.roomShape[k][0]) < 0.001) continue;
                    if((room.roomShape[j][0] + room.roomShape[k][0])/2.0 < center[0]) break;
                    let newDir = thetaToDir(room.roomOrient[j]);
                    let wallZ = room.roomShape[j][1];
                    if(newDir[1] > 0) span[0] = Math.max(span[0],wallZ);
                    else span[1] = Math.min(span[1],wallZ);
                    if(Math.max(room.roomShape[j][0], room.roomShape[k][0]) > currentX) break;
                }
                for(var j = wallIdx+1; true; ++j){
                    if (j >= room.roomShape.length) j -= room.roomShape.length; 
                    var k = (j+1)%room.roomShape.length;
                    if(Math.abs(room.roomShape[j][0] - room.roomShape[k][0]) < 0.001) continue;
                    if((room.roomShape[j][0] + room.roomShape[k][0])/2.0 < center[0]) break;
                    let newDir = thetaToDir(room.roomOrient[j]);
                    let wallZ = room.roomShape[j][1];
                    if(newDir[1] > 0) span[0] = Math.max(span[0],wallZ);
                    else span[1] = Math.min(span[1],wallZ);
                    if(Math.max(room.roomShape[j][0], room.roomShape[k][0]) > currentX) break;
                }
            }
            else if(dirSign[0] == 0 && dirSign[1] == -1){
                let currentZ = center[1] - boundingNearest;
                for(var j = wallIdx-1; true; --j){
                    if (j<0) j += room.roomShape.length;
                    var k = (j+1)%room.roomShape.length;
                    if(Math.abs(room.roomShape[j][1] - room.roomShape[k][1]) < 0.001) continue;
                    if((room.roomShape[j][1] + room.roomShape[k][1])/2.0 > center[1]) break;
                    let newDir = thetaToDir(room.roomOrient[j]);
                    let wallX = room.roomShape[j][0];
                    if(newDir[0] > 0) span[0] = Math.max(span[0],wallX);
                    else span[1] = Math.min(span[1],wallX);
                    if(Math.min(room.roomShape[j][1], room.roomShape[k][1]) < currentZ) break;
                }
                for(var j = wallIdx+1; true; ++j){
                    if (j >= room.roomShape.length) j -= room.roomShape.length; 
                    var k = (j+1)%room.roomShape.length;
                    if(Math.abs(room.roomShape[j][1] - room.roomShape[k][1]) < 0.001) continue;
                    if((room.roomShape[j][1] + room.roomShape[k][1])/2.0 > center[1]) break;
                    let newDir = thetaToDir(room.roomOrient[j]);
                    let wallX = room.roomShape[j][0];
                    if(newDir[0] > 0) span[0] = Math.max(span[0],wallX);
                    else span[1] = Math.min(span[1],wallX);
                    if(Math.min(room.roomShape[j][1], room.roomShape[k][1]) < currentZ) break;
                }
            }
            else if(dirSign[0] ==-1 && dirSign[1] == 0){
                let currentX = center[0] - boundingNearest;
                for(var j = wallIdx-1; true; --j){
                    if (j<0) j += room.roomShape.length;
                    var k = (j+1)%room.roomShape.length;
                    if(Math.abs(room.roomShape[j][0] - room.roomShape[k][0]) < 0.001) continue;
                    if((room.roomShape[j][0] + room.roomShape[k][0])/2.0 > center[0]) break;
                    let newDir = thetaToDir(room.roomOrient[j]);
                    let wallZ = room.roomShape[j][1];
                    if(newDir[1] > 0) span[0] = Math.max(span[0],wallZ);
                    else span[1] = Math.min(span[1],wallZ);
                    if(Math.min(room.roomShape[j][0], room.roomShape[k][0]) < currentX) break;
                }
                for(var j = wallIdx+1; true; ++j){
                    if (j >= room.roomShape.length) j -= room.roomShape.length; 
                    var k = (j+1)%room.roomShape.length;
                    if(Math.abs(room.roomShape[j][0] - room.roomShape[k][0]) < 0.001) continue;
                    if((room.roomShape[j][0] + room.roomShape[k][0])/2.0 > center[0]) break;
                    let newDir = thetaToDir(room.roomOrient[j]);
                    let wallZ = room.roomShape[j][1];
                    if(newDir[1] > 0) span[0] = Math.max(span[0],wallZ);
                    else span[1] = Math.min(span[1],wallZ);
                    if(Math.min(room.roomShape[j][0], room.roomShape[k][0]) < currentX) break;
                }

            }
            else if(dirSign[0] == 0 && dirSign[1] == 1){
                let currentZ = center[1] + boundingNearest;
                for(var j = wallIdx-1; true; --j){
                    if (j<0) j += room.roomShape.length;
                    var k = (j+1)%room.roomShape.length;
                    if(Math.abs(room.roomShape[j][1] - room.roomShape[k][1]) < 0.001) continue;
                    if((room.roomShape[j][1] + room.roomShape[k][1])/2.0 < center[1]) break;
                    let newDir = thetaToDir(room.roomOrient[j]);
                    let wallX = room.roomShape[j][0];
                    if(newDir[0] > 0) span[0] = Math.max(span[0],wallX);
                    else span[1] = Math.min(span[1],wallX);
                    if(Math.max(room.roomShape[j][1], room.roomShape[k][1]) > currentZ) break;
                }
                for(var j = wallIdx+1; true; ++j){
                    if (j >= room.roomShape.length) j -= room.roomShape.length; 
                    var k = (j+1)%room.roomShape.length;
                    if(Math.abs(room.roomShape[j][1] - room.roomShape[k][1]) < 0.001) continue;
                    if((room.roomShape[j][1] + room.roomShape[k][1])/2.0 < center[1]) break;
                    let newDir = thetaToDir(room.roomOrient[j]);
                    let wallX = room.roomShape[j][0];
                    if(newDir[0] > 0) span[0] = Math.max(span[0],wallX);
                    else span[1] = Math.min(span[1],wallX);
                    if(Math.max(room.roomShape[j][1], room.roomShape[k][1]) > currentZ) break;
                }
            }
        
            let doorSpan = [];
            for(var j = 0; j < WindoorOfRoom.door.length; ++j){
                if(WindoorOfRoom.door[j][2] == wallIdx){
                    if(spanDirSign == 0){
                        let p = [WindoorOfRoom.door[j][0].min[0],WindoorOfRoom.door[j][0].max[0]];
                        doorSpan = doorSpan.concat([p]);
                    }
                    else{
                        let p = [WindoorOfRoom.door[j][0].min[2],WindoorOfRoom.door[j][0].max[2]];
                        doorSpan = doorSpan.concat([p]);
                    }
                }
            }
            for(var j = 0; j < WindoorOfRoom.window.length; ++j){
                if(WindoorOfRoom.window[j][2] == wallIdx){
                    if(spanDirSign == 0){
                        let p = [WindoorOfRoom.window[j][0].min[0],WindoorOfRoom.window[j][0].max[0]];
                        doorSpan = doorSpan.concat([p]);
                    }
                    else{
                        let p = [WindoorOfRoom.window[j][0].min[2],WindoorOfRoom.window[j][0].max[2]];
                        doorSpan = doorSpan.concat([p]);
                    }
                }
            }
            let actualLength = 0;
            if(doorSpan.length > 0){
                if(span[1] - doorSpan[0][1] >  doorSpan[0][0] - span[0]) span[0] = doorSpan[0][1];
                else span[1] = doorSpan[0][0];
            }
            actualLength = span[1] - span[0]; console.log(i);

            //首先，需要检查一下能不能往这面墙上靠，actualLength 和 boundingLength
            if(actualLength > currentActualLength * 0.8){
                //如果按照boundingNearest靠到这面墙上需要做些什么呢？

                //首先，需要转成什么样子？需要nearest那一面和这面墙的方向对齐
                //from boundingSign to dirSign
                    // [1, 0] -> 2    min.x -> 2
                    // [0,-1] -> 3    max.z -> 3
                    //[-1, 0] -> 0    max.x -> 0
                    //[ 0, 1] -> 1    min.z -> 1    前面减后面乘以Math.PI / 2.0
                let wallSign = 0;
                if((dirSign[0] == 0) && (dirSign[1] == 1)) wallSign = 1;
                else if((dirSign[0] == 1) && (dirSign[1] == 0)) wallSign = 2;
                else if((dirSign[0] == 0) && (dirSign[1] ==-1)) wallSign = 3;

                var originalOrient = (boundingSign - wallSign) * Math.PI / 2.0;
                var originalLocation = [0.0, 0.0, 0.0];
                //其次，它的位置在哪里，
                if((dirSign[0] == 0) && (dirSign[1] == 1)){
                    originalLocation[0] = (span[1] + span[0])/2.0; originalLocation[2] = center[1] + boundingNearest;
                }else if((dirSign[0] == 1) && (dirSign[1] == 0)) {
                    originalLocation[2] = (span[1] + span[0])/2.0; originalLocation[0] = center[0] + boundingNearest;
                }else if((dirSign[0] == 0) && (dirSign[1] ==-1)){
                    originalLocation[0] = (span[1] + span[0])/2.0; originalLocation[2] = center[1] - boundingNearest;
                }else if((dirSign[0] ==-1) && (dirSign[1] == 0)){
                    originalLocation[2] = (span[1] + span[0])/2.0; originalLocation[0] = center[0] - boundingNearest;
                }
                //最后，这一面墙是谁是需要被记录下来的，
                var res = compareCurrentLocation([], [originalLocation, originalOrient, wallIdx], xscan, zscan, priorBbox); console.log(res);//1.0;//
                if(res > -0.001) schemes = schemes.concat([ [originalLocation, originalOrient, wallIdx] ] );
                if(schemes.length > 3) break;
            }
        }
        
        //----------------------------------------------------------------------------waist--------------------------------------------------------------------------------------------//
        console.log(schemes);

        for(let j = 0; j < schemes.length ;++j){console.log(j);

            //3， adjust the main object location with the information of wall
            if('wall' in meta){ //}else{
                //需要根据当前关联关系包围盒的朝向确定目标墙面的朝向
                let wallOrient = schemes[j][1] - meta.wall[0].nearestOrient0; //???????????????????????????????????????????????????????????????????????
                //nearestOrient0 = -1.57, schemes[j][1] = 0.0, wallDirSign = [1,0], wallOrient = 1.57
                //objectY = nearestOrient0 + wallOrient

                
                //需要依据之间记录的那面墙（如果是门窗那就是门窗所在墙，如果是主动找墙那就是找的那面墙）周围的墙壁来寻找到底是哪一面墙
                let wallDirSign = thetaToDir(wallOrient, 0.2);
                let currentWallIdx = schemes[j][2];
                let actualWallIdx = currentWallIdx;
                let currentWallInfo = wallInformDict(room, currentWallIdx);
                if(currentWallInfo.dir[0] == wallDirSign[0] && currentWallInfo.dir[1] == wallDirSign[1]) actualWallIdx = currentWallIdx;
                else{
                    let wallAIdx = currentWallIdx;//(currentWallIdx+1)%(room.roomShape.length);
                    let wallBIdx = currentWallIdx;//(currentWallIdx-1+room.roomShape.length)%(room.roomShape.length)
                    while(true){
                        wallAIdx = (wallAIdx+1)%(room.roomShape.length);//要求这面墙的终点晚于currX
                        wallAInfoDict = wallInformDict(room, wallAIdx);
                        if(wallAInfoDict.dir[0] == wallDirSign[0] && wallAInfoDict.dir[1] == wallDirSign[1]) { actualWallIdx = wallAIdx; break; }

                        wallBIdx = (wallBIdx-1+room.roomShape.length)%(room.roomShape.length); //要求这面墙的终点晚于currX
                        wallBInfoDict = wallInformDict(room, wallBIdx);
                        if(wallBInfoDict.dir[0] == wallDirSign[0] && wallBInfoDict.dir[1] == wallDirSign[1]) { actualWallIdx = wallBIdx; break; }
                        
                    }
                }

                //把主物体在那个维度挪一下，
                let wallDistance = meta.wall[0].nearestDistance;
                let actualWallInfo = wallInformDict(room, actualWallIdx);
                if((wallDirSign[0] == 0) && (wallDirSign[1] == 1)){
                    schemes[j][0][2] = actualWallInfo.centerZ + wallDistance; 
                }else if((wallDirSign[0] == 1) && (wallDirSign[1] == 0)) {
                    schemes[j][0][0] = actualWallInfo.centerX + wallDistance; 
                }else if((wallDirSign[0] == 0) && (wallDirSign[1] ==-1)){
                    schemes[j][0][2] = actualWallInfo.centerZ - wallDistance; 
                }else if((wallDirSign[0] ==-1) && (wallDirSign[1] == 0)){
                    schemes[j][0][0] = actualWallInfo.centerX - wallDistance; 
                }
                //这边其实也是有可能出问题的，有可能墙的方向蹩过去了......结果就不对了
            }

            /*/4, move the prior bounding box inside the room
            var tmpX = schemes[j][0][0]; var spanZ = [];
            var tmpZ = schemes[j][0][2]; var spanX = [];
            for(var tX in xscan){
                if(tX < tmpX) spanZ = xscan[tX];
                else break;
            }
            for(var tZ in zscan){
                if(tZ < tmpZ) spanX = zscan[tZ];
                else break;
            }
            var realPriorBbox = rotatePriorBbox(priorBbox,schemes[j][1]);
            var moveZ = Math.max(spanZ[0] - realPriorBbox.min.z - tmpZ, 0.0) - Math.max(realPriorBbox.max.z - spanZ[1] + tmpZ, 0.0);
            var moveX = Math.max(spanX[0] - realPriorBbox.min.x - tmpX, 0.0) - Math.max(realPriorBbox.max.x - spanX[1] + tmpX, 0.0);
            schemes[j][0][0] += moveX;
            schemes[j][0][2] += moveZ;*/
        }

        return schemes;//[ [ translate, orient, wallIdx, ,], [, , , ,], ...    ]
    }

    let outOfRoom = function(xscan, zscan, bbox){
        console.log(bbox);
        let xmin = bbox.min.x;
        let xmax = bbox.max.x;
        let zmin = bbox.min.z;
        let zmax = bbox.max.z;
        let xminout = -1000.0;
        let xmaxout = -1000.0;
        let zminout = -1000.0;
        let zmaxout = -1000.0;

        let lastX = 0.0;
        let inSign = false;
        for(var tX in xscan){console.log(tX);
            if(inSign){
                if( (xmin < tX) && (lastX < xmax) ){
                    zminout = Math.max(zminout, xscan[lastX][0] - zmin);
                    zmaxout = Math.max(zmaxout, zmax - xscan[lastX][1]);
                }
            }else inSign = true;
            lastX = tX;
        }
        let lastZ = 0.0; inSign = false;
        for(var tZ in zscan){console.log(tZ);
            if(inSign){
                if( (zmin < tZ) && (lastZ < zmax) ){
                    xminout = Math.max(xminout, zscan[lastZ][0] - xmin);
                    xmaxout = Math.max(xmaxout, xmax - zscan[lastZ][1]);
                }
            }
            else inSign = true;
            lastZ = tZ;
        }
        let ret = {"sign":"none", "val":10000.0, "xmin":xminout, "xmax":xmaxout, "zmin":zminout, "zmax":zmaxout};
        if(xminout > 0.0 && xminout < ret.val){ ret.sign = "xmin"; ret.val = xminout; }
        if(xmaxout > 0.0 && xmaxout < ret.val){ ret.sign = "xmax"; ret.val = xmaxout; }
        if(zminout > 0.0 && zminout < ret.val){ ret.sign = "zmin"; ret.val = zminout; }
        if(zmaxout > 0.0 && zmaxout < ret.val){ ret.sign = "zmax"; ret.val = zmaxout; }
        return ret;
    }

    const objectConflict = function(gtransObjectBboxes, f){
        console.log(gtransObjectBboxes[0]);
        console.log(f);
        for(let i = 0; i < gtransObjectBboxes.length; ++i){
            let e = gtransObjectBboxes[i];
            let xcross = false;
            if((e.max.x > f.min.x) && (f.max.x > e.min.x)){
                xcross = true;
                console.log("wtfx");
            }
            let zcross = false;
            if((e.max.z > f.min.z) && (f.max.z > e.min.z)){
                zcross = true;
                console.log("wtfz");
            }
            if(xcross && zcross){
                return {
                    "id":i,
                    "min":{"x":f.max.x - e.min.x,    "z":f.max.z - e.min.z},
                    "max":{"x":e.max.x - f.min.x,    "z":e.max.z - f.min.z}
                };
            }
        };
        return false;
    }

    var deleteLastPlanObject = function(plan){
        for(let i = 0; i < plan.length; ++i){
            for(let k = 0; k < manager.renderManager.scene_json['rooms'].length; ++k){
                let objList = manager.renderManager.scene_json['rooms'][k].objList;
                for(let j = 0; j < objList.length; ++j){
                    if(objList[j].key == plan[i].key){ removeObjectByUUID(objList[j].key); break; }
                }
            }
        }
    }

    let priorClickScheme = function(e){//deleteLastPlanObject();
        //clear GTrans
        releaseGTRANSChildrens(); INTERSECT_OBJ = null;
        let meta = $(e.target).data("meta"); //console.log(priorClickPlan);
        for(let i = 0; i < priorClickPlan.length; ++i){ //console.log("here");
            let t = priorClickPlan[i];
            if(t.roomId == currentRoomId && t.priorId == meta.priorId) { //return t.plans[0];   别忘了删掉GTRANS里的东西
                deleteLastPlanObject(t.plans[t.currentPlan]); console.log(t);
                t.currentPlan = (t.currentPlan + 1) % t.plans.length ;
                return t.plans[t.currentPlan];
            }
        }
        clickPlan = {"roomId":currentRoomId, "priorId":meta.priorId, "currentPlan":0, "plans":[]}; console.log("here");

        var scans = scanRoom(manager.renderManager.scene_json['rooms'][currentRoomId]);
        var xscan = scans[0];
        var zscan = scans[1];
        var transes = [[]];
        var scl = [1.0, 1.0, 1.0];
        var f = 'obj';
        var stt = 'origin'; console.log("here");

        //check if main object exist or add it in
        if(INTERSECT_OBJ == null || INTERSECT_OBJ.userData.modelId != meta.mainObjId){
            if(currentRoomId === undefined) { alert('no room being selected'); return; }
            var roomBbox = manager.renderManager.scene_json['rooms'][currentRoomId].roomShapeBBox; console.log(roomBbox);
            //console.log(currentRoomId);console.log(manager.renderManager.scene_json['rooms'][currentRoomId]); console.log(meta.mainObjId);
            if(meta.state && isNaN(parseInt(meta.mainObjId))){
                f = 'glb';
                stt = meta.state[0].currentState;
            }
            if('scale' in meta){
                scl = [meta.scale[0].objScaleX, meta.scale[0].objScaleY, meta.scale[0].objScaleZ];
            } //console.log("here");
            transes = mainObjLocation(manager.renderManager.scene_json['rooms'][currentRoomId], meta, xscan, zscan);
        }
        else{
            transes[0] = [INTERSECT_OBJ.userData.json.translate, INTERSECT_OBJ.userData.json.orient];
            scl = [INTERSECT_OBJ.scale.x,INTERSECT_OBJ.scale.y,INTERSECT_OBJ.scale.z];
            f = INTERSECT_OBJ.userData.json.format;
            stt = INTERSECT_OBJ.userData.json.startState;
        }
        console.log(transes);
        //var currentRoom = manager.renderManager.scene_json['rooms'][currentRoomId];
        //if(INTERSECT_OBJ == null || INTERSECT_OBJ.userData.modelId != meta.mainObjId) alert("wtf");

        for(let j = 0; j < transes.length; ++j){
            let furniture = {"modelId":meta.mainObjId, "translate":transes[j][0], "orient":transes[j][1], "scale":scl, "format":f, "startState":stt};
            clickPlan.plans = clickPlan.plans.concat([[furniture]]);

            var priorBbox = rotatePriorBbox(calcPriorBbox(meta), transes[j][1]);//INTERSECT_OBJ.userData.json.orient);
            //console.log(priorBbox);
            var movedRoom = {
                "max":{"x":roomBbox.max[0] - transes[j][0][0],    "z":roomBbox.max[1] - transes[j][0][2]},
                "min":{"x":roomBbox.min[0] - transes[j][0][0],    "z":roomBbox.min[1] - transes[j][0][2]}
            };
            //console.log(movedRoom);
            var lambdas = {
                "max":{"x":Math.min(1.0, movedRoom.max.x / priorBbox.max.x),    "z":Math.min(1.0, movedRoom.max.z / priorBbox.max.z)},
                "min":{"x":Math.min(1.0, movedRoom.min.x / priorBbox.min.x),    "z":Math.min(1.0, movedRoom.min.z / priorBbox.min.z)}
            };
            //console.log(lambdas); console.log(xscan); console.log(zscan);

            let mainItm = {"attachedObjId": meta.mainObjId, "objPosX":0.0, "objPosY":0.0, "objPosZ":0.0, "objOriY":0.0, "objScaleX":scl[0],"objScaleY":scl[1],"objScaleZ":scl[2]};
            if("state" in meta) mainItm["currentState"] = meta.state[0].currentState;
            let mainBbox = moveSinglePriorBbox(mainItm,transes[j]);//[INTERSECT_OBJ.userData.json.translate,INTERSECT_OBJ.userData.json.orient]);
            let gtransObjectBboxes = [mainBbox];
            //console.log(gtransObjectBboxes); console.log(transes[j]);

            //setNewIntersectObj();
            //console.log([INTERSECT_OBJ.userData.json.translate,INTERSECT_OBJ.userData.json.orient]);
            if('gtrans' in meta){
                for(var i = 0; i < meta.gtrans.length; ++i){
                    var ret = singleObjectRelativeLocation(meta.gtrans[i], transes[j]);

                    //（1）prior总体进入房间
                    var realx = (ret[0] > 0 ? ret[0] * lambdas.max.x : ret[0] * lambdas.min.x);// + INTERSECT_OBJ.position.x;
                    var realz = (ret[1] > 0 ? ret[1] * lambdas.max.z : ret[1] * lambdas.min.z);// + INTERSECT_OBJ.position.z;

                    let adjustedItm = JSON.parse(JSON.stringify(meta.gtrans[i]));
                    //adjustedItm.objOriY = meta.gtrans[i].objOriY;
                    adjustedItm.objPosX = realx;
                    adjustedItm.objPosZ = realz;
                    adjustedItm.objOriY += transes[j][1];//INTERSECT_OBJ.userData.json.orient;
                    //（2）各个家具进入房间的具体结构之中、各个家具之间不重叠

                    //console.log(meta.gtrans[i]);
                    let movedBbox = moveSinglePriorBbox(adjustedItm,[transes[j][0], 0.0]);//[INTERSECT_OBJ.userData.json.translate,0.0]);
                    let outRet = outOfRoom(xscan, zscan, movedBbox);
                    //console.log(outRet);
                    let cnt = 0;

                    while(outRet.sign != "none" && cnt < 2){
                        if(outRet.sign == "xmin") realx += outRet.val;
                        if(outRet.sign == "xmax") realx -= outRet.val;
                        if(outRet.sign == "zmin") realz += outRet.val;
                        if(outRet.sign == "zmax") realz -= outRet.val;
                        adjustedItm.objPosX = realx;
                        adjustedItm.objPosZ = realz;
                        movedBbox = moveSinglePriorBbox(adjustedItm,[transes[j][0], 0.0]);//[INTERSECT_OBJ.userData.json.translate,0.0]);
                        outRet = outOfRoom(xscan, zscan, movedBbox);
                        //console.log(outRet);
                        cnt += 1;
                    }

                    //真的要留的话还是应该留各个方向的最大误差，也就是四个数。如果留各个区域的话很不方便做的。
                    //关键问题还是在于如何构建误差：在这个物体的两个方向上分别扫一遍，各个方向上取最大值；完全冲出去的部分不计
                    //各个方向有最大误差，误差最小的方向，应该就是我们要挪的方向。（所谓误差，指的是该方向上的包围盒溢出该方向上墙面的多少，）
                    //往那个方向上走这个误差距离。
                    //跑三轮，跑不对就不跑了。

                    //如果上面这步跑对了，那就看看下面这步；
                    //（3）各个家具之间不重叠
                    //其次告诉它这个家具现在可以怎么挪是合法的：四个方向各一个最大距离：扫一下，扫出来能走的最大距离

                    //再次，把家具挪出其他家具的范围中：形式应该是（x小于多少多少 或 x大于多少多少 或 z小于多少多少 或 z大于多少多少） 且 （x小于多少多少 或 x大于多少多少 或 z小于多少多少 或 z大于多少多少）
                    //挪三次，挪不出去就算了
                    let objConflict = objectConflict(gtransObjectBboxes, movedBbox);
                    cnt = 0;
                    while(objConflict != false && cnt < 2){
                        //console.log("here"); console.log(outRet); console.log(objConflict);
                        let trySign = {sign:"none", val:10000}; let minimumError = Math.min(objConflict.min.x, objConflict.max.x, objConflict.min.z, objConflict.max.z); console.log(minimumError);
                        if(objConflict.min.x < -outRet.xmin){ if(objConflict.min.x < trySign.val) trySign = {sign:"xmin", val:objConflict.min.x}; }
                        if(objConflict.max.x < -outRet.xmax){ if(objConflict.max.x < trySign.val) trySign = {sign:"xmax", val:objConflict.max.x}; }
                        if(objConflict.min.z < -outRet.zmin){ if(objConflict.min.z < trySign.val) trySign = {sign:"zmin", val:objConflict.min.z}; }
                        if(objConflict.max.z < -outRet.zmax){ if(objConflict.max.z < trySign.val) trySign = {sign:"zmax", val:objConflict.max.z}; }
                        if(trySign.sign == "xmin" || minimumError < 0.1 || trySign.val > 0.8) break;

                        if(trySign.sign == "xmin") realx -= trySign.val;
                        if(trySign.sign == "xmax") realx += trySign.val;
                        if(trySign.sign == "zmin") realz -= trySign.val;
                        if(trySign.sign == "zmax") realz += trySign.val;
                        adjustedItm.objPosX = realx;
                        adjustedItm.objPosZ = realz;
                        movedBbox = moveSinglePriorBbox(adjustedItm,[transes[j][0], 0.0]);//[INTERSECT_OBJ.userData.json.translate,0.0]);
                        outRet = outOfRoom(xscan, zscan, movedBbox);
                        objConflict = objectConflict(gtransObjectBboxes, movedBbox);

                        //走哪条路，在允许的位置上（objConflict.min.x < -outRet.xmin），绝对值最小的objConflict.min.x，
                        //走过之后，outRet需要重新更新outOfRoom，objectConflict也需要重算。
                        cnt += 1;
                    }

                    gtransObjectBboxes = gtransObjectBboxes.concat([movedBbox]);
                    //console.log(meta.gtrans[i].objOriY); console.log(adjustedItm.objOriY);
                    adjustedItm.objOriY -= transes[j][1];//INTERSECT_OBJ.userData.json.orient;
                    //console.log(meta.gtrans[i].objOriY); console.log(adjustedItm.objOriY);

                    //singlePriorClickAdd(meta.gtrans[i], realx, realz, transes[0]);

                    furniture = {"modelId": meta.gtrans[i].attachedObjId, 
                                "translate":[transes[j][0][0] + realx, transes[j][0][1] + meta.gtrans[i].objPosY, transes[j][0][2] + realz],
                                "orient":transes[j][1] + meta.gtrans[i].objOriY,
                                "scale":[meta.gtrans[i].objScaleX,meta.gtrans[i].objScaleY,meta.gtrans[i].objScaleZ],
                                "format": ( meta.gtrans[i].currentState && isNaN(parseInt(meta.gtrans[i].attachedObjId)) ) ? "glb" : "obj" ,
                                "startState": ( meta.gtrans[i].currentState && isNaN(parseInt(meta.gtrans[i].attachedObjId)) ) ? meta.gtrans[i].currentState : "origin"};
                    clickPlan.plans[j] = clickPlan.plans[j].concat([furniture]);
                }
            }
        }
        priorClickPlan = priorClickPlan.concat([clickPlan]);
        //console.log(clickPlan);
        return clickPlan.plans[0];
    }

    const priorClick = function(e){
        let meta = $(e.target).data("meta");
        $(`#grids-${meta.identifier}`).css('height', '0px');
        $(`#grids-${meta.identifier}`).css('width', '0px');
        $(`#grids-${meta.identifier}`).css('opacity', '0');

        //load all the models into the cache before doing anything else
        if(INTERSECT_OBJ == null || INTERSECT_OBJ.userData.modelId != meta.mainObjId){
            var f = 'obj';
            var stt = 'origin';
            if(meta.state && isNaN(parseInt(meta.mainObjId))){
                f = 'glb';
                stt = meta.state[0].currentState;
            }
            if(!(meta.mainObjId in objectCache)) {
                loadObjectToCache(meta.mainObjId, anchor = priorClick, anchorArgs = [e], format = f);
                return;
            }
        }
        if('gtrans' in meta){
            for(var i = 0; i < meta.gtrans.length; ++i){
                var itm = meta.gtrans[i];
                var f = 'obj';
                var stt = 'origin';
                if('currentState' in itm  && isNaN(parseInt(itm.attachedObjId))){
                    f = 'glb';
                    stt = itm.currentState;
                }
                if(!(itm.attachedObjId in objectCache)) {
                    loadObjectToCache(itm.attachedObjId, anchor = priorClick, anchorArgs = [e], format = f);
                    return;
                }
            }
        }

        let clickPlan = priorClickScheme(e);
        if(clickPlan){
            for(let i = 0; i < clickPlan.length; ++i){
                let clp = JSON.parse(JSON.stringify(clickPlan[i]));   console.log(clp);
                while(clp["orient"] > Math.PI) clp["orient"] -= 2*Math.PI;
                while(clp["orient"] <-Math.PI) clp["orient"] += 2*Math.PI;
                let p = addObjectFromCache(
                    modelId=clp["modelId"],
                    transform={
                        'translate': clp["translate"],//transes[0][0],//[(roomBbox.max[0] + roomBbox.min[0])/2.0, 0.0, (roomBbox.max[1] + roomBbox.min[1])/2.0], 
                        'rotate': [0, clp["orient"], 0],//transes[0][1]
                        'scale': clp["scale"],//scl,
                        'format': clp["format"],//f,
                        'startState': clp["startState"]//stt
                    }
                ); clickPlan[i].key = p.userData.key; //console.log(p);
                if(i == 0){ INTERSECT_OBJ = p; timeCounter.maniStart = moment(); setNewIntersectObj(); }
                else addToGTRANS(p);
            } 
        }
        else{
            alert("no available layout solution");
        }
    }

    $("#usercommitOSR").click(() => {
        userOSR = $("#userOSR").val();
        nameOSR = $("#searchinput").val() + "_" + $("#nameOSR").val();
        if (userOSR == "") {
            alert("请填写您的用户名");
            return;
        }

        var interInfo = new Array(10);
        interInfo[0] = INTERSECT_OBJ.userData.modelId;
        interInfo[1] = INTERSECT_OBJ.position.x;
        interInfo[2] = INTERSECT_OBJ.position.y;
        interInfo[3] = INTERSECT_OBJ.position.z;
        interInfo[4] = INTERSECT_OBJ.rotation.x;
        interInfo[5] = INTERSECT_OBJ.rotation.y;
        interInfo[6] = INTERSECT_OBJ.rotation.z;
        interInfo[7] = INTERSECT_OBJ.scale.x;
        interInfo[8] = INTERSECT_OBJ.scale.y;
        interInfo[9] = INTERSECT_OBJ.scale.z;
        var gtransInfo = new Array();
        GTRANS_GROUP.traverse(function(objInG) {
            if (objInG.userData.modelId){ //modelID != None
                var objInfo = new Array(9);
                objInfo[0] = objInG.userData.modelId;
                objInfo[1] = objInG.position.x;
                objInfo[2] = objInG.position.y;
                objInfo[3] = objInG.position.z;
                objInfo[4] = objInG.rotation.y;
                objInfo[5] = objInG.scale.x;
                objInfo[6] = objInG.scale.y;
                objInfo[7] = objInG.scale.z;
                objInfo[8] = '';
                if(objInG.userData.json.startState){
                    objInfo[8] = objInG.userData.json.startState;
                }
                var p = new Array(1); p[0] = objInfo;
                gtransInfo = gtransInfo.concat(p);
            }
        })

        $.ajax({
            type: "POST",
            contentType: "application/json; charset=utf-8",
            url: `/usercommitOSR`,
            data: JSON.stringify({
                userOSR: userOSR,
                nameOSR: nameOSR,
                roomConstraints: [$("#considerWall").is(":checked"), $("#considerWindow").is(":checked"), $("#considerDoor").is(":checked")],
                intersectobject: interInfo,
                gtransgroup: gtransInfo,
                json: getDownloadSceneJson()}),
            success: function (msg) {
                alert(msg);
            }
        });
        
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
        if(rapidSearches[i].textContent.includes('CGS-')){
            rapidSearches[i].addEventListener('click', cgsSFunc, false);
        }else{
            rapidSearches[i].addEventListener('click', rapidSFunc, false);
        }
    }
    scene.add(CGSERIES_GROUP);
    scene.add(GTRANS_GROUP);
    selectionBox = new THREE.SelectionBox( camera, scene );
	selectionBoxHelper = new THREE.SelectionHelper( selectionBox, renderer, 'selectBox' );
    onWindowResize();
    deltaClock = new THREE.Clock();
    gameLoop();
    const waterGeometry = new THREE.PlaneGeometry( 20, 20 );
    const params = {
        color: '#ffffff',
        scale: 4,
        flowX: 1,
        flowY: 1
    };
    water = new THREE.Water( waterGeometry, {
        color: params.color,
        scale: params.scale,
        flowDirection: new THREE.Vector2( params.flowX, params.flowY ),
        textureWidth: 1024,
        textureHeight: 1024
    } );

    water.position.y = 1;
    water.rotation.x = Math.PI * - 0.5;
    // scene.add( water );
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

const transformAdjWF = function(wg, axis, pos) {
    let adjFloor = wg.adjFloor;
    const fCache = manager.renderManager.fCache;
    for (let f of adjFloor) {
        const p = fCache[f[0]].children[0].geometry.attributes.position.array;
        for (let i of f[1][0]) {
            p[i] = pos - wg.halfWidth;
        }
        for (let i of f[1][1]) {
            p[i] = pos + wg.halfWidth;
        }
        fCache[f[0]].children[0].geometry.attributes.position.needsUpdate = true;
        fCache[f[0]].children[0].geometry.computeBoundingSphere();
    }

    let adjWall = wg.adjWall;
    const nwCache = manager.renderManager.newWallCache;
    for (let w of adjWall) {
        const instance = nwCache[w[0]];
        const offset = axis == "x" ? instance.position.x : instance.position.z;
        const p = instance.children[0].geometry.attributes.position.array;
        for (let i of w[1][0]) {
            p[i] = pos - wg.halfWidth - offset;
        }
        for (let i of w[1][1]) {
            p[i] = pos + wg.halfWidth - offset;
        }
        instance.children[0].geometry.attributes.position.needsUpdate = true;
        instance.children[0].geometry.computeBoundingSphere();
    }
}

const unselectWall = function() {
    let wallID = INTERSECT_WALL.userData["groupId"];
    let wg = manager.renderManager.wallGroup[wallID];
    let axis = wg.axis;
    let pos = axis == "x" ? INTERSECT_WALL.position.x : INTERSECT_WALL.position.z;

    let roomIDs = [];
    let roomShapes = [];
    for (let r of wg.adjRoomShape) {
        roomIDs.push(r[0]);
        roomShapes.push(manager.renderManager.scene_json.rooms[r[0]].roomShape)
    }
    emitFunctionCall('transformRoomShape', [roomIDs, wallID, pos, roomShapes]);

    transformAdjWF(wg, axis, pos);

    INTERSECT_WALL = undefined;
}

const initAttributes = function() {
    CGSERIES_GROUP.attrArea = 0.5
    CGSERIES_GROUP.attrNum = 0.5
    CGSERIES_GROUP.attrCat = 0.5
    CGSERIES_GROUP.attrSU = 0.5
    CGSERIES_GROUP.attrD = 0.5
    CGSERIES_GROUP.attrS = 0.5

    $('#attrArea').val(CGSERIES_GROUP.attrArea).trigger('input');
    $('#attrNumOfObjects').val(CGSERIES_GROUP.attrNum).trigger('input');
    $('#attrObjRichness').val(CGSERIES_GROUP.attrCat).trigger('input');
    $('#attrSpaceUtilization').val(CGSERIES_GROUP.attrSU).trigger('input');
    $('#attrDependency').val(CGSERIES_GROUP.attrD).trigger('input');
    $('#attrSmoothness').val(CGSERIES_GROUP.attrS).trigger('input');
    
    $('#attrArea').on('change', ()=>{
        // console.log('attrArea', $('#attrArea').val());
        CGSERIES_GROUP.attrArea = +$('#attrArea').val();
    });
    $('#attrNumOfObjects').on('change', ()=>{
        // console.log('attrNumOfObjects', $('#attrNumOfObjects').val());
        CGSERIES_GROUP.attrNum = +$('#attrNumOfObjects').val();
    });
    $('#attrObjRichness').on('change', ()=>{
        // console.log('attrObjRichness', $('#attrObjRichness').val());
        CGSERIES_GROUP.attrCat = +$('#attrObjRichness').val();
    });
    $('#attrSpaceUtilization').on('change', ()=>{
        // console.log('attrSpaceUtilization', $('#attrSpaceUtilization').val());
        CGSERIES_GROUP.attrSU = +$('#attrSpaceUtilization').val();
    });
    $('#attrDependency').on('change', ()=>{
        // console.log('attrDependency', $('#attrDependency').val());
        CGSERIES_GROUP.attrD = +$('#attrDependency').val();
    });
    $('#attrSmoothness').on('change', ()=>{
        // console.log('attrSmoothness', $('#attrSmoothness').val());
        CGSERIES_GROUP.attrS = +$('#attrSmoothness').val();
    });
}