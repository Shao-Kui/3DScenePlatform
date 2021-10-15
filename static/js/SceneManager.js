const traverseObjSetting = function (object) {
    if(object instanceof THREE.Mesh){
        object.castShadow = true;
        object.receiveShadow = true;
        if(Array.isArray(object.material)){
            for(let i = 0; i < object.material.length; i++){
                if(object.material[i].transparent){
                    object.castShadow = false;
                }
            }
        }else{
            if(object.material.transparent){
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
        console.log('called refresh scene! ');
        this.scene_remove(function (userData) {
            if (userData.type === 'w' ||
                userData.type === 'f' ||
                userData.type === 'c'||
                userData.type === 'object') {
                return true;
            }
        });
        this.scene_json = scene_json;
        this.refresh_wall_and_floor();
        this.refresh_instances();
        this.refresh_light();
        if (refresh_camera) {
            this.refresh_camera();
        }
        ALL_SCENE_READY = true;
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
        var objLoader = new THREE.OBJLoader();
        let mtl_path = "/room/" + self.scene_json.origin + "/" + meta + '.mtl';
        let obj_path = "/room/" + self.scene_json.origin + "/" + meta + '.obj';
        objLoader.load(obj_path, function (instance) {
            // var instance = event.detail.loaderRootNode;
            instance.userData = {"type": suffix, "roomId": roomId, "meta": meta, "modelId": modelId};
            instance.castShadow = true;
            instance.receiveShadow = true;
            instance.name = meta;
            traverseObjSetting(instance);
            self.scene.add(instance);
            if(suffix === 'f'){
                instance.traverse(function(child){
                    if(child instanceof THREE.Mesh){
                        // child.material.color.setHex(0x8899AA);
                        // child.material.map = texture;
                        // child.material = material
                    }
                });
                self.cwfCache.push(instance);
                self.fCache.push(instance);
                self.wfCache.push(instance);
            }
            if(suffix === 'w'){
                instance.traverse(function(child){
                    if(child instanceof THREE.Mesh){
                        // child.material.color.setHex(0x8899AA);
                    }
                });
                self.cwfCache.push(instance);
                self.wfCache.push(instance);
                self.wCache.push(instance); 
            }
            instance
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
		this.scene_remove((userData)=>(userData.type=="object" && this.instanceKeyCache[userData.key]));
		this.instanceKeyCache = {};
        this.scene_json.rooms.forEach(function(room){
            room.objList.forEach(async function(inst){ //an obj is a instance
                if(inst === null || inst == undefined){
                    return;
                }
                if('inDatabase' in inst)
                    if(!inst.inDatabase)
                        return;
                if(inst.key === undefined) inst.key=THREE.Math.generateUUID();
                loadObjectToCache(inst.modelId, function(){
                    refreshObjectFromCache(inst);
                });
            });
        });
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
        var width = bbox.max[0] - bbox.min[0];
        var height = bbox.max[2] - bbox.min[2];
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
