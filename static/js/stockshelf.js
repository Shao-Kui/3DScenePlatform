let shelfPlaceholderHandler = () => {
    let shelfKey = INTERSECT_OBJ.userData.shelfKey;
    let shelf = manager.renderManager.instanceKeyCache[shelfKey];
    if (onlineGroup !== 'OFFLINE' && shelf.userData.controlledByID !== undefined && shelf.userData.controlledByID !== onlineUser.id) {
        console.log(`This shelf is already claimed by ${shelf.userData.controlledByID}`);
        INTERSECT_OBJ = undefined;
        return;
    }
    if (shelfKey in INTERSECT_SHELF_PLACEHOLDERS) {
        if (INTERSECT_SHELF_PLACEHOLDERS[shelfKey].has(INTERSECT_OBJ.name)) {
            // cancel
            INTERSECT_SHELF_PLACEHOLDERS[shelfKey].delete(INTERSECT_OBJ.name);
            let index = outlinePass2.selectedObjects.indexOf(INTERSECT_OBJ);
            if(index > -1){
                outlinePass2.selectedObjects.splice(index, 1);
            }
            if (INTERSECT_SHELF_PLACEHOLDERS[shelfKey].size === 0) {
                claimControlObject3D(shelfKey, true);
                delete INTERSECT_SHELF_PLACEHOLDERS[shelfKey];
            }
        } else {
            INTERSECT_SHELF_PLACEHOLDERS[shelfKey].add(INTERSECT_OBJ.name);
            outlinePass2.selectedObjects.push(INTERSECT_OBJ);
        }
    } else {
        INTERSECT_SHELF_PLACEHOLDERS[shelfKey] = new Set([INTERSECT_OBJ.name]);
        claimControlObject3D(shelfKey, false);
        outlinePass2.selectedObjects.push(INTERSECT_OBJ);
    }
    if (Object.keys(INTERSECT_SHELF_PLACEHOLDERS).length == 0) {
        $("#catalogItems").empty();
        return;
    }

    let roomId = shelf.userData.roomId;
    $('#tab_modelid').text(INTERSECT_OBJ.name);
    $('#tab_category').text('shelf-placeholder');
    $('#tab_roomid').text(roomId);
    $('#tab_roomtype').text(manager.renderManager.scene_json.rooms[roomId].roomTypes);
    lookAtShelves(Object.keys(INTERSECT_SHELF_PLACEHOLDERS));
    recommendCommodities(roomId);
}

let cancelClickingShelfPlaceholders = () => {
    outlinePass2.selectedObjects = outlinePass2.selectedObjects.filter(obj => !obj.name.startsWith('shelf-placeholder-'));
    for (const shelfKey in INTERSECT_SHELF_PLACEHOLDERS) {
        claimControlObject3D(shelfKey, true);
    }
    INTERSECT_SHELF_PLACEHOLDERS = {};
    $("#catalogItems").empty();
}

let enterShelfStockingMode = () => {
    cancelClickingObject3D();
    for (let key in manager.renderManager.instanceKeyCache) {
        let inst = manager.renderManager.instanceKeyCache[key];
        if (inst.userData.json.modelId === 'shelf01') {
            addShelfPlaceholders(inst);
        }
    }
    computePlaceholdersVisbility();
    if ($("#sidebarSelect").val() !== "shelfInfoDiv") {
        $("#sidebarSelect").val("shelfInfoDiv").change();
    }
    $('#nextShelfBtn').removeAttr('disabled');
    startShelfPlannerExperiment();
}

let getCube = (width, height, depth, opacity, color = "#ffffff") => {
    const geometry = new THREE.BoxGeometry(width, height, depth);
    const material = new THREE.MeshBasicMaterial();
    material.transparent = true;
    material.opacity = opacity;
    const cube = new THREE.Mesh(geometry, material);
    cube.material.color.setStyle( color );
    cube.material.toneMapped = false;
    return cube;
}

const shelfOffsetY = [1.565, 1.116, 0.666, 0.200];

let addShelfPlaceholders = (shelf) => {
    if (shelf.userData.json.commodities == undefined) {
        shelf.userData.json.commodities = [
            [{ modelId: '', uuid: '' }],
            [{ modelId: '', uuid: '' }],
            [{ modelId: '', uuid: '' }],
            [{ modelId: '', uuid: '' }]
        ];
    }
    for (let r = 0; r < 4; ++r) {
        addShelfPlaceholdersByRow(shelf.userData.key, r, shelf.userData.json.commodities[r].length);
    }
}

let exitShelfStockingMode = () => {
    cancelClickingShelfPlaceholders();
    for (let key in manager.renderManager.instanceKeyCache) {
        if (key.startsWith('shelf-placeholder-')) {
            scene.remove(manager.renderManager.instanceKeyCache[key]);
            delete manager.renderManager.instanceKeyCache[key];
        }
    }
    clearShelfInfo();
    $('#nextShelfBtn').attr("disabled", "true");
}

let isShelfPlaceholder = function(obj) {
    return obj.name !== undefined && obj.name.startsWith('shelf-placeholder-');
}

let getNewUUID = () => {
    let uuid;
    loadMoreServerUUIDs(1);
    if(!uuid) uuid = serverUUIDs.pop(); 
    if(!uuid) uuid = THREE.MathUtils.generateUUID();
    commandStack.push({
        'funcName': 'removeObjectByUUID',
        'args': [uuid, true]
    });
    return uuid;
}

let addCommodityToShelf = function (shelfKey, modelId, r, c, l, order) {
    let shelf = manager.renderManager.instanceKeyCache[shelfKey];
    let commodities = shelf.userData.json.commodities;
    let roomId = shelf.userData.roomId;

    let instancedTransforms = [];
    let bbox = objectCache[modelId].boundingBox;
    let commodityWidth = bbox.max.z - bbox.min.z; // rotate 90 degrees
    let commodityHeight = bbox.max.y - bbox.min.y;
    let commodityDepth = bbox.max.x - bbox.min.x; // rotate 90 degrees
    let phWidth = 1.2 * shelf.scale.x / l;
    let phHeight = 0.4 * shelf.scale.y;
    let phDepth = 0.45 * shelf.scale.z;
    let nx = Math.max(1, Math.floor(phWidth / commodityWidth));
    let ny = Math.max(1, Math.floor(phHeight / commodityHeight)); // optional
    let nz = Math.max(1, Math.floor(phDepth / commodityDepth));
    for (let i = 0; i < nx; ++i) {
        let offsetX = phWidth * i / nx + phWidth / nx / 2 - phWidth / 2;
        for (let j = 0; j < nz; ++j) {
            let offsetZ = phDepth * j / nz - 0.25 * shelf.scale.z + commodityDepth / 2;
            for (let k = 0; k < ny; ++k) {
                let offsetY = k * commodityHeight;
                instancedTransforms.push({
                    'translate': [offsetX, offsetY, offsetZ],
                    'rotate': [0, Math.PI / 2, 0], // rotate 90 degrees
                    'scale': [1.0, 1.0, 1.0]
                });
            }
        }
    }

    let uuid = getNewUUID();
    let offset = new THREE.Vector3(((0.6 / l) * (2 * c + 1) - 0.6) * shelf.scale.x, shelfOffsetY[r] * shelf.scale.y, 0);
    let axis = new THREE.Vector3(0, 1, 0);
    offset.applyAxisAngle(axis, shelf.rotation.y);
    let transform = {
        'translate': [shelf.position.x + offset.x, shelf.position.y + offset.y, shelf.position.z + offset.z],
        'rotate': [shelf.rotation.x, shelf.rotation.y, shelf.rotation.z],
        'scale': [1.0, 1.0, 1.0],
        'format': 'THInstancedObject'
    };
    let timestamp = Date.now();
    const date = new Date();
    let addWhen = date.toLocaleString();
    let otherInfo = {
        'instancedTransforms': instancedTransforms,
        'shelfKey': shelfKey,
        'shelfRow': r,
        'shelfCol': c,
        'order': order,
        'addBy': onlineGroup, 
        'addWhen': addWhen,
        'timestamp': timestamp
    };
    let object3d = addObjectByUUID(uuid, modelId, roomId, transform, otherInfo);
    object3d.name = uuid;
    emitFunctionCall('addObjectByUUID', [uuid, modelId, roomId, transform, otherInfo]);

    commodities[r][c] = { modelId: modelId, uuid: uuid, order: order, addBy: onlineGroup, addWhen: addWhen, timestamp: timestamp };
    let objectProperties = {};
    objectProperties[shelfKey] = { commodities: commodities };
    emitFunctionCall('updateObjectProperties', [objectProperties]);
}

let yulin = function (shelfKey, newCommodities) {
    for (let r = 0; r < 4; ++r) {
        changeShelfRow(shelfKey, r, newCommodities[r]);
    }
}

let clearDanglingCommodities = () => {
    for (let key in manager.renderManager.instanceKeyCache) {
        let inst = manager.renderManager.instanceKeyCache[key];
        if (inst.userData.modelId && inst.userData.modelId.startsWith('yulin-')) {
            let r = inst.userData.json.shelfRow;
            let c = inst.userData.json.shelfCol;
            let shelfKey = inst.userData.json.shelfKey;
            if (shelfKey in manager.renderManager.instanceKeyCache) {
                let commodities = manager.renderManager.instanceKeyCache[shelfKey].userData.json.commodities;
                if (commodities[r][c].uuid !== key) {
                    removeObjectByUUID(key);
                }
            } else {
                // the shelf is gone
                removeObjectByUUID(key);
            }
        } else if (inst.userData.modelId === 'shelf01') {
            let commodities = inst.userData.json.commodities;
            for (let r = 0; r < 4; ++r) {
                let l = commodities[r].length;
                for (let c = 0; c < l; ++c) {
                    if (!(commodities[r][c].uuid in manager.renderManager.instanceKeyCache)) {
                        commodities[r][c] = { modelId: '', uuid: '' };
                    }
                }
            }
        }
    }
}

let addShelfPlaceholdersByRow = function (shelfKey, r, l) {
    let shelf = manager.renderManager.instanceKeyCache[shelfKey];
    let offsetY = shelfOffsetY[r] + 0.2;
    for (let c = 0; c < l; ++c) {
        let placeholder = getCube(1.2 / l, 0.4, 0.45, 0.2);
        let phKey = `shelf-placeholder-${shelfKey}-${r}-${c}`;
        placeholder.name = phKey;
        let offsetX = (0.6 / l) * (2 * c + 1) - 0.6;
        let offset = new THREE.Vector3(offsetX * shelf.scale.x, offsetY * shelf.scale.y, -0.025 * shelf.scale.z);
        let axis = new THREE.Vector3(0, 1, 0);
        offset.applyAxisAngle(axis, shelf.rotation.y);
        placeholder.position.copy(shelf.position);
        placeholder.position.add(offset);
        placeholder.rotation.copy(shelf.rotation);
        placeholder.scale.copy(shelf.scale);
        placeholder.userData.shelfKey = shelfKey;
        placeholder.userData.shelfRow = r;
        placeholder.userData.shelfCol = c;
        placeholder.userData.type = 'object';
        scene.add(placeholder);
        manager.renderManager.instanceKeyCache[phKey] = placeholder;
    }
}

// newRow = [{modelId: 'yulin-xxx'}, {modelId: ''}, ...]
let changeShelfRow = function (shelfKey, r, newRow) {
    let shelf = manager.renderManager.instanceKeyCache[shelfKey];
    let oldRow = shelf.userData.json.commodities[r];
    if (oldRow !== undefined) {
        for (let c = 0; c < oldRow.length; ++c) {
            if (newRow.length === oldRow.length && newRow[c].modelId === oldRow[c].modelId) {
                // same commodity
                newRow[c].uuid = oldRow[c].uuid;
            } else {
                if (oldRow[c].uuid !== "") {
                    removeObjectByUUID(oldRow[c].uuid)
                }
            }
        }
    }
    if (newRow.length !== oldRow.length) {
        for (let c = 0; c < oldRow.length; ++c) {
            let phKey = `shelf-placeholder-${shelfKey}-${r}-${c}`;
            scene.remove(manager.renderManager.instanceKeyCache[phKey]);
            delete manager.renderManager.instanceKeyCache[phKey];
        }
        addShelfPlaceholdersByRow(shelfKey, r, newRow.length);
    }
    shelf.userData.json.commodities[r] = newRow;
    let l = newRow.length;
    for (let c = 0; c < l; ++c) {
        let modelId = newRow[c].modelId;
        if (modelId === "") {
            continue;
        }
        if (newRow.length === oldRow.length && newRow[c].uuid) {
            continue;
        } else {
            addCommodityToShelf(shelfKey, modelId, r, c, l);
        }
    }
}

let setIntersectShelf = () => {
    if (shelfstocking_Mode) cancelClickingShelfPlaceholders();
    if (INTERSECT_OBJ.userData.json.commodities === undefined) {
        addShelfPlaceholders(INTERSECT_OBJ);
    }
    let shelfKey = INTERSECT_OBJ.userData.key;
    claimControlObject3D(shelfKey, false);
    $("#shelfKey").text(shelfKey);
    INTERSECT_SHELF_PLACEHOLDERS[shelfKey] = new Set();
    recommendShelfType(INTERSECT_OBJ.userData.roomId, [shelfKey]);
    let commodities = INTERSECT_OBJ.userData.json.commodities;
    for (let r = 0; r < 4; ++r) {
        let l = commodities[r].length;
        $(`#shelfRow${r}`).val(l);
        if (l === 1) {
            $(`#shelfRow${r}MinusBtn`).attr("disabled", "true");
        } else {
            $(`#shelfRow${r}MinusBtn`).removeAttr('disabled');
        }
        if (l >= 8) {
            $(`#shelfRow${r}PlusBtn`).attr("disabled", "true");
        } else {
            $(`#shelfRow${r}PlusBtn`).removeAttr('disabled');
        }
        $(`#shelfSelectRow${r}Btn`).removeAttr('disabled');
        $(`#shelfClearRow${r}Btn`).removeAttr('disabled');
    }
    $(`#shelfSelectAllBtn`).removeAttr('disabled');
    $(`#shelfClearAllBtn`).removeAttr('disabled');
    $('#selectShelfGroupBtn').removeAttr('disabled');
    if ($("#sidebarSelect").val() !== "shelfInfoDiv") {
        $("#sidebarSelect").val("shelfInfoDiv").change();
    }
    lookAtShelves([shelfKey]);
}

let setShelfType = (t, i) => {
    let shelfKeys = Object.keys(INTERSECT_SHELF_PLACEHOLDERS);
    let objectProperties = {};
    for (let key of shelfKeys) {
        let shelf = manager.renderManager.instanceKeyCache[key];
        shelf.userData.json.shelfType = t;
        shelf.userData.json.selectShelfTypeRank = i;
        objectProperties[shelfKey] = { shelfType: shelf.userData.json.shelfType, selectShelfTypeRank: i };
    }
    console.log('selectShelfType', i);
    socket.emit('selectShelfType', onlineUserID, i, onlineGroup);
    emitFunctionCall('updateObjectProperties', [objectProperties]);
}

let clearShelfInfo = () => {
    $("#shelfKey").text("");
    for (let r = 0; r < 4; ++r) {
        $(`#shelfRow${r}`).val(0);
        $(`#shelfRow${r}MinusBtn`).attr("disabled", "true");
        $(`#shelfRow${r}PlusBtn`).attr("disabled", "true");
        $(`#shelfSelectRow${r}Btn`).attr("disabled", "true");
        $(`#shelfClearRow${r}Btn`).attr("disabled", "true");
    }
    $(`#shelfSelectAllBtn`).attr("disabled", "true");
    $(`#shelfClearAllBtn`).attr("disabled", "true");
    $(`#selectShelfGroupBtn`).attr("disabled", "true");
    $("#shelfTypeRadios").empty();
}

let shelfRowMinus = (r) => {
    let shelfKey = $("#shelfKey").text();
    let oldRow = manager.renderManager.instanceKeyCache[shelfKey].userData.json.commodities[r];
    for (let i = oldRow.length - 1; i >= 0; --i) {
        if (oldRow[i].modelId === "") {
            let newRow = [...oldRow];
            newRow.splice(i, 1);
            $(`#shelfRow${r}`).val(newRow.length);
            if (newRow.length <= 1) $(`#shelfRow${r}MinusBtn`).attr("disabled", "true");
            $(`#shelfRow${r}PlusBtn`).removeAttr('disabled');
            changeShelfRow(shelfKey, r, newRow);
            return;
        }
    }
    alert("不能再减了！");
}

let shelfRowPlus = (r) => {
    let shelfKey = $("#shelfKey").text();
    let oldRow = manager.renderManager.instanceKeyCache[shelfKey].userData.json.commodities[r];
    let newRow = [...oldRow];
    newRow.push({ modelId: '', uuid: '' });
    $(`#shelfRow${r}`).val(newRow.length);
    if (newRow.length >= 8) $(`#shelfRow${r}PlusBtn`).attr("disabled", "true");
    $(`#shelfRow${r}MinusBtn`).removeAttr('disabled');
    changeShelfRow(shelfKey, r, newRow);
}

let shelfRowSelectBtn = (rows) => {
    outlinePass2.selectedObjects = outlinePass2.selectedObjects.filter(obj => !obj.name.startsWith('shelf-placeholder-'));
    let shelfKey = $("#shelfKey").text();
    INTERSECT_SHELF_PLACEHOLDERS = {};
    shelfRowSelect(shelfKey, rows);
}

let shelfRowSelect = (shelfKey, rows) => {
    let shelf = manager.renderManager.instanceKeyCache[shelfKey];
    let commodities = shelf.userData.json.commodities;
    INTERSECT_SHELF_PLACEHOLDERS[shelfKey] = new Set();

    for (let r of rows) {
        let l = commodities[r].length;
        for (let c = 0; c < l; ++c) {
            let phKey = `shelf-placeholder-${shelfKey}-${r}-${c}`;
            INTERSECT_SHELF_PLACEHOLDERS[shelfKey].add(phKey);
            outlinePass2.selectedObjects.push(manager.renderManager.instanceKeyCache[phKey]);
        }
    }

    recommendCommodities(shelf.userData.roomId);
}

let shelfRowClearBtn = (rows) => {
    outlinePass2.selectedObjects = outlinePass2.selectedObjects.filter(obj => !obj.name.startsWith('shelf-placeholder-'));
    $("#catalogItems").empty();
    let shelfKey = $("#shelfKey").text();
    INTERSECT_SHELF_PLACEHOLDERS = {};
    INTERSECT_SHELF_PLACEHOLDERS[shelfKey] = new Set();
    shelfRowClear(shelfKey, rows);
}

let shelfRowClear = (shelfKey, rows) => {
    let shelf = manager.renderManager.instanceKeyCache[shelfKey];
    let commodities = shelf.userData.json.commodities;
    for (let r of rows) {
        let l = commodities[r].length;
        for (let c = 0; c < l; ++c) {
            if (commodities[r][c].uuid) removeObjectByUUID(commodities[r][c].uuid);
            commodities[r][c] = { modelId: '', uuid: '' };
        }
    }
}

let addToGroupShelf = function(so) {
    if (onlineGroup !== 'OFFLINE' && so.userData.controlledByID !== undefined && so.userData.controlledByID !== onlineUser.id) {
        console.log(`This shelf is already claimed by ${so.userData.controlledByID}`);
        return;
    }
    let index = outlinePass2.selectedObjects.indexOf(so);
    if(index > -1){
        outlinePass2.selectedObjects.splice(index, 1);
        delete INTERSECT_SHELF_PLACEHOLDERS[so.userData.key];
        claimControlObject3D(so.userData.key, true);
    } else {
        outlinePass2.selectedObjects.push(so);
        INTERSECT_SHELF_PLACEHOLDERS[so.userData.key] = new Set();
        claimControlObject3D(so.userData.key, false);
        if (so.userData.json.commodities === undefined) {
            addShelfPlaceholders(so);
        }
    }
    if (LOOK_AT_SHELF) lookAtShelves(Object.keys(INTERSECT_SHELF_PLACEHOLDERS));
    recommendShelfType(so.userData.roomId, Object.keys(INTERSECT_SHELF_PLACEHOLDERS));
}

let releaseGroupShelf = function() {
    outlinePass2.selectedObjects = [];
    cancelClickingShelfPlaceholders();
}

let recommendCommodities = (roomId) => {
    let retPlaceholders = {};
    for (let key in INTERSECT_SHELF_PLACEHOLDERS) {
        if (manager.renderManager.instanceKeyCache[key].userData.json.shelfType === undefined) {
            console.log("Please select shelf category!");
            INTERSECT_OBJ = manager.renderManager.instanceKeyCache[key];
            setIntersectShelf();
            selectShelfGroup();
            return;
        }
        retPlaceholders[key] = {};
        let placeholderKeys = Array.from(INTERSECT_SHELF_PLACEHOLDERS[key]);
        for (let phKey of placeholderKeys) {
            let ph = manager.renderManager.instanceKeyCache[phKey];
            retPlaceholders[key][phKey] = [ph.userData.relativeVisibility, ph.userData.visPOI, ph.position.y];
        }
    }
    $("#catalogItems").empty();
    $.ajax({
        type: "POST",
        url: "/shelfPlaceholder",
        data: {
            room: JSON.stringify(manager.renderManager.scene_json.rooms[roomId]),
            placeholders: JSON.stringify(retPlaceholders),
            mode: $("input[name='shelfModeRadio']:checked").val()
        }
    }).done(function (o) {
        $('#searchinput').val('');
        $("#catalogItems").empty();
        searchResults = JSON.parse(o);
        searchResults.forEach(function (item) {
            newCatalogItem(item);
        });
    });
}

let recommendShelfType = (roomId, shelfKeys) => {
    $("#shelfTypeRadios").empty();
    $.ajax({
        type: "POST",
        url: "/shelfType",
        data: {
            room: JSON.stringify(manager.renderManager.scene_json.rooms[0]),
            shelfKeys: JSON.stringify(shelfKeys),
            mode: $("input[name='shelfModeRadio']:checked").val()
        }
    }).done(function (o) {
        $("#shelfTypeRadios").empty();
        shelfTypes = JSON.parse(o);
        shelfTypes.forEach(function (st, i) {
            let label = st.used ? shelfCategoryChineseName[st.name] : `<b>${shelfCategoryChineseName[st.name]}</b>`;
            $("#shelfTypeRadios").append(`
                <div class="form-check form-check-inline">
                    <input class="form-check-input" type="radio" name="shelfTypeRadio" id="shelfTypeRadio${i}" value="${st.name}" onclick="setShelfType('${st.name}', ${i})">
                    <label class="form-check-label" for="shelfTypeRadio${i}" id="shelfTypelabel${i}">${label}</label>
                </div>
            `);
            if (INTERSECT_OBJ?.userData.json?.shelfType === st.name) {
                $(`#shelfTypeRadio${i}`).prop("checked", true);
            }
        });
    });
}

let lookAtShelves = (shelfKeys) => {
    if (!LOOK_AT_SHELF) return;  // $("input[name='shelfModeRadio']:checked").val() != '3'
    if (shelfKeys.length > 5) {
        let aabb = new THREE.Box3();
        for (let shelfKey of shelfKeys) {
            aabb.expandByObject(manager.renderManager.instanceKeyCache[shelfKey]);
        }
        let bbox = {
            min: [aabb.min.x, aabb.min.y, aabb.min.z],
            max: [aabb.max.x, aabb.max.y, aabb.max.z]
        }
        topdownview(bbox);
        return;
    }
    let meanPos = new THREE.Vector3();
    for (let shelfKey of shelfKeys) {
        let shelf = manager.renderManager.instanceKeyCache[shelfKey];
        meanPos.add(shelf.position);
    }
    meanPos.divideScalar(shelfKeys.length);
    let offset = new THREE.Vector3(0, 0, 1.8);
    let axis = new THREE.Vector3(0, 1, 0);
    offset.applyAxisAngle(axis, manager.renderManager.instanceKeyCache[shelfKeys[0]].rotation.y);
    viewTransform({ 
        origin: [meanPos.x + offset.x, 1.5, meanPos.z + offset.z], 
        direction: [-offset.x, 0, -offset.z], 
        target: [meanPos.x, 1, meanPos.z]
    }, false);
    LAST_EDITED_SHELF = manager.renderManager.instanceKeyCache[shelfKeys[0]];
}

let nextShelf = () => {
    let objList = manager.renderManager.scene_json.rooms[0].objList;
    let idx = objList.indexOf(LAST_EDITED_SHELF?.userData.json);
    if (++idx === objList.length) {
        idx = 0;
    }
    let nextShelf = manager.renderManager.instanceKeyCache[objList[idx].key];
    let finishFlag = false;
    while (nextShelf?.userData.modelId !== 'shelf01' || shelfIsStocked(nextShelf)) {
        if (++idx === objList.length) {
            idx = 0;
            if (finishFlag) {
                alert("所有貨架已布滿！");
                return;
            } else {
                finishFlag = true;
            }
        }
        nextShelf = manager.renderManager.instanceKeyCache[objList[idx].key];
    }
    INTERSECT_OBJ = nextShelf;
    LAST_EDITED_SHELF = nextShelf;
    setIntersectShelf();
}

let showTrafficFlowNetwork = () => {
    let h = 1.5
    let trafficFlowNetwork = manager.renderManager.scene_json.rooms[0].trafficFlowNetwork;
    let points = [];
    for (let e of trafficFlowNetwork.edges) {
        let v0 = trafficFlowNetwork.vertices[e[0]];
        let v1 = trafficFlowNetwork.vertices[e[1]];
        points.push(new THREE.Vector3(v0[0], h, v0[2]));
        points.push(new THREE.Vector3(v1[0], h, v1[2]));
    }
    let geometry = new THREE.BufferGeometry().setFromPoints(points);
    let line = new THREE.LineSegments(geometry);
    scene.add(line);

    let path = [];
    for (let p of trafficFlowNetwork.path) {
        let v = trafficFlowNetwork.vertices[p];
        path.push(new THREE.Vector3(v[0], h, v[2]));
    }
    geometry = new THREE.BufferGeometry().setFromPoints(path);
    const material = new THREE.LineBasicMaterial({
        color: 0xff0000,
        linewidth: 3
    });
    let pathline = new THREE.Line(geometry, material);
    scene.add(pathline);

    for (let vId in trafficFlowNetwork.vertices) {
        let v = trafficFlowNetwork.vertices[vId];
        c = getCube(0.1,0.1,0.1,0.8);
        c.position.set(v[0], h, v[2]);
        scene.add(c)
    }
}

let showShelfRoute = () => {
    let h = 1.5
    let shelfRoute = manager.renderManager.scene_json.rooms[0].shelfRoute;
    let path = [];
    for (let p of shelfRoute.path) {
        let v = shelfRoute.vertices[p];
        path.push(new THREE.Vector3(v[0], h, v[2]));
    }
    geometry = new THREE.BufferGeometry().setFromPoints(path);
    const material = new THREE.LineBasicMaterial({
        color: 0x00ff00,
        linewidth: 3
    });
    let pathline = new THREE.Line(geometry, material);
    scene.add(pathline);

    for (let vId in shelfRoute.vertices) {
        let v = shelfRoute.vertices[vId];
        c = getCube(0.1,0.1,0.1,0.8);
        c.position.set(v[0], h, v[2]);
        scene.add(c)
    }
}

let shelfIsStocked = (shelf) => {
    if (shelf.userData.json.commodities === undefined) {
        addShelfPlaceholders(shelf);
        return false;
    }
    for (let row of shelf.userData.json.commodities) {
        for (let c of row) {
            if (c.modelId === "") {
                return false;
            }
        }
    }
    return true;
}

let clearAllShelves = () => {
    for (let obj of manager.renderManager.scene_json.rooms[0].objList) {
        if (obj?.modelId == 'shelf01' && obj.key in manager.renderManager.instanceKeyCache) {
            shelfRowClear(obj.key, [0, 1, 2, 3]);
            // obj.shelfType = undefined;
        }
    }
    clearDanglingCommodities();
}

let selectShelfGroup = () => {
    let shelfKey = $("#shelfKey").text();
    let groupId = manager.renderManager.instanceKeyCache[shelfKey].userData.json.groupId;
    let orient = manager.renderManager.instanceKeyCache[shelfKey].userData.json.orient;
    LOOK_AT_SHELF = false;
    for (let obj of manager.renderManager.scene_json.rooms[0].objList) {
        if (obj?.modelId == 'shelf01' && obj.groupId == groupId && obj.key != shelfKey
            && Math.abs(obj.orient - orient) < 0.1 && obj.key in manager.renderManager.instanceKeyCache) {
            addToGroupShelf(manager.renderManager.instanceKeyCache[obj.key]);
        }
    }
    LOOK_AT_SHELF = true;
    lookAtShelves(Object.keys(INTERSECT_SHELF_PLACEHOLDERS));
}

let startShelfPlannerExperiment = (manualClick = false) => {
    if (manualClick) $('#startShelfPlannerExperimentBtn').removeClass("btn-danger").addClass("btn-primary");
    let mode = $("input[name='shelfModeRadio']:checked").val();
    socket.emit('startShelfPlannerExperiment', onlineUserID, mode, onlineGroup);
}

let endShelfPlannerExperiment = () => {
    let mode = $("input[name='shelfModeRadio']:checked").val();
    socket.emit('endShelfPlannerExperiment', onlineUserID, mode, onlineGroup);
    $("#download_button").click();
}

let randomCommodities = () => {
    let yulinModels = ['yulin-apples', 'yulin-artichokes', 'yulin-avocados', 'yulin-bananas', 'yulin-beer-green-tall', 'yulin-beerpack1', 'yulin-beerpack2', 'yulin-blackricebasket', 'yulin-bleach', 'yulin-burger', 'yulin-butter', 'yulin-cakebag', 'yulin-cakebag2', 'yulin-cakebox', 'yulin-cakebox2', 'yulin-cakepack', 'yulin-candy', 'yulin-carrots', 'yulin-champagne-brown-tall', 'yulin-cheese', 'yulin-chicken', 'yulin-chip1', 'yulin-chip2', 'yulin-choco', 'yulin-choco2', 'yulin-chocobox', 'yulin-chocopack', 'yulin-cleaner1', 'yulin-cleaner2', 'yulin-coffee', 'yulin-coffee-brown-short', 'yulin-cola-red-short', 'yulin-colorricebasket', 'yulin-cream', 'yulin-cream2', 'yulin-donut', 'yulin-egg', 'yulin-egg2', 'yulin-fastfoodcup-pink', 'yulin-fastfoodcup-red', 'yulin-flour', 'yulin-flour2', 'yulin-frenchfries', 'yulin-garlic', 'yulin-glasscup-blue', 'yulin-glasscup-blue2', 'yulin-glasscup-grey', 'yulin-glasscup-grey2', 'yulin-glasscup-pink', 'yulin-glasscup-pink2', 'yulin-glassware-short-blue2', 'yulin-glassware-short-grey', 'yulin-glassware-short-grey2', 'yulin-glassware-short-orange', 'yulin-glassware-short-orange2', 'yulin-glassware-short-pink', 'yulin-glassware-tall-grey', 'yulin-glassware-tall-orange', 'yulin-glassware-tall-pink', 'yulin-grapefruits', 'yulin-greenricebasket', 'yulin-hampack', 'yulin-holder-green', 'yulin-holder-yellow', 'yulin-hotdog', 'yulin-hotdog2', 'yulin-jam', 'yulin-juice-blue-large', 'yulin-juice-brown-large', 'yulin-juice-white-large', 'yulin-ketchup', 'yulin-kiwis', 'yulin-laundry', 'yulin-laundry2', 'yulin-lemons', 'yulin-lemonwater-yellow-short', 'yulin-maffins', 'yulin-mangos', 'yulin-meat', 'yulin-meat2', 'yulin-meatpack', 'yulin-meatpack2', 'yulin-meatpack3', 'yulin-milk-blue-short', 'yulin-milkpack', 'yulin-mushrooms', 'yulin-niujiaobao', 'yulin-oil', 'yulin-oil2', 'yulin-onions', 'yulin-orangericebasket', 'yulin-pancakes', 'yulin-papayas', 'yulin-paperroll', 'yulin-paperroll2', 'yulin-pasta', 'yulin-pasta2', 'yulin-pepper', 'yulin-perrys', 'yulin-pieceofcake', 'yulin-pineapples', 'yulin-plant1', 'yulin-plant2', 'yulin-plant3', 'yulin-plant5', 'yulin-potatos', 'yulin-pretzel', 'yulin-pumpkins', 'yulin-rice', 'yulin-rice2', 'yulin-rollingpin', 'yulin-rollingpin2', 'yulin-salt', 'yulin-sandwich', 'yulin-sausages', 'yulin-sause', 'yulin-seedpack', 'yulin-seedpack2', 'yulin-shampoo-black', 'yulin-shampoo-green', 'yulin-shampoo-white', 'yulin-shortcup-brown', 'yulin-shortcup-grey', 'yulin-soap', 'yulin-soap2', 'yulin-soda-orange-short', 'yulin-squashs', 'yulin-steak', 'yulin-sudong1', 'yulin-sudong2', 'yulin-sudong3', 'yulin-sugar', 'yulin-sugar2', 'yulin-sushis', 'yulin-sushis2', 'yulin-tallcup-red', 'yulin-tallcup-yellow', 'yulin-tea', 'yulin-tea-brown-short', 'yulin-tincan', 'yulin-toast', 'yulin-tomatos', 'yulin-toothpaste', 'yulin-vase', 'yulin-vase2', 'yulin-water-blue-tall', 'yulin-watermelons', 'yulin-wine-green-tall', 'yulin-yogurt', 'yulin-yogurt-pink', 'yulin-zucchinis'];
    for (let obj of manager.renderManager.scene_json.rooms[0].objList) {
        if (obj?.modelId == 'shelf01') {
            let model = yulinModels[Math.floor(Math.random()*151)];
            console.log(model)
            let rows = [];
            for (let i = 0; i < 4; i++) {
                rows.push([{modelId: model}]);
            }
            loadObjectToCache(model, ()=>{
                yulin(obj.key, rows);
            }, [], 'obj');
        }
    }
}

let computePlaceholdersVisbility = () => {
    let yAxis = new THREE.Vector3(0, 1, 0);
    let angles = [Math.PI * 5 / 12, Math.PI / 3, Math.PI / 4, Math.PI / 6, Math.PI / 12, 
                0, -Math.PI / 12, -Math.PI / 6, -Math.PI / 4, -Math.PI / 3, -Math.PI * 5 / 12];
    let maxDis = angles.map(x => 0);

    for (const key in manager.renderManager.instanceKeyCache) {
        if (!key.startsWith('shelf-placeholder-')) continue;
        const placeholder = manager.renderManager.instanceKeyCache[key];
        let origin = placeholder.position.clone();
        let offset = new THREE.Vector3(0 * placeholder.scale.x, 0 * placeholder.scale.y, 0.23 * placeholder.scale.z);
        offset.applyAxisAngle(yAxis, placeholder.rotation.y);
        origin.add(offset);
        const raycaster = new THREE.Raycaster();

        // Visibility to Places of Interest
        let direction = new THREE.Vector3(0.1-origin.x, 1.3-origin.y, 7.5-origin.z);
        direction.normalize();
        raycaster.set(origin, direction);
        let intersects = raycaster.intersectObjects(Object.values(manager.renderManager.instanceKeyCache).concat(Object.values(manager.renderManager.wfCache)), true);
        if (intersects.length == 0) {
            placeholder.userData.visPOI = 1
        } else {
            // console.log(intersects)
            placeholder.userData.visPOI = 0
        }
        // let cube = getCube(0.1, 0.1, 0.1, 0.6, d3.interpolateRdYlBu(1-placeholder.userData.visPOI));
        // cube.position.copy(placeholder.position);
        // scene.add(cube);
        // continue;

        // Visible field
        origin.y = 1;
        placeholder.userData.dis_theta = [];
        for (const [index, theta] of angles.entries()) {
            direction = new THREE.Vector3(0, 0, 1);
            direction.applyAxisAngle(yAxis, placeholder.rotation.y + theta);
            raycaster.set(origin, direction);
            let intersects = raycaster.intersectObjects(Object.values(manager.renderManager.instanceKeyCache).concat(Object.values(manager.renderManager.wfCache)), true);
            if (intersects.length == 0) {
                // console.log('no intersects', origin, theta * 180 / Math.PI)
                continue;
            }
            placeholder.userData.dis_theta.push(intersects[0].distance);
            maxDis[index] = Math.max(maxDis[index], intersects[0].distance);
        }
    }

    let minVisibility, maxVisibility;
    for (const key in manager.renderManager.instanceKeyCache) {
        if (!key.startsWith('shelf-placeholder-')) continue;
        const placeholder = manager.renderManager.instanceKeyCache[key];
        placeholder.userData.dis_theta_norm = placeholder.userData.dis_theta.map((dis, index) => dis / maxDis[index]);
        placeholder.userData.visibility = placeholder.userData.dis_theta_norm.reduce((x,y) => x+y) / placeholder.userData.dis_theta_norm.length;
        minVisibility = minVisibility ? Math.min(minVisibility, placeholder.userData.visibility) : placeholder.userData.visibility;
        maxVisibility = maxVisibility ? Math.max(maxVisibility, placeholder.userData.visibility) : placeholder.userData.visibility;
    }

    let showVisibility = false;
    for (const key in manager.renderManager.instanceKeyCache) {
        if (!key.startsWith('shelf-placeholder-')) continue;
        const placeholder = manager.renderManager.instanceKeyCache[key];
        let vis = (placeholder.userData.visibility - minVisibility) / (maxVisibility - minVisibility);
        placeholder.userData.relativeVisibility = vis;
        if (showVisibility) {
            let cube = getCube(0.1, 0.1, 0.1, 0.6, d3.interpolateRdYlBu(1-vis));
            cube.position.copy(placeholder.position);
            scene.add(cube);
        }
    }
}

let yulinModelChineseName = {
    "yulin-beer-green-tall": "啤酒",
    "yulin-beerpack1": "啤酒",
    "yulin-beerpack2": "啤酒",
    "yulin-champagne-brown-tall": "香槟",
    "yulin-coffee-brown-short": "咖啡",
    "yulin-cola-red-short": "可乐",
    "yulin-juice-blue-large": "果汁",
    "yulin-juice-brown-large": "果汁",
    "yulin-juice-white-large": "果汁",
    "yulin-lemonwater-yellow-short": "柠檬水",
    "yulin-milk-blue-short": "牛奶",
    "yulin-milkpack": "牛奶",
    "yulin-soda-orange-short": "苏打水",
    "yulin-tea-brown-short": "茶",
    "yulin-water-blue-tall": "水",
    "yulin-wine-green-tall": "红酒",
    "yulin-yogurt": "酸奶",
    "yulin-yogurt-pink": "酸奶",
    "yulin-burger": "汉堡",
    "yulin-cakepack": "蛋糕",
    "yulin-hotdog": "热狗",
    "yulin-hotdog2": "热狗",
    "yulin-sandwich": "三明治",
    "yulin-toast": "吐司",
    "yulin-donut": "甜甜圈",
    "yulin-niujiaobao": "牛角包",
    "yulin-pancakes": "班戟",
    "yulin-pieceofcake": "蛋糕",
    "yulin-pretzel": "椒盐脆饼",
    "yulin-maffins": "松饼",
    "yulin-blackricebasket": "谷物",
    "yulin-colorricebasket": "谷物",
    "yulin-flour": "面粉",
    "yulin-flour2": "面粉",
    "yulin-greenricebasket": "谷物",
    "yulin-oil": "油",
    "yulin-oil2": "油",
    "yulin-orangericebasket": "谷物",
    "yulin-rice": "米",
    "yulin-rice2": "米",
    "yulin-butter": "黄油",
    "yulin-cheese": "芝士",
    "yulin-jam": "果酱",
    "yulin-ketchup": "番茄酱",
    "yulin-pepper": "胡椒粉",
    "yulin-salt": "盐",
    "yulin-sause": "酱",
    "yulin-sugar": "糖",
    "yulin-sugar2": "糖",
    "yulin-pasta": "意大利面",
    "yulin-pasta2": "意大利面",
    "yulin-sudong1": "速冻-派",
    "yulin-sudong2": "速冻-饭",
    "yulin-sudong3": "速冻-比萨",
    "yulin-sushis": "寿司",
    "yulin-sushis2": "寿司",
    "yulin-apples": "苹果",
    "yulin-artichokes": "朝鲜蓟",
    "yulin-avocados": "牛油果",
    "yulin-bananas": "香蕉",
    "yulin-carrots": "胡萝卜",
    "yulin-garlic": "大蒜",
    "yulin-grapefruits": "柚子",
    "yulin-kiwis": "猕猴桃",
    "yulin-lemons": "柠檬",
    "yulin-mangos": "芒果",
    "yulin-mushrooms": "蘑菇",
    "yulin-onions": "洋葱",
    "yulin-papayas": "木瓜",
    "yulin-perrys": "榨菜",
    "yulin-pineapples": "菠萝",
    "yulin-potatos": "土豆",
    "yulin-pumpkins": "南瓜",
    "yulin-squashs": "南瓜",
    "yulin-tomatos": "西红柿",
    "yulin-watermelons": "西瓜",
    "yulin-zucchinis": "西葫芦",
    "yulin-chicken": "鸡肉",
    "yulin-egg": "鸡蛋",
    "yulin-egg2": "鸡蛋",
    "yulin-hampack": "火腿",
    "yulin-meat": "火腿",
    "yulin-meat2": "火腿",
    "yulin-meatpack": "鸡翅",
    "yulin-meatpack2": "牛肉",
    "yulin-meatpack3": "猪肉",
    "yulin-sausages": "香肠",
    "yulin-steak": "牛排",
    "yulin-cakebag": "蛋糕",
    "yulin-cakebag2": "蛋糕",
    "yulin-cakebox": "蛋糕",
    "yulin-cakebox2": "蛋糕",
    "yulin-candy": "糖果",
    "yulin-chip1": "薯片",
    "yulin-chip2": "薯片",
    "yulin-choco": "巧克力",
    "yulin-choco2": "巧克力",
    "yulin-chocobox": "巧克力",
    "yulin-chocopack": "巧克力",
    "yulin-coffee": "咖啡",
    "yulin-cream": "奶油",
    "yulin-cream2": "奶油",
    "yulin-frenchfries": "薯条",
    "yulin-tea": "茶",
    "yulin-tincan": "罐头",
    "yulin-shampoo-black": "洗发水",
    "yulin-shampoo-white": "洗发水",
    "yulin-shampoo-green": "洗发水",
    "yulin-cleaner1": "清洁剂",
    "yulin-bleach": "漂白剂",
    "yulin-fastfoodcup-pink": "杯",
    "yulin-fastfoodcup-red": "杯子",
    "yulin-glasscup-blue": "玻璃杯",
    "yulin-glasscup-blue2": "玻璃杯",
    "yulin-glasscup-grey": "玻璃杯",
    "yulin-glasscup-grey2": "玻璃杯",
    "yulin-glasscup-pink": "玻璃杯",
    "yulin-glasscup-pink2": "玻璃杯",
    "yulin-glassware-short-blue2": "玻璃杯",
    "yulin-glassware-short-grey": "玻璃杯",
    "yulin-glassware-short-grey2": "玻璃杯",
    "yulin-glassware-short-orange": "玻璃杯",
    "yulin-glassware-short-orange2": "玻璃杯",
    "yulin-glassware-short-pink": "玻璃杯",
    "yulin-glassware-tall-grey": "玻璃杯",
    "yulin-glassware-tall-orange": "玻璃杯",
    "yulin-glassware-tall-pink": "玻璃杯",
    "yulin-holder-green": "容器",
    "yulin-holder-yellow": "容器",
    "yulin-laundry": "洗衣粉",
    "yulin-laundry2": "洗衣粉",
    "yulin-paperroll": "卫生纸",
    "yulin-paperroll2": "卫生纸",
    "yulin-rollingpin": "擀面杖",
    "yulin-rollingpin2": "擀面杖",
    "yulin-shortcup-brown": "杯子",
    "yulin-shortcup-grey": "杯子",
    "yulin-soap": "肥皂",
    "yulin-soap2": "肥皂",
    "yulin-tallcup-red": "杯子",
    "yulin-tallcup-yellow": "杯子",
    "yulin-toothpaste": "牙膏",
    "yulin-vase": "花瓶",
    "yulin-vase2": "花瓶",
    "yulin-plant1": "植物",
    "yulin-plant2": "植物",
    "yulin-plant3": "植物",
    "yulin-plant5": "植物",
    "yulin-seedpack": "瓜子",
    "yulin-seedpack2": "瓜子"
}

let shelfCategoryChineseName = {
    "frozen fast food": "冷冻食品",
    "vegetable": "蔬菜",
    "snack": "零食",
    "bakery": "面包烘培",
    "drink": "饮料",
    "dairy": "奶制品",
    "fruit": "水果",
    "condiment": "调味",
    "grain": "谷物",
    "plant": "植物",
    "oil": "油",
    "alcohol": "酒水",
    "daily necessities": "日用品",
    "meat": "肉类",
    "mix": "混合"
};