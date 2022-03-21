var rad_items = [
    {className: 'glyphicon glyphicon-tower', html: ''},
    {className: 'glyphicon glyphicon-star', html: ''},
    {className: 'glyphicon glyphicon-move', html: ''},
    //{className: 'glyphicon glyphicon-fullscreen', html: ''}, // scale
    //{className: 'glyphicon glyphicon-resize-vertical', html: ''},
    {className: 'glyphicon glyphicon-repeat', html: ''},
    {className: 'glyphicon glyphicon-remove', html: ''},
    {className: 'glyphicon glyphicon-flag', html: ''}
];

var rad_scale_items = [
    {className: 'glyphicon glyphicon-xScale', html: 'X'},
    {className: 'glyphicon glyphicon-yScale', html: 'Y'},
    {className: 'glyphicon glyphicon-zScale', html: 'Z'}, 
];

var rad_options = {
    button: false,
    deg: 360,
    direction: 180,
    container: {
        width: '100px',
        height: '100px'
    }
}

var toggles = function () {
    radial.toggle();
    isToggle = !isToggle;
    duplicateTimes = 1;
};

const radial_mage_control = function(event){
    genFloorPlanWallTensors();
    loadSingleObjectPrior(INTERSECT_OBJ.userData.modelId);
    On_MAGEMOVE = true;
    transformControls.detach();
    toggles();
}

const radial_cgseries_control = function(event){
    loadCGSeries(INTERSECT_OBJ.userData.modelId);
    On_CGSeries = true;
    transformControls.detach();
    toggles();
}

var radial_move_control = function (event) {
    timeCounter.moveStart = moment();
    datguiObjectFolderRemove(INTERSECT_OBJ); 
    On_MOVE = true;
    transformControls.detach();
    toggles();
};

var radial_rotate_control = function (event) {
    timeCounter.rotateStart = moment();
    datguiObjectFolderRemove(INTERSECT_OBJ); 
    mouse.rotateBase = new THREE.Vector2();
    mouse.rotateBase.set(mouse.x, mouse.y);
    mouse.lastOrient = INTERSECT_OBJ.rotation.y;
    On_ROTATE = true;
    transformControls.detach();
    toggles();
};

var radial_lift_control = function(event){
    datguiObjectFolderRemove(INTERSECT_OBJ); 
    On_LIFT = true;
    transformControls.detach();
    toggles();
};

var radial_scale_control = function(event){
    datguiObjectFolderRemove(INTERSECT_OBJ); 
    On_SCALE = true;
    transformControls.detach();
    toggles();
};

const radial_remove_control = function (event) {
    removeIntersectObject();
    transformControls.detach();
    toggles();
};

var radial_main_object_control = function (event) {
    MAIN_OBJ = INTERSECT_OBJ;
    let mainObjId = MAIN_OBJ.userData.modelId;
    $("#mainObjDiv").text(`Main Object: ${MAIN_OBJ.userData.json.modelId} (${MAIN_OBJ.userData.coarseSemantic})`);
    if (USED_OBJ_LIST[mainObjId] == undefined)
        $('#usedObjDiv').text('Used Object: ');
    else
        $('#usedObjDiv').text(`Used Object: ${USED_OBJ_LIST[mainObjId].filter((v, idx)=>{ return v != mainObjId}).join(', ')}`)
    transformControls.detach();
    toggles();
};

var radial_initialization = function(){
    radial = new Radial(rad_items, rad_options);
    menu = document.getElementById('menu2');
    menu.appendChild(radial.render());

    radial_scale = new Radial(rad_scale_items, rad_options);
    document.getElementById('menu_scale').appendChild(radial_scale.render())

    document.getElementsByClassName('radial__container').forEach(r => {
        r.style.width = "0px";
        r.style.height = "0px";
    }); 
    
    //Config radial logic
    var radial_move_button = document.getElementsByClassName("glyphicon-move")[0];
    radial_move_button.addEventListener('click', radial_move_control);

    var radial_rotate_button = document.getElementsByClassName("glyphicon-repeat")[0];
    radial_rotate_button.addEventListener('click', radial_rotate_control);

    var radial_remove_button = document.getElementsByClassName("glyphicon-remove")[0];
    radial_remove_button.addEventListener('click', radial_remove_control);

    // var radial_lift_button = document.getElementsByClassName("glyphicon-resize-vertical")[0];
    // radial_lift_button.addEventListener('click', radial_lift_control);

    // var radial_scale_button = document.getElementsByClassName("glyphicon-fullscreen")[0];
    // radial_scale_button.addEventListener('click', radial_scale_control);

    var radial_latentspace_button = document.getElementsByClassName("glyphicon-star")[0];
    radial_latentspace_button.addEventListener('click', radial_mage_control);

    document.getElementsByClassName("glyphicon-tower")[0].addEventListener('click', radial_cgseries_control);
    
    var radial_main_object_button = document.getElementsByClassName("glyphicon-flag")[0];
    radial_main_object_button.addEventListener('click', radial_main_object_control);

    radial.show = function() {
        var radial_main_object_button = document.getElementsByClassName("glyphicon-flag")[0];
        if (INTERSECT_OBJ == MAIN_OBJ) {
            radial_main_object_button.style.color = 'yellow';
        } else {
            radial_main_object_button.style.color = 'white';
        }
        var childs = this._container.getElementsByClassName('radial__item');
        for(var i = 0; i < childs.length; i++) {
            childs[i].classList.add("show");
        }
    }
};
