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

const refreshSceneFutureRoomTypes = function(){
    let roomtypes = Object.keys(
    manager.renderManager.scene_json.sceneFuture[`${currentRoomId}`]
    [manager.renderManager.scene_json.rooms[currentRoomId].state]);
    while (catalogItems.firstChild) {
        catalogItems.firstChild.remove();
    }
    roomtypes.forEach(function (rt){
        let iDiv = document.createElement('div');
        iDiv.className = "catalogItem";
        iDiv.textContent = rt;
        // iDiv.style.backgroundImage = "url(" + item.thumbnail + ")";
        // iDiv.setAttribute('objectID', item.id);
        // iDiv.setAttribute('objectName', item.name);
        // iDiv.setAttribute('modelId', item.name);
        // iDiv.setAttribute('coarseSemantic', item.semantic);
        // iDiv.setAttribute('semantic', item.semantic);
        iDiv.addEventListener('click', clickSceneFutureIterms);
        catalogItems.appendChild(iDiv);
    });
}

const getUUID = function(){
    let uuid;
    loadMoreServerUUIDs(1);
    if(!uuid) uuid = serverUUIDs.pop(); 
    if(!uuid) uuid = THREE.MathUtils.generateUUID();
    return uuid;
}

const standardizeRotate = function(rotate, refRotate){
    if(rotate[0] === 0 && rotate[2] === 0){
        rotate[1] = Math.atan2(Math.sin(rotate[1]), Math.cos(rotate[1]));
        if(Math.abs(rotate[1] - refRotate[1]) > Math.PI){
            if(rotate[1] < refRotate[1]){
                rotate[1] += Math.PI * 2;
            }else{
                rotate[1] -= Math.PI * 2;
            }
        }
    }
}

const copyTransform = function(transform){
    return {'translate': [...transform.translate], 'rotate': [...transform.rotate], 'scale': [...transform.scale]};
} 

const clickSceneFutureIterms = function (e) {
    e.preventDefault();
    let roomTransitions = manager.renderManager.scene_json.sceneFuture[`${currentRoomId}`]
    [manager.renderManager.scene_json.rooms[currentRoomId].state]
    [$(e.target).text()];
    let room = manager.renderManager.scene_json.rooms[currentRoomId];
    const previousObjList = [...room.objList];
    previousObjList.sort((a,b) => a.sforder - b.sforder);
    let i;
    for(i = 0; i < previousObjList.length; i++){
        let next = roomTransitions[i];
        let currentKey = previousObjList[i].key;
        if(next.type === "detachable"){
            removeObjectByUUID(currentKey, true);
            next.parts.forEach(part => {
                standardizeRotate(part.startTransform.rotate, part.rotate);
                // let uuid = getUUID();
                // let object = addObjectByUUID(uuid, part.modelId, currentRoomId, {'translate': [...part.startTransform.translate], 'rotate': [...part.startTransform.rotate], 'scale': [...part.startTransform.scale]});
                let object = addObjectFromCache(part.modelId, copyTransform(part.startTransform));
                let uuid = object.name;
                gsap.to(manager.renderManager.instanceKeyCache[uuid]['position'], {
                    duration: 1,
                    x: part['translate'][0],
                    y: part['translate'][1],
                    z: part['translate'][2]
                }).then(() => {
                    manager.renderManager.instanceKeyCache[uuid].userData.json.sforder = part.sforder;
                    synchronize_json_object(object);
                })
                gsap.to(manager.renderManager.instanceKeyCache[uuid]['rotation'], {
                    duration: 1,
                    x: part['rotate'][0],
                    y: part['rotate'][1],
                    z: part['rotate'][2]
                })
            });
            continue;
        }
        if(next.type === "movetransformable"){
            if(next.toState !== 'origin' && previousObjList[i].startState === 'origin'){
                let action = manager.renderManager.instanceKeyCache[previousObjList[i].key].actions[next.toState];
                action.getMixer().addEventListener('finished', e => {
                    action.reset();action.paused = true;
                    action.time = action.getClip().duration;
                });
                action.reset();action.paused = true;
                action.setDuration(1);action.timeScale = Math.abs(action.timeScale);
                action.time = 0;
                action.paused = false;
            }else if(next.toState === 'origin' && previousObjList[i].startState !== 'origin'){
                let action = manager.renderManager.instanceKeyCache[previousObjList[i].key].actions[previousObjList[i].startState];
                action.getMixer().addEventListener('finished', e => {action.reset();action.paused = true;action.time = 0;});
                action.reset();action.paused = true;
                action.setDuration(1);action.timeScale = -Math.abs(action.timeScale);
                action.time = action.getClip().duration;
                action.paused = false;
            }else if(next.toState !== 'origin' && previousObjList[i].startState !== 'origin'){

            }
            manager.renderManager.instanceKeyCache[previousObjList[i].key].userData.json.startState = next.toState;
        }
        standardizeRotate(next.rotate, previousObjList[i]['rotate']);
        gsap.to(manager.renderManager.instanceKeyCache[previousObjList[i].key]['position'], {
            duration: 1,
            x: next['translate'][0],
            y: next['translate'][1],
            z: next['translate'][2]
        }).then(() => {
            if(next.type === "movable" || next.type === "movetransformable"){
                synchronize_json_object(manager.renderManager.instanceKeyCache[currentKey]);
                return;
            }
            if(next.type === "composablepart"){
                removeObjectByUUID(currentKey, true);
                return;
            }
            if(next.type === 'composable'){
                let object = addObjectFromCache(next.modelId, copyTransform(next.finalTransform));
                uuid = object.name;
            }else if(next.type === 'packable_in'){
                removeObjectByUUID(currentKey, true);
                return;
            }
            else{
                let object = addObjectFromCache(next.modelId, copyTransform(next));
                uuid = object.name;
            }
            manager.renderManager.instanceKeyCache[uuid].userData.json.sforder = next.sforder;
            removeObjectByUUID(currentKey, true);
        });
        gsap.to(manager.renderManager.instanceKeyCache[previousObjList[i].key]['rotation'], {
            duration: 1,
            x: next['rotate'][0],
            y: next['rotate'][1],
            z: next['rotate'][2]
        });
        if(["movetransformable", "transformable"].includes(next.type)){
            let tScale = [0,0,0];
            tScale[0] = (objectCache[next.modelId].boundingBox.max.x-objectCache[next.modelId].boundingBox.min.x) / (objectCache[previousObjList[i].modelId].boundingBox.max.x-objectCache[previousObjList[i].modelId].boundingBox.min.x);
            tScale[1] = (objectCache[next.modelId].boundingBox.max.y-objectCache[next.modelId].boundingBox.min.y) / (objectCache[previousObjList[i].modelId].boundingBox.max.y-objectCache[previousObjList[i].modelId].boundingBox.min.y);
            tScale[2] = (objectCache[next.modelId].boundingBox.max.z-objectCache[next.modelId].boundingBox.min.z) / (objectCache[previousObjList[i].modelId].boundingBox.max.z-objectCache[previousObjList[i].modelId].boundingBox.min.z);
            gsap.to(manager.renderManager.instanceKeyCache[previousObjList[i].key]['scale'], {
                duration: 1,
                x: tScale[0],
                y: tScale[1],
                z: tScale[2]
            });
        }
    }
    for(; i < roomTransitions.length; i++){
        let next = roomTransitions[i];
        let uuid, object;
        if(next.type === "packable_out"){
            object = addObjectFromCache(next.modelId, copyTransform(next.inittransform));
            uuid = object.name;
            manager.renderManager.instanceKeyCache[uuid].userData.json.sforder = next.sforder;
        }
        gsap.to(manager.renderManager.instanceKeyCache[uuid]['position'], {
            duration: 1,
            x: next['translate'][0],
            y: next['translate'][1],
            z: next['translate'][2]
        }).then(() => {
            synchronize_json_object(object);
        });
        gsap.to(manager.renderManager.instanceKeyCache[uuid]['rotation'], {
            duration: 1,
            x: next['rotate'][0],
            y: next['rotate'][1],
            z: next['rotate'][2]
        });
    }
    // console.log(nextOrder);
    // Object.keys(nextOrder).forEach(key => {
    //     console.log(manager.renderManager.instanceKeyCache[key].userData.json);
    //     manager.renderManager.instanceKeyCache[key].userData.json.sforder = nextOrder[key];
    // });
    room.objList.sort((a,b) => a.sforder - b.sforder);
    manager.renderManager.scene_json.rooms[currentRoomId].state = $(e.target).text();
    refreshSceneFutureRoomTypes();
}
