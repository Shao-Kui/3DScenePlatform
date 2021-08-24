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

var spotLight = new THREE.SpotLight( 0xffffff, 6);
var directionalLight = new THREE.DirectionalLight(0xFFFFFF, 9.3);

var render_initialization = function () {
    //enabling shadow casting
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;

    //lighting and shadowing
    //0.9 is the stable lightness of ambient light after mid-term; 
    var ambientLight = new THREE.AmbientLight(0xFFFFFF, 1.6);
    scene.add(ambientLight);

    //0.3 is the stable lightness of directional light after mid-term; 
    directionalLight.castShadow = true;
    directionalLight.position.set(0, 10, 0);
    directionalLight.shadow.mapSize.width = 4096;
    directionalLight.shadow.mapSize.height = 4096;
    directionalLight.shadow.camera.near = 0.01;
    directionalLight.shadow.camera.far = 100;
    directionalLight.shadow.camera.left = -100;
    directionalLight.shadow.camera.right = 100;
    directionalLight.shadow.camera.top = 100;
    directionalLight.shadow.camera.bottom = -100;
    scene.add(directionalLight);
    scene.add(directionalLight.target)

    //Create a PointLight and turn on shadows for the light
    spotLight.angle = Math.PI / 3;
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

    // add HemisphereLight
    let hlight = new THREE.HemisphereLight( 0xffffff, 0xffffff, 2.4 );
    scene.add( hlight );

    //adding skybox
    var skyGeo = new THREE.BoxGeometry(1000, 1000, 1000);
    var skyMaterials = skyMaterialsCloudtop;
    skyBox = new THREE.Mesh(skyGeo, skyMaterials);
    scene.add(skyBox);

    // Effect Composer
    // postprocessing
    composer = new THREE.EffectComposer(renderer);
    renderPass = new THREE.RenderPass(scene, camera);
    composer.addPass(renderPass);
    outlinePass = new THREE.OutlinePass(new THREE.Vector2(window.innerWidth, window.innerHeight ), scene, camera );
    outlinePass.edgeStrength = 6;
    outlinePass.edgeGlow = 0.1;
    outlinePass.edgeThickness = 1;
    outlinePass.pulsePeriod = 5;
    outlinePass.visibleEdgeColor.set("#2f8713");
    outlinePass.hiddenEdgeColor.set("#ffffff");
    composer.addPass(outlinePass);
    outlinePass2 = new THREE.OutlinePass(new THREE.Vector2(window.innerWidth, window.innerHeight ), scene, camera );
    outlinePass2.edgeStrength = 6;
    outlinePass2.edgeGlow = 0.1;
    outlinePass2.edgeThickness = 1;
    outlinePass2.pulsePeriod = 5;
    outlinePass2.visibleEdgeColor.set("#3f3395");
    outlinePass2.hiddenEdgeColor.set("#000000");
    composer.addPass(outlinePass2);
};


var render_update = function () {
    //renderTime = Date.now() * 0.00001;
    spotLight.position.x = lx_level + Math.sin(renderTime) * 12;
    spotLight.position.z = lz_level + Math.cos(renderTime) * 12;
    //directionalLight.position.x = Math.sin(renderTime);
    //directionalLight.position.z = Math.cos(renderTime);
    skyBox.rotation.y = (renderTime % (Math.PI * 2)) + Math.PI / 2;
};

