const auxiliary_remove = function(){
    scene.remove(scene.getObjectByName(AUXILIARY_NAME));
    $('#tab_auxobj').text(" ");
}

const auxiliary_catlist = function(sign){
    if(sign === 0){
        $('#tab_auxdom').text('ALL');
        return; 
    }
    let currenti = _auxCatList.indexOf($('#tab_auxdom').text());
    currenti += sign; 
    if(currenti === -1) currenti = _auxCatList.length-1;
    currenti = currenti % _auxCatList.length;
    $('#tab_auxdom').text(_auxCatList[currenti]);
}; 

const _auxCatList = ["ALL"]; 
const gatheringAuxObjCat = async function(coarseSemantic){
    let thekeys = Object.keys(coarseSemantic); 
    thekeys.forEach( k => {
        gatheringObjCat[k] = coarseSemantic[k]; 
        if(!_auxCatList.includes(coarseSemantic[k])){
            _auxCatList.push(coarseSemantic[k]); 
        }
    });
}

// this function relates to the 'AuxiliaryMode' button in the UI;
const auxiliary_control = function(){
    var autoinsert_button = document.getElementById("auxiliary_button");
    AUXILIARY_MODE = !AUXILIARY_MODE;
    // disable ordinary insertion if the auxiliary mode is on; 
    onAddOff();
    if(AUXILIARY_MODE){
        auxiliaryMode();
        autoinsert_button.style.backgroundColor = '#9400D3';
        fpsCount();
    }else{
        // remove 'auxiliaryObject' in the scene; 
        auxiliary_remove();
        autoinsert_button.style.backgroundColor = 'transparent';
        fpsCount();
    }
}

let categoryCodec = {}; 
const auxiliaryLoadWall = function(anchor=()=>{}, anchorArgs=[]){
    $.ajax({
        type: "POST",
        contentType: "application/json; charset=utf-8",
        url: "/priors_of_wall",
        data: JSON.stringify(manager.renderManager.scene_json.rooms[currentRoomId]),
        success: function (data) {
            data = JSON.parse(data);
            manager.renderManager.scene_json.rooms[currentRoomId].auxiliaryWallObj = data;
            if('categoryCodec' in data){
                categoryCodec = data.categoryCodec; 
            }
            gatheringAuxObjCat(data.coarseSemantic); 
            data.object.forEach(o => {
                loadObjectToCache(o);
            });
            mageAddWalReady = true;
            anchor.apply(null, anchorArgs);
        }
    });
}; 

const auxiliaryRoom = function(anchor=()=>{}, anchorArgs=[]){
    $.ajax({
        type: "POST",
        contentType: "application/json; charset=utf-8",
        url: "/priors_of_roomShape",
        data: JSON.stringify(manager.renderManager.scene_json.rooms[currentRoomId]),
        success: function (data) {
            if(manager.renderManager.scene_json.rooms[currentRoomId].auxiliaryDomObj !== undefined){
                manager.renderManager.scene_json.rooms[currentRoomId].auxiliaryDomObj.tensor.dispose();
                manager.renderManager.scene_json.rooms[currentRoomId].auxiliaryDomObj.catMaskTensor.dispose();
                manager.renderManager.scene_json.rooms[currentRoomId].auxiliaryDomObj.roomShapeTensor.dispose();
            }
            data = JSON.parse(data);
            data.roomShapeTensor = tf.tensor(data.room_meta);
            data.tensor = tf.tensor(data.prior);
            data.catMaskTensor = tf.tensor(data.catMask);
            manager.renderManager.scene_json.rooms[currentRoomId].auxiliaryDomObj = data;
            gatheringAuxObjCat(data.coarseSemantic); 
            data.object.forEach(o => {
                loadObjectToCache(o);
            })
            mageAddDomReady = true;
            anchor.apply(null, anchorArgs);
        }
    });
}

const auxiliaryLoadSub = function(anchor=()=>{}, anchorArgs=[]){
    $.ajax({
        type: "POST",
        contentType: "application/json; charset=utf-8",
        url: "/priors_of_objlist",
        data: JSON.stringify(manager.renderManager.scene_json.rooms[currentRoomId]),
        success: function (data) {
            if(auxiliaryPrior !== undefined){
                auxiliaryPrior.tensor.dispose();
                auxiliaryPrior.catMaskTensor.dispose();
            }
            data = JSON.parse(data);
            data.catMaskTensor = tf.tensor(data.catMask);
            auxiliaryPrior = data;
            manager.renderManager.scene_json.rooms[currentRoomId].auxiliarySecObj = data;
            auxiliaryPrior.tensor = tf.tensor(auxiliaryPrior.prior);
            gatheringAuxObjCat(data.coarseSemantic); 
            data.object.forEach(o => {
                loadObjectToCache(o);
            });
            mageAddSubReady = true;
            anchor.apply(null, anchorArgs);
        }  
    });
}

let auxiliaryPrior;
let auxiliaryMode = function(anchor=()=>{}, anchorArgs=[]){
    if(currentRoomId === undefined){
        return;
    }
    manager.renderManager.scene_json.rooms[currentRoomId].objList = 
    manager.renderManager.scene_json.rooms[currentRoomId].objList
    .filter( item => item !== null && item !== undefined ); 
    _auxCatList.length = 1; 
    auxiliaryRoom(anchor=anchor, anchorArgs=anchorArgs);
    auxiliaryLoadWall(anchor=anchor, anchorArgs=anchorArgs);
    auxiliaryLoadSub(anchor=anchor, anchorArgs=anchorArgs); 
}; 

const realTimeObjCache = function(objname, x, y, z, theta, scale=[1.0, 1.0, 1.0], mageAddDerive=""){
    if(objectCache[objname] === undefined){
        return false;
    }
    objectCache[objname].name = AUXILIARY_NAME;
    objectCache[objname].position.set(x, y, z);
    objectCache[objname].rotation.set(0, theta, 0, 'XYZ');
    objectCache[objname].scale.set(scale[0], scale[1], scale[2]);
    // detecting collisions between the pending object and other objects of the same room: 
    let olist = manager.renderManager.scene_json.rooms[currentRoomId].objList;
    for(let i = 0; i < olist.length; i++){
        let obj = olist[i];
        if(obj === undefined || obj === null) continue;
        if(!'key' in obj) continue;
        if(mageAddDerive!==""){
            let domName = mageAddDerive.split('-')[0]; 
            if(domName === obj.modelId) continue; 
        }
        let objmesh = manager.renderManager.instanceKeyCache[obj.key];
        if(detectCollisionGroups(objectCache[objname], objmesh)){
            auxiliary_remove();
            return false;
        }
    }
    // detecting collisions between the pending objects and buffered door meshes; 
    for(let i = 0; i < door_mageAdd_set.length; i++){
        let doorMesh = door_mageAdd_set[i];
        if(detectCollisionGroups(doorMesh, objectCache[objname])){
            auxiliary_remove();
            return false;
        }
    }
    // detecting collisions between the pending objects and the wall: 
    if(manager.renderManager.scene_json.rooms[currentRoomId].auxiliaryDomObj === undefined){
        return false;
    }
    let wallMeta = manager.renderManager.scene_json.rooms[currentRoomId].auxiliaryDomObj.room_meta; 
    if(mageAddDerive.split(' ')[0] !== 'wall'){
        if(detectCollisionWall(wallMeta, objectCache[objname])){
            auxiliary_remove();
            return false; 
        }
    }
    if(!scene.getObjectByName(AUXILIARY_NAME)){
        scene.add(objectCache[objname]);
    }
    if(scene.getObjectByName(AUXILIARY_NAME).userData.modelId !== objname){
        auxiliary_remove();
        scene.add(objectCache[objname]);
    }
    $('#tab_auxobj').text(`${objname}: ${gatheringObjCat[objname]}`);
    objectCache[objname].userData.mageAddDerive = mageAddDerive; 
    return true
}

const auxiliaryWall = function(theIntersect){
    // find the nearest wall first; 
    let awo = manager.renderManager.scene_json.rooms[currentRoomId].auxiliaryWallObj;
    let ado = manager.renderManager.scene_json.rooms[currentRoomId].auxiliaryDomObj;
    if(ado === undefined || awo === undefined)
        return;
    // if(awo === undefined)
    //     return;
    let ftnw = findTheNearestWall(theIntersect, manager.renderManager.scene_json.rooms[currentRoomId].auxiliaryDomObj.roomShapeTensor); 
    let wallDistances = ftnw[1]; 
    wallIndex = ftnw[0][0]; 
    secWallIndex = ftnw[0][1]; 
    // let minDis = wallDistances.slice([wallIndex], [1]).arraySync();
    let secMinDis = wallDistances.slice([secWallIndex], [1]).arraySync(); // the distance w.r.t the second nearest wall; 
    // find object satisfying the beam distance; 
    let beamObjList = []; 
    let oList = manager.renderManager.scene_json.rooms[currentRoomId].objList; 
    let line = new THREE.Line3(); // create once and reuse
    let B = theIntersect.point.clone().add(new THREE.Vector3(ado.room_oriNormal[wallIndex][0], 0, ado.room_oriNormal[wallIndex][1])); 
    line.set(theIntersect.point, B);
    let C = new THREE.Vector3();
    for(let i = 0; i < oList.length; i++){
        let obj = oList[i];
        if(obj === undefined || obj === null) continue;
        if(!'key' in obj) continue;
        let objmesh = manager.renderManager.instanceKeyCache[obj.key];
        if(objmesh === undefined) continue; 
        let pos = objmesh.position.clone(); 
        pos.y = theIntersect.point.y;
        line.closestPointToPoint(pos, false, C); 
        let clamp = line.closestPointToPointParameter(objmesh.position, true); 
        let beamDis = pos.distanceTo(C);
        if(beamDis <= 0.1 && clamp > 0.0) beamObjList.push(objmesh); 
    }
    // find the nearest object among the 'beamObjList'; 
    let ascription; 
    let minBeanEucDIs = Infinity;
    let objname;
    let _fromWhere;  
    if(beamObjList.length === 0){
        return;
        objname = awo.emptyChoice;
        _fromWhere = 'empty'; 
    }
    else{
        for(let i = 0; i < beamObjList.length; i++){
            let objmesh = beamObjList[i]; 
            let dis = objmesh.position.clone().sub(theIntersect.point).length(); 
            if(dis < minBeanEucDIs){
                minBeanEucDIs = dis; 
                ascription = objmesh; 
            }
        }
        objname = awo.mapping[ascription.userData.key]; 
        _fromWhere = ascription.userData.key; 
    }
    if(objname === undefined || !objname in objectCache || objname === 'null'){scene.remove(scene.getObjectByName(AUXILIARY_NAME));return;}
    if(objectCache[objname].coarseAABB.max.x > secMinDis){
        scene.remove(scene.getObjectByName(AUXILIARY_NAME));
        return; 
    }; 
    realTimeObjCache(objname, // object name
        theIntersect.point.x, theIntersect.point.y, theIntersect.point.z, // x, y, z
        ado.room_orient[wallIndex], // theta
        [1, 1, 1], // scale
        `wall ${_fromWhere}`
    );
};

const genFloorPlanWallTensors = function(){
    if(manager.roomShapeTensorAll !== undefined){
        manager.roomStartTensorAll.dispose();
        manager.roomEndTensorAll.dispose();
    }
    manager.roomStartAll = [];
    manager.roomEndAll = [];
    manager.roomNormAll = [];
    manager.roomOrientAll = [];
    manager.renderManager.scene_json.rooms.forEach(room => {
        if('roomShape' in room){
            manager.roomStartAll = manager.roomStartAll.concat(room.roomShape);
            manager.roomEndAll = manager.roomEndAll.concat(room.roomShape.slice(1,room.roomShape.length).concat(room.roomShape.slice(0,1)));
            manager.roomNormAll = manager.roomNormAll.concat(room.roomNorm);
            manager.roomOrientAll = manager.roomOrientAll.concat(room.roomOrient);
        }
    });
    manager.roomStartTensorAll = tf.tensor(manager.roomStartAll);
    manager.roomEndTensorAll = tf.tensor(manager.roomEndAll);
}

const findTheNearestWall = function(theIntersect, wallPointStart, wallPointEnd=undefined){
    // let wallPointStart = manager.renderManager.scene_json.rooms[currentRoomId].auxiliaryDomObj.roomShapeTensor;
    if(wallPointEnd === undefined){wallPointEnd = tf.concat([wallPointStart.slice([1], [wallPointStart.shape[0]-1]), wallPointStart.slice([0], [1])]);}
    let p3 = tf.tensor([theIntersect.point.x, theIntersect.point.z]);
    let a_square = tf.sum(tf.square(wallPointEnd.sub(wallPointStart)), axis=1);
    let b_square = tf.sum(tf.square(wallPointEnd.sub(p3)), axis=1);
    let c_square = tf.sum(tf.square(wallPointStart.sub(p3)), axis=1);
    let siafangbfang = a_square.mul(b_square).mul(4);
    let apbmcfang = tf.square(a_square.add(b_square).sub(c_square));
    let triangleArea = tf.sqrt(tf.relu(siafangbfang.sub(apbmcfang))).mul(0.5); // this is twice the area; 
    let wallDistances = triangleArea.div(tf.norm(wallPointEnd.sub(wallPointStart), 'euclidean', 1));
    let _indicesList = []; 
    let innerProducts = tf.sum((wallPointStart.sub(p3)).mul(wallPointStart.sub(wallPointEnd)), axis=1).arraySync();
    let wallIndices = tf.topk(wallDistances, wallDistances.shape[0], true).indices.arraySync().reverse();
    a_square_sync = a_square.arraySync();
    for(let i = 0; i < wallIndices.length; i++){
        let wi = wallIndices[i];
        if( 0 <= innerProducts[wi] && innerProducts[wi] <= a_square_sync[wi]){
            _indicesList.push(wi);
            // wallIndex = wi;
            if (_indicesList.length >= 2) break;
        }
    }
    // siafangbfang.dispose();
    // apbmcfang.dispose();
    // triangleArea.dispose();
    // wallPointEnd.dispose();
    // a_square.dispose();b_square.dispose();c_square.dispose();p3.dispose();
    return [_indicesList, wallDistances]; 
}

const auxiliaryCG = function(theIntersect, auto=false){
    // find the nearest distance to the nearest wall; ( np.abs(np.cross(p2-p1, p1-p3)) / norm(p2-p1) )
    let ado = manager.renderManager.scene_json.rooms[currentRoomId].auxiliaryDomObj;
    if(ado === undefined)
        return false;
    let wallIndex;
    let secWallIndex; // the second nearest wall index; 
    let ftnw = findTheNearestWall(theIntersect, manager.renderManager.scene_json.rooms[currentRoomId].auxiliaryDomObj.roomShapeTensor); 
    let wallDistances = ftnw[1];
    wallIndex = ftnw[0][0];
    secWallIndex = ftnw[0][1]; 
    // let wallIndex = tf.argMin(wallDistances).arraySync();
    let minDis = wallDistances.slice([wallIndex], [1]).arraySync();
    let secMinDis = wallDistances.slice([secWallIndex], [1]); // the distance w.r.t the second nearest wall; 
    let vecSub;
    let secVecSub; 
    if(ado.tensor.shape[0] !== 0){
        vecSub = tf.abs(tf.transpose(tf.transpose(ado.tensor).slice([2], [1])).sub(minDis)).reshape([-1]);
        secVecSub = tf.transpose(tf.transpose(ado.tensor).slice([6], [1])).reshape([-1]); 
    }else{
        return false;
    }
    // filter out priors exceed the second nearest wall; 
    vecSub = vecSub.where(secVecSub.less(secMinDis), Infinity); 
    // filter out object that the user does not interect in; 
    if($('#tab_auxdom').text() !== 'ALL'){
        vecSub = vecSub.where(ado.catMaskTensor.equal(categoryCodec[$('#tab_auxdom').text()]), Infinity); 
    }
    let index = tf.argMin(vecSub).arraySync();
    // if the 'minimal distance sub' is still high, results in next level; 
    let threshold; 
    if($('#tab_auxdom').text() === 'ALL'){
        threshold = 0.6; 
    }else{
        threshold = 1.5; 
    }
    if(auto) threshold = 0.05;
    if(vecSub.slice([index], [1]).arraySync()[0] >= threshold){
        scene.remove(scene.getObjectByName(AUXILIARY_NAME)); 
        return false;
    }
    let objname = ado.index[index];
    let theprior = ado.prior[index];
    if(realTimeObjCache(objname, // object name
        theIntersect.point.x, 0, theIntersect.point.z, // x, y, z
        ado.room_orient[wallIndex] + theprior[1], // theta
        [theprior[3], theprior[4], theprior[5]], // scale
        'dom'
    ) && auto)
    {
        addObjectFromCache(
            modelId=objname,
            transform={
                'translate': [theIntersect.point.x, 0, theIntersect.point.z], 
                'rotate': [0, ado.room_orient[wallIndex] + theprior[1], 0],
                'scale': [theprior[3], theprior[4], theprior[5]]
            }
        );
        return true;
    }
    return false
}

const auxiliaryMove = function(){
    updateMousePosition();
    // first checking if the intersected point is shooted on the wall; 
    let wallIntersects = raycaster.intersectObjects(manager.renderManager.wCache, true); 
    if (wallIntersects.length > 0){
        auxiliaryWall(wallIntersects[0]); 
        return; 
    }
    // this may require a systematic optimization, since objList can be reduced to a single room;
    let intersectObjList = Object.values(manager.renderManager.instanceKeyCache)
    .concat(Object.values(manager.renderManager.fCache));
    intersects = raycaster.intersectObjects(intersectObjList, true);
    if (intersectObjList.length > 0 && intersects.length > 0) {
        let aso = manager.renderManager.scene_json.rooms[currentRoomId].auxiliarySecObj; 
        if(aso === undefined){
            auxiliaryCG(intersects[0]);
            return;
        }
        let intersectPoint = tf.tensor([intersects[0].point.x, intersects[0].point.y, intersects[0].point.z]);
        let vecSub;
        // if auxiliaryPiror.tensor.shape[0] equals to 0, then no context exists; 
        if(aso.tensor.shape[0] !== 0){
            vecSub = tf.transpose(tf.transpose(aso.tensor).slice([0], [3])).sub(intersectPoint);
        }else{
            auxiliaryCG(intersects[0]);
            return;
        }
        // transform priors
        let eucNorm = tf.norm(vecSub, 'euclidean', 1);
        if($('#tab_auxdom').text() !== 'ALL'){
            eucNorm = eucNorm.where(aso.catMaskTensor.equal(categoryCodec[$('#tab_auxdom').text()]), Infinity); 
        }

        let index = tf.argMin(eucNorm).arraySync();
        let eucDis = eucNorm.slice([index], [1]).arraySync();
        let objname = aso.index[index];
        let theprior = aso.prior[index];
        let threshold; 
        if($('#tab_auxdom').text() === 'ALL'){
            threshold = 0.6; 
        }else{
            threshold = 1.5; 
        }
        if(eucDis >= threshold){
            scene.remove(scene.getObjectByName(AUXILIARY_NAME)); 
            // if the intersection occurs at the floor, try suggest coherent groups; 
            if(manager.renderManager.fCache.includes(intersects[0].object.parent)){
                auxiliaryCG(intersects[0]);
            }
            return;
        }
        let Y; 
        if(['Rug'].includes(aso.coarseSemantic[objname])){
            Y = 0; 
        }else{
            Y = intersects[0].point.y;
        }
        realTimeObjCache(
            // objname, intersects[0].point.x, theprior[1], intersects[0].point.z, theprior[3], [1.0, 1.0, 1.0], 
            objname, intersects[0].point.x, Y, intersects[0].point.z, theprior[3], [1.0, 1.0, 1.0], 
            mageAddDerive=`${aso.belonging[index]}-${objname}`);
    }
}

const auxiliaryRightClick = function(){
    let aobj = scene.getObjectByName(AUXILIARY_NAME); 
    if(!aobj || currentRoomId === undefined) return; 
    let mageAddDerive = aobj.userData.mageAddDerive;
    let insname = aobj.userData.modelId;
    console.log(mageAddDerive);
    let theroom = manager.renderManager.scene_json.rooms[currentRoomId]; 
    $.ajax({
        type: "POST",
        contentType: "application/json; charset=utf-8",
        url: "/mageAddSwapInstance",
        // note that this work highly bases on 'category' instead of 'instance'; 
        data: JSON.stringify({'insname': insname, 'existList': Object.keys(objectCache)}),
        success: function (data) {
            let newinsname = data; 
            if(mageAddDerive.includes('wall')){
                let mad = mageAddDerive.split(' '); 
                if(mad[1] === 'empty') {theroom.auxiliaryWallObj.emptyChoice = newinsname;}
                else{theroom.auxiliaryWallObj.mapping[mad[1]] = newinsname;}
                auxiliaryLoadWall();
            }else if(mageAddDerive.includes('dom')){
                let index = theroom.auxiliaryDomObj.object.indexOf(insname);
                if (index !== -1) {
                    theroom.auxiliaryDomObj.object[index] = newinsname;
                }
                // for(let i = 0; i < theroom.auxiliarySecObj.belonging.length; i++){
                //     if(theroom.auxiliarySecObj.belonging[i] === insname) theroom.auxiliarySecObj.belonging[i] = newinsname; 
                // }
                auxiliaryRoom(); 
            }else{
                theroom.auxiliarySecObj.existPair
                [`${mageAddDerive.split('-')[0]}-${theroom.auxiliarySecObj.coarseSemantic[insname]}`] 
                = newinsname; 
                auxiliaryLoadSub(); 
            }
        }
    });
}

const mageAddAutoCaster = new THREE.Raycaster();
const auxiliaryMove_fullAuto = function(sample){
    let intersectObjList = Object.values(manager.renderManager.instanceKeyCache)
    .concat(Object.values(manager.renderManager.fCache));
    mageAddAutoCaster.set(new THREE.Vector3(sample[0], 100, sample[1]), new THREE.Vector3(0, -1, 0)); 
    let intersects = mageAddAutoCaster.intersectObjects(intersectObjList, true);
    if (intersectObjList.length > 0 && intersects.length > 0) {
        let aso = manager.renderManager.scene_json.rooms[currentRoomId].auxiliarySecObj; 
        let intersectPoint = tf.tensor([intersects[0].point.x, intersects[0].point.y, intersects[0].point.z]);
        let vecSub;
        if(aso.tensor.shape[0] !== 0){
            vecSub = tf.transpose(tf.transpose(aso.tensor).slice([0], [3])).sub(intersectPoint);
        }else{
            return auxiliaryCG(intersects[0], true);
        }
        let eucNorm = tf.norm(vecSub, 'euclidean', 1);
        if($('#tab_auxdom').text() !== 'ALL'){
            eucNorm = eucNorm.where(aso.catMaskTensor.equal(categoryCodec[$('#tab_auxdom').text()]), Infinity); 
        }
        let index = tf.argMin(eucNorm).arraySync();
        let eucDis = eucNorm.slice([index], [1]).arraySync();
        let objname = aso.index[index];
        let theprior = aso.prior[index];
        let threshold = 0.1; 
        // if($('#tab_auxdom').text() === 'ALL'){
        //     threshold = 0.6; 
        // }else{
        //     threshold = 1.5; 
        // }
        if(eucDis >= threshold){
            scene.remove(scene.getObjectByName(AUXILIARY_NAME)); 
            if(manager.renderManager.fCache.includes(intersects[0].object.parent)){
                return auxiliaryCG(intersects[0], true);
            }
        }
        let Y; 
        if(['Rug'].includes(aso.coarseSemantic[objname])){
            Y = 0; 
        }else{
            Y = intersects[0].point.y;
        }
        if(realTimeObjCache(
            objname, intersects[0].point.x, Y, intersects[0].point.z, theprior[3], [1.0, 1.0, 1.0], 
            mageAddDerive=`${aso.belonging[index]}-${objname}`))
        {
            addObjectFromCache(
                modelId=objname,
                transform={
                    'translate': [intersects[0].point.x, Y, intersects[0].point.z], 
                    'rotate': [0, theprior[3], 0],
                    'scale': [1.0, 1.0, 1.0]
                }
            );
            return true;
        }
        return false;
    }
}

var mageAddSubReady = false;
var mageAddDomReady = false;
var mageAddWalReady = false;

const mageAddSample = async function(){
    if(currentRoomId === undefined){
        return;
    }
    $.ajax({
        type: "POST",
        contentType: "application/json; charset=utf-8",
        url: "/magic_samplepoints",
        data: JSON.stringify(manager.renderManager.scene_json.rooms[currentRoomId]),
        success: function (data) {
            let samples = JSON.parse(data);
            auxiliaryMode(anchor=mageAddAuto, anchorArgs=[samples]);
        }
    });
}

const mageAddAuto = function(samples){
    if(samples.length <= 0){
        mageAddSubReady = false;
        mageAddDomReady = false;
        mageAddWalReady = false;
        return
    }
    if(mageAddSubReady && mageAddDomReady && mageAddWalReady){
        tf.engine().startScope();
        let status = auxiliaryMove_fullAuto(samples.pop());
        tf.engine().endScope();
        if(status){
            mageAddSubReady = false;
            mageAddDomReady = false;
            mageAddWalReady = false;
            auxiliaryMode(anchor=mageAddAuto, anchorArgs=[samples]); // Update priors. 
        }else{
            mageAddAuto(samples); // Try the next sample. 
        }
    }
};

const loadSingleObjectPrior = function(modelId){
    let j = getDownloadSceneJson();
    j['tarObj'] = modelId;
    mageAddSinglePrior.enabled = false;
    $.ajax({
        type: "POST",
        contentType: "application/json; charset=utf-8",
        url: "/mageAddSingle",
        data: JSON.stringify(j),
        success: function (data) {
            mageAddSinglePrior.subTensor.dispose();
            mageAddSinglePrior.domTensor.dispose();
            mageAddSinglePrior = JSON.parse(data);
            mageAddSinglePrior.subTensor = tf.tensor(mageAddSinglePrior.subPrior);
            mageAddSinglePrior.domTensor = tf.tensor(mageAddSinglePrior.domPrior);
            // this may require a systematic optimization, since objList can be reduced to a single room;
            mageAddSinglePrior.intersectObjList = Object.values(manager.renderManager.instanceKeyCache)
            .concat(Object.values(manager.renderManager.fCache));
            if(INTERSECT_OBJ){
                mageAddSinglePrior.intersectObjList = 
                mageAddSinglePrior.intersectObjList.filter(d => d.userData.key !== INTERSECT_OBJ.userData.key);
            }
            mageAddSinglePrior.modelId = modelId;
            mageAddSinglePrior.enabled = true;
        }
    });
}

const smallestSignedAngleBetween = function(x, y){
    let a = (x-y+Math.PI) % (Math.PI * 2) - Math.PI;
    let b = (y-x+Math.PI) % (Math.PI * 2) - Math.PI;
    return Math.abs(a) < Math.abs(b) ? a : b;
}

const realTimeSingleCache = function(objname, x, y, z, theta, scale=[1.0, 1.0, 1.0], mageAddDerive=false){
    if(objectCache[objname] === undefined){
        return false;
    }
    let r = objectCache[objname].rotation.y;
    theta = r - smallestSignedAngleBetween(r, theta);
    objectCache[objname].name = AUXILIARY_NAME;
    gsap.to(objectCache[objname].position, {
        duration: 0.2,
        x: x,
        y: y,
        z: z
    });
    if(mageAddDerive){
        gsap.to(objectCache[objname].rotation, {
            duration: 0.2,
            x: 0,
            y: theta,
            z: 0
        });
        if(mageAddDerive === 'dom'){
            gsap.to(objectCache[objname].scale, {
                duration: 0.2,
                x: scale[0],
                y: scale[1],
                z: scale[2]
            });
        }
    }
    
    // objectCache[objname].position.set(x, y, z);
    // objectCache[objname].rotation.set(0, theta, 0, 'XYZ');
    // objectCache[objname].scale.set(scale[0], scale[1], scale[2]);
    // // detecting collisions between the pending object and other objects: 
    // olist = Object.values(manager.renderManager.instanceKeyCache);
    // for(let i = 0; i < olist.length; i++){
    //     let objmesh = olist[i];
    //     if(detectCollisionGroups(objectCache[objname], objmesh)){
    //         // console.log('Collision with an Object: ', objmesh); 
    //         auxiliary_remove();
    //         return false;
    //     }
    // }
    // // detecting collisions between the pending objects and buffered door meshes; 
    // for(let i = 0; i < door_mageAdd_set.length; i++){
    //     let doorMesh = door_mageAdd_set[i];
    //     if(detectCollisionGroups(doorMesh, objectCache[objname])){
    //         // console.log('Collision with a Windoor: ', doorMesh); 
    //         auxiliary_remove();
    //         return false;
    //     }
    // }
    // // detecting collisions between the pending objects and the wall: 
    // for(let i = 0; i < manager.renderManager.scene_json.rooms.length; i++){
    //     let wallMeta = manager.renderManager.scene_json.rooms[i].roomShape;
    //     if(detectCollisionWall(wallMeta, objectCache[objname])){
    //         // console.log('Collision with a Wall: ', wallMeta); 
    //         auxiliary_remove();
    //         return false; 
    //     }
    // }
    if(!scene.getObjectByName(AUXILIARY_NAME)){
        scene.add(objectCache[objname]);
    }
    if(scene.getObjectByName(AUXILIARY_NAME).userData.modelId !== objname){
        auxiliary_remove();
        scene.add(objectCache[objname]);
    }
    objectCache[objname].userData.mageAddDerive = mageAddDerive; 
    return true
}

const mageAddSingleCG = function(theIntersect){
    // find the nearest distance to the nearest wall; ( np.abs(np.cross(p2-p1, p1-p3)) / norm(p2-p1) )
    let wallIndex;
    let secWallIndex; // the second nearest wall index; 
    let ftnw = findTheNearestWall(theIntersect, manager.roomStartTensorAll, manager.roomEndTensorAll); 
    let wallDistances = ftnw[1];
    wallIndex = ftnw[0][0];
    secWallIndex = ftnw[0][1];
    let minDis = wallDistances.slice([wallIndex], [1]).arraySync();
    let secMinDis = wallDistances.slice([secWallIndex], [1]); // the distance w.r.t the second nearest wall; 
    let vecSub;
    let secVecSub; 
    if(mageAddSinglePrior.domTensor.shape[0] !== 0){
        vecSub = tf.abs(tf.transpose(tf.transpose(mageAddSinglePrior.domTensor).slice([2], [1])).sub(minDis)).reshape([-1]);
        secVecSub = tf.transpose(tf.transpose(mageAddSinglePrior.domTensor).slice([6], [1])).reshape([-1]); 
    }else{
        return [theIntersect.point.x, theIntersect.point.y, theIntersect.point.z, 0, [1.0, 1.0, 1.0], false];
    }
    // filter out priors exceed the second nearest wall; 
    vecSub = vecSub.where(secVecSub.less(secMinDis), Infinity); 
    let index = tf.argMin(vecSub).arraySync();
    let threshold = 0.6; 
    if(vecSub.slice([index], [1]).arraySync()[0] >= threshold){
        return [theIntersect.point.x, theIntersect.point.y, theIntersect.point.z, 0, [1.0, 1.0, 1.0], false];
    }
    let theprior = mageAddSinglePrior.domPrior[index];
    return [theIntersect.point.x, 0, theIntersect.point.z, // x, y, z
            manager.roomOrientAll[wallIndex] + theprior[1], // theta
            [theprior[3], theprior[4], theprior[5]], // scale
            'dom'];
}
/*
This function is a special version of 'MageAdd', where we try adding a single object. 
*/
var mageAddSinglePrior = {
    subTensor: tf.tensor([]),
    domTensor: tf.tensor([]),
    enabled: false
}; 
const mageAddSingle = function(){
    if(!mageAddSinglePrior.enabled){
        return [intersects[0].point.x, intersects[0].point.y, intersects[0].point.z, 0, [1.0, 1.0, 1.0], false];
    }
    intersects = raycaster.intersectObjects(mageAddSinglePrior.intersectObjList, true);
    if (mageAddSinglePrior.intersectObjList.length > 0 && intersects.length > 0) {
        let intersectPoint = tf.tensor([intersects[0].point.x, intersects[0].point.y, intersects[0].point.z]);
        let vecSub;
        // if auxiliaryPiror.tensor.shape[0] equals to 0, then no context exists; 
        if(mageAddSinglePrior.subTensor.shape[0] !== 0){
            vecSub = tf.transpose(tf.transpose(mageAddSinglePrior.subTensor).slice([0], [3])).sub(intersectPoint);
        }else{
            return mageAddSingleCG(intersects[0]);
        }
        // transform priors
        let eucNorm = tf.norm(vecSub, 'euclidean', 1);
        let index = tf.argMin(eucNorm).arraySync();
        let eucDis = eucNorm.slice([index], [1]).arraySync();
        let theprior = mageAddSinglePrior.subPrior[index];
        let threshold = 0.6; 
        if(eucDis >= threshold){
            if(manager.renderManager.fCache.includes(intersects[0].object.parent)){
                return mageAddSingleCG(intersects[0]);
            }
        }
        let Y = intersects[0].point.y; 
        // if(['Rug'].includes(INSERT_OBJ.coarseSemantic)){
        //     Y = 0; 
        // }else{
        //     Y = intersects[0].point.y;
        // }
        return [intersects[0].point.x, Y, intersects[0].point.z, theprior[3], [1.0, 1.0, 1.0], 
                `${mageAddSinglePrior.belonging[index]}-${mageAddSinglePrior.modelId}`];
    }
}

var cgseries = {
    anchorOris: tf.tensor([]),
    anchorDises: tf.tensor([]),
    depthDises: tf.tensor([]),
    leftDises: tf.tensor([]),
    rightDises: tf.tensor([]),
    areas: tf.tensor([]),
    objNums: tf.tensor([]),
    spaceUtils: tf.tensor([]),
    catNums: tf.tensor([]),
    dpAnchors: tf.tensor([]),
    dpLefts: tf.tensor([]),
    dpRights: tf.tensor([]),
    dpDepths: tf.tensor([]),
    originCGs: tf.tensor([]),
    diffMatrix: tf.tensor([]),
    scaleOri: tf.tensor([]),
    configs: [],
    enabled: false
}

const refreshCGS = function (data) {
    let newcgseries = JSON.parse(data);
    if(!('configs' in newcgseries)){
        cgseries.enabled = false;
        On_CGSeries = false;
        return
    }
    INTERSECT_OBJ.scale.set(Math.abs(INTERSECT_OBJ.scale.x),Math.abs(INTERSECT_OBJ.scale.y),Math.abs(INTERSECT_OBJ.scale.z))
    CGSERIES_GROUP.lastIndex = undefined;
    cgseries.anchorOris.dispose();
    cgseries.anchorDises.dispose();
    cgseries.depthDises.dispose();
    cgseries.leftDises.dispose();
    cgseries.rightDises.dispose();
    cgseries.areas.dispose();  
    cgseries.objNums.dispose(); 
    cgseries.spaceUtils.dispose(); 
    cgseries.catNums.dispose(); 
    cgseries.dpAnchors.dispose(); 
    cgseries.dpLefts.dispose(); 
    cgseries.dpRights.dispose(); 
    cgseries.dpDepths.dispose(); 
    cgseries.originCGs.dispose(); 
    cgseries.diffMatrix.dispose();
    cgseries.scaleOri.dispose();
    cgseries = newcgseries;   
    cgseries.anchorOris = tf.tensor(cgseries.anchorOris);
    cgseries.anchorDises = tf.tensor(cgseries.anchorDises);
    cgseries.depthDises = tf.tensor(cgseries.depthDises);
    cgseries.leftDises = tf.tensor(cgseries.leftDises);
    cgseries.rightDises = tf.tensor(cgseries.rightDises);
    cgseries.areas = tf.tensor(cgseries.areas);
    cgseries.objNums = tf.tensor(cgseries.objNums);
    cgseries.spaceUtils = tf.tensor(cgseries.spaceUtils);
    cgseries.catNums = tf.tensor(cgseries.catNums);
    cgseries.dpAnchors = tf.tensor(cgseries.dpAnchors);
    cgseries.dpLefts = tf.tensor(cgseries.dpLefts);
    cgseries.dpRights = tf.tensor(cgseries.dpRights);
    cgseries.dpDepths = tf.tensor(cgseries.dpDepths);
    cgseries.originCGs = tf.tensor(cgseries.originCGs, [cgseries.originCGs.length], 'int32');
    cgseries.diffMatrix = tf.tensor(cgseries.diffMatrix);
    // this may require a systematic optimization, since objList can be reduced to a single room;
    cgseries.intersectObjList = Object.values(manager.renderManager.fCache);
    cgseries.object3ds = [];
    CGSERIES_GROUP.clear();
    CGSERIES_GROUP.domCurrentScale = INTERSECT_OBJ.scale.clone();
    CGSERIES_GROUP.scale.set(INTERSECT_OBJ.scale.x, INTERSECT_OBJ.scale.y, INTERSECT_OBJ.scale.z);
    let _a = cgseries.anchorDises.mul(tf.sqrt(tf.pow(tf.cos(cgseries.anchorOris).mul(INTERSECT_OBJ.scale.z), 2).add(tf.pow(tf.sin(cgseries.anchorOris).mul(INTERSECT_OBJ.scale.x), 2))));
    let _d = cgseries.depthDises.mul(tf.sqrt(tf.pow(tf.cos(cgseries.anchorOris).mul(INTERSECT_OBJ.scale.z), 2).add(tf.pow(tf.sin(cgseries.anchorOris).mul(INTERSECT_OBJ.scale.x), 2))));

    let _l = cgseries.leftDises.mul(tf.sqrt(tf.pow(tf.sin(cgseries.anchorOris).mul(INTERSECT_OBJ.scale.z), 2).add(tf.pow(tf.cos(cgseries.anchorOris).mul(INTERSECT_OBJ.scale.x), 2))));
    let _r = cgseries.rightDises.mul(tf.sqrt(tf.pow(tf.sin(cgseries.anchorOris).mul(INTERSECT_OBJ.scale.z), 2).add(tf.pow(tf.cos(cgseries.anchorOris).mul(INTERSECT_OBJ.scale.x), 2))));

    cgseries.anchorDises = _a.where(_a.less(_l), _l);
    cgseries.anchorDises = cgseries.anchorDises.where(_a.less(_r), _r);
    cgseries.depthDises = _d.where(_a.less(_l), _r);
    cgseries.depthDises = cgseries.depthDises.where(_a.less(_r), _l);
    cgseries.leftDises = _l.where(_a.less(_l), _d);
    cgseries.leftDises = cgseries.leftDises.where(_a.less(_r), _a);
    cgseries.rightDises = _r.where(_a.less(_l), _a);
    cgseries.rightDises = cgseries.rightDises.where(_a.less(_r), _d);
    cgseries.scaleOri = tf.fill([cgseries.anchorDises.shape[0]], 0);
    cgseries.scaleOri = cgseries.scaleOri.where(_a.less(_l), Math.PI/2);
    cgseries.scaleOri = cgseries.scaleOri.where(_a.less(_r), -Math.PI/2);

    cgseries.involvedObjects.forEach(o => {
        loadObjectToCache(o, (modelId) => {
            let object3d = objectCache[modelId].clone();
            object3d.children.forEach(child => {
                if(child.material.origin_mtr) child.material = child.material.origin_mtr;
            });
            cgseries.object3ds.push(object3d);
            object3d.onUsed = false;
        }, [o]);
    });
    cgseries.enabled = true;
}

const loadCGSeries = function(modelId, seriesName=undefined){
    let j = {
        'domID': modelId
    };
    cgseries.enabled = false;
    if(seriesName){
        j['seriesName'] = seriesName
    }
    $.ajax({
        type: "POST",
        contentType: "application/json; charset=utf-8",
        url: "/coherent_group_series",
        data: JSON.stringify(j),
        success: refreshCGS
    });
    
}

const moveCGSeries = function(){
    if(!cgseries.enabled){
        return;
    }
    let intersects = raycaster.intersectObjects(cgseries.intersectObjList, true);
    if(cgseries.intersectObjList.length > 0 && intersects.length > 0) {
        let i = intersects[0];
        transformObject3DOnly(INTERSECT_OBJ.userData.key, [i.point.x, i.point.y, i.point.z], 'position', true);
        gsap.to(CGSERIES_GROUP.position, {duration: commonSmoothDuration, x: i.point.x, y: i.point.y, z: i.point.z});
        let roomShape = tf.tensor(manager.renderManager.scene_json.rooms[i.object.parent.userData.roomId].roomShape);
        let rsArray = manager.renderManager.scene_json.rooms[i.object.parent.userData.roomId].roomShape;
        let roomOrient = manager.renderManager.scene_json.rooms[i.object.parent.userData.roomId].roomOrient;
        let ftnw = findTheNearestWall(i, roomShape); 
        let wallDistances = ftnw[1];
        let wallIndex = ftnw[0][0];    
        // This should be a weighted sum of energies. 
        // Currently, we consider only areas. 
        let scores = 
        cgseries.areas.mul(CGSERIES_GROUP.attrArea)
        .add(cgseries.objNums.mul(CGSERIES_GROUP.attrNum))
        .add(cgseries.catNums.mul(CGSERIES_GROUP.attrCat))
        .add(cgseries.spaceUtils.mul(CGSERIES_GROUP.attrSU));
        // let scores = cgseries.objNums.mul(1);
        // left & right: 
        let leftIndex = (wallIndex + 1) % rsArray.length;
        let rightIndex = (wallIndex + rsArray.length - 1) % rsArray.length;
        // depth: 
        let _dli = (leftIndex + 1) % rsArray.length;
        let _dri = (rightIndex  + rsArray.length - 1) % rsArray.length;
        let vecAnchor =  new THREE.Vector2(rsArray[leftIndex][0], rsArray[leftIndex][1]).sub(new THREE.Vector2(rsArray[wallIndex][0], rsArray[wallIndex][1]));
        let vecLeft =  new THREE.Vector2(rsArray[_dli][0], rsArray[_dli][1]).sub(new THREE.Vector2(rsArray[leftIndex][0], rsArray[leftIndex][1]));
        let vecRight =  new THREE.Vector2(rsArray[rightIndex][0], rsArray[rightIndex][1]).sub(new THREE.Vector2(rsArray[wallIndex][0], rsArray[wallIndex][1]));
        let depthIndex = ( vecAnchor.cross(vecLeft) > vecAnchor.cross(vecRight) ) ? _dli : _dri;
        // Dependencies
        let wdt = 0.25;
        let _addiff = wallDistances.slice([wallIndex], [1]).sub(cgseries.anchorDises);
        _addiff = _addiff.where(_addiff.less(wdt), 1.0);
        _addiff = _addiff.where(_addiff.greater(wdt), 0.0);
        scores = scores.add(_addiff.mul(cgseries.dpAnchors).mul(-CGSERIES_GROUP.attrD));
        let _dpdiff = wallDistances.slice([depthIndex], [1]).sub(cgseries.depthDises);
        _dpdiff = _dpdiff.where(_dpdiff.less(wdt), 1.0);
        _dpdiff = _dpdiff.where(_dpdiff.greater(wdt), 0.0);
        scores = scores.add(_dpdiff.mul(cgseries.dpDepths).mul(-CGSERIES_GROUP.attrD));
        let _lfdiff = wallDistances.slice([leftIndex], [1]).sub(cgseries.leftDises);
        _lfdiff = _lfdiff.where(_lfdiff.less(wdt), 1.0);
        _lfdiff = _lfdiff.where(_lfdiff.greater(wdt), 0.0);
        scores = scores.add(_lfdiff.mul(cgseries.dpLefts).mul(-CGSERIES_GROUP.attrD));
        let _rtdiff = wallDistances.slice([rightIndex], [1]).sub(cgseries.rightDises);
        _rtdiff = _rtdiff.where(_rtdiff.less(wdt), 1.0);
        _rtdiff = _rtdiff.where(_rtdiff.greater(wdt), 0.0);
        scores = scores.add(_rtdiff.mul(cgseries.dpRights).mul(-CGSERIES_GROUP.attrD));
        // Smoothness
        if(CGSERIES_GROUP.lastIndex){
            let diffVec = cgseries.diffMatrix.slice([cgseries.configs[CGSERIES_GROUP.lastIndex].originCG], [1]).squeeze();
            diffVec = diffVec.gather(cgseries.originCGs);
            scores.add(diffVec.mul(-CGSERIES_GROUP.attrS))
        }
        

        // filter out priors exceed the depth & left & right: 
        // console.log(wallIndex, depthIndex, leftIndex, rightIndex);
        let constraints = cgseries.anchorDises.less(wallDistances.slice([wallIndex], [1]))
        .logicalAnd(cgseries.depthDises.less(wallDistances.slice([depthIndex], [1]))) 
        .logicalAnd(cgseries.leftDises.less(wallDistances.slice([leftIndex], [1]))) 
        .logicalAnd(cgseries.rightDises.less(wallDistances.slice([rightIndex], [1])));
        scores = scores.where(constraints, -1); 
        // cgseries.anchorDises.less(wallDistances.slice([wallIndex], [1])).print();
        // scores.print();
        let index = tf.argMax(scores).arraySync();
        CGSERIES_GROUP.lastIndex = index;
        if(scores.slice([index], [1]).arraySync()[0] < 0){
            CGSERIES_GROUP.clear();
            CGSERIES_GROUP.lastIndex = undefined;
            return;
        }
        // console.log('alrd', cgseries.anchorDises.slice([index], [1]).arraySync()[0],cgseries.leftDises.slice([index], [1]).arraySync()[0],cgseries.rightDises.slice([index], [1]).arraySync()[0],cgseries.depthDises.slice([index], [1]).arraySync()[0])
        // console.log('wall', wallDistances.slice([wallIndex], [1]).arraySync()[0],wallDistances.slice([leftIndex], [1]).arraySync()[0],wallDistances.slice([rightIndex], [1]).arraySync()[0],wallDistances.slice([depthIndex], [1]).arraySync()[0])
        // expanding factor: 
        let ef = wallDistances.slice([wallIndex], [1]).div(cgseries.anchorDises.slice([index], [1])).arraySync();
        ef = (ef > 1.5) ? 1.5 : ef;  
        let theprior = cgseries.configs[index];
        let domOrient = theprior['anchorOri'] + roomOrient[wallIndex] + cgseries.scaleOri.slice([index], [1]).arraySync()[0];
        transformObject3DOnly(INTERSECT_OBJ.userData.key, [0, domOrient, 0], 'rotation', true); 
        gsap.to(CGSERIES_GROUP.rotation, {duration: commonSmoothDuration, y: domOrient});
        transformObject3DOnly(INTERSECT_OBJ.userData.key, [theprior['domScale'][0] * CGSERIES_GROUP.domCurrentScale.x, theprior['domScale'][1] * CGSERIES_GROUP.domCurrentScale.y, theprior['domScale'][2] * CGSERIES_GROUP.domCurrentScale.z], 'scale', false); 
        gsap.to(CGSERIES_GROUP.scale, {duration: commonSmoothDuration, x:theprior['domScale'][0] * CGSERIES_GROUP.domCurrentScale.x, y:theprior['domScale'][1] * CGSERIES_GROUP.domCurrentScale.y, z:theprior['domScale'][2] * CGSERIES_GROUP.domCurrentScale.z});
        cgseries.object3ds.forEach(c => {c.onUsed = false;});
        theprior.subPriors.forEach(p => {
            // find a correspongding object w.r.t p: 
            let corresObj;
            p.allocated = false;
            for(let i = 0; i < CGSERIES_GROUP.children.length; i++){
                if(CGSERIES_GROUP.children[i].onUsed || CGSERIES_GROUP.children[i].userData.modelId !== p.sub){
                    continue
                }
                CGSERIES_GROUP.children[i].onUsed = true;
                corresObj = CGSERIES_GROUP.children[i];
                p.allocated = true;
                break;
            }
            if(!p.allocated){
            for(let i = 0; i < cgseries.object3ds.length; i++){
                if(cgseries.object3ds[i].onUsed || cgseries.object3ds[i].userData.modelId !== p.sub){
                    continue
                }
                cgseries.object3ds[i].onUsed = true;
                corresObj = cgseries.object3ds[i];
                CGSERIES_GROUP.add(corresObj);
                p.allocated = true;
                break;
            }
            }
            if(p.allocated){
                gsap.to(corresObj.position, {duration: commonSmoothDuration, x: p.translate[0], y: p.translate[1], z: p.translate[2]});
                gsap.to(corresObj.rotation, {duration: commonSmoothDuration, y: p.orient});
                gsap.to(corresObj.scale, {duration: commonSmoothDuration, x: p.scale[0], y: p.scale[1], z: p.scale[2]});
            }
            
        });
        for(let i = 0; i < cgseries.object3ds.length; i++){
            // console.log(cgseries.object3ds[i].position, cgseries.object3ds[i].rotation);
            if(!cgseries.object3ds[i].onUsed){
                CGSERIES_GROUP.remove(cgseries.object3ds[i]);
            }
        }
    }
}

const synchronize_coherentGroup = function(){
    let oArray = [];
    let theprior = cgseries.configs[CGSERIES_GROUP.lastIndex];
    for(let i = 0; i < CGSERIES_GROUP.children.length; i++){
        let c = CGSERIES_GROUP.children[i];
        let _x = c.position.x * CGSERIES_GROUP.scale.x, _y = c.position.y * CGSERIES_GROUP.scale.y, _z = c.position.z * CGSERIES_GROUP.scale.z;
        let tx = Math.cos(CGSERIES_GROUP.rotation.y) * _x + Math.sin(CGSERIES_GROUP.rotation.y) * _z + CGSERIES_GROUP.position.x;
        let ty = _y + CGSERIES_GROUP.position.y;
        let tz = -Math.sin(CGSERIES_GROUP.rotation.y) * _x + Math.cos(CGSERIES_GROUP.rotation.y) * _z + CGSERIES_GROUP.position.z;
        let rx = Math.sin(c.rotation.y) * CGSERIES_GROUP.scale.x;
        let rz = Math.cos(c.rotation.y) * CGSERIES_GROUP.scale.z;
        let theta = Math.atan2(rx, rz);
        // let sz = Math.cos(Math.PI/2 - theta) * CGSERIES_GROUP.scale.x + Math.cos(theta) * CGSERIES_GROUP.scale.z;
        // let sx = Math.cos(theta) * CGSERIES_GROUP.scale.x + Math.cos(Math.PI/2 - theta) * CGSERIES_GROUP.scale.z;
        let sz = Math.sqrt(Math.pow(CGSERIES_GROUP.scale.z * Math.cos(theta), 2) + Math.pow(CGSERIES_GROUP.scale.x * Math.sin(theta), 2))
        let sx = Math.sqrt(Math.pow(CGSERIES_GROUP.scale.z * Math.sin(theta),2) + Math.pow(CGSERIES_GROUP.scale.x * Math.cos(theta),2))
        let o = {
            'modelId': c.userData.modelId,
            'transform': {
                'translate': [tx, ty, tz],
                'rotate': [0, Math.atan2(rx, rz) + CGSERIES_GROUP.rotation.y, 0],
                'scale': [c.scale.x*sx*(CGSERIES_GROUP.scale.x/Math.abs(CGSERIES_GROUP.scale.x)), c.scale.y*CGSERIES_GROUP.scale.y, c.scale.z*sz*(CGSERIES_GROUP.scale.z/Math.abs(CGSERIES_GROUP.scale.z))]
            }
        }
        oArray.push(o);
    }
    addObjectsFromCache(oArray);
}
