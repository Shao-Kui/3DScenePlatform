// The following code is the typical routine of my d3.js code. 
const arcGenerator = d3.arc()
    .innerRadius(30).outerRadius(130);
const arcTween = function (d) {
    var init_startAngle = 0;
    var init_endAngle = 0;
    var interpolate_start = d3.interpolate(init_startAngle, d.startAngle);
    var interpolate_end = d3.interpolate(init_endAngle, d.endAngle);
    return function (t) {
        d.startAngle = interpolate_start(t);
        d.endAngle = interpolate_end(t);
        return arcGenerator(d)
    }
};

let width1 = 600;
let height1 = 400;

// let pic_index=0



let draw_array = [1]


const draw1 = (data_dir) => {

    // console.log(data_dir)

    const container = d3.select('#fig1');
    const boundingrect=container.node().getBoundingClientRect();
    const width = boundingrect.width;
    const height = boundingrect.height;
    const chart = container;
    const margin = { top: 30, right: 30, bottom: 30, left: 30 };
    container.append('g')
        .attr('transform', `translate(${margin.left}, ${margin.top})`)
    // const xValue = d => d.globalsale;
    // const yValue = d => d.platform;
    // const xScale = d3.scaleLinear();
    // const yScale = d3.scaleBand();

    // const data_dir = document.getElementById('chart1Info').value;
    // console.log(data_dir)

    d3.json(data_dir).then(d => {
        let data;
        if (d.evaluation == null) data = d;
        else data = d.evaluation;
        const pie = d3.pie().value(d => d.value);
        const arcData = pie(data);
        const path = d3.arc().innerRadius(30).outerRadius(130);
        const color = d3.scaleOrdinal()
            .domain(data.map(d => d.room))
            .range(d3.schemeSet2.concat(d3.schemeSet3));

        chart.selectAll('path').data(arcData).join('path')
            .attr('d', path)
            .attr('transform', `translate(${width / 2}, ${height / 2})`)
            .attr('fill', d => color(d.data.room))
            .transition().duration(1000).attrTween('d', arcTween);

        const dictOfRoom = {
            'diningroom': '餐厅',
            'livingroom' : '客厅',
            'office' :'办公室',
            'bedroom':'卧室',
        }

        const arcOuter = d3.arc().innerRadius(80).outerRadius(80);
        chart.append('g').attr('transform', `translate(${width / 2}, ${height / 2})`)
            .selectAll('text').data(arcData).join('text')
            .attr('transform', d => `translate(${arcOuter.centroid(d)})`)
            .attr('text-anchor', 'middle')
            .text(d => dictOfRoom[d.data.room] )
            .style('opacity', 0)
            .transition().delay(1000).style('opacity', 1);
        const caption=chart.append('g').attr('class','caption');
        caption.append("foreignObject")
        .attr('y',parseInt(height)-36)
        .attr("width", width)
        .attr("height", 36)
        .append("xhtml:p")
        .attr('style','word-wrap: break-word; text-align:center;')
        .append('text')
        // .attr('text-anchor','middle')
        .text(d.description==null?'':d.description)
        .attr('style','font-size: 12px; fill: #888;');
    });

    // container.attr('width', '40vw')
};
// draw1();

// export function draw1();
