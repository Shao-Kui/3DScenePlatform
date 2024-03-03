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
    return Math.abs(vec1[0] * vec2[1] - vec1[1] * vec2[0]) < eps;
}

function point_between(point1,point2,point3)
{
    const eps = 1e-7;
    const vec1 = [point2[0]-point1[0],point2[1]-point1[1]];
    const vec2 = [point3[0]-point2[0],point3[1]-point2[1]];
    return vec1[0] * vec2[0] + vec1[1] * vec2[1] >= 0;
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

function decide(room,line_id)
{
    const eps = 1e-7;
    const step = 0.5 , min_delta = 2;
    var result = {
        'rooms':[],
        'division_lines':[],
        'division_points':[]};
    var result_val = calculate_room_division_evaluation(room.points,room.type);
    // console.log("Value of no division:");
    // console.log(result_val);
    const origin_val = result_val;
    const idx_of_points = [line_id - 1, line_id, line_id + 1,line_id + 2].map(val => {
        if(val < 0) val += room.points.length;
        if(val >= room.points.length) val -= room.points.length;
        return val;
    });//ID of the four points considered
    var line_dim,line_dir;
    if(Math.abs(room.points[idx_of_points[2]][1] - room.points[idx_of_points[1]][1]) < eps)line_dim = 1;
    else line_dim = 0;
    if(room.points[idx_of_points[0]][line_dim] > room.points[idx_of_points[1]][line_dim] && 
        room.points[idx_of_points[3]][line_dim] > room.points[idx_of_points[2]][line_dim])line_dir = 1;
    else if(room.points[idx_of_points[0]][line_dim] < room.points[idx_of_points[1]][line_dim] && 
        room.points[idx_of_points[3]][line_dim] < room.points[idx_of_points[2]][line_dim])line_dir = -1;
    else line_dir = 0;
    if(line_dir != 0)//split
    {
        const max_move_step = Math.min(Math.abs(room.points[idx_of_points[0]][line_dim]-room.points[idx_of_points[1]][line_dim]),
        Math.abs(room.points[idx_of_points[2]][line_dim]-room.points[idx_of_points[3]][line_dim]));
        for(let delta = min_delta; delta < max_move_step; delta += step)
        {
            var cut_point_1 = structuredClone(room.points[idx_of_points[1]]), cut_point_2 = structuredClone(room.points[idx_of_points[2]]);
            cut_point_1[line_dim] += delta * line_dir;
            cut_point_2[line_dim] += delta * line_dir;
            var room1 = structuredClone(room);
            if(room1.father_wall_start == room1.points[idx_of_points[1]])
                room1.father_wall_start = structuredClone(cut_point_1);
            else if(room1.father_wall_start == room1.points[idx_of_points[2]])
                room1.father_wall_start = structuredClone(cut_point_2);
            if(room1.father_wall_end == room1.points[idx_of_points[1]])
                room1.father_wall_end = structuredClone(cut_point_1);
            else if(room1.father_wall_end == room1.points[idx_of_points[2]])
                room1.father_wall_end = structuredClone(cut_point_2);
            room1.points[idx_of_points[1]] = structuredClone(cut_point_1);
            room1.points[idx_of_points[2]] = structuredClone(cut_point_2);
            room1.points.splice(idx_of_points[1],0,cut_point_1);
            room1.points.splice(idx_of_points[3],0,cut_point_2);
            
            // console.log(d3.polygonArea(room1.points));
            // console.log(d3.polygonArea(room2.points));
            for(const roomtype in area_distribution)
            {
                var room2 = {
                    "points":[structuredClone(cut_point_1),structuredClone(cut_point_1),
                        structuredClone(room.points[idx_of_points[1]]),structuredClone(room.points[idx_of_points[2]])
                    ,structuredClone(cut_point_2),structuredClone(cut_point_2)],
                    "id":-1,
                    "father":room.id,
                    "type":roomtype,
                    "father_wall_start":structuredClone(cut_point_2),
                    "father_wall_end":structuredClone(cut_point_1)
                };
                const cur_val = Math.min(calculate_room_division_evaluation(room1.points,room1.type),calculate_room_division_evaluation(room2.points,room2.type));
                // console.log("Value of split:");
                // console.log(cur_val);
                if(cur_val > result_val)
                {
                    result = {
                        'rooms':[room1,room2],
                        'division_lines':[
                            [structuredClone(cut_point_1),structuredClone(cut_point_2)]
                        ],
                        'division_points':[
                            cut_point_1,cut_point_2
                        ],
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
    return result;
}