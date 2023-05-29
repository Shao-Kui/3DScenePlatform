let zoom = d3.zoom()
    .on('zoom', handleZoom);

function handleZoom(e) {
    d3.select('svg g')
        .attr('transform', e.transform);
}

function initZoom() {
    d3.select('svg')
        .call(zoom);
}

function update2() {
    d3.select('svg g')
        .selectAll('circle')
        .data(data)
        .join('circle')
        .attr('cx', function (d) { return d.x; })
        .attr('cy', function (d) { return d.y; })
        .attr('r', 3);
}

initZoom();
// updateData();
update();

const inputChart1 = document.getElementById('chart1Info');
let previousValue = inputChart1.value;
let currentValue = previousValue;


// import drawChart1 from './chart1.js';

setInterval(function () {

    if (inputChart1.value !== previousValue) {
        // console.log(inputChart1.value)
        currentValue = inputChart1.value;

        d3.select("#fig1").remove();
        let chart1 = d3.select("body").select("#charts").append("svg")
            .attr("width", width1)
            .attr("height", height1)
            .attr("id", "fig1")
        draw1();

        d3.select('#fig2').remove();
        let chart2 = d3.select("body").select("#charts").append("svg")
            .attr("width", width2)
            .attr("height", height2)
            .attr("id", "fig2")
        draw2(previousValue, currentValue);

        previousValue = currentValue;


    }
}, 100);