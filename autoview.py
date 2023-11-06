from re import L
from flask import Blueprint
import flask
import numpy as np
import json
from layoutmethods import projection2d
from layoutmethods.projection2d import processGeo as p2d, getobjCat
from shapely.geometry.polygon import Polygon, LineString, Point
import pathTracing as pt
import sk
import time
import os
import networkx as nx
from sceneviewer.constraints import theLawOfTheThird,layoutConstraint,numSeenObjs,isObjCovered,isProbeOutside
from sceneviewer.constraints import tarWindoorArea2021,wallNormalOffset,isObjHalfCovered,secondNearestWallDis
from sceneviewer.utils import findTheFrontFarestCorner,isObjectInSight
from sceneviewer.utils import isWindowOnWall,calWindoorArea,expandWallSeg,redundancyRemove
from sceneviewer.utils import twoInfLineIntersection,toOriginAndTarget,hamiltonSmooth
from sceneviewer.inset import showPcamInset,showPcamPoints,insetBatch
import shutil
import random
from yltmp.OSRhandler import mainSearch, searchMainModelId, searchId

with open('./dataset/occurrenceCount/autoview_ratio.json') as f:
    res_ratio_dom = json.load(f)

app_autoView = Blueprint('app_autoView', __name__)
pt.r_dir = 'AutoView'
projection2d.get_norm = True
TARDIS = 3.397448931651581
CAMHEI = 1.
pt.REMOVELAMP = False
from sk import ASPECT,DEFAULT_FOV
RENDERWIDTH = 600
SAMPLE_COUNT = 4

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

def keyObjectKeyFunction(obj):
    if obj is None:
        return -1
    if 'modelId' not in obj:
        return -1
    cat = getobjCat(obj['modelId'])
    if cat == "Unknown Category" or cat not in res_ratio_dom:
        return -1
    return res_ratio_dom[cat][obj['roomType']]

def balancing(h, room, theta):
    """
    'h' is a generated probe view. 
    """
    h['direction'] /= np.linalg.norm(h['direction'])
    floorMeta = room['floorMeta'] # p2d('.', '/dataset/room/{}/{}f.obj'.format(room['origin'], room['modelId']))
    onePlanePointList = []
    for obj in room['objList']:
        if not isObjectInSight(obj, h['probe'], h['direction'], floorMeta, theta, room['objList'], False):
            continue
        probeTot = np.array(obj['translate']) - h['probe']
        cosToDirection = np.dot(probeTot, h['direction']) / np.linalg.norm(probeTot)
        DIS = 1 / cosToDirection
        DRC = probeTot / np.linalg.norm(probeTot)
        onePlanePointList.append(h['probe'] + DIS * DRC)
    if len(onePlanePointList) == 0:
        return h['direction']
    centroid = sum(onePlanePointList) / len(onePlanePointList)
    newDirection = centroid - h['probe']
    newDirection /= np.linalg.norm(newDirection, ord=2)
    h['direction'] = newDirection
    toOriginAndTarget(h)
    return newDirection

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

def checkPtoN(pl, nl, floorMeta):
    PtoN = LineString([pl, nl])
    for i in range(floorMeta.shape[0]):
        if PtoN.crosses(LineString([floorMeta[i][0:2], floorMeta[(i+1) % floorMeta.shape[0]][0:2]])):
            return False
    return True
        
def autoViewTwoWallPerspective(room, scene):
    fov = scene['PerspectiveCamera']['fov']
    # change the fov/2 to Radian. 
    theta = (np.pi * fov / 180) / 2
    focal = 1 / np.tan(theta)
    tanPhi = ASPECT / focal
    floorMeta = room['floorMeta'] # p2d('.', '/dataset/room/{}/{}f.obj'.format(room['origin'], room['modelId']))
    floorPoly = Polygon(floorMeta[:, 0:2])
    H = 1.2 # room['wallHeight'] # sk.getWallHeight(f"./dataset/room/{room['origin']}/{room['modelId']}w.obj")
    pcams = []
    for wallDiagIndex in range(floorMeta.shape[0]):
        pcam = {}
        iPre = (wallDiagIndex+floorMeta.shape[0]-1) % floorMeta.shape[0]
        iNxt = (wallDiagIndex + 1) % floorMeta.shape[0]
        iPreP = floorMeta[iPre][0:2]
        iNxtP = floorMeta[iNxt][0:2]
        # extend two walls as far as possible: 
        preList = []
        nxtList = []
        for i in range(floorMeta.shape[0]):
            if i == iPre or i == wallDiagIndex:
                continue
            p3 = floorMeta[i][0:2]
            p4 = floorMeta[(i+1) % floorMeta.shape[0]][0:2]
            _p = twoInfLineIntersection(floorMeta[wallDiagIndex][0:2], iPreP, p3, p4)
            if _p is None:
                continue
            _p = np.array(_p)
            if np.dot(_p - floorMeta[wallDiagIndex][0:2], floorMeta[wallDiagIndex][2:4]) < 0:
                continue
            preList.append(_p)
        for i in range(floorMeta.shape[0]):
            if i == iPre or i == wallDiagIndex:
                continue
            p3 = floorMeta[i][0:2]
            p4 = floorMeta[(i+1) % floorMeta.shape[0]][0:2]
            _p = twoInfLineIntersection(floorMeta[wallDiagIndex][0:2], iNxtP, p3, p4)
            if _p is None:
                continue
            _p = np.array(_p)
            if np.dot(_p - floorMeta[wallDiagIndex][0:2], floorMeta[iPre][2:4]) < 0:
                continue
            nxtList.append(_p)
        MAXdis = -1
        for pl in preList:
            for nl in nxtList:
                if checkPtoN(pl, nl, floorMeta):
                    dis = np.linalg.norm(pl - nl)
                    if MAXdis < dis:
                        MAXdis = dis
                        iPreP = pl
                        iNxtP = nl
        direction = iNxtP - iPreP
        direction = direction[[1,0]]
        direction[1] = -direction[1]
        direction /= np.linalg.norm(direction, ord=2)
        probe = (iNxtP + iPreP) / 2
        if np.dot(direction, floorMeta[wallDiagIndex][0:2] - probe) < 0:
            direction = -direction
        dis = np.linalg.norm(probe - iNxtP, ord=2) / tanPhi
        probe = probe - direction * dis
        pcam['viewLength'] = np.linalg.norm(probe - floorMeta[wallDiagIndex][0:2], ord=2)
        if not floorPoly.contains(Point(probe[0], probe[1])):
            p1 = probe
            p2 = probe + direction * dis
            _plist = []
            for i in range(floorMeta.shape[0]):
                p3 = floorMeta[i][0:2]
                p4 = floorMeta[(i+1) % floorMeta.shape[0]][0:2]
                _p = twoInfLineIntersection(p1, p2, p3, p4)
                if _p is None:
                    continue
                if np.dot(direction, np.array(_p) - p2) > 0:
                    continue
                _plist.append(_p)
            if len(_plist) > 0:
                _i = np.argmin(np.linalg.norm(np.array(_plist), axis=1))
                probe = _plist[_i]
        else:
            probe = probe.tolist()
        if not floorPoly.contains(Point(probe[0], probe[1])):
            continue
        probe.insert(1, H/2)
        probe = np.array(probe)
        direction = direction.tolist()
        direction.insert(1, 0)
        # direction = groundShifting(probe, floorMeta, floorPoly, np.array(direction), theta, H)
        pcam['probe'] = probe
        pcam['direction'] = direction
        pcam['theta'] = theta
        pcam['roomId'] = room['roomId']
        pcam['wallDiagIndex'] = wallDiagIndex
        pcam['type'] = 'twoWallPerspective'
        pcam['floorMeta'] = floorMeta
        pcam['semiRectLength'] = np.linalg.norm(floorMeta[wallDiagIndex][0:2] - iNxtP)
        pcam['semiRectWidth'] = np.linalg.norm(floorMeta[wallDiagIndex][0:2] - iPreP)
        pcam['semiRectArea'] = pcam['semiRectLength'] * pcam['semiRectWidth']
        pcam['semiRectRatio'] = pcam['semiRectArea'] / np.square((pcam['semiRectLength'] + pcam['semiRectWidth']) / 2)
        calculateRectRatio(pcam)
        pcams.append(pcam)
    return pcams

def autoViewsRodrigues(room, scene):
    # change the fov/2 to Radian. 
    theta = (np.pi * scene['PerspectiveCamera']['fov'] / 180) / 2
    # the the floor meta. 
    floorMeta = room['floorMeta'] # p2d('.', '/dataset/room/{}/{}f.obj'.format(room['origin'], room['modelId']))
    floorPoly = Polygon(floorMeta[:, 0:2])
    # the height of the wall. 
    H = room['wallHeight'] # sk.getWallHeight(f"./dataset/room/{room['origin']}/{room['modelId']}w.obj")
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
        pcam['direction'] = np.array([room['roomNorm'][wallIndex][0], 0, room['roomNorm'][wallIndex][1]]) # groundShifting(origin, floorMeta, floorPoly, direction, theta, H)
        pcam['type'] = 'againstMidWall'
        pcams.append(pcam)

    return pcams

def probabilityOPP(h):
    # return h['numObjBeSeen'] + h['targetWallNumWindows']
    # return h['numObjBeSeen'] + h['targetWallWindoorArea'] + h['viewLength']
    # return h['numObjBeSeen'] + h['targetWallWindoorArea']
    res = 0.
    if h['numObjBeSeen'] == 0:
        return res
    if h['isProbeOutside']:
        return res
    if h['wallNormalOffset'] < -0.20:
        return res
    if h['isObjCovered']:
        res -= 1
    if h['type'] in ['wellAlignedShifted', 'againstMidWall', 'was_thin']:
        res += 1
    res += h['numObjBeSeen'] * 1. + h['totalWindoorArea'] * 0.6 + h['layoutDirection'] * 3
    res += int(h['thirdHasObj_rb']) + int(h['thirdHasObj_lb']) + int(h['thirdHasObj_mid'])
    res += h['wallNormalOffset'] * 10
    return res

def probabilityOPP2(h):
    res = 0.
    if h['isObjCovered']:
        return res
    if h['numObjBeSeen'] == 0:
        return res
    if h['wallNormalOffset'] < -0.20:
        return res
    res += h['numObjBeSeen'] * 1. + h['layoutDirection'] * 4
    res += (int(h['thirdHasObj_rb']) + int(h['thirdHasObj_lb']) + int(h['thirdHasObj_mid'])) * 2
    return res

def probabilityOnlyObj(h):
    h['finalScore'] = h['numObjBeSeen'] * 10 + h['semiRectRatio2'] * 5 + np.sqrt(h['semiRectArea'])
    if h['type'] in ['againstMidWall', 'was_thin', 'wellAlignedShifted']:
        h['finalScore'] += 1
    return h['finalScore']

def groundShifting(probe, floorMeta, floorPoly, direction, theta, H, isDebug=False):
    """
    H: the height of wall. NOT the half of the height. 
    """
    p = np.array([probe[0], probe[2]])
    direction2D = np.array([direction[0], direction[2]])
    # find the wall corner with the longest diagonal in front of the probe point. 
    wallDiagIndex = findTheFrontFarestCorner(p, floorMeta, floorPoly, direction2D)
    if isDebug:
        print(floorMeta[wallDiagIndex])
    # calculate the direction from the probe point to 'wallDiagIndex'. 
    wallDiagTop = np.array([floorMeta[wallDiagIndex][0], H, floorMeta[wallDiagIndex][1]])
    # calculate the projected vector on the vertical visual plane. 
    projectedP = sk.pointProjectedToPlane(wallDiagTop, np.cross(np.array([0, 1, 0]), direction), np.array([p[0], H/2, p[1]]))
    projectedVec = projectedP - probe
    # apply Rogrigues Formula. 
    return sk.rogrigues(projectedVec, np.cross(np.array([0, 1, 0]), -direction), -theta)

def calculateRectRatio(h):
    if h['semiRectWidth'] > h['semiRectLength']:
        h['semiRectRatio2'] = h['semiRectLength'] / h['semiRectWidth']
    else:
        h['semiRectRatio2'] = h['semiRectWidth'] / h['semiRectLength']
    return h['semiRectRatio2']

def autoViewOnePointPerspective(room, scene, scoreFunc=probabilityOPP):
    """
    This function tries generate all potential views w.r.t the One-Point Perspective Rule (OPP Rule). 
    Note that several variants exist w.r.t different rules. 
    """
    theta = (np.pi * scene['PerspectiveCamera']['fov'] / 180) / 2
    if 'roomShape' in room:
        floorMeta = np.hstack((np.array(room['roomShape']), np.array(room['roomNorm'])))
    else:
        floorMeta = p2d('.', '/dataset/room/{}/{}f.obj'.format(room['origin'], room['modelId']))
    floorPoly = Polygon(floorMeta[:, 0:2])
    try:
        room['wallHeight'] = sk.getWallHeight(f"./dataset/room/{room['origin']}/{room['modelId']}w.obj")
    except:
        room['wallHeight'] = 2.8
    H = 1.2 # room['wallHeight']
    room['floorMeta'] = floorMeta
    # MAXDIAMETER = sk.roomDiameter(floorMeta)
    # find the anchor point and the anchor wall. 
    hypotheses = []
    # hypotheses += autoViewsRodrigues(room, scene)
    hypotheses += autoViewTwoWallPerspective(room, scene)
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
            if np.dot(floorMeta[wallIndex][2:4], floorMeta[wallJndex][2:4]) >= 0:
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
            h['floorMeta'] = floorMeta
            numSeenObjs(room, h, probe, -normal3D, floorMeta, theta)
            h['targetWallArea'] = H * np.linalg.norm(floorMeta[wallIndex][0:2] - floorMeta[wallIndexNext][0:2], ord=2)
            h['targetWallNumWindows'] = targetWallNumWindows
            h['targetWallWindoorArea'] = targetWallWindoorArea
            # tarWindoorArea2021(h, scene, floorMeta, theta)
            h['theta'] = theta
            h['semiRectLength'] = np.linalg.norm(floorMeta[wallIndex][0:2] - floorMeta[wallIndexNext][0:2])
            h['semiRectWidth'] = np.linalg.norm(p - p1)
            h['semiRectArea'] = h['semiRectLength'] * h['semiRectWidth']
            h['semiRectRatio'] = h['semiRectArea'] / np.square((h['semiRectLength'] + h['semiRectWidth']) / 2)
            calculateRectRatio(h)

            midh = h.copy()
            midh['probe'] = np.array([p1[0], H/2, p1[1]])
            midh['wallIndex'] = wallIndex
            midh['direction'] = normal3D # groundShifting(origin, floorMeta, floorPoly, direction, theta, H)
            midh['type'] = 'againstMidWall'
            hypotheses.append(midh)

            # then we try following the 'Three-Wall' rule. (Left Side) 
            expandPre, expandNxt = expandWallSeg(wallIndex, floorMeta)
            pThW1 = None
            pThW2 = None
            if expandPre is not None and expandNxt is not None:
                pThW1 = twoInfLineIntersection(expandPre, expandPre + floorMeta[wallIndex][2:4], p3, p4)
                pThW2 = twoInfLineIntersection(expandNxt, expandNxt + floorMeta[wallIndex][2:4], p3, p4)
            if pThW1 is not None and pThW2 is not None:
                pThW1, pThW2 = np.array(pThW1), np.array(pThW2)
                thw = h.copy()
                thw['type'] = 'threeWall'
                thw['pThW1'] = pThW1
                thw['pThW2'] = pThW2
                thw['probe'] = pThW1 + (pThW2 - pThW1)/3
                thw['probe'] = np.array([thw['probe'][0], H/2, thw['probe'][1]])
                # thw['direction'] = np.array([floorMeta[wallIndexNext][0], H/2, floorMeta[wallIndexNext][1]]) - thw['probe']
                # acr = floorMeta[wallIndexNext][0:2] + (floorMeta[wallIndex][0:2] - floorMeta[wallIndexNext][0:2])/3
                acr = expandNxt + (expandPre - expandNxt)/3
                thw['direction'] = np.array([acr[0], H/2, acr[1]]) - thw['probe']
                thw['direction'] /= np.linalg.norm(thw['direction'])
                # thw['direction'] = groundShifting(thw['probe'], floorMeta, floorPoly, thw['direction'], theta, H)
                thw['viewLength'] = np.linalg.norm(np.array([floorMeta[wallIndexNext][0], H/2, floorMeta[wallIndexNext][1]]) - thw['probe'], ord=2)
                hypotheses.append(thw)

                # then we try following the 'Three-Wall' rule. (Right Side)
                thwR = thw.copy()
                thwR['probe'] = pThW2 + (pThW1 - pThW2)/3
                thwR['type'] = 'threeWall_R'
                thwR['probe'] = np.array([thwR['probe'][0], H/2, thwR['probe'][1]])
                # thwR['direction'] = np.array([floorMeta[wallIndex][0], H/2, floorMeta[wallIndex][1]]) - thwR['probe']
                # acr = floorMeta[wallIndex][0:2] + (floorMeta[wallIndexNext][0:2] - floorMeta[wallIndex][0:2])/3
                acr = expandPre + (expandNxt - expandPre)/3
                thwR['direction'] = np.array([acr[0], H/2, acr[1]]) - thwR['probe']
                thwR['direction'] /= np.linalg.norm(thwR['direction'])
                # thwR['direction'] = groundShifting(thwR['probe'], floorMeta, floorPoly, thwR['direction'], theta, H)
                thwR['viewLength'] = np.linalg.norm(np.array([floorMeta[wallIndexNext][0], H/2, floorMeta[wallIndexNext][1]]) - thwR['probe'], ord=2)
                hypotheses.append(thwR)

                # then we try following the 'Three-Wall' rule. (Right Side)
                mtm = thw.copy()
                mtm['probe'] = (pThW1 + pThW2) / 2
                mtm['type'] = 'wellAlignedShifted'
                mtm['probe'] = np.array([mtm['probe'][0], H/2, mtm['probe'][1]])
                # thwR['direction'] = np.array([floorMeta[wallIndex][0], H/2, floorMeta[wallIndex][1]]) - thwR['probe']
                # acr = floorMeta[wallIndex][0:2] + (floorMeta[wallIndexNext][0:2] - floorMeta[wallIndex][0:2])/3
                acr = (expandNxt + expandPre) / 2
                mtm['direction'] = np.array([acr[0], H/2, acr[1]]) - mtm['probe']
                mtm['direction'] /= np.linalg.norm(mtm['direction'])
                # mtm['direction'] = groundShifting(mtm['probe'], floorMeta, floorPoly, mtm['direction'], theta, H)
                mtm['viewLength'] = np.linalg.norm(np.array([floorMeta[wallIndexNext][0], H/2, floorMeta[wallIndexNext][1]]) - mtm['probe'], ord=2)
                hypotheses.append(mtm)
            # the prefix wall and the suffix wall
            pThW1 = twoInfLineIntersection(floorMeta[(wallIndex+floorMeta.shape[0]-1)%floorMeta.shape[0]][0:2], floorMeta[wallIndex][0:2], p3, p4)
            pThW2 = twoInfLineIntersection(floorMeta[wallIndexNext][0:2], floorMeta[(wallIndexNext+1)%floorMeta.shape[0]][0:2], p3, p4)
            if pThW1 is not None and pThW2 is not None:
                pThW1, pThW2 = np.array(pThW1), np.array(pThW2)
                thinL = h.copy()
                thinL['type'] = 'threeWall_thin'
                thinL['pThW1'] = pThW1
                thinL['pThW2'] = pThW2
                thinL['probe'] = pThW1 + (pThW2 - pThW1)/3
                thinL['probe'] = np.array([thinL['probe'][0], H/2, thinL['probe'][1]])
                acr = floorMeta[wallIndexNext][0:2] + (floorMeta[wallIndex][0:2] - floorMeta[wallIndexNext][0:2])/3
                thinL['direction'] = np.array([acr[0], H/2, acr[1]]) - thinL['probe']
                thinL['direction'] /= np.linalg.norm(thinL['direction'])
                # thinL['direction'] = groundShifting(thinL['probe'], floorMeta, floorPoly, thinL['direction'], theta, H)
                thinL['viewLength'] = np.linalg.norm(np.array([floorMeta[wallIndexNext][0], H/2, floorMeta[wallIndexNext][1]]) - thinL['probe'], ord=2)
                hypotheses.append(thinL)

                thinR = thw.copy()
                thinR['probe'] = pThW2 + (pThW1 - pThW2)/3
                thinR['type'] = 'threeWall_R_thin'
                thinR['probe'] = np.array([thinR['probe'][0], H/2, thinR['probe'][1]])
                acr = floorMeta[wallIndex][0:2] + (floorMeta[wallIndexNext][0:2] - floorMeta[wallIndex][0:2])/3
                thinR['direction'] = np.array([acr[0], H/2, acr[1]]) - thinR['probe']
                thinR['direction'] /= np.linalg.norm(thinR['direction'])
                # thinR['direction'] = groundShifting(thinR['probe'], floorMeta, floorPoly, thinR['direction'], theta, H)
                thinR['viewLength'] = np.linalg.norm(np.array([floorMeta[wallIndexNext][0], H/2, floorMeta[wallIndexNext][1]]) - thinR['probe'], ord=2)

                wasThin = thw.copy()
                wasThin['probe'] = (pThW1 + pThW2) / 2
                wasThin['type'] = 'was_thin'
                wasThin['probe'] = np.array([wasThin['probe'][0], H/2, wasThin['probe'][1]])
                acr = (floorMeta[wallIndexNext][0:2] + floorMeta[wallIndex][0:2]) / 2
                wasThin['direction'] = np.array([acr[0], H/2, acr[1]]) - wasThin['probe']
                wasThin['direction'] /= np.linalg.norm(wasThin['direction'])
                # wasThin['direction'] = groundShifting(wasThin['probe'], floorMeta, floorPoly, wasThin['direction'], theta, H)
                wasThin['viewLength'] = np.linalg.norm(np.array([floorMeta[wallIndexNext][0], H/2, floorMeta[wallIndexNext][1]]) - wasThin['probe'], ord=2)
                hypotheses.append(wasThin)
    hypotheses = redundancyRemove(hypotheses)
    for h in hypotheses:
        h['roomTypes'] = room['roomTypes']
        h['isObjCovered'] = isObjCovered(h, scene)
        theLawOfTheThird(h, room, theta, ASPECT)
        numSeenObjs(room, h, h['probe'] + h['direction'] * 0.02, h['direction'], floorMeta, theta)
        tarWindoorArea2021(h, scene, floorMeta, theta)
        layoutConstraint(h, room, theta)
        wallNormalOffset(h, floorMeta)
        isObjHalfCovered(h, room)
        secondNearestWallDis(h, floorMeta)
        isProbeOutside(h, floorPoly)
        if h['wallNormalOffset'] < 0.:
            h['probe'] += (abs(h['wallNormalOffset']) * 0.02) * h['direction']     
        toOriginAndTarget(h)
        h['score'] = scoreFunc(h)              
    hypotheses.sort(key=scoreFunc, reverse=True)
    for rank, h in zip(range(0,len(hypotheses)), hypotheses):
        h['rank'] = rank
    bestViews = {
        'wellAlignedShifted': None,
        'threeWall_R': None,
        'threeWall': None,
        'againstMidWall': None,
        'twoWallPerspective': None,
        'threeWall_thin': None,
        'threeWall_R_thin': None,
        'was_thin': None
    }
    for h in hypotheses:
        for viewTps in bestViews:
            if viewTps != h['type']:
                continue
            if bestViews[viewTps] is None:
                bestViews[viewTps] = h
    # bestViews = []
    # numOfChosen = min(3, len(hypotheses))
    # for index in range(0, numOfChosen):
    #     h = hypotheses[index]
    #     bestViews.append(toOriginAndTarget(h))
    return hypotheses

def renderPcamAsync(scenejson,identifier,dst=None):
    pt.USENEWWALL = True
    if dst is not None:
        return pt.pathTracing(scenejson, SAMPLE_COUNT, dst)
    return pt.pathTracing(scenejson, SAMPLE_COUNT, f"./latentspace/autoview/{scenejson['origin']}/{identifier}.png")

renderThreads = {}
def renderGivenPcam(pcam, scenejson, dst=None, isPathTrancing=True):
    scenejson["PerspectiveCamera"] = scenejson["PerspectiveCamera"].copy()
    scenejson["PerspectiveCamera"]['origin'] = pcam['origin']
    scenejson["PerspectiveCamera"]['target'] = pcam['target']
    scenejson["PerspectiveCamera"]['up'] = pcam['up']
    scenejson["canvas"] = scenejson["canvas"].copy()
    scenejson['canvas']['width']  = int(RENDERWIDTH)
    scenejson['canvas']['height'] = int(RENDERWIDTH / ASPECT)
    # identifier = uuid.uuid1()
    identifier = f'{pcam["rank"]}-room{pcam["roomId"]}-{pcam["type"]}'
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
    # scenejson = json.loads( json.dumps(scenejson, default=sk.jsonDumpsDefault) )
    # thread = pt.pathTracingPara.delay(scenejson, 4, f"./latentspace/autoview/{scenejson['origin']}/{identifier}.png")
    # renderThreads[str(identifier)] = thread

def eachNoConstraint(pcams):
    def nonumObjBeSeen(h):
        res = 0.
        # if h['numObjBeSeen'] == 0:
        #     return res
        if h['isProbeOutside']:
            return res
        if h['wallNormalOffset'] < -0.20:
            return res
        if h['isObjCovered']:
            res -= 1
        if h['type'] in ['wellAlignedShifted', 'againstMidWall', 'was_thin']:
            res += 1
        res += h['totalWindoorArea'] * 0.6 + h['layoutDirection'] * 3 # h['numObjBeSeen'] * 1. + 
        res += int(h['thirdHasObj_rb']) + int(h['thirdHasObj_lb']) + int(h['thirdHasObj_mid'])
        res += h['wallNormalOffset'] * 10
        return res

    def nototalWindoorArea(h):
        res = 0.
        if h['numObjBeSeen'] == 0:
            return res
        if h['isProbeOutside']:
            return res
        if h['wallNormalOffset'] < -0.20:
            return res
        if h['isObjCovered']:
            res -= 1
        if h['type'] in ['wellAlignedShifted', 'againstMidWall', 'was_thin']:
            res += 1
        res += h['numObjBeSeen'] * 1. + h['layoutDirection'] * 3 #  + h['totalWindoorArea'] * 0.6
        res += int(h['thirdHasObj_rb']) + int(h['thirdHasObj_lb']) + int(h['thirdHasObj_mid'])
        res += h['wallNormalOffset'] * 10
        return res

    def nothird(h):
        res = 0.
        if h['numObjBeSeen'] == 0:
            return res
        if h['isProbeOutside']:
            return res
        if h['wallNormalOffset'] < -0.20:
            return res
        if h['isObjCovered']:
            res -= 1
        if h['type'] in ['wellAlignedShifted', 'againstMidWall', 'was_thin']:
            res += 1
        res += h['numObjBeSeen'] * 1. + h['layoutDirection'] * 3 + h['totalWindoorArea'] * 0.6
        # res += int(h['thirdHasObj_rb']) + int(h['thirdHasObj_lb']) + int(h['thirdHasObj_mid'])
        res += h['wallNormalOffset'] * 10
        return res

    def nolayoutDirection(h):
        res = 0.
        if h['numObjBeSeen'] == 0:
            return res
        if h['isProbeOutside']:
            return res
        if h['wallNormalOffset'] < -0.20:
            return res
        if h['isObjCovered']:
            res -= 1
        if h['type'] in ['wellAlignedShifted', 'againstMidWall', 'was_thin']:
            res += 1
        res += h['numObjBeSeen'] * 1. + h['totalWindoorArea'] * 0.6 # h['layoutDirection'] * 3 + 
        res += int(h['thirdHasObj_rb']) + int(h['thirdHasObj_lb']) + int(h['thirdHasObj_mid'])
        res += h['wallNormalOffset'] * 10
        return res

    def nowallNormalOffset(h):
        res = 0.
        if h['numObjBeSeen'] == 0:
            return res
        if h['isProbeOutside']:
            return res
        if h['wallNormalOffset'] < -0.20:
            return res
        if h['isObjCovered']:
            res -= 1
        # if h['type'] in ['wellAlignedShifted', 'againstMidWall', 'was_thin']:
        #     res += 1
        res += h['numObjBeSeen'] * 1. + h['layoutDirection'] * 3 + h['totalWindoorArea'] * 0.6 
        res += int(h['thirdHasObj_rb']) + int(h['thirdHasObj_lb']) + int(h['thirdHasObj_mid'])
        # res += h['wallNormalOffset'] * 10
        return res
    
    newpcams = []
    for pc in pcams:
        pc['nonumObjBeSeen'] = nonumObjBeSeen(pc)
        pc['nototalWindoorArea'] = nototalWindoorArea(pc)
        pc['nothird'] = nothird(pc)
        pc['nolayoutDirection'] = nolayoutDirection(pc)
        pc['nowallNormalOffset'] = nowallNormalOffset(pc)

    def showMeAPcam(attr, pc):
        for index in range(len(pcams)):
            if pcams[index][attr] == pc[attr]:
                return pcams.pop(index)

    pc = max(pcams, key=lambda item: item['nonumObjBeSeen'])
    pc = showMeAPcam('nonumObjBeSeen', pc)
    if pc['nonumObjBeSeen'] <= 0:
        return []
    pc['cons'] = 'nonumObjBeSeen'
    newpcams.append(pc)

    pc = max(pcams, key=lambda item: item['nototalWindoorArea'])
    pc = showMeAPcam('nototalWindoorArea', pc)
    if pc['nototalWindoorArea'] <= 0:
        return []
    pc['cons'] = 'nototalWindoorArea'
    newpcams.append(pc)

    pc = max(pcams, key=lambda item: item['nothird'])
    pc = showMeAPcam('nothird', pc)
    if pc['nothird'] <= 0:
        return []
    pc['cons'] = 'nothird'
    newpcams.append(pc)

    pc = max(pcams, key=lambda item: item['nolayoutDirection'])
    pc = showMeAPcam('nolayoutDirection', pc)
    if pc['nolayoutDirection'] <= 0:
        return []
    pc['cons'] = 'nolayoutDirection'
    newpcams.append(pc)

    pc = max(pcams, key=lambda item: item['nowallNormalOffset'])
    pc = showMeAPcam('nowallNormalOffset', pc)
    if pc['nowallNormalOffset'] < 0:
        return []
    pc['cons'] = 'nowallNormalOffset'
    newpcams.append(pc)

    # for pc in newpcams:
    #     print(pc[pc['cons']])
    return newpcams

def eachConstraint(pcams):
    # the following code is for the qualitative comparison of constraints. 
    newpcams = []
    for pc in pcams:
        pc['third'] = int(pc['thirdHasObj_rb']) + int(pc['thirdHasObj_lb'])

    def showMeAPcam(attr, pc):
        for index in range(len(pcams)):
            if pcams[index][attr] == pc[attr]:
                return pcams.pop(index)

    pc = max(pcams, key=lambda item: item['numObjBeSeen'])
    pc = showMeAPcam('numObjBeSeen', pc)
    if pc['numObjBeSeen'] <= 0:
        return []
    pc['cons'] = 'numObjBeSeen'
    newpcams.append(pc)

    pc = max(pcams, key=lambda item: item['totalWindoorArea'])
    pc = showMeAPcam('totalWindoorArea', pc)
    if pc['totalWindoorArea'] <= 0:
        return []
    pc['cons'] = 'totalWindoorArea'
    newpcams.append(pc)

    pc = max(pcams, key=lambda item: item['third'])
    pc = showMeAPcam('third', pc)
    if pc['third'] <= 0:
        return []
    pc['cons'] = 'third'
    newpcams.append(pc)

    pc = max(pcams, key=lambda item: item['layoutDirection'])
    pc = showMeAPcam('layoutDirection', pc)
    if pc['layoutDirection'] <= 0:
        return []
    pc['cons'] = 'layoutDirection'
    newpcams.append(pc)

    pc = max(pcams, key=lambda item: item['wallNormalOffset'])
    pc = showMeAPcam('wallNormalOffset', pc)
    if pc['wallNormalOffset'] < 0:
        return []
    pc['cons'] = 'wallNormalOffset'
    newpcams.append(pc)

    # for pc in newpcams:
    #     print(pc[pc['cons']])
    return newpcams

def autoViewRooms(scenejson, isPathTrancing=True):
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

        pcams = autoViewOnePointPerspective(room, scenejson, probabilityOnlyObj)
        # pcams = eachNoConstraint(pcams)
        # global SAMPLE_COUNT
        # SAMPLE_COUNT = 64
        if isinstance(pcams, (dict,)):
            for tp in pcams:
                if pcams[tp] is None:
                    continue
                # pcams[tp]['direction'] = balancing(pcams[tp], room, pcams[tp]['theta'])
                thread = renderGivenPcam(pcams[tp], scenejson.copy(), isPathTrancing=isPathTrancing)
                if thread is not None:
                    renderThreads.append(thread)
        elif isinstance(pcams, (list,)):
            for index, pcam in zip(range(len(pcams)), pcams[0:20]): # pcams[0:200]
                # if index > 0 and pcam['score'] < 0.01:
                #     continue
                # pcams[index]['direction'] = balancing(pcams[index], room, pcams[index]['theta'])
                thread = renderGivenPcam(pcam, scenejson.copy(), isPathTrancing=isPathTrancing)
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

def hamiltonNext(ndp, views, scene):
    DIS = np.Inf
    res = None
    for view in views:
        if not view['roomId'] == ndp['roomId'] or view['isVisited']:
            continue
        # if np.dot(np.array(view['direction']), np.array(ndp['direction'])) <= 0:
        #     continue
        dis = np.linalg.norm(view['probe'] - ndp['probe'], ord=2)
        if np.linalg.norm(view['probe'] - ndp['probe']) < np.linalg.norm(view['direction'] - ndp['direction']):
            continue
        if np.dot(view['direction'], ndp['direction']) < 0:
            continue
        if dis < DIS:
            DIS = dis
            res = view
    # print(
    #     np.linalg.norm(np.array(view['probe']) - np.array(ndp['probe'])), 
    #     np.linalg.norm(np.array(view['direction']) - np.array(ndp['direction'])),
    #     ndp['roomId'])
    return res

def hamiltonNextRoom(roomId, pre, suc, scene):
    if roomId in suc:
        for res in suc[roomId]:
            if not scene['rooms'][res]['isVisited']:
                return res
    if roomId in pre:
        return pre[roomId]
    return -1

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
        view['probe'] = np.array(view['probe'])
        view['direction'] = np.array(view['direction'])
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
            # if door['roomIds'][0] not in involvedRoomIds and door['roomIds'][1] not in involvedRoomIds:
            #     continue
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
    ndproom = involvedRoomIds[0]
    roomOrder = []
    while ndproom != -1:
        roomOrder.append(ndproom)
        scene['rooms'][ndproom]['isVisited'] = True
        ndproom = hamiltonNextRoom(ndproom, pre, suc, scene)
    for room in scene['rooms']:
        room['isVisited'] = False
    def subPath(s):
        if s == len(roomOrder) - 1:
            return (True, s)
        state = False
        start = roomOrder[s]
        s += 1
        while s < len(roomOrder) and roomOrder[s] != start: 
            if roomOrder[s] in involvedRoomIds and not scene['rooms'][roomOrder[s]]['isVisited']:
                state = True
            s += 1
        return (state, s)
    i = 0
    while i < len(roomOrder):
        state, s = subPath(i)
        if not state:
            roomOrder = roomOrder[0:i+1] + roomOrder[s+1:]
            i -= 1
        else:
            scene['rooms'][roomOrder[i]]['isVisited'] = True
        i += 1
    ndproom = roomOrder[0]
    for view in views:
        if view['roomId'] == ndproom:
            ndpNext = view
    # perform the algorithm of Angluin and Valiant. 
    for i in range(1, len(roomOrder)+1):
        while ndpNext is not None:
            ndp = ndpNext
            res.append(ndp)
            ndp['isVisited'] = True
            ndpNext = hamiltonNext(ndp, views, scene)
        if i == len(roomOrder):
            break
        lastndproom = roomOrder[i-1]
        ndproom = roomOrder[i]
        edge = G[lastndproom][ndproom]
        # if edge['direction'].dot(edge['translate'] - ndp['probe']) < 0:
        if edge['directionToRoom'] != ndproom:
            edge['direction'] = -edge['direction']
        ndpNext = {
            'roomId': ndproom,
            'probe': edge['translate'],
            'origin': edge['translate'].tolist(),
            'target': (edge['translate'] + edge['direction']).tolist(),
            'direction': edge['direction'].tolist()
        }
    res = redundancyRemove(res, False)
    # res = hamiltonSmooth(res)
    with open(f'./latentspace/autoview/{scene["origin"]}/path', 'w') as f:
        json.dump(res, f, default=sk.jsonDumpsDefault)
    return res

def hamiltonBatch(batchList):
    for i in batchList:
        with open(f'./dataset/alilevel_door2021/{i}.json') as f:
            test_file = json.load(f)
        hamilton(test_file)

# for 3D-Front, it requires 269669 seconds. 
def floorplanOrthes():
    pt.cameraType = 'orthographic'
    pt.SAVECONFIG = False
    pt.REMOVELAMP = True
    pt.USENEWWALL = True
    floorplanlist = os.listdir('./dataset/Levels2021/')
    _start = 241
    for floorplanfile in floorplanlist[_start:]:
    # for floorplanfile in ['007e1443-462a-4dae-b47c-44cfc6a5a41d.json']:
        print(_start)
        _start+=1
        if '.json' not in floorplanfile:
            continue
        with open(f'./dataset/Levels2021/{floorplanfile}') as f:
            scenejson = json.load(f)
        # if os.path.exists(f"./dataset/alilevel_door2022_orth/{scenejson['origin']}.png"):
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
            pt.USENEWWALL = False
            pt.pathTracing(scenejson, 1, f"./dataset/alilevel_door2022_orth/{scenejson['origin']}.png")
        except Exception as e:
            print(e)
            continue
        pt.USENEWWALL = True
        pt.pathTracing(scenejson, 1, f"./dataset/alilevel_door2022_orth/{scenejson['origin']}newwall.png")
    # swap the cameraType back to perspective cameras. 
    pt.cameraType = 'perspective'

def highResRendering(dst=None):
    if dst is None:
        dst = 'highres'
    pt.SAVECONFIG = False
    pt.REMOVELAMP = False
    pt.USENEWWALL = True
    pt.emitter = 'constant'
    global RENDERWIDTH, SAMPLE_COUNT
    SAMPLE_COUNT = 64
    RENDERWIDTH = 1920
    jsonfilenames = os.listdir(f'./latentspace/autoview/{dst}')
    for jfn in jsonfilenames:
        if '.json' not in jfn:
            continue
        with open(f'./latentspace/autoview/{dst}/{jfn}', encoding='utf-8') as f:
            view = json.load(f)
        origin = view['scenejsonfile']
        with open(f'dataset/Levels2021/{view["scenejsonfile"]}.json', encoding='utf-8') as f:
            scenejson = json.load(f)
        sk.assignRoomIds(scenejson)
        for room in scenejson['rooms']:
            room['roomNorm'] = sk.generateRoomNormals(room['roomShape'])
        scenejson["PerspectiveCamera"] = {}
        scenejson["PerspectiveCamera"]['fov'] = DEFAULT_FOV
        scenejson["canvas"] = {}
        rThread = renderGivenPcam(view, scenejson, dst=f"./latentspace/autoview/{dst}/{jfn.replace('.json', '.png')}")
        print(f'Rendering {dst} -> {jfn} ... ')
        rThread.join()
    if dst == 'highres':
        return
    # showPcamPoints(origin)
    # showPcamInset(origin)
    # try:
    #     shutil.copytree(f'./latentspace/autoview/{origin}', f'./sceneviewer/results/{origin}')
    #     shutil.copy(f'./dataset/alilevel_door2021/{origin}.json', f'./sceneviewer/results/{origin}/scenejson.json')
    # except:
    #     pass

def sceneViewerBatch():
    pt.SAVECONFIG = False
    pt.REMOVELAMP = False
    pt.USENEWWALL = True
    pt.emitter = 'constant'
    global RENDERWIDTH, SAMPLE_COUNT
    SAMPLE_COUNT = 4
    RENDERWIDTH = 600
    sjfilenames = os.listdir('./dataset/alilevel_door2021')
    sjfilenames = sjfilenames[1400:1500]
    for sjfilename in sjfilenames:
        with open(f'./dataset/Levels2021/{sjfilename}') as f:
            scenejson = json.load(f)
        # if os.path.exists(f'./latentspace/autoview/{scenejson["origin"]}'):
        #     continue
        scenejson["PerspectiveCamera"] = {}
        scenejson["PerspectiveCamera"]['fov'] = DEFAULT_FOV
        scenejson["canvas"] = {}
        sk.preloadAABBs(scenejson)
        print(f'Starting: {scenejson["origin"]}...')
        print(sjfilenames.index(sjfilename))
        renderThreads = autoViewRooms(scenejson)
        for t in renderThreads:
            t.join()

def sceneViewerByFile(scenejson):
    pt.SAVECONFIG = False
    pt.REMOVELAMP = False
    pt.USENEWWALL = True
    pt.emitter = 'constant'
    global RENDERWIDTH, SAMPLE_COUNT
    SAMPLE_COUNT = 4
    RENDERWIDTH = 600
    sk.assignRoomIds(scenejson)
    for room in scenejson['rooms']:
        room['roomNorm'] = sk.generateRoomNormals(room['roomShape'])
    scenejson["PerspectiveCamera"] = {}
    scenejson["PerspectiveCamera"]['fov'] = DEFAULT_FOV
    scenejson["canvas"] = {}
    sk.preloadAABBs(scenejson)
    print(f'Starting: {scenejson["origin"]}...')
    renderThreads = autoViewRooms(scenejson)
    for t in renderThreads:
        t.join()

def autoViewRoom(room, scenejson):
    pt.SAVECONFIG = False
    pt.USENEWWALL = True
    pt.emitter = 'constant'
    sk.preloadAABBs(scenejson)
    renderThreads = []
    pcams = autoViewOnePointPerspective(room, scenejson)
    for pcam in pcams:
        pcam['direction'] = balancing(pcam, scenejson['rooms'][pcam['roomId']], pcam['theta'])
        thread = renderGivenPcam(pcam, scenejson.copy())
        if thread is not None:
            renderThreads.append(thread)

def renderLabelledImages(FD):
    originnames = os.listdir(f'./dataset/PathTracing/TanHao/{FD}')
    global RENDERWIDTH, SAMPLE_COUNT
    SAMPLE_COUNT = 64
    RENDERWIDTH = 1920
    pt.SAVECONFIG = False
    pt.REMOVELAMP = False
    pt.emitter = 'constant'
    for originname in originnames:
        jsonnames = os.listdir(f'./dataset/PathTracing/TanHao/{FD}/{originname}')
        for jsonname in jsonnames:
            identifier = jsonname.split('.')[0]
            if os.path.exists(f"./dataset/PathTracing/TanHao/{FD}/{originname}/{identifier}.png"):
                continue
            print(f'Rendering -- {originname} -- {identifier}. ')
            if '.json' not in jsonname:
                continue
            try:
                with open(f'./dataset/PathTracing/TanHao/{FD}/{originname}/{jsonname}') as f:
                    scenejson = json.load(f)
                scenejson['canvas']['width']  = int(RENDERWIDTH)
                scenejson['canvas']['height'] = int(RENDERWIDTH / ASPECT)
                pt.pathTracing(scenejson, SAMPLE_COUNT, f"./dataset/PathTracing/TanHao/{FD}/{originname}/{identifier}.png")
            except Exception as e:
                print(e)

if __name__ == "__main__":
    start_time = time.time()
    with open('./dataset/Levels2021/sfy1.json', encoding='utf-8') as f:
        sceneViewerByFile(json.load(f))
    with open('./dataset/Levels2021/sfy2.json', encoding='utf-8') as f:
        sceneViewerByFile(json.load(f))
    with open('./dataset/Levels2021/sfy3.json', encoding='utf-8') as f:
        sceneViewerByFile(json.load(f))
    with open('./dataset/Levels2021/sfy4.json', encoding='utf-8') as f:
        sceneViewerByFile(json.load(f))

    batchList = [
        # '187b9a69-55fa-43d4-a309-b9654b061fa5'
        # '20bb8b5e-be3b-4882-afd6-cf66095c447a',
        # '20850871-40c6-42c8-8a18-737cb55f8be0',
        # '20762858-41f4-424d-8fd5-caaf8ab8bef3',
        # '206a5356-a7db-46d6-89dc-2bdb21a8af7b',
        # '1fc66710-a632-4699-9b9f-8e217e1c33c1',
        # '1f8df1b6-5d60-4847-a1ce-8949251a76fb',
        # '1f5d59ce-7227-4643-9540-21f8d90618a2',
        # '1e818dfa-cfd3-43ce-9005-3ebefd7cf467',
        # '1e3aca33-209f-4ebd-8e99-704bc3b0158e',
        # '1e1e3a61-c5f2-4992-a4b8-074c193d02e3',
        # '1e16532d-1ec8-42c6-a66f-ef21e31c22c1',
        # '1e12ac7d-0584-47a4-8f90-b6086554e128',
        # '1dc74c70-21d3-40c6-8bd4-afb94dab934c',
        # '1d7a01b8-4621-4ac0-8d81-b1c8f0cedc98',
        # '1d481334-3f7f-4a41-8d8c-8c6e05a9ac10',
        # '1cdf715f-663f-4fe1-9307-edd66e5312cd',
        # '1cc6ef03-efaa-43d8-84a3-eafee1f6b214',
        # '1cc33f5b-a9f0-4f6c-a859-25ccf28ddfab',
        # '1cb6af4d-b7cf-4f76-8410-c3ac26e3c31a',
        # '1c5c5b3e-bb82-4177-88eb-eacae17642fa',
        # '1c35ad3e-ed43-4481-8bfc-63ee5918f9df',
        # '1c2e47d2-2ddb-4d62-bcc7-93a438f22b18',
        # '1c236ace-0e0e-48e5-8995-f0aef0a55373',
        # '1bf513b5-70af-4c69-b053-beb0f0419b8b',
        # '1bf23764-9d72-43f9-830f-0c0e17e18a83',
        # '1bcbb926-b9ef-471f-ba0f-f711b90bafd6',
        # '1bc22c85-3159-417c-a8cb-4e3788a0a0eb',
        # '1bba94d6-9dfe-4597-bf5a-3c2a3eae85bb',
        # '1b8a6ce5-1abe-4db5-b26e-93c0fbdde77e',
        # '1b86c99f-c4ae-41bc-96db-4597619d7add'
        # 'sfy1','sfy2','sfy3','sfy4'
    ]
    for origin in batchList:
        try:
            highResRendering(origin)
            pass
        except Exception as e:
            print(e)

    # for origin in os.listdir('./sceneviewer/results'):
    #     if os.path.exists(f'./sceneviewer/results/{origin}/showPcamInset2.png'):
    #         shutil.copy(f'./sceneviewer/results/{origin}/showPcamInset2.png', f'C:/Users/ljm/Desktop/untitled3/supp3/{origin}.png')
    # insetBatch(os.listdir('./sceneviewer/results'))
    # insetBatch(['03ff3349-3ab0-45fd-ae99-53da3334cb69'])
    # hamiltonBatch(batchList)
    # for d in os.listdir(f'./dataset/PathTracing/TanHao/userstudy-sceneviewer/'):
    #     renderLabelledImages(f'userstudy-sceneviewer/{d}')

    # with open('./dataset/Levels2021/187b9a69-55fa-43d4-a309-b9654b061fa5.json') as f:
    #    test_file = json.load(f)
    #    sk.preloadAABBs(test_file)
    # autoViewRoom(test_file['rooms'][1], test_file)    

    # sceneViewerBatch()

    print("\r\n --- %s seconds --- \r\n" % (time.time() - start_time))

@app_autoView.route("/bestviewroom/<roomId>", methods=['POST'])
def bestviewroom(roomId):
    if flask.request.method == 'POST':
        try:
            roomId = int(roomId)
        except:
            return None
        pt.SAVECONFIG = False
        sk.preloadAABBs(flask.request.json)
        pcams = autoViewOnePointPerspective(flask.request.json['rooms'][int(roomId)], flask.request.json)
        return json.dumps(pcams[0], default=sk.jsonDumpsDefault)

@app_autoView.route("/usercommitchange/<username>", methods=['POST'])
def usercommitchange(username):
    if flask.request.method == 'POST':
        data = flask.request.json
        scene_json = data['json']
        main_obj = data['mainobj']
        alipay = data['alipay']
        series = data['series']
        SAVE_COMMIT_PATH = f'./layoutmethods/cgseries/{main_obj}/{username}-{series}'
        timestr = time.strftime("%Y%m%d-%H%M%S")
        if not os.path.exists(f"{SAVE_COMMIT_PATH}"):
            os.makedirs(f"{SAVE_COMMIT_PATH}")
        with open(f"{SAVE_COMMIT_PATH}/{username}_{alipay}_{timestr}.json", 'w') as f:
            json.dump(scene_json, f)
        filenames = os.listdir(f'{SAVE_COMMIT_PATH}')
        count = 0
        for filename in filenames:
            if f'{username}_{alipay}_' in filename:
                count += 1
        return f'{count} {main_obj}/{series}/{username}_{alipay}_{timestr}'


def calWall(wallResult, obji, room):
    try:
        shape = np.array(room['roomShape']) # p2d('/' + room['origin'], room['modelId'] + 'f.obj')
    except Exception as e:
        return -1
    if len(shape) <= 2:
        return -1

    # find the nearest wall; 
    p = np.array([obji['translate'][0], obji['translate'][2]])
    shapeEnd = shape[np.arange(1,len(shape)).tolist() + [0]]
    a_square = np.sum((shape - p)**2, axis=1)
    b_square = np.sum((shapeEnd - p)**2, axis=1)
    c_square = np.sum((shape - shapeEnd)**2, axis=1)
    area_double = 0.5 * np.sqrt(4 * a_square * b_square - (a_square + b_square - c_square)**2 )
    distances = area_double / np.sqrt(c_square)
    _indicesList = []
    wallMinIndices = np.argsort(distances)
    innerProducts = np.sum((shape - p) * (shape - shapeEnd), axis=1)
    for i in wallMinIndices:
        if 0 <= innerProducts[i] and innerProducts[i] <= c_square[i]:
            _indicesList.append(i)
            if len(_indicesList) == 2:
                break
            # wallMinIndex = i
    if len(_indicesList) < 2:
        return -1
    
    wallResult[1] = distances[_indicesList[0]]
    wallResult[2] = distances[_indicesList[1]]

    wn = (shape[_indicesList[0]] - shapeEnd[_indicesList[0]])[[1,0]]
    ori = obji['orient'] - np.arctan2(wn[0], -wn[1])
    while ori > np.math.pi:
        ori -= 2 * np.math.pi
    while ori < -(np.math.pi):
        ori += 2 * np.math.pi

    wallResult[0] = ori

    return 1

def obj_WinDoor_Relation(windoorResult, iobj, windoor):
    if windoor['bbox']['max'][1] < 0.001:
        #print('illegal door bbox')
        return -1
    lenx = windoor['bbox']['max'][0] - windoor['bbox']['min'][0]
    leny = windoor['bbox']['max'][1] - windoor['bbox']['min'][1]
    lenz = windoor['bbox']['max'][2] - windoor['bbox']['min'][2]
    width = 0
    posx = (windoor['bbox']['max'][0] + windoor['bbox']['min'][0])/2 - iobj['translate'][0]
    posy = (windoor['bbox']['max'][1] + windoor['bbox']['min'][1])/2 - iobj['translate'][1]
    posz = (windoor['bbox']['max'][2] + windoor['bbox']['min'][2])/2 - iobj['translate'][2]
    dis = np.sqrt(posx*posx + posz*posz)
    ori = - iobj['orient']
    #if iobj['rotateOrder'] != 'XYZ':
        #print('warning: obj_WinDoor_Relation: unexpected rotation order ' + iobj['rotateOrder'])
    #if abs(iobj['rotate'][0]) > 0.001 or abs(iobj['rotate'][2]) > 0.001 :
        #print('warning: obj_WinDoor_Relation: rotation on x-axis or z-axis will be ignored')
    
    if lenx > lenz:
        width = lenx
        windoorResult[7] = 'z'
    else :
        width = lenz
        ori += 1.5708
        windoorResult[7] = 'x'

    windoorResult[0] = dis
    windoorResult[1] = posx
    windoorResult[2] = posy
    windoorResult[3] = posz
    windoorResult[4] = width
    windoorResult[5] = leny
    windoorResult[6] = ori
    return 1

def calDoor(doorResult, iobj, room):
    #print('calculating door from block')
    for obj in room['blockList']:
        if 'coarseSemantic' in obj and (obj['coarseSemantic'] == 'door' or obj['coarseSemantic'] == 'Door'):
            windoorResult = [0,0,0,0,0,0,0,0]
            if obj_WinDoor_Relation(windoorResult, iobj, obj) < 0: #print(obj['bbox'] + 'max0 skip\n')
                continue
            loc = 0  #print(obj['bbox']) print(windoorResult) print('\n')
            for tmp in doorResult:
                if tmp[0] < windoorResult[0]:
                    loc = loc+1
                else:
                    break
            doorResult.insert(loc, windoorResult)
            
    #print('calculating door from obj')
    for obj in room['objList']:
        if 'coarseSemantic' in obj and (obj['coarseSemantic'] == 'door' or obj['coarseSemantic'] == 'Door'):
            windoorResult = [0,0,0,0,0,0,0,0]
            if obj_WinDoor_Relation(windoorResult, iobj, obj) < 0: #print(obj['bbox'] + 'max0 skip\n')
                continue
            loc = 0 #print(obj['bbox']) print(windoorResult) print('\n')
            for tmp in doorResult:
                if tmp[0] < windoorResult[0]:
                    loc = loc+1
                else:
                    break
            doorResult.insert(loc, windoorResult)
    return 1

def calWindow(windowResult, iobj, room):
    #print('calculating window')
    for obj in room['objList']:
        if 'coarseSemantic' in obj and (obj['coarseSemantic'] == 'window' or obj['coarseSemantic'] == 'Window'):
            windoorResult = [0,0,0,0,0,0,0,0]
            if obj_WinDoor_Relation(windoorResult, iobj, obj) < 0: #print(obj['bbox'] +  'max0 skip\n')
                continue
            loc = 0 #print(obj['bbox']) print(windoorResult) print('\n')
            for tmp in windowResult:
                if tmp[0] < windoorResult[0]:
                    loc = loc+1
                else:
                    break
            windowResult.insert(loc, windoorResult)
    return 1

@app_autoView.route("/usercommitOSR", methods=['POST'])
def usercommitOSR():
    if flask.request.method == 'POST':
        timestr = time.strftime("%Y%m%d-%H%M%S")
        data = flask.request.json
        scene_json = data['json']
        intersect = data['intersectobject']
        gtransgroup = data['gtransgroup']
        user = data['userOSR']
        withWall = data['roomConstraints'][0]
        withWindow = data['roomConstraints'][1] #data['windowYL']
        withDoor = data['roomConstraints'][2] #data['doorYL']
        
        try:
            rela_name = data['nameOSR']
        except:
            rela_name = ''
    else:
        return 'sorry you\'re not using POST method'

    wallResult = [-1,-1,-1]
    windowResult = []
    doorResult = []
    flag = False
    changable = False
    for room in scene_json['rooms']:
        for obj in room['objList']:
            if 'modelId' in obj and obj['modelId'] == intersect[0]:
                if abs(obj['translate'][0] - intersect[1]) < 0.001 and abs(obj['translate'][1] - intersect[2]) < 0.001 and abs(obj['translate'][2] - intersect[3]) < 0.001:
                    flag = True #print(obj)
                    if withWall:
                        flag = (calWall(wallResult, obj, room) > 0)
                    if withWindow:
                        flag = (calWindow(windowResult, obj, room) > 0)
                    if withDoor:
                        flag = (calDoor(doorResult, obj, room) > 0)
                    if 'startState' in obj:
                        changable = obj['startState']
                    if not flag:
                        return 'geometry error in the room'
        if flag:
            break

    if not flag:
        return 'object isn\'t found in the scene'

    fd = open("./layoutmethods/object-spatial-relation-dataset.txt", 'a+')
    writeString = intersect[0]

    if abs(1.00 - intersect[7]) > 0.001 or abs(1.00 - intersect[8]) > 0.001 or abs(1.0 - intersect[9]) > 0.001:
        writeString += '; scale[{%.5f, %.5f, %.5f,}:]'%(intersect[7], intersect[8], intersect[9])

    if changable:
        writeString += '; state[{%s,}:]'%(changable)

    if len(gtransgroup):
        writeString += '; gtrans['
        for k in gtransgroup:
            writeString += '{%s, %.5f, %.5f, %.5f, %.5f, %.5f, %.5f, %.5f,'%(k[0],float(k[1]),float(k[2]),float(k[3]),float(k[4]),float(k[5]),float(k[6]),float(k[7]))
            if len(k[8]):
                writeString += '%s,' %(k[8])
            writeString += '}:'
        writeString += ']'
    
    if withWall:
        writeString += '; wall[{%.5f, %.5f, %.5f,}:]'%(wallResult[1],wallResult[2], wallResult[0])
    
    if withWindow and len(windowResult) > 0:
        writeString += '; window['
        for win in windowResult:
            writeString += '{%.5f, %.5f, %.5f, %.5f, %.5f, %.5f, %.5f, %c,}:'%(win[0],win[1],win[2],win[3],win[4],win[5],win[6],win[7])
        writeString += ']'

    if withDoor and len(doorResult) > 0:
        writeString += '; door['
        for dor in doorResult:
            writeString += '{%.5f, %.5f, %.5f, %.5f, %.5f, %.5f, %.5f, %c,}:'%(dor[0],dor[1],dor[2],dor[3],dor[4],dor[5],dor[6],dor[7])
        writeString += ']'
    
    if len(rela_name):
        writeString += '; ' + rela_name
    
    writeString += '; ' + user

    fd.write(writeString + "\n")
    fd.close()

    return f'Successfully submitted relation {rela_name}_{intersect[0]}_{user}_{timestr}' 

@app_autoView.route("/queryAABB/<model>/<state>")
def queryAABB(model, state):
    if os.path.exists(f'./static/dataset/object/{model}/{state}-AABB.json'):
        try:
            AABBcache = {}
            with open(f'./static/dataset/object/{model}/{state}-AABB.json') as f:
                AABBcache = json.load(f)
            return json.dumps({"max":AABBcache["max"], "min":AABBcache["min"]})
        except json.decoder.JSONDecodeError as e:
            print(e)

@app_autoView.route("/usersearchOSR",methods=['POST'])
def usersearchOSR():
    if flask.request.method == 'POST':
        timestr = time.strftime("%Y%m%d-%H%M%S")
        data = flask.request.json
        scene_json = data['json']
        interjson = data['interjson']
        
    else:
        return 'sorry you\'re not using POST method'

    #collect and organize
    wallResult = [-1,-1,-1]
    windowResult = []
    doorResult = []
    room = scene_json['rooms'][interjson['roomId']]
    for obj in room['objList']:
        if 'modelId' in obj and obj['modelId'] == interjson['modelId']:
            if abs(obj['translate'][0] - interjson['translate'][0]) < 0.001 and abs(obj['translate'][1] - interjson['translate'][1]) < 0.001 and abs(obj['translate'][2] - interjson['translate'][2]) < 0.001:
                flag = True #print(obj)
                flag = (calWall(wallResult, obj, room) > 0)
                flag = (calWindow(windowResult, obj, room) > 0)
                flag = (calDoor(doorResult, obj, room) > 0)
                if not flag:
                    print('geometry error in the room')
                    return ""

    #retrieve
    selected = mainSearch(interjson, wallHint = wallResult, windowHint = windowResult, doorHint = doorResult)[0:8];#searchMainModelId(interjson['modelId'])[0:8];#

    for origin in selected:
        print(origin['priorId'], origin['score'])
        t = {}
        t['img'] = origin['priorId'] + '.png'
        t['identifier'] = origin['priorId']
        origin['priorMeta'] = t

    return json.dumps(selected)

@app_autoView.route("/ylimgs/<identifier>")
def ylimgs(identifier):
    if os.path.exists(f'./yltmp/OSRfigures/{identifier}.png'):
        return flask.send_file(f'./yltmp/OSRfigures/{identifier}.png')
    
@app_autoView.route("/catimgs/<identifier>")
def catimgs(identifier):
    if os.path.exists(f'./yltmp/OSRfigures/{identifier}.png'):
        return flask.send_file(f'./yltmp/OSRfigures/{identifier}.png')

def loadClist(name):
    c_List = {}
    loadF = open(name,"r")
    lines = loadF.readlines()
    for line in lines:
        a = line.split("\t")
        k = int(a[0][:-1])
        lst = a[1].split(',')
        c_List[k] = []
        for num in lst[:-1]:
            c_List[k].append(int(num))
    return c_List

coarseTypes = "0808_0_0.8_300"
fineTypes = "0827_0_0.5_50"

@app_autoView.route("/prior_catagory",methods=['POST'])
def prior_catagory():
    c_list = loadClist("./yltmp/class_" + coarseTypes + ".txt")
    ret = []
    cnt = 0

    mainObjFile = open("./yltmp/statistic.txt","r")
    mainObj_list = {}
    for line in mainObjFile.readlines():
        a = line.split("\t")
        mainObj_list[a[0][:-1]] = a[2][:-3]

    for i in c_list:
        t = {}
        t['img'] = str(i) + '.png'
        t['identifier'] = i
        t['mainObjects'] = mainObj_list[str(i)].split(",") #"Multi-seat Sofa:72%"
        t['leng'] = len(c_list[i])
        c = loadClist("./yltmp/classes/" + str(i) + "/class_" + fineTypes + ".txt")
        t['le'] = len(c)
        ret.append(t)
        #print(c_list[i])
    ret.sort(key=lambda t:len(c_list[t['identifier']]))
    return json.dumps(ret[-1:0:-1])#print(ret[-1:0:-1])

manList = [
    [206,140,35,201,208,171,198], #living room
    [10,11,46,130,184,151,167], #shelves
    [127,0,48,189,90,306,332], #beds
    [7,9,43,91,215,221,235], #studies
    [230,82,66,124,107,335,71], #dining
    [53, 58, 88, 192, 148, 139, 72] #utils
]

@app_autoView.route("/catagory_prior_middle/<identifier>",methods=['POST'])
def catagory_prior_middle(identifier):
    c_list = loadClist("./yltmp/classes/" + identifier + "/class_" + fineTypes + ".txt")
    ret = []
    for i in c_list:
        t = {}
        t['img'] = str(i) + '.png'
        t['identifier'] = i
        t['mother'] = identifier
        t['leng'] = len(c_list[i])
        ret.append(t)
    ret.sort(key=lambda t:len(c_list[t['identifier']]))
    return json.dumps(ret[-1:-14:-1])#print(ret[-1:-10:-1])

@app_autoView.route("/catagory_prior/<identifier>/<identi>",methods=['POST'])
def catagory_prior(identifier, identi):
    c_list = loadClist("./yltmp/classes/" + identifier + "/class_" + fineTypes + ".txt")
    selected = searchId(c_list[int(identi)])
    orderCnt = 1
    for origin in selected:
        #print(origin['priorId'], origin['score'])
        t = {}
        t['img'] = origin['priorId'] + '.png'
        t['identifier'] = origin['priorId']
        subsets = []
        strid = str(origin['priorId'])
        for filename in os.listdir('./yltmp/OSRfigures'):
            if filename[:(len(strid)+4)] == strid + '____' and filename[-4:].lower() == '.png':
                subsets.append(filename[(len(strid)+4):-4])
        t['subsets'] = subsets
        t['order'] = orderCnt
        origin['priorMeta'] = t
        origin['identifier'] = origin['priorId']
        orderCnt += 1
    return json.dumps(selected[:13])#print(selected[:13])

methods = ["Inds", "MgAdd", "CLPT", "CGS", "FFG"]
@app_autoView.route("/clickTimer",methods=['POST'])
def clickTimer():
    data = flask.request.json
    timestr = time.strftime("%Y%m%d-%H%M%S")
    f = open("./yltmp/experiment/%s-%s-%s-%s-timer.json"%(data['homeType'],methods[int(data['methodName'])],data['usern'],timestr),"w")
    f.write(json.dumps(data['timeC']))
    f.close()
    f = open("./yltmp/experiment/%s-%s-%s-%s-result.json"%(data['homeType'],methods[int(data['methodName'])],data['usern'],timestr),"w")
    f.write(json.dumps(data['json']))
    f.close()
    return "%s-%s-%s-%s OK"%(data['homeType'],methods[int(data['methodName'])],data['usern'],timestr)

@app_autoView.route("/autoviewfp2023", methods=['POST'])
def autoviewfp2023():
    if flask.request.method == 'POST':
        try:
            roomId = int(roomId)
        except:
            return None
        pt.SAVECONFIG = False
        sk.preloadAABBs(flask.request.json)
        res = []
        for room in flask.request.json['rooms']:
            pcams = autoViewOnePointPerspective(room, flask.request.json, scoreFunc=probabilityOPP2)
            res.append(pcams)
        return json.dumps(res, default=sk.jsonDumpsDefault)

@app_autoView.route("/autoviewroom/<roomId>", methods=['POST'])
def autoviewroom(roomId):
    if flask.request.method == 'POST':
        try:
            roomId = int(roomId)
        except:
            return None
        pt.SAVECONFIG = False
        sk.preloadAABBs(flask.request.json)
        pcams = autoViewOnePointPerspective(flask.request.json['rooms'][roomId], flask.request.json, scoreFunc=probabilityOPP2)
        """
        index = -1
        while abs(index) <= len(pcams) - 1:
            if pcams[index]['isObjCovered'] or pcams[index]['isProbeOutside']:
                index -= 1
            else:
                break
        return json.dumps(pcams[index], default=sk.jsonDumpsDefault)
        """
        
        if 'lastAutoView' not in flask.request.json or 'lastFlag' not in flask.request.json['lastAutoView']:
            pcams[0]['lastFlag'] = True
            return json.dumps(pcams[0], default=sk.jsonDumpsDefault)
        lastFlag = flask.request.json['lastAutoView']['lastFlag']
        if lastFlag:
            index = -1
            while abs(index) <= len(pcams) - 1:
                if pcams[index]['isObjCovered'] or pcams[index]['isProbeOutside']:
                    index -= 1
                else:
                    break
            res = pcams[-1]
        else:
            res = pcams[0]
        res['lastFlag'] = not lastFlag
        return json.dumps(res, default=sk.jsonDumpsDefault)
        """
        if 'lastAutoView' not in flask.request.json:
             return json.dumps(pcams[0], default=sk.jsonDumpsDefault)
        else:
            for pcam in pcams:
                if pcam['type'] != flask.request.json['lastAutoView']['type']:
                    return json.dumps(pcam, default=sk.jsonDumpsDefault)
                if pcam['type'] == 'twoWallPerspective':
                    if pcam['wallDiagIndex'] != flask.request.json['lastAutoView']['wallDiagIndex']:
                        return json.dumps(pcam, default=sk.jsonDumpsDefault)
                else:
                    if pcam['wallIndex'] != flask.request.json['lastAutoView']['wallIndex']:
                        return json.dumps(pcam, default=sk.jsonDumpsDefault)
        """

@app_autoView.route("/autoviewByID")
def autoviewByID():
    ret = []
    origin = flask.request.args.get('origin', default = "", type = str)
    dir1 = f'./sceneviewer/results/{origin}'
    dir2 = f'./latentspace/autoview/{origin}'
    if os.path.exists(dir1):
        filenames = os.listdir(dir1)
    else:
        if not os.path.exists(dir2):
            return []
        else:
            filenames = os.listdir(dir2)
    for filename in filenames:
        if '.json' not in filename:
            continue
        with open(f'{dir1}/{filename}') as f:
            pcam = json.load(f)
        if 'identifier' not in pcam:
            continue
        pcam['img'] = pcam['identifier'] + '.png'
        ret.append(pcam)
    return json.dumps(ret)

allExistingResultsDir = os.listdir('./sceneviewer/results')
@app_autoView.route('/autoviewMapping')
def autoviewMapping():
    ret = []
    selected = random.sample(allExistingResultsDir, 5) + ['03a73289-5269-42b1-af4b-f30056c97c64']
    for origin in selected:
        if not os.path.exists(f'./sceneviewer/results/{origin}/showPcamInset2.png'):
            continue
        t = {}
        t['img'] = origin + '.png'
        t['identifier'] = origin
        ret.append(t)
    return json.dumps(ret)

@app_autoView.route("/autoviewimgs/<origin>/<identifier>")
def autoviewimgs(origin, identifier):
    if origin == 'mapping':
        return flask.send_file(f'./sceneviewer/results/{identifier}/showPcamInset2.png')
    else:
        if os.path.exists(f'./sceneviewer/results/{origin}/{identifier}.png'):
            return flask.send_file(f'./sceneviewer/results/{origin}/{identifier}.png')
        else:
            return flask.send_file(f'./latentspace/autoview/{origin}/{identifier}.png')

@app_autoView.route("/autoViewPath")
def autoViewPath():
    origin = flask.request.args.get('origin', default = "", type = str)
    if not os.path.exists(f'./latentspace/autoview/{origin}/path'):
        return []
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
        try:
            pcam['img'] = pcam['identifier'] + '.png'
        except:
            continue
        ret.append(pcam)
    return ret
