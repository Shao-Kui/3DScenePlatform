const auto_layout = function(){
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
            refreshRoomByID(currentRoomId, data.objList);
        }
    });
};

const auto_layout_PlanIT = function(){
    if (currentRoomId === undefined) {
        console.log("No room is specified. ");
        return
    }
    $.ajax({
        type: "POST",
        contentType: "application/json; charset=utf-8",
        url: "/planit",
        data: JSON.stringify(manager.renderManager.scene_json.rooms[currentRoomId]),
        success: function (data) {
            data = JSON.parse(data);
            temp = data;
            refreshRoomByID(currentRoomId, data.objList);
        }
    });
};

const paletteRender = function(modelIds){
    let svg = d3.select('#scenePaletteSVG');
    svg.selectAll('.latentElement').remove();
    let width = svg.attr('width'), height = svg.attr('height');
}

const paletteExpand = function(modelIds){
    $.ajax({
        type: "POST",
        contentType: "application/json; charset=utf-8",
        url: "/rec_ls_euc",
        dataType: "json",
        data: JSON.stringify(modelIds),
        success: function (data) {
            paletteRender(JSON.parse(data));
        }
    });
}

var palette_recommendation = function(){
    if(currentRoomId === undefined){
      return;
    }
    
}
