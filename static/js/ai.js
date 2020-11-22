var mage_add_control = function(event){
  scenecanvas.style.cursor = 'url(/static/click.png) 27 24, crosshair';
  On_Magic_ADD = true;
}

var mage_add_object = function(){
  var d = {};
  var pos = findGroundTranslation();
  d.roomjson = manager.renderManager.scene_json.rooms[currentRoomId];
  d.translate = [pos.x, pos.y, pos.z];
  $.ajax({
    type: "POST",
    contentType: "application/json; charset=utf-8",
    url: "/magic_position",
    crossDomain: true,
    data: JSON.stringify(d),
    success: function (data) {
      console.log(data);
      INSERT_OBJ = {
        "modelId":data.name,
        "translate": [
          pos.x,
          pos.y,
          pos.z
        ],
        "scale": [
          data.scale[0],
          data.scale[1],
          data.scale[2]
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

var auxiliary_control = function(){
  var autoinsert_button = document.getElementById("auxiliary_button");
  AUXILIARY_MODE = !AUXILIARY_MODE;
  if(AUXILIARY_MODE){
    auxiliaryMode();
    autoinsert_button.style.backgroundColor = '#9400D3';
  }else{
    // remove 'auxiliaryObject' in the scene; 
    scene.remove(scene.getObjectByName(AUXILIARY_NAME));
    autoinsert_button.style.backgroundColor = '#43CD80';
  }
}

let auxiliaryLoadWall = async function(){
  $.ajax({
    type: "POST",
    contentType: "application/json; charset=utf-8",
    url: "/priors_of_wall",
    data: JSON.stringify(manager.renderManager.scene_json.rooms[currentRoomId]),
    success: function (data) {
      data = JSON.parse(data);
      manager.renderManager.scene_json.rooms[currentRoomId].auxiliaryWallObj = data;
      data.object.forEach(o => {
        loadObjectToCache(o);
      })
    }
  });
}

let auxiliaryRoom = async function(){
    $.ajax({
      type: "POST",
      contentType: "application/json; charset=utf-8",
      url: "/priors_of_roomShape",
      data: JSON.stringify(manager.renderManager.scene_json.rooms[currentRoomId]),
      success: function (data) {
        data = JSON.parse(data);
        data.roomShapeTensor = tf.tensor(data.room_meta);
        data.tensor = tf.tensor(data.prior);
        manager.renderManager.scene_json.rooms[currentRoomId].auxiliaryDomObj = data;
        data.object.forEach(o => {
          loadObjectToCache(o);
        })
      }
    });
}

let auxiliaryPrior;
let auxiliaryMode = async function(){
  if(currentRoomId === undefined){
    return;
  }
  manager.renderManager.scene_json.rooms[currentRoomId].objList = 
  manager.renderManager.scene_json.rooms[currentRoomId].objList
  .filter( item => item !== null && item !== undefined ); 
  auxiliaryRoom();
  auxiliaryLoadWall();
  $.ajax({
    type: "POST",
    contentType: "application/json; charset=utf-8",
    url: "/priors_of_objlist",
    data: JSON.stringify(manager.renderManager.scene_json.rooms[currentRoomId]),
    success: function (data) {
      data = JSON.parse(data);
      auxiliaryPrior = data;
      manager.renderManager.scene_json.rooms[currentRoomId].auxiliarySecObj = data;
      auxiliaryPrior.tensor = tf.tensor(auxiliaryPrior.prior);
      data.object.forEach(o => {
        loadObjectToCache(o);
      })
    }
  });
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

var auto_layout = function(){
  if (currentRoomId === undefined) {
      console.log("No room is specified. ");
      return
  }
  $.ajax({
      type: "POST",
      contentType: "application/json; charset=utf-8",
      url: "/sklayout",
      data: JSON.stringify(manager.renderManager.scene_json.rooms[currentRoomId]),
      success: function (data) {
          data = JSON.parse(data);
          temp = data;
          manager.renderManager.scene_json.rooms[currentRoomId].objList = data.objList;
          manager.renderManager.refresh_instances();
      }
  });
};

var palette_recommendation = function(){
  if(currentRoomId === undefined){
    return;
  }
  $.ajax({
    type: "POST",
    contentType: "application/json; charset=utf-8",
    url: "/palette_recommendation",
    crossDomain: true,
    data: JSON.stringify(manager.renderManager.scene_json.rooms[currentRoomId].objList),
    success: function (data) {
      while(catalogItems.firstChild){
    		catalogItems.firstChild.remove();
    	}
      console.log(data);
      data.forEach(function(item){
  			var iDiv = document.createElement('div');
  			iDiv.className = "catalogItem";
  			iDiv.style.backgroundImage = "url(" + item.thumbnail + ")";
  			iDiv.setAttribute('objectID', item.id);
  			iDiv.setAttribute('objectName', item.name);
        iDiv.setAttribute('semantic', item.semantic);
  			iDiv.addEventListener('click', clickCatalogItem)
  			catalogItems.appendChild(iDiv);
  		})
    },
    dataType: "json"
  });
}
