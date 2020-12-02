var rad_items = [
    {className: 'glyphicon glyphicon-star', html: ''},
    {className: 'glyphicon glyphicon-move', html: ''},
    {className: 'glyphicon glyphicon-fullscreen', html: ''}, // scale
    {className: 'glyphicon glyphicon-resize-vertical', html: ''},
    {className: 'glyphicon glyphicon-repeat', html: ''},
    {className: 'glyphicon glyphicon-remove', html: ''}
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
};

var radial_move_control = function (event) {
    datguiObjectFolderRemove(INTERSECT_OBJ); 
    On_MOVE = true;
    toggles();
};

var radial_rotate_control = function (event) {
    datguiObjectFolderRemove(INTERSECT_OBJ); 
    mouse.rotateBase = new THREE.Vector2();
    mouse.rotateBase.set(mouse.x, mouse.y);
    On_ROTATE = true;
    toggles();
};

var radial_lift_control = function(event){
    datguiObjectFolderRemove(INTERSECT_OBJ); 
    On_LIFT = true;
    toggles();
};

var radial_scale_control = function(event){
    datguiObjectFolderRemove(INTERSECT_OBJ); 
    On_SCALE = true;
    toggles();
};

var radial_remove_control = function (event) {
    removeIntersectObject();
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

    var radial_lift_button = document.getElementsByClassName("glyphicon-resize-vertical")[0];
    radial_lift_button.addEventListener('click', radial_lift_control);

    var radial_scale_button = document.getElementsByClassName("glyphicon-fullscreen")[0];
    radial_scale_button.addEventListener('click', radial_scale_control);

    var radial_latentspace_button = document.getElementsByClassName("glyphicon-star")[0];
    radial_latentspace_button.addEventListener('click', manager.renderManager.latent_space_click);
};
