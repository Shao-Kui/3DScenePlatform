var rad_items = [
    {className: 'glyphicon glyphicon-star', html: ''},
    {className: 'glyphicon glyphicon-move', html: ''},
    {className: 'glyphicon glyphicon-plus', html: ''},
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
}

var radial_remove_control = function (event) {
    var roomId = INTERSECT_OBJ.userData.roomId;
    delete manager.renderManager.scene_json.rooms[roomId].objList
        [find_object_json(INTERSECT_OBJ)];
    manager.renderManager.scene_remove(userData => {
        return INTERSECT_OBJ.userData.key === userData.key;
    });
    toggles();
};
