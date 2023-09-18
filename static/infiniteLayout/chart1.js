// The following code is the typical routine of my d3.js code. 


let width1 = 600;
let height1 = 400;

// let pic_index=0



let draw_array = [1]


const draw1 = (data_dir) => {

    // console.log(data_dir)
    const arcGenerator = d3.arc()
    .innerRadius(20).outerRadius(80);
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

    const container = d3.select('#fig1a');
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
        const path = d3.arc().innerRadius(20).outerRadius(80);
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

        const arcOuter = d3.arc().innerRadius(50).outerRadius(50);
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

const draw1b = (data_dir , depth) => {

    // console.log(data_dir)
    const arcGenerator = d3.arc()
    .innerRadius(20).outerRadius(80 - 10 * Math.max(depth-1,0));
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

    const container = d3.select('#fig1b');
    const boundingrect=container.node().getBoundingClientRect();
    const width = boundingrect.width;
    const height = boundingrect.height;
    const chart = container;
    const margin = { top: 30, right: 30, bottom: 30, left: 30 };
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
        let outerrooms = [];
        for(let i = 1; i < depth; i++)
        {
            let mxv = -1.0, mxpos = -1;
            for(let j = 0; j < data.length; j++)
            {
                if(data[j].value > mxv)
                {
                    mxv = data[j].value;
                    mxpos = j;
                }
            }
            outerrooms.push(data.map(d => {return {"room":d.room,"value":0.0}}));
            outerrooms[i-1][mxpos].value = 1;
            data[mxpos].value = 0;
        }
        const pie = d3.pie().value(d => d.value);
        const arcData = pie(data);
        const path = d3.arc().innerRadius(20).outerRadius(80 - 15 * Math.max(depth-1,0));
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

        const arcOuter = d3.arc().innerRadius(50 - 7.5 * depth).outerRadius(50 - 7.5 * depth);
        chart.append('g').attr('transform', `translate(${width / 2}, ${height / 2})`)
            .selectAll('text').data(arcData).join('text')
            .attr('transform', d => `translate(${arcOuter.centroid(d)})`)
            .attr('text-anchor', 'middle')
            .text(d => {
                if(d.data.value > 0)return dictOfRoom[d.data.room];
                else return '';
            })
            .style('opacity', 0)
            .transition().delay(1000).style('opacity', 1);
        for(let i = 0; i + 1 < depth; i++)
        {
            chart.append('g').attr('transform', `translate(${width / 2}, ${height / 2})`)
            .selectAll('path').data(pie(outerrooms[i])).join('path')
                .attr("d", d3.arc().innerRadius(80 - 15 * (i + 1)).outerRadius(80 - 15 * i))
                .attr('fill', d => {
                    const color = d3.scaleOrdinal()
                    .domain(data.map(dat => dat.room))
                    .range(d3.schemeSet2.concat(d3.schemeSet3));
                    return color(d.data.room);
                });
            const arcInner = d3.arc().innerRadius(80 - 15 * (i + 0.5)).outerRadius(80 - 15 * (i + 0.5));
            chart.append('g').attr('transform', `translate(${width / 2}, ${height / 2})`)
                .selectAll('text').data(pie(outerrooms[i])).join('text')
                .attr('transform', d => `translate(${arcInner.centroid(d)})`)
                .attr('text-anchor', 'middle')
                .text(d => {
                    if(d.data.value > 0)return dictOfRoom[d.data.room];
                    else return '';
                })
                .style('opacity', 0)
                .transition().delay(1000).style('opacity', 1);
        }
    });

    // container.attr('width', '40vw')
};
// draw1();

// export function draw1();
