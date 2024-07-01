import sk
import numpy as np
import json
import copy
import math
import os
from sceneviewer.utils import twoInfLineIntersection,isPointOnVisualPlanes
from scenePhotographer.utils import Fov,aspect,findBBoxforGroup,pointInLine,normalize,TOKENS
from scenePhotographer.constraints import shapeOfView,symmetryScore,linesConvergeScore,amountOfInformation,maxSightWithWall,linesDynamics
import pathTracing as pt
import time
import cv2
from sklearn.cluster import AgglomerativeClustering 
import sys



SAMPLE_COUNT = 4
RENDERWIDTH = 600
ASPECT = 16 / 9

category_distance = []
category_list = ['Barstool', 'Bookcase / jewelry Armoire', 'Bunk Bed', 'Ceiling Lamp', 'Chaise Longue Sofa', 'Children Cabinet', 'Classic Chinese Chair', 'Coffee Table', 'Corner/Side Table', 'Desk', 'Dining Chair', 'Dining Table', 'Drawer Chest / Corner cabinet', 'Dressing Chair', 'Dressing Table', 'Footstool / Sofastool / Bed End Stool / Stool', 'Kids Bed', 'King-size Bed', 'L-shaped Sofa', 'Lazy Sofa', 'Lounge Chair / Cafe Chair / Office Chair', 'Loveseat Sofa', 'Nightstand', 'Pendant Lamp', 'Round End Table', 'Shelf', 'Sideboard / Side Cabinet / Console table', 'Single bed', 'TV Stand', 'Three-seat / Multi-seat Sofa', 'Wardrobe', 
'Wine Cabinet', 'armchair', 'door', 'window']

def compareVolume(obj1, obj2):
    """
        function to compare the volume of two objects' bounding box
    """
    v1_max = np.array(obj1['bbox']['max'])
    v1_min = np.array(obj1['bbox']['min'])
    v2_max = np.array(obj2['bbox']['max'])
    v2_min = np.array(obj2['bbox']['min'])

    _v1 = v1_max - v1_min
    _v2 = v2_max - v2_min

    v1 = abs(_v1[0]*_v1[1]*_v1[2])
    v2 = abs(_v2[0]*_v2[1]*_v2[2])

    return v1>v2



    

def volumeObj(obj1):
    v1_max = np.array(obj1['bbox']['max'])
    v1_min = np.array(obj1['bbox']['min'])
    _v1 = v1_max - v1_min
    return abs(_v1[0]*_v1[1]*_v1[2])

def centreOfObj(obj):
    """
        return the centre of obj's bounding box    
    """
    v1_max = np.array(obj['bbox']['max'])
    v1_min = np.array(obj['bbox']['min'])
    return (v1_max+v1_min)/2

def centreOfGroup(group):
    """
        return the centre of group's bounding box
    """
    g_max = np.array(group[0]["bbox"]['max'])
    g_min = np.array(group[0]['bbox']['min'])

    for obj in group:
        if obj['bbox']['min'][0] < g_min[0]:
            g_min[0] = obj['bbox']['min'][0]
        if obj['bbox']['min'][2] < g_min[2]:
            g_min[2] = obj['bbox']['min'][2]
        if obj['bbox']['min'][1] < g_min[1]:
            g_min[1] = obj['bbox']['min'][1]
        if obj['bbox']['max'][0] > g_max[0]:
            g_max[0] = obj['bbox']['max'][0]
        if obj['bbox']['max'][2] > g_max[2]:
            g_max[2] = obj['bbox']['max'][2]
        if obj['bbox']['max'][1] >g_max[1]:
            g_max[1] = obj['bbox']['max'][1]

    return (g_max+g_min)/2
        

def deduplicate(pcams:list):
    anchor = 0
    for i, pcam in enumerate(pcams):
        if i == 0:
            continue
        anchor_pcam = pcams[anchor]
        d1 = np.array(anchor_pcam['direction'])
        d2 = np.array(pcam['direction'])

        o1 = np.array(anchor_pcam['origin'])
        o2 = np.array(pcam['origin'])

        if 1-np.dot(d1,d2) <=1e-2 and np.linalg.norm(o1-o2) < 3:
            pcam['score'] = 0
            pcam['duplicate'] = 1
        else:
            anchor = i     
    return pcams   
                




def cameraRotateAngle(phi):
    return math.atan(0.2360679774997898 * math.tan(phi))

def keyToSort(pcam):
    return pcam['score']

def rotate(v, theta):
    # theta in radian
    v = np.array(v)
    rMatrix = np.array([
        [math.cos(theta),-math.sin(theta)],
        [math.sin(theta),math.cos(theta)]
    ])
    return np.matmul(rMatrix,v)


def furnitureCluster(room):
    objects = []
    objects_without_dw =[]
    length_of_objs =0
    for obj1 in room['objList']:
        if 'coarseSemantic' not in obj1 or obj1["coarseSemantic"] == 'Window' or obj1['coarseSemantic'] == 'Door':
            continue
        length_of_objs+=1
        objects_without_dw.append(obj1)
    dis_matrix = [[0 for _ in range(length_of_objs)] for __ in range(length_of_objs)]
    for i in range(length_of_objs):
        obj1 = objects_without_dw[i]
        for j in range(i+1,length_of_objs):
            obj2 = objects_without_dw[j]
            centre1 = centreOfObj(obj1)
            centre2 = centreOfObj(obj2)
            # type1 = category_list.index(obj1['coarseSemantic'])
            # type2 = category_list.index(obj2['coarseSemantic'])
            dis_matrix[i][j] = dis_matrix[j][i] = np.linalg.norm(centre1-centre2)#+ category_distance[type1][type2]
    if length_of_objs == 0:
        return None
    roomShape = room['roomShape']
    bbox = findBBox(roomShape)
    span = max(bbox[0]-bbox[1])
    threshold = span/3#+4.5
    try:
        agglomerative_label = AgglomerativeClustering(n_clusters=None,affinity='precomputed',distance_threshold=threshold,linkage='average').fit_predict(dis_matrix)

        
    except:
        agglomerative_label =  [0 for _ in range(length_of_objs)]
    return agglomerative_label

def autoViewsIncline(room, scene, nums = 1):
    # change the fov/2 to Radian. 
    theta = (np.pi * scene['PerspectiveCamera']['fov'] / 180) / 2
    # the the floor meta. 
    roomShape = np.array(room['roomShape'])
    floorMeta = np.hstack((np.array(room['roomShape']), np.array(room['roomNorm'])))
    r = room
    room_type = r['roomTypes']
    objects:list = copy.deepcopy(r['objList'])
    # determine dominant furniture
    
    objects.sort(key=volumeObj,reverse=True)
    dom_furniture = objects[:nums]
    for fur in dom_furniture:
        print(fur["coarseSemantic"])
    f_min = np.array(dom_furniture[0]['bbox']['min'])
    f_max = np.array(dom_furniture[0]['bbox']['max'])

    for dom in dom_furniture:
        if dom['bbox']['min'][0] < f_min[0]:
            f_min[0] = dom['bbox']['min'][0]
        if dom['bbox']['min'][2] > f_min[2]:
            f_min[2] = dom['bbox']['min'][2]
        if dom['bbox']['max'][0] > f_max[0]:
            f_max[0] = dom['bbox']['max'][0]
        if dom['bbox']['max'][2] < f_max[2]:
            f_max[2] = dom['bbox']['max'][2]
    
    f_centre = (f_max+ f_min)/2  # 临时的，后面会改'
    f_centre_2d = np.array([f_centre[0], f_centre[2]])


    wall_number = len(roomShape)
    min_dist = 10000
    selected_vertex = None
    for hot, vertex in enumerate(roomShape):
        succ_i = (hot+1)%wall_number #index
        pred_i = (hot-1)%wall_number
        succ = roomShape[succ_i]
        pred = roomShape[pred_i]

        if np.dot(succ-vertex,f_centre_2d-vertex) <0 or np.dot(pred-vertex,f_centre_2d-vertex) < 0:
            continue
        
        dist = np.linalg.norm(vertex-f_centre_2d)
        if dist < min_dist:
            min_dist = dist
            selected_vertex = vertex
    
    if selected_vertex is None:
        print("error in finding corners!!!")
        return
    
    ori = None
    for wall_index in range(len(roomShape)):
        wall_next = (wall_index+1)%len(roomShape)
        p3 = [roomShape[wall_index][0],roomShape[wall_index][1]]
        p4 = [roomShape[wall_next][0],roomShape[wall_next][1]]
        p = twoInfLineIntersection(selected_vertex, f_centre_2d, p3, p4)
        
        if p is None or not pointInLine(p,p3,p4):
            continue
        ori = np.array([p[0], 1.2, p[1]])
        print(ori)
        break
    
    raw_target =  np.array([selected_vertex[0], 1.2, selected_vertex[1]])
    raw_direction = normalize(raw_target - ori)
    raw_direction = [raw_direction[0],raw_direction[2]]
    rotate_angle = cameraRotateAngle(theta) ## radian


    final_direction1 = rotate(raw_direction,rotate_angle)
    final_direction1 = np.array([final_direction1[0], 0, final_direction1[1]])
    final_target1 = ori + 2*final_direction1



    final_direction2 = rotate(raw_direction,-rotate_angle)
    final_direction2 = np.array([final_direction2[0], 0, final_direction2[1]])
    print(final_direction2)
    final_target2 = ori + 2*final_direction2
    

    
    pcam = {}
    pcam['theta'] = theta
    # TODO theta can be adjusted
    pcam['roomId'] = room['id']
    pcam['origin'] = ori
    pcam['up'] = [0,1,0]
    pcam['rank'] = 0

    pcam['wallIndex'] = wall_index
    pcam['direction'] = final_direction1
    pcam['type'] = 'incline'
    pcam['target'] = final_target1
    pcam['count'] = 1

    pcam2 = {}
    pcam2['theta'] = theta
    # TODO theta can be adjusted
    pcam2['roomId'] = room['id']
    pcam2['origin'] = ori
    pcam2['up'] = [0,1,0]
    pcam2['rank'] = 0

    pcam2['wallIndex'] = wall_index
    pcam2['direction'] = final_direction2
    pcam2['type'] = 'incline'
    pcam2['target'] = final_target2
    pcam2['count'] = 2


    return [pcam,pcam2]      
    
def autoViewsDominant(room, scene, nums = 1):
    """
        return reasonable perspectives to view a certain interior scene
        according to volume
    """
    # change the fov/2 to Radian. 
    theta = (np.pi * scene['PerspectiveCamera']['fov'] / 180) / 2
    # the the floor meta. 
    roomShape = room['roomShape']
    floorMeta = np.hstack((np.array(room['roomShape']), np.array(room['roomNorm'])))
    r = room
    room_type = r['roomTypes']
    objects:list = copy.deepcopy(r['objList'])
    # determine dominant furniture


    objects.sort(key=volumeObj,reverse=True)
    dom_furniture = objects[:nums]
    for fur in dom_furniture:
        print(fur["coarseSemantic"])
    f_min = np.array(dom_furniture[0]['bbox']['min'])
    f_max = np.array(dom_furniture[0]['bbox']['max'])

    for dom in dom_furniture:
        if dom['bbox']['min'][0] < f_min[0]:
            f_min[0] = dom['bbox']['min'][0]
        if dom['bbox']['min'][2] > f_min[2]:
            f_min[2] = dom['bbox']['min'][2]
        if dom['bbox']['max'][0] > f_max[0]:
            f_max[0] = dom['bbox']['max'][0]
        if dom['bbox']['max'][2] < f_max[2]:
            f_max[2] = dom['bbox']['max'][2]
    
    f_centre = (f_max+ f_min)/2
    f_max[1]  = f_centre[1]
    f_min[1] = f_centre[1]

    directions = [
        [0,0,1],
        [1,0,0]

    ]


    directions = np.array(directions)
    pcams = []

    # count 
    count = 0
    for d in directions:
        p1 = [f_centre[0],f_centre[2]]
        p2 = f_centre + d
        p2 = [p2[0],p2[2]]
        for wall_index in range(len(roomShape)):
            wall_next = (wall_index+1)%len(roomShape)
            p3 = [roomShape[wall_index][0],roomShape[wall_index][1]]
            p4 = [roomShape[wall_next][0],roomShape[wall_next][1]]
            p = twoInfLineIntersection(p1, p2, p3, p4)
            #### 这里好像有问题 ！！ 
            if p is None:
                continue
            
            p = np.array(p)
            #print(p)
            ori_probe = np.array([p[0], 1.2, p[1]])
            target =  np.array([f_centre[0], 1.2, f_centre[2]])
            pcam = {}
            pcam['theta'] = theta
            # TODO theta can be adjusted
            pcam['roomId'] = room['id']
            pcam['origin'] = ori_probe
            pcam['up'] = [0,1,0]
            pcam['rank'] = 0

            pcam['wallIndex'] = wall_index
            pcam['direction'] = -d
            pcam['type'] = 'dominant-1'
            pcam['target'] = target
            pcam['count'] = count
            count += 1
            pcams.append(pcam)


    # calculate the hit points of the 'ray' and walls


    # maybe the process can be accelerate

    return pcams
    # take photo for dominant furniture
    # return pcams


def autoViewsCluster(room, scene, room_index):
    theta = (np.pi * scene['PerspectiveCamera']['fov'] / 180) / 2
    # the the floor meta. 
    roomShape = room['roomShape']
    print('here')

    objects:list = copy.deepcopy(room['objList'])

    groups = furnitureCluster(room)
    if groups is None:
        return []
    num_groups = len(set(groups))

    furniture_groups = [[] for _ in range(num_groups)]
    idx = 0
    for obj in objects:
        if 'coarseSemantic' not in obj or obj["coarseSemantic"] == 'Window' or obj['coarseSemantic'] == 'Door':
            continue
        furniture_groups[groups[idx]].append(obj)
        idx+=1
    

    pcams = []
    count = 0
    groups = []
    furniture_groups.sort(key=len,reverse=True)
    
    
    for group in furniture_groups:
        # 找中心
        # 打视点
        groups.append(group)
    if len(furniture_groups) >=2 :
        length = len(furniture_groups)
        for i in range(0,length):
            for j in range(i+1,length):
                temp = furniture_groups[i]+furniture_groups[j]
                groups.append(temp)

    for group in groups:
        g_centre = centreOfGroup(group)
        directions = [
            [0,0,1],
            [1,0,0],
            [-1,0,0],
            [0,0,-1]
        ]
        directions = np.array(directions)
        for d in directions:
            target = copy.deepcopy(g_centre)
            H = 1.2
            target[1] = H
            origin = target-d*maxSightWithWall(room,target,-d,True)
            origin = origin+0.05*d
            pcam = {}
            hfov = Fov(origin, d,target, group)

            pcam['ratio'] = aspect(origin,d,roomShape,hfov)
            pcam['theta'] = np.arctan(np.tan(hfov)/pcam['ratio'])
            # TODO theta can be adjusted
            pcam['direction'] = d
            pcam['roomId'] = room['id']
            pcam['origin'] = origin
            pcam['up'] = [0,1,0]
            pcam['rank'] = 0
            pcam['type'] = 'ClusterOrthorhombic'
            pcam['target'] = target
            pcam['count'] = count
            pcam['room_index'] = room_index
            pcam['symmetry'] = 0#symmetryScore(room,scene,pcam)
            pcam['lineDynamics'] =  linesDynamics(room,scene,pcam)
            pcam['information'] = amountOfInformation(room,scene,pcam)
            pcam['shapeOfView'] = shapeOfView(room,scene,pcam)
            pcam['score'] = 10*pcam['symmetry']+0.5*pcam['lineDynamics']+10*pcam['information']+1*pcam['shapeOfView'] if pcam['shapeOfView']>0 else 0
            count += 1
       
            pcams.append(pcam)  
            
    print(len(pcams))         
    return pcams

def topDownViews(room, scene, room_index):
    theta = (np.pi * scene['PerspectiveCamera']['fov'] / 180) / 2
    roomShape = room['roomShape']
    bbox = findBBox(roomShape)

    center = (bbox[0]+bbox[1])/2
    center = np.array([center[0],0,center[1]])
    direction = np.array([0,-1,0])
    length =5
    origin = center - length*direction

    pcams =[]

    pcam = {}
    pcam['theta'] = theta
    pcam['roomId'] = room['id']
    pcam['direction'] = direction
    pcam['origin'] = origin
    pcam['target'] = center
    pcam['up'] = [1,0,0]
    pcam['rank'] = 0
    pcam['type'] = 'topdown'
    pcam['room_index'] = room_index
    pcam['score'] = 0



    pcams.append(pcam)
    return pcams


def autoViewsClusterIncline(room, scene,room_index):
    theta = (np.pi * scene['PerspectiveCamera']['fov'] / 180) / 2
    # the the floor meta. 
    roomShape = room['roomShape']

    objects:list = copy.deepcopy(room['objList'])

    groups = furnitureCluster(room)
    if groups is None:
        return []
    num_groups = len(set(groups))

    furniture_groups = [[] for _ in range(num_groups)]
    idx = 0
    for obj in objects:
        if 'coarseSemantic' not in obj or obj["coarseSemantic"] == 'Window' or obj['coarseSemantic'] == 'Door':
            continue
        furniture_groups[groups[idx]].append(obj)
        idx+=1
    
    pcams = []
    count = 0
    furniture_groups.sort(key=len,reverse=True)
    for group in furniture_groups:
        # 找中心
        # 打视点
        g_max, g_min = findBBoxforGroup(group)
        g_centre = (g_max+g_min)/2
        four_corners = np.array([
            [g_max[0],g_centre[1], g_max[2]],
            [g_max[0],g_centre[1],g_min[2]],
            [g_min[0],g_centre[1],g_min[2]],
            [g_min[0],g_centre[1],g_max[2]]
        ])
        h = 1.3
        if g_centre[1] < 1.0:
            h = 1
        group_span = np.linalg.norm(four_corners[0]-four_corners[2])

        min_d = 1000
        min_idx = -1
        min_corner = None

        for corner in four_corners:
            for idx in range(len(roomShape)):
                jdx = (idx+1)%len(roomShape)
                kdx = (idx-1)%len(roomShape)
                test_vertex = np.array(roomShape[idx])
                succ_vertex = np.array(roomShape[jdx])
                prev_vertex = np.array(roomShape[kdx])

                wall_n = test_vertex-prev_vertex
                wall_s = succ_vertex-test_vertex
                mat = np.array([
                    wall_n,
                    wall_s,
                ])

                flag = np.linalg.det(mat) > 0
                corner_2d = np.array([corner[0],corner[2]])
                dist = np.linalg.norm(corner_2d-test_vertex)
                if dist<min_d and flag:
                    min_d = dist
                    min_idx = idx 
                    min_corner = corner
        
        center_projected = np.array([g_centre[0],g_centre[2]])
        section_wall_vertex = np.array(roomShape[min_idx])
        d1 = 0.75*group_span # scalar
        beta = cameraRotateAngle(theta)
        
        d2 = np.linalg.norm(section_wall_vertex-center_projected)
        gamma = np.arcsin(d1/d2*np.sin(beta))
        

             
        direction = min_corner - g_centre
        direction[1]=0
        direction = direction/np.linalg.norm(direction)
        if direction[0]*direction[2] > 0:
            direction = np.flip(direction)
        else:
            direction = -np.flip(direction)

        target = g_centre
        g_centre[1] = h

        origin = target-(0.75*group_span)*direction

        pcam = {}
        pcam['theta'] = theta
        pcam['roomId'] = room['id']
        pcam['origin'] = origin
        pcam['up'] = [0,1,0]
        pcam['rank'] = 0

        pcam['wallIndex'] = -1
        pcam['direction'] =direction
        pcam['type'] = 'ClusterInclineTPP'
        pcam['target'] = target
        pcam['room_index'] = room_index
        pcam['count'] = count
        pcam['symmetry'] = symmetryScore(room,scene,pcam)
        pcam['linecoverge'] = linesConvergeScore(room,scene,pcam)
        pcam['information'] = amountOfInformation(room,scene,pcam)
        pcam['shapeOfView'] = shapeOfView(room,scene,pcam)
        pcam['score'] = 1*pcam['symmetry']+pcam['linecoverge']+10*pcam['information']+0.1*pcam['shapeOfView'] if pcam['shapeOfView']>0 else 0
        count+=1
        pcams.append(pcam)





        for idx in range(len(roomShape)):
            jdx = (idx+1)%len(roomShape)
            kdx = (idx-1)%len(roomShape)
            test_vertex = np.array(roomShape[idx])
            succ_vertex = np.array(roomShape[jdx])
            prev_vertex = np.array(roomShape[kdx])

            wall_n = test_vertex-prev_vertex
            wall_s = succ_vertex-test_vertex
            mat = np.array([
                wall_n,
                wall_s,
            ])

            flag = np.linalg.det(mat) > 0
            g_centre_2d = np.array([g_centre[0],g_centre[2]])
            dist = np.linalg.norm(g_centre_2d-test_vertex)
            if dist<min_d and flag:
                min_d = dist
                min_idx = idx      
        selected_vertex = roomShape[min_idx]
        raw_origin = np.array([g_centre[0],g_centre[2]])
        raw_direction = selected_vertex - raw_origin
        final_direction = np.array([raw_direction[0],0,raw_direction[1]])
        for wall_index in range(len(roomShape)):
            wall_next = (wall_index+1)%len(roomShape)
            p3 = [roomShape[wall_index][0],roomShape[wall_index][1]]
            p4 = [roomShape[wall_next][0],roomShape[wall_next][1]]
            p = twoInfLineIntersection([selected_vertex[0],selected_vertex[1]],[raw_origin[0],raw_origin[1]], p3, p4)
            if p is None or not pointInLine(p,p3,p4):
                continue
            ori = np.array([p[0], h, p[1]])

            # pcam = {}
            # pcam['theta'] = theta
            # # TODO theta can be adjusted
            # pcam['roomId'] = room['id']
            # pcam['origin'] = ori+final_direction*0.1
            # pcam['up'] = [0,1,0]
            # pcam['rank'] = 0

            # pcam['wallIndex'] = wall_index
            # pcam['direction'] = final_direction
            # pcam['type'] = 'ClusterIncline'
            # pcam['target'] = [g_centre[0],h,g_centre[2]]
            # pcam['room_index'] = room_index
            # pcam['count'] = count
            # pcam['symmetry'] = symmetryScore(room,scene,pcam)
            # pcam['linecoverge'] = linesConvergeScore(room,scene,pcam)
            # pcam['information'] = amountOfInformation(room,scene,pcam)
            # pcam['shapeOfView'] = shapeOfView(room,scene,pcam)
            # pcam['score'] = 1*pcam['symmetry']+pcam['linecoverge']+10*pcam['information']+0.1*pcam['shapeOfView'] if pcam['shapeOfView']>0 else 0
            # count+=1
            # pcams.append(pcam)
    return pcams
    #         h = 1.3
    #     for wall_jndex in range(len(roomShape)):
    #         selected_vertex = roomShape[wall_jndex]
    #         raw_origin = np.array(g_centre[0],g_centre[2])
    #         rotate_angle = cameraRotateAngle(theta)
    #         raw_direction = selected_vertex-raw_origin
    #         final_direction1 = rotate(raw_direction,rotate_angle)
    #         final_direction1 = np.array([final_direction1[0], 0, final_direction1[1]])

    #         final_direction2 = rotate(raw_direction,-rotate_angle)
    #         final_direction2 = np.array([final_direction2[0], 0, final_direction2[1]])

    #         final_directions = [final_direction1,final_direction2]
    #         for d in final_directions:
    #             final_target = g_centre+2*d
    #             for wall_index in range(len(roomShape)):
    #                 wall_next = (wall_index+1)%len(roomShape)
    #                 p3 = [roomShape[wall_index][0],roomShape[wall_index][1]]
    #                 p4 = [roomShape[wall_next][0],roomShape[wall_next][1]]
    #                 p = twoInfLineIntersection([final_target[0],final_target[2]],[g_centre[0],g_centre[2]], p3, p4)
        
    #                 if p is None or not pointInLine(p,p3,p4):
    #                     continue
    #                 h = 1.3
    #                 if g_centre[1] < 1.2:
    #                     h = 1.3
    #                 ori = np.array([p[0], h, p[1]])

    #                 pcam = {}
    #                 pcam['theta'] = theta
    #                 # TODO theta can be adjusted
    #                 pcam['roomId'] = room['id']
    #                 pcam['origin'] = ori
    #                 pcam['up'] = [0,1,0]
    #                 pcam['rank'] = 0

    #                 pcam['wallIndex'] = wall_index
    #                 pcam['direction'] = d
    #                 pcam['type'] = 'ClusterIncline'
    #                 pcam['target'] = [g_centre[0],h,g_centre[2]]
    #                 pcam['room_index'] = room_index
    #                 pcam['count'] = count
    #                 pcam['score'] = evaluateViews(room,scene,pcam)
    #                 count+=1
    #                 pcams.append(pcam)
    # return pcams

        

"""
    for view rendering;
"""
def renderPcamAsync(scenejson,identifier,dst=None):
    pt.USENEWWALL = True
    if dst is not None:
        return pt.pathTracing(scenejson, SAMPLE_COUNT, dst)
    return pt.pathTracing(scenejson, SAMPLE_COUNT, f"./latentspace/sfy/{scenejson['origin']}/{identifier}.png")

def renderGivenPcam(pcam, scenejson, dst=None, isPathTrancing=True,room_id = None):
    scenejson["PerspectiveCamera"] = scenejson["PerspectiveCamera"].copy()
    scenejson["PerspectiveCamera"]['fov'] = 180*pcam['theta']/np.pi*2
    scenejson["PerspectiveCamera"]['origin'] = pcam['origin']
    scenejson["PerspectiveCamera"]['target'] = pcam['target']
    scenejson["PerspectiveCamera"]['up'] = pcam['up']
    scenejson["canvas"] = scenejson["canvas"].copy()
    scenejson['canvas']['width']  = int(RENDERWIDTH)
    scenejson['canvas']['height'] = int(RENDERWIDTH / pcam['ratio'])
    # identifier = uuid.uuid1()
    identifier = f'0-room{pcam["roomId"]}-{pcam["type"]}'
    if room_id is not None:
        identifier = f'sfy-{room_id}-{pcam["room_index"]}-{pcam["type"]}-{pcam["rank"]}'
    # identifier = f'room{pcam["roomId"]}-{pcam["type"]}-{pcam["cons"]}'
    if not os.path.exists(f"./latentspace/sfy/{scenejson['origin']}"):
        os.makedirs(f"./latentspace/sfy/{scenejson['origin']}")
    pcam['identifier'] = str(identifier)
    pcam['scenejsonfile'] = scenejson['origin']
    with open(f"./latentspace/sfy/{scenejson['origin']}/{identifier}.json", 'w') as f:
        json.dump(pcam, f, default=sk.jsonDumpsDefault)
    if isPathTrancing:
        thread = sk.BaseThread(
            name='autoView', 
            target=renderPcamAsync,
            method_args=(scenejson.copy(),identifier,dst)
        )
        thread.start()
        return thread

def autoViewRooms(scenejson, isPathTrancing=True, room_id = None):
    pt.SAVECONFIG = False
    sk.preloadAABBs(scenejson)
    renderThreads = []
    for idx,room in enumerate(scenejson['rooms']):
        # we do not generating views in an empty room. 
        obj3DModelCount = 0
        for obj in room['objList']:
            try:
                if sk.objectInDataset(obj['modelId']) or obj['format'] == 'sfy' or obj['format'] == 'glb':
                    obj3DModelCount += 1
            except:
                continue
        if obj3DModelCount == 0:
            continue

        pcams = autoViewsCluster(room, scenejson,idx)
        print(len(pcams))
    
        pcams.sort(key=keyToSort,reverse=True)
        # pcams = deduplicate(pcams)
        # pcams.sort(key=keyToSort,reverse=True)
            
        
        for i,pcam in enumerate(pcams):
            pcam['rank'] = i
        #print(pcams)
        # pcams = eachNoConstraint(pcams)
        # global SAMPLE_COUNT
        # SAMPLE_COUNT = 64
        if isinstance(pcams, (dict,)):
            for tp in pcams:
                if pcams[tp] is None:
                    continue
                # pcams[tp]['direction'] = balancing(pcams[tp], room, pcams[tp]['theta'])
                thread = renderGivenPcam(pcams[tp], scenejson.copy(), isPathTrancing=isPathTrancing, room_id=room_id)
                if thread is not None:
                    renderThreads.append(thread)
        elif isinstance(pcams, (list,)):
            for index, pcam in zip(range(len(pcams)), pcams[0:11]): # pcams[0:200]
                # if index > 0 and pcam['score'] < 0.01:
                #     continue
                # pcams[index]['direction'] = balancing(pcams[index], room, pcams[index]['theta'])
                thread = renderGivenPcam(pcam, scenejson.copy(), isPathTrancing=isPathTrancing, room_id=room_id)
                if thread is not None:
                    renderThreads.append(thread)
    if not os.path.exists(f'./latentspace/sfy/{scenejson["origin"]}'):
        os.mkdir(f'./latentspace/sfy/{scenejson["origin"]}')
        print(f'{scenejson["origin"]} is an empty floorplan. ')
        # return []
    # hamilton(scenejson)
    print(len(renderThreads))
    for t in renderThreads:
        t.join()
    # try:
    #     showPcamInset(scenejson['origin'])
    #     showPcamPoints(scenejson['origin'])
    # except:
    #     pass
    return renderThreads


def renderAll():
    start_time = time.time()
    root_path = 'C:\\Users\\evan\\Desktop\\zhx_workspace\\SceneViewer\\test_20230821'
    for file_name in os.listdir(root_path):
        room_file = os.path.join(root_path,file_name)
        room_id = file_name.split('.')[0]
        print(room_id)
        if room_id not in TOKENS:
            continue
        with open(room_file,'r') as f:
            scene_json = json.load(f)
        f.close()
        # print(scene_json['rooms'][0]['roomNorm'])
        scene_json['PerspectiveCamera'] = {}
        scene_json['PerspectiveCamera']['fov'] = 75
        scene_json['canvas'] = {}
        sk.preloadAABBs(scene_json)

        
        print(f'Starting: {scene_json["origin"]}...')
        try:
            renderThreads = autoViewRooms(scene_json,room_id=room_id)
        except:
            continue
        for t in renderThreads:
            t.join()

    print("\r\n --- %s seconds --- \r\n" % (time.time() - start_time))


def findBBox(roomShape):
    right_up = [-1000,-1000]
    left_down = [100000,100000]
    for wall in roomShape:
        if wall[0]>right_up[0]:
            right_up[0] = wall[0]
        if wall[0] < left_down[0]:
            left_down[0] = wall[0]
        if wall[1] > right_up[1]:
            right_up[1] = wall[1]
        if wall[1] < left_down[1]:
            left_down[1] = wall[1]
    return np.array([right_up,left_down])

def showRoomDownView(room,scale, pcams,scene_json):
    img = np.zeros((scale,scale,3),np.int8)
    img[:] = (255,255,255)
    centre = (scale//2, scale//2)
    
    
 
    K = 100

    roomShape = room['roomShape']
    bbox = np.array(findBBox(roomShape))
    old_centre = (bbox[0]+bbox[1])/2

    # draw walls of the room
    for wall_index in range(len(roomShape)):
        wall_next = (wall_index+1) % len(roomShape)
        p1 = (np.array(roomShape[wall_index])-old_centre)*K+centre
        p1[0] = int(p1[0])
        p1[1] = int(p1[1])
        p2 = (np.array(roomShape[wall_next])-old_centre)*K+centre
        p2[0] = int(p2[0])
        p2[1] = int(p2[1])
        p1 = np.array(p1,np.int32)
        p2 = np.array(p2,np.int32)
        cv2.line(img,p1,p2,(255,255,255),8)
        
    # draw objects 
    colors = [(0,0,255),(255,0,0), (0,255,0),(255,255,0),(0,255,255), (255,0,255),(0,200,200),(128,128,128),(156,12,245)]
    groups = furnitureCluster(room)
    idx = 0
    for obj in room['objList']:
        if 'coarseSemantic' not in obj or obj['coarseSemantic'] == 'Door' or obj['coarseSemantic'] == 'Window':
            continue
        p_max = (np.array((obj['bbox']['max'][0],obj['bbox']['max'][2]))-old_centre)*K+centre
        p_min = (np.array((obj['bbox']['min'][0],obj['bbox']['min'][2]))-old_centre)*K+centre
        p_max = np.array(p_max,np.int32)
        p_min = np.array(p_min,np.int32)
        obj_centre = (p_max+p_min)//2


        cv2.rectangle(img,p_min,p_max,colors[groups[idx]],8)
        #cv2.rectangle(img,p_min,p_max,colors[0],8)
        idx+=1
    
    print(len(pcams))

    for pcam in pcams:
        origin = (np.array((pcam['origin'][0],pcam['origin'][2])) - old_centre)*K+centre
        origin = np.array(origin,np.int32)
        target = (np.array((pcam['target'][0],pcam['target'][2])) - old_centre)*K+centre
        target = np.array(target,np.int32)

        cv2.circle(img, origin,6,(255,255,255), -1)
        cv2.putText(img,str(pcam['rank']),origin,cv2.FONT_HERSHEY_SIMPLEX,1,(255,255,255),2)

        
        cv2.line(img,origin,target,(255,0,0),8)
        
    cv2.imshow('tst',img)
    #cv2.imwrite(f'C:\\Users\\evan\\Desktop\\zhx_workspace\\SceneViewer\\cluster_result\\{scene_json["origin"]}.jpg',img)

    cv2.waitKey(0)
        

def test():
    test_dir ='C:\\Users\\evan\\Desktop\\zhx_workspace\\SceneViewer\\test_20230821'
    # r'C:\Users\evan\Desktop\zhx_workspace\索菲亚柜体转换_20240115\target'
    #'C:\\Users\\evan\\Desktop\\zhx_workspace\\SceneViewer\\test_20230821'
    for jsfile in os.listdir(test_dir):
        test_file = os.path.join(test_dir,jsfile)
        #5CA9B380-7571-4910-A22F-3069A5A3A886.json 客厅+餐厅黑色主题
        #5BAE2F7B-323D-4d02-8BE2-0BDFC12D240E.json 白色主题卧室
        #D835ADAA-B9B0-45d4-B354-1198C6908D0D.json 一边柜体卧室
        #52D3AC63-A286-4aea-A7A1-C4ED76590955.json 白色主题客厅加餐厅
        if jsfile!='r3.json':
            continue
        with open(test_file,'r') as f:  
            scene_json = json.load(f)
        f.close()
        scene_json['PerspectiveCamera'] = {}
        scene_json['PerspectiveCamera']['fov'] = 75
        scene_json['canvas'] = {}
        sk.preloadAABBs(scene_json)
        print('*'*79)
        print(scene_json['origin'])
        for idx,room in enumerate(scene_json['rooms']):
            pcams = topDownViews(room,scene_json,idx)
            try:
                showRoomDownView(room,1024, pcams,scene_json)
            except:
                continue


def test_view():
    room = 'C:\\Users\\evan\\Desktop\\zhx_workspace\\SceneViewer\\test_20230821\\rooms1.json'
    pcam = 'D:\\zhx_workspace\\3DScenePlatformDev\\latentspace\\autoview\\0ec97239-1e30-4334-8d60-e21fb2f91f8f\\sfy-rooms1-0-ClusterOrthorhombic-15.json'
    with open(room) as f:
        scene = json.load(f)
    sk.preloadAABBs(scene)
    with open(pcam) as f:
        pcam = json.load(f)
    for obj in scene['rooms'][0]['objList']:
        if 'bbox' not in obj or 'coarseSemantic' not in obj or obj['coarseSemantic'] == 'Window' or obj['coarseSemantic'] == 'Door':
            continue
        center =obj['AABB']['center']
        if isPointOnVisualPlanes(center,pcam['origin'],pcam['direction'],pcam['theta']):
            print(obj['coarseSemantic'])


if __name__ == "__main__":
    category_distance =np.loadtxt(r"C:\Users\evan\Desktop\zhx_workspace\SceneViewer\category_distance.txt")
    
    if len(sys.argv)>1:
        if sys.argv[1] == 'render':
            renderAll()
        elif sys.argv[1] == 'test':
            test()
        else:
            pass
    else:
        # renderAll()
        test()
        #test_view()        
        
