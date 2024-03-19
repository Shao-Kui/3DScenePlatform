const area_distribution = {
    "livingroom":[31.34055880017362,37.98303794068651],
    "kitchen":[5.424599317113867,3.1243986198765556],
    "bathroom":[3.773808768026618,1.6098949048550089],
    "balcony":[4.0439683698808535,4.463824697714653],
    "bedroom":[11.331962509888777,10.288293423901251],
    "diningroom":[8.502216889056243,13.928773352224832],
    "storage":[2.4083905823027605,3.6633656211885017],
    // "entrance":[4.2053069540373595,10.083163192657635]
};

function normal_distribution_pdf(x, mean, variance)
{
    const denominator = Math.sqrt(2 * Math.PI * variance);
    const exponent = - (x - mean) * (x - mean) / (2 * variance);
    return (1 / denominator) * Math.exp(exponent);
}

function on_same_line(point1,point2,point3)
{
    const eps = 1e-7;
    const vec1 = [point2[0]-point1[0],point2[1]-point1[1]];
    const vec2 = [point3[0]-point2[0],point3[1]-point2[1]];
    return (Math.abs(vec1[0]) < eps && Math.abs(vec2[0]) < eps) || (Math.abs(vec1[1]) < eps && Math.abs(vec2[1]) < eps);
}

function point_between(point1,point2,point3)
{
    const eps = 1e-7;
    const vec1 = [point2[0]-point1[0],point2[1]-point1[1]];
    const vec2 = [point3[0]-point2[0],point3[1]-point2[1]];
    return vec1[0] * vec2[0] + vec1[1] * vec2[1] >= -eps;
}

function same_point(point1,point2)
{
    const eps = 1e-7;
    return Math.abs(point1[0]-point2[0]) < eps && Math.abs(point1[1]-point2[1]) < eps;
}

function calculate_room_division_evaluation(points, type){
    // const tri = D3.delaunay(points);

    const C_1 = 0, C_2 = 0, C_3 = 0.5, C_4 = 5, C_5 = 30;

    // const count_of_skeleton_edges = tri.triangles.length - points.length + tri.hull.length;

    // let max_degree_of_skeleton = 3;

    // const len_of_simplices = tri.triangles.length;

    const len_of_points = points.length;

    // for(let i = 0; i < len_of_simplices; i++)
    // {
        //TODO: check the max degree of skeleton
        // if Math.abs()
    // }
    var real_boundary_points = points.length;

    for(let i = 1; i < points.length - 1; i++)
    {
        if(on_same_line(points[i-1],points[i],points[i+1]))real_boundary_points--;
    }
    if(on_same_line(points[points.length-2],points[points.length-1],points[0]))real_boundary_points--;
    if(on_same_line(points[points.length-1],points[0],points[1]))real_boundary_points--;

    const area = Math.abs(d3.polygonArea(points));

    let outer_boundary = [[points[0][0],points[0][0]],[points[0][1],points[0][1]]];

    for(let i = 1; i < len_of_points; i++)
    {
        for(let j = 0; j < 2; j++)
        {
            outer_boundary[j][0] = Math.min(points[i][j],outer_boundary[j][0]);
            outer_boundary[j][1] = Math.max(points[i][j],outer_boundary[j][1]);
        }
    }

    const outer_area = (outer_boundary[0][1] - outer_boundary[0][0]) * (outer_boundary[1][1] - outer_boundary[1][0]);

    return - C_3 * Math.exp(real_boundary_points) + C_4 * Math.log(area / outer_area / 0.75) + C_5 * Math.exp(normal_distribution_pdf(area,area_distribution[type][0],area_distribution[type][1]))
}

function cut_half_of_room(points,startpoint,endpoint)
{
    const eps = 1e-7;
    var result = [];
    for(let i = points.length - 1; i >= 0; i--)
    {
        if(Math.abs(startpoint[0] - points[i][0]) < eps && Math.abs(startpoint[1] - points[i][1]) < eps)
        {
            while(Math.abs(endpoint[0] - points[i][0]) >= eps || Math.abs(endpoint[1] - points[i][1]) >= eps)
            {
                result.push(points[i]);
                i++;
                if(i == points.length)i = 0;
            }
            return result;
        }
    }
    return result;
}

function room_merged_with_father(room)
{
    const father_room = arrayOfRooms[room.father];
    var new_room = {
        "points":cut_half_of_room(father_room.points,room.father_wall_start,room.father_wall_end),
        "type":father_room.type,
        "id":father_room.id,
        "father":father_room.father,
        "father_wall_start":father_room.father_wall_start,
        "father_wall_end":father_room.father_wall_end
    };
    new_room.points.concat(cut_half_of_room(room.points,room.father_wall_end,room.father_wall_start));
    return new_room;
}

function move_point(point_id,new_coordinate)
{
    var pt1 = arrayOfRoomPoints[point_id];
    pt1.position = new_coordinate;
    var new_linkedInnerLines = [];
    for(line_id in pt1.linkedInnerLines)
    {
        const line = pt1.linkedInnerLines[line_id];
        const other_point_id = line[1],room_id = line[2];
        const pt2 = arrayOfRoomPoints[other_point_id];
        const new_line_obj = createCylinderMesh(pt1.position[0],0,pt1.position[1],pt2.position[0],0,pt2.position[1],0xff0000,0.05);
        if(Math.abs(pt1.position[0] - pt2.position[0]) < 1e-7)new_line_obj.rotation.x = 1.57;
        else new_line_obj.rotation.z = 1.57;
        new_line_obj.startid = (line[0].startid==point_id)?point_id:other_point_id;
        new_line_obj.endid = (line[0].startid==point_id)?other_point_id:point_id;
        new_linkedInnerLines.push([new_line_obj,other_point_id,room_id]);
        for(var i = 0; i < pt2.linkedInnerLines.length; i++)
            if(pt2.linkedInnerLines[i][1] == point_id)pt2.linkedInnerLines[i][0] = new_line_obj;
        for(var i = 0; i < arrayOfInnerLines[room_id].length; i++)
        {
            if(arrayOfInnerLines[room_id][i].uuid == line[0].uuid)arrayOfInnerLines[room_id][i] = new_line_obj;
        }
        scene.add(new_line_obj);
        scene.remove(line[0]);
    }
    pt1.linkedInnerLines = new_linkedInnerLines;
}

function new_room_point(position)
{
    arrayOfRoomPoints[roomPointIndexCounter] = {
        "position":position,
        "id":roomPointIndexCounter,
        "linkedInnerLines":[]
    };
    roomPointIndexCounter++;
    return roomPointIndexCounter - 1;
}

function add_inner_line_between_points(pt1,pt2,roomid)
{
    const cylinder = createCylinderMesh(pt1.position[0],0,pt1.position[1],pt2.position[0],0,pt2.position[1],0xff0000,0.05);
    if(Math.abs(pt1.position[0] - pt2.position[0]) < 1e-7)cylinder.rotation.x = 1.57;
    else cylinder.rotation.z = 1.57;
    cylinder.startid = pt1.id;
    cylinder.endid = pt2.id;
    scene.add(cylinder);
    pt1.linkedInnerLines.push([cylinder,pt2.id,roomid]);
    pt2.linkedInnerLines.push([cylinder,pt1.id,roomid]);
    return cylinder;
}

function remove_room_point(ptid, roomid)
{
    for(let t=0; t<arrayOfRooms[roomid].points.length; ++t){
        if(arrayOfRooms[roomid].points[t]==ptid){ arrayOfRooms[roomid].points.splice(t,1); break;}
    }
    delete arrayOfRoomPoints[ptid];
}

function remove_inner_line(roomid,pt1id,pt2id)
{
    for(let t=0; t<arrayOfInnerLines[roomid].length; ++t){
        if(arrayOfInnerLines[roomid][t].startid==pt1id && arrayOfInnerLines[roomid][t].endid==pt2id){
            scene.remove(arrayOfInnerLines[roomid][t]);
            arrayOfInnerLines[roomid].splice(t,1);break;
        }
    }
    
    let pt1 = arrayOfRoomPoints[pt1id], pt2 = arrayOfRoomPoints[pt2id];
    for(let t=0; t<pt1.linkedInnerLines.length; ++t){
        if(pt1.linkedInnerLines[t][1]==pt2id && pt1.linkedInnerLines[t][2]==roomid){
            pt1.linkedInnerLines.splice(t,1);break;
        }
    }
    for(let t=0; t<pt2.linkedInnerLines.length; ++t){
        if(pt2.linkedInnerLines[t][1]==pt1id && pt2.linkedInnerLines[t][2]==roomid){
            pt2.linkedInnerLines.splice(t,1);break;
        }
    }

}

function cut_inner_line(room_id,line_id,position)
{
    const newpt1 = arrayOfRoomPoints[new_room_point(position)], newpt2 = arrayOfRoomPoints[new_room_point(position)];
    const pt1 = arrayOfRoomPoints[arrayOfRooms[room_id].points[line_id]],pt2 = arrayOfRoomPoints[arrayOfRooms[room_id].points[line_id == arrayOfRooms[room_id].points.length - 1 ? 0 : line_id + 1]];
    const line = arrayOfInnerLines[room_id][line_id];
    for(let i = 0; i < pt1.linkedInnerLines.length; i++)
    {
        if(pt1.linkedInnerLines[i][1] == pt2.id)
        {
            pt1.linkedInnerLines.splice(i,1);
            break;
        }
    }
    for(let i = 0; i < pt2.linkedInnerLines.length; i++)
    {
        if(pt2.linkedInnerLines[i][1] == pt1.id)
        {
            pt2.linkedInnerLines.splice(i,1);
            break;
        }
    }
    // console.log('removing line');
    // console.log(line);
    scene.remove(line);
    arrayOfInnerLines[room_id].splice(line_id,1,add_inner_line_between_points(pt1,newpt1,room_id),add_inner_line_between_points(newpt1,newpt2,room_id),add_inner_line_between_points(newpt2,pt2,room_id));
    arrayOfRooms[room_id].points.splice(line_id + 1,0,newpt1.id,newpt2.id);
}

function decide(room,line_id)
{
    const eps = 1e-7;
    const step = 0.5 , min_delta = 2;
    var result = {
        'rooms':[],
        'division_lines':[],
        'division_points':[]};
    const room_shape = room.points.map(id => arrayOfRoomPoints[id].position);
    var result_val = calculate_room_division_evaluation(room_shape,room.type);
    // console.log("Value of no division:");
    // console.log(result_val);
    const idx_of_points = [line_id - 1, line_id, line_id + 1,line_id + 2].map(val => {
        if(val < 0) val += room_shape.length;
        if(val >= room_shape.length) val -= room_shape.length;
        return val;
    });//ID of the four points considered
    var line_dim,line_dir;
    if(Math.abs(room_shape[idx_of_points[2]][1] - room_shape[idx_of_points[1]][1]) < eps)line_dim = 1;
    else line_dim = 0;
    if(room_shape[idx_of_points[0]][line_dim] > room_shape[idx_of_points[1]][line_dim] && 
        room_shape[idx_of_points[3]][line_dim] > room_shape[idx_of_points[2]][line_dim])line_dir = 1;
    else if(room_shape[idx_of_points[0]][line_dim] < room_shape[idx_of_points[1]][line_dim] && 
        room_shape[idx_of_points[3]][line_dim] < room_shape[idx_of_points[2]][line_dim])line_dir = -1;
    else line_dir = 0;
    if(line_dir != 0)//split
    {
        const max_move_step = Math.min(Math.abs(room_shape[idx_of_points[0]][line_dim]-room_shape[idx_of_points[1]][line_dim]),
        Math.abs(room_shape[idx_of_points[2]][line_dim]-room_shape[idx_of_points[3]][line_dim]));
        var original_cut_1 = structuredClone(room_shape[idx_of_points[1]]),
        original_cut_2 = structuredClone(room_shape[idx_of_points[2]]);
        for(let delta = min_delta; delta < max_move_step; delta += step)
        {
            room_shape[idx_of_points[1]] = structuredClone(original_cut_1);
            room_shape[idx_of_points[2]] = structuredClone(original_cut_2);
            room_shape[idx_of_points[1]][line_dim] += line_dir * delta;
            room_shape[idx_of_points[2]][line_dim] += line_dir * delta;
            const room1_val = calculate_room_division_evaluation(room_shape,room.type);//let newRoomRes=newRoomOut(room, roomShape);
            for(const roomtype in area_distribution)
            {
                var room2 = {
                    "points":[structuredClone(room_shape[idx_of_points[1]]),
                        // structuredClone(room_shape[idx_of_points[1]]),
                        // structuredClone(room_shape[idx_of_points[1]]),
                        structuredClone(original_cut_1),structuredClone(original_cut_2),
                        structuredClone(room_shape[idx_of_points[2]]),
                        // structuredClone(room_shape[idx_of_points[2]]),
                        // structuredClone(room_shape[idx_of_points[2]]),
                    ],
                    "id":-1,
                    "father":room.id,
                    "type":roomtype,
                    "father_wall_start": -1,
                    "father_wall_end": -1
                };
                const cur_val = Math.min(room1_val,calculate_room_division_evaluation(room2.points,room2.type));
                // console.log("Value of split:");
                // console.log(cur_val);
                if(cur_val > result_val)
                {
                    result = {
                        'rooms':[{},room2],//temporarily save the information
                        'division_lines':[],
                        'division_points':[
                            structuredClone(room_shape[idx_of_points[1]]),
                            structuredClone(room_shape[idx_of_points[2]])
                        ],
                        'inserted_points':[]
                    };
                    result_val = cur_val;
                }
            }
        }
    }
    // if(room.father != -1)//merge
    // {
    //     const merged_room = room_merged_with_father(room);
    //     const father_val = calculate_room_division_evaluation(arrayOfRooms[room.father].points,arrayOfRooms[room.father].type);
    //     const merged_val = calculate_room_division_evaluation(merged_room.points,merged_room.type);
    //     // console.log("Value of merge:");
    //     // console.log(merged_val);
    //     if(Math.max(Math.min(origin_val,father_val),result_val) < merged_val)
    //     {
    //         result_val = merged_val;
    //         result = {
    //             'rooms':[merged_room],
    //             'division_lines':[],
    //             'division_points':[],
    //         };
    //     }
    // }
    if(result.rooms.length == 1)//Merge with father
    {
        console.log(selected_room_id);
        arrayOfInnerLines[selected_room_id].forEach(l => {scene.remove(l)});
        delete arrayOfInnerLines.selected_room_id;
        let father_id = arrayOfRooms[selected_room_id].father;
        arrayOfRooms[father_id] = result[0];
        delete arrayOfRooms.selected_room_id;
    }
    else if(result.rooms.length == 2)//divide
    {
        move_point(room.points[idx_of_points[1]],result.division_points[0]);
        move_point(room.points[idx_of_points[2]],result.division_points[1]);
        // cut_inner_line(room.id,idx_of_points[1],result.division_points[1]);
        // cut_inner_line(room.id,idx_of_points[1],result.division_points[0]);
        result.rooms[1].points = result.rooms[1].points.map(pos => new_room_point(pos));
        // result.division_lines = [
        //     [room.points[idx_of_points[1]],room.points[idx_of_points[2]]],
        //     [roomPointIndexCounter - 4,roomPointIndexCounter - 1]
        // ];
        arrayOfInnerLines[roomIndexCounter] = [];
        for(let i = 0; i < result.rooms[1].points.length; i++)
        {
            let j = (i == result.rooms[1].points.length - 1) ? 0 : i + 1;
            arrayOfInnerLines[roomIndexCounter].push(add_inner_line_between_points(arrayOfRoomPoints[result.rooms[1].points[i]],arrayOfRoomPoints[result.rooms[1].points[j]],roomIndexCounter));
        }
        for(let i = 0; i < 2; i++)// && false
        {
            const current_cutpoint = result.division_points[i];
            for(let j = 0; j < arrayOfLines.length; j++)
            {
                const current_line = arrayOfLines[j];
                if(on_same_line([current_line.start1[0],current_line.start1[2]],current_cutpoint,[current_line.end1[0],current_line.end1[2]])
                 && point_between([current_line.start1[0],current_line.start1[2]],current_cutpoint,[current_line.end1[0],current_line.end1[2]]))
                {
                    seperate_lines(arrayOfLines[j],current_line.start1,current_line.end1,current_cutpoint[0],0,current_cutpoint[1],false);
                    break;
                }
            }
        }
        room = result.rooms[0];
        arrayOfRooms[roomIndexCounter] = result.rooms[1];
        arrayOfRooms[roomIndexCounter].id = roomIndexCounter;
        roomIndexCounter++;
    }
}