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
            iDiv.setAttribute('coarseSemantic', item.semantic);
            iDiv.addEventListener('click', clickCatalogItem)
            catalogItems.appendChild(iDiv);
        })
    });
};

var clickTextSearchButton = function () {
    while (catalogItems.firstChild) {
        catalogItems.firstChild.remove();
    }
    var search_url = "/query2nd?kw=" + document.getElementById("searchinput").value;
    $.getJSON(search_url, function (data) {
        searchResults = data;
        searchResults.forEach(function (item) {
            var iDiv = document.createElement('div');
            iDiv.className = "catalogItem";
            iDiv.style.backgroundImage = "url(" + item.thumbnail + ")";
            iDiv.setAttribute('objectID', item.id);
            iDiv.setAttribute('objectName', item.name);
            iDiv.setAttribute('modelId', item.name);
            iDiv.setAttribute('coarseSemantic', item.semantic);
            iDiv.setAttribute('semantic', item.semantic);
            iDiv.addEventListener('click', clickCatalogItem)
            catalogItems.appendChild(iDiv);
        })
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

const clickAutoViewItem = function(e){
    clickAutoViewItemDuration = 1;
    let pcam = $(e.target).data("pcam");
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

const AUTOVIEWPATHSPEED = 1.;
const clickAutoViewPath = function(){
    let search_url = "/autoViewPath?origin=" + manager.renderManager.scene_json.origin;
    $.getJSON(search_url, function (data) {
        let autoViewPathPos = gsap.timeline({repeat: 0});
        let autoViewPathTar = gsap.timeline({repeat: 0});
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

var searchPanelInitialization = function(){
    $("#searchbtn").click(clickTextSearchButton);
    // $("#autoView").click(clickAutoViewButton);
    $("#autoView").click(() => {
        socket.emit('autoView', getDownloadSceneJson(), onlineGroup); 
    });
    $("#autoViewPath").click(clickAutoViewPath);
    /*$("#sketchsearchbtn").click(clickSketchSearchButton);
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
    });*/
}