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

const atsc = (theta) => Math.atan2(Math.sin(theta), Math.cos(theta));

const standardizeRotate = function(rotate, refRotate){
    if(rotate[0] === 0 && rotate[2] === 0){
        rotate[1] = Math.atan2(Math.sin(rotate[1]), Math.cos(rotate[1]));
        // refRotate[1] = Math.atan2(Math.sin(refRotate[1]), Math.cos(refRotate[1]));
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
                actionForthToTarget(action);
            }else if(next.toState === 'origin' && previousObjList[i].startState !== 'origin'){
                let action = manager.renderManager.instanceKeyCache[previousObjList[i].key].actions[previousObjList[i].startState];
                actionBackToOrigin(action);
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

const getDerivationByID = function(totalAnimaID, derivationID){
    $.getJSON(`/static/dataset/infiniteLayout/${totalAnimaID}/${derivationID}.json`, function (data) {
        console.log(data);
    });
}

const getCurrentIndexing = function(){
    // Note that for InfiniteLayout, we only consider a single room, so every floorplan starts from the first room. 
    let index = [];
    manager.renderManager.scene_json.rooms[0].objList.forEach(o => {if('sforder' in o){index.push(0);}});
    manager.renderManager.scene_json.rooms[0].objList.forEach(o => {if('sforder' in o){index[o.sforder] = currentAnimation.state_encoding[o.sforder].indexOf(o.startState);}});
    return index.join("") + "_0" // `_${manager.renderManager.scene_json.rooms[0].sflayoutid}`;
}

const operationFuture = function(){
    let taID = manager.renderManager.scene_json.rooms[0].totalAnimaID;
    floorPlanMapping.clear();
    if(manager.renderManager.scene_json.rooms[0].sflayoutid === undefined){
        manager.renderManager.scene_json.rooms[0].sflayoutid = getCurrentIndexing();
    }
    let index = manager.renderManager.scene_json.rooms[0].sflayoutid // getCurrentIndexing();
    while (catalogItems.firstChild) {
        catalogItems.firstChild.remove();
    }
    let sub = currentAnimation.index[index];
    if(currentAnimation.index[index].length >= 20){
        sub = currentAnimation.index[index].slice(0, 20);
    }
    sub.forEach(item => {
        let iDiv = document.createElement('div');
        let image = new Image();
        image.onload = function(){
            iDiv.style.width = `${$(window).width() * 0.10}px`;
            iDiv.style.height = `${$(window).width() * 0.10 / (image.width / image.height)}px`;
        };
        let imgdir = `/static/dataset/infiniteLayout/${taID}img/${item.target_node}.png`;
        image.src = imgdir;
        iDiv.className = "mapping catalogItem";
        iDiv.style.backgroundImage = `url(${imgdir})`;
        iDiv.style.backgroundSize = '100% 100%';
        iDiv.style.visibility = 'visible';
        iDiv.addEventListener('contextmenu', e => {e.preventDefault();mappingHover(e);});
        iDiv.addEventListener('mouseout', mappingLeave);
        iDiv.addEventListener('click', (e) => {
            $.getJSON(`/static/dataset/infiniteLayout/${taID}/${item.anim_id}.json`, function(result){
                let meta = $(e.target).data("meta");
                if(meta.anim_forward){
                    sceneTransformTo(result.actions);
                }else{
                    sceneTransformBack(result.actions);
                }
                manager.renderManager.scene_json.rooms[0].sflayoutid = item.target_node
            });
            mappingLeave(e);
        });
        iDiv.classList.add('tiler');
        catalogItems.appendChild(iDiv);
        item.identifier = item.anim_id;
        $(iDiv).data('meta', item);
        floorPlanMapping.set(item.anim_id, image);
    });
    Splitting({
        target: '.tiler',
        by: 'cells',
        rows: nrs,
        columns: ncs,
        image: true
    });
    $('.tiler .cell-grid .cell').each(function(){
        let meta = $(this).parent().parent().data("meta");
        $(this).parent().attr('id', `grids-${meta.identifier}`);
        $(this).attr('id', `grid-${meta.identifier}`);
    })
}

const sceneTransformFirst = function(derivation, name){
    for(let j = 0; j < derivation.length; j++){
        for(let k = 0; k < derivation[j].length; k++){
            if(derivation[j][k].action === 'move' && name === 'move'){
                return derivation[j][k].p1;
            }
            if(derivation[j][k].action === 'rotate' && name === 'rotate'){
                return derivation[j][k].r1;
            }
            if(derivation[j][k].action === 'transform' && name === 'transform'){
                return derivation[j][k].s1;
            }
        }
    }
}

const sceneTransformLast = function(derivation, name){
    for(let j = derivation.length-1; j >= 0; j--){
        for(let k = derivation[j].length-1; k >= 0; k--){
            if(derivation[j][k].action === 'move' && name === 'move'){
                return derivation[j][k].p2;
            }
            if(derivation[j][k].action === 'rotate' && name === 'rotate'){
                return derivation[j][k].r2;
            }
            if(derivation[j][k].action === 'transform' && name === 'transform'){
                return derivation[j][k].s2;
            }
        }
    }
}

const sceneTransformTo = function(derivations){
    currentSeqs = derivations;
    updateAnimationRecordDiv();
    const T = Math.max(...derivations.map(d => Math.max(...d.map(dd => Math.max(...dd.map(ddd => ddd.t[1]))))));
    for(let i = 0; i < derivations.length; i++){
        let object = undefined;
        for(let finder = 0; finder < manager.renderManager.scene_json.rooms[0].objList.length; finder++){
            if(manager.renderManager.scene_json.rooms[0].objList[finder].sforder === i){
                object = manager.renderManager.scene_json.rooms[0].objList[finder];
                break;
            }
        }
        if(object === undefined){
            console.log('error! sceneTransformTo finds a undefined object? ');
            continue;
        }
        // let object = manager.renderManager.scene_json.rooms[currentRoomId].objList[i];
        // if(!('key' in object)){
        //     continue
        // }
        let object3d = manager.renderManager.instanceKeyCache[object.key];
        let initp = sceneTransformFirst(derivations[i], 'move');
        if(initp){object3d.position.set(initp[0], object3d.position.y, initp[2]);}
        let initr = sceneTransformFirst(derivations[i], 'rotate');
        if(initr){object3d.rotation.set(0, initr, 0);}
        let inits = sceneTransformFirst(derivations[i], 'transform');
        if(inits){objectToAction(object3d, inits, 0.1);}
        // console.log(object3d.userData.json.modelId, initp, initr, inits)
        derivations[i].forEach(seq => {
            seq.forEach(a => {
                if(a.action === 'move'){
                    setTimeout(transformObject3DOnly, a.t[0] * 1000, object.key, [a.p2[0], a.p2[1], a.p2[2]], 'position', true, a.t[1] - a.t[0], 'none');
                }
                if(a.action === 'rotate'){
                    let r = [0, atsc(a.r2), 0];
                    standardizeRotate(r, [0, atsc(a.r1), 0]);
                    object3d.rotation.set(0, atsc(a.r1), 0);
                    setTimeout(transformObject3DOnly, a.t[0] * 1000, object.key, r, 'rotation', true, a.t[1] - a.t[0], 'none');
                }
                if(a.action === 'transform'){
                    setTimeout(objectToAction, a.t[0] * 1000, object3d, a.s2, a.t[1] - a.t[0], 'none');
                }
            })
        });
        setTimeout(synchronize_json_object, T * 1000, object3d);
    }
    // setTimeout(operationFuture, T * 1000 + 200);
}

const sceneTransformBack = function(derivations){
    const T = Math.max(...derivations.map(d => Math.max(...d.map(dd => Math.max(...dd.map(ddd => ddd.t[1]))))));
    for(let i = derivations.length-1; i >= 0; i--){
        let object = undefined;
        for(let finder = 0; finder < manager.renderManager.scene_json.rooms[0].objList.length; finder++){
            if(manager.renderManager.scene_json.rooms[0].objList[finder].sforder === i){
                object = manager.renderManager.scene_json.rooms[0].objList[finder];
                break;
            }
        }
        if(object === undefined){
            console.log('error! sceneTransformBack finds a undefined object? ');
            continue;
        }
        let object3d = manager.renderManager.instanceKeyCache[object.key];
        let initp = sceneTransformLast(derivations[i], 'move');
        if(initp){object3d.position.set(initp[0], object3d.position.y, initp[2]);}
        let initr = sceneTransformLast(derivations[i], 'rotate');
        if(initr){object3d.rotation.set(0, initr, 0);}
        let inits = sceneTransformLast(derivations[i], 'transform');
        if(inits){objectToAction(object3d, inits, 0.1);}
        // console.log(object3d.userData.json.modelId, initp, initr, inits)
        derivations[i].slice().reverse().forEach(seq => {
            seq.slice().reverse().forEach(a => {
                if(a.action === 'move'){
                    setTimeout(transformObject3DOnly, (T - a.t[1]) * 1000, object.key, [a.p1[0], a.p1[1], a.p1[2]], 'position', true, a.t[1] - a.t[0], 'none');
                }
                if(a.action === 'rotate'){
                    let r = [0, atsc(a.r1), 0];
                    standardizeRotate(r, [0, atsc(a.r2), 0]);
                    object3d.rotation.set(0, atsc(a.r2), 0);
                    setTimeout(transformObject3DOnly, (T - a.t[1]) * 1000, object.key, r, 'rotation', true, a.t[1] - a.t[0], 'none');
                }
                if(a.action === 'transform'){
                    setTimeout(objectToAction, (T - a.t[1]) * 1000, object3d, a.s1, a.t[1] - a.t[0], 'none');
                }
            });
            setTimeout(synchronize_json_object, T * 1000, object3d);
        })
    }
    // setTimeout(operationFuture, T * 1000 + 200);
}
