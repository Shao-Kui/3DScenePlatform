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
        if(!event.value){
            synchronize_json_object(INTERSECT_OBJ);
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
        }else if(transformControls.mode === 'rotate'){
            transformObject3DOnly(INTERSECT_OBJ.userData.key, 
                [INTERSECT_OBJ.rotation.x, INTERSECT_OBJ.rotation.y, INTERSECT_OBJ.rotation.z], 'rotation');
        }else if(transformControls.mode === 'scale'){
            transformObject3DOnly(INTERSECT_OBJ.userData.key, 
                [INTERSECT_OBJ.scale.x, INTERSECT_OBJ.scale.y, INTERSECT_OBJ.scale.z], 'scale');
        }
    });
}

const topdownview = function(){
    let bbox = manager.renderManager.scene_json.rooms[currentRoomId].bbox; 
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
        orbitControls.sphericalDelta.theta += 3.14/2;
        orbitControls.update();
        // gsap.to(orbitControls.sphericalDelta, {
        //     duration: 1,
        //     theta: thetaTar,
        // });
        // tCamUp = gsap.to(camera.up, {
        //     duration: 1,
        //     x: 1,
        //     y: 0,
        //     z: 0
        // });
    }else{
        // tCamUp = gsap.to(camera.up, {
        //     duration: 1,
        //     x: 0,
        //     y: 0,
        //     z: 1
        // });
    }
    // gsap.to(camera.position, {
    //     duration: 1,
    //     x: lx,
    //     y: camHeight,
    //     z: lz
    // });
    // gsap.to(orbitControls.target, {
    //     duration: 1,
    //     x: lx,
    //     y: 0,
    //     z: lz
    // });
    // gsap.to(camera.up, {
    //     duration: 1,
    //     x: 0,
    //     y: 1,
    //     z: 0
    // });
};

var ctrlPressing = false;
var duplicateTimes = 1;
const onKeyDown = function(event){
    if(event.target.matches("input")) return;
    pressedKeys[event.keyCode] = true;
    switch ( event.keyCode ) {
        case 81: // Q
            Q_DOWN = true;
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
        case 85: // U
            // start to record audio; 
            reco.record();
            break;
        case 82: // R
            render_function();
            break;
        case 83: // S
            downloadSceneJson();
            break;
        case 49: // 1
            auxiliary_catlist(-1)
            break;
        case 50: // 2
            auxiliary_catlist(1)
            break;
        case 192: // `
            auxiliary_catlist(0)
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
            ctrlPressing = true;
            break;
        case 46:
            if(INTERSECT_OBJ === undefined){break;}
            radial_remove_control();
            break;

        case 68: // d
            if(INTERSECT_OBJ === undefined){break;}
            addObjectFromCache(
                modelId=INTERSECT_OBJ.userData.modelId,
                transform={
                    'translate': [INTERSECT_OBJ.position.x+0.1*duplicateTimes, INTERSECT_OBJ.position.y, INTERSECT_OBJ.position.z+0.1*duplicateTimes], 
                    'rotate': [INTERSECT_OBJ.rotation.x, INTERSECT_OBJ.rotation.y, INTERSECT_OBJ.rotation.z],
                    'scale': [INTERSECT_OBJ.scale.x,INTERSECT_OBJ.scale.y,INTERSECT_OBJ.scale.z]
                }
            );
            duplicateTimes += 1;
            break;
    }
    if(event.keyCode === 90 && ctrlPressing){
        if(commandStack.length > 0){
            let cmd = commandStack.pop();
            onlineFuncList[cmd.funcName].apply(null, cmd.args);
            emitFunctionCall(cmd.funcName, cmd.args);
        }
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
        case 17:
            ctrlPressing = false;
            break;
          
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
