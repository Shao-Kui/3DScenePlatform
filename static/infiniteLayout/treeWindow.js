// ************** Generate the tree diagram	 *****************
let infinitePanelWidth = window.innerWidth;//document.getElementById('infinitePanel').offsetWidth;
let infinitePanelHeight = window.innerHeight;//document.getElementById('infinitePanel').offsetHeight;
var margin = { top: infinitePanelHeight * 0.2, right: 0, bottom: 0, left: infinitePanelWidth * 0.01 };
var width = infinitePanelWidth;
var height = infinitePanelHeight;
var i = 0;
var tree = d3.layout.tree().size([height, width]);
var diagonal = d3.svg.diagonal().projection(function (d) { return [d.x, d.y]; });
var svg = d3.select("body").select("#generatedTree").append("svg").attr('id', 'infiniteSVG').attr('opacity', '1')
// .attr("width", width + margin.right + margin.left)
.attr("width", '100%')
.attr("height", height-margin.top-margin.bottom)
.append("g").attr('id', 'infiniteSuperGroup').attr("transform", "translate(" + margin.left + "," + margin.top + ") scale(1.15)")
.append("g").attr('id', 'infiniteGroup').attr('opacity', '1');
const ziweiSchemeSet = ['#ffffff', '#ffd186', '#c8dbf5', '#ffbcc7']
const dictOfRoom = {
    'diningroom': 'Dinning Room',//'餐厅',
    'livingroom' : 'Living Room',//'客厅',
    'office' : 'Office',//'办公室',
    'bedroom': 'Bedroom'//'卧室',
}
const colorOfRoom = {
    'diningroom': '#ffffff',//'餐厅',
    'livingroom' : '#ffbcc7',//'客厅',
    'office' : '#c5dcf8',//'办公室',
    'bedroom': '#ffd286'//'卧室',
}

const updateTreeWindow = function(root) {
    const captiong = svg.append('g').attr('transform', `translate(${width / 2 - infinitePanelWidth * 0.1}, ${-150})`);
    captiong.selectAll('.captionrect').data(Object.keys(dictOfRoom)).enter().append('rect')
        .attr('class', 'captionsgroup')
        .attr('y', (d, i) => i * 32)
        .attr('width', 40)
        .attr('height', 20)
        .attr('fill', d => colorOfRoom[d])

    captiong.selectAll('.captiontext').data(Object.keys(dictOfRoom)).enter().append('text')
        .attr('class', 'captiontext')
        .attr('y', (d, i) => i * 32 + 15)
        .attr('x', 42)
        .attr('width', 40)
        .attr('height', 20)
        .attr('font-size', '1.2em')
        .text(d => dictOfRoom[d])
    // Compute the new tree layout.
    let nodes = tree.nodes(root).reverse();
    let links = tree.links(nodes);

    // Normalize for fixed-depth.
    nodes.forEach(function (d) { d.y = d.depth * 100; });
    // nodes.forEach(function (d) { d.x = d.x * 1.25; });

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
        .attr("id", d => `node${d.id}`)
        .attr("transform", function (d) {
            return "translate(" + d.x + "," + d.y + ")";
    });

    const len = width / 50;
    const pielen = width / 55
    const pieleninner = width / 70
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

    // Declare the links…
    var link = svg.selectAll("path.link")
        .data(links, function (d) { return d.target.id; });

    // Enter the links.
    link.enter().insert("path", "g")
    .attr("class", "link")
    .attr("stroke", "#666666")
    .attr("d", diagonal);

    nodeEnter.append("rect") 
    .attr("class","imagerect")
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
        let scale = 12;
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
        draw1(d.pics[d.imgindex] + ".json");
        draw1b(d.pics[d.imgindex] + ".json" , d.depth);
        if(manager.renderManager.scene_json.rooms[0].currentTransMeta.root != undefined)
            draw2('/static/dataset/infiniteLayout/'+onlineGroup+'_origin_values.json',file_dir);
        else
            draw2('/static/dataset/infiniteLayout/'+onlineGroup+`_animimg/${manager.renderManager.scene_json.rooms[0].currentTransMeta.anim_id}.json`,file_dir);
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
        d3.select('#fig1a').selectAll('g').remove();
        d3.select('#fig1a').selectAll('path').remove();
        d3.select('#fig1a').selectAll('polyline').remove();
        d3.select('#fig1b').selectAll('g').remove();
        d3.select('#fig1b').selectAll('path').remove();
        d3.select('#fig1b').selectAll('polyline').remove();
        d3.select('#fig1b').selectAll('text').remove();
        d3.select('#fig2').selectAll('g').remove();
        d.imgindex = -1;
    })
    .on('click', d => { // value d is the datum of the clicked primitive. 
        stats.dom.style.display = 'flex';
        // require that all the animations goes from the root or to the root
        let taID = manager.renderManager.scene_json.rooms[0].totalAnimaID;
        // if(!manager.renderManager.scene_json.rooms[0].currentTransMeta){
        //     for(let i = 0; i < nodes.length; i++){
        //         if(manager.renderManager.scene_json.rooms[0].sflayoutid === nodes[i].meta.target_node || manager.renderManager.scene_json.rooms[0].sflayoutid === nodes[i].meta.root){
        //             manager.renderManager.scene_json.rooms[0].currentTransMeta = nodes[i].meta;
        //             break;
        //         }
        //     }
        // }
        if(manager.renderManager.scene_json.rooms[0].currentTransMeta.root === undefined){
            if(d.meta.root === undefined){
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
                $.getJSON(`/static/dataset/infiniteLayout/${taID}/${manager.renderManager.scene_json.rooms[0].currentTransMeta.anim_id}.json`, function(result1){
                    sceneTransformBack(result1.actions);
                    manager.renderManager.scene_json.rooms[0].currentTransMeta = d.meta;
                });
                manager.renderManager.scene_json.rooms[0].sflayoutid = d.meta.root;
            }
        }else{
            if(d.meta.root === undefined){
                $.getJSON(`/static/dataset/infiniteLayout/${taID}/${d.meta.anim_id}.json`, function(result2){
                    sceneTransformTo(result2.actions);
                    manager.renderManager.scene_json.rooms[0].currentTransMeta = d.meta;
                    manager.renderManager.scene_json.rooms[0].sflayoutid = d.meta.target_node;                        
                });  
            }else{ // This branch indicates a root -> root situation, so just reset the scene. 
                // $.getJSON(`/static/dataset/infiniteLayout/${taID}/${currentAnimation.index[manager.renderManager.scene_json.rooms[0].currentTransMeta.root][0].anim_id}.json`, function(result2){
                $.getJSON(`/static/dataset/infiniteLayout/${manager.renderManager.scene_json.rooms[0].totalAnimaID.split('_anim')[0]}_origin.json`, function(originjson){
                    manager.renderManager.scene_json.rooms[0].objList.forEach(o => {
                        if(o.sforder === undefined){return}
                        let origino = originjson.rooms[0].objList.find(oo => oo.sforder === o.sforder);
                        let object3d = manager.renderManager.instanceKeyCache[o.key];
                        object3d.position.set(origino.translate[0], origino.translate[1], origino.translate[2]);
                        object3d.rotation.set(origino.rotate[0], origino.rotate[1], origino.rotate[2]);
                        console.log(o.sforder, origino.startState, 0.1)
                        objectToAction(object3d, origino.startState, 0.1);
                        synchronizeObjectJsonByObject3D(object3d);
                    })               
                })
            }
        }
        $('#operationFutureModal').modal('hide')
    });

    // add the surrounding pie graph
    nodeEnter.each(function(d, i){
        d3.json(d.pics[0] + ".json").then(data => {
                        if(data.evaluation != null)data = data.evaluation;
            let outerrooms = [];
            for(let i = 1; i < d.depth; i++)
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
            // console.log(d);
            d3.select(this).selectAll('path.pieplot').data(pie(data))
            .enter()
            .append("path")
            .attr("class","pieplot")
            .attr("id",`pieplot${d.id}`)
            .attr("d", d3.arc().innerRadius(pieleninner - 5 * Math.max(0 , d.depth - 1)).outerRadius(pielen - 5 * Math.max(0 , d.depth - 1)))
            .attr('fill', d => colorOfRoom[d.data.room]);
            for(let i = 0; i + 1 < d.depth; i++)
            {
                d3.select(this).selectAll(`path#pieplot${d.id}-${i}`).data(pie(outerrooms[i]))
                .enter()
                .append("path")
                .attr("class","pieplot")
                .attr("id",`pieplot${d.id}-${i}`)
                .attr("d", d3.arc().innerRadius(pielen - 5 * (i+1)).outerRadius(pielen - 5 * i))
                .attr('fill', d => colorOfRoom[d.data.room]);
            }
            d3.selectAll(`path#pieplot${d.id}`).lower();
            for(let i = 0; i + 1 < d.depth; i++)
                d3.selectAll(`path#pieplot${d.id}-${i}`).lower();
        })
    });

}