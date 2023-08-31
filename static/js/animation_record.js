class AnimationSlider {
    static max = 4;

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
        const text1 = document.createElement("span");
        text1.innerText = '0';
        text1.style.fontSize = this.allProps.fontSize + 'px';
        text1.style.top = this.allProps.pointRadius * 2 + 2 + "px";
        text1.style.position = 'absolute';
        text1.style.left = '0%';
        text1.style.transform = 'translateX(-50%)';
        this.container.appendChild(text1);

        const text2 = document.createElement("span");
        text2.innerText = AnimationSlider.max / 4;
        text2.style.fontSize = this.allProps.fontSize + 'px';
        text2.style.top = this.allProps.pointRadius * 2 + 2 + "px";
        text2.style.position = 'absolute';
        text2.style.left = '25%';
        text2.style.transform = 'translateX(-50%)';
        this.container.appendChild(text2);

        const text3 = document.createElement("span");
        text3.innerText = AnimationSlider.max / 2;
        text3.style.fontSize = this.allProps.fontSize + 'px';
        text3.style.top = this.allProps.pointRadius * 2 + 2 + "px";
        text3.style.position = 'absolute';
        text3.style.left = '50%';
        text3.style.transform = 'translateX(-50%)';
        this.container.appendChild(text3);

        const text4 = document.createElement("span");
        text4.innerText = AnimationSlider.max * 3 / 4;
        text4.style.fontSize = this.allProps.fontSize + 'px';
        text4.style.top = this.allProps.pointRadius * 2 + 2 + "px";
        text4.style.position = 'absolute';
        text4.style.left = '75%';
        text4.style.transform = 'translateX(-50%)';
        this.container.appendChild(text4);

        const text5 = document.createElement("span");
        text5.innerText = AnimationSlider.max;
        text5.style.fontSize = this.allProps.fontSize + 'px';
        text5.style.top = this.allProps.pointRadius * 2 + 2 + "px";
        text5.style.position = 'absolute';
        text5.style.left = '100%';
        text5.style.transform = 'translateX(-50%)';
        this.container.appendChild(text5);
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
        let halfDuration = anim.duration / 2;
        if (t < halfDuration) {
            t = halfDuration;
        } else if (t > AnimationSlider.max - halfDuration) {
            t = AnimationSlider.max - halfDuration;
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

    pointMouseOverHandler(e) {
        let targetPoint = e.target;
        if (!this.selectedPoint) {
            const transparentColor = AnimationSlider.addTransparencyToColor(targetPoint.style.backgroundColor, 16);
            targetPoint.style.boxShadow = `0px 0px 0px ${Math.floor(this.allProps.pointRadius / 1.5)}px ${transparentColor}`;
        }
        this.tooltip.style.transform = "translate(-50%, -60%) scale(1)";
        this.showTooltip(targetPoint);
    }

    pointContextMenuHandler(e) {
        let targetPoint = e.target;
        console.log('Delete: ', targetPoint.anim);
        const index = this.allProps.animations[targetPoint.seqId].indexOf(targetPoint.anim);
        if (index > -1) {
            this.allProps.animations[targetPoint.seqId].splice(index, 1);
        }
        targetPoint.remove();
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

    pointMouseOutHandler(e) {
        if (!this.selectedPoint) {
            let targetPoint = e.target;
            targetPoint.style.boxShadow = "none";
            this.tooltip.style.transform = "translate(-50%, -60%) scale(0)";
        }
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
    manager.renderManager.scene_json.rooms[0].objList.sort((a, b) => a.sforder - b.sforder);
    manager.renderManager.scene_json.rooms[0].objList.forEach(o => {
        if (o.format === 'glb' && o.sforder !== undefined) {
            let slider = new AnimationSlider("AnimationRecordDiv", { animations: currentSeqs[o.sforder] });
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
