(function(g){
	var options = {
		// True if the first element is a button
		button: false,
		// 360 degrees = circle
		deg: 360,
		// left to right = +180
		direction: 180,
		// Container dimensions
		container: {
			width: '100px',
			height: '100px'
		}
	};
	
	var classes = {
		container: 'radial__container',
		button: 'radial__button',
		item: 'radial__item',
	};
	
	var el = {
		className: ' ',
		disabled: false,
		href: null,
		html: '',
		target: '_blank',
		index: 0,
		_alfa: 0,
	};
	
	// Some functions
	var template = function(item) {
		var element = document.createElement('span');
		if(item.href) {
			element = document.createElement('a')
			element.href = item.href;
			element.target = item.target;
		}
		if(item.isButton) {
			element.className = item.className + ' ' + classes.button;
		}else{
			element.className = item.className + ' ' + classes.item;
		}
		element.innerHTML = item.html;
		element.style.position = 'absolute';
		element.style.top = Math.round(item._top) + 'px';
		element.style.left = Math.round(item._left) + 'px';
		element.style.zIndex = item.index;
		
		return element;
	};
	
	var createContainer = function(options) {
		var container = document.createElement('div');
		container.style.width = options.width;
		container.style.height = options.height;
		container.style.position = 'relative';
		container.className = classes.container;
		
		return container;
	};
	
	var extendOpt = function(obj, source){
		var tObj = {};
		for (var prop in obj) {
			tObj[prop] = (source[prop] !== undefined) ? source[prop] : obj[prop];
		}
		
		return tObj;
	};
	
	var extendOptions = function(arr) {
		var tArr = [];
		for (var i = 0; i< arr.length; i++) {
			tArr[i] = extendOpt(el, arr[i]);
		}
		
		return tArr;
	};
	
	var radians = function(degrees) {
	  return degrees * Math.PI / 180;
	};
	
	var getPosition = function(container, item, direction) {
		var height = Math.round(parseInt(container.style.height)/2);
		var width =  Math.round(parseInt(container.style.width)/2);
		if(item._alfa === null) {
			return {
				top: height,
				left: width
			};
		}
		
		var r = radians(item._alfa + direction);
		return {
			top: height + Math.sin(r) * height,
			left: width + Math.cos(r) * width
		};
	}
	
	// Class
	var Radial = function(items, newOptions, degrees) {
		this.options = extendOpt(options, newOptions || {});
		this._items = extendOptions(items);
		if(!(degrees===undefined)){ //if it is NOT undefined
			for(var i = 0; i<this._items.length; i++){
				if(!(degrees[i]===undefined)){
					this._items[i]._alfa = degrees[i];
				}
				else{
					this._items[i]._alfa = 0;
				}
			}
		}
		this._container = createContainer(this.options.container);
		this.calc();
	};
	
	
	Radial.prototype = {
		
		/**
		* Get single item
		* @param {Number} index
		* @return {Object} item
		*/
		get: function(index){
			return (index > -1) ? this._items[index] : this._items;
		},
		
		/**
		* Get alfa of an item
		* @param {Object} / {Number} item
		* @return {Number} alfa
		*/
		getAlfa: function(item) {
			if(typeof item === 'number') {
				item = this.get(item);
			}
			
			return item._alfa;
		},
		
		/**
		* Get Items length
		* @return {Number} length
		*/
		count: function(){
			return this._items.length;
		},
		
		/**
		* Add new Items to the list
		* @param {Array} items
		* @return void
		*/
		add: function(items) {
			if(items.length) {
				this._items = this._items.concat(extendOptions(items));
			}else{
				this._items.push(extendOpt(el, items));
			}
			
			this.calc();
		},
		
		/**
		* Remove item from list
		* @param {Number} index
		* @return void
		*/
		remove: function(index) {
			this._items.splice(index,1);
			this.calc();
		},
		
		/**
		* Calc correct angle to each element
		* @return void
		*/
		calc: function() {
			var count = (this.options.button) ? this.count()-1 : this.count();
			var newcount = count;
			var anglesaccountedfor = 0;
			for(var k = 0; k<this._items.length; k++){
				anglesaccountedfor += this._items[k]._alfa;
				if(this._items[k]._alfa != 0 && this.options.button){
					newcount--;
				}
			}
			if((anglesaccountedfor > this.options.deg) || (anglesaccountedfor > 360)){
				for(var k = 0; k<this._items.length; k++){
					this._items[k]._alfa = 0; //if the angles don't add up then reset all values to default
					anglesaccountedfor = 0;
					newcount = count;
				}
			}
			var alfa = 0;
			if(newcount != 0){
				alfa = (this.options.deg > 359) ? (360-anglesaccountedfor)/newcount : (this.options.deg-anglesaccountedfor)/(newcount-1);
			}
			else{
				alfa = (this.options.deg > 359) ? (360-anglesaccountedfor)/count : (this.options.deg-anglesaccountedfor)/(count-1);
			}
			var i = -alfa;
			var j = 0;
			if(this.options.button) {
				this._items[0]._alfa = null;
				this._items[0].isButton = true;
				j++;
				count++;
			}
			for(j; j < this._items.length; j++) {
				if(newcount != 0){
					var newalfa = (this._items[j]._alfa == 0) ? Math.round(i + alfa) : Math.round(i + this._items[j]._alfa);
					this._items[j]._alfa = newalfa;
				}
				else{
					var newalfa = Math.round(i + alfa);
					this._items[j]._alfa += newalfa;
				}
				i = newalfa;
			}
			
		},
		
		/**
		* Render radial menu
		* @return {DOMElement} container
		*/
		render: function() {
			this._container.innerHTML = '';
			for(var i = 0; i < this.count(); i++) {
				var calculated = getPosition(this._container, this._items[i], this.options.direction);
				this._items[i]._top = calculated.top;
				this._items[i]._left = calculated.left;
				this._container.appendChild(template(this._items[i]));
			}
			return this._container;
		},
		
		/**
		* Show animation, be free to override 'show function'
		* @return void
		*/
		show: function() {
			var childs = this._container.getElementsByClassName(classes.item);
			for(var i = 0; i < childs.length; i++) {
				childs[i].classList.add("show");
			}
		},

		/**
		* Hide animation, be free to override 'hide function'
		* @return void
		*/
		hide: function() {
			var childs = this._container.getElementsByClassName(classes.item);
			for(var i = 0; i < childs.length; i++) {
				childs[i].classList.remove("show");
			}
		},

		/**
		* Toggle between show and hide state
		* @return void
		*/
		toggle: function() {
			if(this.visible) {
				this.hide();
				this.visible = false;
			}else{
				this.show();
				this.visible = true;
			}
		}
	};
	
	g.Radial = Radial;
	
})(this);
