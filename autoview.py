from re import L
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

def preloadAABBs(scene):
    for room in scene['rooms']:
        for obj in room['objList']:
            if not sk.objectInDataset(obj['modelId']):
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

def keyObjectKeyFunction(obj):
    if obj is None:
        return -1
    if 'modelId' not in obj:
        return -1
    cat = getobjCat(obj['modelId'])
    if cat == "Unknown Category" or cat not in res_ratio_dom:
        return -1
    return res_ratio_dom[cat][obj['roomType']]

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
    pattern['translate'] = sk.transform_a_point(np.array(pattern['translate']), theDom['translate'], theDom['orient'], theDom['scale'])
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

def findTheFrontFarestCorner(probe, floorMeta, floorPoly, pd):
    MAXLEN = -1
    wallDiagIndex = -1
    for wallJndex in range(floorMeta.shape[0]):
        trobe = floorMeta[wallJndex][0:2]
        # check if the diagonal lies inside the edges of the polygon. 
        line = LineString((probe, trobe))
        if sk.isLineIntersectsWithEdges(line, floorMeta):
            continue
        # check if some point on the diagonal is inside the polygon. 
        mPoint = Point((probe + trobe) / 2)
        if not floorPoly.contains(mPoint):
            continue
        if np.dot(trobe - probe, pd) < 0:
            continue
        LEN = np.linalg.norm(probe - trobe, ord=2)
        if LEN > MAXLEN:
            MAXLEN = LEN
            wallDiagIndex = wallJndex
    return wallDiagIndex

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
        if sk.isLineIntersectsWithEdges(line, floorMeta):
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

def twoInfLineIntersection(p1, p2, p3, p4, isDebug=False):
    x1 = p1[0]
    y1 = p1[1]
    x2 = p2[0]
    y2 = p2[1]
    x3 = p3[0]
    y3 = p3[1]
    x4 = p4[0]
    y4 = p4[1]
    D = (x1-x2)*(y3-y4)-(y1-y2)*(x3-x4)
    if isDebug:
        print(D)
    if np.abs(D) < 0.0001:
        return None
    px= ( (x1*y2-y1*x2)*(x3-x4)-(x1-x2)*(x3*y4-y3*x4) ) / D
    py= ( (x1*y2-y1*x2)*(y3-y4)-(y1-y2)*(x3*y4-y3*x4) ) / D
    return [px, py]

def isPointOnVisualPlanes(t, probe, direction, theta, aspect=1.0, isDebug=False):
    """
    aspect: width / height. 
    """
    cosTheta = np.cos(theta)
    # cosPhi = np.cos( np.arctan(aspect / (1 / np.tan(theta))) )
    temp = 1 / np.tan(theta)
    cosPhi = temp / np.sqrt(aspect * aspect + temp * temp)
    probeTOt = t - probe
    # the normal of the VP vertical. 
    nVPv = np.cross(direction, np.array([0, 1, 0]))
    nVPv /= np.linalg.norm(nVPv, ord=2)
    # the normal of the VP horizontal. 
    nVPh = np.cross(direction, nVPv)
    nVPh /= np.linalg.norm(nVPh, ord=2)
    # the projected vector w.r.t vertical and horizontal VPs. 
    projVPv = -np.dot(nVPv, probeTOt) * nVPv + probeTOt
    projVPh = -np.dot(nVPh, probeTOt) * nVPh + probeTOt
    if isDebug:
        print('angles: ')
        print(np.dot(direction, projVPv) / np.linalg.norm(direction) / np.linalg.norm(projVPv))
        print(np.dot(direction, projVPh) / np.linalg.norm(direction) / np.linalg.norm(projVPh))
        print(np.arccos(np.dot(direction, projVPv) / np.linalg.norm(direction) / np.linalg.norm(projVPv)))
        print(np.arccos(np.dot(direction, projVPh) / np.linalg.norm(direction) / np.linalg.norm(projVPh)))
    if np.dot(direction, projVPv) / np.linalg.norm(direction) / np.linalg.norm(projVPv) < cosTheta:
        return False
    if np.dot(direction, projVPh) / np.linalg.norm(direction) / np.linalg.norm(projVPh) < cosPhi:
        return False
    return True

def isObjectInSight(obj, probe, direction, floorMeta, theta, objList, isDebug=False):
    if isDebug:
        print('Checking: ', obj['modelId'])
    if not sk.objectInDataset(obj['modelId']):
        return False
    t = np.array(obj['translate'])
    # project the 't' to the two visual planes (VP). 
    probeTOt = t - probe
    seenVertices = 0
    for vertex in obj['AABB']['eightPoints']:
        if isPointOnVisualPlanes(vertex, probe, direction, theta, 1.0, isDebug):
            seenVertices += 1
    # if all vertices are not seen. 
    if seenVertices == 0:
        return False
    """
    if np.dot(direction, probeTOt) <= 0:
        return False
    if np.dot(direction, probeTOt) / np.linalg.norm(direction) / np.linalg.norm(probeTOt) < cosAlpha:
        return False
    """
    line = LineString((probe[[0, 2]], t[[0, 2]]))
    if sk.isLineIntersectsWithEdges(line, floorMeta):
        return False           
    for o in objList:
        if 'AABB' not in o or o['id'] == obj['id']:
            continue
        
        # calculate the nearest point from center to 'probeTot'. 
        """
        magnitute = np.dot(o['AABB']['center'] - probe, probeTOt) / np.linalg.norm(probeTOt)
        nP = probe + magnitute * (probeTOt / np.linalg.norm(probeTOt))
        if len(sk.inside_test(nP.reshape(1, 3), o['AABB']['eightPoints'])) == 0:
            return False
        """
        probeToO = np.array(o['AABB']['center']) - probe
        probeToObj = obj['AABB']['eightPoints'] - probe
        distanceToObj = np.linalg.norm(probeToObj, ord=2, axis=1)
        magnitute = np.sum(probeToObj * probeToO, axis=1) / distanceToObj
        nPs = probe + magnitute.reshape(8, 1) * (probeToObj / distanceToObj.reshape(8, 1))
        if len(sk.inside_test(nPs, o['AABB']['eightPoints'])) == 0:
            return False
    return True

def isObjectOnWall(obj, p1, p2):
    p = np.array([obj['translate_frombb'][0], obj['translate_frombb'][2]])
    d = sk.pointToLineDistance(p, p1, p2)
    if d < 0.5 and sk.isPointBetweenLineSeg(p, p1, p2):
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

def probabilityOPP(h):
    # return h['numObjBeSeen'] + h['targetWallNumWindows']
    # return h['numObjBeSeen'] + h['targetWallWindoorArea'] + h['viewLength']
    return h['numObjBeSeen'] + h['targetWallWindoorArea']

def numSeenObjs(room, h, probe, direction, floorMeta, theta, isDebug=False):
    h['numObjBeSeen'] = 0
    h['objBeSeen'] = []
    for obj in room['objList']:
        if isObjectInSight(obj, probe, direction, floorMeta, theta, room['objList'], isDebug):
            h['numObjBeSeen'] += 1
            h['objBeSeen'].append(obj['modelId'])

def theLawOfTheThird(h, room, theta, aspect=1):
    """
    'theta' is half the fov that vertically spand from the top -> bottom. 
    """
    h['direction'] = h['direction'] / np.linalg.norm(h['direction'])
    # first we calculate the direction of four respective 'intersections of the third'. 
    lengthHeight = 2 * np.tan(theta)
    lengthWidth  = aspect * lengthHeight
    anchor = h['probe'] + h['direction']
    stepHeight = lengthHeight / 2 - lengthHeight / 3
    stepWidth = lengthWidth / 2 - lengthWidth / 3
    stepUp    = calCamUpVec(h['probe'], anchor)
    stepRight = np.cross(h['direction'], stepUp)
    stepUp /= np.linalg.norm(stepUp, ord=2)
    stepRight /= np.linalg.norm(stepRight)

    # the right-bottom:
    rb = anchor - stepHeight * stepUp + stepWidth * stepRight - h['probe']
    rb /= np.linalg.norm(rb)
    res = sk.rayCastsAABBs(h['probe'], rb, room['objList'])
    h['thirdObjList'] = [o['obj']['modelId'] for o in res]
    if len(res) == 0:
        h['thirdHasObj'] = False
        h['thirdFirstObj'] = '-1'
    else:
        h['thirdHasObj'] = True
        h['thirdFirstObj'] = res[0]['obj']['modelId']
        
def groundShifting(probe, floorMeta, floorPoly, direction, theta, H):
    p = np.array([probe[0], probe[2]])
    direction2D = np.array([direction[0], direction[2]])
    # find the wall corner with the longest diagonal in front of the probe point. 
    wallDiagIndex = findTheFrontFarestCorner(p, floorMeta, floorPoly, direction2D)
    # calculate the direction from the probe point to 'wallDiagIndex'. 
    wallDiagTop = np.array([floorMeta[wallDiagIndex][0], H, floorMeta[wallDiagIndex][1]])
    # calculate the projected vector on the vertical visual plane. 
    projectedP = sk.pointProjectedToPlane(wallDiagTop, np.cross(np.array([0, 1, 0]), direction), np.array([p[0], H/2, p[1]]))
    projectedVec = projectedP - probe
    # apply Rogrigues Formula. 
    return sk.rogrigues(projectedVec, np.cross(np.array([0, 1, 0]), -direction), -theta)

def toOriginAndTarget(bestView):
    """
    print(floorMeta[bestView['wallIndex']][0:2], floorMeta[(bestView['wallIndex']+1) % floorMeta.shape[0]][0:2])
    print(floorMeta[bestView['wallJndex']][0:2], floorMeta[(bestView['wallJndex']+1) % floorMeta.shape[0]][0:2])
    """
    origin = bestView['probe'].tolist()
    target = (bestView['probe'] + 0.5 * bestView['direction']).tolist()
    bestView["origin"] = origin
    bestView["target"] = target
    bestView["up"] = calCamUpVec(np.array(bestView["origin"]), np.array(bestView["target"])).tolist()
    return bestView

def autoViewOnePointPerspective(room, scene):
    """
    This function tries generate all potential views w.r.t the One-Point Perspective Rule (OPP Rule). 
    Note that several variants exist w.r.t different rules. 
    """
    theta = (np.pi * scene['PerspectiveCamera']['fov'] / 180) / 2
    floorMeta = p2d('.', '/dataset/room/{}/{}f.obj'.format(room['origin'], room['modelId']))
    floorPoly = Polygon(floorMeta[:, 0:2])
    H = sk.getWallHeight(f"./dataset/room/{room['origin']}/{room['modelId']}w.obj")
    MAXDIAMETER = sk.roomDiameter(floorMeta)
    # find the anchor point and the anchor wall. 
    hypotheses = []
    for wallIndex in range(floorMeta.shape[0]):
        # first get the meta from the target wall. 
        wallIndexNext = ( wallIndex + 1 ) % floorMeta.shape[0]
        middlePoint = (floorMeta[wallIndex][0:2] + floorMeta[wallIndexNext][0:2]) / 2
        normal = floorMeta[wallIndex][2:4]
        normal3D = np.array([normal[0], 0, normal[1]])
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
            # 'probe point' is the most important point which is eventually the camera position (origin). 
            p = np.array(p)
            probe = np.array([p[0], H/2, p[1]])
            
            # first generate the well-aligned hypothesis. 
            h = {}
            h['type'] = 'wellAligned'
            h['probe'] = probe
            h['direction'] = -normal3D
            h['viewLength'] = np.linalg.norm(middlePoint - p, ord=2)
            h['normal'] = normal.copy()
            h['wallIndex'] = wallIndex
            h['wallJndex'] = wallJndex
            numSeenObjs(room, h, probe, -normal3D, floorMeta, theta)
            h['targetWallArea'] = H * np.linalg.norm(floorMeta[wallIndex][0:2] - floorMeta[wallIndexNext][0:2], ord=2)
            h['targetWallNumWindows'] = targetWallNumWindows
            h['targetWallWindoorArea'] = targetWallWindoorArea
            theLawOfTheThird(h, room, theta, 1)
            # hypotheses.append(h)

            # then we try following the 'Three-Wall' rule. (Left Side) 
            thw = h.copy()
            thw['type'] = 'threeWall'
            # the prefix wall and the suffix wall
            pThW1 = twoInfLineIntersection(floorMeta[(wallIndex+floorMeta.shape[0]-1)%floorMeta.shape[0]][0:2], floorMeta[wallIndex][0:2], p3, p4)
            pThW2 = twoInfLineIntersection(floorMeta[wallIndexNext][0:2], floorMeta[(wallIndexNext+1)%floorMeta.shape[0]][0:2], p3, p4)
            if pThW1 is not None and pThW2 is not None:
                pThW1, pThW2 = np.array(pThW1), np.array(pThW2)
                thw['probe'] = pThW1 + (pThW2 - pThW1)/3
                thw['probe'] = np.array([thw['probe'][0], H/2, thw['probe'][1]])
                thw['direction'] = np.array([floorMeta[wallIndexNext][0], H/2, floorMeta[wallIndexNext][1]]) - thw['probe']
                thw['direction'] /= np.linalg.norm(thw['direction'])
                thw['direction'] = groundShifting(thw['probe'], floorMeta, floorPoly, thw['direction'], theta, H)
                thw['viewLength'] = np.linalg.norm(np.array([floorMeta[wallIndexNext][0], H/2, floorMeta[wallIndexNext][1]]) - thw['probe'], ord=2)
                numSeenObjs(room, thw, thw['probe'], thw['direction'], floorMeta, theta)
                theLawOfTheThird(thw, room, theta, 1)
                hypotheses.append(thw)

                # then we try following the 'Three-Wall' rule. (Right Side)
                thwR = thw.copy()
                thwR['probe'] = pThW2 + (pThW1 - pThW2)/3
                thw['type'] = 'threeWall_R'
                thwR['probe'] = np.array([thwR['probe'][0], H/2, thwR['probe'][1]])
                thwR['direction'] = np.array([floorMeta[wallIndex][0], H/2, floorMeta[wallIndex][1]]) - thwR['probe']
                thwR['direction'] /= np.linalg.norm(thwR['direction'])
                thwR['direction'] = groundShifting(thwR['probe'], floorMeta, floorPoly, thwR['direction'], theta, H)
                thwR['viewLength'] = np.linalg.norm(np.array([floorMeta[wallIndexNext][0], H/2, floorMeta[wallIndexNext][1]]) - thwR['probe'], ord=2)
                numSeenObjs(room, thwR, thwR['probe'], thwR['direction'], floorMeta, theta)
                theLawOfTheThird(thwR, room, theta, 1)
                hypotheses.append(thwR)

            # next we try generate the ground-shifted hypothesis. 
            hgs = h.copy()
            hgs['type'] = 'wellAlignedShifted'
            # find the wall corner with the longest diagonal in front of the probe point. 
            wallDiagIndex = findTheFrontFarestCorner(p, floorMeta, floorPoly, -normal)
            # calculate the direction from the probe point to 'wallDiagIndex'. 
            wallDiagTop = np.array([floorMeta[wallDiagIndex][0], H, floorMeta[wallDiagIndex][1]])
            # calculate the projected vector on the vertical visual plane. 
            projectedP = sk.pointProjectedToPlane(wallDiagTop, np.cross(np.array([0, 1, 0]), -normal3D), np.array([p[0], H/2, p[1]]))
            projectedVec = projectedP - probe
            # apply Rogrigues Formula. 
            direction = sk.rogrigues(projectedVec, np.cross(np.array([0, 1, 0]), normal3D), -theta)
            hgs['direction'] = direction
            numSeenObjs(room, hgs, probe, direction, floorMeta, theta)
            theLawOfTheThird(hgs, room, theta, 1)
            hypotheses.append(hgs)

    hypotheses.sort(key=probabilityOPP, reverse=True)
    exsitingProbes = []
    bestViews = {
        'wellAlignedShifted': None,
        'threeWall_R': None,
        'threeWall': None
    }
    for h in hypotheses:
        for viewTps in bestViews:
            if viewTps != h['type']:
                continue
            if bestViews[viewTps] is None:
                bestViews[viewTps] = toOriginAndTarget(h)
    return bestViews

def autoViewThird(room, scene):
    pass

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
        json.dump(pcam, f, default=sk.jsonDumpsDefault)

def autoViewRooms(scenejson):
    for room in scenejson['rooms']:
        # pcam = autoViewTwoPoint(room)
        # renderGivenPcam(pcam, test_file)
        # pcam = autoViewFromPatterns(room)
        # if pcam is not None:
        #     renderGivenPcam(pcam, test_file)
        # pcam = autoViewOnePoint(room)
        # renderGivenPcam(pcam, test_file)

        pcams = autoViewOnePointPerspective(room, scenejson)
        for tp in pcams:
            if pcams[tp] is None:
                continue
            renderGivenPcam(pcams[tp], test_file)

        # auto-views w.r.t one-point perspective. 
        # pcams = autoViewsRodrigues(room, test_file['PerspectiveCamera']['fov'])
        # for pcam in pcams:
        #     renderGivenPcam(pcam, test_file)

if __name__ == "__main__":
    start_time = time.time()
    # with open('./examples/a630400d-2cd7-459f-8a89-85ba949c8bfd-l6453-dl (1).json') as f:
    with open('./examples/autoviewtest1.json') as f:
        test_file = json.load(f)
    preloadAABBs(test_file)

    # pcam = autoViewOnePointPerspective(test_file['rooms'][4], test_file)
    # renderGivenPcam(pcam, test_file)

    # pcams = autoViewsOnePoint(test_file['rooms'][4], test_file['PerspectiveCamera']['fov'])
    # for pcam in pcams:
    #     renderGivenPcam(pcam, test_file)
    
    autoViewRooms(test_file)
    print("\r\n --- %s secondes --- \r\n" % (time.time() - start_time))
