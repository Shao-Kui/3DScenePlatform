const objectCache = {}; 
const objectLoadingQueue = {};
const gatheringObjCat = {}; 
const loadObjectToCacheContent = function(instance){
    const modelId = instance.modelId;
    instance.userData = {
        "type": 'object',
        "roomId": currentRoomId,
        "modelId": modelId,
        "name": modelId,
        "format": instance.format,
        "coarseSemantic": ""
    };
    // enable shadowing of instances; 
    instance.castShadow = true;
    instance.receiveShadow = true;
    instance.coarseAABB = new THREE.Box3().setFromObject(instance);
    instance.boundingBox = {'min': new THREE.Vector3(Infinity, Infinity, Infinity), 'max': new THREE.Vector3(-Infinity, -Infinity, -Infinity)};
    traverseObjSetting(instance);
    if('geometry' in instance){
        instance.geometry.computeBoundingBox();
        instance.boundingBox = instance.geometry.boundingBox;
    }
    instance.children.forEach(child => {
        // if(child.material.newmtr_lowopa !== undefined) child.material = child.material.newmtr_lowopa;
        if('geometry' in child){
            child.geometry.computeBoundingBox();
            if(child.geometry.boundingBox.max.x > instance.boundingBox.max.x){instance.boundingBox.max.x = child.geometry.boundingBox.max.x;}
            if(child.geometry.boundingBox.max.y > instance.boundingBox.max.y){instance.boundingBox.max.y = child.geometry.boundingBox.max.y;}
            if(child.geometry.boundingBox.max.z > instance.boundingBox.max.z){instance.boundingBox.max.z = child.geometry.boundingBox.max.z;}
            if(child.geometry.boundingBox.min.x < instance.boundingBox.min.x){instance.boundingBox.min.x = child.geometry.boundingBox.min.x;}
            if(child.geometry.boundingBox.min.y < instance.boundingBox.min.y){instance.boundingBox.min.y = child.geometry.boundingBox.min.y;}
            if(child.geometry.boundingBox.min.z < instance.boundingBox.min.z){instance.boundingBox.min.z = child.geometry.boundingBox.min.z;}
        }
    });
    let associatedBox = new THREE.Mesh(new THREE.BoxGeometry(
        instance.boundingBox.max.x - instance.boundingBox.min.x, 
        instance.boundingBox.max.y - instance.boundingBox.min.y, 
        instance.boundingBox.max.z - instance.boundingBox.min.z
    ), new THREE.MeshPhongMaterial({color: 0xffffff}));
    associatedBox.position.set(0, (instance.boundingBox.max.y - instance.boundingBox.min.y)/2, 0)
    instance.associatedBox = associatedBox;
    traverseMtlToOppacity(instance);
    objectCache[modelId] = instance;
    while(objectLoadingQueue[modelId].length){
        let _f = objectLoadingQueue[modelId].pop();
        _f.anchor.apply(null, _f.anchorArgs);
    }
    delete objectLoadingQueue.modelId;
}
let loadObjectToCache = function(modelId, anchor=()=>{}, anchorArgs=[], format='obj'){
    if(modelId in objectCache){
        anchor.apply(null, anchorArgs);
        return;
    }
    if(modelId in objectLoadingQueue){
        objectLoadingQueue[modelId].push({'modelId': modelId, 'anchor': anchor, 'anchorArgs': anchorArgs});
        return;
    }
    objectLoadingQueue[modelId] = [];
    let mtlurl = `/mtl/${modelId}`;
    let meshurl = `/mesh/${modelId}`;
    if(format === 'obj'){
        let objLoader = new THREE.OBJLoader();
        let mtlLoader = new THREE.MTLLoader();
        mtlLoader.load(mtlurl, function (mCreator) {
            objLoader.setMaterials(mCreator);
            objLoader.load(meshurl, function (instance) {
                instance.format = format;
                instance.modelId = modelId;
                loadObjectToCacheContent(instance);
                anchor.apply(null, anchorArgs);
            });
        });
    }else if(format === 'glb'){
        let gltfLoader = new THREE.GLTFLoader();
        console.log(`/static/dataset/object/${modelId}/${modelId}.glb`);
        gltfLoader.load(`/static/dataset/object/${modelId}/${modelId}.glb`, function(instance){
            instance.scene.modelId = modelId;
            instance.scene.animations = instance.animations;
            instance.scene.format = format;
            loadObjectToCacheContent(instance.scene);
            anchor.apply(null, anchorArgs);
        })
    }
};

const traverseMtlToOppacity = function (object) {
    if(object instanceof THREE.Mesh){
        let newmtr_lowopa;
        if(Array.isArray(object.material)){
            newmtr_lowopa = [];
            for(let i = 0; i < object.material.length; i++){
                let mtl = object.material[i].clone()
                mtl.transparent = true;
                mtl.opacity = 0.6;
                newmtr_lowopa.push(mtl);
            }
        }else{
            newmtr_lowopa = object.material.clone();
            newmtr_lowopa.transparent = true;
            newmtr_lowopa.opacity = 0.6;
            
        }
        newmtr_lowopa.origin_mtr = object.material;
        newmtr_lowopa.newmtr_lowopa = newmtr_lowopa;
        object.material.origin_mtr = object.material;
        object.material.newmtr_lowopa = newmtr_lowopa;
        object.material = newmtr_lowopa;
        return;
    }
    if(object.children.length === 0){
        return;
    }
    object.children.forEach(function(child){
        traverseMtlToOppacity(child);
    });
};

let refreshObjectFromCache = function(objToInsert){
    if(!(objToInsert.modelId in objectCache)) return;
    let object3dFull = objectCache[objToInsert.modelId].clone();
    let object3d;
    if(manager.renderManager.islod){
        object3d = new THREE.LOD();
        object3d.addLevel(new THREE.Group(), 40);
        object3d.addLevel(objectCache[objToInsert.modelId].associatedBox.clone(), 10);
        object3d.addLevel(object3dFull, 0);
    }else{
        object3d = object3dFull;
    }
    object3d.name = undefined;
    if(objToInsert.rotate[0] === 0 && objToInsert.rotate[2] === 0){
        objToInsert.rotate[1] = Math.atan2(Math.sin(objToInsert.rotate[1]), Math.cos(objToInsert.rotate[1]));
    }
    object3d.scale.set(objToInsert.scale[0],objToInsert.scale[1],objToInsert.scale[2]);
    object3d.rotation.set(objToInsert.rotate[0],objToInsert.rotate[1],objToInsert.rotate[2]);
    object3d.position.set(objToInsert.translate[0],objToInsert.translate[1],objToInsert.translate[2]);
    object3d.userData = {
        "type": 'object',
        "key": objToInsert.key,
        "roomId": objToInsert.roomId,
        "modelId": objToInsert.modelId,
        "format": objToInsert.format,
        "coarseSemantic": objToInsert.coarseSemantic,
        "isSceneObj": true
    };
    object3dFull.children.forEach(child => {
        if(child.material){
            if(child.material.origin_mtr) child.material = child.material.origin_mtr;
        }
    });
    manager.renderManager.instanceKeyCache[objToInsert.key] = object3d;
    // add reference from object3d to objectjson: 
    object3d.userData.json = objToInsert;
    if(['Ceiling Lamp', 'Pendant Lamp', 'Wall Lamp', 'chandelier'].includes(object3d.userData.coarseSemantic)){
        let light = new THREE.PointLight( 0xffffff, 10, 100 );
        light.name = SEMANTIC_POINTLIGHT;
        light.position.set(0,0,0);
        object3d.add(light);
    }
    object3d.name = objToInsert.key;
    scene.add(object3d);
    if(objToInsert.format === 'glb'){
        playAnimation(object3d);
    }
    return object3d; 
}

const trafficFlowObjList = ['snack01', 'snack02', 'snack03', 'snack04', 'snacks01', 'snacks02', 'snacks03', 'snacks04', 'snacks05', 'snacks06', 
'cake02', 'cake03', 'sandwich01', 'sandwich02', 'burger01', 'cake04', 'cake05', 'friescounter01', 'cake06', 'cake07', 'tacocounter01', 'fruit01', 'fruit02', 
'fruit03', 'fruit04', 'fruit05', 'fruit06', 'fruit07', 'fruit08', 'fruit09', 'fruit10', 'fruit11', 'vegetable01', 'vegetable02', 'vegetable03', 
'vegetable04', 'vegetable05', 'vegetable06', 'vegetable07', 'vegetable08', 'vegetable09', 'vegetable10', 'vegetable11', 'vegetable12', 
'vegetable13', 'vegetable14', 'vegetable15', 'vegetable16', 'vegetable17', 'meat01', 'meat02', 'meat03', 'meat04', 'meat05', 'meat06', 
'meat07', 'meat08', 'meat09', 'meat10', 'grain01', 'grain02', 'staplefood01', 'staplefood02', 'staplefood03', 'oil01', 'oil02', 
'eggscounter03', 'flavoring01', 'container02', 'container03', 'container04', 'coffee02', 'drinks01', 'drinks02', 'drinks03', 'drinks04', 
'drinks05', 'wine01', 'milk01', 'drinks06', 'drinks07', 'drinks08', 'drinks09', 'drinks10', 'drinks11', 'drinks12', 'drinks13', 'vendor01', 
'vendor02', 'housekeeping01', 'housekeeping02', 'housekeeping03', 'housekeeping', 'petfood01', 'freezer01', 'freezer02', 'freezer03', 
'freezer04', 'freezer05', 'freezer06', 'freezer07', 'freezer08', 'freezer09', 'freezer10', 'shirt01', 'shirt02', 'shirt03', 'shirt04', 
'shirt05', 'shirt06', 'shirt07', 'shirt08', 'shorts01', 'pants01', 'pants02', 'pants03', 'pants04', 'pants05', 'skirt01', 'skirt02'];
let addObjectFromCache = function(modelId, transform={'translate': [0,0,0], 'rotate': [0,0,0], 'scale': [1.0,1.0,1.0], 'format': 'obj'}, uuid=undefined, origin=true){
    loadMoreServerUUIDs(1);
    if(!uuid) uuid = serverUUIDs.pop(); 
    if(!uuid) uuid = THREE.MathUtils.generateUUID();
    commandStack.push({
        'funcName': 'removeObjectByUUID',
        'args': [uuid, true]
    });
    if(trafficFlowObjList.includes(modelId)){
        transform.scale[0] = 0.9 / (objectCache[modelId].boundingBox.max.x-objectCache[modelId].boundingBox.min.x);
        transform.scale[1] = transform.scale[0];
        transform.scale[2] = 0.45 / (objectCache[modelId].boundingBox.max.z-objectCache[modelId].boundingBox.min.z);
    }
    let roomID = calculateRoomID(transform.translate)
    let object3d = addObjectByUUID(uuid, modelId, roomID, transform);
    object3d.name = uuid;
    emitFunctionCall('addObjectByUUID', [uuid, modelId, roomID, transform]);
    if(transform.format === 'glb'){
        playAnimation(object3d);
    }
    return object3d; 
};

const addObjectsFromCache = function(oArray){
    loadMoreServerUUIDs(oArray.length);
    let uuids = [];
    // console.log(oArray)
    oArray.forEach(o => {
        let uuid = serverUUIDs.pop(); // For object, pop a new uuid. 
        if(!uuid){
            uuid = THREE.MathUtils.generateUUID();
        }
        let roomID = calculateRoomID(o.transform.translate);
        addObjectByUUID(uuid, o.modelId, roomID, o.transform);
        emitFunctionCall('addObjectByUUID', [uuid, o.modelId, roomID, o.transform]);
        uuids.push(uuid);
    });
    commandStack.push({
        'funcName': 'removeObjectsByUUID',
        'args': [uuids]
    });
};

const playAnimation = function(object3d){
    const animaMixer = new THREE.AnimationMixer(object3d);
    animaMixers.push(animaMixer);
    object3d.actions = {};
    objectCache[object3d.userData.modelId].animations.forEach(animation => {
        let action = animaMixer.clipAction(animation);
        action.timeScale = 1; 
        action.loop = THREE.LoopOnce;
        action.play();
        action.paused = true;
        action.time = 0;
        if(object3d.userData.json.startState === animation.name){
            action.time = action.getClip().duration;
        }
        // object3d.currentAction = action;
        object3d.actions[animation.name] = action;
    });
}