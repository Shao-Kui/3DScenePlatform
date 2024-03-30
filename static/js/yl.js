//egRoom = {id:1, type:"", edgeList:[], eBoxList:[]}

//elastic box

//egEBox = {eBoxId:1, roomId:1, objList:[], edgeList:[], currentCover:[[0.0,0.0],[0.0,0.0]], currentRange:[0.0,0.0], dirRange:[[],[]]}

//egEdge = {edgeId:1, eBoxId:-1,roomId:0, point:[[0,0],[0,0]], dir:[1,0], neighbourEdge:[ {edgeId:1, eBoxId:-1, roomId:1}, ], onWall:false} // 
//egEdge = {edgeId:1, eBoxId:1, roomId:0, point:[[0,0],[0,0]], dir:[0,-1],neighbourEdge:[ {edgeId:1, eBoxId:-1, roomId:1}, ], onWall:false}

//egObj = {userData:{}, translate:[], relativeTranslate:{}}

function completeRoomInformationWhileAdding(id){ //temporary function to build bridge between data structure
    //console.log("fucking world!");
    if(!("eBoxList" in arrayOfRooms[id]))arrayOfRooms[id].eBoxList = [];
    //console.log(arrayOfRoomPoints);
    //console.log(arrayOfRoomPoints[arrayOfRooms[id].points[0]]);
    //console.log(arrayOfRoomPoints[arrayOfRooms[id].points[1]]);
    /*let t = toEbox(arrayOfRoomPoints[arrayOfRooms[id].points[0]].position, arrayOfRoomPoints[arrayOfRooms[id].points[2]].position);
    for(let i = 0; i < 4; ++i){
        t.edgeList[i].eBoxId = -1;
        t.edgeList[i].roomId = id;
        t.edgeList[i].neighbourEdge = [];
    }*/
    let p0 = arrayOfRoomPoints[arrayOfRooms[id].points[0]].position;
    let p1 = arrayOfRoomPoints[arrayOfRooms[id].points[1]].position;
    let p2 = arrayOfRoomPoints[arrayOfRooms[id].points[2]].position;
    let p3 = arrayOfRoomPoints[arrayOfRooms[id].points[3]].position;
    //ed0 ={edgeId:0,roomId:id,eBoxId:-1,point:[p0,p1],dir:[Math.abs(Math.sign(p0[1]-p1[1]))*Math.sign(p3[0]-p0[0]),Math.abs(Math.sign(p0[0]-p1[0]))*Math.sign(p3[1]-p0[1])],neighbourEdge:[], onWall:false};
    //ed1 ={edgeId:1,roomId:id,eBoxId:-1,point:[p1,p2],dir:[Math.abs(Math.sign(p1[1]-p2[1]))*Math.sign(p0[0]-p1[0]),Math.abs(Math.sign(p1[0]-p2[0]))*Math.sign(p0[1]-p1[1])],neighbourEdge:[], onWall:false};
    //ed2 ={edgeId:2,roomId:id,eBoxId:-1,point:[p2,p3],dir:[Math.abs(Math.sign(p2[1]-p3[1]))*Math.sign(p1[0]-p2[0]),Math.abs(Math.sign(p2[0]-p3[0]))*Math.sign(p1[1]-p2[1])],neighbourEdge:[], onWall:false};
    //ed3 ={edgeId:3,roomId:id,eBoxId:-1,point:[p3,p0],dir:[Math.abs(Math.sign(p3[1]-p0[1]))*Math.sign(p2[0]-p3[0]),Math.abs(Math.sign(p3[0]-p0[0]))*Math.sign(p2[1]-p3[1])],neighbourEdge:[], onWall:false};
    
    ed0 ={edgeId:0,roomId:id,eBoxId:-1,point:[[p0[0],p0[1]],[p1[0],p1[1]]],dir:[Math.abs(Math.sign(p0[1]-p1[1]))*Math.sign(p3[0]-p0[0]),Math.abs(Math.sign(p0[0]-p1[0]))*Math.sign(p3[1]-p0[1])],neighbourEdge:[], onWall:false};
    ed1 ={edgeId:1,roomId:id,eBoxId:-1,point:[[p1[0],p1[1]],[p2[0],p2[1]]],dir:[Math.abs(Math.sign(p1[1]-p2[1]))*Math.sign(p0[0]-p1[0]),Math.abs(Math.sign(p1[0]-p2[0]))*Math.sign(p0[1]-p1[1])],neighbourEdge:[], onWall:false};
    ed2 ={edgeId:2,roomId:id,eBoxId:-1,point:[[p2[0],p2[1]],[p3[0],p3[1]]],dir:[Math.abs(Math.sign(p2[1]-p3[1]))*Math.sign(p1[0]-p2[0]),Math.abs(Math.sign(p2[0]-p3[0]))*Math.sign(p1[1]-p2[1])],neighbourEdge:[], onWall:false};
    ed3 ={edgeId:3,roomId:id,eBoxId:-1,point:[[p3[0],p3[1]],[p0[0],p0[1]]],dir:[Math.abs(Math.sign(p3[1]-p0[1]))*Math.sign(p2[0]-p3[0]),Math.abs(Math.sign(p3[0]-p0[0]))*Math.sign(p2[1]-p3[1])],neighbourEdge:[], onWall:false};
    
    arrayOfRooms[id].edgeList = [ed0,ed1,ed2,ed3];
    console.log("go fuck yourself");
    //console.log(arrayOfRooms[id].edgeList);

}

function changeNeighbour(ed, oldId){
    for(let i = 0; i < ed.neighbourEdge.length; ++i){
        let vi = ed.neighbourEdge[i];
        let e = arrayOfRooms[vi.roomId].eBoxList[vi.eBoxId].edgeList[vi.edgeId];
        for(let j = 0; j < e.neighbourEdge.length; ++j){
            let vj = e.neighbourEdge[j];
            if(vj.roomId == ed.roomId && vj.edgeId == oldId && vj.eBoxId == vj.eBoxId){
                vj.edgeId = ed.edgeId; break;
            }
        }
    }
    return;
}

function clearNeighbour(ed){
    for(let i = 0; i < ed.neighbourEdge.length; ++i){
        let vi = ed.neighbourEdge[i];
        let e = arrayOfRooms[vi.roomId].eBoxList[vi.eBoxId].edgeList[vi.edgeId];
        for(let j = 0; j < e.neighbourEdge.length; ++j){
            let vj = e.neighbourEdge[j];
            if(vj.roomId == ed.roomId && vj.edgeId == ed.edgeId && vj.eBoxId == -1){
                e.neighbourEdge.splice(j,1); break;
            }
        }
    }
    return;
}

function checkNeighbour(ed){
    for(let i = 0; i < ed.neighbourEdge.length; ++i){
        let vi = ed.neighbourEdge[i];
        let e = arrayOfRooms[vi.roomId].eBoxList[vi.eBoxId].edgeList[vi.edgeId];
        let stat = edgeStatus(e,ed);
        if(stat != 2){//如果我和这个东西不再交了
            //从我这里删除它的印记
            ed.neighbourEdge.splice(i,1); --i;
        }
        else{//如果我和这个东西还是交的
            e.neighbourEdge = e.neighbourEdge.concat([{edgeId:ed.edgeId, eBoxId:ed.eBoxId, roomId:ed.roomId}])
            //从那里更新我的印记，从那里添加新的印记
        }

    }

}

function cutting_inner_line(room_id,line_id,position){
    //console.log("fuck the world again"); //console.log(position);
    let r = arrayOfRooms[room_id];
    clearNeighbour(r.edgeList[line_id]);
    //line_id
    var s = JSON.parse(JSON.stringify(r.edgeList[line_id]));
    var t = JSON.parse(JSON.stringify(r.edgeList[line_id]));
    r.edgeList[line_id].point[1] = [position[0], position[1]];
    checkNeighbour(r.edgeList[line_id]);
    
    t.point = [[position[0], position[1]],[position[0], position[1]]];
    t.dir = [s.dir[1],-s.dir[0]]; t.edgeId = line_id+1; t.neighbourEdge = [];
    r.edgeList.splice(line_id+1,0,t);

    //line_id+2
    s.point[0] = [position[0], position[1]];
    s.edgeId = line_id+2;
    checkNeighbour(s);
    r.edgeList.splice(line_id+2,0,s);


    for(let i = line_id+3; i < r.edgeList.length; ++i){
        r.edgeList[i].edgeId = i;
        changeNeighbour(r.edgeList[i], i-1);
    }
    //console.log(r);
}

/*function moveWallOnly(roomid,wallid,point0,point1){

    if(Math.abs(arrayOfRooms[roomid].edgeList[wallid].dir[0]) > Math.abs(arrayOfRooms[roomid].edgeList[wallid].dir[1])){
        if(arrayOfRooms[roomid].edgeList[wallid].point[0][1] > arrayOfRooms[roomid].edgeList[wallid].point[1][1]){
            arrayOfRooms[roomid].edgeList[wallid].point[0][1] = Math.max(point0[1], point1[1]); 
            arrayOfRooms[roomid].edgeList[wallid].point[1][1] = Math.min(point0[1], point1[1]);
        }
        else{
            arrayOfRooms[roomid].edgeList[wallid].point[0][1] = Math.min(point0[1], point1[1]); 
            arrayOfRooms[roomid].edgeList[wallid].point[1][1] = Math.max(point0[1], point1[1]);
        }
        
        arrayOfRooms[roomid].edgeList[wallid].point[0][0] = point0[0];
        arrayOfRooms[roomid].edgeList[wallid].point[1][0] = point1[0];
        
    }else{
        if(arrayOfRooms[roomid].edgeList[wallid].point[0][0] > arrayOfRooms[roomid].edgeList[wallid].point[1][0]){
            arrayOfRooms[roomid].edgeList[wallid].point[0][0] = Math.max(point0[0], point1[0]);
            arrayOfRooms[roomid].edgeList[wallid].point[1][0] = Math.min(point0[0], point1[0]);
        }
        else{
            arrayOfRooms[roomid].edgeList[wallid].point[0][0] = Math.min(point0[0], point1[0]);
            arrayOfRooms[roomid].edgeList[wallid].point[1][0] = Math.max(point0[0], point1[0]);
        }
        arrayOfRooms[roomid].edgeList[wallid].point[0][1] = point0[1]; 
        arrayOfRooms[roomid].edgeList[wallid].point[1][1] = point1[1]; 
    }

    arrayOfRooms[roomid].edgeList[(wallid+1)%(arrayOfRooms[roomid].edgeList.length)].point[0][0] += arrayOfRooms[roomid].edgeList[wallid].point[1][0];
    arrayOfRooms[roomid].edgeList[(wallid+1)%(arrayOfRooms[roomid].edgeList.length)].point[0][1] += arrayOfRooms[roomid].edgeList[wallid].point[1][1];
    arrayOfRooms[roomid].edgeList[(wallid+arrayOfRooms[roomid].edgeList.length-1)%(arrayOfRooms[roomid].edgeList.length)].point[1][0] += arrayOfRooms[roomid].edgeList[wallid].point[0][0];
    arrayOfRooms[roomid].edgeList[(wallid+arrayOfRooms[roomid].edgeList.length-1)%(arrayOfRooms[roomid].edgeList.length)].point[1][1] += arrayOfRooms[roomid].edgeList[wallid].point[0][1];

}*/

function func(info, realMove=false, dsMove=false){ if(debugHJK)return;
    /*if(1 in arrayOfRooms){//[0].eBoxList.length>0
    console.log(info);
    console.log("room1 edge0 before");
    console.log(arrayOfRooms[1].edgeList[0].point[0][0]);
    console.log(arrayOfRooms[1].edgeList[0].point[0][1]);
    console.log(arrayOfRooms[1].edgeList[0].point[1][0]);
    console.log(arrayOfRooms[1].edgeList[0].point[1][1]);
    console.log("room1 edge1 before");
    console.log(arrayOfRooms[1].edgeList[1].point[0][0]);
    console.log(arrayOfRooms[1].edgeList[1].point[0][1]);
    console.log(arrayOfRooms[1].edgeList[1].point[1][0]);
    console.log(arrayOfRooms[1].edgeList[1].point[1][1]);
    console.log("room1 edge2 before");
    console.log(arrayOfRooms[1].edgeList[2].point[0][0]);
    console.log(arrayOfRooms[1].edgeList[2].point[0][1]);
    console.log(arrayOfRooms[1].edgeList[2].point[1][0]);
    console.log(arrayOfRooms[1].edgeList[2].point[1][1]);
    console.log("room1 edge3 before");
    console.log(arrayOfRooms[1].edgeList[3].point[0][0]);
    console.log(arrayOfRooms[1].edgeList[3].point[0][1]);
    console.log(arrayOfRooms[1].edgeList[3].point[1][0]);
    console.log(arrayOfRooms[1].edgeList[3].point[1][1]);

    console.log("hjk room1 edges before");
    console.log(arrayOfRoomPoints[4].position[0]);
    console.log(arrayOfRoomPoints[4].position[1]);
    console.log(arrayOfRoomPoints[5].position[0]);
    console.log(arrayOfRoomPoints[5].position[1]);
    console.log(arrayOfRoomPoints[6].position[0]);
    console.log(arrayOfRoomPoints[6].position[1]);
    console.log(arrayOfRoomPoints[7].position[0]);
    console.log(arrayOfRoomPoints[7].position[1]);

    if(arrayOfRooms[0].eBoxList.length > 0){
    console.log("room0 box0 edge1 before");
    console.log(arrayOfRooms[1].eBoxList[0].edgeList[1].point[0][0]);
    console.log(arrayOfRooms[1].eBoxList[0].edgeList[1].point[0][1]);
    console.log(arrayOfRooms[1].eBoxList[0].edgeList[1].point[1][0]);
    console.log(arrayOfRooms[1].eBoxList[0].edgeList[1].point[1][1]);}
    }*/


    //console.log("func"); //console.log(info.movedir);
    scheme = null;
    //info.roomid,  info.wallinfo,  info.movedir,   info.movelength
    
    //change room wall info at first
    //console.log(info.movedir[0]*info.moveLength); console.log(info.moveLength); console.log(info.movedir);
    arrayOfRooms[info.roomid].edgeList[info.wallid].point[0][0] += info.movedir[0]*info.moveLength;
    arrayOfRooms[info.roomid].edgeList[info.wallid].point[0][1] += info.movedir[1]*info.moveLength; //console.log((info.wallid+arrayOfRooms[info.roomid].edgeList.length-1)%(arrayOfRooms[info.roomid].edgeList.length));
    arrayOfRooms[info.roomid].edgeList[info.wallid].point[1][0] += info.movedir[0]*info.moveLength; //console.log((info.wallid+1)%(arrayOfRooms[info.roomid].edgeList.length));
    arrayOfRooms[info.roomid].edgeList[info.wallid].point[1][1] += info.movedir[1]*info.moveLength; //console.log(info.wallid);    
    arrayOfRooms[info.roomid].edgeList[(info.wallid+1)%(arrayOfRooms[info.roomid].edgeList.length)].point[0][0] += info.movedir[0]*info.moveLength;
    arrayOfRooms[info.roomid].edgeList[(info.wallid+1)%(arrayOfRooms[info.roomid].edgeList.length)].point[0][1] += info.movedir[1]*info.moveLength;
    arrayOfRooms[info.roomid].edgeList[(info.wallid+arrayOfRooms[info.roomid].edgeList.length-1)%(arrayOfRooms[info.roomid].edgeList.length)].point[1][0] += info.movedir[0]*info.moveLength;
    arrayOfRooms[info.roomid].edgeList[(info.wallid+arrayOfRooms[info.roomid].edgeList.length-1)%(arrayOfRooms[info.roomid].edgeList.length)].point[1][1] += info.movedir[1]*info.moveLength;
    //console.log(arrayOfRooms[info.roomid]); return;

    let currentEdge = arrayOfRooms[info.roomid].edgeList[info.wallid];
    let synScheme = {flexLength:0, moveLength:info.moveLength, history:[]};
    for(let e = 0; e < currentEdge.neighbourEdge.length; ++e){
        let newInfo = JSON.parse(JSON.stringify(currentEdge.neighbourEdge[e]));
        //console.log("fuck the world again and again and again and again"); console.log(newInfo);
        sch = recur(newInfo, {dir:info.movedir, length:info.moveLength, flexLength:0});

        synScheme.moveLength = Math.min(synScheme.moveLength,sch.moveLength);
        synScheme.history = synScheme.history.concat(JSON.parse(JSON.stringify(sch.history)));
        //console.log(synScheme.history);console.log(synScheme.moveLength);console.log(synScheme.history[0].edgeList[0].point[0][0]);console.log(arrayOfRooms[info.roomid].eBoxList[0].edgeList[0].point[0][0]);
    }
    //scheme = recur({edgeId:info.wallid, eBoxId:-1, roomId:info.roomid}, {dir:info.movedir, length:info.moveLength, flexLength:0});
    
    act(synScheme, realMove, dsMove);
    if(realMove && dsMove) adding(info);
    if(dsMove) updateNeighbours(info.roomid);

    /*if(arrayOfRooms[0].eBoxList.length>0){
    console.log("room0 edge0");
    console.log(arrayOfRooms[0].edgeList[0].point[0][0]);
    console.log(arrayOfRooms[0].edgeList[0].point[0][1]);
    console.log(arrayOfRooms[0].edgeList[0].point[1][0]);
    console.log(arrayOfRooms[0].edgeList[0].point[1][1]);

    console.log("hjk room0 edge0");
    console.log(arrayOfRoomPoints[0].position[0]);
    console.log(arrayOfRoomPoints[0].position[1]);
    console.log(arrayOfRoomPoints[1].position[0]);
    console.log(arrayOfRoomPoints[1].position[1]);
    
    console.log("room0 box0 edge1");
    console.log(arrayOfRooms[0].eBoxList[0].edgeList[1].point[0][0]);
    console.log(arrayOfRooms[0].eBoxList[0].edgeList[1].point[0][1]);
    console.log(arrayOfRooms[0].eBoxList[0].edgeList[1].point[1][0]);
    console.log(arrayOfRooms[0].eBoxList[0].edgeList[1].point[1][1]);}*/


    return;
}

function edgeCross(edge1, edge2, strech1=0.0, strech2=0.0){
    if(Math.abs(edge1.dir[0]) == Math.abs(edge2.dir[0])){ return false; }
    p = 0;if(Math.abs(edge1.dir[0]) < Math.abs(edge2.dir[0])){p = 1;}
    return (edge1.point[0][p]<Math.max(edge2.point[0][p], edge2.point[1][p])+strech2)
         &&(Math.min(edge2.point[0][p], edge2.point[1][p])-strech2<edge1.point[0][p])
         &&(edge2.point[0][1-p]<Math.max(edge1.point[0][1-p], edge1.point[1][1-p])+strech1)
         &&(Math.min(edge1.point[0][1-p], edge1.point[1][1-p])-strech1<edge2.point[0][1-p]);
}

//房间分割之后，可能会出现比较大尺度上地位于房间外面，现在考虑怎么调整呢？

//考虑先判断出弹性盒如何出现在了房间的外面，如何考虑呢？
    //考虑交边。各个边和弹性盒的各个边测一下交不交
    //交边在弹性盒里一共两种情况，
            //其他情况都是错的？？
        //对边交了
                        //临边交了//如果只会划一条线的话其实连这种情况都不会出现吗？
                                            //先不管？//交边在房间里一共几种情况？不知道，有可能会很复杂，

        //暂时只考虑只划一条线的情况。
        //弹性盒的对边交的话，那么交的应该是原房间的同一条边才对，那么我们应该取这条边的内朝向，作为应该向内移动的方向，
                //如果不是同一条边，那么就是也是有问题，
        //进一步地，去找到弹性盒中这个方向的边
                //如果弹性盒中这个方向的边不是位于房间外侧，那么也是有问题
        //计算出这个边在房间那个边外面多少

        //逐步往里缩，一次缩的长度不要太多，

    //如果有多个弹性盒交到了房间外面怎么办
            //暂时还是给他ban掉吧

function visualRoom(roomShape){
    let newRoomEdgeList = [];
    let lp = roomShape[0];
    for(let i = 1; i <= roomShape.length; ++i){
        let tp = roomShape[i%(roomShape.length)];
        let newEdge = {edgeId:i-1,eBoxId:-1,roomId:-1, point:[[lp[0],lp[1]],[tp[0],tp[1]]], dir:[Math.sign(lp[1]-tp[1]),Math.sign(tp[0]-lp[0])], neighbourEdge:[], onWall:false}
        newRoomEdgeList = newRoomEdgeList.concat([newEdge]);
        lp = tp; 
    } //console.log(newRoomEdgeList);
    return newRoomEdgeList;
}

function rayFactory(source, hint){
    let ray = {point:[[source[0],source[1]],[source[0],source[1]]], dir:[0,0]};
    ray.point[Math.floor(hint/2)][hint%2] = Math.floor(hint/2)==0 ? -1000:1000;
    ray.dir[1-hint%2] = 1;
    return ray;
}

function inOrOut(room, elasticBox){
    let outFlag = -1; let errorFlag=1;
    for(let e=0; e<4;++e){  
        /*console.log(e);
        console.log(elasticBox.edgeList[e].point[0][0]);
        console.log(elasticBox.edgeList[e].point[0][1]);
        console.log(elasticBox.edgeList[e].point[1][0]);
        console.log(elasticBox.edgeList[e].point[1][1]);
        console.log(elasticBox.edgeList[e].dir[0]);
        console.log(elasticBox.edgeList[e].dir[1]);*/
        let crossCnt = 0;
        let hint=0; let online=false; 
        for(; hint<4;++hint){
            let ray = rayFactory(elasticBox.edgeList[e].point[0],hint);
            /*console.log(hint);
            console.log(ray.point[0][0]);
            console.log(ray.point[0][1]);
            console.log(ray.point[1][0]);
            console.log(ray.point[1][1]);
            console.log(ray.dir[0]);
            console.log(ray.dir[1]);*/
            let hintReject = false; crossCnt = 0;
            for(let f=0; f<room.edgeList.length;++f){
                let ed = room.edgeList[f];
                /*console.log(f);
                console.log(ed.point[0][0]);
                console.log(ed.point[0][1]);
                console.log(ed.point[1][0]);
                console.log(ed.point[1][1]);
                console.log(ed.dir[0]);
                console.log(ed.dir[1]);*/
                if(Math.abs(ed.dir[0])==Math.abs(ray.dir[0]) && Math.abs(ed.dir[1])==Math.abs(ray.dir[1])){
                    let dis = Math.abs(ed.dir[0])>Math.abs(ed.dir[1])?Math.abs(ed.point[0][0]-ray.point[0][0]):Math.abs(ed.point[0][1]-ray.point[0][1]);
                    //console.log(dis);
                    if(dis<0.01) hintReject = true;
                }
                if(hintReject) break;
                else{
                    if(edgeCross(ed,ray,0,-0.01) != edgeCross(ed,ray,0,0.01)){
                        online=true; //console.log(online);
                    }else if(edgeCross(ed,ray)){
                        crossCnt++; //console.log(crossCnt);
                    }
                } 
                //console.log(crossCnt);
                if(online) break;
            }
            if(!hintReject || online){break;}
        }
        if(hint==4 || online)continue; //point e is on a room corner, no proper ray could be found (or) this point is on a edge so it should not effect the box is in or out
        if(outFlag<0)outFlag = crossCnt%2;
        else if(outFlag != crossCnt%2){console.log("not fully in or out"); errorFlag=-1;}
        //console.log("checking");console.log(e);
        //console.log(crossCnt);
    }
    return (errorFlag==-1?-1:outFlag);
}

function checkRoomCrossEBox(room, elasticBox){
    let flag = -1;
    let glag = -1;
    let sump = 0;
    let dir = [];
    let dis = 0;
    let p = [];
    let ps = [];
    let singleEdgeCase = -1; let doubleEdgeCase = -1;
    for(let f=0;f<room.edgeList.length;++f){
        p = [];
        for(let e=0;e<4;++e){
            if(edgeCross(room.edgeList[f], elasticBox.edgeList[e],0.01,-0.01)) p = p.concat([e]);
        }
        ps = ps.concat([p]); //for(let k=0;k<p.length;++k)console.log(p[k]);
        sump += p.length;
        if(p.length == 2 && p[1]-p[0] == 2){ singleEdgeCase = f; }
    }//console.log(sump);console.log(ps);
    if(sump == 0){
        let ioo = inOrOut(room, elasticBox); //console.log(ioo);
        if(ioo==1){console.log("inOrOut in");
            return {edgeIds:[],eEdgeIds:[], dirs:[], diss:[], outState:0};
        }else if(ioo==0){//console.log("inOrOut out");
            return {edgeIds:[],eEdgeIds:[], dirs:[], diss:[], outState:2};
        }else{console.log("ioo error"); console.log(room); console.log(elasticBox);}
    }
    if(sump != 2){
        console.log("error p");
        console.log(room);
        console.log(elasticBox);
        return {edgeIds:[],eEdgeIds:[], dirs:[], diss:[], outState:-1};
    }
    
    for(let f=0;f<room.edgeList.length;++f){
        if(ps[f].length == 1 && ps[(f+1)%(room.edgeList.length)].length == 1 && Math.abs(ps[f][0] - ps[f][1]) == 1){
            doubleEdgeCase = f; break;
        }
    }

    if(singleEdgeCase >= 0){
        flag = singleEdgeCase;

        let x = 1;
        glag = -1;
        for(let e=0;e<4;++e){
            if(elasticBox.edgeList[e].dir[0] == room.edgeList[flag].dir[0] && elasticBox.edgeList[e].dir[1] == room.edgeList[flag].dir[1]){glag=e;break;}
        }
        dir = elasticBox.edgeList[glag].dir;

        if(Math.abs(room.edgeList[flag].dir[0]) > Math.abs(room.edgeList[flag].dir[1])){x=0;}

        let x0 = room.edgeList[flag].point[0][x];
        let x1 = elasticBox.edgeList[glag].point[0][x];
        //前进距离，那就是沿着room.edgeList[f].dir的移动距离，
        dis = (x0 - x1)*room.edgeList[flag].dir[x]; let ratio = dis/elasticBox.currentRange[x]; 
        if(dis<-0.01){ console.log("dis < 0 error"); }

        let outState = (ratio<0.3) ? 1 : 2;

        return {edgeIds:[flag],eEdgeIds:[glag], dirs:[dir], diss:[dis], outState:outState};
    }
    
    if(doubleEdgeCase >= 0){
        flag = doubleEdgeCase;

        let x = 1;
        glag = -1;
        for(let e=0;e<4;++e){
            if(elasticBox.edgeList[e].dir[0] == room.edgeList[flag].dir[0] && elasticBox.edgeList[e].dir[1] == room.edgeList[flag].dir[1]){glag=e;break;}
        }
        dir = elasticBox.edgeList[glag].dir;

        if(Math.abs(room.edgeList[flag].dir[0]) > Math.abs(room.edgeList[flag].dir[1])){x=0;}

        let x0 = room.edgeList[flag].point[0][x];
        let x1 = elasticBox.edgeList[glag].point[0][x];
        //前进距离，那就是沿着room.edgeList[f].dir的移动距离，
        dis = (x0 - x1)*room.edgeList[flag].dir[x]; let ratio = dis/elasticBox.currentRange[x];
        if(dis<-0.01){ console.log("dis < 0 error"); }

        let flagg = (doubleEdgeCase+1)%(room.edgeList);

        x = 1;
        let glagg = -1;
        for(let e=0;e<4;++e){
            if(elasticBox.edgeList[e].dir[0] == room.edgeList[flagg].dir[0] && elasticBox.edgeList[e].dir[1] == room.edgeList[flagg].dir[1]){glagg=e;break;}
        }
        let dirr = elasticBox.edgeList[glagg].dir;

        if(abs(room.edgeList[flagg].dir[0]) > abs(room.edgeList[flagg].dir[1])){x=0;}

        x0 = room.edgeList[flagg].point[0][x];
        x1 = elasticBox.edgeList[glagg].point[0][x];
        //前进距离，那就是沿着room.edgeList[f].dir的移动距离，
        let diss = (x0 - x1)*room.edgeList[flagg].dir[x]; let ratio1 = diss/elasticBox.currentRange[x];
        if(diss<-0.01){ console.log("dis < 0 error"); }

        return {edgeIds:[flag, flagg],eEdgeIds:[glag,glagg], dirs:[dir,dirr], diss:[dis,diss], out:(ratio>0.5)||(ratio1>0.5)};
    }
    
    console.log("not single or double case");
    return {edgeIds:[],eEdgeIds:[], dirs:[], diss:[], outState:-1};    
}

/*function checkRoomOut(room){
    let ret = []; //console.log("room.eBoxList.length");console.log(room.eBoxList.length);
    for(let e=0; e<room.eBoxList.length;++e){ 
        let res = checkRoomCrossEBox(room, room.eBoxList[e]);
        ret = ret.concat([{eBoxId:e, roomId:room.id, edgeIds:res.edgeIds, eEdgeIds:res.eEdgeIds, dirs:res.dirs, diss:res.diss, outState:res.outState}]);
    }
    return ret;
}

function newRoomOut(room, roomShape, newRoomId=-1){
    //calculate_room_division_evaluation函数有对房间形态的评分，我们可以将弹性盒割裂情况添加上去
    //decide函数中有对内部房间分割的决定，我需要修改那个函数从而实现弹性盒向房间形态对齐。
    let virtualRoomIndex = 100;
    newRoom = {id:virtualRoomIndex, type:room.type, eBoxList:[], edgeList:[]};
    newRoom.eBoxList = JSON.parse(JSON.stringify(room.eBoxList));
    newRoom.edgeList = JSON.parse(JSON.stringify(visualRoom(roomShape)));
   
    arrayOfRooms[virtualRoomIndex] = newRoom;

    res = checkRoomOut(newRoom);
    let deleteList = [];
    let historyList = [];
    let historyCnt = 0;
    for(let j = res.length-1; j>=0; --j){
        if(res[j].outState == 2){
            newRoom.eBoxList.splice(res[j].eBoxId,1);
            deleteList = deleteList.concat([res[j].eBoxId]);
            res.splice(j,1);
        }
        else if(res[j].outState == 0) { //console.log("something in new room");
            newRoom.eBoxList[j].roomId = (newRoomId==-1)?room.id:newRoomId;
            newRoom.eBoxList[j].eBoxId = historyCnt; historyCnt++;
            historyList = historyList.concat([newRoom.eBoxList[j]]);
            res.splice(j,1);
        }
    }

    if(res.length == 0){return {history:historyList, deleteList:deleteList, roomId:(newRoomId==-1)?room.id:newRoomId};}
    if(res.length>1){ console.log("more than one box"); return {history:[], deleteList:deleteList, roomId:room.id};}

    updateNeighbours(virtualRoomIndex);
    //console.log(res);
    var scheme;
    if(res[0].edgeIds.length==1){ //console.log("single edge case");
        scheme = recur({edgeId:res[0].eEdgeIds[0], eBoxId:res[0].eBoxId, roomId:virtualRoomIndex}, {dir:res[0].dirs[0], length:res[0].diss[0], flexLength:0});
        act(scheme, true, false);
    }
    else if(res[0].edgeIds.length==2){  //console.log("double edge case");
        scheme = recur({edgeId:res[0].eEdgeIds[0], eBoxId:res[0].eBoxId, roomId:virtualRoomIndex}, {dir:res[0].dirs[0], length:res[0].diss[0], flexLength:0});
        act(scheme, true, false);
        scheme = recur({edgeId:res[0].eEdgeIds[1], eBoxId:res[0].eBoxId, roomId:virtualRoomIndex}, {dir:res[0].dirs[1], length:res[0].diss[1], flexLength:0});
        act(scheme, true, false);
    }else{ console.log(res); console.log("not single or double case");}//console.log(res);}//

    delete arrayOfRooms[virtualRoomIndex];

    for(let i = 0; i < scheme.history.length; ++i) scheme.history[i].roomId = (newRoomId==-1)?room.id:newRoomId;
    return {history:scheme.history, deleteList:deleteList, roomId:(newRoomId==-1)?room.id:newRoomId};
}*/

const roomTypeSemanticLevels={
    "livingroom":["sofa","dining table","desk"],
    "kitchen":[],
    "bathroom":["a"],//(847,860)
    "balcony":[],
    "bedroom":["bed","desk"],
    "diningroom":["dining table"],
    "storage":["b"], //[558,683,684,687]
    "study":["desk"]
}

function checkRoomEboxSemantic(roomType, ebox){
    if(roomType=="bathroom"){ return ebox.bid<860 && ebox.bid>847 ? 0:-1;}
    if(roomType=="kitchen"){ return ebox.bid<865 && ebox.bid>859 ? 0:-1;}
    if(roomType=="storage"){ return (ebox.bid in [558,683,684,687]) ? 0:-1;}
    for(let i=0; i<roomTypeSemanticLevels[roomType].length; ++i){
        let nm = roomTypeSemanticLevels[roomType][i]; //console.log(nm);
        for(let o=0; o<ebox.objList.length; ++o){
            //console.log(ebox.objList[o].cs.toLowerCase());
            if(ebox.objList[o].cs.toLowerCase().includes(nm)) return i;
        }
    }
    
    return -1;
}


function seperationEvaluation(eBoxList, roomshape0, type0, roomshape1, type1){
    //originalRoom里有很多的弹性盒，这些弹性盒在如此的房间划分方案之下会有哪些问题呢？
    //其实每一个弹性盒是属于0还是属于1（甚至是哪条边应该往哪里移动）还是都不属于应该删了就可以从这里给出了。
    //存在evaluation里
    //因为这些内容其实都是在你评估房间划分时需要捎带手去做的。
    var eva = [[],[],[],{removedBox:0,confiltBox:0,conflictDis:0}];

    let virtualRoomIndex = 100; //while(virtualRoomIndex in arrayOfRooms){virtualRoomIndex++;}
    var newRoom0 = {id:virtualRoomIndex, type:type0, edgeList:JSON.parse(JSON.stringify(visualRoom(roomshape0)))};

    /*for(let ii=0;ii<4;++ii){console.log("roomId 0 edgeId " + String(ii));
    console.log(newRoom0.edgeList[ii].point[0][0]);
    console.log(newRoom0.edgeList[ii].point[0][1]);
    console.log(newRoom0.edgeList[ii].point[1][0]);
    console.log(newRoom0.edgeList[ii].point[1][1]);}*/
    
    virtualRoomIndex = 101; //while(virtualRoomIndex in arrayOfRooms){virtualRoomIndex++;}
    var newRoom1 = {id:virtualRoomIndex, type:type1, edgeList:JSON.parse(JSON.stringify(visualRoom(roomshape1)))};

    /*for(let ii=0;ii<4;++ii){console.log("roomId 1 edgeId " + String(ii));
    console.log(newRoom1.edgeList[ii].point[0][0]);
    console.log(newRoom1.edgeList[ii].point[0][1]);
    console.log(newRoom1.edgeList[ii].point[1][0]);
    console.log(newRoom1.edgeList[ii].point[1][1]);}*/
    
    //console.log(eBoxList);

    for(let e=0; e<eBoxList.length;++e){
        /*console.log("eBoxList[e]");
        console.log(eBoxList[e]);*/
        let res0 = checkRoomCrossEBox(newRoom0, eBoxList[e]);
        /*console.log("res0");
        console.log(res0);
        console.log("newRoom0");
        console.log(newRoom0);*/
        res0.semanticLevel = checkRoomEboxSemantic(type0, eBoxList[e]);
        if(res0.semanticLevel<0) res0.outState = 2;//check my semantic, if I failed
        let res1 = checkRoomCrossEBox(newRoom1, eBoxList[e]);
        /*console.log("res1");
        console.log(res1);
        console.log("newRoom1");
        console.log(newRoom1);*/
        res1.semanticLevel = checkRoomEboxSemantic(type1, eBoxList[e]);
        if(res1.semanticLevel<0) res1.outState = 2;//check my semantic, if I failed
        if(res0.outState == 2 && res1.outState == 2){
            eva[2]=eva[2].concat([{eBoxId:e, roomId:eBoxList[e].roomId, outState:3}]);
            eva[3].removedBox+=1;
        }else if(res0.outState == 2){ let res = res1;
            eva[1]=eva[1].concat([{eBoxId:e, roomId:newRoom1.id, edgeIds:res.edgeIds, eEdgeIds:res.eEdgeIds, dirs:res.dirs, diss:res.diss, outState:res.outState, semanticLevel:res.semanticLevel}]);
            if(res1.outState>0){eva[3].conflictBox+=1; for(let j=0;j<res.diss;++j)eva[3].conflictDis+=res.diss[j]; }
        }else if(res1.outState == 2){ let res = res0;
            eva[0]=eva[0].concat([{eBoxId:e, roomId:newRoom0.id, edgeIds:res.edgeIds, eEdgeIds:res.eEdgeIds, dirs:res.dirs, diss:res.diss, outState:res.outState, semanticLevel:res.semanticLevel}]);
            if(res0.outState>0){eva[3].conflictBox+=1; for(let j=0;j<res.diss;++j)eva[3].conflictDis+=res.diss[j]; }
        }else{
            console.log("some ebox is regarded as belonging to both room while seperating");
        }
    }//console.log(eva);
    return eva;
}

function seperationCalculation(eBoxList, roomshape, tp, evaluation){

    //originalRoom里有很多的弹性盒，这些弹性盒在如此的房间划分方案之下应该如何处置呢？
    //这里是否需要引入虚拟房间呢？其实是由于可能需要多次实践。我还是建议引入虚拟房间来进行操作。

    if(evaluation.length==0) return [];
    //evalution中有这个“每一个弹性盒是属于0还是属于1（甚至是哪条边应该往哪里移动）还是都不属于”的信息
    //这里主要是持续地去调用recur函数和updateNeighbours函数于两个虚拟房间中获得一份调整后的弹性盒布局方式
    //存在calculation中

    let currentRoomId = evaluation[0].roomId;
    if(!(currentRoomId in arrayOfRooms)){  arrayOfRooms[currentRoomId] = {
        id:currentRoomId, type:tp, edgeList:JSON.parse(JSON.stringify(visualRoom(roomshape))), eBoxList:[]
    };  }
    for(let e=0; e<evaluation.length; ++e){
        arrayOfRooms[currentRoomId].eBoxList = arrayOfRooms[currentRoomId].eBoxList.concat([eBoxList[evaluation[e].eBoxId]])
        arrayOfRooms[currentRoomId].eBoxList[e].eBoxId=e;
        arrayOfRooms[currentRoomId].eBoxList[e].roomId=currentRoomId;
    }

    let moveFlag = false;
    var scheme = {history:[]};
    for(let e=0; e<evaluation.length; ++e){
        let res = evaluation[e];
        if(res.edgeIds.length==1){ //console.log("single edge case");
            if(moveFlag){console.log("more than one box");} moveFlag=true;
            scheme = recur({edgeId:res.eEdgeIds[0], eBoxId:e, roomId:currentRoomId}, {dir:res.dirs[0], length:res.diss[0], flexLength:0});
            
            updateNeighbours(currentRoomId);
        }else if(res.edgeIds.length==2){  //console.log("double edge case");
            if(moveFlag){console.log("more than one box");}moveFlag=true;
            scheme = recur({edgeId:res.eEdgeIds[0], eBoxId:e, roomId:currentRoomId}, {dir:res.dirs[0], length:res.diss[0], flexLength:0});
            updateNeighbours(currentRoomId);
            scheme = recur({edgeId:res.eEdgeIds[1], eBoxId:e, roomId:currentRoomId}, {dir:res.dirs[1], length:res.diss[1], flexLength:0});
            updateNeighbours(currentRoomId);
        }else if(res.edgeIds.length != 0){console.log("not single or double case");}
    }

    for(let i = 0; i < scheme.history.length; ++i){
        //console.log(arrayOfRooms[scheme.history[i].roomId].eBoxList.length);
        let ie = scheme.history[i].edgeList;
        
        //console.log(arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId]);
        for(let ii=0;ii<4;++ii){
            arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].edgeList[ii].point[0][0] = ie[ii].point[0][0];
            arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].edgeList[ii].point[0][1] = ie[ii].point[0][1];
            arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].edgeList[ii].point[1][0] = ie[ii].point[1][0];
            arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].edgeList[ii].point[1][1] = ie[ii].point[1][1];
            arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].edgeList[ii].dir[0] = ie[ii].dir[0];
            arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].edgeList[ii].dir[1] = ie[ii].dir[1];
        }
        arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].currentCover = [[0,0],[0,0]];
        arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].currentCover[0][0] = Math.min(ie[0].point[0][0],ie[1].point[0][0],ie[2].point[0][0],ie[3].point[0][0]);
        arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].currentCover[0][1] = Math.max(ie[0].point[0][0],ie[1].point[0][0],ie[2].point[0][0],ie[3].point[0][0]);
        arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].currentCover[1][0] = Math.min(ie[0].point[0][1],ie[1].point[0][1],ie[2].point[0][1],ie[3].point[0][1]);
        arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].currentCover[1][1] = Math.max(ie[0].point[0][1],ie[1].point[0][1],ie[2].point[0][1],ie[3].point[1][1])
        
        arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].currentRange = [0,0];
        arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].currentRange[0] = arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].currentCover[0][1] - arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].currentCover[0][0];
        arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].currentRange[1] = arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].currentCover[1][1] - arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].currentCover[1][0];
        
    }

    return arrayOfRooms[currentRoomId].eBoxList; //就它的ebox吧
}

function seperationRemoving(evaluation2){
    for(let e=0; e<evaluation2.length; ++e){
        let ebox=arrayOfRooms[evaluation2[e].roomId].eBoxList[evaluation2[e].eBoxId];
        for(let o = 0; o < ebox.objList.length; ++o){
            removeObjectByUUID(ebox.objList[o].key);
        }
    }
}

function seperationAction(roomId, roomshape, tp, cal){
    //利用calculation进行操作。主要就是操作我自己的数据结构：arrayOfRooms里的东西，edgeList，eBoxList
    //我觉得可以考虑直接来重置。

    //从calculation中读取到一份调整后的弹性盒布局方式，
    //注意不要忘记把弹性盒的id改成roomId，

    if(!(roomId in arrayOfRooms)){  arrayOfRooms[roomId] = {
        id:roomId, type:tp, edgeList:[], eBoxList:[]
    };  }
    arrayOfRooms[roomId].eBoxList = JSON.parse(JSON.stringify(cal));
    arrayOfRooms[roomId].edgeList = JSON.parse(JSON.stringify(visualRoom(roomshape)));
    /*for(let ii=0;ii<4;++ii){console.log("roomId " + String(roomId) + "  edgeId " + String(ii));
    console.log(arrayOfRooms[roomId].edgeList[ii].point[0][0]);
    console.log(arrayOfRooms[roomId].edgeList[ii].point[0][1]);
    console.log(arrayOfRooms[roomId].edgeList[ii].point[1][0]);
    console.log(arrayOfRooms[roomId].edgeList[ii].point[1][1]);}*/
    for(let i = 0; i < arrayOfRooms[roomId].edgeList.length; ++i){
        arrayOfRooms[roomId].edgeList[i].roomId=roomId;
    }
    arrayOfRooms[roomId].type = tp;console.log(roomSemanticState);
    while(roomSemanticState.length <= roomId){roomSemanticState=roomSemanticState.concat([[]]);}
    while(roomSemanticState[roomId].length < roomTypeSemanticLevels[tp].length){roomSemanticState[roomId]=roomSemanticState[roomId].concat([0]);}

    for(let i = 0; i < cal.length; ++i){
        //console.log(arrayOfRooms[cal[i].roomId].eBoxList[i]);
        arrayOfRooms[roomId].eBoxList[i].roomId = roomId;
        for(let ii=0;ii<4;++ii){arrayOfRooms[roomId].eBoxList[i].edgeList[ii].roomId = roomId;}
    
        for(let j = 0; j < arrayOfRooms[roomId].eBoxList[i].objList.length; ++j){
            let obj = arrayOfRooms[roomId].eBoxList[i].objList[j];

            if(obj.type == "toMain"){
                let obj0 = arrayOfRooms[roomId].eBoxList[i].objList[0];
                obj.position[0] = Math.cos(obj0.orient) * obj.tr[0] + Math.sin(obj0.orient) * obj.tr[2] + obj0.position[0];
                obj.position[1] = obj.tr[1] + obj0.position[1];
                obj.position[2] = Math.cos(obj0.orient) * obj.tr[2] - Math.sin(obj0.orient) * obj.tr[0] + obj0.position[2];
                try{
                    transformObject3DOnly(obj.key, obj.position, 'position');
                }catch(error){}
            }
            else{
                let wall = arrayOfRooms[roomId].eBoxList[i].edgeList[obj.wallid];
                
                obj.position[0] = wall.point[0][0]*obj.ver+wall.point[1][0]*(1-obj.ver)+wall.dir[0]*obj.dis;
                obj.position[1] = obj.height;
                obj.position[2] = wall.point[0][1]*obj.ver+wall.point[1][1]*(1-obj.ver)+wall.dir[1]*obj.dis;
                try{
                    transformObject3DOnly(obj.key, obj.position, 'position');
                }catch(error){}
            }
        }

        roomSemanticState[roomId][checkRoomEboxSemantic(tp,arrayOfRooms[roomId].eBoxList[i])] = 1;

    }
    updateNeighbours(roomId);
    console.log(arrayOfRooms[roomId]);
    if(cal.length>0){delete arrayOfRooms[cal[0].roomId];}
    return;
}

function seperating(eBoxList, room0, room1, evaluation){
    var calculation0 = seperationCalculation(eBoxList, room0.room_shape, room0.type, evaluation[0]);
    console.log(room1.room_shape);
    var calculation1 = seperationCalculation(eBoxList, room1.room_shape, room1.type, evaluation[1]);
    seperationRemoving(evaluation[2]);
    seperationAction(parseInt(room0.id), room0.room_shape, room0.type, calculation0); console.log(0);
    console.log(room1.room_shape);
    seperationAction(parseInt(room1.id), room1.room_shape, room1.type, calculation1); console.log(1);
    return;
}

function merging(room0, room1, newRoomShape){

}

//递归方法
function recur(info, path){
    //console.log(path);
    //console.log("recur");
    if(info.eBoxId == -1 && path.flexLength > 0){ let scheme = {flexLength:path.flexLength, moveLength:0, history:[]}; return scheme;} //reached an wall, should stop
    
    //reached an wall, should stop
    //info需要包含什么信息
        //目前的房间id
        //当前弹性盒的id是什么

    //info.roomId:0
    //info.eBoxId:-1
    //info.edgeId:?
    //var newEdgeId = (info.edgeId + 2)%4;
    var s = (Math.abs(path.dir[0]) > Math.abs(path.dir[1]))?0:1;
    //console.log(arrayOfRooms[info.roomId].edgeList[info.edgeId]);//return;
    if(info.eBoxId != -1){
    if(arrayOfRooms[info.roomId].eBoxList[info.eBoxId].edgeList[info.edgeId].neighbourEdge.length>1 && path.dir[s] == -arrayOfRooms[info.roomId].eBoxList[info.eBoxId].edgeList[info.edgeId].dir[s]){
        return {flexLength:path.flexLength, moveLength:path.length, history:[]};
    }}
    var currentEdge = info.eBoxId == -1 ? arrayOfRooms[info.roomId].edgeList[info.edgeId] : arrayOfRooms[info.roomId].eBoxList[info.eBoxId].edgeList[(info.edgeId+2)%4];
    var currentEBox = info.eBoxId == -1 ? null : arrayOfRooms[info.roomId].eBoxList[info.eBoxId];
    //console.log(currentEBox);
    //path需要包含什么信息：
        //总共需要向哪个方向移动多少
        //递归路径上的各个弹性盒的相关信息
            //在该方向上的长度
            //在该方向上的可缩放程度
            //
    
    //path.dir
    //path.length
    //path.flexLength=0

    //add my own infomation into path
    //
    if(currentEdge.neighbourEdge.length == 0){ //no children, can move
        if(info.eBoxId == -1){ let scheme = {flexLength:path.flexLength, moveLength:path.length, history:[]}; return scheme;} //only moving wall, not effecting elastic boxes
        //console.log("fucking it is here"); console.log(path.length);
        let newEBox = JSON.parse(JSON.stringify(currentEBox));
        for(let e = 0; e < newEBox.edgeList.length; ++e){
            newEBox.edgeList[e].point[0][0] += path.dir[0]*path.length;
            newEBox.edgeList[e].point[0][1] += path.dir[1]*path.length;
            newEBox.edgeList[e].point[1][0] += path.dir[0]*path.length;
            newEBox.edgeList[e].point[1][1] += path.dir[1]*path.length;
        }
        newEBox.currentCover[0][0] += path.dir[0]*path.length;
        newEBox.currentCover[0][1] += path.dir[0]*path.length;
        newEBox.currentCover[1][0] += path.dir[1]*path.length;
        newEBox.currentCover[1][1] += path.dir[1]*path.length;
        //console.log(newEBox);
        //{edgeId:1, eBoxId:-1,roomId:1, edgeList:[ [point:[[0,0],[0,0]], dir:[0,0]], [point:[[0,0],[0,0]], dir:[0,0]], ...... ],}
        return {flexLength:path.flexLength, moveLength:path.length, history:[newEBox]};
    }
    
    if(currentEBox.currentRange[s]>=currentEBox.dirRange[s][1] && (path.dir[s]*currentEdge.dir[s]) > 0.5){
        //seperate the two boxes evenif they are close to each other. because myself is too large
        let newEBox = JSON.parse(JSON.stringify(currentEBox));
        for(let e = 0; e < newEBox.edgeList.length; ++e){
            newEBox.edgeList[e].point[0][0] += path.dir[0]*path.length;
            newEBox.edgeList[e].point[0][1] += path.dir[1]*path.length;
            newEBox.edgeList[e].point[1][0] += path.dir[0]*path.length;
            newEBox.edgeList[e].point[1][1] += path.dir[1]*path.length;
        }
        //{edgeId:1, eBoxId:-1,roomId:1, edgeList:[ [point:[[0,0],[0,0]], dir:[0,0]], [point:[[0,0],[0,0]], dir:[0,0]], ...... ],}
        return {flexLength:path.flexLength, moveLength:path.length, history:[newEBox]};
    }
    
    let newPath = JSON.parse(JSON.stringify(path));
    newPath.flexLength += currentEBox.currentRange[s];
    /*if(currentEBox.currentRange[s] < currentEBox.dirRange[s][1] && currentEBox.currentRange[s] > currentEBox.dirRange[s][0]){ console.log("adding flexlength"); }
    else{console.log("not adding");}*/
    
    let synScheme = {flexLength:path.flexLength, moveLength:path.length, history:[]};

    for(let e = 0; e < currentEdge.neighbourEdge.length; ++e){
        let newInfo = JSON.parse(JSON.stringify(currentEdge.neighbourEdge[e]));
        sch = recur(newInfo, newPath);
        synScheme.moveLength = Math.min(synScheme.moveLength,sch.moveLength);
        synScheme.history = synScheme.history.concat(sch.history);
        synScheme.flexLength = sch.flexLength; //console.log(sch.flexLength); console.log(currentEBox.currentRange[1]);
    }
    
    //综合返回的ret和path来决断此弹性盒的调整方式

    //from synScheme.moveLength we can get one length
    //from path.length we can get one length
    //from currentEBox.dirRange we can get if this box can cover the gap between these two and how much can it cover
    //it should cover this gap according to the sign
    let frontLength = path.length;
    let backLength = synScheme.moveLength;
    //console.log(backLength);console.log("backLength");
    //console.log(frontLength);console.log("frontLength");

    if (Math.abs(frontLength - backLength) > 0.001){
        frontLength = backLength + (frontLength - backLength) * currentEBox.currentRange[s] / synScheme.flexLength;
        //console.log("gap between back and front");
        //if(currentEBox.currentRange[s] < currentEBox.dirRange[s][1] && currentEBox.currentRange[s] > currentEBox.dirRange[s][0]){console.log("in the range");
        //}else{ console.log("out of range");} //frontLength = backLength;//though they are the same, what should be the value    
    }
    //console.log(backLength);console.log("backLength");
    //console.log(frontLength);console.log("frontLength");
    //console.log(currentEBox);// edgeId == 1 is back, with lower z(1); edgeId==3 is front, with higher z(1);
    /*{
        console.log(currentEBox.edgeList[1].point[0][0]);
        console.log(currentEBox.edgeList[1].point[0][1]);
        console.log(currentEBox.edgeList[1].point[1][0]);
        console.log(currentEBox.edgeList[1].point[1][1]);
        console.log(currentEBox.edgeList[3].point[0][0]);
        console.log(currentEBox.edgeList[3].point[0][1]);
        console.log(currentEBox.edgeList[3].point[1][0]);
        console.log(currentEBox.edgeList[3].point[1][1]);
    }*/
    let newEBox = JSON.parse(JSON.stringify(currentEBox));
    for(let i = 0; i < 4; ++i){
        let e = (info.edgeId + i)%4;
        let pl = frontLength;
        if (i == 2 || i == 3)pl = backLength;
        newEBox.edgeList[e].point[0][0] += path.dir[0]*pl;
        newEBox.edgeList[e].point[0][1] += path.dir[1]*pl;

        if (i == 2 || i == 1)pl = backLength;
        else pl = frontLength;
        newEBox.edgeList[e].point[1][0] += path.dir[0]*pl;
        newEBox.edgeList[e].point[1][1] += path.dir[1]*pl;
    }

    /*{
        console.log(newEBox.edgeList[1].point[0][0]);
        console.log(newEBox.edgeList[1].point[0][1]);
        console.log(newEBox.edgeList[1].point[1][0]);
        console.log(newEBox.edgeList[1].point[1][1]);
        console.log(newEBox.edgeList[3].point[0][0]);
        console.log(newEBox.edgeList[3].point[0][1]);
        console.log(newEBox.edgeList[3].point[1][0]);
        console.log(newEBox.edgeList[3].point[1][1]);
    }*/

    newEBox.currentCover = [[Math.min(newEBox.edgeList[0].point[0][0],newEBox.edgeList[1].point[0][0],newEBox.edgeList[2].point[0][0],newEBox.edgeList[3].point[0][0]),Math.max(newEBox.edgeList[0].point[0][0],newEBox.edgeList[1].point[0][0],newEBox.edgeList[2].point[0][0],newEBox.edgeList[3].point[0][0])],
                            [Math.min(newEBox.edgeList[0].point[0][1],newEBox.edgeList[1].point[0][1],newEBox.edgeList[2].point[0][1],newEBox.edgeList[3].point[0][1]),Math.max(newEBox.edgeList[0].point[0][1],newEBox.edgeList[1].point[0][1],newEBox.edgeList[2].point[0][1],newEBox.edgeList[3].point[0][1])]];
    newEBox.currentRange = [newEBox.currentCover[0][1]-newEBox.currentCover[0][0],newEBox.currentCover[1][1]-newEBox.currentCover[1][0]];
    //console.log(newEBox);

    synScheme.history = synScheme.history.concat([newEBox]);
    let scheme = {flexLength:synScheme.flexLength, moveLength:frontLength, history:synScheme.history};
    //scheme需要包含什么信息
        //已移动长度moveLength，相关总长度flexLength，历史弹性盒的调整方式（包括自己）history
    return scheme;
}

function cover(cover0, cover1){ return (cover0[0][0] < cover1[0][1] && cover1[0][0] < cover0[0][1] && cover0[1][0] < cover1[1][1] && cover1[1][0] < cover0[1][1]); }

function toEbox(p0, p1){ //console.log(p0);console.log(p1);
    ebox = {edgeList:[{},{},{},{}], currentCover:[[Math.min(p0[0], p1[0]),Math.max(p0[0], p1[0])],[Math.min(p0[1], p1[1]),Math.max(p0[1], p1[1])]], currentRange:[Math.abs(p0[0]-p1[0]),Math.abs(p0[1]-p1[1])]};

    ebox.edgeList[0] ={edgeId:0,eBoxId:-1,point:[[ebox.currentCover[0][0],ebox.currentCover[1][0]],[ebox.currentCover[0][0],ebox.currentCover[1][1]]],dir:[ 1,0], onWall:false}
    //ebox.edgeList[0].onWall = (p1.length > 2 && p1[2] && ebox.edgeList[0].point.indexOf([p1[0],p1[1]]) >=0);
    ebox.edgeList[1] ={edgeId:1,eBoxId:-1,point:[[ebox.currentCover[0][0],ebox.currentCover[1][1]],[ebox.currentCover[0][1],ebox.currentCover[1][1]]],dir:[0,-1], onWall:false}
    //ebox.edgeList[1].onWall = (p1.length > 2 && p1[2] && ebox.edgeList[1].point.indexOf([p1[0],p1[1]]) >=0);
    ebox.edgeList[2] ={edgeId:2,eBoxId:-1,point:[[ebox.currentCover[0][1],ebox.currentCover[1][1]],[ebox.currentCover[0][1],ebox.currentCover[1][0]]],dir:[-1,0], onWall:false}
    //ebox.edgeList[2].onWall = (p1.length > 2 && p1[2] && ebox.edgeList[2].point.indexOf([p1[0],p1[1]]) >=0);
    ebox.edgeList[3] ={edgeId:3,eBoxId:-1,point:[[ebox.currentCover[0][1],ebox.currentCover[1][0]],[ebox.currentCover[0][0],ebox.currentCover[1][0]]],dir:[ 0,1], onWall:false}
    //ebox.edgeList[3].onWall = (p1.length > 2 && p1[2] && ebox.edgeList[3].point.indexOf([p1[0],p1[1]]) >=0);
    
    if(p0[0]<p1[0] && p0[1]<p1[1]){
        ebox.edgeList[2].onWall = true; ebox.edgeList[1].onWall = true;
    }else if(p0[0]<p1[0] && p0[1]>p1[1]){
        ebox.edgeList[2].onWall = true; ebox.edgeList[3].onWall = true;
    }else if(p0[0]>p1[0] && p0[1]<p1[1]){
        ebox.edgeList[0].onWall = true; ebox.edgeList[1].onWall = true;
    }else{
        ebox.edgeList[0].onWall = true; ebox.edgeList[3].onWall = true;
    }

    return ebox;
}

var roomTypeSemanticLevelEboxes = {};
var roomSemanticState = [[]];
function searchBoxBasic(currentRoom){
    if(!(currentRoom.type in roomTypeSemanticLevelEboxes)){
        //load all things related to this function from the backend
        roomTypeSemanticLevelEboxes[currentRoom.type] = [];

        $.ajax({
            type: "POST",
            contentType: "application/json; charset=utf-8",
            url: `/eboxes/${currentRoom.type}`,
            async: false,
            success: function (msg) {
                roomTypeSemanticLevelEboxes[currentRoom.type] = msg.ls;
                //alert(msg);
            }
        });
    }

    while(roomSemanticState.length <= currentRoom.id){
        roomSemanticState=roomSemanticState.concat([[]]);
    }
    
    //search something under current situation
    if(currentRoom.type == "bedroom"){
        if(roomSemanticState[currentRoom.id].length==0) roomSemanticState[currentRoom.id]=[0,0];
        
        if(roomSemanticState[currentRoom.id][0] == 0){//console.log("bedroom level 0");
            return roomTypeSemanticLevelEboxes[currentRoom.type][0];
        }else if(roomSemanticState[currentRoom.id][1] == 0){//console.log("bedroom level 1");
            return roomTypeSemanticLevelEboxes[currentRoom.type][1];
        }else {
            return [];
        }
    }
    else if(currentRoom.type == "livingroom"){
        if(roomSemanticState[currentRoom.id].length==0) roomSemanticState[currentRoom.id]=[0,0,0];

        if(roomSemanticState[currentRoom.id][0] == 0){
            return roomTypeSemanticLevelEboxes[currentRoom.type][0];//
        }else if(roomSemanticState[currentRoom.id][1] == 0){
            return roomTypeSemanticLevelEboxes[currentRoom.type][1];
        }else if(roomSemanticState[currentRoom.id][2] == 0){
            return roomTypeSemanticLevelEboxes[currentRoom.type][2];
        }else {
            return [];
        }
    }else if(currentRoom.type == "diningroom"){
        if(roomSemanticState[currentRoom.id].length==0) roomSemanticState[currentRoom.id]=[0];

        if(currentRoom.eBoxList.length == 0){
            return roomTypeSemanticLevelEboxes[currentRoom.type][0];//
        }else {
            return [];
        }
    }else if(currentRoom.type == "bathroom"){
        if(roomSemanticState[currentRoom.id].length==0) roomSemanticState[currentRoom.id]=[0];
        
        if(currentRoom.eBoxList.length == 0){
            return roomTypeSemanticLevelEboxes[currentRoom.type][0];//
        }else {
            return [];
        }
    }else if(currentRoom.type == "storage"){
        if(roomSemanticState[currentRoom.id].length==0) roomSemanticState[currentRoom.id]=[0];
        
        if(currentRoom.eBoxList.length == 0){
            return roomTypeSemanticLevelEboxes[currentRoom.type][0];//
        }else {
            return [];
        }
    }else if(currentRoom.type == "kitchen"){
        if(roomSemanticState[currentRoom.id].length==0) roomSemanticState[currentRoom.id]=[0];
        
        if(currentRoom.eBoxList.length == 0){
            return roomTypeSemanticLevelEboxes[currentRoom.type][0];//
        }else {
            return [];
        }
    }else if(currentRoom.type == "balcony"){
        roomSemanticState[currentRoom.id]=[];
        
        return [];
    }else{
        alert("unimplemented function");
    }

    return [];
}

function adding(info){
    currentRoom = arrayOfRooms[info.roomid];//.eBoxList;///console.log(currentRoom);
    
    var funcBoxes = searchBoxBasic(currentRoom);
    for(let f=0; f<funcBoxes.length;++f){
        let box = searchingBox(funcBoxes[f], currentRoom)
        if(box){ //console.log("selected funcbox id " + String(f));
            let eid = addingCalc(box, info.roomid);
            addingAct(info.roomid, eid); break;
        }
    }
}

function transformBox(f,spin,trans,scale){///console.log(f);
    var e = JSON.parse(JSON.stringify(f));
    for(let p=0;p<4;++p){
        e.edgeList[p].point[0] = [f.edgeList[p].point[0][0]*scale[0]*spin[0][0]+f.edgeList[p].point[0][1]*scale[1]*spin[0][1]+trans[0], f.edgeList[p].point[0][0]*scale[0]*spin[1][0]+f.edgeList[p].point[0][1]*scale[1]*spin[1][1]+trans[1]]
        e.edgeList[p].point[1] = [f.edgeList[p].point[1][0]*scale[0]*spin[0][0]+f.edgeList[p].point[1][1]*scale[1]*spin[0][1]+trans[0], f.edgeList[p].point[1][0]*scale[0]*spin[1][0]+f.edgeList[p].point[1][1]*scale[1]*spin[1][1]+trans[1]]
        e.edgeList[p].dir = [f.edgeList[p].dir[0]*spin[0][0]+f.edgeList[p].dir[1]*spin[0][1], f.edgeList[p].dir[0]*spin[1][0]+f.edgeList[p].dir[1]*spin[1][1]]
        e.edgeList[p].neighbourEdge = [];
    }//console.log(e);
    e.currentCover = [[Math.min(e.edgeList[0].point[0][0],e.edgeList[1].point[0][0],e.edgeList[2].point[0][0],e.edgeList[3].point[0][0]),Math.max(e.edgeList[0].point[0][0],e.edgeList[1].point[0][0],e.edgeList[2].point[0][0],e.edgeList[3].point[0][0])],
                      [Math.min(e.edgeList[0].point[0][1],e.edgeList[1].point[0][1],e.edgeList[2].point[0][1],e.edgeList[3].point[0][1]),Math.max(e.edgeList[0].point[0][1],e.edgeList[1].point[0][1],e.edgeList[2].point[0][1],e.edgeList[3].point[0][1])]];
    e.currentRange = [e.currentCover[0][1]-e.currentCover[0][0],e.currentCover[1][1]-e.currentCover[1][0]];
    return e;
}


let lock=2;
function searchingBox(funcBox, currentRoom){ //if(lock==0){return false;}else{lock-=1;}
    //再从房间的各个点中，找到一个点去贴着放这个fucnBox，再用for cover来检查是否和已有的弹性盒碰撞。
    let I=[-1];
    let spin = [[[1,0],[0,1]],[[0,1],[-1,0]],[[-1,0],[0,-1]],[[0,-1],[1,0]]];
    for(let i=0;i<4;++i){
        if(funcBox.edgeList[i].onWall && funcBox.edgeList[(i+1)%4].onWall){I = [i];}
    }
    if(I[0]==-1){
        for(let i=0;i<4;++i){ if(funcBox.edgeList[i].onWall){I=[(i+3)%4,i];}}
    }
    
    for(let ii = 0; ii < I.length; ++ii){
        let fi = I[ii]; //console.log(ii); console.log(fi);
        for(let pp=0; pp < currentRoom.edgeList.length; ++pp){ //console.log(pp);
            let ed = currentRoom.edgeList[pp];  let pt = [ed.point[1][0],ed.point[1][1]];
            let nexted = currentRoom.edgeList[(pp+1)%currentRoom.edgeList.length];
            
            if((nexted.point[1][0]-nexted.point[0][0])*ed.dir[0]+(nexted.point[1][1]-nexted.point[0][1])*ed.dir[1]<0) continue;
            
            let dirs = [[ed.dir[0],ed.dir[1]],[nexted.dir[0],nexted.dir[1]]];let v=0;
            for(; v<4;++v){
                let DIRS = [[funcBox.edgeList[(fi+v)%4].dir[0],funcBox.edgeList[(fi+v)%4].dir[1]],[funcBox.edgeList[(fi+v+1)%4].dir[0],funcBox.edgeList[(fi+v+1)%4].dir[1]]];
                if((DIRS[0][0]==dirs[0][0]&&DIRS[0][1]==dirs[0][1]&&DIRS[1][0]==dirs[1][0]&&DIRS[1][1]==dirs[1][1])
                 ||(DIRS[1][0]==dirs[0][0]&&DIRS[1][1]==dirs[0][1]&&DIRS[0][0]==dirs[1][0]&&DIRS[0][1]==dirs[1][1])){
                    break;
                 }
            }
            if(v==4){console.log("no corresponding direction v found"); return false;}
            
            let p = [funcBox.edgeList[fi].point[1][0],funcBox.edgeList[fi].point[1][1]];
            let trans = [
                pt[0]-spin[v][0][0]*p[0]-spin[v][0][1]*p[1],
                pt[1]-spin[v][1][0]*p[0]-spin[v][1][1]*p[1]
            ];
            let blankBox = transformBox(funcBox, spin[v], trans, [1,1]);
            
            let coverFlag = false;
            for(let e=0; e < currentRoom.eBoxList.length; ++e){
                coverFlag = cover(currentRoom.eBoxList[e].currentCover, blankBox.currentCover);
                if(coverFlag) break;
            }if(coverFlag) continue;  //console.log("searchingBox");
            let res = checkRoomCrossEBox(currentRoom, blankBox); if(res.outState != 0) continue;

            /*{
                console.log("room0 edge0");
                console.log(arrayOfRooms[0].edgeList[0].point[0][0]);
                console.log(arrayOfRooms[0].edgeList[0].point[0][1]);
                console.log(arrayOfRooms[0].edgeList[0].point[1][0]);
                console.log(arrayOfRooms[0].edgeList[0].point[1][1]);
            
                console.log("hjk room0 edge0");
                console.log(arrayOfRoomPoints[0].position[0]);
                console.log(arrayOfRoomPoints[0].position[1]);
                console.log(arrayOfRoomPoints[1].position[0]);
                console.log(arrayOfRoomPoints[1].position[1]);
                
                console.log("blankBox edge1");
                console.log(blankBox.edgeList[1].point[0][0]);
                console.log(blankBox.edgeList[1].point[0][1]);
                console.log(blankBox.edgeList[1].point[1][0]);
                console.log(blankBox.edgeList[1].point[1][1]);}*/





            return blankBox;
        }
    }

    return false;
}

function addingCalc(box, i){
    for(let j = 0; j < box.objList.length; ++j){
        let obj = box.objList[j];

        if(obj.type == "toMain"){
            let obj0 = box.objList[0]; obj.position = [0,0,0];
            obj.position[0] = Math.cos(obj0.orient) * obj.tr[0] + Math.sin(obj0.orient) * obj.tr[2] + obj0.position[0];
            obj.position[1] = obj.tr[1] + obj0.position[1];
            obj.position[2] = Math.cos(obj0.orient) * obj.tr[2] - Math.sin(obj0.orient) * obj.tr[0] + obj0.position[2];

            obj.orient = obj.ro + obj0.orient;
        }
        else{
            let wall = box.edgeList[obj.wallid]; obj.position = [0,0,0];
            obj.position[0] = wall.point[0][0]*obj.ver+wall.point[1][0]*(1-obj.ver)+wall.dir[0]*obj.dis;
            obj.position[2] = wall.point[0][1]*obj.ver+wall.point[1][1]*(1-obj.ver)+wall.dir[1]*obj.dis;
            
            if(Math.abs(wall.dir[0]) > Math.abs(wall.dir[1])){
                if(wall.dir[0] > 0){ obj.orient = obj.ori; }
                else{ obj.orient = obj["ori"] + Math.PI; }
            }else{
                if(wall.dir[1] > 0){obj.orient = obj.ori-Math.PI/2.0;}
                else{obj.orient = obj.ori+Math.PI/2.0;}
            }
        }
    }
    let currentRoom = arrayOfRooms[i];
    box.eBoxId = currentRoom.eBoxList.length;
    box.roomId = i;
    currentRoom.eBoxList = currentRoom.eBoxList.concat([box]);
    roomSemanticState[i][checkRoomEboxSemantic(currentRoom.type,box)] = 1;
    //console.log(roomSemanticState[0][0]);console.log(roomSemanticState[0][1]);//console.log(currentRoom.eBoxList); //console.log(currentRoom.eBoxList[0]);
    return box.eBoxId;
}

function addingAct(rid, eid){
    let box = arrayOfRooms[rid].eBoxList[eid]; //console.log(box);

    for(let j = 0; j < box.objList.length; ++j){
        let obj = box.objList[j];
        var f = 'obj';
        var stt = 'origin';
        if('currentState' in obj && isNaN(parseInt(obj.id))){
            f = 'glb';
            stt = obj.currentState;
        }
        if(!(obj.id in objectCache)) {
            loadObjectToCache(obj.id, anchor = addingAct, anchorArgs = [rid, eid], format = f);
            return;
        }
    }//console.log(box);

    for(let j = 0; j < box.objList.length; ++j){
        let obj = box.objList[j];
        let r = addObjectFromCache(
            modelId=obj.id,
            transform={'translate': obj.position,'rotate': [0, obj.orient, 0],'scale': obj.scl}
        );
        obj.key = r.name;
    }
    
}

function edgeStatus(e,f){ //if(Math.abs(f.dir[0])==0)f.dir[0]=0;if(Math.abs(f.dir[1])==0)f.dir[1]=0;if(Math.abs(e.dir[0])==0)e.dir[0]=0;if(Math.abs(e.dir[1])==0)e.dir[1]=0;
    let fx = (Math.abs(f.dir[0]) > Math.abs(f.dir[1])) ? 0 : 1;
    let ex = (Math.abs(e.dir[0]) > Math.abs(e.dir[1])) ? 0 : 1;
    if(fx == ex && f.dir[fx] == -e.dir[ex]){
        if(Math.abs(f.point[0][fx]-e.point[0][ex])<0.05 && Math.max(f.point[0][1-fx],f.point[1][1-fx]) > Math.min(e.point[0][1-ex],e.point[1][1-ex]) && Math.max(e.point[0][1-ex],e.point[1][1-ex]) > Math.min(f.point[0][1-fx],f.point[1][1-fx])){
            return 1; //back to back close
        }
    }
    else if(fx == ex && f.dir[fx] == e.dir[ex]){
        if(Math.abs(f.point[0][fx]-e.point[0][ex])<0.05 && Math.max(f.point[0][1-fx],f.point[1][1-fx]) > Math.min(e.point[0][1-ex],e.point[1][1-ex]) && Math.max(e.point[0][1-ex],e.point[1][1-ex]) > Math.min(f.point[0][1-fx],f.point[1][1-fx])){
            
            /*console.log("f");
            console.log(f.roomId);
            console.log(f.eBoxId);
            console.log(f.edgeId);
            console.log("e");
            console.log(e.roomId);
            console.log(e.eBoxId);
            console.log(e.edgeId);*/
            return 2; //face to back close
        }
    }
    else if(edgeCross(e, f)){
        return 3; //cross
    }

    return 0; //otherwise
}

function updateNeighbours(r){ //if(lock==0){return;}else{lock=0;}
    let edgeList0 = arrayOfRooms[r].edgeList;
    for(let i = 0; i < edgeList0.length; ++i){
        edgeList0[i].neighbourEdge = [];
    } 
    for(let j = 0; j < arrayOfRooms[r].eBoxList.length; ++j){
        let edgeList1 = arrayOfRooms[r].eBoxList[j].edgeList;
        for(let jj = 0; jj < edgeList1.length; ++jj){
            edgeList1[jj].neighbourEdge = [];
        }
        //let edgeList1 = arrayOfRooms[r].eBoxList[j].edgeList;
        for(let ii = 0; ii < edgeList0.length; ++ii){
            for(let jj = 0; jj < arrayOfRooms[r].eBoxList[j].edgeList.length; ++jj){
                let a = edgeStatus(edgeList0[ii],edgeList1[jj]);
                if(a == 2){
                    edgeList0[ii].neighbourEdge = edgeList0[ii].neighbourEdge.concat([{edgeId:jj, eBoxId:j, roomId:r}])
                    edgeList1[jj].neighbourEdge = edgeList1[jj].neighbourEdge.concat([{edgeId:ii, eBoxId:-1,roomId:r}])
                    //console.log("close");
                }
                else if(a==1 || a==3){
                    console.log("cross");
                }
                if(ii==4 && jj==1){
                    console.log("a here");
                    console.log(a);
                    console.log(ii);
                    console.log(edgeList0[ii].point[0][0]);
                    console.log(edgeList0[ii].point[0][1]);
                    console.log(edgeList0[ii].point[1][0]);
                    console.log(edgeList0[ii].point[1][1]);
                    console.log(edgeList0[ii].dir[0]);
                    console.log(edgeList0[ii].dir[1]);
                    console.log(jj);
                    console.log(edgeList1[jj].point[0][0]);
                    console.log(edgeList1[jj].point[0][1]);
                    console.log(edgeList1[jj].point[1][0]);
                    console.log(edgeList1[jj].point[1][1]);
                    console.log(edgeList1[jj].dir[0]);
                    console.log(edgeList1[jj].dir[1]);
                }
            }
        }
    }
    if(arrayOfRooms[r].eBoxList.length > 0){
        console.log(1);
        console.log(arrayOfRooms[r].edgeList[4].point[0][0]);
        console.log(arrayOfRooms[r].edgeList[4].point[0][1]);
        console.log(arrayOfRooms[r].edgeList[4].point[1][0]);
        console.log(arrayOfRooms[r].edgeList[4].point[1][1]);
        console.log(arrayOfRooms[r].edgeList[4].dir[0]);
        console.log(arrayOfRooms[r].edgeList[4].dir[1]);
        console.log(0);
        console.log(1);
        console.log(arrayOfRooms[r].eBoxList[0].edgeList[1].point[0][0]);
        console.log(arrayOfRooms[r].eBoxList[0].edgeList[1].point[0][1]);
        console.log(arrayOfRooms[r].eBoxList[0].edgeList[1].point[1][0]);
        console.log(arrayOfRooms[r].eBoxList[0].edgeList[1].point[1][1]);
        console.log(arrayOfRooms[r].eBoxList[0].edgeList[1].dir[0]);
        console.log(arrayOfRooms[r].eBoxList[0].edgeList[1].dir[1]);
    }
    console.log("updateNeighbours");
    console.log(arrayOfRooms[r].edgeList);
    //console.log(arrayOfRooms[r].eBoxList[0].edgeList);

    for(let i = 0; i < arrayOfRooms[r].eBoxList.length; ++i){
        edgeList0 = arrayOfRooms[r].eBoxList[i].edgeList;
        //arrayOfRooms[r].eBoxList[i].edgeList.neighbourEdge = []; //edgeList0 = arrayOfRooms[r].eBoxList[i].edgeList;
        for(let j = i+1; j < arrayOfRooms[r].eBoxList.length; ++j){
            edgeList1 = arrayOfRooms[r].eBoxList[j].edgeList;
            //edgeList1 = arrayOfRooms[r].eBoxList[j].edgeList;
            for(let ii = 0; ii < edgeList0.length; ++ii){
                for(let jj = 0; jj < edgeList1.length; ++jj){
                    let a = edgeStatus(edgeList0[ii],edgeList1[jj]);
                    if(a == 1){
                        edgeList0[ii].neighbourEdge = edgeList0[ii].neighbourEdge.concat([{edgeId:jj, eBoxId:j, roomId:r}])
                        edgeList1[jj].neighbourEdge = edgeList1[jj].neighbourEdge.concat([{edgeId:ii, eBoxId:i, roomId:r}])
                        /*console.log(ii); console.log(jj);
                        console.log(a); console.log(edgeList0[1].dir[0]); console.log(edgeList0[1].dir[1]); console.log(edgeList1[2].dir[0]); console.log(edgeList1[2].dir[1]);
                        console.log(edgeList0[1].point[0][0]);
                        console.log(edgeList0[1].point[0][1]);
                        console.log(edgeList0[1].point[1][0]);
                        console.log(edgeList0[1].point[1][1]);
                        console.log(edgeList1[2].point[0][0]);
                        console.log(edgeList1[2].point[0][1]);
                        console.log(edgeList1[2].point[1][0]);
                        console.log(edgeList1[2].point[1][1]);*/
                    }
                    else if(a==3 || a==2){
                        console.log("cross"); /*console.log(ii); console.log(jj);
                        console.log(a); console.log(edgeList0[1].dir[0]); console.log(edgeList0[1].dir[1]); console.log(edgeList1[2].dir[0]); console.log(edgeList1[2].dir[1]);
                        console.log(edgeList0[1].point[0][0]);
                        console.log(edgeList0[1].point[0][1]);
                        console.log(edgeList0[1].point[1][0]);
                        console.log(edgeList0[1].point[1][1]);
                        console.log(edgeList1[2].point[0][0]);
                        console.log(edgeList1[2].point[0][1]);
                        console.log(edgeList1[2].point[1][0]);
                        console.log(edgeList1[2].point[1][1]);*/
                    }
                }
            }
        }
    }
}

//实践方法
function act(scheme, realMove, dsMove){
    if(dsMove){
        //firstly move the elastic boxes;
        for(let i = 0; i < scheme.history.length; ++i){
            //console.log(arrayOfRooms[scheme.history[i].roomId].eBoxList.length);
            while(arrayOfRooms[scheme.history[i].roomId].eBoxList.length <= scheme.history[i].eBoxId){
                let e0 = {edgeId:0, eBoxId:arrayOfRooms[scheme.history[i].roomId].eBoxList.length,roomId:scheme.history[i].roomId, point:[[0,0],[0,0]], dir:[1,0], neighbourEdge:[], onWall:false};
                let e1 = {edgeId:1, eBoxId:arrayOfRooms[scheme.history[i].roomId].eBoxList.length,roomId:scheme.history[i].roomId, point:[[0,0],[0,0]], dir:[1,0], neighbourEdge:[], onWall:false};
                let e2 = {edgeId:2, eBoxId:arrayOfRooms[scheme.history[i].roomId].eBoxList.length,roomId:scheme.history[i].roomId, point:[[0,0],[0,0]], dir:[1,0], neighbourEdge:[], onWall:false};
                let e3 = {edgeId:3, eBoxId:arrayOfRooms[scheme.history[i].roomId].eBoxList.length,roomId:scheme.history[i].roomId, point:[[0,0],[0,0]], dir:[1,0], neighbourEdge:[], onWall:false};
                let egEBox = {eBoxId:arrayOfRooms[scheme.history[i].roomId].eBoxList.length, roomId:scheme.history[i].roomId, objList:[], edgeList:[e0,e1,e2,e3], currentCover:[[0.0,0.0],[0.0,0.0]], currentRange:[0.0,0.0], dirRange:[[0,0],[0,0]]};
                arrayOfRooms[scheme.history[i].roomId].eBoxList = arrayOfRooms[scheme.history[i].roomId].eBoxList.concat([egEBox]);
            
                //console.log(arrayOfRooms[scheme.history[i].roomId].eBoxList.length);
            }
            arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].objList = scheme.history[i].objList;
            arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].dirRange = scheme.history[i].dirRange;
            let ie = scheme.history[i].edgeList;
            /*{
                console.log(scheme.history[i].edgeList[1].point[0][0]);
                console.log(scheme.history[i].edgeList[1].point[0][1]);
                console.log(scheme.history[i].edgeList[1].point[1][0]);
                console.log(scheme.history[i].edgeList[1].point[1][1]);
                console.log(scheme.history[i].edgeList[3].point[0][0]);
                console.log(scheme.history[i].edgeList[3].point[0][1]);
                console.log(scheme.history[i].edgeList[3].point[1][0]);
                console.log(scheme.history[i].edgeList[3].point[1][1]);
            }
            {
                console.log(arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].edgeList[1].point[0][0]);
                console.log(arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].edgeList[1].point[0][1]);
                console.log(arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].edgeList[1].point[1][0]);
                console.log(arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].edgeList[1].point[1][1]);
                console.log(arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].edgeList[3].point[0][0]);
                console.log(arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].edgeList[3].point[0][1]);
                console.log(arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].edgeList[3].point[1][0]);
                console.log(arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].edgeList[3].point[1][1]);
            }*/
            //console.log(arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId]);
            for(let ii=0;ii<4;++ii){
                arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].edgeList[ii].point[0][0] = ie[ii].point[0][0];
                arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].edgeList[ii].point[0][1] = ie[ii].point[0][1];
                arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].edgeList[ii].point[1][0] = ie[ii].point[1][0];
                arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].edgeList[ii].point[1][1] = ie[ii].point[1][1];
                arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].edgeList[ii].dir[0] = ie[ii].dir[0];
                arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].edgeList[ii].dir[1] = ie[ii].dir[1];
            }
            arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].currentCover = [[0,0],[0,0]];
            arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].currentCover[0][0] = Math.min(ie[0].point[0][0],ie[1].point[0][0],ie[2].point[0][0],ie[3].point[0][0]);
            arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].currentCover[0][1] = Math.max(ie[0].point[0][0],ie[1].point[0][0],ie[2].point[0][0],ie[3].point[0][0]);
            arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].currentCover[1][0] = Math.min(ie[0].point[0][1],ie[1].point[0][1],ie[2].point[0][1],ie[3].point[0][1]);
            arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].currentCover[1][1] = Math.max(ie[0].point[0][1],ie[1].point[0][1],ie[2].point[0][1],ie[3].point[1][1])
            /*[
                [,Math.max(ie[0].point[0][0],ie[1].point[0][0],ie[2].point[0][0],ie[3].point[0][0])],
                [Math.min(ie[0].point[0][1],ie[1].point[0][1],ie[2].point[0][1],ie[3].point[0][1]),Math.max(ie[0].point[0][1],ie[1].point[0][1],ie[2].point[0][1],ie[3].point[0][1])]
            ];*/
            arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].currentRange = [0,0];
            arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].currentRange[0] = arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].currentCover[0][1] - arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].currentCover[0][0];
            arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].currentRange[1] = arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].currentCover[1][1] - arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].currentCover[1][0];
            /*{
                console.log(arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].edgeList[1].point[0][0]);
                console.log(arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].edgeList[1].point[0][1]);
                console.log(arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].edgeList[1].point[1][0]);
                console.log(arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].edgeList[1].point[1][1]);
                console.log(arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].edgeList[3].point[0][0]);
                console.log(arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].edgeList[3].point[0][1]);
                console.log(arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].edgeList[3].point[1][0]);
                console.log(arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].edgeList[3].point[1][1]);
            }*/
            if(realMove){
                for(let j = 0; j < arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].objList.length; ++j){
                    let obj = arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].objList[j];

                    if(obj.type == "toMain"){
                        let obj0 = arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].objList[0];
                        obj.position[0] = Math.cos(obj0.orient) * obj.tr[0] + Math.sin(obj0.orient) * obj.tr[2] + obj0.position[0];
                        obj.position[1] = obj.tr[1] + obj0.position[1];
                        obj.position[2] = Math.cos(obj0.orient) * obj.tr[2] - Math.sin(obj0.orient) * obj.tr[0] + obj0.position[2];
                        try{
                            transformObject3DOnly(obj.key, obj.position, 'position');
                        }catch(error){}
                    }
                    else{
                        let wall = arrayOfRooms[scheme.history[i].roomId].eBoxList[scheme.history[i].eBoxId].edgeList[obj.wallid];
                        /*{
                            console.log(obj.wallid);
                            console.log(wall.point[0][0]);
                            console.log(wall.point[0][1]);
                            console.log(wall.point[1][0]);
                            console.log(wall.point[1][1]);
                        }*/
                        obj.position[0] = wall.point[0][0]*obj.ver+wall.point[1][0]*(1-obj.ver)+wall.dir[0]*obj.dis;
                        obj.position[1] = obj.height;
                        obj.position[2] = wall.point[0][1]*obj.ver+wall.point[1][1]*(1-obj.ver)+wall.dir[1]*obj.dis;
                        try{
                            transformObject3DOnly(obj.key, obj.position, 'position');
                        }catch(error){}
                    }
                }
            }
        }

        
        if("deleteList" in scheme && scheme.deleteList.length > 0 && "roomId" in scheme){
            let j = scheme.deleteList.length-1;let cnt = 0;
            for(let i = arrayOfRooms[scheme.roomId].eBoxList.length-1; i>=0; --i){
                if(arrayOfRooms[scheme.roomId].eBoxList[i].eBoxId == scheme.deleteList[j]){
                    arrayOfRooms[scheme.roomId].eBoxList.splice(i,1);
                    j -= 1; cnt += 1;
                }else{
                    arrayOfRooms[scheme.roomId].eBoxList[i].eBoxId -= cnt;
                }
            }
        }
    }
}

/**
 * 都有哪些接口？
 *      初始化
 *          啊啊啊搞什么呀？
 *          啊啊啊，
 * 
 *      加断点的行为
 *          sk.js: seperate_lines()
 *          movelinemodel.js: cut_inner_line()
 *          yl.js: cutting_inner_line()
 * 
 *      移动边的行为
 *          sk.js: follow_mouse_pro()
 *          movelinemodel.js: move_point()
 *          yl.js:func() 我就是感觉自己需要的信息并非是move_point的输出，而是follow_mouse_pro的某些中间信息
 * 
 *      改变房间的行为
 *          movelinemodel.js: decide()
 *          yl.js: newRoomOut()
 *      
 */