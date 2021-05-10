import numpy as np
import json
import projection2d
from projection2d import processGeo as p2d, getobjCat
from shapely.geometry.polygon import Polygon, LineString, Point
from scipy.spatial.transform import Rotation as R
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

def preloadAABBs(scene):
    for room in scene['rooms']:
        for obj in room['objList']:
            if not os.path.exists(f'./dataset/object/{obj["modelId"]}'):
                continue
            AABB = sk.load_AABB(obj['modelId'])
            eightPoints = np.array([
                [AABB['max'][0], AABB['min'][1], AABB['max'][2]],
                [AABB['min'][0], AABB['min'][1], AABB['max'][2]],
                [AABB['min'][0], AABB['min'][1], AABB['min'][2]],
                [AABB['max'][0], AABB['min'][1], AABB['min'][2]],
                [AABB['max'][0], AABB['max'][1], AABB['max'][2]],
                [AABB['min'][0], AABB['max'][1], AABB['max'][2]],
                [AABB['min'][0], AABB['max'][1], AABB['min'][2]],
                [AABB['max'][0], AABB['max'][1], AABB['min'][2]],
            ])
            scale = np.array(obj['scale'])
            rX = R.from_euler('x', obj['rotate'][0], degrees=False).as_matrix()
            rY = R.from_euler('y', obj['rotate'][1], degrees=False).as_matrix()
            rZ = R.from_euler('z', obj['rotate'][2], degrees=False).as_matrix()
            rotate = rZ @ rY @ rX
            translate = np.array(obj['translate'])
            center = (np.array(AABB['max']) + np.array(AABB['min'])) / 2
            center = rotate @ (center * scale) + translate
            eightPoints = eightPoints * scale
            eightPoints = rotate @ eightPoints.T
            eightPoints = eightPoints.T + translate
            obj['AABB'] = {
                'eightPoints': eightPoints,
                'center': center
            }

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

def isLineIntersectsWithEdges(line, floorMeta):
    for i in range(floorMeta.shape[0]):
        l = LineString((floorMeta[i][0:2], floorMeta[(i+1)%floorMeta.shape[0]][0:2]))
        if line.crosses(l):
            return True
    return False

def pointToLineDistance(point, p1, p2):
    return np.linalg.norm(np.cross(p2-p1, p1-point)) / np.linalg.norm(p2-p1)

def findTheLongestDiagonal(wallIndex, floorMeta, floorPoly):
    probe = floorMeta[wallIndex][0:2]
    MAXLEN = -1
    wallDiagIndex = -1
    for wallJndex in range(floorMeta.shape[0]):
        # a diagonal can not be formed using adjacent vertices or 'wallIndex' itself.
        if wallJndex == wallIndex or wallJndex == ( wallIndex + 1 ) % floorMeta.shape[0] or wallIndex == ( wallJndex + 1 ) % floorMeta.shape[0]:
            continue
        trobe = floorMeta[wallJndex][0:2]
        # check if the diagonal lies inside the edges of the polygon. 
        line = LineString((probe, trobe))
        if isLineIntersectsWithEdges(line, floorMeta):
            continue
        # check if some point on the diagonal is inside the polygon. 
        mPoint = Point((probe + trobe) / 2)
        if not floorPoly.contains(mPoint):
            continue
        LEN = np.linalg.norm(probe - trobe, ord=2)
        if LEN > MAXLEN:
            MAXLEN = LEN
            wallDiagIndex = wallJndex
    return wallDiagIndex

def autoViewDiag(room):
    pass

def autoViewsOnePoint(room, fov):
    # change the fov/2 to Radian. 
    theta = (np.pi * fov / 180) / 2
    floorMeta = p2d('.', '/dataset/room/{}/{}f.obj'.format(room['origin'], room['modelId']))
    floorPoly = Polygon(floorMeta[:, 0:2])
    H = sk.getWallHeight(f"./dataset/room/{room['origin']}/{room['modelId']}w.obj")
    pcams = []
    for wallIndex in range(floorMeta.shape[0]):
        # find the longest diagonal w.r.t 'floorMeta[wallIndex][0:2]'. 
        wallDiagIndex = findTheLongestDiagonal(wallIndex, floorMeta, floorPoly)
        print(f' - the longest wallDiagIndex is {wallDiagIndex}.')
        # calculate the direction of the diagonal. 
        v = (floorMeta[wallDiagIndex][0:2] - floorMeta[wallIndex][0:2]).tolist()
        v.insert(1, 0.)
        v /= np.linalg.norm(np.array(v), ord=2)
        k = np.cross(v, np.array([0, 1, 0]))
        k /= np.linalg.norm(k, ord=2)
        # apply Rogrigues Formula. 
        target = v * np.cos(-theta) + np.cross(k, v) * np.sin(-theta)
        pcam = {}
        pcam["origin"] = floorMeta[wallIndex][0:2].tolist()
        pcam["origin"].insert(1, H)
        pcam["target"] = (np.array(pcam["origin"]) + target).tolist()
        pcam["origin"] = (np.array(pcam["origin"]) + target * 0.05).tolist()
        pcam["up"] = calCamUpVec(np.array(pcam["origin"]), np.array(pcam["target"])).tolist()
        pcams.append(pcam)
    return pcams

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

def twoInfLineIntersection(p1, p2, p3, p4):
    x1 = p1[0]
    y1 = p1[1]
    x2 = p2[0]
    y2 = p2[1]
    x3 = p3[0]
    y3 = p3[1]
    x4 = p4[0]
    y4 = p4[1]
    D = (x1-x2)*(y3-y4)-(y1-y2)*(x3-x4)
    if D < 0.05:
        return None
    px= ( (x1*y2-y1*x2)*(x3-x4)-(x1-x2)*(x3*y4-y3*x4) ) / D
    py= ( (x1*y2-y1*x2)*(y3-y4)-(y1-y2)*(x3*y4-y3*x4) ) / D
    return [px, py]

def isObjectInSight(obj, probe, direction, floorMeta):
    if not sk.objectInDataset(obj['modelId']):
        return False
    sinAlpha = np.sin(np.pi/4)
    t = np.array([obj['translate'][0], obj['translate'][2]])
    probeTOt = t - probe
    if np.dot(direction, probeTOt) < sinAlpha:
        return False
    line = LineString((probe, t))
    if isLineIntersectsWithEdges(line, floorMeta):
        return False           
    return True

def isPointBetweenLineSeg(point, p1, p2):
    s = np.dot(p2 - p1, point - p1) / np.linalg.norm(p2 - p1)
    if 0 < s and s < np.linalg.norm(p2 - p1):
        return True
    else:
        return False

def isObjectOnWall(obj, p1, p2):
    p = np.array([obj['translate_frombb'][0], obj['translate_frombb'][2]])
    d = pointToLineDistance(p, p1, p2)
    if d < 0.5 and isPointBetweenLineSeg(p, p1, p2):
        return True
    else:
        return False

def isWindowOnWall(obj, p1, p2):
    if 'coarseSemantic' not in obj:
        return False
    if obj['coarseSemantic'] not in ['window', 'Window']:
        return False
    x = (obj['bbox']['min'][0] + obj['bbox']['max'][0]) / 2
    z = (obj['bbox']['min'][2] + obj['bbox']['max'][2]) / 2
    obj['translate_frombb'] = [x, 0, z]
    return isObjectOnWall(obj, p1, p2) 

def calWindoorArea(obj, p1, p2):
    if 'coarseSemantic' not in obj:
        return 0
    if obj['coarseSemantic'] not in ['window', 'Window', 'door', 'Door']:
        return 0.
    if (obj['bbox']['max'][0] - obj['bbox']['min'][0]) * (obj['bbox']['max'][1] - obj['bbox']['min'][1]) * (obj['bbox']['max'][2] - obj['bbox']['min'][2]) == 0:
        return 0.
    x = (obj['bbox']['min'][0] + obj['bbox']['max'][0]) / 2
    z = (obj['bbox']['min'][2] + obj['bbox']['max'][2]) / 2
    obj['translate_frombb'] = [x, 0, z]
    # if the object is not on the wall, we ignore it. 
    if not isObjectOnWall(obj, p1, p2):
        return 0.
    y = obj['bbox']['max'][1] - obj['bbox']['min'][1]
    # discard the depth of the windoor. 
    if np.abs(np.dot(p1 - p2, np.array([0, 1]))) < np.abs(np.dot(p1 - p2, np.array([1, 0]))):
        l = obj['bbox']['max'][0] - obj['bbox']['min'][0]
    else:
        l = obj['bbox']['max'][2] - obj['bbox']['min'][2]
    return l * y

def wallArea(p1, p2, H):
    return H * np.linalg.norm(p1 - p2)

def probabilityOPP(h):
    # return h['numObjBeSeen'] + h['targetWallNumWindows']
    return h['targetWallWindoorArea']

def autoViewOnePointPerspective(room, scene):
    floorMeta = p2d('.', '/dataset/room/{}/{}f.obj'.format(room['origin'], room['modelId']))
    H = sk.getWallHeight(f"./dataset/room/{room['origin']}/{room['modelId']}w.obj")
    # find the anchor point and the anchor wall. 
    hypotheses = []
    for wallIndex in range(floorMeta.shape[0]):
        wallIndexNext = ( wallIndex + 1 ) % floorMeta.shape[0]
        middlePoint = (floorMeta[wallIndex][0:2] + floorMeta[wallIndexNext][0:2]) / 2
        # the normal of the probe wall. 
        normal = floorMeta[wallIndex][2:4]
        # construct the probe lineString. 
        p1 = middlePoint
        p2 = middlePoint + normal
        # detect wall decorations including windows.
        targetWallNumWindows = 0
        for r in scene['rooms']:
            for obj in r['objList']:
                if isWindowOnWall(obj, floorMeta[wallIndex][0:2], floorMeta[wallIndexNext][0:2]):
                    targetWallNumWindows += 1
        targetWallWindoorArea = 0.
        for r in scene['rooms']:
            for obj in r['objList']:
                targetWallWindoorArea += calWindoorArea(obj, floorMeta[wallIndex][0:2], floorMeta[wallIndexNext][0:2])
        for wallJndex in range(floorMeta.shape[0]):
            if wallJndex == wallIndex:
                continue
            p3 = floorMeta[wallJndex][0:2]
            p4 = floorMeta[(wallJndex+1)%floorMeta.shape[0]][0:2]
            p = twoInfLineIntersection(p1, p2, p3, p4)
            if p is None:
                continue
            h = {}
            p = np.array(p)
            h['probe'] = p
            h['viewLength'] = np.linalg.norm(middlePoint - p, ord=2)
            h['normal'] = normal.copy()
            h['wallIndex'] = wallIndex
            h['wallJndex'] = wallJndex
            # count the number of involved objects. 
            h['numObjBeSeen'] = 0
            for obj in room['objList']:
                if isObjectInSight(obj, p, -normal, floorMeta):
                    h['numObjBeSeen'] += 1
            h['targetWallArea'] = H * np.linalg.norm(floorMeta[wallIndex][0:2] - floorMeta[wallIndexNext][0:2], ord=2)
            h['targetWallNumWindows'] = targetWallNumWindows
            h['targetWallWindoorArea'] = targetWallWindoorArea
            hypotheses.append(h)
    bestView = max(hypotheses, key=probabilityOPP)
    """
    print(floorMeta[bestView['wallIndex']][0:2], floorMeta[(bestView['wallIndex']+1) % floorMeta.shape[0]][0:2])
    print(floorMeta[bestView['wallJndex']][0:2], floorMeta[(bestView['wallJndex']+1) % floorMeta.shape[0]][0:2])
    """
    origin = bestView['probe'].tolist()
    origin.insert(1, H/2)
    target = (bestView['probe'] - bestView['normal']).tolist()
    target.insert(1, H/2)
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

        pcam = autoViewOnePointPerspective(room, scenejson)
        renderGivenPcam(pcam, test_file)

        # auto-views w.r.t one-point perspective. 
        # pcams = autoViewsRodrigues(room, test_file['PerspectiveCamera']['fov'])
        # for pcam in pcams:
        #     renderGivenPcam(pcam, test_file)

if __name__ == "__main__":
    start_time = time.time()
    with open('./examples/a630400d-2cd7-459f-8a89-85ba949c8bfd-l6453-dl (1).json') as f:
        test_file = json.load(f)
    preloadAABBs(test_file)

    # pcam = autoViewOnePointPerspective(test_file['rooms'][4], test_file)
    # print(pcam)
    # renderGivenPcam(pcam, test_file)

    # pcams = autoViewsOnePoint(test_file['rooms'][4], test_file['PerspectiveCamera']['fov'])
    # for pcam in pcams:
    #     renderGivenPcam(pcam, test_file)
    
    # autoViewRooms(test_file)
    print("\r\n --- %s secondes --- \r\n" % (time.time() - start_time))
