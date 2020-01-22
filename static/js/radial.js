var rad_items = [
    {className: 'glyphicon glyphicon-star', html: ''},
    {className: 'glyphicon glyphicon-move', html: ''},
    {className: 'glyphicon glyphicon-fullscreen', html: ''},
    {className: 'glyphicon glyphicon-resize-vertical', html: ''},
    {className: 'glyphicon glyphicon-repeat', html: ''},
    {className: 'glyphicon glyphicon-remove', html: ''}
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
    On_MOVE = true;
    toggles();
};

var radial_rotate_control = function (event) {
    mouse.rotateBase = new THREE.Vector2();
    mouse.rotateBase.set(mouse.x, mouse.y);
    On_ROTATE = true;
    toggles();
};

var radial_lift_control = function(event){
    On_LIFT = true;
    toggles();
};

var radial_scale_control = function(event){
    On_SCALE = true;
    toggles();
};

var radial_remove_control = function (event) {
    var roomId = INTERSECT_OBJ.userData.roomId;
    delete manager.renderManager.scene_json.rooms[roomId].objList
        [find_object_json(INTERSECT_OBJ)];
    manager.renderManager.scene_remove(userData => {
        return INTERSECT_OBJ.userData.key === userData.key;
    });
    toggles();
};

var radial_initialization = function(){
    r = document.getElementsByClassName('radial__container')[0];
    r.style.width = "0px";
    r.style.height = "0px";
    
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
