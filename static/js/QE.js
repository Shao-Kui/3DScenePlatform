var Q_DOWN = false;
var E_DOWN = false;
var prevTime = performance.now();
var QE_initialization = function(){};
var keyboard_update = function(){
  var time = performance.now();
  var delta = 0; // ( time - prevTime ) / 300;
  if(Q_DOWN){
    camera.rotation.y += delta;
  }
  if(E_DOWN){
    camera.rotation.y -= delta;
  }
  prevTime = time;
};
let topdownview = function(){
  let bbox = manager.renderManager.scene_json.rooms[currentRoomId].bbox; 
  let lx = (bbox.max[0] + bbox.min[0]) / 2;
  let ymax = bbox.max[1];
  let lz = (bbox.max[2] + bbox.min[2]) / 2;
  camera.rotation.order = 'YXZ';
  camera.position.set(lx, ymax + 1, lz);
  camera.lookAt(lx, 0, lz);
  orbitControls.target.set(lx, 0, lz);
};
var onKeyDown = function (event) {
  switch ( event.keyCode ) {
      case 81: // Q
          Q_DOWN = true;
          break;
      case 69: // E
          E_DOWN = true;
          break;
      case 32: // white space
        topdownview();
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
  }
};
