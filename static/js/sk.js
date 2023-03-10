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
    $('#tab_CLTP').text(timeCounter.cltp.toFixed(3));
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
        if (clutterpalette_Mode) { p = clutterpalettePos; }
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
        if (clutterpalette_Mode) {
            timeCounter.cltp += moment.duration(moment().diff(timeCounter.cltpStart)).asSeconds();
        }else{
            timeCounter.add += moment.duration(moment().diff(timeCounter.addStart)).asSeconds();
        }
        updateTimerTab();
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

const onClutterpaletteClick = function() {
    timeCounter.cltpStart = moment();
    let intersects = raycaster.intersectObjects(manager.renderManager.wfCache, true);
    if (intersects.length > 0) {
        clutterpalettePos = { x: intersects[0].point.x, y: 0, z: intersects[0].point.z };
        while (catalogItems.firstChild) { catalogItems.firstChild.remove(); }
        while (secondaryCatalogItems.firstChild) { secondaryCatalogItems.firstChild.remove(); }
        let roomId = intersects[0].object.parent.userData.roomId;
        let room = manager.renderManager.scene_json.rooms[roomId];
        let aabb = new THREE.Box3();
        for (let obj of room.objList) {
            if (obj.key in manager.renderManager.instanceKeyCache) {
                aabb.setFromObject(manager.renderManager.instanceKeyCache[obj.key]);
                obj.bbox = {
                    min: [aabb.min.x, aabb.min.y, aabb.min.z],
                    max: [aabb.max.x, aabb.max.y, aabb.max.z]
                };
            }
        }
        $.ajax({
            type: "POST",
            url: "/clutterpalette",
            data: {
                room: JSON.stringify(room),
                pos: JSON.stringify(clutterpalettePos)
            }
        }).done(function (o) {
            $('#searchinput').val('');
            searchResults = JSON.parse(o);
            searchResults.forEach(function (item) {
                newCatalogItem(item);
            });
        });
    }
}

const onClickIntersectObject = function(event){
    duplicateTimes = 1;
    var instanceKeyCache = manager.renderManager.instanceKeyCache;
    instanceKeyCache = Object.values(instanceKeyCache);
    intersects = raycaster.intersectObjects(instanceKeyCache, true);
    if (instanceKeyCache.length > 0 && intersects.length > 0) {
        if(['Door', 'Window'].includes(intersects[0].object.parent.userData.format)){
            return;
        }
        // start to count time consumed. 
        timeCounter.maniStart = moment();
        if(INTERSECT_OBJ){
            if(intersects[0].object.parent.userData.key !== INTERSECT_OBJ.userData.key){
                if (shelfstocking_Mode) {
                    if(INTERSECT_OBJ.userData.modelId === 'shelf01') {
                        claimControlObject3D(INTERSECT_OBJ.userData.key, true);
                        clearShelfInfo();
                    }
                }else if(pressedKeys[16]){// entering group transformation mode: 
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
        if (shelfstocking_Mode) {
            if(isShelfPlaceholder(INTERSECT_OBJ)){
                shelfPlaceholderHandler();
                return;
            }else if(INTERSECT_OBJ.userData.modelId === 'shelf01'){
                setIntersectShelf();
                return;
            }else{
                cancelClickingShelfPlaceholders();
            }
        }
        setNewIntersectObj(event);
        menu.style.left = (event.clientX - 63) + "px";
        menu.style.top = (event.clientY - 63) + "px";
        if (INTERSECT_WALL != undefined)
            unselectWall();
        return;
    }else{
        cancelClickingObject3D();
        if (clutterpalette_Mode) { onClutterpaletteClick(); }
        if (shelfstocking_Mode) {
            cancelClickingShelfPlaceholders();
            clearShelfInfo();
        }
        // return; // if you want to disable movable wall, just uncomment this line. 
        /*if (INTERSECT_WALL == undefined) {
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
        }*/
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
        let p = raycaster.intersectObjects(Object.values(manager.renderManager.instanceKeyCache).concat(Object.values(manager.renderManager.wfCache).concat(areaList)), true)[0].point;
        if (clutterpalette_Mode) { p = clutterpalettePos; }
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
        if (clutterpalette_Mode) {
            timeCounter.cltp += moment.duration(moment().diff(timeCounter.cltpStart)).asSeconds();
        }else{
            timeCounter.add += moment.duration(moment().diff(timeCounter.addStart)).asSeconds();
        }
        updateTimerTab();
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
    }else if(shelfstocking_Mode && instanceKeyCache.length > 0 && intersects.length > 0 && intersects[0].object.name.startsWith('shelf-placeholder-')){
        outlinePass.selectedObjects = [intersects[0].object]
    }else{
        outlinePass.selectedObjects = [GTRANS_GROUP]
    }  
    // currentMovedTimeStamp = moment();
    tf.engine().startScope();
    if(On_ADD && INSERT_OBJ.modelId in objectCache && INSERT_OBJ.object3d !== undefined && !clutterpalette_Mode){
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

const numberOfObjectsInTheScene = function(){
    let count = 0;
    manager.renderManager.scene_json.rooms.forEach(r => {
        r.objList.forEach(o => {
            if(o.inDatabase){
                count += 1;
            }
        });
    });
    console.log(count);
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
    $("#operationFuture").click(function(){
        let taID = manager.renderManager.scene_json.rooms[0].totalAnimaID;
        $.getJSON(`/static/dataset/infiniteLayout/${taID}.json`, function (data) {
            currentAnimation = data;
            operationFuture();
        });
    });
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
        timeCounter.cltp - ${timeCounter.cltp}\r\n
        timeCounter.total - ${timeCounter.total}
        `);
        timeCounter.navigate = 0;
        timeCounter.move = 0;
        timeCounter.rotate = 0;
        timeCounter.scale = 0;
        timeCounter.cgs = 0;
        timeCounter.cltp = 0;
        timeCounter.total = 0;
        timeCounter.add = 0;
        timeCounter.remove = 0;
        timeCounter.totalStart = moment();
    });
    $("#clutterpalette_button").click(function() {
        let button = document.getElementById("clutterpalette_button");
        clutterpalette_Mode = !clutterpalette_Mode;
        if(clutterpalette_Mode){
            button.style.backgroundColor = '#9400D3';
            $("#secondaryCatalogItems").show();
        }else{
            button.style.backgroundColor = 'transparent';
            $("#secondaryCatalogItems").hide();
            // while (catalogItems.firstChild) {catalogItems.firstChild.remove();}
            // while (secondaryCatalogItems.firstChild) {secondaryCatalogItems.firstChild.remove();}
        }
    });
    $("#stockshelf_button").click(function() {
        let button = document.getElementById("stockshelf_button");
        shelfstocking_Mode = !shelfstocking_Mode;
        if(shelfstocking_Mode){
            button.style.backgroundColor = '#9400D3';
            enterShelfStockingMode();
        }else{
            button.style.backgroundColor = 'transparent';
            exitShelfStockingMode();
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

    $("#usercommitOSR").click(() => {
        userOSR = $("#userOSR").val();
        nameOSR = $("#nameOSR").val();
        if (userOSR == "") {
            alert("请填写您的用户名");
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
        $('#floorPlanbtn').click();
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

let shelfPlaceholderHandler = () => {
    let shelfKey = INTERSECT_OBJ.userData.shelfKey;
    let shelf = manager.renderManager.instanceKeyCache[shelfKey];
    if (onlineGroup !== 'OFFLINE' && shelf.userData.controlledByID !== undefined && shelf.userData.controlledByID !== onlineUser.id) {
        console.log(`This shelf is already claimed by ${shelf.userData.controlledByID}`);
        INTERSECT_OBJ = undefined;
        return;
    }
    if (shelfKey in INTERSECT_SHELF_PLACEHOLDERS) {
        if (INTERSECT_SHELF_PLACEHOLDERS[shelfKey].has(INTERSECT_OBJ.name)) {
            // cancel
            INTERSECT_SHELF_PLACEHOLDERS[shelfKey].delete(INTERSECT_OBJ.name);
            let index = outlinePass2.selectedObjects.indexOf(INTERSECT_OBJ);
            if(index > -1){
                outlinePass2.selectedObjects.splice(index, 1);
            }
            if (INTERSECT_SHELF_PLACEHOLDERS[shelfKey].size === 0) {
                claimControlObject3D(shelfKey, true);
                delete INTERSECT_SHELF_PLACEHOLDERS[shelfKey];
            }
        } else {
            INTERSECT_SHELF_PLACEHOLDERS[shelfKey].add(INTERSECT_OBJ.name);
            outlinePass2.selectedObjects.push(INTERSECT_OBJ);
        }
    } else {
        INTERSECT_SHELF_PLACEHOLDERS[shelfKey] = new Set([INTERSECT_OBJ.name]);
        claimControlObject3D(shelfKey, false);
        outlinePass2.selectedObjects.push(INTERSECT_OBJ);
    }

    let roomId = shelf.userData.roomId;
    $('#tab_modelid').text(INTERSECT_OBJ.name);
    $('#tab_category').text('shelf-placeholder');
    $('#tab_roomid').text(roomId);
    $('#tab_roomtype').text(manager.renderManager.scene_json.rooms[roomId].roomTypes);
    while (catalogItems.firstChild) { catalogItems.firstChild.remove(); }

    if (INTERSECT_SHELF_PLACEHOLDERS.size == 0) return;
    $.ajax({
        type: "POST",
        url: "/shelfPlaceholder",
        data: {
            room: JSON.stringify(manager.renderManager.scene_json.rooms[roomId]),
            placeholders: JSON.stringify(INTERSECT_SHELF_PLACEHOLDERS)
        }
    }).done(function (o) {
        $('#searchinput').val('');
        searchResults = JSON.parse(o);
        searchResults.forEach(function (item) {
            newCatalogItem(item);
        });
    });
}

let cancelClickingShelfPlaceholders = () => {
    outlinePass2.selectedObjects = outlinePass2.selectedObjects.filter(obj => !obj.name.startsWith('shelf-placeholder-'));
    for (const shelfKey in INTERSECT_SHELF_PLACEHOLDERS) {
        claimControlObject3D(shelfKey, true);
    }
    INTERSECT_SHELF_PLACEHOLDERS = {};
    while (catalogItems.firstChild) { catalogItems.firstChild.remove(); }
}

let enterShelfStockingMode = () => {
    cancelClickingObject3D();
    for (let key in manager.renderManager.instanceKeyCache) {
        let inst = manager.renderManager.instanceKeyCache[key];
        if (inst.userData.json.modelId === 'shelf01') {
            if (inst.userData.json.commodities == undefined) {
                inst.userData.json.commodities = [
                    [{ modelId: '', uuid: '' }, { modelId: '', uuid: '' }],
                    [{ modelId: '', uuid: '' }, { modelId: '', uuid: '' }],
                    [{ modelId: '', uuid: '' }, { modelId: '', uuid: '' }],
                    [{ modelId: '', uuid: '' }, { modelId: '', uuid: '' }, { modelId: '', uuid: '' }]
                ];
            }
            addShelfPlaceholders(key);
        }
    }
}

let getCube = (width, height, depth, opacity) => {
    const geometry = new THREE.BoxGeometry(width, height, depth);
    const material = new THREE.MeshBasicMaterial();
    material.transparent = true;
    material.opacity = opacity;
    const cube = new THREE.Mesh(geometry, material);
    return cube;
}

const shelfOffestY = [1.565, 1.116, 0.666, 0.200];

let addShelfPlaceholders = (shelfKey) => {
    let shelf = manager.renderManager.instanceKeyCache[shelfKey];
    for (let r = 0; r < 4; ++r) {
        addShelfPlaceholdersByRow(shelfKey, r, shelf.userData.json.commodities[r].length);
    }
}

let exitShelfStockingMode = () => {
    cancelClickingShelfPlaceholders();
    for (let key in manager.renderManager.instanceKeyCache) {
        if (key.startsWith('shelf-placeholder-')) {
            scene.remove(manager.renderManager.instanceKeyCache[key]);
            delete manager.renderManager.instanceKeyCache[key];
        }
    }
    clearShelfInfo();
}

let isShelfPlaceholder = function(obj) {
    return obj.name !== undefined && obj.name.startsWith('shelf-placeholder-');
}

let addCommodityToShelf = function (shelfKey, modelId, r, c, l) {
    if (!(modelId in objectCache)) {
        loadObjectToCache(modelId, anchor = addCommodityToShelf, anchorArgs = [shelfKey, modelId, r, c, l]);
        return;
    }
    let offsetX = (0.6 / l) * (2 * c + 1) - 0.6;
    let offsetY = shelfOffestY[r];
    let shelf = manager.renderManager.instanceKeyCache[shelfKey];
    let commodity = addObjectFromCache(
        modelId = modelId,
        transform = {
            'translate': [shelf.position.x + offsetX, shelf.position.y + offsetY, shelf.position.z],
            'rotate': [shelf.rotation.x, shelf.rotation.y, shelf.rotation.z],
            'scale': [shelf.scale.x, shelf.scale.y, shelf.scale.z]
        },
        uuid = undefined,
        origin = true,
        otherInfo = {
            shelfKey: shelfKey,
            shelfRow: r,
            shelfCol: c
        }
    );
    shelf.userData.json.commodities[r][c] = { modelId: modelId, uuid: commodity.name };
    let objectProperties = {};
    objectProperties[shelfKey] = { commodities: shelf.userData.json.commodities };
    emitFunctionCall('updateObjectProperties', [objectProperties]);
}

let yulin = function (shelfKey, newCommodities) {
    for (let r = 0; r < 4; ++r) {
        changeShelfRow(shelfKey, r, newCommodities[r]);
    }
}

let clearDanglingCommodities = () => {
    for (let key in manager.renderManager.instanceKeyCache) {
        let inst = manager.renderManager.instanceKeyCache[key];
        if (inst.userData.modelId.startsWith('yulin-')) {
            let r = inst.userData.json.shelfRow;
            let c = inst.userData.json.shelfCol;
            let shelfKey = inst.userData.json.shelfKey;
            if (shelfKey in manager.renderManager.instanceKeyCache) {
                let commodities = manager.renderManager.instanceKeyCache[shelfKey].userData.json.commodities;
                if (commodities[r][c].uuid !== key) {
                    removeObjectByUUID(key);
                }
            } else {
                // the shelf is gone
                removeObjectByUUID(key);
            }
        } else if (inst.userData.modelId === 'shelf01') {
            let commodities = inst.userData.json.commodities;
            for (let r = 0; r < 4; ++r) {
                let l = commodities[r].length;
                for (let c = 0; c < l; ++c) {
                    if (!(commodities[r][c].uuid in manager.renderManager.instanceKeyCache)) {
                        commodities[r][c] = { modelId: '', uuid: '' };
                    }
                }
            }
        }
    }
}

let addShelfPlaceholdersByRow = function(shelfKey, r, l) {
    let shelf = manager.renderManager.instanceKeyCache[shelfKey];
    offsetY = shelfOffestY[r]+0.2;
    for (let c = 0; c < l; ++c) {
        let placeholder = getCube(1.2/l, 0.4, 0.45, 0.2);
        let phKey = `shelf-placeholder-${shelfKey}-${r}-${c}`;
        placeholder.name = phKey;
        let offsetX = (0.6/l)*(2*c+1)-0.6;
        placeholder.position.set(shelf.position.x+offsetX, shelf.position.y+offsetY, shelf.position.z-0.025);
        placeholder.rotation.set(shelf.rotation.x, shelf.rotation.y, shelf.rotation.z);
        placeholder.scale.set(shelf.scale.x, shelf.scale.y, shelf.scale.z);
        placeholder.userData.shelfKey = shelfKey;
        placeholder.userData.shelfRow = r;
        placeholder.userData.shelfCol = c;
        scene.add(placeholder);
        manager.renderManager.instanceKeyCache[phKey] = placeholder;
    }
}

// newRow = [{modelId: 'yulin-xxx'}, {modelId: ''}, ...]
let changeShelfRow = function (shelfKey, r, newRow) {
    let shelf = manager.renderManager.instanceKeyCache[shelfKey];
    let oldRow = shelf.userData.json.commodities[r];
    if (oldRow !== undefined) {
        for (let c = 0; c < oldRow.length; ++c) {
            if (newRow.length === oldRow.length && newRow[c].modelId === oldRow[c].modelId) {
                // same commodity
                newRow[c].uuid = oldRow[c].uuid;
            } else {
                if (oldRow[c].uuid !== "") {
                    removeObjectByUUID(oldRow[c].uuid)
                }
            }
        }
    }
    if (newRow.length !== oldRow.length) {
        for (let c = 0; c < oldRow.length; ++c) {
            let phKey = `shelf-placeholder-${shelfKey}-${r}-${c}`;
            scene.remove(manager.renderManager.instanceKeyCache[phKey]);
            delete manager.renderManager.instanceKeyCache[phKey];
        }
        addShelfPlaceholdersByRow(shelfKey, r, newRow.length);
    }
    shelf.userData.json.commodities[r] = newRow;
    let l = newRow.length;
    for (let c = 0; c < l; ++c) {
        let modelId = newRow[c].modelId;
        if (newRow.length === oldRow.length && newRow[c].uuid !== undefined && newRow[c].uuid !== "") {
            continue;
        } else {
            addCommodityToShelf(shelfKey, modelId, r, c, l);
        }
    }
}

let setIntersectShelf = () => {
    if (shelfstocking_Mode) cancelClickingShelfPlaceholders();
    $("#shelfKey").text(INTERSECT_OBJ.userData.key);
    for (let r = 0; r < 4; ++r) {
        let l = INTERSECT_OBJ.userData.json.commodities[r].length;
        $(`#shelfRow${r}`).val(l);
        if (l === 1) {
            $(`#shelfRow${r}MinusBtn`).attr("disabled", "true");
        } else {
            $(`#shelfRow${r}MinusBtn`).removeAttr('disabled');
        }
        if (l >= 8) {
            $(`#shelfRow${r}PlusBtn`).attr("disabled", "true");
        } else {
            $(`#shelfRow${r}PlusBtn`).removeAttr('disabled');
        }
        $(`#shelfSelectRow${r}Btn`).removeAttr('disabled');
    }
    $(`#shelfSelectAllBtn`).removeAttr('disabled');
    claimControlObject3D(INTERSECT_OBJ.userData.key, false);
    $("#shelfInfoDiv").collapse('show');
}

let clearShelfInfo = () => {
    $("#shelfKey").text("");
    for (let r = 0; r < 4; ++r) {
        $(`#shelfRow${r}`).val(0);
        $(`#shelfRow${r}MinusBtn`).attr("disabled", "true");
        $(`#shelfRow${r}PlusBtn`).attr("disabled", "true");
        $(`#shelfSelectRow${r}Btn`).attr("disabled", "true");
    }
    $(`#shelfSelectAllBtn`).attr("disabled", "true");
}

let shelfRowMinus = (r) => {
    let shelfKey = $("#shelfKey").text();
    let oldRow = manager.renderManager.instanceKeyCache[shelfKey].userData.json.commodities[r];
    for (let i = oldRow.length - 1; i >= 0; --i) {
        if (oldRow[i].modelId === "") {
            let newRow = [...oldRow];
            newRow.splice(i, 1);
            changeShelfRow(shelfKey, r, newRow);
            $(`#shelfRow${r}`).val(newRow.length);
            if (newRow.length <= 1) $(`#shelfRow${r}MinusBtn`).attr("disabled", "true");
            $(`#shelfRow${r}PlusBtn`).removeAttr('disabled');
            return;
        }
    }
    alert("不能再减了！");
}

let shelfRowPlus = (r) => {
    let shelfKey = $("#shelfKey").text();
    let oldRow = manager.renderManager.instanceKeyCache[shelfKey].userData.json.commodities[r];
    let newRow = [...oldRow];
    newRow.push({modelId:""});
    changeShelfRow(shelfKey, r, newRow);
    $(`#shelfRow${r}`).val(newRow.length);
    if (newRow.length >= 8) $(`#shelfRow${r}PlusBtn`).attr("disabled", "true");
    $(`#shelfRow${r}MinusBtn`).removeAttr('disabled');
}

let shelfRowSelect = (rows) => {
    outlinePass2.selectedObjects = outlinePass2.selectedObjects.filter(obj => !obj.name.startsWith('shelf-placeholder-'));
    while (catalogItems.firstChild) { catalogItems.firstChild.remove(); }

    let shelfKey = $("#shelfKey").text();
    let shelf = manager.renderManager.instanceKeyCache[shelfKey];
    let commodities = shelf.userData.json.commodities;
    INTERSECT_SHELF_PLACEHOLDERS = {};
    INTERSECT_SHELF_PLACEHOLDERS[shelfKey] = new Set();

    for (let r of rows) {

        let l = commodities[r].length;
        for (let c = 0; c < l; ++c) {
            let phKey = `shelf-placeholder-${shelfKey}-${r}-${c}`;
            INTERSECT_SHELF_PLACEHOLDERS[shelfKey].add(phKey);
            outlinePass2.selectedObjects.push(manager.renderManager.instanceKeyCache[phKey]);
        }
    }

    $.ajax({
        type: "POST",
        url: "/shelfPlaceholder",
        data: {
            room: JSON.stringify(manager.renderManager.scene_json.rooms[shelf.userData.roomId]),
            placeholders: JSON.stringify(INTERSECT_SHELF_PLACEHOLDERS)
        }
    }).done(function (o) {
        $('#searchinput').val('');
        searchResults = JSON.parse(o);
        searchResults.forEach(function (item) {
            newCatalogItem(item);
        });
    });
}