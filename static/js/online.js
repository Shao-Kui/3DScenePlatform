// global variables for online mode; 
const socket = io();
const onlineFuncList = {};
const serverUUIDs = [];
const onlineUserID = "{{ serverGivenUserID }}";
const onlineUser = {'id': "{{ serverGivenUserID }}", 'name': ''}; 
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
        while(arguments[i]!== undefined){args.push(arguments[i]); i++; }                
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
}

const emitFunctionCall = function(funcName, arguments){
    socket.emit('functionCall', funcName, arguments, onlineGroup);
    socket.emit('onlineSceneUpdate', manager.renderManager.scene_json, onlineGroup);
}

const claimControlObject3D = function(uuid, isRelease){
    socket.emit('claimControlObject3D', onlineUserID, uuid, isRelease, onlineGroup); 
};

socket.on("claimControlObject3D", (objKey, isRelease, userID) => {
    // console.log('claimControlObject3D', objKey, isRelease, userID);
    if(!(objKey in manager.renderManager.instanceKeyCache)){
        return; 
    }
    if(isRelease) manager.renderManager.instanceKeyCache[objKey].userData.controlledByID = undefined;
    else manager.renderManager.instanceKeyCache[objKey].userData.controlledByID = userID;  
});

const onlineInitialization = function(){
    // try loading the online scene: 
    loadOnlineSceneJson();
    socketInit();
    onlineFuncList['addObjectFromCache'] = addObjectFromCache;
    onlineFuncList['removeObjectByUUID'] = removeObjectByUUID;
    onlineFuncList['transformObjectByUUID'] = transformObjectByUUID;
    onlineFuncList['animateObject3DOnly'] = animateObject3DOnly; 
    const timelyEmitAnimationObject3DOnly = setInterval(emitAnimationObject3DOnly, 100);

    function closingCode(){
        if(INTERSECT_OBJ) if(INTERSECT_OBJ.userData.key) claimControlObject3D(INTERSECT_OBJ.userData.key, true);
        return null;
    }
    window.onbeforeunload = closingCode;
}