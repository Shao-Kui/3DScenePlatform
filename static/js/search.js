const clickCatalogItem = function (e) {
    scene.remove(scene.getObjectByName(INSERT_NAME));
    // avoid confictions between ordinary insertions and the auxiliary mode; 
    if(!manager.renderManager.scene_json || AUXILIARY_MODE) return;    
    On_ADD = true;
    scenecanvas.style.cursor = "crosshair";
    loadObjectToCache($(e.target).attr("modelId")); 
    INSERT_OBJ = {
        "modelId": $(e.target).attr("objectName"),
        "coarseSemantic": $(e.target).attr("coarseSemantic"), 
        "translate": [0.0, 0.0, 0.0],"scale": [1.0, 1.0, 1.0],"rotate": [0.0, 0.0, 0.0]
    };
}

const clickTextureItem = function(e){
    console.log($(e.target));
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
    iDiv.addEventListener('click', clickCatalogItem)
    catalogItems.appendChild(iDiv);
};

const clickSketchSearchButton = function () {
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
            newCatalogItem(item);
        });
    });
};

const clickTextSearchButton = function () {
    while (catalogItems.firstChild) {
        catalogItems.firstChild.remove();
    }
    var search_url = "/query2nd?kw=" + document.getElementById("searchinput").value;
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

const clickAutoViewButton = function () {
    while (catalogItems.firstChild) {
        catalogItems.firstChild.remove();
    }
    let search_url = "/autoviewByID?origin=" + manager.renderManager.scene_json.origin;
    $.getJSON(search_url, function (data) {
        searchResults = data;
        searchResults.forEach(function (item) {
            let iDiv = document.createElement('div');
            iDiv.className = "catalogItem";
            iDiv.style.backgroundImage = `url(/autoviewimgs/${manager.renderManager.scene_json.origin}/${item.img})`;
            iDiv.addEventListener('click', clickAutoViewItem)
            catalogItems.appendChild(iDiv);
            $(iDiv).data('pcam', item);
        });
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
    const F = 0.65;
    let meta = $(e.target).data("meta");
    let image = floorPlanMapping.get(meta.identifier);
    let mappingDisplay = document.getElementById('mappingDisplay');
    let w, h;
    // make the image being displayed inside the window. 
    if($(window).height() >= $(window).width()){
        w = $(window).width() * F;
        h = w / (image.width / image.height);
    }else{
        h = $(window).height() * F;
        w = h / (image.height / image.width)
    }
    image.style.height = `${h}px`;
    image.style.width = `${w}px`;
    mappingDisplay.style.height = `${h}px`;
    mappingDisplay.style.width = `${w}px`;
    mappingDisplay.style.top = `${($(window).height()-h)/2}px`;
    mappingDisplay.style.left = `${($(window).width()-w)/2}px`;
    mappingDisplay.appendChild(image);
    mappingDisplay.style.display = 'inline-block';
}

const mappingLeave = function(e){
    let mappingDisplay = document.getElementById('mappingDisplay');
    mappingDisplay.firstChild.remove();
    mappingDisplay.style.display = 'none';
}

const mappingClick = function(e){
    autoViewPathPos.kill();
    autoViewPathTar.kill();
    let meta = $(e.target).data("meta");
    $.getJSON(`/getSceneJsonByID/${meta.identifier}`, function(result){
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
        searchResults.forEach(function (item) {
            let iDiv = document.createElement('div');
            let image = new Image();
            image.onload = function(){
                iDiv.style.width = `${$(window).width() * 0.10}px`;
                iDiv.style.height = `${$(window).width() * 0.10 / (image.width / image.height)}px`;
                let wh = getMappingWidthHeight(image);
                let w = wh[0], h = wh[1];
                $(`#grids-${item.identifier}`).css('height', `${h}px`);
                $(`#grids-${item.identifier}`).css('width', `${w}px`);
                $(`#grids-${item.identifier} .cell`).css('height', `${h/nrs}px`);
                $(`#grids-${item.identifier} .cell`).css('width', `${w/ncs}px`);
                $(`#grids-${item.identifier}`).css('top', `${($(window).height()-h)/2}px`);
                $(`#grids-${item.identifier}`).css('left', `${($(window).width()-w)/2}px`);
            };
            image.src = `/autoviewimgs/mapping/${item.identifier}`;
            iDiv.className = "catalogItem";
            iDiv.style.backgroundImage = `url(/autoviewimgs/mapping/${item.identifier})`;
            iDiv.style.backgroundSize = '100% 100%';
            iDiv.style.visibility = 'visible';
            // iDiv.addEventListener('mouseover', mappingHover);
            // iDiv.addEventListener('mouseout', mappingLeave);
            iDiv.addEventListener('click', mappingClick);
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
            let image = floorPlanMapping.get(meta.identifier);
            let wh = getMappingWidthHeight(image);
            let w = wh[0], h = wh[1];
            $(this).css('height', `${h/nrs}px`);
            $(this).css('width', `${w/ncs}px`);
            $(this).parent().css('height', `${h}px`);
            $(this).parent().css('width', `${w}px`);
        })
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
    // $("#autoView").click(clickAutoViewButton);
    $("#autoView").click(() => { socket.emit('autoView', getDownloadSceneJson(), onlineGroup); });
    $("#autoViewPath").click(clickAutoViewPath);
    $("#autoViewMapping").click(clickAutoViewMapping);
    $("#floorPlanbtn").click(() => {
        let origin = document.getElementById("searchinput").value;
        $.getJSON(`/getSceneJsonByID/${origin}`, function(result){
            socket.emit('sceneRefresh', result, onlineGroup);
        });
    })
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
    /*
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
    });*/
}