import numpy as np
import json
import projection2d
from projection2d import processGeo as p2d, getobjCat
from shapely.geometry.polygon import Polygon
import random
import pathTracing as pt
import sk
import shutil
import time
import uuid
import os

with open('./dataset/occurrenceCount/autoview_ratio.json') as f:
    res_ratio_dom = json.load(f)

pt.r_dir = 'AutoView'
projection2d.get_norm = True
TARDIS = 3.397448931651581
CAMHEI = 1.
pt.REMOVELAMP = False

# https://stackoverflow.com/questions/21037241/how-to-determine-a-point-is-inside-or-outside-a-cube
def inside_test(points , cube3d):
    """
    cube3d  =  numpy array of the shape (8,3) with coordinates in the clockwise order. first the bottom plane is considered then the top one.
    points = array of points with shape (N, 3).

    Returns the indices of the points array which are outside the cube3d
    """
    b1,b2,b3,b4,t1,t2,t3,t4 = cube3d

    dir1 = (t1-b1)
    size1 = np.linalg.norm(dir1)
    dir1 = dir1 / size1

    dir2 = (b2-b1)
    size2 = np.linalg.norm(dir2)
    dir2 = dir2 / size2

    dir3 = (b4-b1)
    size3 = np.linalg.norm(dir3)
    dir3 = dir3 / size3

    cube3d_center = (b1 + t3)/2.0

    dir_vec = points - cube3d_center

    res1 = np.where( (np.absolute(np.dot(dir_vec, dir1)) * 2) > size1 )[0]
    res2 = np.where( (np.absolute(np.dot(dir_vec, dir2)) * 2) > size2 )[0]
    res3 = np.where( (np.absolute(np.dot(dir_vec, dir3)) * 2) > size3 )[0]

    return list( set().union(res1, res2, res3) )

def autoview(scenejson):
    pass

def keyObjectKeyFunction(obj):
    if obj is None:
        return -1
    if 'modelId' not in obj:
        return -1
    cat = getobjCat(obj['modelId'])
    if cat == "Unknown Category" or cat not in res_ratio_dom:
        return -1
    return res_ratio_dom[cat][obj['roomType']]

'''
:param point: the given point in a 3D space
:param translate: the translation in 3D
:param angle: the rotation angle on XOZ plain
:param scale: the scale in 3D
'''
def transform_a_point(point, translate, angle, scale):
    result = point.copy()
    scaled = point.copy()
    scaled = point * scale
    result[0] =  np.cos(angle) * scaled[0] + np.sin(angle) * scaled[2]
    result[2] = -np.sin(angle) * scaled[0] + np.cos(angle) * scaled[2]
    return result + translate

def calCamUpVec(origin, target):
    # calculate the 'up' vector via the normal of plane;    
    upInit = np.array([0., 1., 0.])
    normal = target - origin
    normal = normal / np.linalg.norm(normal, ord=2)
    up = upInit - np.sum(upInit * normal) * normal
    up = up / np.linalg.norm(up, ord=2)
    return up

def autoViewRoom(room):
    """
    room: the room(json) of S-K format. 

    returns a aesthetic view of a single room, 
    including origin vector, target vector and up vector of the camera. 
    """
    floorMeta = p2d('.', '/dataset/room/{}/{}f.obj'.format(room['origin'], room['modelId']))
    floorShape = Polygon(floorMeta[:, 0:2]) # requires python library 'shapely'
    roomType = room['roomTypes'][0]
    for obj in room['objList']:
        obj['roomType'] = roomType
    room['objList'].sort(key=keyObjectKeyFunction, reverse=True)

    # return autoViewOnePoint(floorMeta)
    # return autoViewFromPatterns(room)

def autoViewFromPatterns(room):
    pcam = {}
    roomType = room['roomTypes'][0]
    for obj in room['objList']:
        obj['roomType'] = roomType
    room['objList'].sort(key=keyObjectKeyFunction, reverse=True)
    if len(room['objList']) == 0:
        return None
    theDom = room['objList'][0]
    # find a random pattern of object room['objList'][0];
    try:
        with open(f"./latentspace/pos-orient-5/{theDom['modelId']}.json") as f:
            pattern = random.choice(random.choice(list(json.load(f).items()))[1])
            print(pattern)
    except Exception as e:
        print(e)
        return None
    # rotate & scale the prior; 
    pattern['translate'] = transform_a_point(np.array(pattern['translate']), theDom['translate'], theDom['orient'], theDom['scale'])
    # camTranslate = np.array(theDom['translate']) + pattern['translate']
    camTranslate = pattern['translate'].copy()
    pcam["origin"] = (camTranslate.copy()).tolist()
    # calculate the vector toward the 'target'; 
    theta = theDom['orient'] + pattern['orient']
    camTarget = camTranslate.copy()
    camTarget[0] += np.sin(theta)
    camTarget[2] += np.cos(theta)
    pcam["target"] = (camTarget.copy()).tolist()
    # calculate the 'up' vector via the normal of plane;    
    pcam["up"] = calCamUpVec(camTranslate, camTarget).tolist()
    # get the object AABB bounding box; 
    subAABB = sk.load_AABB(pattern['sub'])
    tall = subAABB['max'][1] * pattern['scale'][1]
    pcam["origin"][1] = tall
    pcam["target"][1] = tall
    return pcam

def autoViewOnePoint(room):
    floorMeta = p2d('.', '/dataset/room/{}/{}f.obj'.format(room['origin'], room['modelId']))
    H = 1.2
    # currently, we randomly select a wall for one-point perspective. 
    wallIndex = np.random.choice(floorMeta.shape[0])
    wallIndexNext = ( wallIndex + 1 ) % floorMeta.shape[0]
    middlePoint = (floorMeta[wallIndex][0:2] + floorMeta[wallIndexNext][0:2]) / 2
    middlePoint += floorMeta[wallIndex][2:4] * 0.05
    pcam = {}
    pcam["origin"] = middlePoint.tolist()
    pcam["origin"].insert(1, H)
    pcam["target"] = (middlePoint + floorMeta[wallIndex][2:4] * 10).tolist()
    pcam["target"].insert(1, H)
    pcam["up"] = calCamUpVec(np.array(pcam["origin"]), np.array(pcam["target"])).tolist()
    return pcam

def autoViewRodrigues(room, fov):
    # change the fov/2 to Radian. 
    theta = (np.pi * fov / 180) / 2
    # the the floor meta. 
    floorMeta = p2d('.', '/dataset/room/{}/{}f.obj'.format(room['origin'], room['modelId']))
    wallIndex = np.random.choice(floorMeta.shape[0])
    wallIndexNext = ( wallIndex + 1 ) % floorMeta.shape[0]
    middlePoint = (floorMeta[wallIndex][0:2] + floorMeta[wallIndexNext][0:2]) / 2
    middlePoint += floorMeta[wallIndex][2:4] * 0.005
    # the height of the wall. 
    H = sk.getWallHeight(f"./dataset/room/{room['origin']}/{room['modelId']}w.obj")
    origin = middlePoint.tolist()
    origin.insert(1, H)
    # the normal of the wall. 
    normal = floorMeta[wallIndex][2:4].tolist()
    normal.insert(1, 0.)
    # apply Rogrigues Formula. 
    v = np.array(normal)
    v /= np.linalg.norm(v, ord=2)
    k = (floorMeta[wallIndex][0:2] - floorMeta[wallIndexNext][0:2]).tolist()
    k.insert(1, 0.)
    k = np.array(k)
    k /= np.linalg.norm(k, ord=2)
    target = v * np.cos(-theta) + np.cross(k, v) * np.sin(-theta)
    # construct the perspective camera. 
    pcam = {}
    pcam["origin"] = origin
    pcam["target"] = (np.array(origin) + target).tolist()
    pcam["up"] = calCamUpVec(np.array(pcam["origin"]), np.array(pcam["target"])).tolist()
    return pcam

def autoViewsRodrigues(room, fov):
    # change the fov/2 to Radian. 
    theta = (np.pi * fov / 180) / 2
    # the the floor meta. 
    floorMeta = p2d('.', '/dataset/room/{}/{}f.obj'.format(room['origin'], room['modelId']))
    # the height of the wall. 
    H = sk.getWallHeight(f"./dataset/room/{room['origin']}/{room['modelId']}w.obj")
    pcams = []
    for wallIndex in range(floorMeta.shape[0]):
        wallIndexNext = ( wallIndex + 1 ) % floorMeta.shape[0]
        middlePoint = (floorMeta[wallIndex][0:2] + floorMeta[wallIndexNext][0:2]) / 2
        middlePoint += floorMeta[wallIndex][2:4] * 0.005
        origin = middlePoint.tolist()
        origin.insert(1, H)
        # the normal of the wall. 
        normal = floorMeta[wallIndex][2:4].tolist()
        normal.insert(1, 0.)
        # apply Rogrigues Formula. 
        v = np.array(normal)
        v /= np.linalg.norm(v, ord=2)
        k = (floorMeta[wallIndex][0:2] - floorMeta[wallIndexNext][0:2]).tolist()
        k.insert(1, 0.)
        k = np.array(k)
        k /= np.linalg.norm(k, ord=2)
        target = v * np.cos(-theta) + np.cross(k, v) * np.sin(-theta)
        # construct the perspective camera. 
        pcam = {}
        pcam["origin"] = origin
        pcam["target"] = (np.array(origin) + target).tolist()
        pcam["up"] = calCamUpVec(np.array(pcam["origin"]), np.array(pcam["target"])).tolist()
        # pcams.append(pcam)

        # next, we try generating a view w.r.t the current wall. 
        v = np.array([0, -1, 0])
        target = v * np.cos(theta) + np.cross(k, v) * np.sin(theta)
        pcam = {}
        pcam["origin"] = origin
        pcam["target"] = (np.array(origin) + target).tolist()
        pcam["up"] = calCamUpVec(np.array(pcam["origin"]), np.array(pcam["target"])).tolist()
        pcams.append(pcam)

    return pcams

def autoViewTwoPoint(room):
    floorMeta = p2d('.', '/dataset/room/{}/{}f.obj'.format(room['origin'], room['modelId']))
    # note that the result anchor point is 'walllIndexNext'. 
    wallIndex = np.random.choice(floorMeta.shape[0])
    wallIndexNext = ( wallIndex + 1 ) % floorMeta.shape[0]
    direction = floorMeta[wallIndex][2:4] + floorMeta[wallIndexNext][2:4]
    direction /= np.linalg.norm(direction, ord=2)
    origin = (floorMeta[wallIndexNext][0:2] + direction * 0.05).tolist()
    origin.insert(1, CAMHEI)
    target = (floorMeta[wallIndexNext][0:2] + direction * (0.05+TARDIS)).tolist()
    target.insert(1, CAMHEI)
    pcam = {}
    pcam["origin"] = origin
    pcam["target"] = target
    pcam["up"] = calCamUpVec(np.array(pcam["origin"]), np.array(pcam["target"])).tolist()
    return pcam

def renderGivenPcam(pcam, scenejson):
    scenejson["PerspectiveCamera"]['origin'] = pcam['origin']
    scenejson["PerspectiveCamera"]['target'] = pcam['target']
    scenejson["PerspectiveCamera"]['up'] = pcam['up']
    scenejson['canvas']['width']  = "600"
    scenejson['canvas']['height'] = "600"
    casename = pt.pathTracing(scenejson, 4)
    identifier = uuid.uuid1()
    if not os.path.exists(f"./latentspace/autoview/{scenejson['origin']}"):
        os.makedirs(f"./latentspace/autoview/{scenejson['origin']}")
    shutil.copy(casename + '/render.png', f"./latentspace/autoview/{scenejson['origin']}/{identifier}.png")
    pcam['identifier'] = str(identifier)
    with open(f"./latentspace/autoview/{scenejson['origin']}/{identifier}.json", 'w') as f:
        json.dump(pcam, f)

def autoViewRooms(scenejson):
    for room in scenejson['rooms']:
        # pcam = autoViewTwoPoint(room)
        # renderGivenPcam(pcam, test_file)
        # pcam = autoViewFromPatterns(room)
        # if pcam is not None:
        #     renderGivenPcam(pcam, test_file)
        # pcam = autoViewOnePoint(room)
        # renderGivenPcam(pcam, test_file)

        # auto-views w.r.t one-point perspective. 
        pcams = autoViewsRodrigues(room, test_file['PerspectiveCamera']['fov'])
        for pcam in pcams:
            renderGivenPcam(pcam, test_file)

if __name__ == "__main__":
    start_time = time.time()
    with open('./examples/a630400d-2cd7-459f-8a89-85ba949c8bfd-l6453-dl (1).json') as f:
        test_file = json.load(f)
    # pcam = autoViewTwoPoint(test_file['rooms'][4])
    # print(pcam)
    # renderGivenPcam(pcam, test_file)

    # pcams = autoViewsRodrigues(test_file['rooms'][4], test_file['PerspectiveCamera']['fov'])
    # for pcam in pcams:
    #     renderGivenPcam(pcam, test_file)
    
    autoViewRooms(test_file)
    print("\r\n --- %s secondes --- \r\n" % (time.time() - start_time))
