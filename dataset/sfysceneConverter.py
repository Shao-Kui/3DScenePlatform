import os
import json
import cv2
import numpy as np
import math
import tqdm
from shapely.geometry import Point, Polygon
import warnings
# from SFYObjConverter import convertJsonlToSFYObjList
# from childrenList_conversion import load_data

H = 2.8
BASE_DIR = '.\\2023-09\\'
TARGET_DIR = ".\\target\\"

def checkClockwise(points):
    res = 0
    for i in range(len(points)):
        a = np.array(points[i])
        b = np.array(points[(i+1)%len(points)])
        c = np.array(points[(i+2)%len(points)])
        res += 0.5 * ((b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1]))
    if res > 0:
        return True
    else:
        return False


def transformScene(sfy_scene,origin,objlist):
    scene_json = {}
    scene_json['origin'] = origin
    scene_json['id'] = 0
    scene_json['up'] = [0,1,0]
    scene_json['front'] = [0,0,1]
    scene_json['rooms'] = []
    points = []
    for point in sfy_scene['points'].keys():
        points.append(sfy_scene['points'][point]['value'])
    points = np.array([points]).T
    x_min = np.min(points[0])
    x_max = np.max(points[0])
    z_min = np.min(points[1])
    z_max = np.max(points[1])

    scene_json['bbox'] = {
        'min' : [
            x_min,-1e-6,z_min
        ],
        'max' : [
            x_max,H,z_max
        ]
    }

    scale = 1024
    img = np.zeros((scale,scale,3),np.int8)
    # img[:] = np.array(255, 255, 255)
    img[:] = np.array((255, 255, 255)).astype(img.dtype)
    centre = (scale//2, scale//2)
    bbox = np.array([
        np.array([x_min,z_min]),
        np.array([x_max,z_max])
    ])
    # print(bbox[0])
    old_centre = (bbox[0]+bbox[1])/2

    K = 30

    for i,sfy_room in enumerate(sfy_scene['spaces']):
        sfy_room = sfy_scene['spaces'][sfy_room]
        room = {}
        room['id'] = ''
        room['modelId'] = ''
        room['roomTypes'] = [sfy_room['name']]
        room['origin'] = origin
        room['roomId']= i
        room['objList'] = []

        room['roomShape'] = []

        lines = []
        lines_index = []

        point_bucket = {}
        for sfy_wall in sfy_room['linked_walls']:
            bg = sfy_scene['walls'][sfy_wall]['start_point']
            ed = sfy_scene['walls'][sfy_wall]['end_point']
            if [bg,ed] in lines_index or [ed, bg] in lines_index:
                continue
            if bg in point_bucket.keys():
                point_bucket[bg] += 1
            else:
                point_bucket[bg] =1

            if ed in point_bucket.keys():
                point_bucket[ed] += 1
            else:
                point_bucket[ed] =1
            
            lines_index.append([bg,ed])
            #lines.append([sfy_scene['points'][str(bg)]['value'][0:2],sfy_scene['points'][str(ed)]['value'][0:2]])
        # print(lines)
        # print(point_bucket)
        end_flag = False
        while not end_flag:
            # 遍历为奇数的点
            end_flag = True
            # print(point_bucket)
            for pt in point_bucket.keys():
                if point_bucket[pt] == 1:
                    end_flag = False
                    for line in lines_index.copy():
                        if pt in line:
                            lines_index.remove(line)
                            for item in line:
                                point_bucket[item] -= 1
                            break
                    break

        # print(point_bucket)             
        for line_id in lines_index:
            line_id = list(line_id)
            lines.append([sfy_scene['points'][str(line_id[0])]['value'][0:2],sfy_scene['points'][str(line_id[1])]['value'][0:2]])




        linedot = np.array(lines,dtype=float).T
        # print(linedot)
        x_max_room = np.max(linedot[0])
        x_min_room = np.min(linedot[0])
        z_max_room = np.max(linedot[1])
        z_min_room = np.min(linedot[1])

        room['bbox'] = {
            'min' : [
                x_min_room,-1e-6,z_min_room
            ],
            'max' : [
                x_max_room,H,z_max_room
            ]
        }

        # print(room['bbox']

        for line in lines:
            p1 = (np.array(line[0])-old_centre)*K+centre
            p2 = (np.array(line[1])-old_centre)*K+centre
            p1 = np.array(p1, np.int32)
            p2 = np.array(p2, np.int32)
            cv2.line(img,p1,p2,(255,255,255),6)
        
        # cv2.imshow('',img)
            
        
        


        while len(lines_index) > 2:
            # print(lines)
            poly:list = lines_index[0]
            lines_c = lines_index.copy()
            for line in lines_c[1:]:
                if line[0] == poly[0]:
                    lines_index[0].insert(0,line[-1])
                    lines_index.remove(line)
                    break
                elif line[0] == poly[-1]:
                    lines_index[0].append(line[-1])
                    lines_index.remove(line)
                    break
                elif line[-1] == poly[0]:
                    lines_index[0].insert(0,line[0])
                    lines_index.remove(line)
                    break
                elif line[-1] == poly[-1]:
                    lines_index[0].append(line[0])
                    lines_index.remove(line)
                    break
        points = lines_index[0]
        for point in points:
            room['roomShape'].append(sfy_scene['points'][str(point)]['value'][0:2])
        if not checkClockwise(room['roomShape']):
            room['roomShape'].reverse()

        for idx,wall_v in enumerate(room['roomShape']):
            # if idx == len(room['roomShape'])-1:
            #     break
            jdx = (idx+1)%len(room['roomShape'])
            wall_succ= np.array(room['roomShape'][jdx])
            wall_v = np.array(wall_v)
            delta = wall_succ-wall_v
            if abs(delta[0]) < 1e-4:
                room['roomShape'][jdx][0] = room['roomShape'][idx][0]
            if abs(delta[1]) < 1e-4:
                room['roomShape'][jdx][1] = room['roomShape'][idx][1]
        room_meta = []

        # 处理点
        for idx,wall_v in enumerate(room['roomShape']):
            # if idx == len(room['roomShape'])-1:
            #     break
            jdx = (idx+1)%len(room['roomShape'])
            wall_succ= np.array(room['roomShape'][jdx])
            wall_v = np.array(wall_v)
            room_meta.append((wall_succ-wall_v)/np.linalg.norm(wall_succ-wall_v))
        room_meta = np.array(room_meta)
        normals = room_meta[:,[1,0]]
        normals[:, 1] = -normals[:, 1]
        normals = -normals

        rshape = np.array(room['roomShape'])

        for idx, wall in enumerate(rshape):
            jdx = (idx+1)%len(rshape)
            kdx = (idx-1)%len(rshape)
            delta = normals[idx]+normals[kdx]
            
            for i in range(len(delta)):
                if delta[i]!=0:
                    delta[i] = 1 if delta[i] > 0 else -1
            rshape[idx] += 0.1*delta

        
        room['roomShape'] = rshape.tolist()
        room['roomNorm'] = normals.tolist()
        
        
        room['roomOrient'] = np.arctan2(normals[:, 0], normals[:, 1]).tolist()
        
        # if room['roomId'] == 0:
        #     room['objList'] = objlist
        for obj in objlist:
            corner1 = np.array(obj['bbox']['min'])
            corner2 = np.array(obj['bbox']['max'])

            center = (corner1+corner2)/2
            center2d= Point(center[0],center[2])

            a = Polygon(room['roomShape'])
            

            if a.contains(center2d):
                # print('here')
                room['objList'].append(obj)
        

        scene_json['rooms'].append(room)



    # cv2.imshow('',img)
    # cv2.waitKey(0)
    # cv2.imwrite(f'img/{origin}.jpg',img)
    return scene_json

def load_data(filename):
    """
    读取jsonl文件并生成objList
    """
    objTree = []
    
    roomId = 0
    # 读取roomId
    # with open(DATA_DIR + filename + ".json", "r", encoding="utf-8") as layoutFile:
    #     layoutData = json.load(layoutFile)
    #     roomId = next(iter(layoutData['spaces']))

    with open(BASE_DIR + filename + ".jsonl", "r", encoding="utf-8") as file:
        blocks = []
        current_block = []
        for line in file:
            data = json.loads(line)
            if data['father_idx'] == "":
                if len(current_block) > 0:
                    blocks.append(current_block)
                current_block = [data]
            else:
                current_block.append(data)
        blocks.append(current_block)

    for block in blocks:
        father_obj = build_tree(block, roomId)
        objTree.append(father_obj)
    return objTree

def build_tree(block, roomId):
    """
    以父物件为单位生成每个父物件的物件树
    """
    father_obj = {}

    while len(block) > 0:
        obj_to_del = []
        for obj_data in block:
            # 对每一个子物件，寻找idx对应的父物件位置，并添加到对应位置
            idx_to_find = obj_data['father_idx']
            if idx_to_find == "":
                father_obj = extract_dataline(block[0], roomId)
                father_obj["format"] = "sfyobj"

                obj_to_del.append(block[0])
            else:
                # 若能找到，则添加
                location = locate_idx(idx_to_find, father_obj)
                if len(location) > 0:
                    obj = extract_dataline(obj_data, roomId)
                    father_obj = modify_element(father_obj, location, obj)
                    obj_to_del.append(obj_data)
                # 若找不到则跳过
                else:
                    continue
        for x in obj_to_del:
            block.remove(x)


    #father_obj = apply_transformation(father_obj)

    return father_obj

def modify_element(nested_list, location, obj):
    """
    将子物件插入到物件树对应位置
    """
    nested_list = [nested_list]
    result = nested_list
    for index in location:
        result = result[index]['childrenList']

    result.append(obj)
    return nested_list[0]

def locate_idx(idx, obj, i=0):
    location = []
    if obj['idx'] == idx: # 找到了节点
        location.append(i)
        return location # 没有找到节点，递归终点
    if len(obj['childrenList']) == 0:
        return location
    
    location.append(i)
    start_num = len(location)
    for k, child_obj in enumerate(obj['childrenList']):
        cur_location = locate_idx(idx, child_obj, i=k)
        if len(cur_location) == 0:
            continue
        else:
            location.extend(cur_location)
    end_num = len(location)
    if start_num == end_num: #该次循环和子循环没有找到idx，pop掉之前添加的i
        location.pop()
    return location

def extract_dataline(data, roomId):
    """
    提取每一行数据并转换为物件信息
    """
    obj = {}

    obj['idx'] = data['idx']
    obj['father_idx'] = data['father_idx']
    obj['type'] = data['name']
    obj['modelId'] = data['idx'] # 暂时没有可用modelId

    #matrix = swap_yz_axes(data['mtx'])
    matrix = data['mtx']
    warnings.filterwarnings("error")
    try:
        obj['translate'], obj['scale'], obj['rotate'] = decompose_matrix(matrix)
    except RuntimeWarning as e:
        print(f"caught a runtime warning:{e}, {data}")

    size = data['value']
    size_swapped = [size[0], size[2], size[1]]
    position = data['position']
    position_swapped = [position[0], position[2], position[1]]
    min = position_swapped
    max = [x + y for x, y in zip(size_swapped, position_swapped)]
    obj['bbox'] = {'min':min, 'max':max} # 尚未矩陣變換的bbox

    obj['rotateOrder'] = 'XYZ'
    obj['orient'] = 0.0
    obj['coarseSemantic'] = data['name']
    obj['roomId'] = roomId
    obj['inDatabase'] = False
    obj['roomIds'] = []
    obj['attrs_name'] = data['attrs_name']
    obj['attrs_value'] = data['attrs_value']
    obj['childrenList'] = []
    
    return obj


def decompose_matrix(matrix):
    """
    将matrix转换为平移、旋转、缩放值
    """
    matrix = np.transpose(np.array(matrix))
    translate = matrix[:3, 3].tolist()

    no_t_matrix = matrix[:3, :3]
    scale = [np.linalg.norm([row[k] for row in no_t_matrix]) for k in range(3)]
    for k, x in enumerate(scale):
        if x == 0:
            scale[k] = 1e-9 # 防止除以零

    r = [[row[k]/scale[k] for k in range(3)] for row in no_t_matrix] # 似乎会出现异常

    rotate = [math.atan2(r[2][1], r[2][2]), math.asin(r[2][0]), math.atan2(r[1][0], r[0][0])] # y值可能会有错误

    
    translation = [translate[0], translate[2], translate[1]]
    rotation = [rotate[0], rotate[2], rotate[1]]
    scalar = [scale[0], scale[2], scale[1]]

    return translation, scalar, rotation



if not os.path.exists(TARGET_DIR):
    os.makedirs(TARGET_DIR)

for item in tqdm.tqdm(os.listdir(BASE_DIR)):
    if item.split('.')[-1] == 'json':
        with open(os.path.join(BASE_DIR,item),encoding='utf-8') as f:
            sfy_scene = json.load(f)

        # print()
        # print('*'*79)
        # print(os.path.join(TARGET_DIR + item))
        objlist = load_data(item.split('.')[0])
        #scene_json = transformScene(sfy_scene,item.split('.')[0], objlist)
        try:   
            scene_json = transformScene(sfy_scene,item.split('.')[0], objlist)
        except:
            continue
        filename = os.path.join(TARGET_DIR, item)
        with open(filename,'w') as f:
            print(filename)
            json.dump(scene_json,f)


