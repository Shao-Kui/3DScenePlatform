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

const clickAutoViewItem = function(e){
    let pcam = $(e.target).data("pcam");
    gsap.to(camera.position, {
        duration: 1,
        x: pcam.origin[0],
        y: pcam.origin[1],
        z: pcam.origin[2]
    });
    gsap.to(orbitControls.target, {
        duration: 1,
        x: pcam.target[0],
        y: pcam.target[1],
        z: pcam.target[2]
    });
    gsap.to(camera.up, {
        duration: 1,
        x: 0,
        y: 1,
        z: 0
    });
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

const clickAutoViewPath = function(){
    let search_url = "/autoViewPath?origin=" + manager.renderManager.scene_json.origin;
    $.getJSON(search_url, function (data) {
        let autoViewPathPos = gsap.timeline({repeat: 0});
        let autoViewPathTar = gsap.timeline({repeat: 0});
        data.forEach(function (datum) {
            autoViewPathPos.to(camera.position, {
                duration: 1,
                x: datum.origin[0],
                y: datum.origin[1],
                z: datum.origin[2],
                ease: "none"
            });
            autoViewPathTar.to(orbitControls.target, {
                duration: 1,
                x: datum.target[0],
                y: datum.target[1],
                z: datum.target[2],
                ease: "none"
            });
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
    $("#autoView").click(clickAutoViewButton);
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