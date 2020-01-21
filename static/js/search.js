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
    var search_url = "/query?kw=" + document.getElementById("searchinput").value;
    $.getJSON(search_url, function (data) {
        searchResults = data;
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
}