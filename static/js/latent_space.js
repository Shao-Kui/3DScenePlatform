var c1m, c2m, o1m, o2m, io1m, ic2m;
var to_latent_space = function () {
    if (latent_space_mode == false) {
        c1m = new THREE.Matrix4();
        o1m = new THREE.Matrix4();
        c2m = new THREE.Matrix4();
        o2m = new THREE.Matrix4();

        t1v = new THREE.Matrix4();


        c1m.copy(camera.matrix);
        o1m.copy(INTERSECT_OBJ.matrix);

        t1v.setPosition(manager.renderManager.controls.target);

        toggle_latent_space();

        objname = INTERSECT_OBJ.name;
        that_obj = scene.getObjectByName(objname);

        c2m.copy(camera.matrix);
        o2m.copy(that_obj.matrix);


        if (that_obj == null)
            console.log('no such object in latent space');
        else {
            io1m = new THREE.Matrix4();
            ic2m = new THREE.Matrix4();

            io1m.getInverse(o1m);
            ic2m.getInverse(c2m);


            ctm = new THREE.Matrix4();
            ttm = new THREE.Matrix4();

            ctm.multiply(c1m);
            ctm.multiply(io1m);
            ctm.multiply(o2m);
            ctm.multiply(ic2m);

            ttm.multiply(t1v);
            ttm.multiply(io1m);
            ttm.multiply(o2m);
            nt = new THREE.Vector3(0,0,0);
            nt.applyMatrix4(ttm);

            manager.renderManager.controls.target.set(nt.x,nt.y,nt.z);
            camera.applyMatrix(ctm);

            manager.renderManager.controls.update();
        }

    } else {
        toggle_latent_space();
    }
    // objname = INTERSECT_OBJ.name;
    // toggle_latent_space();
    // that_obj = scene.getObjectByName(objname);
    // camera.lookAt(that_obj.position);
    // manager.renderManager.controls.update();
};
var toggle_latent_space = function (to_mode = !latent_space_mode) {
    if (to_mode === latent_space_mode)
        return;
    if (manager)
        manager.renderManager.controls.enabled = false;
    if (latent_space_mode == false) {
        latent_space_mode = true;
        manager = ls_manager;
    } else {
        latent_space_mode = false;
        manager = sc_manager;
    }
    manager.renderManager.controls.enabled = true;
    renderer = manager.renderManager.renderer;
    camera = manager.renderManager.camera;
    scene = manager.renderManager.scene;
};
