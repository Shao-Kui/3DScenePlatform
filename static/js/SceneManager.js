function pausecomp(millis) {
    var date = new Date();
    var curDate = null;
    do {
        curDate = new Date();
    }
    while (curDate - date < millis);
}

var traverseObjSetting = function (object) {
    if(object instanceof THREE.Mesh){
        object.castShadow = true;
        object.receiveShadow = true;
        if(Array.isArray(object.material)){
            for(var i = 0; i < object.material.length; i++){
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
    })
};

class SceneManager {
    constructor(parent_manager, canvas) {

        this.parent_manager = parent_manager;
        this.canvas = canvas;
        this.objectInfoCache = {};
        this.instanceKeyCache = {};

        this.latentNameCache = {};

        this.cwfCache = [];
        this.init_canvas();
    }


    init_canvas = () => {

        var self = this;
        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(75, $(this.canvas).width() / $(this.canvas).height(), 0.01, 1000);
        this.camera.userData = {"type": "camera"};
        this.scene.add(this.camera);
        // const renderer = new THREE.RayTracingRenderer();
        this.renderer = new THREE.WebGLRenderer({canvas: this.canvas, 
            alpha: true, 
            antialias: 4, 
            preserveDrawingBuffer: true});

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
        console.log(instances_to_remove);
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
        var objLoader = new THREE.OBJLoader2();
        var mtl_path = "/room/" + self.scene_json.origin + "/" + meta + '.mtl';
        var obj_path = "/room/" + self.scene_json.origin + "/" + meta + '.obj';
        objLoader.loadMtl(mtl_path, null, function (materials) {
            objLoader.setModelName(meta);
            objLoader.setMaterials(materials);
            objLoader.load(obj_path, function (event) {
                var instance = event.detail.loaderRootNode;
                instance.userData = {"type": suffix, "roomId": roomId};
                instance.castShadow = true;
                instance.receiveShadow = true;
                traverseObjSetting(instance);
                self.scene.add(instance);
                if (suffix === 'f') {
                    self.cwfCache.push(instance);
                }
            }, null, null, null, false);
        }, null, function(){
            objLoader.setModelName(meta);
            objLoader.load(obj_path, function (event) {
                var instance = event.detail.loaderRootNode;
                instance.userData = {"type": suffix, "roomId": roomId};
                instance.castShadow = true;
                instance.receiveShadow = true;
                traverseObjSetting(instance);
                self.scene.add(instance);
                if (suffix === 'f') {
                    self.cwfCache.push(instance);
                }
            }, null, null, null, false);
        });
    };

    refresh_instances(){
	    //try to add unique id for each instanceof
	    var self=this;
	    var newkeycache={};
        this.scene_json.rooms.forEach(function(room){
            room.objList.forEach(function(inst){ //an obj is a instance
                if(inst === null || inst == undefined){
                    return;
                }
                if('inDatabase' in inst)
                    if(!inst.inDatabase)
                        return;
                if(!(inst.key)){
                    inst.key=THREE.Math.generateUUID();
                }
                if(self.instanceKeyCache[inst.key]){
                    var instance=self.instanceKeyCache[inst.key];
                    instance.scale.set(inst.scale[0],inst.scale[1],inst.scale[2]);
                    instance.rotation.set(inst.rotate[0],inst.rotate[1],inst.rotate[2],inst.rotateOrder);
                    instance.position.set(inst.translate[0],inst.translate[1],inst.translate[2]);
                    newkeycache[inst.key]=instance;
                }
                else{
                    // to prevent incomplete model to be deleted by this.scene_remove
                    // newkeycache[inst.key]=true;
                    if(!(self.objectInfoCache[inst.modelId])){
                        /*fetch("/objmeta/"+inst.modelId).then(function(response) {
                            return response.json();
                        })
                        .then(function(meta) {
                            if(meta.id === undefined || meta.name === undefined){
                                return;
                            }
                            self.objectInfoCache[inst.modelId]=meta;
                            self.load_instance(inst);
                        });*/
                        let meta = {};
                        meta.mesh = `/mesh/${inst.modelId}`;
                        meta.mtl = `/mtl/${inst.modelId}`;
                        self.objectInfoCache[inst.modelId]=meta;
                        self.load_instance(inst);
                    }else{
                        self.load_instance(inst);
                    }
                }
                self.renderer.render(self.scene,self.camera);
            });
        });

		this.scene_remove((userData)=>(userData.type=="object" && !newkeycache[userData.key]));
		this.instanceKeyCache=newkeycache;
	}

    add_latent_obj = () => {
        var self = this;
        if (!this.latentNameCache[INTERSECT_OBJ.userData.name]) {
            self.latentNameCache[INTERSECT_OBJ.userData.name] = self.instanceKeyCache[INTERSECT_OBJ.userData.key];
        }
        fetch("/latent_space/" + INTERSECT_OBJ.userData.name + "/"
            + INTERSECT_OBJ.position.x + "/"
            + INTERSECT_OBJ.position.y + "/"
            + INTERSECT_OBJ.position.z + "/").then(re => {
            return re.json()
        }).then(list => {
            list.forEach(inst => {
                if (inst === null || inst === undefined) {
                    return;
                }
                if (this.latentNameCache[inst.modelId]) {
                    return;
                }
                inst.key = THREE.Math.generateUUID();
                if (self.objectInfoCache[inst.modelId]) {
                    self.load_instance(inst, "latent");
                } else {
                    fetch("/objmeta/" + inst.modelId)
                        .then(function (response) {
                            return response.json();
                        }).then(function (meta) {
                        if (meta.id === undefined || meta.name === undefined) {
                            return;
                        }
                        self.objectInfoCache[inst.modelId] = meta;
                        self.load_instance(inst, "latent");
                    });
                }
                self.renderer.render(self.scene, self.camera);
            });
        });
    };
    refresh_latent = () => {
        var hidetype = "";
        if (INTERSECT_OBJ)
            hidetype = INTERSECT_OBJ.userData.coarseSemantic;
        self.scene.children.forEach(inst => {
            if (inst.userData.type === "latent") {
                inst.visible = inst.userData.coarseSemantic !== hidetype;
            }
            if (INTERSECT_OBJ)
                INTERSECT_OBJ.visible = true;
        });

    };

    enter_latent = () => {
        var self = this;
        var iid = INTERSECT_OBJ.uuid;
        self.add_latent_obj();
        scene.children.forEach(inst => {
            if (inst.userData.type === "object" ||
                inst.userData.type === "w" ||
                inst.userData.type === "f" ||
                inst.userData.type === "c") {
                if (inst.uuid !== iid) {
                    inst.visible = false;
                }
            }
        });
    };

    quit_latent = () => {
        var self = this;
        if (INTERSECT_OBJ) {
            INTERSECT_OBJ.userData.type = 'object';
            INTERSECT_OBJ.userData.roomId = 0;
            self.scene_json.rooms[0]['objList'].push(object_to_listobject(INTERSECT_OBJ));
            for (let name in self.latentNameCache) {
                if(self.latentNameCache[name].userData.type==="latent")
                    delete self.instanceKeyCache[self.latentNameCache[name].userData.key];
            }
            self.instanceKeyCache[INTERSECT_OBJ.userData.key] = INTERSECT_OBJ;
            self.latentNameCache = {};
        }
        scene.children.forEach(inst => {
            if (inst.userData.type === "object" ||
                inst.userData.type === "w" ||
                inst.userData.type === "f" ||
                inst.userData.type === "c") {
                inst.visible = true;
            }
        });
        self.scene_remove(userData => {
            return userData.type === "latent";
        })
    };

    latent_space_click = () => {
        var self = this;
        if (latent_space_mode === false) {
            self.enter_latent();
        } else {
            self.quit_latent();
        }
        latent_space_mode = !latent_space_mode;
    };


    load_instance = (inst, object_type = 'object') => {
        //pausecomp(300);
        var self = this;
        var meta = this.objectInfoCache[inst.modelId];
        var objLoader = new THREE.OBJLoader2();
        objLoader.loadMtl(meta.mtl, null, function (materials) {
            objLoader.setModelName(inst.modelId);
            objLoader.setMaterials(materials);
            objLoader.load(meta.mesh, function (event) {
                var instance = event.detail.loaderRootNode;
                instance.scale.set(inst.scale[0], inst.scale[1], inst.scale[2]);
                instance.rotation.set(inst.rotate[0], inst.rotate[1], inst.rotate[2], inst.rotateOrder);
                instance.position.set(inst.translate[0], inst.translate[1], inst.translate[2]);
                instance.userData = {
                    "type": object_type,
                    "key": inst.key,
                    "roomId": inst.roomId,
                    "name": inst.modelId,
                    "coarseSemantic": inst.coarseSemantic
                };
                self.instanceKeyCache[inst.key] = instance;
                if (object_type === "latent")
                    self.latentNameCache[inst.modelId] = instance;
                instance.castShadow = true;
                instance.receiveShadow = true;
                traverseObjSetting(instance);
                self.scene.add(instance);
                self.renderer.render(self.scene, self.camera);
            }, null, null, null, false);
        });
    };

    refresh_camera = () => {
        console.log("start to refresh camera! ");
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

var object_to_listobject = (obj) => {
    re = {
        id: "to-do",
        type: obj.userData.type,
        modelId: obj.userData.name,
        bbox: {min: Array(3), max: Array(3)},
        translate: [obj.position.x, obj.position.y, obj.position.z],
        scale: [obj.scale.x, obj.scale.y, obj.scale.z],
        rotate: [obj.rotation._x, obj.rotation._y, obj.rotation._z],
        rotateOrder: obj.rotation._order,
        orient: "to-do",
        coarseSemantic: obj.userData.coarseSemantic,
        roomId: 0,
        key: obj.userData.key
    };
    return re;
};

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
                self.load_scene(result);
            };
            fr.readAsText(files.item(0));
            $(self.load_dialog).dialog("close");
        };
    }

    load_scene(json) {
        this.renderManager.refresh_scene(json, true);
    }

}
