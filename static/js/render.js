

var render_initialization = function () {
    var axis = new THREE.AxesHelper(1000);
    scene.add(axis);

    directionalLight = new THREE.DirectionalLight(0xFFFFFF, 0.3);
    directionalLight.castShadow = true;
    directionalLight.position.y = 0.5;
    scene.add(directionalLight);

    var ambientLight = new THREE.AmbientLight(0xFFFFFF, 0.9);
    scene.add(ambientLight);

    //adding skybox
    var tgaLoader = new THREE.TGALoader();
    var skyGeo = new THREE.CubeGeometry(1000, 1000, 1000);
    var skyMaterials = [
        new THREE.MeshBasicMaterial({map: tgaLoader.load("/static/skybox/mp_impaler/impaler-point_ft.tga"), side: THREE.DoubleSide}),
        new THREE.MeshBasicMaterial({map: tgaLoader.load("/static/skybox/mp_impaler/impaler-point_bk.tga"), side: THREE.DoubleSide}),
        new THREE.MeshBasicMaterial({map: tgaLoader.load("/static/skybox/mp_impaler/impaler-point_up.tga"), side: THREE.DoubleSide}),
        new THREE.MeshBasicMaterial({map: tgaLoader.load("/static/skybox/mp_impaler/impaler-point_dn.tga"), side: THREE.DoubleSide}),
        new THREE.MeshBasicMaterial({map: tgaLoader.load("/static/skybox/mp_impaler/impaler-point_rt.tga"), side: THREE.DoubleSide}),
        new THREE.MeshBasicMaterial({map: tgaLoader.load("/static/skybox/mp_impaler/impaler-point_lf.tga"), side: THREE.DoubleSide})
    ];
    var sky = new THREE.Mesh(skyGeo, skyMaterials);
    scene.add(sky);
};


var render_update = function () {
    var time = Date.now() * 0.0001;
    //directionalLight.position.x = Math.sin(time);
    //directionalLight.position.z = Math.cos(time);

};

