


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

    function raise() {
        d3.select(this).raise()
        // console.log('彳亍')
        // console.log(this)
    }

    nodeEnter.append("svg:image") 
        .attr("xlink:href", function (d) {
            // console.log(this.zIndex)
            return d.pics[0] + ".png";
            // return "images/" + (parseInt(d.pics[0]) % 3 + 1) + ".png";
            // return "images/" + d.pics[0] + ".png";
        })
        // .attr("xlink:href", "https://github.com/favicon.ico")
        .attr("x", -len / 2)
        .attr("y", -len / 2)
        .attr("width", len)
        .attr("height", len)
        .attr("id", function(d){
            id = id+1;
            return id;
        })
        .style('position', 'relative')
        .style('z-index', 1)
        .on('mouseover', function (d) {
            // console.log(this)
            currentid = this.id;
            // console.log(currentid)
            this.isHere = true;
            let file_dir = d.pics[0] + ".json";
            const pics_array = d.pics;

            let thisId = this.id;
            let ptr = this;

            this.style.position = 'relative';
            const thisLayout = document.getElementById(thisId)
            thisLayout.href.baseVal = d.pics[pic_index] + ".png"
            z_index += 1;
            this.style.zIndex = z_index;
            this.style.z_index = z_index

            let scale = 6;

            d3.select(this)
                // .attr("opacity", 0.5)
                // .attr("stroke", "white")
                // .attr("stroke-width", 6);
                .transition()
                .attr("x", -width / scale)
                .attr("y", -width / scale)
                .attr("width", width / (scale / 2))
                .attr("height", width / (scale / 2))
            
            d3.select(this.parentNode).raise()

            
            
            

            // console.log(this.style.zIndex)

            // 这里的思路是对每个结点加上一个eventListener，但是为了防止一个结点加太多次，就用一个表来记录有无加过
            if(listenrArray[thisId] == true) {
                listenrArray[thisId] = false;
                document.addEventListener('keydown', function(e) {
                   
                    if(currentid == thisId) {
                        if(d.pics.length <= 1) return ;
                        // console.log()
                        if(e.key == 'ArrowLeft') {
                            pic_index -= 1;
                            pic_index = (pic_index + d.pics.length) % d.pics.length
                        } 
                        else if(e.key == 'ArrowRight') {
                            pic_index += 1;
                            pic_index %= d.pics.length
                        } 
                        else return ;
                        d3.select('#fig1').selectAll('g').remove();
                        d3.select('#fig1').selectAll('path').remove();
                        d3.select('#fig2').selectAll('g').remove();
                        // console.log(pic_index)
                        // ptr.parentElement.attr("xlink:href", d.pics[pic_index % d.pics.length] + ".png")
                        const thisLayout = document.getElementById(thisId)
                        thisLayout.href.baseVal = d.pics[pic_index] + ".png"
                        z_index += 1;
                        thisLayout.style.zIndex = z_index;
                        // console.log(thisLayout.href.baseVal)
                        // thisLayout.attr("xlink:href", d.pics[pic_index % d.pics.length] + ".png")
                        file_dir = d.pics[pic_index] + ".json";


                        draw1(d.pics[pic_index % d.pics.length] + ".json")
                        draw2('/static/dataset/infiniteLayout/'+onlineGroup+'_origin_values.json',file_dir);

        
                    }
                })
            }

            draw1(d.pics[0] + ".json")
            draw2('/static/dataset/infiniteLayout/'+onlineGroup+'_origin_values.json',file_dir);



        })
        // .on('mouseover', raise)
        .on('mouseout', function (d) {
            this.isHere = false;
            d3.select(this)
                .transition()
                .attr("x", -len / 2)
                .attr("y", -len / 2)
                .attr("width", len)
                .attr("height", len);
                // .attr("opacity", 1)
                // .attr("stroke", "black")
                // .attr("stroke-width", 1);
            d3.select('#fig1').selectAll('g').remove();
            d3.select('#fig1').selectAll('path').remove();
            d3.select('#fig2').selectAll('g').remove();
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

