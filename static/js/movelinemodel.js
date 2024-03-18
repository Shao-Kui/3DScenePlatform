const area_distribution = {
    "livingroom":[31.34055880017362,37.98303794068651],
    "diningroom":[8.502216889056243,13.928773352224832],
    "kitchen":[5.424599317113867,3.1243986198765556],
    "bathroom":[3.773808768026618,1.6098949048550089],
    "balcony":[4.0439683698808535,4.463824697714653],
    "storage":[2.4083905823027605,3.6633656211885017],
    "bedroom":[11.331962509888777,10.288293423901251],
    // "entrance":[4.2053069540373595,10.083163192657635]
};

const room_type_distribution = [
[[1, 0, 1, 1, 1, 0, 0, 2],0.2377457048076447],
[[1, 0, 1, 1, 1, 0, 0, 3],0.17128781502203297],
[[1, 0, 1, 1, 0, 0, 0, 3],0.04602168638906768],
[[1, 0, 1, 1, 2, 0, 0, 3],0.06941624993810962],
[[1, 0, 1, 2, 1, 0, 0, 2],0.015237411496756944],
[[1, 0, 1, 1, 0, 0, 0, 2],0.05738476011288805],
[[1, 0, 1, 1, 1, 0, 1, 2],0.012514234787344656],
[[1, 0, 1, 1, 2, 0, 0, 2],0.11535128979551419],
[[1, 0, 1, 2, 0, 0, 0, 3],0.024818042283507452],
[[1, 0, 1, 2, 1, 0, 0, 3],0.12155270584740308],
[[1, 0, 1, 2, 2, 0, 0, 2],0.010434718027429816],
];

const room_type_to_id_map = {
    "livingroom":0,
    "diningroom":1,
    "kitchen":2,
    "bathroom":3,
    "balcony":4,
    "entrance":5,
    "storage":6,
    "bedroom":7
};

const min_side_length = {
    "livingroom":3,
    "diningroom":2,
    "kitchen":2,
    "bathroom":2,
    "balcony":1,
    "storage":1,
    "bedroom":3
};

const room_link_distribution = {
'livingroom_bedroom': 196766, 
 'livingroom_kitchen': 75089, 
 'livingroom_bathroom': 79119, 
 'livingroom_balcony': 47740, 
 'bedroom_balcony': 24408, 
 'bedroom_bathroom': 14668, 
 'kitchen_balcony': 12502, 
 'kitchen_diningroom': 895, 
 'livingroom_diningroom': 1225, 
 'kitchen_bathroom': 1720, 
 'storage_livingroom': 2277, 
 'bedroom_bedroom': 858, 
 'kitchen_bedroom': 308, 
 'storage_kitchen': 403, 
 'storage_bedroom': 410, 
 'diningroom_bedroom': 306, 
 'diningroom_bathroom': 186, 
 'balcony_balcony': 64, 
 'bathroom_bathroom': 476, 
 'diningroom_balcony': 63, 
 'kitchen_kitchen': 61, 
 'storage_balcony': 69, 
 'bathroom_balcony': 293, 
 'storage_bathroom': 57, 
}

function get_room_type_evaluation(current_room_type)
{
    const room_type_count = 8;
    let res = 0.0;
    for(let i = 0; i < room_type_distribution.length; i++)
    {
        let tmp_res = 0.0;
        for(let j = 0; j < room_type_count; j++)
            tmp_res += Math.pow(3,Math.abs(current_room_type[j] - room_type_distribution[i][0][j]));
        res += tmp_res * room_type_distribution[i][1];
    }
    return - res;    
}

function get_link_evaluation(room_type_1,room_type_2)
{
    return room_type_1 + '_' + room_type_2 in room_link_distribution || room_type_2 + '_' + room_type_1 in room_link_distribution; 
}

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

const C_type = 0.01;

function calculate_room_division_evaluation(points, type){
    // const tri = D3.delaunay(points);

    const C_1 = 0, C_2 = 0, C_3 = 5, C_4 = 5, C_5 = 10;

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

    if((outer_boundary[0][1] - outer_boundary[0][0]) < min_side_length[type] || (outer_boundary[1][1] - outer_boundary[1][0]) < min_side_length[type])return -1e9;
    if(area < area_distribution[type][0] / 2)return -1e9;

    const outer_area = (outer_boundary[0][1] - outer_boundary[0][0]) * (outer_boundary[1][1] - outer_boundary[1][0]);

    // console.log("Evaluation Info");
    // console.log(type);
    // console.log(area);
    // console.log(outer_area);
    // console.log(C_4 * Math.log(area / outer_area / 0.75));
    // console.log(- C_3 * real_boundary_points);
    // console.log(C_5 * Math.exp(10 * normal_distribution_pdf(area,area_distribution[type][0],area_distribution[type][1])));
    // console.log(- C_3 * real_boundary_points + C_4 * Math.log(area / outer_area / 0.75) + C_5 * Math.exp(10 * normal_distribution_pdf(area,area_distribution[type][0],area_distribution[type][1])));

    return - C_3 * Math.exp(real_boundary_points) + C_4 * Math.log(area / outer_area / 0.75) + C_5 * Math.exp(10 * (Math.exp(10 * normal_distribution_pdf(area,area_distribution[type][0],area_distribution[type][1])) - 1));
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
        new_line_obj.startid = point_id;
        new_line_obj.endid = other_point_id;
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

const room_type_counter = [0,0,0,0,0,0,0,0];

function decide(room,line_id)
{
    const eps = 1e-7;
    const step = 0.5 , min_delta = 2;
    var result = {
        'rooms':[],
        'division_lines':[],
        'division_points':[]};
    const room_shape = room.points.map(id => arrayOfRoomPoints[id].position);
    var result_val = calculate_room_division_evaluation(room_shape,room.type) + C_type * get_room_type_evaluation(room_type_counter);
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
            const room1_val = calculate_room_division_evaluation(room_shape,room.type);
            for(const roomtype in area_distribution)
            {
                if(!get_link_evaluation(room.type, roomtype))continue;
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
                room_type_counter[room_type_to_id_map[roomtype]] += 1;
                const cur_val = Math.min(room1_val,calculate_room_division_evaluation(room2.points,room2.type))
                + C_type * get_room_type_evaluation(room_type_counter);
                room_type_counter[room_type_to_id_map[roomtype]] -= 1;
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
        console.log("已退出可拖动状态");
        now_x1 = 0 ;
        now_x2 = 0;
        now_y1 = 0;
        now_y2 = 0;
        now_z1 = 0;
        now_z2 = 0;
        now_move_index = -1;//全部重置
        On_LINEMOVE = false;
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
        for(let i = 0; i < 2; i++)
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
        room_type_counter[room_type_to_id_map[result.rooms[1].type]] += 1;
        room = result.rooms[0];
        arrayOfRooms[roomIndexCounter] = result.rooms[1];
        arrayOfRooms[roomIndexCounter].id = roomIndexCounter;
        roomIndexCounter++;
        console.log("已退出可拖动状态");
        now_x1 = 0 ;
        now_x2 = 0;
        now_y1 = 0;
        now_y2 = 0;
        now_z1 = 0;
        now_z2 = 0;
        can_add_dot = 0;
        now_move_index = -1;//全部重置
        has_moved = 0;
        On_LINEMOVE = false;
    }
}