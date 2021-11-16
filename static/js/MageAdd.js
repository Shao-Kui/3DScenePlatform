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
