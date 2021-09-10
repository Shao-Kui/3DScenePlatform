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
from sceneviewer.utils import preloadAABBs,findTheFrontFarestCorner,isObjectInSight
from sceneviewer.utils import isWindowOnWall,calWindoorArea,expandWallSeg,redundancyRemove
from sceneviewer.utils import twoInfLineIntersection,toOriginAndTarget,hamiltonSmooth
from sceneviewer.inset import showPcamInset,showPcamPoints,insetBatch
import shutil

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
    floorMeta = p2d('.', '/dataset/room/{}/{}f.obj'.format(room['origin'], room['modelId']))
    floorPoly = Polygon(floorMeta[:, 0:2])
    H = sk.getWallHeight(f"./dataset/room/{room['origin']}/{room['modelId']}w.obj")
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
        direction = groundShifting(probe, floorMeta, floorPoly, np.array(direction), theta, H)
        pcam['probe'] = probe
        pcam['direction'] = direction
        pcam['theta'] = theta
        pcam['roomId'] = room['roomId']
        pcam['wallDiagIndex'] = wallDiagIndex
        pcam['type'] = 'twoWallPerspective'
        pcam['floorMeta'] = floorMeta
        pcams.append(pcam)
    return pcams

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

def autoViewOnePointPerspective(room, scene, scoreFunc=probabilityOPP):
    """
    This function tries generate all potential views w.r.t the One-Point Perspective Rule (OPP Rule). 
    Note that several variants exist w.r.t different rules. 
    """
    theta = (np.pi * scene['PerspectiveCamera']['fov'] / 180) / 2
    floorMeta = p2d('.', '/dataset/room/{}/{}f.obj'.format(room['origin'], room['modelId']))
    floorPoly = Polygon(floorMeta[:, 0:2])
    H = sk.getWallHeight(f"./dataset/room/{room['origin']}/{room['modelId']}w.obj")
    # MAXDIAMETER = sk.roomDiameter(floorMeta)
    # find the anchor point and the anchor wall. 
    hypotheses = []
    hypotheses += autoViewsRodrigues(room, scene)
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
            # hypotheses.append(h)

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
                thw['direction'] = groundShifting(thw['probe'], floorMeta, floorPoly, thw['direction'], theta, H)
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
                thwR['direction'] = groundShifting(thwR['probe'], floorMeta, floorPoly, thwR['direction'], theta, H)
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
                mtm['direction'] = groundShifting(mtm['probe'], floorMeta, floorPoly, mtm['direction'], theta, H)
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
                thinL['direction'] = groundShifting(thinL['probe'], floorMeta, floorPoly, thinL['direction'], theta, H)
                thinL['viewLength'] = np.linalg.norm(np.array([floorMeta[wallIndexNext][0], H/2, floorMeta[wallIndexNext][1]]) - thinL['probe'], ord=2)
                hypotheses.append(thinL)

                thinR = thw.copy()
                thinR['probe'] = pThW2 + (pThW1 - pThW2)/3
                thinR['type'] = 'threeWall_R_thin'
                thinR['probe'] = np.array([thinR['probe'][0], H/2, thinR['probe'][1]])
                acr = floorMeta[wallIndex][0:2] + (floorMeta[wallIndexNext][0:2] - floorMeta[wallIndex][0:2])/3
                thinR['direction'] = np.array([acr[0], H/2, acr[1]]) - thinR['probe']
                thinR['direction'] /= np.linalg.norm(thinR['direction'])
                thinR['direction'] = groundShifting(thinR['probe'], floorMeta, floorPoly, thinR['direction'], theta, H)
                thinR['viewLength'] = np.linalg.norm(np.array([floorMeta[wallIndexNext][0], H/2, floorMeta[wallIndexNext][1]]) - thinR['probe'], ord=2)

                wasThin = thw.copy()
                wasThin['probe'] = (pThW1 + pThW2) / 2
                wasThin['type'] = 'was_thin'
                wasThin['probe'] = np.array([wasThin['probe'][0], H/2, wasThin['probe'][1]])
                acr = (floorMeta[wallIndexNext][0:2] + floorMeta[wallIndex][0:2]) / 2
                wasThin['direction'] = np.array([acr[0], H/2, acr[1]]) - wasThin['probe']
                wasThin['direction'] /= np.linalg.norm(wasThin['direction'])
                wasThin['direction'] = groundShifting(wasThin['probe'], floorMeta, floorPoly, wasThin['direction'], theta, H)
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
    identifier = f'room{pcam["roomId"]}-{pcam["type"]}-{pcam["rank"]}'
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

def autoViewRooms(scenejson, isPathTrancing=True):
    pt.SAVECONFIG = False
    preloadAABBs(scenejson)
    renderThreads = []
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

        pcams = autoViewOnePointPerspective(room, scenejson)
        if isinstance(pcams, (dict,)):
            for tp in pcams:
                if pcams[tp] is None:
                    continue
                # pcams[tp]['direction'] = balancing(pcams[tp], room, pcams[tp]['theta'])
                thread = renderGivenPcam(pcams[tp], scenejson.copy(), isPathTrancing=isPathTrancing)
                if thread is not None:
                    renderThreads.append(thread)
        elif isinstance(pcams, (list,)):
            for index, pcam in zip(range(len(pcams)), pcams[0:6]):
                if index > 0 and pcam['score'] < 5:
                    continue
                thread = renderGivenPcam(pcam, scenejson.copy(), isPathTrancing=isPathTrancing)
                if thread is not None:
                    renderThreads.append(thread)
    if not os.path.exists(f'./latentspace/autoview/{scenejson["origin"]}'):
        print(f'{scenejson["origin"]} is an empty floorplan. ')
        return []
    hamilton(scenejson)
    for t in renderThreads:
        t.join()
    try:
        showPcamInset(scenejson['origin'])
        showPcamPoints(scenejson['origin'])
    except:
        pass
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

def highResRendering(dst=None):
    if dst is None:
        dst = 'highres'
    pt.SAVECONFIG = False
    pt.REMOVELAMP = False
    global RENDERWIDTH, SAMPLE_COUNT
    SAMPLE_COUNT = 64
    RENDERWIDTH = 1920
    jsonfilenames = os.listdir(f'./latentspace/autoview/{dst}')
    for jfn in jsonfilenames:
        if '.json' not in jfn:
            continue
        with open(f'./latentspace/autoview/{dst}/{jfn}') as f:
            view = json.load(f)
        origin = view['scenejsonfile']
        with open(f'dataset/alilevel_door2021/{view["scenejsonfile"]}.json') as f:
            scenejson = json.load(f)
        scenejson["PerspectiveCamera"] = {}
        scenejson["PerspectiveCamera"]['fov'] = DEFAULT_FOV
        scenejson["canvas"] = {}
        rThread = renderGivenPcam(view, scenejson, dst=f"./latentspace/autoview/{dst}/{jfn.replace('.json', '.png')}")
        print(f'Rendering {dst} -> {jfn} ... ')
        rThread.join()
    if dst == 'highres':
        return
    showPcamPoints(origin)
    showPcamInset(origin)
    try:
        shutil.copytree(f'./latentspace/autoview/{origin}', f'./sceneviewer/results/{origin}')
        shutil.copy(f'./dataset/alilevel_door2021/{origin}.json', f'./sceneviewer/results/{origin}/scenejson.json')
    except:
        pass

def sceneViewerBatch():
    pt.SAVECONFIG = False
    pt.REMOVELAMP = False
    global RENDERWIDTH, SAMPLE_COUNT
    SAMPLE_COUNT = 4
    RENDERWIDTH = 600
    sjfilenames = os.listdir('./dataset/alilevel_door2021')
    sjfilenames = sjfilenames[701:800]
    for sjfilename in sjfilenames:
        with open(f'./dataset/alilevel_door2021/{sjfilename}') as f:
            scenejson = json.load(f)
        scenejson["PerspectiveCamera"] = {}
        scenejson["PerspectiveCamera"]['fov'] = DEFAULT_FOV
        scenejson["canvas"] = {}
        preloadAABBs(scenejson)
        print(f'Starting: {scenejson["origin"]}...')
        print(sjfilenames.index(sjfilename))
        renderThreads = autoViewRooms(scenejson)
        for t in renderThreads:
            t.join()

def autoViewRoom(room, scenejson):
    pt.SAVECONFIG = False
    preloadAABBs(scenejson)
    renderThreads = []
    pcams = autoViewOnePointPerspective(room, scenejson)
    for pcam in pcams:
        thread = renderGivenPcam(pcam, scenejson.copy())
        if thread is not None:
            renderThreads.append(thread)

def renderLabelledImages():
    originnames = os.listdir('./dataset/PathTracing/TanHao/us-results')
    global RENDERWIDTH, SAMPLE_COUNT
    SAMPLE_COUNT = 64
    RENDERWIDTH = 1920
    pt.SAVECONFIG = False
    pt.REMOVELAMP = False
    for originname in originnames:
        jsonnames = os.listdir(f'./dataset/PathTracing/TanHao/us-results/{originname}')
        for jsonname in jsonnames:
            if '.json' not in jsonname:
                continue
            with open(f'./dataset/PathTracing/TanHao/us-results/{originname}/{jsonname}') as f:
                scenejson = json.load(f)
            scenejson['canvas']['width']  = int(RENDERWIDTH)
            scenejson['canvas']['height'] = int(RENDERWIDTH / ASPECT)
            identifier = jsonname.split('.')[0]
            print(f'Rendering -- {originname} -- {identifier}. ')
            pt.pathTracing(scenejson, SAMPLE_COUNT, f"./dataset/PathTracing/TanHao/us-results/{originname}/{identifier}.png")

if __name__ == "__main__":
    start_time = time.time()
    # with open('./examples/4cc6dba0-a26e-42cb-a964-06cb78d60bae.json') as f:
    # with open('./examples/a630400d-2cd7-459f-8a89-85ba949c8bfd.json') as f:
    # with open('./examples/ceea988a-1df7-418e-8fef-8e0889f07135-l7767-dl.json') as f:
    # with open('./examples/cb2146ba-8f9e-4a68-bee7-50378200bade-l7607-dl (1).json') as f:
    # with open('./examples/ba9d5495-f57f-45a8-9100-33dccec73f55.json') as f:
    # with open('./dataset/alilevel_door2021/1310949e-14c4-40fb-a410-e9973be8f50a.json') as f:
    #    test_file = json.load(f)
    #    preloadAABBs(test_file)
    # autoViewRoom(test_file['rooms'][6], test_file)    
    # autoViewRoom(test_file['rooms'][4], test_file)
    # autoViewRoom(test_file['rooms'][5], test_file)
    # autoViewRoom(test_file['rooms'][7], test_file)
    # autoViewRoom(test_file['rooms'][3], test_file)

    # sceneViewerBatch()

    _batchList = [
        '028448cc-806f-4f6f-81aa-68d5824f6c02',
        '0338bdd5-e321-467e-a998-38f2218e2fdd',
        '03ff3349-3ab0-45fd-ae99-53da3334cb69',
        '03a73289-5269-42b1-af4b-f30056c97c64',
        '04940635-c251-4356-968e-3b8d9fe93a4c',
        "03b2259c-c24b-44a9-b055-2fe85137419a",
        '0486afe9-e7ec-40d9-91e0-09513a96a80e',
        '02a9b734-993c-496c-99e4-6458e35f9178',
        "05d05b98-e95c-4671-935d-7af6a1468d07",
        "071527d1-4cb5-47a9-abd0-b1d83bd3e286",
        '1337c3b5-e8e8-4e2f-b7d5-f3aafdfd6f7b',
        '12d084a8-6632-472a-af65-32e7109e5783',
        '13da455c-9e07-43b2-9e3f-d6d04953ed73',
        '13df5493-ce89-4506-b44e-79cf4cd70dcf',
        '129008ef-715d-468c-afc5-ffe677749a7b',

        '07199256-1340-4456-b395-51df1728a340',
        '0734ff41-9567-4c61-9fe3-3fc4a1a4c859',
        '07f02d16-a025-4bc4-a45d-5f487c545f49',
        '080c76df-0abc-48e8-a165-8c2889728cdb',
        '080f4008-d8fa-4c36-973e-43d105fba378',
        '08892fe9-7514-4c4a-a518-ca0839ad6e0b',
        '09da55e8-7969-4f80-bbbf-1b4450339558',
        '0a048a26-4b3f-4d28-a92f-f81feacaec27',
        '0b600c41-0c8e-42da-bd16-364f3775fc08',
        '0a625f72-80fe-47aa-a5bd-4d41b98f2477',
        '0c2cf150-5293-43d7-acbf-8c1b0a67070a',
        '0c2871b9-8c04-4a17-b750-98ed1d3481f9',
        '0c282c9e-45e5-4b9c-9f8b-dd03260f66f6',
        '0c1558c3-0dbb-4bab-ac73-a60059bf29b6',
        '0c0bfec0-4f44-496f-92f9-4c6c4822693c',
        '0c026d68-32ff-40ba-8468-68c53fe83579',
        '0bfc766b-76b6-483e-affa-1502e50d9245',
        '0bf1e074-c12a-4299-9348-a7625db13fef',
        '0bedeb9c-a14f-4b8f-9278-c113f396cd29',
        '0be73303-6270-482d-be06-528c07da02fb',
        '0bd6a397-9660-4769-bc08-84047dbd5b52',
        '0bd6628a-d04c-4fd6-9dbb-78d983b590ad',
        '0bd1cdea-366c-47b6-a65d-ee7ccde0aaa9',
        '0bb97953-5e24-4874-a799-c78d1374c3f9',
        '0bb42fe5-5bca-4154-b721-d9eb8370b947',
        '0bae68bc-b465-4f11-9d52-ebf5b44b0100',
        '0b9e6ebf-18b8-453f-8457-0b62adab1827',
        '0b923d1a-d8af-497b-8482-acb8103a4eae',
        '0b49b9ac-af46-4e0a-b60e-5f1cb0db54b1',
        '0b324ba6-32f3-4ea8-b3d7-710bf86014dc',
        '0b1bec4e-9607-499c-8a34-b78f114d6314',
        '0b105b2a-e368-40ef-90a3-a4c422b915b4',
        '0adfb786-3070-498b-a0a4-ed7b9b050931',
        '0ad9d615-74b1-4537-8144-aa459ada39b6',
        '0ad01ed9-1cf8-4cad-8cae-b7cca6ddaf11',
        '0abea0c8-3398-4d26-b03d-9fb1fc9708a4',
        '0abe65fc-108e-4f9b-a8ff-29758234b9ec',
        '0aad3aa3-ec12-49a0-b7cf-548d42b0b12b',
        '0aa05d5a-81d5-497b-832c-c90c3fe73a36',
        '0a6cbc7a-613a-41c8-a52e-5b8491f898ce',
        '0a625f72-80fe-47aa-a5bd-4d41b98f2477',
        '0d2ade9f-c238-47b4-8b02-c0f2324e76be',
        '0e75222c-2d88-401b-8f36-1510d06f6675',
        '0d4aac61-f561-426e-9091-0a4a6625fcb5',
        '0df95e6f-4f59-4f45-b883-2d9ac6a3dbad',
        '0de4695f-4f6a-4b52-9a79-0a9685dc9880',
        '0dce14f8-0700-474a-8ac4-d65fe9a2263d',
        '0d7ded41-b1f0-4696-b8d4-4a97933d269c',
        '1161ca83-eb14-4f54-9db7-979743710223',
        '1406ae68-1301-4668-9e2b-eddd896d5842',
        '13cdb804-7a94-4708-b89d-03f699fccf5c',
        '1378067e-c594-41c1-995d-8f62cb257d45',
        '13ca007f-c55b-489a-9f28-f3e5baffe5c9',
        '1344f85d-7268-4d3a-b84a-a7cfb8c9e441'
    ]

    batchList = [
        'highres',
        '1310949e-14c4-40fb-a410-e9973be8f50a',
        '13c929aa-1a8b-47c0-9f34-273b45378dd0'
    ]

    for origin in batchList:
        try:
            # highResRendering(origin)
            pass
        except Exception as e:
            print(e)

    # for origin in os.listdir('./sceneviewer/results'):
    #     shutil.copy(f'./sceneviewer/results/{origin}/showPcamInset2.png', f'C:/Users/ljm/Desktop/untitled3/supp2/{origin}.png')
    # insetBatch(os.listdir('./sceneviewer/results'))
    # insetBatch(['03ff3349-3ab0-45fd-ae99-53da3334cb69'])
    # hamiltonBatch(batchList)
    renderLabelledImages()
    print("\r\n --- %s seconds --- \r\n" % (time.time() - start_time))

@app_autoView.route("/bestviewroom/<roomId>", methods=['POST'])
def bestviewroom(roomId):
    if flask.request.method == 'POST':
        try:
            roomId = int(roomId)
        except:
            return None
        pt.SAVECONFIG = False
        preloadAABBs(flask.request.json)
        pcams = autoViewOnePointPerspective(flask.request.json['rooms'][int(roomId)], flask.request.json)
        return json.dumps(pcams[0], default=sk.jsonDumpsDefault)

@app_autoView.route("/autoviewroom/<roomId>", methods=['POST'])
def autoviewroom(roomId):
    if flask.request.method == 'POST':
        try:
            roomId = int(roomId)
        except:
            return None
        pt.SAVECONFIG = False
        preloadAABBs(flask.request.json)
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

@app_autoView.route('/autoviewMapping')
def autoviewMapping():
    imgnames = os.listdir('./sceneviewer/mapping')
    ret = []
    for imgname in imgnames[0:5]:
        if '.png' not in imgname:
            continue
        t = {}
        t['img'] = imgname
        t['identifier'] = imgname.split('.')[0]
        ret.append(t)
    return json.dumps(ret)

@app_autoView.route("/autoviewimgs/<origin>/<identifier>")
def autoviewimgs(origin, identifier):
    if origin == 'mapping':
        return flask.send_from_directory(f'./sceneviewer/mapping', identifier + '.png')
    else:
        return flask.send_from_directory(f'./latentspace/autoview/{origin}', identifier + '.png')

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
