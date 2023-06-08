


// ************** Generate the tree diagram	 *****************
var margin = { top: 40, right: 20, bottom: 20, left: 20 },
    width = 10000 - margin.right - margin.left,
    height = 800 - margin.top - margin.bottom;
width = 1200;
height = 1200;

var i = 0;

var tree = d3.layout.tree()
    .size([height, width]);

var diagonal = d3.svg.diagonal()
    .projection(function (d) { return [d.x, d.y]; });

var svg = d3.select("body").select("#generatedTree").append("svg")
    .attr("width", width + margin.right + margin.left)
    .attr("width", '50vw')
    .attr("height", height + margin.top + margin.bottom)
    .append("g")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

// 获得树的数据
var obj = JSON.parse(data1);
root = obj[0];

var currentmeta = root.meta;

let currentid = -1;

update(root);

function update(source) {

    // Compute the new tree layout.
    var nodes = tree.nodes(root).reverse(),
        links = tree.links(nodes);

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



    let len = width / 12;


    // TODO
    // 加入的图片只有一张，但如果用pic[0]显然不具有代表性...而且norm也需要重新选择
    // let pic_index = 0;
    let pic_index = 0;

    let id=0;


    console.log(nodeEnter[0].length)

    const arr_len = nodeEnter[0].length + 10
    let listenrArray = new Array(arr_len).fill(true)

    let z_index = arr_len;

    let defs = svg.append('defs');
    defs.selectAll('.mypattern').data(nodes).enter().append('pattern')
    .attr('class', 'mypattern')
    .attr("id", d => `imgdef${d.id}`)
    .attr("width", 1)
    .attr("height", 1)
    .attr("patternUnits", "objectBoundingBox")
    .append("image").attr('id', d => `image${d.id}`)
    .attr("href", d => d.pics[0] + ".png")
    .attr('preserveAspectRatio', "xMidYMid meet")
    .attr("width", len)
    .attr("height", len);

    nodeEnter.append("rect") 
    //.attr("href", d => d.pics[0] + ".png")
    .attr("fill", d => `url(#imgdef${d.id})`).attr('stroke-width', 3)
    .attr("x", -len / 2)
    .attr("y", -len / 2)
    .attr("width", len)
    .attr("height", len)
    .attr("id", function(d){
        id = id+1;
        return id;
    })
    //.attr('stroke', 'black').attr('stroke-width', '2px')
    .on('mouseover', function (d) {
        let file_dir = d.pics[0] + ".json";
        let scale = 6;
        d.imgindex = 0;
        d3.select(this.parentNode).raise()
        d3.select(this).transition()
        .attr("x", -width / scale)
        .attr("y", -width / scale)
        .attr("width", width / (scale / 2))
        .attr("height", width / (scale / 2))
        d3.select(`#image${d.id}`).transition()
        .attr("width", width / (scale / 2))
        .attr("height", width / (scale / 2))
        draw1(d.pics[d.imgindex] + ".json")
        draw2('/static/dataset/infiniteLayout/'+onlineGroup+'_origin_values.json',file_dir);
    })
    .on('mouseout', function (d) {
        // this.isHere = false;
        d3.select(this)
        .transition()
        .attr("x", -len / 2)
        .attr("y", -len / 2)
        .attr("width", len)
        .attr("height", len);
        d3.select(`#image${d.id}`).transition()
        .attr("width", len)
        .attr("height", len);
        d3.select('#fig1').selectAll('g').remove();
        d3.select('#fig1').selectAll('path').remove();
        d3.select('#fig2').selectAll('g').remove();
        d.imgindex = -1;
    })
        .on('click',(d)=>{
            //Require that all the animations goes from the root or to the root
            let taID = manager.renderManager.scene_json.rooms[0].totalAnimaID;
            if(currentmeta.root == undefined)
            {
                if(d.meta.root == undefined)
                {
                    $.getJSON(`/static/dataset/infiniteLayout/${taID}/${currentmeta.anim_id}.json`, function(result1){
                        const T = Math.max(...result1.actions.map(d => Math.max(...d.map(dd => Math.max(...dd.map(ddd => ddd.t[1]))))));
                        sceneTransformBack(result1.actions);
                        manager.renderManager.scene_json.rooms[0].sflayoutid = root.meta.root;
                        setTimeout(
                            ()=>{
                                $.getJSON(`/static/dataset/infiniteLayout/${taID}/${d.meta.anim_id}.json`, function(result2){
                        // let meta = $(e.target).data("meta");
                        // if(meta.anim_forward){
                            
                                sceneTransformTo(result2.actions);
                                currentmeta = d.meta;
                                manager.renderManager.scene_json.rooms[0].sflayoutid = d.meta.target_node;
                            }
                        );
                    },T*1000+1000);
                });
                }
                else
                {
                    $.getJSON(`/static/dataset/infiniteLayout/${taID}/${currentmeta.anim_id}.json`, function(result1){
                        sceneTransformBack(result1.actions);
                        currentmeta = d.meta;
                    });
                    manager.renderManager.scene_json.rooms[0].sflayoutid = d.meta.root;
                }
            }
            else
            {
                if(d.meta.root == undefined)
                {
                    $.getJSON(`/static/dataset/infiniteLayout/${taID}/${d.meta.anim_id}.json`, function(result2){
                        // let meta = $(e.target).data("meta");
                        // if(meta.anim_forward){
                            sceneTransformTo(result2.actions);
                            currentmeta = d.meta;
                            manager.renderManager.scene_json.rooms[0].sflayoutid = d.meta.target_node;
                        // }else{
                            // sceneTransformBack(result.actions);
                        // }
                        
                    });
                    
                }
            }
            // document.querySelector("#operationFutureModal")
            // .style.display="none";
            $('#operationFutureModal').modal('hide')
        })
        ;


    // Declare the links…
    var link = svg.selectAll("path.link")
        .data(links, function (d) { return d.target.id; });

    // Enter the links.
    link.enter().insert("path", "g")
        .attr("class", "link")
        .attr("d", diagonal);
}

