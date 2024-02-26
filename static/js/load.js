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
    // traverseMtlToOpacity(instance); // from 2023.3.3 this feature is temperally removed due to instanseMesh. 
    objectCache[modelId] = instance;
    playAnimation(objectCache[modelId]);
    while(objectLoadingQueue[modelId].length){
        let _f = objectLoadingQueue[modelId].pop();
        _f.anchor.apply(null, _f.anchorArgs);
    }
    delete objectLoadingQueue.modelId;
}
let loadObjectToCache = function(modelId, anchor=()=>{}, anchorArgs=[], format='obj'){
    if(format === 'instancedMesh'){return;}
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
    if(format === 'obj' || format === 'THInstancedObject'){
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
    }else if(format === 'Door' || format === 'Window'){
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
    }
    else if(format === 'glb'){
        let gltfLoader = new THREE.GLTFLoader();
        gltfLoader.load(`/static/dataset/object/${modelId}/${modelId}.glb`, function(instance){
            instance.scene.modelId = modelId;
            instance.scene.animations = instance.animations;
            instance.scene.format = format;
            loadObjectToCacheContent(instance.scene);
            anchor.apply(null, anchorArgs);
        })
    }
};

const traverseMtlToOpacity = function (object, opacity = 0.6) {
    if(object instanceof THREE.Mesh){
        let newmtr_lowopa;
        if(Array.isArray(object.material)){
            newmtr_lowopa = [];
            for(let i = 0; i < object.material.length; i++){
                let mtl = object.material[i].clone()
                mtl.transparent = true;
                mtl.opacity = opacity;
                newmtr_lowopa.push(mtl);
            }
        }else{
            newmtr_lowopa = object.material.clone();
            newmtr_lowopa.transparent = true;
            newmtr_lowopa.opacity = opacity;
            
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
        traverseMtlToOpacity(child, opacity);
    });
};

let refreshObjectFromCache = function(objToInsert){
    if(!(objToInsert.modelId in objectCache)) return;
    let object3dFull = objectCache[objToInsert.modelId].clone();
    if (objToInsert.format ==="THInstancedObject") {
        let instancedTransforms = objToInsert.instancedTransforms;
        object3dFull = new THREE.Group();
        objectCache[objToInsert.modelId].children.forEach(c => {
            let mesh = new THREE.InstancedMesh(c.geometry, c.material, instancedTransforms.length);
            for (let i = 0; i < instancedTransforms.length; ++i) {
                const temp = new THREE.Object3D();
                temp.position.set(instancedTransforms[i].translate[0], instancedTransforms[i].translate[1], instancedTransforms[i].translate[2]);
                temp.rotation.set(instancedTransforms[i].rotate[0], instancedTransforms[i].rotate[1], instancedTransforms[i].rotate[2]);
                temp.scale.set(instancedTransforms[i].scale[0], instancedTransforms[i].scale[1], instancedTransforms[i].scale[2]);
                temp.updateMatrix();
                mesh.setMatrixAt(i, temp.matrix);
            }
            object3dFull.add(mesh);
        });
    }
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
    if(objToInsert.format === 'Door' || objToInsert.format === 'Window'){
        objToInsert.translate[0] = (objToInsert.bbox.max[0] + objToInsert.bbox.min[0]) / 2;
        objToInsert.translate[1] = objToInsert.bbox.min[1];
        objToInsert.translate[2] = (objToInsert.bbox.max[2] + objToInsert.bbox.min[2]) / 2;
        let roomShape = tf.tensor(manager.renderManager.scene_json.rooms[objToInsert.roomId].roomShape);
        let ftnw = findTheNearestWall({'point': {'x': objToInsert.translate[0], 'y': objToInsert.translate[1], 'z': objToInsert.translate[2]}}, roomShape); 
        let wallIndex = ftnw[0][0];
        objToInsert.rotate[1] = manager.renderManager.scene_json.rooms[objToInsert.roomId].roomOrient[wallIndex];
        objToInsert.scale[0] = (objToInsert.bbox.max[0] - objToInsert.bbox.min[0]) / (objectCache[objToInsert.modelId].boundingBox.max.x-objectCache[objToInsert.modelId].boundingBox.min.x);
        objToInsert.scale[1] = (objToInsert.bbox.max[1] - objToInsert.bbox.min[1]) / (objectCache[objToInsert.modelId].boundingBox.max.y-objectCache[objToInsert.modelId].boundingBox.min.y);
        objToInsert.scale[2] = (objToInsert.bbox.max[2] - objToInsert.bbox.min[2]) / (objectCache[objToInsert.modelId].boundingBox.max.z-objectCache[objToInsert.modelId].boundingBox.min.z);
        if(Math.abs(objToInsert.rotate[1] % Math.PI) > 0.1){
            objToInsert.scale[0] = (objToInsert.bbox.max[2] - objToInsert.bbox.min[2]) / (objectCache[objToInsert.modelId].boundingBox.max.x-objectCache[objToInsert.modelId].boundingBox.min.x);
            objToInsert.scale[2] = (objToInsert.bbox.max[0] - objToInsert.bbox.min[0]) / (objectCache[objToInsert.modelId].boundingBox.max.z-objectCache[objToInsert.modelId].boundingBox.min.z);
        }
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
    if(['Ceiling Lamp', 'Pendant Lamp', 'Wall Lamp', 'chandelier', 'wall_lamp'].includes(object3d.userData.coarseSemantic)){
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

const refreshSceneCall = function(thejson){
    commandStack.push({
        'funcName': 'refreshSceneByJson',
        'args': [getDownloadSceneJson()]
    });
    socket.emit('sceneRefresh', thejson, onlineGroup);
};

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

let addObjectFromCache = function(modelId, transform={'translate': [0,0,0], 'rotate': [0,0,0], 'scale': [1.0,1.0,1.0], 'format': 'obj', 'startState': 'origin'}, uuid=undefined, origin=true, otherInfo = {}){
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
    let roomID = calculateRoomID(transform.translate);
    let object3d = addObjectByUUID(uuid, modelId, roomID, transform, otherInfo);
    object3d.name = uuid;
    emitFunctionCall('addObjectByUUID', [uuid, modelId, roomID, transform, otherInfo]);
    return object3d;
};

const instancedCache = {};
const addObjectUsingInstance = function(o){
    if(!(o.modelId in instancedCache)){
        setTimeout(addObjectUsingInstance, Math.random() * 3000 + 1000, o);
        return;
    }
    instancedCache[o.modelId].forEach(c => {
        const position = new THREE.Vector3();
        const rotation = new THREE.Euler();
        const quaternion = new THREE.Quaternion();
        const scale = new THREE.Vector3();
        const matrix = new THREE.Matrix4();
        position.x = o['translate'][0]
        position.y = o['translate'][1]
        position.z = o['translate'][2]
        rotation.x = o['rotate'][0]
        rotation.y = o['rotate'][1]
        rotation.z = o['rotate'][2]
        quaternion.setFromEuler( rotation );
        scale.x = o['scale'][0];
        scale.y = o['scale'][1];
        scale.z = o['scale'][2];
        matrix.compose( position, quaternion, scale );
        c.setMatrixAt(o.cumulatedCount, matrix);
        c.instanceMatrix.needsUpdate = true;
    })
}
const traverseSceneJson = function(sj){
    Object.keys(instancedCache).forEach(modelId => {
        instancedCache[modelId].forEach(c => {
            scene.remove(c);
        });
        delete instancedCache[modelId];
    });
    let modelIds = new Map();
    sj.rooms.forEach(room => {
        room.objList.forEach(o => {
            if(modelIds.has(o.modelId)){
                modelIds.set(o.modelId, modelIds.get(o.modelId)+1);
            }else{
                modelIds.set(o.modelId, 1);
            }
            o.cumulatedCount = modelIds.get(o.modelId)-1;
        })
    });
    sj.rooms.forEach(room => {
        room.objList.forEach(o => {
            if(modelIds.get(o.modelId) > 100000 || o.format === 'instancedMesh'){
                o.format = 'instancedMesh';
                loadObjectToCache(o.modelId, () => {
                    if(o.modelId in instancedCache){
                        return;
                    }
                    let res = []; // this array will finally contain all instancedMesh in THREE.js. 
                    objectCache[o.modelId].children.forEach(c => {
                        let im = new THREE.InstancedMesh(c.geometry, c.material, modelIds.get(o.modelId));
                        res.push(im);
                        scene.add(im);
                    });
                    instancedCache[o.modelId] = res;
                }, []);
                addObjectUsingInstance(o);
            }
            if(o.format === 'sfy'){
                let geometry = new THREE.BoxGeometry( 
                    (o.bbox.max[0] - o.bbox.min[0]), 
                    (o.bbox.max[1] - o.bbox.min[1]), 
                    (o.bbox.max[2] - o.bbox.min[2])
                ); 
                let material = new THREE.MeshBasicMaterial({color: 0xd92511});
                material.transparent = true;
                material.opacity = 0.25
                let object3d = new THREE.Mesh( geometry, material );
                object3d.position.set( 
                    (o.bbox.max[0] + o.bbox.min[0]) / 2,
                    (o.bbox.max[1] + o.bbox.min[1]) / 2,
                    (o.bbox.max[2] + o.bbox.min[2]) / 2
                ); 
                manager.renderManager.instanceKeyCache[o.key] = object3d;
                object3d.userData = {
                    "type": 'object',
                    "key": o.key,
                    "roomId": o.roomId,
                    "modelId": o.modelId,
                    "format": o.format,
                    "coarseSemantic": o.coarseSemantic,
                    "isSceneObj": true
                };
                scene.add(object3d); 
            }
            // SFY parameterized furniture
            if (o.format === 'sfyobj') {
                let generateTransparentBox = (o, color = 0xd92511, opacity = 0.5) => {
                    let geometry = new THREE.BoxGeometry(o.value[0], o.value[2], o.value[1]);
                    geometry.translate(o.value[0]/2, o.value[2]/2, -o.value[1]/2);
                    let material = new THREE.MeshBasicMaterial({color: color});
                    material.transparent = true;
                    material.opacity = opacity
                    let object3d = new THREE.Mesh( geometry, material );
                    const m = new THREE.Matrix4();
                        m.set(o.mtx[0][0], o.mtx[2][0], o.mtx[1][0], o.mtx[3][0], 
                            o.mtx[0][2], o.mtx[2][2], o.mtx[1][2], o.mtx[3][2], 
                            o.mtx[0][1], o.mtx[2][1], o.mtx[1][1], o.mtx[3][1], 
                            o.mtx[0][3], o.mtx[2][3], o.mtx[1][3], o.mtx[3][3] );
                    object3d.applyMatrix4(m);
                    return object3d;
                };

                let traverseSFYObjChildren = (rootO, parent) => {
                    if (rootO.childrenList === undefined) return;
                    rootO.childrenList.forEach(o => {
                        let object3d = generateTransparentBox(o, color=colorHash.hex(o.idx));
                        object3d.name = o.idx;
                        object3d.userData = {
                            "type": 'object',
                            "key": o.key,
                            "roomId": o.roomId,
                            "modelId": o.modelId,
                            "format": o.format,
                            "coarseSemantic": o.coarseSemantic,
                            "isSceneObj": true,
                            "world_mtx": o.world_mtx,
                            "isSceneObj": false
                        };
                        traverseSFYObjChildren(o, object3d);
                        parent.add(object3d);
                    });
                };

                let object3d = generateTransparentBox(o, color=colorHash.hex(o.idx));
                if (o.childrenList) traverseSFYObjChildren(o, object3d);
                manager.renderManager.instanceKeyCache[o.key] = object3d;
                object3d.name = o.idx;
                object3d.userData = {
                    "type": 'object',
                    "key": o.key,
                    "roomId": o.roomId,
                    "modelId": o.modelId,
                    "format": o.format,
                    "coarseSemantic": o.coarseSemantic,
                    "isSceneObj": true,
                    "world_mtx": o.world_mtx,
                    "json": o
                };
                scene.add(object3d); 
            }
        })
    });
}

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
        action.weight = 0;
        let startState = 'origin';
        if(object3d.userData.json){startState = object3d.userData.json.startState;}
        if(startState === animation.name){
            action.time = action.getClip().duration;
            action.weight = 1;
        }
        action.getMixer().addEventListener('finished', e => {
            let action = e.action;
            action.reset();action.paused = true;
            action.afterCall(action);
            // action.time = action.getClip().duration;action.weight = 1;
            // console.log('starting forth to target', action.weight, action.getClip().name);
        });
        // object3d.currentAction = action;
        object3d.actions[animation.name] = action;
    });
}

const actionSet = function(object3d, status){
    if(object3d.actions === undefined){
        return;
    }
    if(object3d.actions.length === 0){
        return;
    }
    let anames = Object.keys(object3d.actions);
    anames.forEach(aname => {
        let action = object3d.actions[aname];
        action.reset();action.paused = true;action.weight = 0;
    });
    if(status === 'origin'){
        return;
    }
    let action = object3d.actions[status];
    action.reset();action.paused = true;
    action.time = action.getClip().duration;
    action.weight = 1;
}

const getMaterial = function(imgPath){
    let texture = new THREE.TextureLoader().load(imgPath);
    texture.wrapS = THREE.RepeatWrapping;
    texture.wrapT = THREE.RepeatWrapping;
    texture.repeat.set(1, 1);
    return new THREE.MeshPhongMaterial( { map: texture } );
}

const getShapeByAreaShape = function(areaShape, interior){
    let shape = new THREE.Shape();
    shape.moveTo(areaShape[0][0], areaShape[0][1]);
    for(let i = 1; i < areaShape.length; i++){
        shape.lineTo(areaShape[i][0], areaShape[i][1]);
    }
    shape.lineTo(areaShape[0][0], areaShape[0][1]);
    if(interior){
        interior.forEach(itrr => {
            let path = new THREE.Path();
            path.moveTo(itrr[0][0], itrr[0][1]);
            for(let i = 1; i < itrr.length; i++){
                path.lineTo(itrr[i][0], itrr[i][1]);
            }
            path.lineTo(itrr[0][0], itrr[0][1]);
            shape.holes.push(path);
        });
    }
    return shape;
}
const waterparams = {
    color: '#0040C0',
    scale: 1,
    flowX: 10,
    flowY: 10
};
const materialMap = new Map();
const assignMaterial = function(imgpath){
    if(materialMap.has(imgpath)){
        return materialMap.get(imgpath);
    }
    else{
        materialMap.set(imgpath, getMaterial(imgpath));
    }
}
const addAreaToScene = function(mesh, room){
    mesh.rotation.x = Math.PI * 0.5;
    mesh.scale.z = -1;
    if(room.layer){mesh.position.y = room.layer*0.02;}
    mesh.userData = {'roomId': room.roomId};
    scene.add(mesh);
    areaList.push(mesh);
}
const addAreaByRoom = function(room){
    let mesh;
    if(!room.areaType){
        room.areaType = 'earth'
    }
    if(room.areaType === 'water'){
        mesh = new THREE.Water( new THREE.ShapeGeometry(getShapeByAreaShape(room.areaShape)), {
            color: waterparams.color,
            scale: waterparams.scale,
            flowDirection: new THREE.Vector2( waterparams.flowX, waterparams.flowY ),
            textureWidth: 128,
            textureHeight: 128
        });
        addAreaToScene(mesh, room);return;
    }
    if(room.areaType === 'grass'){
        mesh = new THREE.Mesh(new THREE.ShapeGeometry(getShapeByAreaShape(room.areaShape, room.interior)), assignMaterial('/GeneralTexture/grass02.jpg')) ;
    }
    if(room.areaType === 'earth'){
        mesh = new THREE.Mesh(new THREE.ShapeGeometry(getShapeByAreaShape(room.areaShape, room.interior)), assignMaterial('/GeneralTexture/earth01.jpg')) ;
    }
    if(room.areaType=='garden'){
        mesh = new THREE.Mesh(new THREE.ShapeGeometry(getShapeByAreaShape(room.areaShape, room.interior)), assignMaterial('/GeneralTexture/flower01.jpg')) ;
    }
    if(room.areaType === 'road1'){
        mesh = new THREE.Mesh(new THREE.ShapeGeometry(getShapeByAreaShape(room.areaShape, room.interior)), assignMaterial('/GeneralTexture/road01.jpg')) ;
    }
    if(room.areaType === 'road2'){
        mesh = new THREE.Mesh(new THREE.ShapeGeometry(getShapeByAreaShape(room.areaShape, room.interior)), assignMaterial('/GeneralTexture/road02.jpg')) ;
    }
    if(mesh === undefined){
        return;
    }
    if(!mesh.material.map){
        setTimeout(addAreaByRoom, 1000, room);
        return;
    }
    // const vertices = mesh.geometry.attributes.position.array;
    // for ( let i = 0, j = 0, l = vertices.length; i < l; i ++, j += 3 ) {
    //     vertices[ j + 2 ] = Math.random() * 3;
    // }
    addAreaToScene(mesh, room);
}

const areaList = [];
var areaCounter = 0;
const refreshArea = function(scene_json){
    areaCounter = 0;
    areaList.forEach(a => {
        scene.remove(a);
    });
    areaList.length = 0;
    scene_json.rooms.forEach(room => {
        if(!room.areaShape){return;}
        setTimeout(addAreaByRoom, areaCounter * 100, room);
        areaCounter++;
    });
}


const addWater = function(geometry){
    const watermaterial = 1;
}