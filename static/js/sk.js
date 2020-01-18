var gameLoop = function () {
    render_update();
    orth_view_port_update();
    keyboard_update();
    requestAnimationFrame(gameLoop);
    camera.updateMatrixWorld();
    manager.renderManager.orthcamera.updateMatrixWorld();
    raycaster.setFromCamera(mouse, camera);
    renderer.render(scene, camera);
    manager.renderManager.orthrenderer.render(scene, manager.renderManager.orthcamera);
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

var clickSketchSearchButton = function () {
    while (catalogItems.firstChild) {
        catalogItems.firstChild.remove();
    }

    var dataURL = drawingCanvas.toDataURL();
    dataURL = dataURL.split(',')[1]
    $.ajax({
        type: "POST",
        url: "/sketch",
        data: {
            imgBase64: dataURL
        }
    }).done(function (o) {
        searchResults = JSON.parse(o);
        searchResults.forEach(function (item) {
            var iDiv = document.createElement('div');
            iDiv.className = "catalogItem";
            iDiv.style.backgroundImage = "url(" + item.thumbnail + ")";
            iDiv.setAttribute('objectID', item.id);
            iDiv.setAttribute('objectName', item.name);
            iDiv.setAttribute('semantic', item.semantic);
            iDiv.addEventListener('click', clickCatalogItem)
            catalogItems.appendChild(iDiv);
        })
    });
};

var clickTextSearchButton = function () {
    while (catalogItems.firstChild) {
        catalogItems.firstChild.remove();
    }

    var search_url = "/query?kw=" + document.getElementById("searchinput").value;
    $.getJSON(search_url, function (data) {
        searchResults = data;
        searchResults.forEach(function (item) {
            var iDiv = document.createElement('div');
            iDiv.className = "catalogItem";
            iDiv.style.backgroundImage = "url(" + item.thumbnail + ")";
            iDiv.setAttribute('objectID', item.id);
            iDiv.setAttribute('objectName', item.name);
            iDiv.setAttribute('semantic', item.semantic);
            iDiv.addEventListener('click', clickCatalogItem)
            catalogItems.appendChild(iDiv);
        })
    });
};

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
    updateMousePosition();
};
var temp;
var clear_panel = function () {
    Auto_Rec_Mode = false;
    document.getElementById("rec_container").style.display = "none";
    document.getElementById("record_panel").style.display = "none";
    document.getElementById("searchinput").style.display = "none";
    document.getElementById("searchbtn").style.display = "none";
    document.getElementById("drawing-canvas").style.display = "none";
    document.getElementById("sketchsearchdiv").style.display = "none";
    document.getElementById("sketchsearchbtn").style.display = "none";
    document.getElementById("rec_button").style.backgroundColor = '#007bff';
};
var setting_up = function () {
    clear_panel();  // clear panel first before use individual functions.
    setUpCanvasDrawing();
    render_initialization();
    orth_initialization();
    $("#searchbtn").click(clickTextSearchButton);
    $("#sketchsearchbtn").click(clickSketchSearchButton);
    $("#sketchclearbtn").click(clearCanvas);
    $("#rec_button").click(function () {
        clear_panel();
        Auto_Rec_Mode = true;
        document.getElementById("rec_container").style.display = "block";
        document.getElementById("rec_button").style.backgroundColor = '#9400D3';
    });
    $("#colla_button").click(function () {
        clear_panel();
        document.getElementById("drawing-canvas").style.display = "block";
        document.getElementById("record_panel").style.display = "block";
        document.getElementById("sketchsearchdiv").style.display = "flex";
    });
    $("#text_button").click(function () {
        clear_panel();
        document.getElementById("searchinput").style.display = "inline-block";
        document.getElementById("searchbtn").style.display = "inline-block";
    });
    $("#sketch_button").click(function () {
        clear_panel();
        document.getElementById("drawing-canvas").style.display = "block";
        document.getElementById("sketchsearchdiv").style.display = "flex";
        document.getElementById("sketchsearchbtn").style.display = "block";
    });
    $("#sklayout").click(function () {
        if (currentRoomId === undefined) {
            console.log("No room is specified. ");
            return
        }
        $.ajax({
            type: "POST",
            contentType: "application/json; charset=utf-8",
            url: "/sklayout",
            data: JSON.stringify(manager.renderManager.scene_json.rooms[currentRoomId]),
            success: function (data) {
                data = JSON.parse(data);
                temp = data;
                manager.renderManager.scene_json.rooms[currentRoomId].objList = data.objList;
                manager.renderManager.refresh_instances();
            }
        });
    });
    $("#reshuffle").click(function () {
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
    });

    function onWindowResize() { //改用画布的height width
        camera.aspect = scenecanvas.clientWidth / scenecanvas.clientHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(scenecanvas.clientWidth, scenecanvas.clientHeight);
    }

    r = document.getElementsByClassName('radial__container')[0];
    r.style.width = "0px";
    r.style.height = "0px";
    scenecanvas.addEventListener('mousemove', onDocumentMouseMove, false);
    window.addEventListener('resize', onWindowResize, false);
    scenecanvas.addEventListener('click', onClickObj);
    document.addEventListener('keydown', onKeyDown, false);
    document.addEventListener('keyup', onKeyUp, false);
    orthcanvas.addEventListener('mousedown', orth_mousedown);
    orthcanvas.addEventListener('mouseup', orth_mouseup);
    orthcanvas.addEventListener('mousemove', orth_mousemove);
    orthcanvas.addEventListener('click', orth_mouseclick);

    var mage_button = document.getElementById("mage_button");
    mage_button.addEventListener('click', mage_add_control);

    var layout_button = document.getElementById("layout_button");
    layout_button.addEventListener('click', auto_layout);

    var autoinsert_button = document.getElementById("autoinsert_button");
    autoinsert_button.addEventListener('click', auto_insert_control);

    //Config radial logic
    var radial_move_button = document.getElementsByClassName("glyphicon-move")[0];
    radial_move_button.addEventListener('click', radial_move_control);

    var radial_rotate_button = document.getElementsByClassName("glyphicon-repeat")[0];
    radial_rotate_button.addEventListener('click', radial_rotate_control);

    var radial_remove_button = document.getElementsByClassName("glyphicon-remove")[0];
    radial_remove_button.addEventListener('click', radial_remove_control);

    // a stub for Wei-Yu
    var radial_latentspace_button = document.getElementsByClassName("glyphicon-star")[0];
    radial_latentspace_button.addEventListener('click', manager.renderManager.latent_space_click);

    gameLoop();
};
