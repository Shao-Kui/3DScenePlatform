const canvasForImage = document.createElement('canvas');
const decideTransparencyByTexture = function(m, g, offset=0){
    if(m.transparent){return true;}
    if(!g.attributes.uv){return false;}
    if(!m.map){return false;}
    if(!m.map.image){return false;}
    canvasForImage.width = m.map.image.width;
    canvasForImage.height = m.map.image.height;
    canvasForImage.getContext('2d').drawImage(m.map.image, 0, 0, m.map.image.width, m.map.image.height);
    let alpha = canvasForImage.getContext('2d').getImageData(
        m.map.image.width * g.attributes.uv.array[0 + offset*2],
        m.map.image.height * (1 - g.attributes.uv.array[1 + offset*2]),
        1,1
    ).data
    if(alpha[3] < 255){
        return true;
    }else{
        return false;
    }
}
const decideTransparencyByTextureArray = function(m, g){
    if(Array.isArray(m)){
        for(let i = 0; i < g.groups.length; i++){
            let t1 = decideTransparencyByTexture(m[g.groups[i].materialIndex], g, g.groups[i].start + g.groups[i].count-1);
            let t2 = decideTransparencyByTexture(m[g.groups[i].materialIndex], g, g.groups[i].start + Math.trunc(g.groups[i].count/2));
            let t3 = decideTransparencyByTexture(m[g.groups[i].materialIndex], g, g.groups[i].start);
            m[g.groups[i].materialIndex].transparent = t1 || t2 || t3;
            
            // m[g.groups[i].materialIndex].transparent = false;
            // for(let i = g.groups[i].start; i < g.groups[i].start + g.groups[i].count; i = i + 1){
            //     m[g.groups[i].materialIndex].transparent = m[g.groups[i].materialIndex].transparent || decideTransparencyByTexture(m[g.groups[i].materialIndex], g, i);
            //     if(m[g.groups[i].materialIndex].transparent = m[g.groups[i].materialIndex].transparent){
            //         break;
            //     }
            // }
        }
    }else{
        let t1 = decideTransparencyByTexture(m, g, 0);
        let t2 = false, t3 = false, t4 = false;
        if(g.attributes.uv){
            t2 = decideTransparencyByTexture(m, g, Math.trunc(g.attributes.uv.count/2));
            t3 = decideTransparencyByTexture(m, g, g.attributes.uv.count-1);
            t4 = decideTransparencyByTexture(m, g, Math.trunc(g.attributes.uv.count * 0.7));
        }
        m.transparent = t1 || t2 || t3 || t4;

        // m.transparent = false;
        // for(let i = 0; i < g.attributes.uv.count; i = i + 1){
        //     m.transparent = m.transparent || decideTransparencyByTexture(m, g, i);
        //     if(m.transparent){
        //         break;
        //     }
        // }
    }
}
const checkTextureOpacity = function(m, g){
    if(!m){
        return;
    }
    if(Array.isArray(m)){
        for(let i = 0; i < m.length; i++){
            if(!m[i].map){
                continue;
            }
            if(!m[i].map.image){
                setTimeout(checkTextureOpacity, 3000, m, g);
                return;
            }else{
                decideTransparencyByTextureArray(m, g);
            }
        }
    }else{
        if(!m.map){
            return;
        }
        if(!m.map.image){
            setTimeout(checkTextureOpacity, 3000, m, g);
            return;
        }else{
            decideTransparencyByTextureArray(m, g);
        }
    }
}
const traverseObjSetting = function (object) {
    if(object instanceof THREE.Mesh){
        object.castShadow = true;
        object.receiveShadow = true;
        checkTextureOpacity(object.material, object.geometry);
        if(Array.isArray(object.material)){
            for(let i = 0; i < object.material.length; i++){
                object.material[i].reflectivity = 0;
                if(object.material[i].transparent){
                    object.castShadow = false;
                }
            }
        }else{
            if(object.material.transparent){
                object.material.reflectivity = 0;
                object.castShadow = false;
            }
        }
        return;
    }
    if(object.children.length === 0){
        return;
    }
    object.children.forEach(function(child){
        traverseObjSetting(child);
    });
};

class SceneManager {
    constructor(parent_manager, canvas) {
        this.parent_manager = parent_manager;
        this.canvas = canvas;
        this.objectInfoCache = {};
        this.instanceKeyCache = {};
        this.latentNameCache = {};
        this.cwfCache = []; 
        this.fCache = []; 
        this.wfCache = []; 
        this.wCache = []; 
        this.newWallCache = []; 
        this.init_canvas();
    }

    init_canvas = () => {
        var self = this;
        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(75, $(this.canvas).width() / $(this.canvas).height(), 0.01, 1000);
        this.camera.userData = {"type": "camera"};
        this.camera.rotation.order = 'YXZ';
        this.camera.position.set(0, 6, 0);
        this.scene.add(this.camera);
        // const renderer = new THREE.RayTracingRenderer();
        this.renderer = new THREE.WebGLRenderer({canvas: this.canvas, 
            alpha: true, 
            antialias: 4, 
            preserveDrawingBuffer: true}
        );
        this.renderer.setClearColor(0xffffff, 0); // second param is opacity, 0 => transparent
        this.renderer.physicallyCorrectLights = true;
        this.renderer.outputEncoding = THREE.sRGBEncoding;
        this.renderer.shadowMap.enabled = true;
        this.renderer.toneMapping = THREE.ReinhardToneMapping;

        // Start to configurate the orthogonal top renderer and camera.
        this.orthrenderer = new THREE.WebGLRenderer({
            canvas: ($(this.parent_manager.uiDOM).find("#orthcanvas"))[0],
            alpha: true,
            antialias: 4
        });
        this.orthrenderer.setClearColor(0xeeeeee, 0.66);
        this.orthrenderer.physicallyCorrectLights = true;
        this.orthrenderer.outputEncoding = THREE.sRGBEncoding;
        this.orthrenderer.shadowMap.enabled = true;
        this.orthrenderer.toneMapping = THREE.ReinhardToneMapping;
        var owidth = 50;
        var oheight = 50;
        this.orthcamera = new THREE.OrthographicCamera(owidth / -2, owidth / 2, oheight / 2, oheight / -2, 0.01, 1000);
        this.orthcamera.userData = {"type": "camera"};
        this.scene.add(this.orthcamera);
        this.on_resize();
        orbitControls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
        firstPersonControls = new THREE.PointerLockControls(this.camera, this.renderer.domElement);
        transformControls = new THREE.TransformControls(this.camera, this.renderer.domElement);
        transformControlsConfig();
        this.scene.add(transformControls);
        // firstPersonControls = new THREE.PointerLockControls(this.camera);
        this.camera.position.set(0, 6, 0);
        this.camera.lookAt(9, 6, 12);
        orbitControls.target.set(9, 6, 12);
    };

    scene_remove = datafilter => {
        var self = this;
        var instances_to_remove = [];
        this.scene.children.forEach(function (inst) {
            if (inst.userData) {
                var userData = inst.userData;
                if (datafilter(userData)) {
                    instances_to_remove.push(inst);
                }
            }
        });
        instances_to_remove.forEach(function (inst) {
            self.scene.remove(inst);
        });
    };

    refresh_scene = (scene_json, refresh_camera = false) => {
        // this.scene_remove((userData)=>(userData.type=="object" && this.instanceKeyCache[userData.key]));
        this.scene_remove( (userData) => (userData.type === "object" && this.instanceKeyCache[userData.key]) );
        this.scene_remove(function (userData) {
            if (userData.type === 'w' ||
                userData.type === 'f' ||
                userData.type === 'd' ||
                userData.type === 'c' ||
                userData.type === 'object') {
                return true;
            }
        });
        this.instanceKeyCache = {};
        traverseSceneJson(scene_json);
        outlinePass.selectedObjects = [];
        outlinePass2.selectedObjects = [];
        if(scene_json.islod){
            this.islod = true;
            $("#lodCheckBox").prop('checked', true);
        }else{
            this.islod = false;
            $("#lodCheckBox").prop('checked', false);
        }
        this.defaultCWFMaterial = getMaterial('/GeneralTexture/51124.jpg');
        this.scene_json = scene_json;
        this.refresh_wall_and_floor();
        this.refresh_instances();
        this.refresh_light();
        if (refresh_camera) {
            this.refresh_camera();
        }
        ALL_SCENE_READY = true;
        refreshArea(this.scene_json);
        if(this.scene_json.rooms[0].totalAnimaID){
            let taID = this.scene_json.rooms[0].totalAnimaID;
            $.getJSON(`/static/dataset/infiniteLayout/${taID}.json`, data => {
                currentAnimation = data;
                $.getJSON(`/static/dataset/infiniteLayout/${this.scene_json.rooms[0].totalAnimaID}img/layoutTree.json`, function (nextdata) {
                    updateTreeWindow(nextdata); // This code initialize the Tree for InfiniteLayout. 
                });
            });
        }
    };

    refresh_light(){
        var bbox = this.scene_json.bbox;
        lx_level = (bbox.max[0] + bbox.min[0]) / 2;
        lz_level = (bbox.max[2] + bbox.min[2]) / 2;
        spotLight.position.set(lx_level, 12, lz_level);
        spotLight.target.position.set(lx_level, 0, lz_level);
    }

    refresh_wall_and_floor = () => {
        this.cwfCache = [];
        this.fCache = []; 
        this.wfCache = []; 
        this.wCache = []; 
        this.newWallCache = [];
        this.useNewWall = USE_NEW_WALL;
        if (this.useNewWall)
            this.reconstructWalls();
        var self = this;
        for (var i = 0; i < this.scene_json.rooms.length; i++) {
            self.load_cwf_room_meta(this.scene_json.rooms[i])
        }
    };

    load_cwf_room_meta = room => {
        var self = this;
        fetch("/room/" + this.scene_json.origin + "/" + room.modelId).then(function (response) {
            return response.json();
        }).then(function (meta) {
            for (var j = 0; j < meta.length; j++) {
                if (meta[j] === 'c') {
                    continue;
                }
                self.load_cwf_instances(room.modelId, meta[j], room.roomId);
            }
        })
    };

    load_cwf_instances = (modelId, suffix, roomId) => {
        var meta = modelId + suffix;
        var self = this;
        var objLoader = new THREE.OBJLoader(this.loadingManager);
        let mtl_path = "/room/" + self.scene_json.origin + "/" + meta + '.mtl';
        let obj_path = "/room/" + self.scene_json.origin + "/" + meta + '.obj';
        objLoader.load(obj_path, function (instance) {
            // var instance = event.detail.loaderRootNode;
            instance.userData = {"type": suffix, "roomId": roomId, "meta": meta, "modelId": modelId};
            instance.castShadow = true;
            instance.receiveShadow = true;
            instance.name = meta;
            traverseObjSetting(instance);
            // self.scene.add(instance);
            if(suffix === 'f'){
                instance.traverse(function(child){
                    if(child instanceof THREE.Mesh){
                        // child.material.color.setHex(0x8899AA);
                        // child.material.map = texture;
                        // child.material = material
                    }
                });
                if (self.useNewWall == false) {
                    self.scene.add(instance);
                    self.cwfCache.push(instance);
                    self.fCache.push(instance);
                    self.wfCache.push(instance);
                }
            }
            if(suffix === 'w'){
                instance.traverse(function(child){
                    if(child instanceof THREE.Mesh){
                        // child.material.color.setHex(0x8899AA);
                    }
                });
                if (self.useNewWall == false) {
                    self.scene.add(instance);
                    self.cwfCache.push(instance);
                    self.wfCache.push(instance);
                }
                self.wCache.push(instance); 
            }
            instance.children.forEach(c => {
                c.material = self.defaultCWFMaterial;
            });
        }, null, null, null, false);
    }

    //     objLoader.loadMtl(mtl_path, null, function (materials) {
    //         objLoader.setModelName(meta);
    //         objLoader.setMaterials(materials);
    //         objLoader.load(obj_path, function (event) {
    //             var instance = event.detail.loaderRootNode;
    //             instance.userData = {"type": suffix, "roomId": roomId};
    //             instance.castShadow = true;
    //             instance.receiveShadow = true;
    //             traverseObjSetting(instance);
    //             self.scene.add(instance);
    //             if (suffix === 'f') {
    //                 self.cwfCache.push(instance);
    //             }
    //         }, null, null, null, false);
    //     }, null, function(){
    //         objLoader.setModelName(meta);
    //         objLoader.load(obj_path, function (event) {
    //             var instance = event.detail.loaderRootNode;
    //             instance.userData = {"type": suffix, "roomId": roomId};
    //             instance.castShadow = true;
    //             instance.receiveShadow = true;
    //             traverseObjSetting(instance);
    //             self.scene.add(instance);
    //             if(suffix === 'w'){
    //                 instance.traverse(function(child){
    //                     if(child instanceof THREE.Mesh){
    //                         child.material.color.setHex(0xFFFFFF);
    //                     }
    //                 });
    //             }
    //             if (suffix === 'f') {
    //                 instance.traverse(function(child){
    //                     if(child instanceof THREE.Mesh){
    //                         child.material.color.setHex(0x8899AA);
    //                     }
    //                 });
    //                 self.cwfCache.push(instance);
    //             }
    //         }, null, null, null, false);
    //     });
    // };

    refresh_instances(){
	    // var self=this;
        let loadingCounter = 0;
        this.scene_json.rooms.forEach(function(room){
            room.objList.forEach(async function(inst){ //an obj is a instance
                if(inst === null || inst == undefined){
                    return;
                }
                if(inst.format === 'Door' || inst.format === 'Window'){
                    if(inst.format === 'Door') inst.modelId = '214';
                    if(inst.format === 'Window') inst.modelId = '126';
                    loadObjectToCache(inst.modelId, function(){
                        refreshObjectFromCache(inst);
                    }, [], inst.format);
                }
                if('inDatabase' in inst)
                    if(!inst.inDatabase)
                        return;
                if(inst.modelId === 'noUse'){
                    return;
                }
                if(inst.key === undefined) inst.key=THREE.Math.generateUUID();
                if(!('format' in inst)){
                    inst.format = 'obj';
                }
                setTimeout(loadObjectToCache, loadingCounter*100, inst.modelId, function(){
                    refreshObjectFromCache(inst);
                }, [], inst.format);
                loadingCounter++;
                // loadObjectToCache(inst.modelId, function(){
                //     refreshObjectFromCache(inst);
                // }, [], inst.format);
            });
        });
        if('sceneFutureCache' in this.scene_json){
            this.scene_json.sceneFutureCache.forEach(modelId => {
                loadObjectToCache(modelId);
            });
        }
        
	}

    refresh_camera = () => {
        var bbox = this.scene_json.bbox;
        var lx = (bbox.max[0] + bbox.min[0]) / 2;
        var lz = (bbox.max[2] + bbox.min[2]) / 2;
        this.camera.rotation.order = 'YXZ';
        this.camera.position.set(lx, 6, lz);
        this.camera.lookAt(lx, 0, lz);
        orbitControls.target.set(lx, 0, lz);
        //Start to set orthogonal camera.
        var width = (bbox.max[0] - bbox.min[0]) + 1;
        var height = (bbox.max[2] - bbox.min[2]) + 1;
        this.orthcamera.left = width / -2;
        this.orthcamera.right = width / 2;
        this.orthcamera.top = height / 2;
        this.orthcamera.bottom = height / -2;
        this.orthcamera.updateProjectionMatrix();
        this.orthcamera.position.set(lx, 200, lz);
        this.orthcamera.lookAt(lx, 0, lz);
    };

    on_resize = () => {
        this.canvas.width = $(this.canvas).width();
        this.canvas.height = $(this.canvas).height();
        this.camera.aspect = this.canvas.width / this.canvas.height;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(this.canvas.width, this.canvas.height);
    };
    
    addWall = (walls, coor, s, t) => {
        let keyNotExist = true;
        for (const key in walls) {
            if (Math.abs(coor - key) > 0.001) continue;
            else keyNotExist = false;
            let seg = walls[key];
            seg.push([s, t, false]);
            seg.sort((a, b) => a[0] == b[0] ? a[1] - b[1] : a[0] - b[0]);
            for (let i = 1; i < seg.length;) {
                if (seg[i][1] <= seg[i - 1][1]) {
                    seg.splice(i, 1);
                } else if (seg[i][0] <= seg[i - 1][1] + 0.241) {
                    seg[i - 1][1] = seg[i][1];
                    seg.splice(i, 1);
                } else {
                    i++;
                }
            }
        }
        if (keyNotExist) {
            // coor = Math.round(coor*10000)/10000;
            walls[coor] = [[s, t, false]];
        }
    }

    addEdge = (v1, v2, norm) => {
        if (v1[0] == v2[0]) {
            let s = Math.min(v1[1], v2[1]);
            let t = Math.max(v1[1], v2[1]);
            if (norm[0] < 0)
                this.addWall(this.walls.x[0], v1[0], s, t);
            else
                this.addWall(this.walls.x[1], v1[0], s, t);
        }
        if (v1[1] == v2[1]) {
            let s = Math.min(v1[0], v2[0]);
            let t = Math.max(v1[0], v2[0]);
            if (norm[1] < 0)
                this.addWall(this.walls.z[0], v1[1], s, t);
            else
                this.addWall(this.walls.z[1], v1[1], s, t);
        }
    }

    genWallMesh = (x, y, z, py) => {
        const material = new THREE.MeshBasicMaterial();
        let geometry = new THREE.BoxGeometry(x, y, z);
        // geometry.translate(px, py, pz);
        let newWall = new THREE.Mesh(geometry, material);
        newWall.position.setY(py);
        return newWall;
    }

    addWallGroup = (axis, k0, k1, w) => {
        w.splice(2, 1);
        let groupId = this.wallGroup.length;
        let wg = { "axis": axis, "groupId": groupId, "coor": [k0, k1], "halfWidth": (k1-k0)/2, "seg": w, "x": [], "z": [], "wd": [], "walls": [], "idxRange": [], "adjFloor": [], "adjWall": [], "adjRoomShape": [] };
        if (axis == "x") {
            wg.x = [k0, k1];
            wg.z = w;
        }
        else {
            wg.x = w;
            wg.z = [k0, k1];
        }
        this.wallGroup.push(wg);
    }

    reconstructWalls = () => {
        var self = this;
        this.walls = { x: [{}, {}], z: [{}, {}] };
        this.wallGroup = [];

        const rooms = this.scene_json.rooms;
        rooms.forEach(room => {
            let roomShape = room.roomShape;
            if (roomShape == undefined) return;
            let max = [...roomShape[0]], min = [...roomShape[0]];
            for (let i = 0; i < roomShape.length; ++i) {
                let j = (i + 1) == roomShape.length ? 0 : i + 1;
                self.addEdge(roomShape[i], roomShape[j], room.roomNorm[i]);
                max[0] = Math.max(max[0], roomShape[i][0]);
                max[1] = Math.max(max[1], roomShape[i][1]);
                min[0] = Math.min(min[0], roomShape[i][0]);
                min[1] = Math.min(min[1], roomShape[i][1]);
            }
            room["roomShapeBBox"] = {"max": max, "min": min}
        });

        rooms.forEach(room => {
            const roomShape = room.roomShape;
            if (roomShape == undefined) return;
            var contour = [];
            for (let v of roomShape) {
                contour.push(new THREE.Vector2(v[0], v[1]));
            }
            var triangles = THREE.ShapeUtils.triangulateShape(contour, []);
            const vertices = [];
            const normal = [];
            const geometry = new THREE.BufferGeometry();
            for (let f of triangles) {
                for (let i = 2; i >= 0; --i) {
                    vertices.push(roomShape[f[i]][0]);
                    vertices.push(0.0);
                    vertices.push(roomShape[f[i]][1]);
                    normal.push(0, 1, 0);
                }
            }
            geometry.setAttribute( 'position', new THREE.BufferAttribute( Float32Array.from(vertices), 3 ) );
            geometry.setAttribute( 'normal', new THREE.BufferAttribute( Float32Array.from(normal), 3 ) );
            const mesh = new THREE.Mesh( geometry, self.defaultCWFMaterial);
            let instance = new THREE.Group();
            instance.add(mesh);
            instance.userData = {"type": 'f', "roomId": room.roomId, "meta": "newFloor", "modelId": "newFloor"};
            instance.castShadow = true;
            instance.receiveShadow = true;
            instance.name = "newFloor" + room.roomId;
            traverseObjSetting(instance);
            self.scene.add(instance);
            self.cwfCache.push(instance);
            self.fCache.push(instance);
            self.wfCache.push(instance);
        });

        for (const axis of ["x", "z"]) {
            let wall0 = this.walls[axis][0];
            let wall1 = this.walls[axis][1]
            let key0 = Object.keys(wall0);
            let key1 = Object.keys(wall1);
            key0.sort((a, b) => parseFloat(a) - parseFloat(b));
            key1.sort((a, b) => parseFloat(a) - parseFloat(b));
            key0.forEach((val,idx)=>key0[idx]=parseFloat(val));
            key1.forEach((val,idx)=>key1[idx]=parseFloat(val));
            for (let k0 of key0) {
                let seg0 = [...wall0[k0]];
                for (let k1 of key1) {
                    if (k0 > k1) continue;
                    if (k0 + 0.25 < k1) break;
                    let tmpSeg=[];
                    for (let i = 0; i < seg0.length; ++i) {
                        let w0 = wall0[k0][i];
                        for (let w1 of wall1[k1]) {
                            if (w0[0]>w1[1] || w0[1]<w1[0]) continue;
                            tmpSeg.push([Math.min(w0[0], w1[0]), Math.max(w0[1], w1[1])]);
                            seg0.splice(i, 1);
                            w1[2] = true;
                            break;
                        }
                    }
                    tmpSeg.sort((a, b) => a[0] == b[0] ? a[1] - b[1] : a[0] - b[0]);
                    for (let i = 1; i < tmpSeg.length;) {
                        if (tmpSeg[i][1] <= tmpSeg[i - 1][1]) {
                            tmpSeg.splice(i, 1);
                        } else if (tmpSeg[i][0] <= tmpSeg[i - 1][1] + 0.001) {
                            tmpSeg[i - 1][1] = tmpSeg[i][1];
                            tmpSeg.splice(i, 1);
                        } else {
                            i++;
                        }
                    }
                    
                    for (let w of tmpSeg)
                        this.addWallGroup(axis, k0, k1, w);
                }
                
                for (let w0 of seg0)
                    this.addWallGroup(axis, k0, k0+0.24, w0);
            }
            for (let k1 of key1)
                for (let w1 of wall1[k1])
                    if (!w1[2])
                        this.addWallGroup(axis, k1 - 0.24, k1, w1);
        }

        for (let wg of this.wallGroup) {
            for (let room of rooms) {
                let bbox = room.roomShapeBBox;
                if (bbox == undefined) continue;
                if (bbox.min[0] > wg.x[1] || bbox.max[0] < wg.x[0] || bbox.min[1] > wg.z[1] || bbox.max[1] < wg.z[0])
                    continue;
                let pIdList = [[], []];
                let roomShape = room.roomShape;
                for (let i = 0; i < roomShape.length; ++i) {
                    let x = roomShape[i][0], z = roomShape[i][1];
                    if (wg.x[0] <= x && x <= wg.x[1] && wg.z[0] <= z && z <= wg.z[1]) {
                        if (wg.axis == "x") {
                            if (Math.abs(x-wg.x[0])<0.001)
                                pIdList[0].push(i);
                            else if (Math.abs(x-wg.x[1])<0.001)
                                pIdList[1].push(i);
                        } else {
                            if (Math.abs(z-wg.z[0])<0.001)
                                pIdList[0].push(i);
                            else if (Math.abs(z-wg.z[1])<0.001)
                                pIdList[1].push(i);
                        }
                    }
                }
                if (pIdList[0].length || pIdList[1].length) {
                    wg.adjRoomShape.push([room.roomId, pIdList]);
                    room.objList.forEach(obj => {
                        let bbox = obj.bbox;
                        if (obj.coarseSemantic == "Window" || obj.coarseSemantic == "Door")
                            if (!(bbox.min[0] > wg.x[1] || bbox.max[0] < wg.x[0] || bbox.min[2] > wg.z[1] || bbox.max[2] < wg.z[0] || bbox.min[1]==bbox.max[1])) {
                                if (wg.axis == "x")
                                    wg.wd.push([bbox.min[2], bbox.max[2], bbox.min[1], bbox.max[1]]);
                                else
                                    wg.wd.push([bbox.min[0], bbox.max[0], bbox.min[1], bbox.max[1]]);
                            }
                    });
                }
            }
            if (wg.wd.length == 0) {
                wg.walls.push(wg.seg);
            } else {
                wg.wd.sort((a, b)=>a[0]-b[0]);
                wg.walls.push([wg.seg[0], wg.wd[0][0]]);
                for (let i = 0; i < wg.wd.length; ++i) {
                    wg.walls.push(wg.wd[i]);
                    if (i < wg.wd.length - 1)
                        wg.walls.push([wg.wd[i][1], wg.wd[i+1][0]]);
                    else
                        wg.walls.push([wg.wd[i][1], wg.seg[1]]);
                }
            }
        }

        for (let groupId = 0; groupId < this.wallGroup.length; ++groupId) {
            let wg = this.wallGroup[groupId];
            let ls = this.newWallCache.length;
            let axis = wg.axis;
            let x, z, px, pz;
            for (let w of wg.walls) {
                let curIdx = this.newWallCache.length;
                if (axis == "x") {
                    x = wg.x[1] - wg.x[0];
                    z = w[1] - w[0];
                    px = (wg.x[1] + wg.x[0]) / 2;
                    pz = (w[1] + w[0]) / 2;
                } else {
                    x = w[1] - w[0];
                    z = wg.z[1] - wg.z[0];
                    px = (w[1] + w[0]) / 2;
                    pz = (wg.z[1] + wg.z[0]) / 2;
                }
                let instance = new THREE.Group();
                let roomHeight = 2.8
                if (w.length == 2) {
                    instance.add(this.genWallMesh(x, roomHeight, z, roomHeight/2));
                    instance.userData = {"type": "w", "axis": axis, "groupId": groupId, "index": curIdx};
                } else {
                    instance.add(this.genWallMesh(x, roomHeight-w[3], z, (roomHeight-w[3])/2+w[3]));
                    instance.add(this.genWallMesh(x, w[2], z, w[2] / 2));
                    instance.userData = {"type": "d", "axis": axis, "groupId": groupId, "index": curIdx};
                }
                instance.position.setX(px);
                instance.position.setZ(pz);
                instance.children.forEach(c => {
                    c.material = self.defaultCWFMaterial;
                });
                this.scene.add(instance);
                this.newWallCache.push(instance);
                this.cwfCache.push(instance);
                this.wfCache.push(instance);
                this.wCache.push(instance); 
            }
            let lt = this.newWallCache.length;
            wg.idxRange = [ls, lt];
            
            let adjFloor = []
            for (let f = 0; f < this.fCache.length; ++f) {
                let pIdList = [[], []];
                let instance = this.fCache[f];
                instance.traverse(function (child) {
                    if (child instanceof THREE.Mesh) {
                        let attr = child.geometry.attributes;
                        let pos = attr.position.array;
                        for (let i = axis == "x" ? 0 : 2; i < pos.length; i += 3) {
                            let q = axis == "x" ? pos[i + 2] : pos[i - 2];
                            if (q < wg.seg[0] - 0.25 || q > wg.seg[1] + 0.25) continue;
                            if (Math.abs(pos[i] - wg.coor[0]) < 0.001) {
                                pIdList[0].push(i);
                            } else if (Math.abs(pos[i] - wg.coor[1]) < 0.001) {
                                pIdList[1].push(i);
                            }
                        }
                    }
                });
                if (pIdList[0].length || pIdList[1].length)
                    adjFloor.push([f, pIdList]);
            }
            wg.adjFloor = adjFloor;
        }

        for (let wg of this.wallGroup) {
            let adjWall = [];
            let axis = wg.axis;
            let coor = wg.coor;
            for (let w = 0; w < this.newWallCache.length; ++w) {
                let instance = this.newWallCache[w];
                if (instance.userData.axis == axis) continue;
                if (instance.userData.type == "d") continue;
                let pIdList = [[], []];
                let pos = instance.children[0].geometry.attributes.position.array;
                let offsetp = axis == "x" ? instance.position.x : instance.position.z;
                let offsetq = axis == "x" ? instance.position.z : instance.position.x;
                for (let i = axis == "x" ? 0 : 2; i < pos.length; i += 3) {
                    let q = axis == "x" ? pos[i + 2] : pos[i - 2];
                    if (offsetq + q < wg.seg[0]-0.25 || offsetq + q > wg.seg[1]+0.25) continue;
                    if (Math.abs(offsetp + pos[i] - coor[0])<0.001) {
                        pIdList[0].push(i);
                    } else if (Math.abs(offsetp + pos[i] - coor[1])<0.001) {
                        pIdList[1].push(i);
                    }
                }
                if (pIdList[0].length || pIdList[1].length) {
                    adjWall.push([w, pIdList]);
                }
            }
            wg.adjWall = adjWall;
        }
        let geometry = new THREE.BoxGeometry(100, 0, 100);
        // const material = new THREE.MeshBasicMaterial();
        this.infFloor = new THREE.Mesh(geometry, self.defaultCWFMaterial);
    }
}

class SceneController {
    constructor(uiDOM) {
        this.uiDOM = uiDOM;
        this.renderManager = new SceneManager(this, ($(this.uiDOM).find("#scenecanvas"))[0]);
        this.init_menu();
    }

    init_menu() {
        this.init_load_button();
    }

    init_load_button() {
        this.load_button = ($(this.uiDOM).find("#load_button"))[0];
        this.load_dialog = ($(this.uiDOM).find("#load_dialog"))[0];
        this.load_dialog_input = ($(this.uiDOM).find("#load_dialog_input"))[0];
        this.load_dialog_button = ($(this.uiDOM).find("#load_dialog_button"))[0];
        $(this.load_dialog).dialog({autoOpen: false});
        $(this.load_button).click(this.load_button_click());
        $(this.load_dialog_button).click(this.load_dialog_button_click());
    }

    load_button_click() { //use closure to pass self
        var self = this;
        return function () {
            $(self.load_dialog).dialog("open");
        };
    }

    load_dialog_button_click() {
        var self = this;
        return function () {
            var files = $(self.load_dialog_input)[0].files;
            if (files.length <= 0) {
                return;
            }
            var fr = new FileReader();
            fr.onload = function (e) {
                var result = JSON.parse(e.target.result);
                socket.emit('sceneRefresh', result, onlineGroup);
                // self.load_scene(result);
            };
            fr.readAsText(files.item(0));
            $(self.load_dialog).dialog("close");
        };
    }

    load_scene(json) {
        $('#tab_origin').text(json.origin);
        this.renderManager.refresh_scene(json, true); 
        _refresh_mageAdd_wall(json); 
        genFloorPlanWallTensors();
    }
}
