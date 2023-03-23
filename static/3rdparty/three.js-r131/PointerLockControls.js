/**
 * @author mrdoob / http://mrdoob.com/
 * @author Mugen87 / https://github.com/Mugen87
 */

THREE.PointerLockControls = function ( camera, domElement ) {

	var scope = this;

	this.domElement = domElement || document.body;
	this.isLocked = false;

	// camera.rotation.set( 0, 0, 0 );
    // var theta = 0;
    // var phi = Math.PI / 2;
    let drct = orbitControls.target.clone().sub(camera.position).normalize();
    var phi = Math.acos(drct.y);
    var theta = Math.atan2(drct.z, drct.x)

	var pitchObject = new THREE.Object3D();
	// pitchObject.add( camera );

	var yawObject = new THREE.Object3D();
	yawObject.position.y = 3;
	// yawObject.add( pitchObject );

	var PI_2 = Math.PI / 2;

	function onMouseMove( event ) {

		if (scope.isLocked === false) return;

		let movementX = event.movementX || event.mozMovementX || event.webkitMovementX || 0;
		let movementY = event.movementY || event.mozMovementY || event.webkitMovementY || 0;
		// yawObject.rotation.y -= movementX * 0.002;
		// pitchObject.rotation.x -= movementY * 0.002;
        theta += movementX * 0.001;
        phi += movementY * 0.001;
        phi = Math.max(phi, 0.01);
        phi = Math.min(phi, Math.PI - 0.01);
		// pitchObject.rotation.x = Math.max( - PI_2, Math.min( PI_2, pitchObject.rotation.x ) );
        orbitControls.target.x = Math.cos(theta) * Math.sin(phi) + camera.position.x
        orbitControls.target.z = Math.sin(theta) * Math.sin(phi) + camera.position.z
        orbitControls.target.y = Math.cos(phi) + camera.position.y

	}

	function onPointerlockChange() {

		if ( document.pointerLockElement === scope.domElement ) {

			scope.dispatchEvent( { type: 'lock' } );

			scope.isLocked = true;

		} else {

			scope.dispatchEvent( { type: 'unlock' } );

			scope.isLocked = false;

		}

	}

	function onPointerlockError() {

		console.error( 'THREE.PointerLockControls: Unable to use Pointer Lock API' );

	}

	this.connect = function () {

		document.addEventListener( 'mousemove', onMouseMove, false );
		document.addEventListener( 'pointerlockchange', onPointerlockChange, false );
		document.addEventListener( 'pointerlockerror', onPointerlockError, false );

	};

	this.disconnect = function () {

		document.removeEventListener( 'mousemove', onMouseMove, false );
		document.removeEventListener( 'pointerlockchange', onPointerlockChange, false );
		document.removeEventListener( 'pointerlockerror', onPointerlockError, false );

	};

	this.dispose = function () {

		this.disconnect();

	};

	this.getObject = function () {

		return yawObject;

	};

	this.getDirection = function () {

		// assumes the camera itself is not rotated

		var direction = new THREE.Vector3( 0, 0, - 1 );
		var rotation = new THREE.Euler( 0, 0, 0, 'YXZ' );

		return function ( v ) {
			// rotation.set( pitchObject.rotation.x, yawObject.rotation.y, 0 );
			// v.copy( direction ).applyEuler( rotation );
			// return v;
            v.x = Math.cos(theta) * Math.sin(phi);
            v.z = Math.sin(theta) * Math.sin(phi);
            v.y = Math.cos(phi);
            return v;
		};

	}();

	this.lock = function () {

		this.domElement.requestPointerLock();

	};

	this.unlock = function () {

		document.exitPointerLock();

	};

	// this.connect();

};

THREE.PointerLockControls.prototype = Object.create( THREE.EventDispatcher.prototype );
THREE.PointerLockControls.prototype.constructor = THREE.PointerLockControls;
