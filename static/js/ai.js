var mage_add_control = function(event){
  scenecanvas.style.cursor = 'url(/static/click.png) 27 24, crosshair';
  On_Magic_ADD = true;
}

var mage_add_object = function(){
  var d = {};
  var pos = findGroundTranslation();
  d.objList = manager.renderManager.scene_json.rooms[currentRoomId].objList;
  d.translate = [pos.x, pos.y, pos.z];
  $.ajax({
    type: "POST",
    contentType: "application/json; charset=utf-8",
    url: "/magic_position",
    crossDomain: true,
    data: JSON.stringify(d),
    success: function (data) {
      console.log(data);
      if(data.valid === 0){
        return;
      }
      INSERT_OBJ = {
        "modelId":data.name,
        "translate": [
          pos.x,
          pos.y,
          pos.z
        ],
        "scale": [
          1.0,
          1.0,
          1.0
        ],
        "rotate": [
          data.rotate[0],
          data.rotate[1],
          data.rotate[2]
        ]
      };
      INSERT_OBJ.roomId = currentRoomId;
      manager.renderManager.scene_json.rooms[currentRoomId].objList.push(INSERT_OBJ);
      manager.renderManager.refresh_instances();
    },
    dataType: "json"
  });
};

var auto_insert_control = function(){
  var autoinsert_button = document.getElementById("autoinsert_button");
  Auto_Insert_Mode = !Auto_Insert_Mode;
  if(Auto_Insert_Mode){
    autoinsert_button.style.backgroundColor = '#9400D3';
  }else{
    autoinsert_button.style.backgroundColor = '#43CD80';
  }
}

var mage_auto_insert = function(e){
  if(currentRoomId === undefined){
    return;
  }
  var d = {};
  d.objList = manager.renderManager.scene_json.rooms[currentRoomId].objList;
  d.category = $(e.target).attr("semantic");
  d.origin = manager.renderManager.scene_json.origin;
  d.modelId = manager.renderManager.scene_json.rooms[currentRoomId].modelId;
  d.objectName = $(e.target).attr("objectName");
  $.ajax({
    type: "POST",
    contentType: "application/json; charset=utf-8",
    url: "/magic_category",
    crossDomain: true,
    data: JSON.stringify(d),
    success: function (data) {
      console.log(data);
      if(data.valid === 0){
        return;
      }
      INSERT_OBJ = {
        "modelId":$(e.target).attr("objectName"),
        "translate": [
          data.translate[0],
          data.translate[1],
          data.translate[2]
        ],
        "scale": [
          1.0,
          1.0,
          1.0
        ],
        "rotate": [
          data.rotate[0],
          data.rotate[1],
          data.rotate[2]
        ]
      };
      INSERT_OBJ.roomId = currentRoomId;
      manager.renderManager.scene_json.rooms[currentRoomId].objList.push(INSERT_OBJ);
      manager.renderManager.refresh_instances();
    },
    dataType: "json"
  });
};

var auto_layout = function(event){
  if(currentRoomId === undefined){
    return;
  }
  var room = manager.renderManager.scene_json.rooms[currentRoomId];
  if(room.roomTypes.length === 0){
    return;
  }
  var d = {};
  d.body = {};
  d.body.roomtype = room.roomTypes[0];
  d.body.origin = room.origin;
  //d.body.level = ;
  d.body.roomid = room.modelId;
  $.ajax({
    type: "POST",
    contentType: "application/json; charset=utf-8",
    url: "http://166.111.71.45:11426/generate",
    crossDomain: true,
    data: JSON.stringify(d),
    success: function (data) {
      manager.renderManager.scene_json.rooms[currentRoomId].objList = data;
      manager.renderManager.scene_json.rooms[currentRoomId].objList.forEach(function(obj){
        obj.roomId = currentRoomId;
      });
      manager.renderManager.refresh_instances();
    },
    dataType: "json"
  });
};
