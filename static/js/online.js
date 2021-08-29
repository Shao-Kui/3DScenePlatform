// global variables for online mode; 
// const socket = io();
const socket = io({transports: ['websocket']});
const onlineFuncList = {};
const serverUUIDs = [];
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

const onlineInitialization = function(){
    // try loading the online scene: 
    loadOnlineSceneJson();
    socketInit();
    onlineFuncList['addObjectFromCache'] = addObjectFromCache;
    onlineFuncList['removeObjectByUUID'] = removeObjectByUUID;
    onlineFuncList['transformObjectByUUID'] = transformObjectByUUID;
    onlineFuncList['animateObject3DOnly'] = animateObject3DOnly; 
    onlineFuncList['refreshRoomByID'] = refreshRoomByID;
    const timelyEmitAnimationObject3DOnly = setInterval(emitAnimationObject3DOnly, 100);

    function closingCode(){
        if(INTERSECT_OBJ) if(INTERSECT_OBJ.userData.key) claimControlObject3D(INTERSECT_OBJ.userData.key, true);
        return null;
    }
    window.onbeforeunload = closingCode;
}