var Q_DOWN = false;
var E_DOWN = false;
var prevTime = performance.now();
var QE_initialization = function(){};
var keyboard_update = function(){
  var time = performance.now();
  var delta = ( time - prevTime ) / 300;
  if(Q_DOWN){
    camera.rotation.y += delta;
  }
  if(E_DOWN){
    camera.rotation.y -= delta;
  }
  prevTime = time;
};
var onKeyDown = function (event) {
    switch ( event.keyCode ) {
        case 81: // Q
            Q_DOWN = true;
            break;
        case 69: // E
            E_DOWN = true;
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
