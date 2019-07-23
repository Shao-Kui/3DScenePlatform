function pausecomp(millis)
{
    var date = new Date();
    var curDate = null;
    do { curDate = new Date(); }
    while(curDate-date < millis);
}

class SceneRenderManager{
	constructor(parent_manager,canvas){
		this.parent_manager=parent_manager;
		this.canvas=canvas;
		this.objectInfoCache={};
		this.instanceKeyCache={};
		this.init_canvas();
		this.init_materials();
	}
	init_canvas(){
		var self=this;
		this.scene=new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera( 75, $(this.canvas).width()/$(this.canvas).height(), 0.01, 1000 );
		this.camera.userData={"type":"camera"};
		this.scene.add(this.camera);
		this.renderer = new THREE.WebGLRenderer({ canvas: this.canvas,alpha: true,antialias:4 });
		this.renderer.setClearColor( 0xffffff, 0 ); // second param is opacity, 0 => transparent
		this.on_resize();
		//this.renderer.render(this.scene,this.camera);
	}
	init_materials(){
		this.wallMaterial=new THREE.MeshBasicMaterial( {map: new THREE.TextureLoader().load('./texture//beam_8.jpg'), side:THREE.DoubleSide} );
		this.floorMaterial=new THREE.MeshBasicMaterial( {map: new THREE.TextureLoader().load('./texture//laminate_1_2.jpg'), side:THREE.DoubleSide} );
	}

	scene_remove(datafilter){
		var self=this;
		var instances_to_remove=[];
		this.scene.children.forEach(function(inst){
			if(inst.userData){
				var userData=inst.userData;
				if(datafilter(userData)){
					instances_to_remove.push(inst);
				}
			}
		});
		instances_to_remove.forEach(function(inst){
			self.scene.remove(inst);
		});
	}


	refresh_scene(scene_json,refresh_camera=false){
		this.scene_json=scene_json;
		this.floorz=this.scene_json.bbox[0][2];
		this.ceilz=this.scene_json.bbox[1][2];
		this.refresh_light();
		this.refresh_wall_and_floor();
		this.refresh_instances();
		if(refresh_camera){
			this.refresh_camera();
		}
		//this.renderer.render(this.scene,this.camera);
	}

	refresh_light(){
		this.scene_remove((userData)=>(userData.type=="light"));
		var ambientlight=new THREE.AmbientLight( 0xFFFFFF );
		ambientlight.userData={"type":"light"}
		this.scene.add(ambientlight);
	}

	refresh_wall_and_floor(){
		var self=this;
		this.scene_remove((userData)=>(userData.type=="floor"||userData.type=="wall"));
		var geo=this.scene_json.geo;
		geo.forEach(function (g){
			for (var i=0;i<g.length;i++){
				var s=g[i];
				var t=g[(i+1)%(g.length)];
				var geometry = new THREE.PlaneGeometry( Math.pow(Math.pow(t[1]-s[1],2)+Math.pow(t[0]-s[0],2),0.5), self.ceilz-self.floorz, 32,32 );
				var mesh=new THREE.Mesh(geometry,self.wallMaterial);
				mesh.rotation.set(Math.PI*0.5,Math.atan2(s[1]-t[1],s[0]-t[0]),0,"XZY")
				mesh.position.set((s[0]+t[0])*0.5,(s[1]+t[1])*0.5,(self.ceilz-self.floorz)*0.5);
				mesh.userData={"type":"wall"}
				self.scene.add(mesh);
			}

			var sp=new THREE.Shape();
			for (var i=0;i<g.length;i++){
				var s=g[i];
				if(i==0) {
					sp.moveTo(s[0],s[1]);
				}else{
					sp.lineTo(s[0],s[1]);
				}
			}
      var geometry = new THREE.ShapeBufferGeometry( sp );
      var mesh=new THREE.Mesh(geometry,self.floorMaterial);
      mesh.userData={"type":"floor"}
      self.scene.add(mesh);

		});

	}

	refresh_instances(){
		//try to add unique id for each instanceof
		var self=this;
		var newkeycache={};

		this.scene_json.objects.forEach(function(inst){ //an obj is a instance
			if(!(inst.key)){
				inst.key=THREE.Math.generateUUID();
			}
			if(self.instanceKeyCache[inst.key]){
				var instance=self.instanceKeyCache[inst.key];
				instance.scale.set(inst.scale[0],inst.scale[1],inst.scale[2]);
				instance.rotation.set(-inst.rotate[0],-inst.rotate[1],-inst.rotate[2],"XZY");
				instance.position.set(inst.translate[0],inst.translate[1],inst.translate[2]);
				newkeycache[inst.key]=instance;
			}
			else{
				newkeycache[inst.key]=true; //to prevent incomplete model to be deleted by this.scene_remove
				if(!(self.objectInfoCache[inst.modelId])){
					fetch("/objmeta/"+inst.modelId).then(function(response) {
						return response.json();
					})
					.then(function(meta) {
						self.objectInfoCache[inst.modelId]=meta;
						self.load_instance(inst);
					});
				} else{
					self.load_instance(inst);
				}
			}
		});
		this.scene_remove((userData)=>(userData.type=="object" && !newkeycache[userData.key]));
		this.instanceKeyCache=newkeycache;
	}
	load_instance(inst){
		pausecomp(300);
		var self=this;
		var meta=this.objectInfoCache[inst.modelId];
		var objLoader = new THREE.OBJLoader2();
		objLoader.loadMtl( meta.mtl, null, function(materials){
			objLoader.setModelName( inst.modelId );
			objLoader.setMaterials( materials );
			objLoader.load( meta.mesh, function(event){
				var instance=event.detail.loaderRootNode;
				instance.scale.set(inst.scale[0],inst.scale[1],inst.scale[2]);
				instance.rotation.set(-inst.rotate[0],-inst.rotate[1],-inst.rotate[2],"XZY");
				instance.position.set(inst.translate[0],inst.translate[1],inst.translate[2]);
				instance.userData={"type":"object","key":inst.key};
				self.instanceKeyCache[inst.key]=instance;
				self.scene.add(instance);
				//self.renderer.render(self.scene,self.camera);
			}, null, null, null, false );
		});

	}
	refresh_camera(){
		var bbox=this.scene_json.bbox;
		this.camera.position.set((bbox[0][0]+bbox[1][0])*0.5,(bbox[0][1]+bbox[1][1])*0.5+0.3,(this.ceilz-this.floorz)*2+this.ceilz);
		this.camera.lookAt((bbox[0][0]+bbox[1][0])*0.5,(bbox[0][1]+bbox[1][1])*0.5,this.floorz);
	}



	on_resize(){
		this.canvas.width=$(this.canvas).width();
		this.canvas.height=$(this.canvas).height();
		this.camera.aspect = this.canvas.width / this.canvas.height;
		this.camera.updateProjectionMatrix();
		this.renderer.setSize( this.canvas.width, this.canvas.height );
	}
}
class SceneUIManager{
	constructor(uiDOM){
		this.uiDOM=uiDOM;
		this.renderManager=new SceneRenderManager(this,($(this.uiDOM).find("#scenecanvas"))[0])
		this.init_menu();
	}

	init_menu(){
		this.init_load_button();
	}

	init_load_button(){
		this.load_button=($(this.uiDOM).find("#load_button"))[0];
		this.load_dialog=($(this.uiDOM).find("#load_dialog"))[0];
		this.load_dialog_input=($(this.uiDOM).find("#load_dialog_input"))[0];
		this.load_dialog_button=($(this.uiDOM).find("#load_dialog_button"))[0];
		$(this.load_dialog).dialog({ autoOpen: false });
		$(this.load_button).click(this.load_button_click());
		$(this.load_dialog_button).click(this.load_dialog_button_click());
	}
	load_button_click(){ //use closure to pass self
		var self=this;
		return function(){
			$(self.load_dialog).dialog( "open" );
		};
	}
	load_dialog_button_click(){
		var self=this;
		return function(){
			var files = $(self.load_dialog_input)[0].files;
			if (files.length <= 0) {
				return;
			}
			var fr = new FileReader();
			fr.onload = function(e) {
				var result = JSON.parse(e.target.result);
				self.load_scene(result);
			}
			fr.readAsText(files.item(0));
			$(self.load_dialog).dialog( "close" );
		};
	}
	load_scene(json){
		this.renderManager.refresh_scene(json,true);
	}

}
