var render_initialization = function (scene) {
    scene.add(new THREE.AxesHelper(1000));

    directionalLight = new THREE.DirectionalLight(0xFFFFFF, 0.3);
    directionalLight.castShadow = true;
    directionalLight.position.y = 0.5;

    scene.add(directionalLight);


    if (latent_space_mode == false)
        scene.add(new THREE.AmbientLight(0xFFFFFF, 0.9));
    else
        scene.add(new THREE.AmbientLight(0xaaaaaa, 0.9));
};

var render_update = function () {
    var time = Date.now() * 0.0001;
    //directionalLight.position.x = Math.sin(time);
    //directionalLight.position.z = Math.cos(time);
};
