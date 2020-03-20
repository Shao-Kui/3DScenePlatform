var gameLoop = function () {
    render_update();
    orth_view_port_update();
    keyboard_update();

    camera.updateMatrixWorld();
    manager.renderManager.orthcamera.updateMatrixWorld();
    raycaster.setFromCamera(mouse, camera);
    renderer.render(scene, camera);
    manager.renderManager.orthrenderer.render(scene, manager.renderManager.orthcamera);

    requestAnimationFrame(gameLoop);
};

var screen_to_ground = function (mx, my, ground_y = 0) {
    var vec = new THREE.Vector3();
    var pos = new THREE.Vector3();
    vec.set(mx, my, 0.5);
    vec.unproject(camera);
    vec.sub(camera.position).normalize();
    var distance = (ground_y - camera.position.y) / vec.y;
    pos.copy(camera.position).add(vec.multiplyScalar(distance));
    return pos;
};

var radial_move_method = function (mx, my) {
    //from https://stackoverflow.com/questions/13055214/mouse-canvas-x-y-to-three-js-world-x-y-z
    var vec = new THREE.Vector3();
    var pos = new THREE.Vector3();
    vec.set(mx, my, 0.5);
    vec.unproject(camera);
    vec.sub(camera.position).normalize();
    var distance = (INTERSECT_OBJ.position.y - camera.position.y) / vec.y;
    pos.copy(camera.position).add(vec.multiplyScalar(distance));
    return pos;
};

var find_object_json = function (obj) {
    var key = obj.userData.key;
    var room = manager.renderManager.scene_json.rooms[obj.userData.roomId];
    for (var i = 0; i < room.objList.length; i++) {
        if (!room.objList[i]) {
            continue;
        }
        if (room.objList[i].key === key) {
            return i;
        }
    }
    return null;
};

var synchronize_json_object = function (object) {
    var i = find_object_json(object);
    var inst = manager.renderManager.scene_json.rooms[object.userData.roomId].objList[i];
    inst.scale[0] = object.scale.x;
    inst.scale[1] = object.scale.y;
    inst.scale[2] = object.scale.z;
    inst.translate[0] = object.position.x;
    inst.translate[1] = object.position.y;
    inst.translate[2] = object.position.z;
    inst.rotate[0] = object.rotation.x;
    inst.rotate[1] = object.rotation.y;
    inst.rotate[2] = object.rotation.z;
    inst.orient = Math.atan2(Math.sin(object.rotation.y), Math.cos(object.rotation.x) * Math.cos(object.rotation.y));
};

var synchronize_roomId = function (object) {
    if (currentRoomId === object.userData.roomId || currentRoomId === undefined) {
        return;
    }
    var i = find_object_json(object);
    var obj_json = manager.renderManager.scene_json.rooms[object.userData.roomId].objList[i];
    obj_json.roomId = currentRoomId;
    manager.renderManager.scene_json.rooms[currentRoomId].objList.push(obj_json);
    delete manager.renderManager.scene_json.rooms[object.userData.roomId].objList[i];
    object.userData.roomId = currentRoomId;
}

var updateMousePosition = function () {
    mouse.x = ((event.clientX - $(scenecanvas).offset().left) / scenecanvas.clientWidth) * 2 - 1;
    mouse.y = -((event.clientY - $(scenecanvas).offset().top) / scenecanvas.clientHeight) * 2 + 1;
}

var clickCatalogItem = function (e) {
    if (!manager.renderManager.scene_json) {
        return;
    }
    //check if auto insert mode is on
    if (Auto_Insert_Mode) {
        mage_auto_insert(e);
        return;
    }
    On_ADD = true;
    scenecanvas.style.cursor = "crosshair";
    INSERT_OBJ = {
        "modelId": $(e.target).attr("objectName"),
        "coarseSemantic": $(e.target).attr("coarseSemantic"), 
        "translate": [
            0.0,
            0.0,
            0.0
        ],
        "scale": [
            1.0,
            1.0,
            1.0
        ],
        "rotate": [
            0.0,
            0.0,
            0.0
        ]
    };
}

var findGroundTranslation = function () {
    if (currentRoomId === undefined) {
        return;
    }
    var vec = new THREE.Vector3();
    var pos = new THREE.Vector3();
    vec.set(mouse.x, mouse.y, 0.5);
    vec.unproject(camera);
    vec.sub(camera.position).normalize();
    var distance =
        (manager.renderManager.scene_json.rooms[currentRoomId].bbox.min[1]
            - camera.position.y) / vec.y;
    pos.copy(camera.position).add(vec.multiplyScalar(distance));
    return pos;
}

var addCatalogItem = function () {
    var vec = new THREE.Vector3();
    var pos = new THREE.Vector3();
    vec.set(mouse.x, mouse.y, 0.5);
    vec.unproject(camera);
    vec.sub(camera.position).normalize();
    var distance =
        (manager.renderManager.scene_json.rooms[currentRoomId].bbox.min[1]
            - camera.position.y) / vec.y;
    pos.copy(camera.position).add(vec.multiplyScalar(distance));
    INSERT_OBJ.translate[0] = pos.x;
    INSERT_OBJ.translate[1] = pos.y;
    INSERT_OBJ.translate[2] = pos.z;
    INSERT_OBJ.roomId = currentRoomId;
    manager.renderManager.scene_json.rooms[currentRoomId].objList.push(INSERT_OBJ);
    manager.renderManager.refresh_instances();
}

var onClickObj = function (event) {

    scenecanvas.style.cursor = "auto";
    //Do raycasting, judge whether or not users choose a new object.
    camera.updateMatrixWorld();
    raycaster.setFromCamera(mouse, camera);
    var intersects = raycaster.intersectObjects(manager.renderManager.cwfCache, true);
    if (manager.renderManager.cwfCache.length > 0 && intersects.length > 0) {
        currentRoomId = intersects[0].object.parent.userData.roomId;
        console.log("Current Room ID: " + currentRoomId);
    } else {
        currentRoomId = undefined;
    }
    if (On_ADD) {
        On_ADD = false;
        if (currentRoomId != undefined) {
            addCatalogItem();
        }
    }
    if (On_MOVE) {
        On_MOVE = false;
        synchronize_json_object(INTERSECT_OBJ);
        synchronize_roomId(INTERSECT_OBJ);
        return;
    }
    if (On_LIFT) {
        On_LIFT = false;
        synchronize_json_object(INTERSECT_OBJ);
        return;
    }
    if (On_SCALE) {
        On_SCALE = false;
        synchronize_json_object(INTERSECT_OBJ);
    }
    if (On_ROTATE) {
        On_ROTATE = false;
        synchronize_json_object(INTERSECT_OBJ);
        return;

    }
    if (On_Magic_ADD) {
        On_Magic_ADD = false;
        if (!manager.renderManager.scene_json) {
            return;
        }
        if (currentRoomId != undefined) {
            mage_add_object();
        }
    }
    var instanceKeyCache = manager.renderManager.instanceKeyCache;
    instanceKeyCache = Object.values(instanceKeyCache);
    intersects = raycaster.intersectObjects(instanceKeyCache, true);
    if (instanceKeyCache.length > 0 && intersects.length > 0) {
        INTERSECT_OBJ = intersects[0].object.parent; //currentRoomId = INTERSECT_OBJ.userData.roomId;
        console.log(INTERSECT_OBJ);
        console.log(INTERSECT_OBJ.userData);
        menu.style.left = (event.clientX - 63) + "px";
        menu.style.top = (event.clientY - 63) + "px";
        if (!isToggle) {
            radial.toggle();
            isToggle = !isToggle;
        }
    } else {
        console.log("object not intersected! ");
        INTERSECT_OBJ = undefined; //currentRoomId = undefined;
        if (isToggle) {
            radial.toggle();
            isToggle = !isToggle;
        }
    }

    if (latent_space_mode == true && INTERSECT_OBJ) {
        manager.renderManager.add_latent_obj();
    }
    if (latent_space_mode == true) {
        manager.renderManager.refresh_latent();
    }

    if (Auto_Rec_Mode && manager.renderManager.scene_json && currentRoomId != undefined) {
        palette_recommendation();
    }
};

function onDocumentMouseMove(event) {
    event.preventDefault();
    if (On_ROTATE && INTERSECT_OBJ != null) {
        var rtt_pre = new THREE.Vector2();
        var rtt_nxt = new THREE.Vector2();
        rtt_pre.set(mouse.x, mouse.y);
        updateMousePosition();
        rtt_nxt.set(mouse.x, mouse.y);
        rtt_pre.sub(mouse.rotateBase);
        rtt_nxt.sub(mouse.rotateBase);
        INTERSECT_OBJ.rotateY(rtt_nxt.angle() - rtt_pre.angle());
    }
    if (On_MOVE && INTERSECT_OBJ != null) {
        var last_pos = radial_move_method(mouse.x, mouse.y);
        updateMousePosition();
        var pos = radial_move_method(mouse.x, mouse.y);
        pos.sub(last_pos);
        INTERSECT_OBJ.position.set(
            INTERSECT_OBJ.position.x + pos.x,
            INTERSECT_OBJ.position.y + pos.y,
            INTERSECT_OBJ.position.z + pos.z);
    }
    if (On_LIFT && INTERSECT_OBJ != null) {
        var last_y = mouse.y;
        updateMousePosition();
        var this_y = mouse.y;
        INTERSECT_OBJ.position.set(
            INTERSECT_OBJ.position.x,
            INTERSECT_OBJ.position.y + 2 * (this_y - last_y),
            INTERSECT_OBJ.position.z);
    }
    if (On_SCALE && INTERSECT_OBJ != null){
        var last_x = mouse.x;
        updateMousePosition();
        var this_x = mouse.x;
        s = 0.3;
        INTERSECT_OBJ.scale.set(
            INTERSECT_OBJ.scale.x + s * (this_x - last_x),
            INTERSECT_OBJ.scale.y + s * (this_x - last_x),
            INTERSECT_OBJ.scale.z + s * (this_x - last_x));
    }
    updateMousePosition();
};

var onWindowResize = function() { //改用画布的height width
    camera.aspect = scenecanvas.clientWidth / scenecanvas.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(scenecanvas.clientWidth, scenecanvas.clientHeight);
}

var reshuffleRoom = function () {
    if (currentRoomId === undefined) {
        console.log("No room is specified. ");
        return
    }
    $.ajax({
        type: "POST",
        contentType: "application/json; charset=utf-8",
        url: "/reshuffle",
        data: JSON.stringify(manager.renderManager.scene_json.rooms[currentRoomId]),
        success: function (data) {
            data = JSON.parse(data);
            temp = data;
            manager.renderManager.scene_json.rooms[currentRoomId].objList = data.objList;
            manager.renderManager.refresh_instances();
        }
    });
};

var temp;
var setting_up = function () {
    clear_panel();  // clear panel first before use individual functions.
    setUpCanvasDrawing();
    render_initialization();
    orth_initialization();
    searchPanelInitialization();
    radial_initialization();
    
    $("#sklayout").click(auto_layout);
    $("#layout_button").click(auto_layout);
    $("#reshuffle").click(reshuffleRoom);
    $("#mage_button").click(mage_add_control);
    $("#autoinsert_button").click(auto_insert_control);
    $("#download_button").click(function(){
        let json_to_dl = JSON.parse(JSON.stringify(manager.renderManager.scene_json));
        // delete unnecessary keys; 
        json_to_dl.rooms.forEach(function(room){
            room.objList.forEach(function(inst){
                if(inst === null || inst === undefined){
                    return
                }
                delete inst.key;
            })
        })
        var dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(json_to_dl));
        var dlAnchorElem = document.getElementById('downloadAnchorElem');
        dlAnchorElem.setAttribute("href",     dataStr     );
        dlAnchorElem.setAttribute("download", `${json_to_dl.origin}-l${json_to_dl.id}-dl.json`);
        dlAnchorElem.click();
    });

    scenecanvas.addEventListener('mousemove', onDocumentMouseMove, false);
    window.addEventListener('resize', onWindowResize, false);
    scenecanvas.addEventListener('click', onClickObj);
    document.addEventListener('keydown', onKeyDown, false);
    document.addEventListener('keyup', onKeyUp, false);
    orthcanvas.addEventListener('mousedown', orth_mousedown);
    orthcanvas.addEventListener('mouseup', orth_mouseup);
    orthcanvas.addEventListener('mousemove', orth_mousemove);
    orthcanvas.addEventListener('click', orth_mouseclick);

    gameLoop();
};
