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
let topdownview = function(){
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
  camera.rotation.order = 'YXZ';
  camera.position.set(lx, camHeight, lz);
  camera.lookAt(lx, 0, lz);
  orbitControls.target.set(lx, 0, lz);
  let lx_length = bbox.max[0] - bbox.min[0];
  let lz_length = bbox.max[2] - bbox.min[2];
  if(lz_length > lx_length){
    orbitControls.sphericalDelta.theta+=3.14/2;
    orbitControls.update();
  }
};
var onKeyDown = function(event){
    if(event.target.matches("input")) return;
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
        case 49: // 1
            auxiliary_catlist(-1)
            break;
        case 50: // 2
            auxiliary_catlist(1)
            break;
        case 192: // `
            auxiliary_catlist(0)
            break;
    }
};

var onKeyUp = function (event) {
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
          
  }
};
