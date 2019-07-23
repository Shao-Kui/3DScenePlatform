var directionalLight;
var ambientLight;

var render_initialization = function(){
  directionalLight = new THREE.DirectionalLight(0xFFFFFF, 0.3);
  directionalLight.castShadow = true;
  directionalLight.position.y = 0.5;
  scene.add(directionalLight);

  var ambientLight=new THREE.AmbientLight(0xFFFFFF, 0.9);
  scene.add(ambientLight);
}

var render_update = function(){
  var time= Date.now() * 0.0001;
  directionalLight.position.x = Math.sin(time);
  directionalLight.position.z = Math.cos(time);
}
