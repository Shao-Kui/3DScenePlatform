const remove2 = () => {
    const container = d3.select('#fig2');
    container.selectAll('g').remove();
};

let width2 = 600;
let height2 = 400;




const draw2 = (old_dir, new_dir) => {
    const container = d3.select('#fig2');
    const width = container.attr('width');
    const height = container.attr('height');
    const chart = container;
    const margin = { top: 30, right: 30, bottom: 30, left: 150 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;
    container.append('g')
        .attr('transform', `translate(${margin.left}, ${margin.top})`);
    const xValue = d => d.room;
    const yValue = d => d.value;
    const xScale = d3.scaleBand();
    const yScale = d3.scaleLinear();
    const color = d3.scaleOrdinal().range(d3.schemeSet2);



    d3.json(old_dir).then(d => {
        let data;
        if (d.evaluation == null) data = d;
        else data = d.evaluation;
        olddata = data;
        d3.json(new_dir).then(d => {
            let data;
            if (d.evaluation == null) data = d;
            else data = d.evaluation;
            for (let i = 0; i < data.length; i++) {
                data[i]['type'] = 'new room';
            }
            for (let i = 0; i < olddata.length; i++) {
                olddata[i]['type'] = 'origin room';
                data.push(olddata[i])
            }
            xScale.domain(data.map(xValue)).range([0, innerWidth]).padding(0.15);
            yScale.domain(d3.extent(data.concat([{ "value": 0 }]), yValue)).range([innerHeight, 0]).nice();
            const Group = chart.append('g').attr('transform', `translate(${margin.left}, ${margin.top})`);
            const rects = Group.selectAll('rect').data(data).join('rect')
                .attr('width', xScale.bandwidth() / 2)
                .attr('height', d => (d.type == 'origin room' ? innerHeight - yScale(yValue(d)) : 0))
                .attr('y', d => (d.type == 'origin room' ? yScale(yValue(d)) : innerHeight)).attr('x', d => (d.type === 'origin room' ? 0 : xScale.bandwidth() / 2) + xScale(xValue(d)))
                .attr('fill', d => color(d.type));

            rects.transition().duration(1000)
                .attr('width', xScale.bandwidth() / 2)
                .attr('height', d => innerHeight - yScale(yValue(d)))
                .attr('y', d => yScale(yValue(d))).attr('x', d => (d.type === 'origin room' ? 0 : xScale.bandwidth() / 2) + xScale(xValue(d)))
                .attr('fill', d => color(d.type));
            const xAxisMethod = d3.axisBottom(xScale);
            const yAxisMethod = d3.axisLeft(yScale);
            const xAxisGroup = Group.append('g').call(xAxisMethod);
            const yAxisGroup = Group.append('g').call(yAxisMethod);
            xAxisGroup.attr('transform', `translate(${0}, ${innerHeight})`);
            d3.selectAll('.tick text').attr('font-size', '1.0em').attr('font-weight', 'bold');
            var legend = Group.selectAll(".legend")
                .data(Array.from(new Set(data.map(d => d.type)))).join('g')
                .attr("class", "legend")
                .attr("transform", (d, i) => `translate(${(20)},${(i * 20)})`);
            legend.append("rect")
                .attr("x", 0)
                .attr("y", -3)
                .attr("width", 20)
                .attr("height", 20)
                .style("fill", d => color(d));
            legend.append("text")
                .attr("x", 25)
                .attr("y", 7)
                .attr("dy", ".45em")
                .attr("text-anchor", "start")
                .attr("font-size", '1.0em')
                .text(d => d[0].toUpperCase() + d.slice(1));
        })
    })
};
// draw2();