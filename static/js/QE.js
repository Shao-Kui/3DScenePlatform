var Q_DOWN = false;
var E_DOWN = false;
var prevTime = performance.now();
//var QE_initialization = function(){};
var keyboard_update = function(){
  var time = performance.now();
  var delta = ( time - prevTime ) / 300;
  if(Q_DOWN){
    orbitControls.sphericalDelta.theta += delta;
  }
  if(E_DOWN){
    orbitControls.sphericalDelta.theta -= delta;
  }
  orbitControls.update();
  prevTime = time;
};

const transformControlsConfig = function(){
    transformControls.addEventListener('dragging-changed', function (event){
        scenecanvas.removeEventListener('click', onClickObj);
        onTouchTimes = 2;
        // scenecanvas.removeEventListener('touchend', onTouchObj);
        orbitControls.enabled = !event.value;
        if (isToggle) {
            radial.toggle();
            isToggle = !isToggle;
        }
        if(event.value){
            timeCounter.maniStart = moment();
        }else{
            synchronize_json_object(INTERSECT_OBJ);
            if(transformControls.mode === 'translate'){
                timeCounter.move += moment.duration(moment().diff(timeCounter.maniStart)).asSeconds();
            }else if(transformControls.mode === 'rotate'){
                timeCounter.rotate += moment.duration(moment().diff(timeCounter.maniStart)).asSeconds();
            }else if(transformControls.mode === 'scale'){
                timeCounter.scale += moment.duration(moment().diff(timeCounter.maniStart)).asSeconds();
            }
            timeCounter.maniStart = moment();
        }
        if(animaRecord_Mode && transformControls.mode === 'translate'){
            let index = INTERSECT_OBJ.userData.json.sforder;
            let startTime;
            if(currentSeqs[index][0].length === 0){
                startTime = 0;
            }else{
                startTime = currentSeqs[index][0].at(-1).t[1];
            }
            if(event.value){
                currentSeqs[index][0].push({
                    "action": "move",
                    "p1": [INTERSECT_OBJ.position.x, INTERSECT_OBJ.position.y, INTERSECT_OBJ.position.z],
                    "t": [startTime, startTime+1]
                });
            }else{
                let a = currentSeqs[index][0].at(-1);
                a.p2 = [INTERSECT_OBJ.position.x, INTERSECT_OBJ.position.y, INTERSECT_OBJ.position.z];
                a.t[1] = a.t[0] + Math.sqrt(Math.pow(a.p1[0]-a.p2[0], 2) + Math.pow(a.p1[1]-a.p2[1], 2) + Math.pow(a.p1[2]-a.p2[2], 2)) / 4;
                updateAnimationSlider(index)
            }
        }
    });
    transformControls.addEventListener('change', function (event) {
        if(INTERSECT_OBJ === undefined){
            return;
        }
        if(transformControls.mode === 'translate'){
            let oSet = Object.values(manager.renderManager.instanceKeyCache).filter(d => d.userData.key !== INTERSECT_OBJ.userData.key);
            if(oSet.length > 0 && pressedKeys[17]){
                let closestX = oSet.map(d => d.position.x).reduce(function(prev, curr) {
                    return (Math.abs(curr - INTERSECT_OBJ.position.x) < Math.abs(prev - INTERSECT_OBJ.position.x) ? curr : prev);
                });
                if(Math.abs(closestX - INTERSECT_OBJ.position.x) < 0.25){
                    INTERSECT_OBJ.position.x = closestX;
                }
                let closestZ = oSet.map(d => d.position.z).reduce(function(prev, curr) {
                    return (Math.abs(curr - INTERSECT_OBJ.position.z) < Math.abs(prev - INTERSECT_OBJ.position.z) ? curr : prev);
                });
                if(Math.abs(closestZ - INTERSECT_OBJ.position.z) < 0.25){
                    INTERSECT_OBJ.position.z = closestZ;
                }
            }
            transformObject3DOnly(INTERSECT_OBJ.userData.key, 
                [INTERSECT_OBJ.position.x, INTERSECT_OBJ.position.y, INTERSECT_OBJ.position.z], 'position');
            gsap.to(GTRANS_GROUP.position, {duration: commonSmoothDuration, x: INTERSECT_OBJ.position.x, y: INTERSECT_OBJ.position.y, z: INTERSECT_OBJ.position.z});
        }else if(transformControls.mode === 'rotate'){
            transformObject3DOnly(INTERSECT_OBJ.userData.key, 
                [INTERSECT_OBJ.rotation.x, INTERSECT_OBJ.rotation.y, INTERSECT_OBJ.rotation.z], 'rotation');
            GTRANS_GROUP.rotation.set(INTERSECT_OBJ.rotation.x, GTRANS_GROUP.rotation.y, INTERSECT_OBJ.rotation.z)
            gsap.to(GTRANS_GROUP.rotation, {duration: commonSmoothDuration, y: INTERSECT_OBJ.rotation.y});
        }else if(transformControls.mode === 'scale'){
            transformObject3DOnly(INTERSECT_OBJ.userData.key, 
                [INTERSECT_OBJ.scale.x, INTERSECT_OBJ.scale.y, INTERSECT_OBJ.scale.z], 'scale');
        }
    });
}

const actionAddTime = function(duration=1){
    let index = INTERSECT_OBJ.userData.json.sforder;
    let startTime;
    if(currentSeqs[index][0].length === 0){
        startTime = 0;
    }else{
        startTime = currentSeqs[index][0].at(-1).t[1];
    }
    currentSeqs[index][0].push({
        "action": "pause",
        "t": [startTime, startTime+duration]
    });
    updateAnimationSlider(index)
}

const topdownAreaview = function(){
    let bbox = manager.renderManager.scene_json.bbox; 
    let lx = (bbox.max[0] + bbox.min[0]) / 2;
    let lz = (bbox.max[2] + bbox.min[2]) / 2;
    let lx_length = bbox.max[0] - bbox.min[0];
    let lz_length = bbox.max[2] - bbox.min[2];
    camfovratio = Math.tan((camera.fov/2) * Math.PI / 180) 
    if(lz_length > lx_length){
        orbitControls.sphericalDelta.theta = Math.PI / 2;
        camHeight = 0 + (bbox.max[0]/2 - bbox.min[0]/2) / camfovratio;
    }else{
        camHeight = 0 + (bbox.max[2]/2 - bbox.min[2]/2) / camfovratio;
    }
    camera.position.set(lx, camHeight, lz);
    camera.lookAt(lx, 0, lz);
    orbitControls.target.set(lx, 0, lz);
}

const topdownview = function(bbox = undefined){
    bbox = bbox ?? manager.renderManager.scene_json.rooms[currentRoomId].bbox; 
    let lx = (bbox.max[0] + bbox.min[0]) / 2;
    let ymax = bbox.max[1];
    let lz = (bbox.max[2] + bbox.min[2]) / 2;
    let camfovratio = Math.tan((camera.fov/2) * Math.PI / 180); 
    let height_x = (bbox.max[0]/2 - bbox.min[0]/2) / camfovratio;
    let height_z = (bbox.max[2]/2 - bbox.min[2]/2) / camfovratio;
    let camHeight = ymax + Math.max(height_x, height_z)
    if(camHeight > 36 || camHeight < -36 || isNaN(camHeight)){
        // prevent if there is NaN in datasets; 
        camHeight = 6;
    }
    camera.position.set(lx, camHeight, lz);
    camera.lookAt(lx, 0, lz);
    orbitControls.target.set(lx, 0, lz);
    let lx_length = bbox.max[0] - bbox.min[0];
    let lz_length = bbox.max[2] - bbox.min[2];
    let tCamUp;
    if(lz_length > lx_length){
        // let thetaTar = orbitControls.sphericalDelta.theta + Math.PI / 2;
        orbitControls.sphericalDelta.theta += Math.PI / 2;
    }else{

    }
    orbitControls.sphericalDelta.theta += Math.PI;
};

var ctrlPressing = false;
var fivePressing=false;
var duplicateTimes = 1;
const onKeyDown = function(event){
    if(event.target.matches("input")) return;
    pressedKeys[event.keyCode] = true;
    switch ( event.keyCode ) {
        case 39: // →
            let functionalNode = d3.selectAll('rect').filter(d => d.imgindex >= 0);
            if(functionalNode.size() === 1){
                let datum = functionalNode.datum();
                datum.imgindex  = (datum.imgindex + 1) % datum.pics.length;
                d3.select(`#image${datum.id}`).attr("href", datum.pics[datum.imgindex] + ".png");
                let file_dir = datum.pics[datum.imgindex] + ".json";
                draw1(file_dir);
                draw2('/static/dataset/infiniteLayout/'+onlineGroup+'_origin_values.json',file_dir);
            }
            break;
        case 81: // Q
            Q_DOWN = true;
            break;
        case 65: // A
            if (shelfstocking_Mode && !$('#shelfSelectAllBtn').prop('disabled'))
                $('#shelfSelectAllBtn').click();
            break;
        case 67: // C
            orbitControls.enabled = !orbitControls.enabled;
            scenecanvas.addEventListener('click', onClickObj);
            break;
        case 69: // E
            E_DOWN = true;
            break;
        case 32: // white space
            topdownview();
            break;
        case 71: // G
            if (shelfstocking_Mode && !$('#selectShelfGroupBtn').prop('disabled'))
                $('#selectShelfGroupBtn').click();
            break;
        case 78: // N
            if (shelfstocking_Mode && !$('#nextShelfBtn').prop('disabled'))
                $('#nextShelfBtn').click();
            break;
        case 220: // backslash
            topdownAreaview();
            break;
        case 85: // U
            // start to record audio; 
            reco.record();
            break;
        case 82: // R
            render_function();
            break;
        // case 83: // S
        //     downloadSceneJson();
        //     break;
        case 49: // 1
        case 97: // 1
            if (shelfstocking_Mode) {
                if (!$('#shelfSelectRow0Btn').prop('disabled')) $('#shelfSelectRow0Btn').click();
            } else {
                auxiliary_catlist(-1)
            }
            break;
        case 50: // 2
        case 98: // 2
            if (shelfstocking_Mode) {
                if (!$('#shelfSelectRow1Btn').prop('disabled')) $('#shelfSelectRow1Btn').click();
            } else {
                auxiliary_catlist(1)
            }
            break;
        case 51: // 3
        case 99: // 3
            if (shelfstocking_Mode) {
                if (!$('#shelfSelectRow2Btn').prop('disabled')) $('#shelfSelectRow2Btn').click();
            }
            break;
        case 52:  // 4
        case 100: // 4
            if (shelfstocking_Mode) {
                if (!$('#shelfSelectRow3Btn').prop('disabled')) $('#shelfSelectRow3Btn').click();
            }
            break;
        case 84:  // 5
            fivePressing=true;console.log("fivePressing");
            break;
        case 192: // `
            auxiliary_catlist(0)
            break;
        case 107: // +
        case 187: // + 
            if (animaRecord_Mode) {
                updateAnimationRecordDiv(AnimationSlider.max + 4);
            }
            break;
        case 109: // -
        case 189: // -
            if (animaRecord_Mode) {
                let animaMax = 4;
                for (let i = 0; i < currentSeqs.length; i++) {
                    let anim = currentSeqs[i][0];
                    for (let j = 0; j < anim.length; j++) {
                        animaMax = Math.max(animaMax, anim[j].t[1]);
                    }
                }
                animaMax = Math.ceil(animaMax / 4) * 4;
                updateAnimationRecordDiv(Math.max(AnimationSlider.max - 4, animaMax));
            }
            break;
        case 188: // ,
            transformControls.setMode('translate');
            break;
        case 190: // .
            transformControls.setMode('rotate');
            break;
        case 191: // /
            transformControls.setMode('scale');
            break;
        case 17:
            ctrlPressing = true; console.log("ctrlPressing");
            break;
        case 18:
            enteringBoxSelectionMode();
            break;
        case 46:
            if(INTERSECT_OBJ === undefined){break;}
            radial_remove_control();
            break;
        case 68: // d
            if(INTERSECT_OBJ === undefined){break;}
            let orient = Math.atan2(Math.sin(INTERSECT_OBJ.rotation.y), Math.cos(INTERSECT_OBJ.rotation.x) * Math.cos(INTERSECT_OBJ.rotation.y)) + Math.PI/2;
            let _x = objectCache[INTERSECT_OBJ.userData.modelId].boundingBox.max.x - objectCache[INTERSECT_OBJ.userData.modelId].boundingBox.min.x;
            _x *= INTERSECT_OBJ.scale.x;
            let newINTERSECT_OBJ = addObjectFromCache(
                modelId=INTERSECT_OBJ.userData.modelId,
                transform={
                    'translate': [INTERSECT_OBJ.position.x+_x*Math.sin(orient), INTERSECT_OBJ.position.y, INTERSECT_OBJ.position.z+_x*Math.cos(orient)], 
                    'rotate': [INTERSECT_OBJ.rotation.x, INTERSECT_OBJ.rotation.y, INTERSECT_OBJ.rotation.z],
                    'scale': [INTERSECT_OBJ.scale.x,INTERSECT_OBJ.scale.y,INTERSECT_OBJ.scale.z],
                    'startState': INTERSECT_OBJ.userData.json.startState,
                    'format': INTERSECT_OBJ.userData.format
                }
            );
            duplicateTimes += 1;
            timeCounter.add += moment.duration(moment().diff(timeCounter.maniStart)).asSeconds();
            timeCounter.maniStart = moment();
            // swap the control to the new inserted object. 
            claimControlObject3D(INTERSECT_OBJ.userData.key, true);
            synchronize_json_object(INTERSECT_OBJ);
            INTERSECT_OBJ = newINTERSECT_OBJ;
            setNewIntersectObj();
            break;
    }
    if(event.keyCode === 90 && ctrlPressing){
        if(commandStack.length > 0){
            let cmd = commandStack.pop();
            onlineFuncList[cmd.funcName].apply(null, cmd.args);
            emitFunctionCall(cmd.funcName, cmd.args);
        }
    }

    if(event.keyCode === 77 && pressedKeys[17]){ 
        tmp = $("#considerWall").is(":checked");
        $("#considerWall").attr("checked", !tmp);
    }

    if(event.keyCode === 66 && pressedKeys[17]){
        $("#usercommitOSR").click();
    }

    if(event.keyCode === 83 && pressedKeys[17]){ // Ctrl + S
        event.preventDefault();
        socket.emit('onlineSceneUpdate', getDownloadSceneJson(), onlineGroup);
    }
};

var onKeyUp = function (event) {
    pressedKeys[event.keyCode] = false;
    switch ( event.keyCode ) {
        case 81: // Q
            Q_DOWN = false;
            break;
        case 69: // E
            E_DOWN = false;
            break;
        case 85: // U
            reco.stop();
            audioToText();
            break;
        case 13: // ENTER
            clickTextSearchButton();
            break;
        case 84:  // 5
            fivePressing=false;console.log("fiveLosing");
            break;
        case 17:
            ctrlPressing = false;console.log("ctrlLosing");
            break;
        case 18:
            leavingBoxSelectionMode();
            break;
    }
};

const boxSelectedObjects = [];

const enteringBoxSelectionMode = function(){
    cancelClickingObject3D();
    orbitControls.enabled = false;
    document.removeEventListener('click', onClickObj);
    selectionBoxHelper.element.style.background = 'rgba(75, 160, 255, 0.3)';
    selectionBoxHelper.element.style.border = '1px solid #55aaff';
    document.addEventListener('pointerdown', boxSelectionDown);
    document.addEventListener('pointermove', boxSelectionMove);
    document.addEventListener('pointerup', boxSelectionUp);
}

const leavingBoxSelectionMode = function(){
    outlinePass2.selectedObjects = [];
    orbitControls.enabled = true;
    selectionBoxHelper.element.style.background = 'none';
    selectionBoxHelper.element.style.border = 'none';
    document.removeEventListener('pointerdown', boxSelectionDown);
    document.removeEventListener('pointermove', boxSelectionMove);
    document.removeEventListener('pointerup', boxSelectionUp);
    for(let i = 0; i < boxSelectedObjects.length; i++){
        if(i == 0){
            INTERSECT_OBJ = manager.renderManager.instanceKeyCache[boxSelectedObjects[i]];
            setNewIntersectObj();
        }else{
            addToGTRANS(manager.renderManager.instanceKeyCache[boxSelectedObjects[i]]);
        }
    }
    boxSelectedObjects.length = 0;
}

const boxSelectionDown = function(event) {
    event.preventDefault();
    document.removeEventListener('click', onClickObj);
    boxSelectedObjects.length = 0;
    outlinePass2.selectedObjects = [];
    for(const item of selectionBox.collection){
        let selectedObj;
        if(item.parent.name in manager.renderManager.instanceKeyCache){
            selectedObj = item.parent;
        }
        else if(item.name in manager.renderManager.instanceKeyCache){
            selectedObj = item;
        }
        if(!selectedObj) continue;
        if(!boxSelectedObjects.includes(selectedObj.name)){
            outlinePass2.selectedObjects.push(selectedObj);
            boxSelectedObjects.push(selectedObj.name);
        }
    }
    selectionBox.startPoint.set(
        ((event.clientX - $(scenecanvas).offset().left) / scenecanvas.clientWidth) * 2 - 1, 
        -((event.clientY - $(scenecanvas).offset().top) / scenecanvas.clientHeight) * 2 + 1,
        0.5
    );
}

const boxSelectionMove = function(event){
    event.preventDefault();
    document.removeEventListener('click', onClickObj);
    if (selectionBoxHelper.isDown) {
        // for ( let i = 0; i < selectionBox.collection.length; i ++ ) {
        //    selectionBox.collection[ i ].material.emissive.set( 0x000000 );
        // }
        boxSelectedObjects.length = 0;
        outlinePass2.selectedObjects = [];
        selectionBox.endPoint.set(
            ((event.clientX - $(scenecanvas).offset().left) / scenecanvas.clientWidth) * 2 - 1, 
            -((event.clientY - $(scenecanvas).offset().top) / scenecanvas.clientHeight) * 2 + 1,
            0.5
        );
        const allSelected = selectionBox.select();
        for (let i = 0; i < allSelected.length; i++) {
            let selectedObj;
            if(allSelected[i].parent.name in manager.renderManager.instanceKeyCache){
                selectedObj = allSelected[i].parent;
            }
            else if(allSelected[i].name in manager.renderManager.instanceKeyCache){
                selectedObj = allSelected[i];
            }
            if(!selectedObj) continue
            if(!boxSelectedObjects.includes(selectedObj.name)){
                outlinePass2.selectedObjects.push(selectedObj);
                boxSelectedObjects.push(selectedObj.name);
            }
        }
    }
}

const boxSelectionUp = function(event){
    document.removeEventListener('click', onClickObj);
    selectionBox.endPoint.set(
        ((event.clientX - $(scenecanvas).offset().left) / scenecanvas.clientWidth) * 2 - 1, 
        -((event.clientY - $(scenecanvas).offset().top) / scenecanvas.clientHeight) * 2 + 1,
        0.5
    );
    const allSelected = selectionBox.select();
    for (let i = 0; i < allSelected.length; i++) {
        let selectedObj;
        if(allSelected[i].parent.name in manager.renderManager.instanceKeyCache){
            selectedObj = allSelected[i].parent;
        }
        else if(allSelected[i].name in manager.renderManager.instanceKeyCache){
            selectedObj = allSelected[i];
        }
        if(!selectedObj) continue
        if(!boxSelectedObjects.includes(selectedObj.name)){
            outlinePass2.selectedObjects.push(selectedObj);
            boxSelectedObjects.push(selectedObj.name);
        }
    }
};

var firstPersonControls;
var fpCtrlMode = false;
const fpctrl = {
    moveForward: false,
    moveBackward: false,
    moveLeft: false,
    moveRight: false,
    moveUp: false,
    moveDown: false,
    prevTime: performance.now(),
    direction: new THREE.Vector3(),
}

const onKeyDownFirstPerson = function(event){
    switch ( event.keyCode ) {
        case 38: // up
        case 87: // w
            fpctrl.moveForward = true;
            break;
        case 37: // left
        case 65: // a
            fpctrl.moveLeft = true;
            break;
        case 40: // down
        case 83: // s
            fpctrl.moveBackward = true;
            break;
        case 39: // right
        case 68: // d
            fpctrl.moveRight = true;
            break;
        case 32: // space
            fpctrl.moveUp = true;
            break;
        case 67: // C
            fpctrl.moveDown = true;
            break;
        case 82: // R
            render_function();
            downloadSceneJson();
            break;
    }
};

var onKeyUpFirstPerson = function (event) {
    switch ( event.keyCode ) {
        case 38: // forward
        case 87: // w
            fpctrl.moveForward = false;
            break;
        case 37: // left
        case 65: // a
            fpctrl.moveLeft = false;
            break;
        case 40: // backward
        case 83: // s
            fpctrl.moveBackward = false;
            break;
        case 39: // right
        case 68: // d
            fpctrl.moveRight = false;
            break;
        case 32: // space
            fpctrl.moveUp = false;
            break;
        case 67: // C
            fpctrl.moveDown = false;
            break;
    }
};

const firstPersonUpdate = function(){
    if (firstPersonControls.isLocked === true) {
        delta = 0.05;
        let fw = Number(fpctrl.moveForward) - Number(fpctrl.moveBackward);
        let lr = Number(fpctrl.moveLeft) - Number(fpctrl.moveRight);
        let ud = Number(fpctrl.moveUp) - Number(fpctrl.moveDown);
        let camera_direction = firstPersonControls.getDirection(new THREE.Vector3());
        if ( fpctrl.moveForward || fpctrl.moveBackward ){
            camera.position.x += camera_direction.x * delta * fw;
            // camera.position.y += camera_direction.y * delta * fw; // Subnautica. 
            camera.position.y = manager.renderManager.scene_json.coarseWallHeight / 2;
            camera.position.z += camera_direction.z * delta * fw;
            orbitControls.target.x += camera_direction.x * delta * fw;
            // orbitControls.target.y += camera_direction.y * delta * fw; // Subnautica. 
            orbitControls.target.z += camera_direction.z * delta * fw;
        }
        if ( fpctrl.moveLeft || fpctrl.moveRight ){
            let v = new THREE.Vector3().crossVectors(camera.up, camera_direction);
            camera.position.x += v.x * delta * lr;
            // camera.position.y += v.y * delta * lr; // Subnautica. 
            camera.position.y = manager.renderManager.scene_json.coarseWallHeight / 2;
            camera.position.z += v.z * delta * lr;
            orbitControls.target.x = camera_direction.x + camera.position.x;
            orbitControls.target.z = camera_direction.z + camera.position.z;
            orbitControls.target.y = camera_direction.y + camera.position.y;
        }
        if ( fpctrl.moveUp || fpctrl.moveDown ){
            // camera.position.y += delta * ud; // Subnautica. 
            // orbitControls.target.y = camera_direction.y + camera.position.y; // Subnautica. 
        }
    }
};

const firstPersonLockFunction = function(){
    firstPersonControls.lock();
}

const firstPersonOn = function(){
    if(!manager.renderManager.scene_json.coarseWallHeight){
        manager.renderManager.scene_json.coarseWallHeight = 2.6
    }
    camera.position.y = manager.renderManager.scene_json.coarseWallHeight / 2; 
    orbitControls.enabled = false;
    fpCtrlMode = true;
    firstPersonControls.connect();
    document.removeEventListener('click', onClickObj)
    document.removeEventListener('keydown', onKeyDown);
    document.removeEventListener('keyup', onKeyUp);
    document.addEventListener('click', firstPersonLockFunction);
    document.addEventListener('keydown', onKeyDownFirstPerson, false);
    document.addEventListener('keyup', onKeyUpFirstPerson, false);
}

const firstPersonOff = function(){
    orbitControls.enabled = true;
    fpCtrlMode = false;
    firstPersonControls.disconnect();
    document.removeEventListener('click', firstPersonLockFunction);
    document.removeEventListener('keydown', onKeyDownFirstPerson);
    document.removeEventListener('keyup', onKeyUpFirstPerson);
    document.addEventListener('keydown', onKeyDown);
    document.addEventListener('keyup', onKeyUp);
}
