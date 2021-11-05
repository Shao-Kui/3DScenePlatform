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

const paletteInit = function(){
    let svg = d3.select('#scenePaletteSVG');
    let width = svg.attr('width'), height = svg.attr('height');
    svg.attr("viewBox", [width / 2 - 100, height / 2 - 100, 200, 200]);
    let g = svg.select("#scenePaletteSVG g");
    function zoomed({transform}) {
        g.attr("transform", transform);
    }
    const zoom = d3.zoom()
    .scaleExtent([0.1, 40])
    .on("zoom", zoomed);
    svg.call(zoom);
}

// const clickPaletteItem = function(e, d){
//     e.preventDefault();
//     console.log(e);
//     scene.remove(scene.getObjectByName(INSERT_NAME));
//     // avoid confictions between ordinary insertions and the auxiliary mode; 
//     if(!manager.renderManager.scene_json || AUXILIARY_MODE) return;    
//     if(e.type === 'contextmenu'){
//         On_MAGEADD = true;
//         loadSingleObjectPrior(d.modelId);
//     }else{
//         On_ADD = true;
//     }
//     scenecanvas.style.cursor = "crosshair";
//     loadObjectToCache(d.modelId); 
//     INSERT_OBJ = {
//         "modelId": d.modelId,
//         "coarseSemantic": d.coarseSemantic, 
//         "translate": [0.0, 0.0, 0.0],"scale": [1.0, 1.0, 1.0],"rotate": [0.0, 0.0, 0.0]
//     };
// }

const paletteRender = function(elements){
    let svg = d3.select('#scenePaletteSVG');
    let width = svg.attr('width'), height = svg.attr('height');
    let g = d3.select("#scenePaletteSVG g").attr('id', 'scenePaletteGroup');
    const RADIUS = 40;
    g.selectAll('.mypattern').data(elements).join('pattern').attr('class', 'mypattern')
    .attr("id", d => `ls_${d.index}_img`).attr("width", 1).attr("height", 1).attr("patternUnits", 'objectBoundingBox')
    .append("svg:image")
    .attr("href", d => `/thumbnail/${d.modelId}`)
    .attr('preserveAspectRatio', 'xMidYMid slice')
    .attr("width", RADIUS*2).attr("height", RADIUS*2);
    let circles = g.selectAll('circle').data(elements).join('circle').attr('r', RADIUS)
    .attr("fill", d => `url(#ls_${d.index}_img)`)
    .on('click', clickCatalogItem)
    .on('contextmenu', clickCatalogItem);
    let links = [];
    for(let i = 1; i < elements.length; i++){
        let dis = Math.sqrt(Math.pow(elements[i].x-elements[0].x, 2) + Math.pow(elements[i].y-elements[0].y, 2));
        links.push({
            "source": elements[i].index,
            "target": elements[0].index,
            'dis': dis > RADIUS*2 ? dis : RADIUS*2
        });
    }
    let ticked = () => circles.attr('cx', d => d.x).attr('cy', d => d.y);
    let disFunc = (link) => link.dis; 
    simulation = d3.forceSimulation(elements)
    .alphaDecay(0.05).velocityDecay(0.05)
    .force('manyBody', d3.forceManyBody().strength(-30).distanceMin(RADIUS*2))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force("link", d3.forceLink(links).strength(0.01).distance(disFunc))
    .on('tick', ticked);
}

const paletteExpand = function(modelIds){
    $.ajax({
        type: "POST",
        contentType: "application/json; charset=utf-8",
        url: "/rec_ls_euc",
        dataType: "json",
        data: JSON.stringify(modelIds),
        success: paletteRender
    });
}

var palette_recommendation = function(){
    if(currentRoomId === undefined){
      return;
    }
    
}
