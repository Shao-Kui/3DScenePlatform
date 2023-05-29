


// ************** Generate the tree diagram	 *****************
var margin = { top: 40, right: 20, bottom: 20, left: 20 },
    width = 10000 - margin.right - margin.left,
    height = 2400 - margin.top - margin.bottom;

var i = 0;

var tree = d3.tree()
    .size([height, width]);

var diagonal = function (d) {
    return "M" + d.source.y + "," + d.source.x
        + "C" + (d.source.y + d.target.y) / 2 + "," + d.source.x
        + " " + (d.source.y + d.target.y) / 2 + "," + d.target.x
        + " " + d.target.y + "," + d.target.x;
};

var svg = d3.select("body").select("#generatedTree").append("svg")
    .attr("width", width + margin.right + margin.left)
    .attr("height", height + margin.top + margin.bottom)
    .append("g")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

// 获得树的数据
var obj = JSON.parse(data1);
root = obj[0];

update(root);

function update(source) {

    // Compute the new tree layout.
    // var nodes = tree.nodes(root).reverse(),
    //     links = tree.links(nodes);

    // create a hierarchy from the root
    const treeRoot = d3.hierarchy(root)
    d3.tree(treeRoot)
    // nodes
    const nodes = treeRoot.descendants()
    // links
    const links = treeRoot.links()

    // Normalize for fixed-depth.
    nodes.forEach(function (d) { d.y = d.depth * 100; });

    // Declare the nodes…
    var node = svg.selectAll("g.node")
        .data(nodes, function (d) { return d.id || (d.id = ++i); });

    // console.log(node)

    // Enter the nodes.
    var nodeEnter = node.enter().append("g")
        .attr("class", "node")
        .attr("transform", function (d) {
            return "translate(" + d.x + "," + d.y + ")";
        });



    let len = 50

    nodeEnter.append("svg:image")
        .attr("xlink:href", function (d) {
            return "./../files/" + d.pics[0] + ".png";
            // return "images/" + (parseInt(d.pics[0]) % 3 + 1) + ".png";
            // return "images/" + d.pics[0] + ".png";
        })
        // .attr("xlink:href", "https://github.com/favicon.ico")
        .attr("x", -len / 2)
        .attr("y", -len / 2)
        .attr("width", len)
        .attr("height", len)
        .on('mouseover', function (d) {
            d3.select(this)
                .attr("opacity", 0.5)
                .attr("stroke", "white")
                .attr("stroke-width", 6);
        })
        .on('mouseout', function (d) {
            d3.select(this)
                .attr("opacity", 1)
                .attr("stroke", "black")
                .attr("stroke-width", 1);
        })
        ;
    // nodeEnter append image with local url from json

    // nodeEnter.append("text")
    // 	.attr("y", function (d) {
    // 		return (d.children || d._children ? -20 : 20) - 80;
    // 	})
    // 	.attr("dy", ".35em")
    // 	.attr("text-anchor", "middle")
    // 	.text(function (d) { return d.name; })
    // 	.style("fill-opacity", 1);



    // nodeEnter.append("circle")
    // 	.attr("r", 5)
    // 	.style("fill", "#fff");

    // nodeEnter.append("text")
    // 	.attr("y", function (d) {
    // 		return d.children || d._children ? -20 : 20;
    // 	})
    // 	.attr("dy", ".35em")
    // 	.attr("text-anchor", "middle")
    // 	.text(function (d) { return d.name; })
    // 	.style("fill-opacity", 1);

    // // // let radius = 20;

    // // // nodeEnter
    // // // 	.append("circle")
    // // // 	.attr("r", radius)
    // // // 	.attr("fill", "#fff")
    // // // 	.attr("stroke", d => (d._children ? "#555" : "#999"))
    // // // 	.attr("stroke-width", 1);

    // // // nodeEnter
    // // // 	.append("svg:image")
    // // // 	.attr("xlink:href", function (d) {
    // // // 		return "images/" + d.pics[0] + ".png";
    // // // 	})
    // // // 	.attr("x", function (d) {
    // // // 		return -1.5 * radius;
    // // // 	})
    // // // 	.attr("y", function (d) {
    // // // 		return -1.5 * radius;
    // // // 	})
    // // // 	.attr("height", radius * 3)
    // // // 	.attr("width", radius * 3)
    // // // 	.attr("clip-path", "url(#avatar-clip)");

    // Declare the links…
    var link = svg.selectAll("path.link")
        .data(links, function (d) { return d.target.id; });

    // Enter the links.
    link.enter().insert("path", "g")
        .attr("class", "link")
        .attr("d", diagonal);

}
