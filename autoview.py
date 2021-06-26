from re import L
from flask import Blueprint, request, copy_current_request_context
from flask_socketio import emit
import flask
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

app_autoView = Blueprint('app_autoView', __name__)
pt.r_dir = 'AutoView'
projection2d.get_norm = True
TARDIS = 3.397448931651581
CAMHEI = 1.
pt.REMOVELAMP = False
ASPECT = 16 / 9
RENDERWIDTH = 600

def preloadAABBs(scene):
    for room in scene['rooms']:
        for obj in room['objList']:
            if sk.objectInDataset(obj['modelId']):
                AABB = sk.load_AABB(obj['modelId'])
            else:
                if 'coarseSemantic' in obj and obj['coarseSemantic'] in ['window', 'Window', 'door', 'Door']:
                    AABB = obj['bbox']
                else:
                    continue
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

def balancing(h, room, theta):
    """
    'h' is a generated probe view. 
    """
    h['direction'] /= np.linalg.norm(h['direction'])
    floorMeta = p2d('.', '/dataset/room/{}/{}f.obj'.format(room['origin'], room['modelId']))
    onePlanePointList = []
    for obj in room['objList']:
        if not isObjectInSight(obj, h['probe'], h['direction'], floorMeta, theta, room['objList'], False):
            continue
        probeTot = np.array(obj['translate']) - h['probe']
        cosToDirection = np.dot(probeTot, h['direction']) / np.linalg.norm(probeTot)
        DIS = 1 / cosToDirection
        DRC = probeTot / np.linalg.norm(probeTot)
        onePlanePointList.append(h['probe'] + DIS * DRC)
    centroid = sum(onePlanePointList) / len(onePlanePointList)
    newDirection = centroid - h['probe']
    newDirection /= np.linalg.norm(newDirection, ord=2)
    return newDirection

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

def longestDiagonalSimple(wallIndex, floorMeta, floorPoly):
    probe = floorMeta[wallIndex][0:2]
    MAXLEN = -1
    wallDiagIndex = -1
    for wallJndex in range(floorMeta.shape[0]):
        # a diagonal can not be formed using adjacent vertices or 'wallIndex' itself.
        if wallJndex == wallIndex or wallJndex == ( wallIndex + 1 ) % floorMeta.shape[0] or wallIndex == ( wallJndex + 1 ) % floorMeta.shape[0]:
            continue
        trobe = floorMeta[wallJndex][0:2]
        LEN = np.linalg.norm(probe - trobe, ord=2)
        if LEN > MAXLEN:
            MAXLEN = LEN
            wallDiagIndex = wallJndex
    return wallDiagIndex

def probabilityTPP(h):
    return h['numObjBeSeen'] + h['viewLength'] # + h['targetWallWindoorArea']

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

def autoViewTwoPointPerspective(room, scene):
    fov = scene['PerspectiveCamera']['fov']
    # change the fov/2 to Radian. 
    theta = (np.pi * fov / 180) / 2
    floorMeta = p2d('.', '/dataset/room/{}/{}f.obj'.format(room['origin'], room['modelId']))
    floorPoly = Polygon(floorMeta[:, 0:2])
    H = sk.getWallHeight(f"./dataset/room/{room['origin']}/{room['modelId']}w.obj")
    pcams = []
    for wallIndex in range(floorMeta.shape[0]):
        pcam = {}
        # find the longest diagonal w.r.t 'floorMeta[wallIndex][0:2]'. 
        wallDiagIndex = findTheLongestDiagonal(wallIndex, floorMeta, floorPoly)
        # wallDiagIndex = longestDiagonalSimple(wallIndex, floorMeta, floorPoly)
        targetWallWindoorArea = 0.
        for r in scene['rooms']:
            for obj in r['objList']:
                targetWallWindoorArea += calWindoorArea(obj, floorMeta[(wallDiagIndex+floorMeta.shape[0]-1)%floorMeta.shape[0]][0:2], floorMeta[wallDiagIndex][0:2])
        for r in scene['rooms']:
            for obj in r['objList']:
                targetWallWindoorArea += calWindoorArea(obj, floorMeta[wallDiagIndex][0:2], floorMeta[(wallDiagIndex+1)%floorMeta.shape[0]][0:2])
        # calculate the direction of the diagonal. 
        v = (floorMeta[wallDiagIndex][0:2] - floorMeta[wallIndex][0:2]).tolist()
        v.insert(1, 0.)
        v /= np.linalg.norm(np.array(v), ord=2)
        k = np.cross(v, np.array([0, 1, 0]))
        k /= np.linalg.norm(k, ord=2)
        # apply Rogrigues Formula. 
        direction = v * np.cos(-theta) + np.cross(k, v) * np.sin(-theta)
        direction /= np.linalg.norm(direction)
        probe = np.array([floorMeta[wallIndex][0], H, floorMeta[wallIndex][1]])
        numSeenObjs(room, pcam, probe, direction, floorMeta, theta)
        pcam['probe'] = probe + direction * 1
        pcam['direction'] = direction
        pcam['viewLength'] = np.linalg.norm(v, ord=2)
        pcam['targetWallWindoorArea'] = targetWallWindoorArea
        pcam['theta'] = theta
        pcam['roomId'] = room['roomId']
        pcams.append(pcam)
    pcams.sort(key=probabilityTPP, reverse=True)
    return toOriginAndTarget(pcams[0])

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

def isObjCovered(h, scene, aspect=ASPECT):
    """
    aspect: width / height. 
    """
    cosTheta = np.cos(h['theta'])
    # cosPhi = np.cos( np.arctan(aspect / (1 / np.tan(theta))) )
    temp = 1 / np.tan(h['theta'])
    cosPhi = temp / np.sqrt(aspect * aspect + temp * temp)
    # the normal of the VP vertical. 
    nVPv = np.cross(h['direction'], np.array([0, 1, 0]))
    nVPv /= np.linalg.norm(nVPv, ord=2)
    # the normal of the VP horizontal. 
    nVPh = np.cross(h['direction'], nVPv)
    nVPh /= np.linalg.norm(nVPh, ord=2)
    for room in scene['rooms']:
        for obj in room['objList']:
            if not sk.objectInDataset(obj['modelId']):
                continue
            if len(sk.inside_test(h['probe'].reshape(1, 3), obj['AABB']['eightPoints'])) == 0:
                h['coveredBy'] = obj['modelId']
                h['isObjCovered'] = True
                return True
            signpp = False
            signpn = False
            signnp = False
            signnn = False
            for vertex in obj['AABB']['eightPoints']:
                probeTOt = vertex - h['probe']
                # the projected vector w.r.t vertical and horizontal VPs. 
                projVPv = -np.dot(nVPv, probeTOt) * nVPv + probeTOt
                projVPh = -np.dot(nVPh, probeTOt) * nVPh + probeTOt
                ct = np.dot(h['direction'], projVPv) / np.linalg.norm(h['direction']) / np.linalg.norm(projVPv)
                cp = np.dot(h['direction'], projVPh) / np.linalg.norm(h['direction']) / np.linalg.norm(projVPh)
                one = np.dot(nVPv, probeTOt)
                two = np.dot(nVPh, probeTOt)
                if ct < cosTheta and cp < cosPhi:
                    if one > 0 and two > 0:
                        signpp = True
                    elif one > 0 and two < 0:
                        signpn = True
                    elif one < 0 and two > 0:
                        signnp = True
                    else:
                        signnn = True
            if signpp and signpn and signnp and signnn:
                h['coveredBy'] = obj['modelId']
                h['isObjCovered'] = True
                return True
    return False


def tarWindoorArea2021(h, scene, floorMeta, theta):
    totalWindoorArea = 0.0
    totalWindoorNum = 0
    totalWinNum = 0
    totalDoorNum = 0
    totalWinArea = 0.
    totalDoorArea = 0.
    for r in scene['rooms']:
        for obj in r['objList']:
            if 'coarseSemantic' not in obj:
                continue
            if obj['coarseSemantic'] not in ['window', 'Window', 'door', 'Door']:
                continue
            x = (obj['bbox']['min'][0] + obj['bbox']['max'][0]) / 2
            z = (obj['bbox']['min'][2] + obj['bbox']['max'][2]) / 2
            obj['translate_frombb'] = [x, 0, z]
            y = obj['bbox']['max'][1] - obj['bbox']['min'][1]
            if (obj['bbox']['max'][0] - obj['bbox']['min'][0]) * (obj['bbox']['max'][1] - obj['bbox']['min'][1]) * (obj['bbox']['max'][2] - obj['bbox']['min'][2]) == 0:
                continue
            if not isObjectInSight(obj, h['probe'], h['direction'], floorMeta, theta, r['objList']):
                continue
            # discard the depth of the windoor. 
            l = max(obj['bbox']['max'][0] - obj['bbox']['min'][0], obj['bbox']['max'][2] - obj['bbox']['min'][2])
            totalWindoorNum += 1
            totalWindoorArea += l * y
            if obj['coarseSemantic'] in ['door', 'Door']:
                totalDoorNum += 1
                totalDoorArea += l * y
            if obj['coarseSemantic'] in ['window', 'Window']:
                totalWinNum += 1
                totalWinArea += l * y
    h['totalWindoorArea'] = totalWindoorArea
    h['totalWindoorNum'] = totalWindoorNum
    h['totalWinNum'] = totalWinNum
    h['totalDoorNum'] = totalDoorNum
    h['totalWinArea'] = totalWinArea
    h['totalDoorArea'] = totalDoorArea

def autoViewsRodrigues(room, scene):
    # change the fov/2 to Radian. 
    theta = (np.pi * scene['PerspectiveCamera']['fov'] / 180) / 2
    # the the floor meta. 
    floorMeta = p2d('.', '/dataset/room/{}/{}f.obj'.format(room['origin'], room['modelId']))
    floorPoly = Polygon(floorMeta[:, 0:2])
    # the height of the wall. 
    H = sk.getWallHeight(f"./dataset/room/{room['origin']}/{room['modelId']}w.obj")
    pcams = []
    for wallIndex in range(floorMeta.shape[0]):
        pcam = {}
        wallIndexNext = ( wallIndex + 1 ) % floorMeta.shape[0]
        middlePoint = (floorMeta[wallIndex][0:2] + floorMeta[wallIndexNext][0:2]) / 2
        middlePoint += floorMeta[wallIndex][2:4] * 0.005
        origin = middlePoint.tolist()
        origin.insert(1, H/2)
        direction = floorMeta[wallIndex][2:4].tolist()
        direction.insert(1, 0.)
        origin = np.array(origin)
        direction = np.array(direction)

        pcam['theta'] = theta
        pcam['roomId'] = room['roomId']
        # pcam['viewLength'] = np.linalg.norm(middlePoint - p, ord=2)
        pcam['probe'] = origin
        pcam['wallIndex'] = wallIndex
        pcam['direction'] = groundShifting(origin, floorMeta, floorPoly, direction, theta, H)
        pcam['type'] = 'againstMidWall'
        tarWindoorArea2021(pcam, scene, floorMeta, theta)
        numSeenObjs(room, pcam, pcam['probe'], pcam['direction'], floorMeta, theta)

        # apply Rogrigues Formula. 
        # v = np.array(direction)
        # v /= np.linalg.norm(v, ord=2)
        # k = (floorMeta[wallIndex][0:2] - floorMeta[wallIndexNext][0:2]).tolist()
        # k.insert(1, 0.)
        # k = np.array(k)
        # k /= np.linalg.norm(k, ord=2)
        # target = v * np.cos(-theta) + np.cross(k, v) * np.sin(-theta)
        # construct the perspective camera. 
        # pcams.append(pcam)

        # next, we try generating a view w.r.t the current wall. 
        # v = np.array([0, -1, 0])
        # target = v * np.cos(theta) + np.cross(k, v) * np.sin(theta)
        # pcam = {}
        # pcam["origin"] = origin
        # pcam["target"] = (np.array(origin) + target).tolist()
        # pcam["up"] = calCamUpVec(np.array(pcam["origin"]), np.array(pcam["target"])).tolist()

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

def isPointOnVisualPlanes(t, probe, direction, theta, aspect=ASPECT, isDebug=False):
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
    
    if obj['coarseSemantic'] in ['window', 'Window', 'door', 'Door']:
        t = np.array(obj['translate_frombb'])
    else:
        if not sk.objectInDataset(obj['modelId']):
            return False
        t = np.array(obj['translate'])
    
    # project the 't' to the two visual planes (VP). 
    probeTOt = t - probe
    seenVertices = 0
    for vertex in obj['AABB']['eightPoints']:
        if isPointOnVisualPlanes(vertex, probe, direction, theta, ASPECT, isDebug):
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
    # return h['numObjBeSeen'] + h['targetWallWindoorArea']
    if h['isObjCovered']:
        return 0.
    if h['numObjBeSeen'] == 0:
        return 0.
    return h['numObjBeSeen'] + h['totalWindoorArea']

def numSeenObjs(room, h, probe, direction, floorMeta, theta, isDebug=False):
    h['numObjBeSeen'] = 0
    h['objBeSeen'] = []
    for obj in room['objList']:
        if isObjectInSight(obj, probe, direction, floorMeta, theta, room['objList'], isDebug):
            h['numObjBeSeen'] += 1
            h['objBeSeen'].append(obj['modelId'])

def theLawOfTheThird(h, room, theta, aspect=ASPECT):
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
    """
    H: the height of wall. NOT the half of the height. 
    """
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
    hypotheses += autoViewsRodrigues(room, scene)
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
            # generate the probe point. 
            p = twoInfLineIntersection(p1, p2, p3, p4)
            if p is None:
                continue
            # 'probe point' is the most important point which is eventually the camera position (origin). 
            p = np.array(p)
            probe = np.array([p[0], H/2, p[1]])
            
            # first generate the well-aligned hypothesis. 
            h = {}
            h['roomId'] = room['roomId']
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
            tarWindoorArea2021(h, scene, floorMeta, theta)
            h['theta'] = theta
            theLawOfTheThird(h, room, theta, ASPECT)
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
                theLawOfTheThird(thw, room, theta, ASPECT)
                tarWindoorArea2021(thw, scene, floorMeta, theta)
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
                theLawOfTheThird(thwR, room, theta, ASPECT)
                tarWindoorArea2021(thwR, scene, floorMeta, theta)
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
            theLawOfTheThird(hgs, room, theta, ASPECT)
            tarWindoorArea2021(hgs, scene, floorMeta, theta)
            hypotheses.append(hgs)
    for h in hypotheses:
        h['isObjCovered'] = isObjCovered(h, scene)
    hypotheses.sort(key=probabilityOPP, reverse=True)
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

def renderPcamAsync(scenejson,identifier):
    casename = pt.pathTracing(scenejson, 4, f"./latentspace/autoview/{scenejson['origin']}/{identifier}.png")

renderThreads = {}
def renderGivenPcam(pcam, scenejson):
    scenejson["PerspectiveCamera"] = scenejson["PerspectiveCamera"].copy()
    scenejson["PerspectiveCamera"]['origin'] = pcam['origin']
    scenejson["PerspectiveCamera"]['target'] = pcam['target']
    scenejson["PerspectiveCamera"]['up'] = pcam['up']
    scenejson["canvas"] = scenejson["canvas"].copy()
    scenejson['canvas']['width']  = int(RENDERWIDTH)
    scenejson['canvas']['height'] = int(RENDERWIDTH / ASPECT)
    identifier = uuid.uuid1()
    if not os.path.exists(f"./latentspace/autoview/{scenejson['origin']}"):
        os.makedirs(f"./latentspace/autoview/{scenejson['origin']}")
    pcam['identifier'] = str(identifier)
    pcam['scenejsonfile'] = scenejson['origin']
    with open(f"./latentspace/autoview/{scenejson['origin']}/{identifier}.json", 'w') as f:
        json.dump(pcam, f, default=sk.jsonDumpsDefault)
    thread = sk.BaseThread(
        name='autoView', 
        target=renderPcamAsync,
        method_args=(scenejson.copy(),identifier)
    )
    thread.start()
    # scenejson = json.loads( json.dumps(scenejson, default=sk.jsonDumpsDefault) )
    # thread = pt.pathTracingPara.delay(scenejson, 4, f"./latentspace/autoview/{scenejson['origin']}/{identifier}.png")
    # renderThreads[str(identifier)] = thread

def autoViewRooms(scenejson):
    pt.SAVECONFIG = False
    preloadAABBs(scenejson)
    fov = scenejson['PerspectiveCamera']['fov']
    # change the fov/2 to Radian. 
    theta = (np.pi * fov / 180) / 2
    for room in scenejson['rooms']:
        # we do not generating views in an empty room. 
        obj3DModelCount = 0
        for obj in room['objList']:
            try:
                if sk.objectInDataset(obj['modelId']):
                    obj3DModelCount += 1
            except:
                continue
        if obj3DModelCount == 0:
            continue

        # pcam = autoViewTwoPoint(room)
        # renderGivenPcam(pcam, test_file)
        # pcam = autoViewFromPatterns(room)
        # if pcam is not None:
        #     renderGivenPcam(pcam, test_file)
        # pcam = autoViewOnePoint(room)
        # renderGivenPcam(pcam, test_file)

        # pcam = autoViewTwoPointPerspective(room, scenejson)
        # renderGivenPcam(pcam, scenejson)

        # newDirection = balancing(pcam, test_file['rooms'][1], pcam['theta'])
        # print(pcam['direction'], newDirection)

        pcams = autoViewOnePointPerspective(room, scenejson)
        for tp in pcams:
            if pcams[tp] is None:
                continue
            # pcams[tp]['direction'] = balancing(pcams[tp], room, pcams[tp]['theta'])
            renderGivenPcam(pcams[tp], scenejson.copy())

        # auto-views w.r.t one-point perspective. 
        # pcams = autoViewsRodrigues(room, test_file['PerspectiveCamera']['fov'])
        # for pcam in pcams:
        #     renderGivenPcam(pcam, test_file)
    hamilton(scenejson)

def hamiltonNext(ndp, views, scene):
    DIS = np.Inf
    res = None
    for view in views:
        if not view['roomId'] == ndp['roomId'] or view['isVisited']:
            continue
        # if np.dot(np.array(view['direction']), np.array(ndp['direction'])) <= 0:
        #     continue
        dis = np.linalg.norm(np.array(view['probe']) - np.array(ndp['probe']), ord=2)
        if dis < DIS:
            DIS = dis
            res = view
    return res

def hamiltonNextRoom(roomId, pre, suc, scene):
    if roomId in suc:
        for res in suc[roomId]:
            if not scene['rooms'][res]['isVisited']:
                return res
    if roomId in pre:
        return pre[roomId]
    return -1


import networkx as nx
def hamilton(scene):
    involvedRoomIds = []
    views = []
    # load existing views. 
    for fn in os.listdir(f'./latentspace/autoview/{scene["origin"]}'):
        if '.json' not in fn:
            continue
        with open(f'./latentspace/autoview/{scene["origin"]}/{fn}') as f:
            views.append(json.load(f))
    for view in views:
        view['isVisited'] = False
        if view['roomId'] not in involvedRoomIds:
            involvedRoomIds.append(view['roomId'])
    res = []
    # deciding connections of a floorplan. 
    G = nx.Graph()
    for room in scene['rooms']:
        room['isVisited'] = False
        floorMeta = p2d('.', '/dataset/room/{}/{}f.obj'.format(room['origin'], room['modelId']))
        try:
            H = sk.getWallHeight(f"./dataset/room/{room['origin']}/{room['modelId']}w.obj")
        except:
            continue
        for door in room['objList']:
            if 'coarseSemantic' not in door:
                continue
            if door['coarseSemantic'] not in ['Door', 'door']:
                continue
            if len(door['roomIds']) < 2:
                continue
            if door['roomIds'][0] not in involvedRoomIds and door['roomIds'][1] not in involvedRoomIds:
                continue
            x = (door['bbox']['min'][0] + door['bbox']['max'][0]) / 2
            z = (door['bbox']['min'][2] + door['bbox']['max'][2]) / 2
            DIS = np.Inf
            for wallIndex in range(floorMeta.shape[0]):
                wallIndexNext = ( wallIndex + 1 ) % floorMeta.shape[0]
                dis = sk.pointToLineDistance(np.array([x, z]), floorMeta[wallIndex, 0:2], floorMeta[wallIndexNext, 0:2])
                if dis < DIS:
                    DIS = dis
                    direction = np.array([floorMeta[wallIndex, 2], 0, floorMeta[wallIndex, 3]])
            translate = np.array([x, H/2, z])
            G.add_edge(door['roomIds'][0], door['roomIds'][1], translate=translate, direction=direction, directionToRoom=room['roomId'])
    pre = nx.dfs_predecessors(G)
    suc = nx.dfs_successors(G)
    # decide the s and t which are the start point and end point respectively. 
    # ndproom = list(nx.dfs_successors(G).keys())[0]
    ndproom = views[0]['roomId']
    # ndpNext = None
    # for view in views:
    #     if view['roomId'] == ndproom:
    #         ndpNext = view
    for e in G.edges:
        if ndproom in e:
            edge = G[e[0]][e[1]]
            if ndproom != edge['directionToRoom']:
                edge['direction'] = -edge['direction']
            ndpNext = {
                'roomId': ndproom,
                'probe': edge['translate'],
                'origin': edge['translate'].tolist(),
                'target': (edge['translate'] + edge['direction']).tolist(),
                'direction': edge['direction'].tolist()
            }
    # perform the algorithm of Angluin and Valiant. 
    while not ndproom == -1:
        while ndpNext is not None:
            ndp = ndpNext
            res.append(ndp)
            ndp['isVisited'] = True
            ndpNext = hamiltonNext(ndp, views, scene)
        lastndproom = ndproom
        ndproom = hamiltonNextRoom(ndproom, pre, suc, scene)
        if ndproom == -1:
            break
        edge = G[lastndproom][ndproom]
        if edge['direction'].dot(edge['translate'] - ndp['probe']) < 0:
            edge['direction'] = -edge['direction']
        scene['rooms'][ndproom]['isVisited'] = True
        ndpNext = {
            'roomId': ndproom,
            'probe': edge['translate'],
            'origin': edge['translate'].tolist(),
            'target': (edge['translate'] + edge['direction']).tolist(),
            'direction': edge['direction'].tolist()
        }
    
    with open(f'./latentspace/autoview/{scene["origin"]}/path', 'w') as f:
        json.dump(res, f, default=sk.jsonDumpsDefault)
    return res

# for 3D-Front, it requires 269669 seconds. 
def floorplanOrthes():
    pt.cameraType = 'orthographic'
    pt.SAVECONFIG = False
    pt.REMOVELAMP = True
    floorplanlist = os.listdir('./dataset/alilevel_door2021/')
    # for floorplanfile in floorplanlist:
    for floorplanfile in ['e8b0a6bf-58a2-49de-b9ea-231995fc9e3b.json', '317d64ff-b96e-4743-88f6-2b5b27551a7c.json']:
        if '.json' not in floorplanfile:
            continue
        with open(f'./dataset/alilevel_door2021/{floorplanfile}') as f:
            scenejson = json.load(f)
        # if os.path.exists(f"./dataset/alilevel_door2021_orth/{scenejson['origin']}.png"):
        #     continue
        points = []
        for room in scenejson['rooms']:
            try:
                floorMeta = p2d('.', '/dataset/room/{}/{}f.obj'.format(room['origin'], room['modelId']))
                points += floorMeta[:, 0:2].tolist()
                wallMeta = sk.getMeshVertices('/dataset/room/{}/{}w.obj'.format(room['origin'], room['modelId']))
                points += wallMeta[:, [0, 2]].tolist()
            except:
                continue
        v = np.array(points)
        l = np.min(v[:, 0])
        r = np.max(v[:, 0])
        u = np.min(v[:, 1])
        d = np.max(v[:, 1])
        # orthViewLen = max((r - l), (d - u)) + 0.45
        orthViewLen = (r - l) + 0.45
        scenejson["PerspectiveCamera"] = {}
        scenejson["PerspectiveCamera"]['origin'] = [(r + l)/2, 50, (d + u)/2]
        scenejson["PerspectiveCamera"]['target'] = [(r + l)/2, 0,  (d + u)/2]
        scenejson["PerspectiveCamera"]['up'] = [0, 0, 1]
        scenejson["OrthCamera"] = {}
        scenejson["OrthCamera"]['x'] = orthViewLen / 2
        scenejson["OrthCamera"]['y'] = orthViewLen / 2
        scenejson["canvas"] = {}
        scenejson['canvas']['width']  = int((r - l) * 100)
        scenejson['canvas']['height'] = int((d - u) * 100)
        print(f'Rendering {floorplanfile} ...')
        try:
            pt.pathTracing(scenejson, 64, f"./dataset/alilevel_door2021_orth/{scenejson['origin']}.png")
        except Exception as e:
            print(e)
            continue
    # swap the cameraType back to perspective cameras. 
    pt.cameraType = 'perspective'

if __name__ == "__main__":
    start_time = time.time()
    # with open('./examples/4cc6dba0-a26e-42cb-a964-06cb78d60bae.json') as f:
    with open('./examples/a630400d-2cd7-459f-8a89-85ba949c8bfd-l6176-dl.json') as f:
    # with open('./examples/ceea988a-1df7-418e-8fef-8e0889f07135-l7767-dl.json') as f:
    # with open('./examples/cb2146ba-8f9e-4a68-bee7-50378200bade-l7607-dl (1).json') as f:
        test_file = json.load(f)
    preloadAABBs(test_file)

    # pcam = autoViewOnePointPerspective(test_file['rooms'][4], test_file)
    # renderGivenPcam(pcam, test_file)

    # pcam = autoViewTwoPointPerspective(test_file['rooms'][1], test_file)
    # newDirection = balancing(pcam, test_file['rooms'][1], pcam['theta'])
    # print(pcam['direction'], newDirection)
    # pcam['direction'] = newDirection
    # pcam = toOriginAndTarget(pcam)
    # renderGivenPcam(pcam, test_file)
    
    autoViewRooms(test_file)

    # hamilton(test_file)

    # floorplanOrthes()

    print("\r\n --- %s seconds --- \r\n" % (time.time() - start_time))

@app_autoView.route("/autoviewByID")
def autoviewByID():
    ret = []
    origin = flask.request.args.get('origin', default = "", type = str)
    if not os.path.exists(f'./latentspace/autoview/{origin}'):
        return []
    filenames = os.listdir(f'./latentspace/autoview/{origin}')
    for filename in filenames:
        if '.json' not in filename:
            continue
        with open(f'./latentspace/autoview/{origin}/{filename}') as f:
            pcam = json.load(f)
        pcam['img'] = pcam['identifier'] + '.png'
        ret.append(pcam)
    return json.dumps(ret)

@app_autoView.route("/autoviewimgs/<origin>/<identifier>")
def autoviewimgs(origin, identifier):
    # if identifier in renderThreads:
    #     if not renderThreads[identifier].ready():
    #         casename = renderThreads[identifier].get()
    return flask.send_from_directory(f'./latentspace/autoview/{origin}', identifier + '.png')

@app_autoView.route("/autoViewPath")
def autoViewPath():
    origin = flask.request.args.get('origin', default = "", type = str)
    with open(f'./latentspace/autoview/{origin}/path') as f:
        res = json.load(f)
    return json.dumps(res)

def autoViewsRes(origin):
    ret = []
    filenames = os.listdir(f'./latentspace/autoview/{origin}')
    for filename in filenames:
        if '.json' not in filename:
            continue
        with open(f'./latentspace/autoview/{origin}/{filename}') as f:
            pcam = json.load(f)
        pcam['img'] = pcam['identifier'] + '.png'
        ret.append(pcam)
    return ret
