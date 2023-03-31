const clickCatalogItem = function (e, d=undefined) {
    e.preventDefault();
    if(e.path && d3.select(e.path[0].parentElement).attr('id') === 'scenePaletteGroup'){
        INSERT_OBJ = {
            "modelId": d.modelId,
            "coarseSemantic": d.coarseSemantic, 
            "translate": [0.0, 0.0, 0.0],"scale": [1.0, 1.0, 1.0],"rotate": [0.0, 0.0, 0.0]
        };
    }else{
        if($(e.target).attr('status') === 'clutterpaletteCategory'){
            while (secondaryCatalogItems.firstChild) {secondaryCatalogItems.firstChild.remove();}
            searchResults = JSON.parse($(e.target).attr('secondaryCatalogItems'));
            searchResults.forEach(function (item) {
                newSecondaryCatalogItem(item);
            });
        }
        INSERT_OBJ = {
            "modelId": $(e.target).attr("objectName"),
            "coarseSemantic": $(e.target).attr("coarseSemantic"), 
            "translate": [0.0, 0.0, 0.0],"scale": [1.0, 1.0, 1.0],"rotate": [0.0, 0.0, 0.0],
            "format": $(e.target).attr("format"),
            "status": $(e.target).attr("status"),
            'object3d': undefined
        };
    }
    scene.remove(scene.getObjectByName(INSERT_NAME));
    // avoid confictions between ordinary insertions and the auxiliary mode; 
    if(!manager.renderManager.scene_json || AUXILIARY_MODE) return;
    if(e.type === 'contextmenu'){
        On_MAGEADD = true;
        loadSingleObjectPrior(INSERT_OBJ.modelId);
    }else{
        On_ADD = true;
        timeCounter.addStart = moment();
    }
    scenecanvas.style.cursor = "crosshair";
    loadObjectToCache(INSERT_OBJ.modelId, ()=>{
        if (shelfstocking_Mode && INSERT_OBJ.modelId.startsWith('yulin') && Object.keys(INTERSECT_SHELF_PLACEHOLDERS).length !== 0) {
            stockShelves();
            return;
        }
        INSERT_OBJ.object3d = objectCache[INSERT_OBJ.modelId].clone();
        if(INSERT_OBJ.status !== undefined){
            playAnimation(INSERT_OBJ.object3d);
        }
        if (clutterpalette_Mode) {
            INSERT_OBJ.object3d.name = INSERT_NAME;
            INSERT_OBJ.object3d.position.set(clutterpalettePos.x, clutterpalettePos.y, clutterpalettePos.z);
            INSERT_OBJ.object3d.rotation.set(0, 0, 0, 'XYZ');
            INSERT_OBJ.object3d.scale.set(1, 1, 1);
            scene.add(INSERT_OBJ.object3d)
        }
    }, [], INSERT_OBJ.format); 
}

const stockShelves = () => {
    On_ADD = false;
    scenecanvas.style.cursor = "auto";
    let modelId = INSERT_OBJ.modelId;
    for (const shelfKey in INTERSECT_SHELF_PLACEHOLDERS) {
        let shelf = manager.renderManager.instanceKeyCache[shelfKey];
        let commodities = shelf.userData.json.commodities;
        for (const phKey of INTERSECT_SHELF_PLACEHOLDERS[shelfKey]) {
            let ph = manager.renderManager.instanceKeyCache[phKey];
            let r = ph.userData.shelfRow;
            let c = ph.userData.shelfCol;
            let l = commodities[r].length;
            if (commodities[r][c].uuid) {
                removeObjectByUUID(commodities[r][c].uuid)
                commodities[r][c] = { modelId: '', uuid: '' };
            }
            if (modelId !== 'yulin-empty') {
                addCommodityToShelf(shelfKey, modelId, r, c, l);
            }
        }
    }
    cancelClickingShelfPlaceholders();
}

const clickTextureItem = function(e){
    let texture = new THREE.TextureLoader().load($(e.target).data("imgpath"));
    texture.wrapS = THREE.RepeatWrapping;
    texture.wrapT = THREE.RepeatWrapping;
    texture.repeat.set(1, 1);
    let material = new THREE.MeshPhongMaterial( { map: texture } );
    manager.renderManager.cwfCache.forEach(o => {
        o.children.forEach(c => {
            c.material = material;
        });
    });
};

const applyLayoutViewAdjust = function(){
    if(LayoutViewAdjust_MODE && (currentRoomId)){
        $.ajax({
            type: "POST",
            contentType: "application/json; charset=utf-8",
            url: `/autoviewroom/${currentRoomId}`,
            data: JSON.stringify(getDownloadSceneJson()),
            success: function (data) {
                pcam = JSON.parse(data);
                console.log(pcam);
                viewTransform(pcam)
                manager.renderManager.scene_json.lastAutoView = pcam;
            }
        });
    }
}

const newCatalogItem = function(item){
    let iDiv = document.createElement('div');
    iDiv.className = "catalogItem";
    iDiv.style.backgroundImage = "url(" + item.thumbnail + ")";
    iDiv.setAttribute('objectID', item.id);
    iDiv.setAttribute('objectName', item.name);
    iDiv.setAttribute('modelId', item.name);
    iDiv.setAttribute('coarseSemantic', item.semantic);
    iDiv.setAttribute('semantic', item.semantic);
    if(!item.status){item.status = 'origin';}
    if(item.status === "clutterpaletteCategory"){
        iDiv.setAttribute('secondaryCatalogItems', item.secondaryCatalogItems);
        iDiv.innerHTML = item.semantic;
    }
    iDiv.setAttribute('status', item.status);
    if(!item.format){
        item.format = 'obj'
    }
    iDiv.setAttribute('format', item.format);
    iDiv.addEventListener('click', clickCatalogItem);
    iDiv.addEventListener('contextmenu', clickCatalogItem);
    catalogItems.appendChild(iDiv);
};

const newSecondaryCatalogItem = function(item){
    let iDiv = document.createElement('div');
    iDiv.className = "catalogItem";
    iDiv.style.backgroundImage = "url(" + item.thumbnail + ")";
    iDiv.setAttribute('objectID', item.id);
    iDiv.setAttribute('objectName', item.name);
    iDiv.setAttribute('modelId', item.name);
    iDiv.setAttribute('coarseSemantic', item.semantic);
    iDiv.setAttribute('semantic', item.semantic);
    if(!item.status){item.status = 'origin';}
    iDiv.setAttribute('status', item.status);
    if(!item.format){
        item.format = 'obj'
    }
    iDiv.setAttribute('format', item.format);
    iDiv.addEventListener('click', clickCatalogItem);
    iDiv.addEventListener('contextmenu', clickCatalogItem);
    gatheringObjCat[item.name] = item.semantic;
    secondaryCatalogItems.appendChild(iDiv);
};

const clickSketchSearchButton = function () {
    while (catalogItems.firstChild) {
        catalogItems.firstChild.remove();
    }
    let dataURL = drawingCanvas.toDataURL();
    dataURL = dataURL.split(',')[1]
    let keyword = $('#searchinput').val();
    $.ajax({
        type: "POST",
        url: "/sketch",
        data: {
            imgBase64: dataURL,
            keyword: keyword
        }
    }).done(function (o) {
        $('#searchinput').val(''); // remember to clear the input box each time; 
        searchResults = JSON.parse(o);
        searchResults.forEach(function (item) {
            newCatalogItem(item);
        });
    });
};

const clickTextSearchButton = function () {
    while (catalogItems.firstChild) {
        catalogItems.firstChild.remove();
    }
    var search_url = "/query2nd?kw=" + document.getElementById("searchinput").value
    + `&num=${20}`;
    $.getJSON(search_url, function (data) {
        searchResults = data;
        searchResults.forEach(function (item) {
            newCatalogItem(item);
        });
    });
};

const clickModuleSearchButton = function () {
    while (catalogItems.firstChild) {catalogItems.firstChild.remove();}
    var search_url = "/queryModule?kw=" + document.getElementById("searchinput").value;
    $.getJSON(search_url, function (data) {
        searchResults = data;
        searchResults.forEach(function (item) {
            newCatalogItem(item);
        });
    });
};

const autoViewGetMid = function(lastPos, pcam, direction, tarDirection){
    let mid = {
        x: (lastPos.x + pcam.origin[0]) / 2,
        y: (lastPos.y + pcam.origin[1]) / 2,
        z: (lastPos.z + pcam.origin[2]) / 2
    };
    let bisector = new THREE.Vector3(0,0,0).add(direction).add(tarDirection);
    let midDirection;
    if(bisector.length() === 0){
        let theta = Math.PI / 2;
        let k = new THREE.Vector3(pcam.up[0], pcam.up[1], pcam.up[2]);
        let v = tarDirection.copy();
        midDirection = v.multiplyScalar(Math.cos(theta)).add(k.cross(v).multiplyScalar(Math.sin(theta)));
        midDirection = bisector.normalize();
    }else{
        midDirection = bisector.normalize();
    }
    let midLookat = {
        x: mid.x + midDirection.x,
        y: mid.y,
        z: mid.z + midDirection.z
    }
    return [mid, midLookat]
}

const viewTransform = function(pcam){
    cancelClickingObject3D();
    clickAutoViewItemDuration = 1;
    let direction = new THREE.Vector3(
        orbitControls.target.x - camera.position.x,
        orbitControls.target.y - camera.position.y,
        orbitControls.target.z - camera.position.z
    ).normalize();
    let tarDirection = new THREE.Vector3(pcam.direction[0], pcam.direction[1], pcam.direction[2]).normalize();
    gsap.to(camera.up, {
        duration: clickAutoViewItemDuration,
        x: 0,
        y: 1,
        z: 0
    });
    if(direction.dot(tarDirection) > 0){
        gsap.to(camera.position, {
            duration: clickAutoViewItemDuration,
            x: pcam.origin[0],
            y: pcam.origin[1],
            z: pcam.origin[2]
        });
        gsap.to(orbitControls.target, {
            duration: clickAutoViewItemDuration,
            x: pcam.target[0],
            y: pcam.target[1],
            z: pcam.target[2],
        });
    }else{
        let camTween = gsap.timeline({repeat: 0});
        let orbTween = gsap.timeline({repeat: 0});
        let midres = autoViewGetMid(camera.position, pcam, direction, tarDirection);
        let mid = midres[0], midLookat = midres[1];
        camTween.to(camera.position, {
            duration: clickAutoViewItemDuration/2,
            x: mid.x,
            y: mid.y,
            z: mid.z
        });
        orbTween.to(orbitControls.target, {
            duration: clickAutoViewItemDuration/2,
            x: midLookat.x,
            y: midLookat.y,
            z: midLookat.z
        });
        camTween.to(camera.position, {
            duration: clickAutoViewItemDuration/2,
            x: pcam.origin[0],
            y: pcam.origin[1],
            z: pcam.origin[2]
        });
        orbTween.to(orbitControls.target, {
            duration: clickAutoViewItemDuration/2,
            x: pcam.target[0],
            y: pcam.target[1],
            z: pcam.target[2]
        });
    }
}

const clickAutoViewItem = function(e){
    let pcam = $(e.target).data("pcam");
    viewTransform(pcam);
}

const sceneViewerMethod = function(ret){
    ret.forEach(function (item) {
        let iDiv = document.createElement('div');
        let image = new Image();
        image.src = `/autoviewimgs/${manager.renderManager.scene_json.origin}/${item.identifier}`;
        image.onload = function(){
            iDiv.style.width = '120px';
            iDiv.style.height = `${120 / (image.width / image.height)}px`;
        };
        iDiv.className = "catalogItem";
        iDiv.style.backgroundImage = `url(/autoviewimgs/${manager.renderManager.scene_json.origin}/${item.identifier})`;
        iDiv.style.backgroundSize = '100% 100%';
        iDiv.addEventListener('click', clickAutoViewItem);
        catalogItems.appendChild(iDiv);
        $(iDiv).data('pcam', item);
    });
}

const clickAutoViewButton = function () {
    while (catalogItems.firstChild) {
        catalogItems.firstChild.remove();
    }
    let search_url = "/autoviewByID?origin=" + manager.renderManager.scene_json.origin;
    $.getJSON(search_url, function (data) {
        sceneViewerMethod(data);
    });
};

let autoViewPathPos = gsap.timeline({repeat: 0});
let autoViewPathTar = gsap.timeline({repeat: 0});
const AUTOVIEWPATHSPEED = 1.;
const clickAutoViewPath = function(){
    let search_url = "/autoViewPath?origin=" + manager.renderManager.scene_json.origin;
    $.getJSON(search_url, function (data) {
        autoViewPathPos.kill()
        autoViewPathTar.kill()
        autoViewPathPos = gsap.timeline({repeat: 0});
        autoViewPathTar = gsap.timeline({repeat: 0});
        let lastPos = undefined
        let direction = new THREE.Vector3(
            orbitControls.target.x - camera.position.x,
            orbitControls.target.y - camera.position.y,
            orbitControls.target.z - camera.position.z
        ).normalize(); 
        data.forEach(function (datum) {
            let t;
            let thisPos = new THREE.Vector3(datum.origin[0], datum.origin[1], datum.origin[2]); 
            if(lastPos){
                t = lastPos.distanceTo(thisPos) / AUTOVIEWPATHSPEED;
            }else{
                t = 0.6
                lastPos = new THREE.Vector3(camera.position.x, camera.position.y, camera.position.z); 
            }
            let tarDirection = new THREE.Vector3(datum.direction[0], datum.direction[1], datum.direction[2]).normalize();
            if(direction.dot(tarDirection) > 0){
                autoViewPathPos.to(camera.position, {
                    duration: t,
                    x: datum.origin[0],
                    y: datum.origin[1],
                    z: datum.origin[2],
                    ease: "none"
                });
                autoViewPathTar.to(orbitControls.target, {
                    duration: t,
                    x: datum.target[0],
                    y: datum.target[1],
                    z: datum.target[2],
                    ease: "none"
                });
            }else{
                let midres = autoViewGetMid(lastPos, datum, direction, tarDirection);
                let mid = midres[0], midLookat = midres[1];
                autoViewPathPos.to(camera.position, {
                    duration: t/2,
                    x: mid.x,
                    y: mid.y,
                    z: mid.z,
                    ease: "none"
                });
                autoViewPathTar.to(orbitControls.target, {
                    duration: t/2,
                    x: midLookat.x,
                    y: midLookat.y,
                    z: midLookat.z,
                    ease: "none"
                });
                autoViewPathPos.to(camera.position, {
                    duration: t/2,
                    x: datum.origin[0],
                    y: datum.origin[1],
                    z: datum.origin[2],
                    ease: "none"
                });
                autoViewPathTar.to(orbitControls.target, {
                    duration: t/2,
                    x: datum.target[0],
                    y: datum.target[1],
                    z: datum.target[2],
                    ease: "none"
                });
            }
            direction = tarDirection;
            lastPos = thisPos;
        });
    });
}

const mappingHover = function(e){
    let meta = $(e.target).data("meta");
    let image = floorPlanMapping.get(meta.identifier);
    let wh = getMappingWidthHeight(image);
    let w = wh[0], h = wh[1];
    let scale = 1
    if (w > $(window).width() * 0.80) {
        scale = $(window).width() * 0.80 / w
    }
    $(`#grids-${meta.identifier}`).css('height', `${h*scale}px`);
    $(`#grids-${meta.identifier}`).css('width', `${w*scale}px`);
    $(`#grids-${meta.identifier}`).css('opacity', '1');
    $(`#grids-${meta.identifier} .cell`).css('height', `${h/nrs}px`);
    $(`#grids-${meta.identifier} .cell`).css('width', `${w/ncs}px`);
    // $(`#grids-${meta.identifier}`).css('top', `${($(window).height()-h)/2}px`);
    // $(`#grids-${meta.identifier}`).css('left', `${($(window).width()-w)/2}px`);
}

const mappingLeave = function(e){
    let meta = $(e.target).data("meta");
    $(`#grids-${meta.identifier}`).css('height', '0px');
    $(`#grids-${meta.identifier}`).css('width', '0px');
    $(`#grids-${meta.identifier}`).css('opacity', '0');
}

const mappingClick = function(e){
    autoViewPathPos.kill();
    autoViewPathTar.kill();
    let meta = $(e.target).data("meta");
    $.getJSON(`/getSceneJsonByID/${meta.identifier}`, function(result){
        refreshSceneCall(result);
    });
}

const mappingRightClick = function(e){
    e.preventDefault();
    autoViewPathPos.kill();
    autoViewPathTar.kill();
    let meta = $(e.target).data("meta");
    $.getJSON(`/getSceneJsonByID/${meta.identifier}`, function(result){
        result.rooms.forEach(r => {
            let newObjList = [];
            r.objList.forEach(o => {
                if(!o.inDatabase){
                    newObjList.push(o);
                }
            });
            r.objList = newObjList;
        });
        socket.emit('sceneRefresh', result, onlineGroup);
    });
}

const addImageProcess = function(src){
    return new Promise((resolve) => {
        let img = new Image();
        img.onload = () => resolve(img);
        img.src = src;
    })
}

const getMappingWidthHeight = function(image){
    const F = 0.75;
    let w, h;
    // make the image being displayed inside the window.
    if($(window).height() >= $(window).width()){
        w = $(window).width() * F;
        h = w / (image.width / image.height);
    }else{
        h = $(window).height() * F;
        w = h / (image.height / image.width);
    }
    return [w, h]
}

const layoutviewadjust_control = function(){
    var layoutviewadjust_button = document.getElementById("layoutviewadjust_button");
    LayoutViewAdjust_MODE = !LayoutViewAdjust_MODE;
    if(LayoutViewAdjust_MODE){
        layoutviewadjust_button.style.backgroundColor = '#9400D3';
    }else{
        layoutviewadjust_button.style.backgroundColor = 'transparent';
    }
}

const nrs = 1;
const ncs = 1;
const floorPlanMapping = new Map();
const clickAutoViewMapping = function(){
    let search_url = "/autoviewMapping";
    $.getJSON(search_url, function (searchResults) {
        floorPlanMapping.clear();
        while (catalogItems.firstChild) {
            catalogItems.firstChild.remove();
        }
        // searchResults.push({
        //     'identifier': '05d05b98-e95c-4671-935d-7af6a1468d07'
        // })
        searchResults.forEach(function (item) {
            let iDiv = document.createElement('div');
            let image = new Image();
            image.onload = function(){
                iDiv.style.width = `${$(window).width() * 0.10}px`;
                iDiv.style.height = `${$(window).width() * 0.10 / (image.width / image.height)}px`;
                // let wh = getMappingWidthHeight(image);
                // let w = wh[0], h = wh[1];
                // $(`#grids-${item.identifier}`).css('height', `${h}px`);
                // $(`#grids-${item.identifier}`).css('width', `${w}px`);
                // $(`#grids-${item.identifier} .cell`).css('height', `${h/nrs}px`);
                // $(`#grids-${item.identifier} .cell`).css('width', `${w/ncs}px`);
                // $(`#grids-${item.identifier}`).css('top', `${($(window).height()-h)/2}px`);
                // $(`#grids-${item.identifier}`).css('left', `${($(window).width()-w)/2}px`);
            };
            image.src = `/autoviewimgs/mapping/${item.identifier}`;
            iDiv.className = "mapping catalogItem";
            iDiv.style.backgroundImage = `url(/autoviewimgs/mapping/${item.identifier})`;
            iDiv.style.backgroundSize = '100% 100%';
            iDiv.style.visibility = 'visible';
            iDiv.addEventListener('mouseover', mappingHover);
            iDiv.addEventListener('mouseout', mappingLeave);
            iDiv.addEventListener('click', mappingClick);
            iDiv.addEventListener('contextmenu', mappingRightClick);
            iDiv.classList.add('tiler');
            catalogItems.appendChild(iDiv);
            $(iDiv).data('meta', item);
            floorPlanMapping.set(item.identifier, image);
        });
        Splitting({
            target: '.tiler',
            by: 'cells',
            rows: nrs,
            columns: ncs,
            image: true
        });
        $('.tiler .cell-grid .cell').each(function(index){
            let meta = $(this).parent().parent().data("meta");
            $(this).parent().attr('id', `grids-${meta.identifier}`);
            $(this).attr('id', `grid-${meta.identifier}`);
            // let image = floorPlanMapping.get(meta.identifier);
            // let wh = getMappingWidthHeight(image);
            // let w = wh[0], h = wh[1];
            // $(this).css('height', `${h/nrs}px`);
            // $(this).css('width', `${w/ncs}px`);
            // $(this).parent().css('height', `${h}px`);
            // $(this).parent().css('width', `${w}px`);
        })
    });
};

const jiahong1115 = ['4.0_3.0_2', '4.0_3.0_64', '4.0_4.0_2', '4.0_4.0_64', '5.0_3.0_2', '5.0_3.0_47', 
'5.0_4.0_47', '5.5_4.0_23', '6.0_3.0_47', '6.0_3.0_61', '6.5_4.5_64', '6.5_4.5_78'];
const clickSelectRoomShape = function(){
    floorPlanMapping.clear();
    while (catalogItems.firstChild) {
        catalogItems.firstChild.remove();
    }
    jiahong1115.forEach(item => {
        let iDiv = document.createElement('div');
        let image = new Image();
        image.onload = function(){
            iDiv.style.width = `${$(window).width() * 0.10}px`;
            iDiv.style.height = `${$(window).width() * 0.10 / (image.width / image.height)}px`;
        };
        image.src = `/static/dataset/jiahong1115/${item}.png`;
        iDiv.className = "mapping catalogItem";
        iDiv.style.backgroundImage = `url(/static/dataset/jiahong1115/${item}.png)`;
        iDiv.style.backgroundSize = '100% 100%';
        iDiv.style.visibility = 'visible';
        iDiv.addEventListener('mouseover', mappingHover);
        iDiv.addEventListener('mouseout', mappingLeave);
        iDiv.addEventListener('click', (e) => {
            $.getJSON(`/static/dataset/jiahong1115/${item}.json`, function(result){
                result.origin = item;
                refreshSceneCall(result);
            });
            mappingLeave(e);
        });
        iDiv.classList.add('tiler');
        catalogItems.appendChild(iDiv);
        $(iDiv).data('meta', {'identifier': item.replaceAll('.', '-')});
        floorPlanMapping.set(item.replaceAll('.', '-'), image);
    });
    Splitting({
        target: '.tiler',
        by: 'cells',
        rows: nrs,
        columns: ncs,
        image: true
    });
    $('.tiler .cell-grid .cell').each(function(index){
        let meta = $(this).parent().parent().data("meta");
        $(this).parent().attr('id', `grids-${meta.identifier}`);
        $(this).attr('id', `grid-${meta.identifier}`);
    })
}

const showLargerCGSPreview = function(e){
    e.preventDefault();
    let meta = $(e.target).data("meta");
    let image = cgsPreview.get(meta);
    let wh = getMappingWidthHeight(image);
    let w = wh[0], h = wh[1];
    let scale = 1
    if (w > $(window).width() * 0.80) {
        scale = $(window).width() * 0.80 / w
    }
    $(`#grids-${meta}`).css('height', `${h*scale}px`);
    $(`#grids-${meta}`).css('width', `${w*scale}px`);
    $(`#grids-${meta}`).css('opacity', '1');
    $(`#grids-${meta} .cell`).css('height', `${h/nrs}px`);
    $(`#grids-${meta} .cell`).css('width', `${w/ncs}px`);
}

const hideLargerCGSPreview = function(e){
    let meta = $(e.target).data("meta");
    $(`#grids-${meta}`).css('height', '0px');
    $(`#grids-${meta}`).css('width', '0px');
    $(`#grids-${meta}`).css('opacity', '0');
}

const getOnLoadImage = function(src, iDiv){
    let image = new Image();
    image.onload = function(){
        iDiv.style.width = `${$(window).width() * 0.10}px`;
        iDiv.style.height = `${$(window).width() * 0.10 / (image.width / image.height)}px`;
    };
    image.src = src;
    return image;
}

const createSplittingDiv = function(imgsrc){
    let iDiv = document.createElement('div');
    iDiv.className = "mapping catalogItem";
    iDiv.style.backgroundImage = `url(${imgsrc})`;
    iDiv.style.backgroundSize = '100% 100%';
    iDiv.style.visibility = 'visible';
    iDiv.addEventListener('contextmenu', showLargerCGSPreview);
    iDiv.addEventListener('mouseout', hideLargerCGSPreview);
    iDiv.classList.add('tiler');
    catalogItems.appendChild(iDiv);
    return iDiv;
}

const CGSSplittingInit = function(){
    Splitting({
        target: '.tiler',
        by: 'cells',
        rows: nrs,
        columns: ncs,
        image: true
    });
    $('.tiler .cell-grid .cell').each(function(){
        let meta = $(this).parent().parent().data("meta");
        $(this).parent().attr('id', `grids-${meta}`);
        $(this).attr('id', `grid-${meta}`);
    })
}

const cgsPreviewClear = function(){
    cgsPreview.clear();
    while (catalogItems.firstChild) {
        catalogItems.firstChild.remove();
    }
}

const cgsPreview = new Map();

const cgsSFunc = function(){
    if(On_CGSeries){
        On_CGSeries = false;
        synchronize_json_object(INTERSECT_OBJ);
        CGSERIES_GROUP.clear();
        timeCounter.cgs += moment.duration(moment().diff(timeCounter.cgsStart)).asSeconds();
    }
    let search_url = `/getCGSCat/${this.textContent}`;
    $.getJSON(search_url, function (searchResults) {
        cgsPreviewClear();
        searchResults.forEach(function (item) {
            let imgsrc = `/cgsPreview/${item.dom}/${item.series}`
            let iDiv = createSplittingDiv(imgsrc);
            let image = getOnLoadImage(imgsrc, iDiv);
            iDiv.setAttribute('objectName', item.dom);
            $(iDiv).data('meta', `${item.dom}-${item.series}`);
            cgsPreview.set(`${item.dom}-${item.series}`, image);
            iDiv.addEventListener('click', clickCatalogItem);
        });
        CGSSplittingInit();
    })
}

const clickCGSPreview = function(){
    if(INTERSECT_OBJ === undefined){
        return;
    }
    let search_url = `/availableCGS/${INTERSECT_OBJ.userData.modelId}`;
    $.getJSON(search_url, function (searchResults) {
        cgsPreviewClear();
        searchResults.forEach(function (item) {
            let imgsrc = `/cgsPreview/${INTERSECT_OBJ.userData.modelId}/${item}`
            let iDiv = createSplittingDiv(imgsrc);
            let image = getOnLoadImage(imgsrc, iDiv);
            $(iDiv).data('meta', item);
            iDiv.setAttribute('objectName', INTERSECT_OBJ.userData.modelId);
            cgsPreview.set(item, image);
            iDiv.addEventListener('click', function(e){
                if(On_CGSeries){
                    loadCGSeries(INTERSECT_OBJ.userData.modelId, $(e.target).data("meta"));
                }else{
                    clickCatalogItem(e)
                }
                
            });
        });
        CGSSplittingInit();
    });
};

const clear_panel = function(){
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

const searchPanelInitialization = function(){
    $("#searchbtn").click(clickTextSearchButton);
    $("#autoView").click(clickAutoViewButton);
    // $("#autoView").click(() => { socket.emit('autoView', getDownloadSceneJson(), onlineGroup); });
    $("#autoViewPath").click(clickAutoViewPath);
    $("#autoViewMapping").click(clickAutoViewMapping);
    $("#selectRoomShapebtn").click(clickSelectRoomShape);
    // $("#floorPlanbtn").click(() => {
    //     let origin = document.getElementById("searchinput").value;
    //     $.getJSON(`/getSceneJsonByID/${origin}`, function(result){
    //         socket.emit('sceneRefresh', result, onlineGroup);
    //     });
    // })
    $("#floorPlanbtn").click(clickModuleSearchButton);
    $("#sketchsearchbtn").click(clickSketchSearchButton);
    $("#sketchclearbtn").click(clearCanvas);
    $("#manyTextures").click(() => {
        while (catalogItems.firstChild) {
            catalogItems.firstChild.remove();
        }
        let search_url = "/manyTextures";
        $.getJSON(search_url, function (data) {
            searchResults = data;
            searchResults.forEach(function (item) {
                let iDiv = document.createElement('div');
                iDiv.className = "catalogItem";
                iDiv.style.backgroundImage = "url(" + item.imgpath + ")";;
                iDiv.addEventListener('click', clickTextureItem)
                catalogItems.appendChild(iDiv);
                $(iDiv).data('imgpath', item.imgpath);
            });
        });
    })
}