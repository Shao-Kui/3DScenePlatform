import sk
import numpy as np
from layoutmethods.projection2d import processGeo as p2d, getobjCat
from shapely.geometry.polygon import Polygon, LineString, Point
import json
import copy
import math
import os
from sceneviewer.utils import twoInfLineIntersection
import pathTracing as pt
import time
import cv2
from PIL import Image,ImageDraw

SAMPLE_COUNT = 4
RENDERWIDTH = 600
ASPECT = 16 / 9

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
        [0,0,-1],
        [1,0,0],
        [-1,0,0]
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
            print(p)
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




def cameraRotateAngle(phi):
    return math.atan(0.2360679774997898 * math.tan(phi))


"""
    for view rendering;
"""

def renderPcamAsync(scenejson,identifier,dst=None):
    pt.USENEWWALL = True
    if dst is not None:
        return pt.pathTracing(scenejson, SAMPLE_COUNT, dst)
    return pt.pathTracing(scenejson, SAMPLE_COUNT, f"./latentspace/autoview/{scenejson['origin']}/{identifier}.png")

def renderGivenPcam(pcam, scenejson, dst=None, isPathTrancing=True,room_id = None):
    scenejson["PerspectiveCamera"] = scenejson["PerspectiveCamera"].copy()
    scenejson["PerspectiveCamera"]['origin'] = pcam['origin']
    scenejson["PerspectiveCamera"]['target'] = pcam['target']
    scenejson["PerspectiveCamera"]['up'] = pcam['up']
    scenejson["canvas"] = scenejson["canvas"].copy()
    scenejson['canvas']['width']  = int(RENDERWIDTH)
    scenejson['canvas']['height'] = int(RENDERWIDTH / ASPECT)
    # identifier = uuid.uuid1()
    identifier = f'0-room{pcam["roomId"]}-{pcam["type"]}'
    if room_id is not None:
        identifier = f'sfy-{room_id}-{pcam["count"]}'
    # identifier = f'room{pcam["roomId"]}-{pcam["type"]}-{pcam["cons"]}'
    if not os.path.exists(f"./latentspace/autoview/{scenejson['origin']}"):
        os.makedirs(f"./latentspace/autoview/{scenejson['origin']}")
    pcam['identifier'] = str(identifier)
    pcam['scenejsonfile'] = scenejson['origin']
    with open(f"./latentspace/autoview/{scenejson['origin']}/{identifier}.json", 'w') as f:
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
    for room in scenejson['rooms']:
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

        pcams = autoViewsDominant(room, scenejson, 1)
        print(pcams)
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
            for index, pcam in zip(range(len(pcams)), pcams[0:20]): # pcams[0:200]
                # if index > 0 and pcam['score'] < 0.01:
                #     continue
                # pcams[index]['direction'] = balancing(pcams[index], room, pcams[index]['theta'])
                thread = renderGivenPcam(pcam, scenejson.copy(), isPathTrancing=isPathTrancing, room_id=room_id)
                if thread is not None:
                    renderThreads.append(thread)
    if not os.path.exists(f'./latentspace/autoview/{scenejson["origin"]}'):
        print(f'{scenejson["origin"]} is an empty floorplan. ')
        return []
    # hamilton(scenejson)
    for t in renderThreads:
        t.join()
    # try:
    #     showPcamInset(scenejson['origin'])
    #     showPcamPoints(scenejson['origin'])
    # except:
    #     pass
    return renderThreads


def renderAll():
    print("new view method!!")
    start_time = time.time()
    root_path = 'C:\\Users\\evan\\Desktop\\zhx_workspace\\SceneViewer\\test_20230821'
    for file_name in os.listdir(root_path):
        room_file = os.path.join(root_path,file_name)
        room_id = file_name.split('.')[0]
        print(room_id)
        with open(room_file,'r') as f:
            scene_json = json.load(f)
        f.close()
        # print(scene_json['rooms'][0]['roomNorm'])
        scene_json['PerspectiveCamera'] = {}
        scene_json['PerspectiveCamera']['fov'] = 75
        scene_json['canvas'] = {}
        sk.preloadAABBs(scene_json)

        
        print(f'Starting: {scene_json["origin"]}...')
        renderThreads = autoViewRooms(scene_json,room_id=room_id)
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
    return [right_up,left_down]

def showRoomDownView(room,scale, pcams):
    img = np.zeros((scale,scale,3),np.int8)
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
        cv2.line(img,p1,p2,(20,120,50),8)
        
    # draw objects 
    for obj in room['objList']:
        if obj['coarseSemantic'] == 'Door' or obj['coarseSemantic'] == 'Window':
            continue
        p_max = (np.array((obj['bbox']['max'][0],obj['bbox']['max'][2]))-old_centre)*K+centre
        p_min = (np.array((obj['bbox']['min'][0],obj['bbox']['min'][2]))-old_centre)*K+centre
        p_max = np.array(p_max,np.int32)
        p_min = np.array(p_min,np.int32)
        obj_centre = (p_max+p_min)//2


        cv2.rectangle(img,p_min,p_max,(255,255,255),8)
    
    print(len(pcams))

    for pcam in pcams:
        origin = (np.array((pcam['origin'][0],pcam['origin'][2])) - old_centre)*K+centre
        origin = np.array(origin,np.int32)
        target = (np.array((pcam['target'][0],pcam['target'][2])) - old_centre)*K+centre
        target = np.array(target,np.int32)

        
        cv2.circle(img, origin,6,(255,0,0), -1)
        cv2.putText(img,str(pcam['count']),origin,cv2.FONT_HERSHEY_SIMPLEX,1,(255,0,0),2)
        # cv2.line(img,origin,target,(255,0,0),8)
        
    cv2.imshow('tst',img)
    cv2.waitKey(0)
        

def test():
    test_file = 'C:\\Users\\evan\\Desktop\\zhx_workspace\\SceneViewer\\test_20230821\\5CA9B380-7571-4910-A22F-3069A5A3A886.json'
     #5CA9B380-7571-4910-A22F-3069A5A3A886.json
     #5BAE2F7B-323D-4d02-8BE2-0BDFC12D240E.json
     #D835ADAA-B9B0-45d4-B354-1198C6908D0D.json
     #52D3AC63-A286-4aea-A7A1-C4ED76590955.json
    with open(test_file,'r') as f:  
        scene_json = json.load(f)
    f.close()
    scene_json['PerspectiveCamera'] = {}
    scene_json['PerspectiveCamera']['fov'] = 75
    scene_json['canvas'] = {}
    sk.preloadAABBs(scene_json)
    print('*'*79)
    for room in scene_json['rooms']:
        pcams = autoViewsDominant(room,scene_json,1)
        showRoomDownView(room,1024, pcams)




if __name__ == "__main__":
    #renderAll()
    test()

        
        
