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
