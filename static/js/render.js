var tgaLoader = new THREE.TGALoader();
var skyMaterialsCloudtop = [
    // new THREE.MeshBasicMaterial({map: tgaLoader.load("/static/skybox/mp_impaler/impaler-point_ft.tga"), side: THREE.DoubleSide}),
    // new THREE.MeshBasicMaterial({map: tgaLoader.load("/static/skybox/mp_impaler/impaler-point_bk.tga"), side: THREE.DoubleSide}),
    // new THREE.MeshBasicMaterial({map: tgaLoader.load("/static/skybox/mp_impaler/impaler-point_up.tga"), side: THREE.DoubleSide}),
    // new THREE.MeshBasicMaterial({map: tgaLoader.load("/static/skybox/mp_impaler/impaler-point_dn.tga"), side: THREE.DoubleSide}),
    // new THREE.MeshBasicMaterial({map: tgaLoader.load("/static/skybox/mp_impaler/impaler-point_rt.tga"), side: THREE.DoubleSide}),
    // new THREE.MeshBasicMaterial({map: tgaLoader.load("/static/skybox/mp_impaler/impaler-point_lf.tga"), side: THREE.DoubleSide})

    // new THREE.MeshBasicMaterial({map: tgaLoader.load("/static/skybox/ame_fade/fadeaway_ft.tga"), side: THREE.DoubleSide}),
    // new THREE.MeshBasicMaterial({map: tgaLoader.load("/static/skybox/ame_fade/fadeaway_bk.tga"), side: THREE.DoubleSide}),
    // new THREE.MeshBasicMaterial({map: tgaLoader.load("/static/skybox/ame_fade/fadeaway_up.tga"), side: THREE.DoubleSide}),
    // new THREE.MeshBasicMaterial({map: tgaLoader.load("/static/skybox/ame_fade/fadeaway_dn.tga"), side: THREE.DoubleSide}),
    // new THREE.MeshBasicMaterial({map: tgaLoader.load("/static/skybox/ame_fade/fadeaway_rt.tga"), side: THREE.DoubleSide}),
    // new THREE.MeshBasicMaterial({map: tgaLoader.load("/static/skybox/ame_fade/fadeaway_lf.tga"), side: THREE.DoubleSide})

    new THREE.MeshBasicMaterial({map: tgaLoader.load("/static/skybox/ely_cloudtop/cloudtop_ft.tga"), side: THREE.DoubleSide}),
    new THREE.MeshBasicMaterial({map: tgaLoader.load("/static/skybox/ely_cloudtop/cloudtop_bk.tga"), side: THREE.DoubleSide}),
    new THREE.MeshBasicMaterial({map: tgaLoader.load("/static/skybox/ely_cloudtop/cloudtop_up.tga"), side: THREE.DoubleSide}),
    new THREE.MeshBasicMaterial({map: tgaLoader.load("/static/skybox/ely_cloudtop/cloudtop_dn.tga"), side: THREE.DoubleSide}),
    new THREE.MeshBasicMaterial({map: tgaLoader.load("/static/skybox/ely_cloudtop/cloudtop_rt.tga"), side: THREE.DoubleSide}),
    new THREE.MeshBasicMaterial({map: tgaLoader.load("/static/skybox/ely_cloudtop/cloudtop_lf.tga"), side: THREE.DoubleSide})
];

var spotLight = new THREE.SpotLight( 0xffffff, 0.4);

var render_initialization = function () {
    var axis = new THREE.AxesHelper(1000);
    scene.add(axis);

    //enabling shadow casting
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;

    //lighting and shadowing
    //0.9 is the stable lightness of ambient light after mid-term; 
    var ambientLight = new THREE.AmbientLight(0xFFFFFF, 0.9);
    scene.add(ambientLight);

    //0.3 is the stable lightness of directional light after mid-term; 
    var directionalLight = new THREE.DirectionalLight(0xFFFFFF, 0.3);
    directionalLight.castShadow = false;
    directionalLight.position.set(0, 10, 0);
    directionalLight.shadow.mapSize.width = 4096 * 4;
    directionalLight.shadow.mapSize.height = 4096 * 4;
    directionalLight.shadow.camera.near = 0.01;
    directionalLight.shadow.camera.far = 100;
    directionalLight.shadow.camera.left = -100;
    directionalLight.shadow.camera.right = 100;
    directionalLight.shadow.camera.top = 100;
    directionalLight.shadow.camera.bottom = -100;
    scene.add(directionalLight);
    scene.add(directionalLight.target)

    //Create a PointLight and turn on shadows for the light
    spotLight.angle = Math.PI / 4;
    spotLight.penumbra = 0;
    spotLight.decay = 0;
    spotLight.distance = 0;
    spotLight.castShadow = true;
    spotLight.shadow.mapSize.width = 4096;
    spotLight.shadow.mapSize.height = 4096;
    spotLight.shadow.camera.near = 0.01;
    spotLight.shadow.camera.far = 1000;
    // scene.add( spotLight );
    // scene.add( spotLight.target );

    //adding skybox
    var skyGeo = new THREE.CubeGeometry(1000, 1000, 1000);
    var skyMaterials = skyMaterialsCloudtop;
    skyBox = new THREE.Mesh(skyGeo, skyMaterials);
    scene.add(skyBox);
};


var render_update = function () {
    var time = Date.now() * 0.00001;
    spotLight.position.x = lx_level + Math.sin(time) * 12;
    spotLight.position.z = lz_level + Math.cos(time) * 12;
    skyBox.rotation.y = (time % (Math.PI * 2)) + Math.PI / 2;
};

