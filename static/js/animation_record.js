class AnimationSlider {
    static max = 4;
    static showPreviewAnim = true;
    static initStates;

    constructor(selector, props = {}) {
        this.defaultProps = {
            colors: {
                move: "rgb(210, 110, 127)",
                rotate: "rgb(25, 118, 210)",
                transform: "rgb(67, 210, 89)",
                rail: "rgba(25, 118, 210, 0.4)"
            },
            pointRadius: 10,
            fontSize: 15
        };

        this.allProps = {
            ...this.defaultProps,
            ...props,
            colors: {
                ...this.defaultProps.colors,
                ...props.colors
            }
        };

        this.container = this.initContainer(selector);

        this.rail = this.initRail();
        this.container.appendChild(this.rail);

        this.tooltip = this.initTooltip();
        this.container.appendChild(this.tooltip);

        this.timeline = this.initTimeline();

        this.points = this.initPoints();

        this.pointMouseupHandler = this.pointMouseupHandler.bind(this);
        this.pointMouseMoveHandler = this.pointMouseMoveHandler.bind(this);
        this.selectedPoint = undefined;

        this.changeHandlers = [];

        let object = manager.renderManager.scene_json.rooms[0].objList.filter(obj=>obj.sforder === this.allProps.sforder)[0];
        this.allProps.objectKey = object.key;

        return this;
    }

    initContainer(selector) {
        const container = document.createElement("div");
        container.classList.add("animationslider-container", "my-2");
        container.style.height = this.allProps.pointRadius * 2 + 15 + "px";
        let e = document.getElementById(selector);
        e.appendChild(container);
        let eStyle = getComputedStyle(e);
        this.width = Math.floor(parseFloat(eStyle.width) - parseFloat(eStyle.paddingLeft) - parseFloat(eStyle.paddingRight));
        return container;
    }

    /**
     * Initialize Rail
     */
    initRail() {
        const rail = document.createElement("span");
        rail.classList.add("animationslider-rail");
        rail.style.background = this.allProps.colors.rail;
        rail.style.height = 1 + "px";
        rail.style.top = this.allProps.pointRadius * 2 + "px";
        return rail;
    }

    /**
     * Initialize Timeline
     */
    initTimeline() {
        for (let i = 0; i < 5; i++) {
            const text = document.createElement("span");
            text.innerText = i * AnimationSlider.max / 4;
            text.style.fontSize = this.allProps.fontSize + 'px';
            text.style.top = this.allProps.pointRadius * 2 + 2 + "px";
            text.style.position = 'absolute';
            text.style.left = (25 * i) + '%';
            text.style.transform = 'translateX(-50%)';
            this.container.appendChild(text);
        }
    }

    initPoints() {
        return this.allProps.animations.map((seq, seqId) =>
            seq.map((anim) => this.initPoint(anim, seqId))
        );
    }

    initPoint(anim, seqId) {
        const point = document.createElement("span");
        point.classList.add("animationslider-point");

        anim.t[0] = this.round(anim.t[0], 1);
        anim.t[1] = this.round(anim.t[1], 1);
        anim.duration = anim.t[1] - anim.t[0];
        if (anim.duration < 0.1) {
            anim.duration = 0.1;
            anim.t[1] = anim.t[0] + anim.duration;
        }
        point.anim = anim;
        point.seqId = seqId;
        point.style.width = (anim.duration / AnimationSlider.max) * 100 + "%";
        point.style.height = this.allProps.pointRadius * 2 + "px";
        let t = (anim.t[0] + anim.t[1]) / 2;
        let pos = (t / AnimationSlider.max) * 100;
        point.style.left = pos + "%";
        let pointColors = this.allProps.colors[anim.action];
        point.style.background = pointColors;

        point.addEventListener("mousedown", e =>
            this.pointClickHandler(e)
        );
        point.addEventListener("mouseover", e =>
            this.pointMouseOverHandler(e)
        );
        point.addEventListener("mouseout", e =>
            this.pointMouseOutHandler(e)
        );
        point.addEventListener("contextmenu", e =>
            this.pointContextMenuHandler(e)
        );

        this.container.appendChild(point)
        return point;
    }

    /**
     * Initialize tooltip
     */
    initTooltip() {
        const tooltip = document.createElement("span");
        tooltip.classList.add("animationslider-tooltip");
        tooltip.style.fontSize = this.allProps.pointRadius + "px";
        return tooltip;
    }

    showTooltip(targetPoint) {
        this.tooltip.style.left = targetPoint.style.left;
        let animation = targetPoint.anim;
        this.tooltip.textContent = `${animation.action}\r\n[${animation.t[0]}-${animation.t[1]}]`;
    }

    /**
     * Stop point moving on mouse up
     */
    pointMouseupHandler() {
        this.changeHandlers.forEach(func => func(this.allProps.animations));
        this.selectedPoint.style.boxShadow = "none";
        this.selectedPoint = undefined;
        this.tooltip.style.transform = "translate(-50%, -60%) scale(0)";
        document.removeEventListener("mouseup", this.pointMouseupHandler);
        document.removeEventListener("mousemove", this.pointMouseMoveHandler);
    }

    /**
     * Start point moving on mouse move
     * @param {Event} e
     */
    pointMouseMoveHandler(e) {
        let mousePosition = this.getMouseRelativePosition(e.pageX);
        let t = mousePosition / this.container.offsetWidth * AnimationSlider.max;
        let anim = this.selectedPoint.anim;
        let prev = 0, next = AnimationSlider.max;
        let seq = this.allProps.animations.flat();
        let animIdx = seq.indexOf(anim);
        if (animIdx > 0) prev = seq[animIdx - 1].t[1];
        if (animIdx !== -1 && animIdx + 1 < seq.length) next = seq[animIdx + 1].t[0];
        let halfDuration = anim.duration / 2;
        if (t < prev + halfDuration) {
            t = prev + halfDuration;
        } else if (t > next - halfDuration) {
            t = next - halfDuration;
        }
        let t0 = this.round(t - halfDuration, 1);
        anim.t[0] = t0;
        anim.t[1] = this.round(t0 + anim.duration, 1);
        let newPosition = t / AnimationSlider.max * 100;
        this.selectedPoint.style.left = newPosition + "%";
        this.showTooltip(this.selectedPoint);
    }

    round(value, precision) {
        let multiplier = Math.pow(10, precision || 0);
        return Math.round(value * multiplier) / multiplier;
    }

    pointClickHandler(e) {
        e.preventDefault();
        this.selectedPoint = e.target;
        document.addEventListener("mouseup", this.pointMouseupHandler);
        document.addEventListener("mousemove", this.pointMouseMoveHandler);
    }

    previewAnim(targetPoint) {
        if (!AnimationSlider.showPreviewAnim) return;
        let anim = targetPoint.anim;
        anim.isPreviewing = true;
        let seq = this.allProps.animations.flat();
        let animIdx = seq.indexOf(anim);
        let object3d = manager.renderManager.instanceKeyCache[this.allProps.objectKey];
        let initP, initR, initS;
        for (let i = animIdx-1; i >= 0; i--) {
            if (initP !== undefined && initR !== undefined && initS !== undefined) break;
            if (initP === undefined && seq[i].action === 'move') initP = seq[i].p2;
            if (initR === undefined && seq[i].action === 'rotate') initR = seq[i].r2;
            if (initS === undefined && seq[i].action === 'transform') initS = seq[i].s2;
        }
        initP = initP ?? AnimationSlider.initStates[this.allProps.sforder].p;
        initR = initR ?? AnimationSlider.initStates[this.allProps.sforder].r;
        initS = initS ?? AnimationSlider.initStates[this.allProps.sforder].s;
        object3d.position.set(initP[0], object3d.position.y, initP[2]);
        object3d.rotation.set(0, initR, 0);
        objectToAction(object3d, initS, 0);

        if (anim.action === 'move') {
            setTimeout(transformObject3DOnly, 100, this.allProps.objectKey, [anim.p2[0], anim.p2[1], anim.p2[2]], 'position', true, anim.t[1] - anim.t[0], 'none');
        }
        if (anim.action === 'rotate') {
            let r = [0, atsc(anim.r2), 0];
            standardizeRotate(r, [0, atsc(anim.r1), 0]);
            object3d.rotation.set(0, atsc(anim.r1), 0);
            setTimeout(transformObject3DOnly, 100, this.allProps.objectKey, r, 'rotation', true, anim.t[1] - anim.t[0], 'none');
        }
        if (anim.action === 'transform') {
            setTimeout(objectToAction, 100, object3d, anim.s2, anim.t[1] - anim.t[0]);
        }
    }

    endPreviewAnim(targetPoint) {
        if (!AnimationSlider.showPreviewAnim) return;
        delete targetPoint.anim.isPreviewing;
        let seq = this.allProps.animations.flat();
        if (seq.filter(anim=>anim.isPreviewing).length > 0) return;
        let object3d = manager.renderManager.instanceKeyCache[this.allProps.objectKey];
        let initP, initR, initS;
        for (let i = seq.length-1; i >= 0; i--) {
            if (initP !== undefined && initR !== undefined && initS !== undefined) break;
            if (initP === undefined && seq[i].action === 'move') initP = seq[i].p2;
            if (initR === undefined && seq[i].action === 'rotate') initR = seq[i].r2;
            if (initS === undefined && seq[i].action === 'transform') initS = seq[i].s2;
        }
        initP = initP ?? AnimationSlider.initStates[this.allProps.sforder].p;
        initR = initR ?? AnimationSlider.initStates[this.allProps.sforder].r;
        initS = initS ?? AnimationSlider.initStates[this.allProps.sforder].s;
        object3d.position.set(initP[0], object3d.position.y, initP[2]);
        object3d.rotation.set(0, initR, 0);
        objectToAction(object3d, initS, 0);
    }

    pointMouseOverHandler(e) {
        let targetPoint = e.target;
        if (!this.selectedPoint) {
            const transparentColor = AnimationSlider.addTransparencyToColor(targetPoint.style.backgroundColor, 16);
            targetPoint.style.boxShadow = `0px 0px 0px ${Math.floor(this.allProps.pointRadius / 1.5)}px ${transparentColor}`;
        }
        this.tooltip.style.transform = "translate(-50%, -60%) scale(1)";
        this.showTooltip(targetPoint);
        this.previewAnim(targetPoint);
    }

    pointContextMenuHandler(e) {
        e.preventDefault();
        let targetPoint = e.target;
        console.log('Delete: ', targetPoint.anim);
        const index = this.allProps.animations[targetPoint.seqId].indexOf(targetPoint.anim);
        if (index > -1) {
            this.allProps.animations[targetPoint.seqId].splice(index);
            for (let i = this.points[targetPoint.seqId].length-1; i >= index; i--) 
                this.points[targetPoint.seqId][i].remove();
            this.points[targetPoint.seqId].splice(index);
        }
        setTimeout(() => { this.endPreviewAnim(e.target); }, 100);
    }

    /**
     * Add transparency for rgb, rgba or hex color
     * @param {string} color
     * @param {number} percentage
     */
    static addTransparencyToColor(color, percentage) {
        if (color.startsWith("rgba")) {
            return color.replace(/(\d+)(?!.*\d)/, percentage + "%");
        }

        if (color.startsWith("rgb")) {
            let newColor = color.replace(/(\))(?!.*\))/, `, ${percentage}%)`);
            return newColor.replace("rgb", "rgba");
        }

        if (color.startsWith("#")) {
            return color + percentage.toString(16);
        }

        return color;
    }

    static setInitStates() {
        AnimationSlider.initStates = manager.renderManager.scene_json.rooms[currentRoomId].objList
            .filter(o => o.sforder !== undefined)
            .sort((a, b) => a.sforder - b.sforder)
            .map(o => {
                let object3d = manager.renderManager.instanceKeyCache[o.key];
                return {
                    p: [object3d.position.x, object3d.position.y, object3d.position.z], 
                    r: object3d.rotation.y, 
                    s: object3d.userData.json.startState
                };
            });
        console.log(AnimationSlider.initStates);
    }

    pointMouseOutHandler(e) {
        if (!this.selectedPoint) {
            let targetPoint = e.target;
            targetPoint.style.boxShadow = "none";
            this.tooltip.style.transform = "translate(-50%, -60%) scale(0)";
        }
        setTimeout(() => { this.endPreviewAnim(e.target); }, 100);
    }

    /**
     * Get mouse position relatively from containers left position on the page
     */
    getMouseRelativePosition(pageX) {
        return pageX - this.container.offsetLeft;
    }

    /**
     * Register onChange callback to call it on slider move end passing all the present values
     */
    onChange(func) {
        if (typeof func !== "function") {
            throw new Error("Please provide function as onChange callback");
        }
        this.changeHandlers.push(func);
        return this;
    }

    update() {
        this.allProps.animations.forEach((seq, seqId) => {
            for (let i = this.points[seqId].length; i < seq.length; i++) {
                let point = this.initPoint(seq[i], seqId);
                this.points[seqId].push(point);
            }
        });
    }
}

const downloadJson = (data, fileName) => {
    var downloadAnchorElem = document.getElementById('downloadAnchorElem');
    downloadAnchorElem.setAttribute("href", "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(data)));
    downloadAnchorElem.setAttribute("download", `${fileName}.json`);
    downloadAnchorElem.click();
}

const updateAnimationRecordDiv = (sliderMax = undefined) => {
    if ($("#sidebarSelect").val() !== "AnimationRecordDiv") {
        $("#sidebarSelect").val("AnimationRecordDiv").change();
    }
    $("#AnimationRecordDiv").empty();
    let animaMax = Math.max(sliderMax || 4, 4);
    currentSeqs.forEach((seqs) => {
        seqs.forEach((seq) => {
            seq.forEach((anim) => {
                animaMax = Math.max(animaMax, anim.t[1]);
            });
        });
    });
    AnimationSlider.max = Math.ceil(animaMax / 4) * 4;
    animaSliders = {};
    let animaRecDiv = document.getElementById("AnimationRecordDiv");
    let previewButton = document.createElement("button");
    previewButton.innerHTML = "Preview";
    previewButton.classList.add("btn", "btn-primary", "mx-2");
    previewButton.addEventListener('click', (e) => {
        sceneTransformTo(currentSeqs);
    });
    animaRecDiv.appendChild(previewButton);
    let finishButton = document.createElement("button");
    finishButton.innerHTML = "Finish";
    finishButton.classList.add("btn", "btn-primary", "mx-2");
    finishButton.addEventListener('click', (e) => {
        console.log(currentSeqs);
        downloadJson(currentSeqs, onlineGroup);
    });
    animaRecDiv.appendChild(finishButton);
    manager.renderManager.scene_json.rooms[0].objList.sort((a, b) => a.sforder - b.sforder);
    manager.renderManager.scene_json.rooms[0].objList.forEach(o => {
        if (o.format === 'glb' && o.sforder !== undefined) {
            let slider = new AnimationSlider("AnimationRecordDiv", { sforder: o.sforder, animations: currentSeqs[o.sforder] });
            slider.container.id = `sforder${o.sforder}`;
            animaSliders[o.sforder] = slider;
            let label = document.createElement("label");
            label.innerText = o.modelId;
            label.style.fontSize = '18px';
            label.classList.add("mb-3");
            animaRecDiv.appendChild(label);
        }
    });
}

const updateAnimationSlider = (index) => {
    let animaMax = 0;
    currentSeqs[index].forEach((seq) => {
        seq.forEach((anim) => {
            animaMax = Math.max(animaMax, anim.t[1]);
        });
    });
    if (animaMax > AnimationSlider.max) {
        updateAnimationRecordDiv(Math.ceil(animaMax / 4) * 4);
    } else {
        animaSliders[index].update();
    }
}

const AnimationRecordDivWheelHandler = (e) => {
    return;
};