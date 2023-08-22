// ************** Generate the tree diagram	 *****************
var margin = { top: 0, right: 0, bottom: 0, left: 0 };
var width = 1200;
var height = 1200;
var i = 0;
var tree = d3.layout.tree().size([height, width]);
var diagonal = d3.svg.diagonal().projection(function (d) { return [d.x, d.y]; });
var svg = d3.select("body").select("#generatedTree").append("svg")
    // .attr("width", width + margin.right + margin.left)
    .attr("width", '100%')
    .attr("height", height-margin.top-margin.bottom)
    .append("g")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");
// 获得树的数据

const updateTreeWindow = function(root) {

    // Compute the new tree layout.
    let nodes = tree.nodes(root).reverse(),
        links = tree.links(nodes);

    // Normalize for fixed-depth.
    nodes.forEach(function (d) { d.y = d.depth * 100; });

    // Declare the nodes…
    let node = svg.selectAll("g.node")
    .data(nodes, function (d) { return d.id || (d.id = ++i); });
    
    if(!manager.renderManager.scene_json.rooms[0].sflayoutid){
        manager.renderManager.scene_json.rooms[0].sflayoutid = getCurrentIndexing()
    }
    if(!manager.renderManager.scene_json.rooms[0].currentTransMeta){
        for(let i = 0; i < nodes.length; i++){
            if(manager.renderManager.scene_json.rooms[0].sflayoutid === nodes[i].meta.target_node || manager.renderManager.scene_json.rooms[0].sflayoutid === nodes[i].meta.root){
                manager.renderManager.scene_json.rooms[0].currentTransMeta = nodes[i].meta;
                break;
            }
        }
    }

    // Enter the nodes.
    var nodeEnter = node.enter().append("g")
        .attr("class", "node")
        .attr("transform", function (d) {
            return "translate(" + d.x + "," + d.y + ")";
    });

    let len = width / 12;
    let id=0;

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
    .on('click', d => { // value d is the datum of the clicked primitive. 
        // require that all the animations goes from the root or to the root
        console.log(d);
        let taID = manager.renderManager.scene_json.rooms[0].totalAnimaID;
        if(manager.renderManager.scene_json.rooms[0].currentTransMeta.root === undefined){
            if(d.meta.root === undefined){
                console.log('if if')
                $.getJSON(`/static/dataset/infiniteLayout/${taID}/${manager.renderManager.scene_json.rooms[0].currentTransMeta.anim_id}.json`, function(result1){
                    const T = Math.max(...result1.actions.map(d => Math.max(...d.map(dd => Math.max(...dd.map(ddd => ddd.t[1]))))));
                    sceneTransformBack(result1.actions);
                    manager.renderManager.scene_json.rooms[0].sflayoutid = root.meta.root;
                    setTimeout(
                        ()=>{
                            $.getJSON(`/static/dataset/infiniteLayout/${taID}/${d.meta.anim_id}.json`, function(result2){                           
                            sceneTransformTo(result2.actions);
                            manager.renderManager.scene_json.rooms[0].currentTransMeta = d.meta;
                            manager.renderManager.scene_json.rooms[0].sflayoutid = d.meta.target_node;
                        }
                    );
                    },T*1000+1000);
                });
            }
            else{
                console.log('if else')
                $.getJSON(`/static/dataset/infiniteLayout/${taID}/${manager.renderManager.scene_json.rooms[0].currentTransMeta.anim_id}.json`, function(result1){
                    sceneTransformBack(result1.actions);
                    manager.renderManager.scene_json.rooms[0].currentTransMeta = d.meta;
                });
                manager.renderManager.scene_json.rooms[0].sflayoutid = d.meta.root;
            }
        }else{
            console.log('else')
            if(d.meta.root === undefined){
                $.getJSON(`/static/dataset/infiniteLayout/${taID}/${d.meta.anim_id}.json`, function(result2){
                    sceneTransformTo(result2.actions);
                    manager.renderManager.scene_json.rooms[0].currentTransMeta = d.meta;
                    manager.renderManager.scene_json.rooms[0].sflayoutid = d.meta.target_node;                        
                });  
            }
        }
        $('#operationFutureModal').modal('hide')
    });


    // Declare the links…
    var link = svg.selectAll("path.link")
        .data(links, function (d) { return d.target.id; });

    // Enter the links.
    link.enter().insert("path", "g")
        .attr("class", "link")
        .attr("d", diagonal);
}

