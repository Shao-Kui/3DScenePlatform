// global variables for online mode; 
// const socket = io();
const socket = io({transports: ['websocket']});
const onlineFuncList = {};
const serverUUIDs = [];
const commandStack = [];
gsap.ticker.lagSmoothing();

const loadOnlineSceneJson = function(){
    if(onlineGroup === 'OFFLINE') return;
    $.ajax({
        type: "POST",
        contentType: "application/json; charset=utf-8",
        url: `/online/${onlineGroup}`,
        // data: JSON.stringify( ... ),
        success: function (data) {
            manager.load_scene(JSON.parse(data));
        }
    });
}

const loadMoreServerUUIDs = function(num=5){
    // populate UUIDs from the server:
    for(let i = 0; i < num; i++){$.ajax({
        url: '/applyuuid',
        type: 'GET',
        success: data => { serverUUIDs.push(data); }
    });}  
}

const socketInit = function(){
    // client-side
    socket.on("sceneRefresh", sceneJson => {
        manager.load_scene(sceneJson);
    });
    socket.on("functionCall", (fname, arguments) => {
        let args = [], i = 0;
        while(arguments[i] !== undefined){args.push(arguments[i]); i++; }          
        // console.log(fname, args);      
        onlineFuncList[fname].apply(null, args);
    });
    socket.on("message", (arg) => {
        console.log(arg);
    });
    socket.on("join", (msg, userid) => {
        console.log(msg, userid);
    });
    socket.emit('join', onlineGroup);
    loadMoreServerUUIDs(10);
    socket.on('autoView', ret => {
        while (catalogItems.firstChild) {
            catalogItems.firstChild.remove();
        }
        ret.forEach(function (item) {
            let iDiv = document.createElement('div');
            let image = new Image();
            image.src = `/autoviewimgs/${manager.renderManager.scene_json.origin}/${item.identifier}`;
            image.onload = function(){
                iDiv.style.width = '120px';
                iDiv.style.height = `${120 / (image.width / image.height)}px`;
            };
            iDiv.className = "catalogItem";
            iDiv.style.backgroundImage = `url(/autoviewimgs/${manager.renderManager.scene_json.origin}/${item.identifier})`;
            iDiv.style.backgroundSize = '100% 100%';
            iDiv.addEventListener('click', clickAutoViewItem);
            catalogItems.appendChild(iDiv);
            $(iDiv).data('pcam', item);
        });
    })
}

const emitFunctionCall = function(funcName, arguments){
    socket.emit('functionCall', funcName, arguments, onlineGroup);
    socket.emit('onlineSceneUpdate', getDownloadSceneJson(), onlineGroup);
}

const claimControlObject3D = function(uuid, isRelease){
    socket.emit('claimControlObject3D', onlineUserID, uuid, isRelease, onlineGroup); 
};

socket.on("claimControlObject3D", (objKey, isRelease, userID) => {
    // console.log('claimControlObject3D', objKey, isRelease, userID);
    if(!(objKey in manager.renderManager.instanceKeyCache)){
        return; 
    }
    if(isRelease){
        manager.renderManager.instanceKeyCache[objKey].userData.controlledByID = undefined;
        let index = outlinePass2.selectedObjects.indexOf(manager.renderManager.instanceKeyCache[objKey]);
        if(index > -1){
            outlinePass2.selectedObjects.splice(index, 1);
        }
    }
    else{
        manager.renderManager.instanceKeyCache[objKey].userData.controlledByID = userID;
        outlinePass2.selectedObjects.push(manager.renderManager.instanceKeyCache[objKey]);
    };  
});

const emitAnimationObject3DOnly = function(){
    if(tCache.length === 0) return; 
    if(origin && onlineGroup !== 'OFFLINE'){
        socket.emit('functionCall', 'animateObject3DOnly', [tCache], onlineGroup);
    }
    tCache.length = 0; 
}

const refreshRoomByID = function(roomId, objList, origin=true){
    manager.renderManager.scene_json.rooms[roomId].objList = objList;
    manager.renderManager.refresh_instances();
    if(origin && onlineGroup !== 'OFFLINE'){emitFunctionCall('refreshRoomByID', [roomId, objList, false]);}
}

const transformObjectByUUID = function(uuid, transform, origin=true){
    let object3d = manager.renderManager.instanceKeyCache[uuid]; 
    // set object3d first: 
    console.log(transform);
    object3d.position.set(transform.translate[0], transform.translate[1], transform.translate[2]); 
    object3d.scale.set(transform.scale[0], transform.scale[1], transform.scale[2]);
    object3d.rotation.set(transform.rotate[0], transform.rotate[1], transform.rotate[2]);
    synchronizeObjectJsonByObject3D(object3d);
    // the core code for calculating orientations of objects; 
    if(AUXILIARY_MODE){auxiliaryMode();}
    if(origin && onlineGroup !== 'OFFLINE'){
        emitFunctionCall('transformObjectByUUID', [uuid, transform, false]);
    }
};

const removeObjectByUUID = function(uuid, origin=true){
    let objectToDelete = manager.renderManager.instanceKeyCache[uuid];
    if(objectToDelete === undefined) return; 
    scene.remove(objectToDelete); // remove the object from the scene; 
    let roomId = objectToDelete.userData.json.roomId;
    // delete manager.renderManager.scene_json.rooms[roomId].objList[find_object_json(objectToDelete)];
    let i = manager.renderManager.scene_json.rooms[roomId].objList.indexOf(objectToDelete.userData.json);
    manager.renderManager.scene_json.rooms[roomId].objList.splice(i, 1);
    delete manager.renderManager.instanceKeyCache[uuid];
    if(origin && onlineGroup !== 'OFFLINE'){
        emitFunctionCall('removeObjectByUUID', [uuid, false]);
    }
}

const addObjectByUUID = function(uuid, modelId, transform={'translate': [0,0,0], 'rotate': [0,0,0], 'scale': [1.0,1.0,1.0]}, origin=true){
    if(!(modelId in objectCache)){
        loadObjectToCache(modelId, anchor=addObjectByUUID, anchorArgs=[uuid, modelId, transform, origin]);
        return; 
    }
    // check room ID: 
    let roomID = calculateRoomID(transform.translate); 
    let objToInsert = {
        "modelId": modelId,
        "coarseSemantic": gatheringObjCat[modelId], 
        "translate": transform.translate,
        "scale": transform.scale,
        "roomId": roomID,
        "rotate": transform.rotate,
        "orient": transform.rotate[1], 
        "key": uuid,
        "mageAddDerive": objectCache[modelId].userData.mageAddDerive
    };
    let object3d = objectCache[modelId].clone();
    object3d.name = undefined;
    object3d.scale.set(objToInsert.scale[0],objToInsert.scale[1],objToInsert.scale[2]);
    object3d.rotation.set(objToInsert.rotate[0],objToInsert.rotate[1],objToInsert.rotate[2]);
    object3d.position.set(objToInsert.translate[0],objToInsert.translate[1],objToInsert.translate[2]);
    object3d.userData = {
        "type": 'object',
        "key": objToInsert.key,
        "roomId": roomID,
        "modelId": modelId,
        "coarseSemantic": gatheringObjCat[modelId]
    };
    object3d.children.forEach(child => {
        if(child.material.origin_mtr) child.material = child.material.origin_mtr;
    });
    manager.renderManager.scene_json.rooms[roomID].objList.push(objToInsert);
    manager.renderManager.instanceKeyCache[objToInsert.key] = object3d;
    object3d.userData.json = objToInsert; // add reference from object3d to objectjson. 
    scene.add(object3d)
    if(origin && onlineGroup !== 'OFFLINE'){emitFunctionCall('addObjectByUUID', [uuid, modelId, transform, false]);}
    return object3d;
}

const onlineInitialization = function(){
    // try loading the online scene: 
    loadOnlineSceneJson();
    socketInit();
    onlineFuncList['addObjectFromCache'] = addObjectFromCache;
    onlineFuncList['removeObjectByUUID'] = removeObjectByUUID;
    onlineFuncList['transformObjectByUUID'] = transformObjectByUUID;
    onlineFuncList['addObjectByUUID'] = addObjectByUUID;
    onlineFuncList['animateObject3DOnly'] = animateObject3DOnly; 
    onlineFuncList['refreshRoomByID'] = refreshRoomByID;
    const timelyEmitAnimationObject3DOnly = setInterval(emitAnimationObject3DOnly, 100);

    function closingCode(){
        if(INTERSECT_OBJ) if(INTERSECT_OBJ.userData.key) claimControlObject3D(INTERSECT_OBJ.userData.key, true);
        return null;
    }
    window.onbeforeunload = closingCode;
}
