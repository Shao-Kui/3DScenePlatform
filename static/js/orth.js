var orth_initialization = function(){
  var geometry = new THREE.Geometry();
  geometry.vertices.push(new THREE.Vector3(-1, 100, 1));
  geometry.vertices.push(new THREE.Vector3(1, 100, 1));
  geometry.vertices.push(new THREE.Vector3(1, 100, -1));
  geometry.vertices.push(new THREE.Vector3(-1, 100, -1));
  geometry.vertices.push(new THREE.Vector3(-1, 100, 1));
  var material = new THREE.LineBasicMaterial( { color: 0x000000, linewidth: 10 } );
  orthline = new THREE.Line( geometry, material );
  scene.add( orthline );
}

var orth_view_port_update = function(){
  if(!manager.renderManager.scene_json){
    orthline.geometry.vertices[0].x = 39;orthline.geometry.vertices[0].z = 46;
    orthline.geometry.vertices[1].x = 40;orthline.geometry.vertices[1].z = 50;
    orthline.geometry.vertices[2].x = 43;orthline.geometry.vertices[2].z = 37;
    orthline.geometry.vertices[3].x = 39;orthline.geometry.vertices[3].z = 37;
    orthline.geometry.vertices[4].x = 39;orthline.geometry.vertices[4].z = 46;
    orthline.geometry.verticesNeedUpdate = true;
    return;
  }
  var y_ =  manager.renderManager.scene_json.bbox.max[1] + manager.renderManager.scene_json.bbox.min[1];
  y_ = y_ / 2;
  var pos_left_up = screen_to_ground(-1, 1, y_);
  var pos_right_up = screen_to_ground(1, 1, y_);
  var pos_left_down = screen_to_ground(1, -1, y_);
  var pos_right_down = screen_to_ground(-1, -1, y_);
  if(!ALL_SCENE_READY){
    orthline.geometry.vertices[0].x = 39;orthline.geometry.vertices[0].z = 46;
  }else{
    orthline.geometry.vertices[0].x = pos_left_up.x;orthline.geometry.vertices[0].z = pos_left_up.z;
  }
  orthline.geometry.vertices[1].x = pos_right_up.x;orthline.geometry.vertices[1].z = pos_right_up.z;
  orthline.geometry.vertices[2].x = pos_left_down.x;orthline.geometry.vertices[2].z = pos_left_down.z;
  orthline.geometry.vertices[3].x = pos_right_down.x;orthline.geometry.vertices[3].z = pos_right_down.z;
  orthline.geometry.vertices[4].x = pos_left_up.x;orthline.geometry.vertices[4].z = pos_left_up.z;
  orthline.geometry.verticesNeedUpdate = true;
}

var get_orthline_mid = function(){
  var x = 0.0;
  var y = 0.0;
  for(var i = 0; i < 4; i++){
    x += orthline.geometry.vertices[i].x;
    y += orthline.geometry.vertices[i].z;
  }
  x = x / 4;
  y = y / 4;
  return new THREE.Vector3(x, 0, y);
}

var last_look;
var orth_mousedown = function(event){
  if(manager.renderManager.scene_json === undefined){
    return;
  }
  On_Orth_MOVE = true;
  orthline.visible = false;
  orbitControls.enabled = false;
  var x_ = (orthmouse.x + 1)/2;
  var z_ = (orthmouse.y + 1)/2;
  var bbox = manager.renderManager.scene_json.bbox;
  var lx = (1 - x_) * bbox.min[0] + x_ * bbox.max[0];
  var lz = z_ * bbox.min[2] + (1 - z_) * bbox.max[2];
  var om = get_orthline_mid();
  last_look = new THREE.Vector3(lx, 0, lz);
  manager.renderManager.camera.position.x += (last_look.x - om.x);
  manager.renderManager.camera.position.z += (last_look.z - om.z);
};
var orth_mouseup = function(event){
  if(manager.renderManager.scene_json === undefined){
    return;
  }
  var x_ = (orthmouse.x + 1)/2;
  var z_ = (orthmouse.y + 1)/2;
  var bbox = manager.renderManager.scene_json.bbox;
  var lx = (1 - x_) * bbox.min[0] + x_ * bbox.max[0];
  var lz = z_ * bbox.min[2] + (1 - z_) * bbox.max[2];
  orbitControls.target.set(lx, 0, lz);
  On_Orth_MOVE = false;
  orthline.visible = true;
  orbitControls.enabled = true;
};
var orth_mousemove = function(event){
  orthmouse.x = ( (event.clientX - $(orthcanvas).offset().left) / orthcanvas.clientWidth ) * 2 - 1;
  orthmouse.y = - ( (event.clientY - $(orthcanvas).offset().top) / orthcanvas.clientHeight ) * 2 + 1;
  if(On_Orth_MOVE){
    var x_ = (orthmouse.x + 1)/2;
    var y_ = (orthmouse.y + 1)/2;
    var bbox = manager.renderManager.scene_json.bbox;
    var lx = (1 - x_) * bbox.min[0] + x_ * bbox.max[0];
    var lz = y_ * bbox.min[2] + (1 - y_) * bbox.max[2];
    //manager.renderManager.camera.lookAt(lx, 0, lz);
    //orbitControls.target.set(lx, 0, lz);
    manager.renderManager.camera.position.x += (lx - last_look.x);
    manager.renderManager.camera.position.z += (lz - last_look.z);
    last_look.set(lx, 0, lz);
  }
};
var orth_mouseclick = function(event){
  //console.log(orthmouse);
};
