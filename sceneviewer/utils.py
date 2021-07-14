import numpy as np
import sk
from scipy.spatial.transform import Rotation as R
from shapely.geometry.polygon import Polygon, LineString, Point
from sk import ASPECT

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

def calCamUpVec(origin, target):
    # calculate the 'up' vector via the normal of plane;    
    upInit = np.array([0., 1., 0.])
    normal = target - origin
    normal = normal / np.linalg.norm(normal, ord=2)
    up = upInit - np.sum(upInit * normal) * normal
    up = up / np.linalg.norm(up, ord=2)
    return up

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

def expandWallSeg(wallIndex, floorMeta):
    wallIndexNext = ( wallIndex + 1 ) % floorMeta.shape[0]
    p1 = floorMeta[wallIndex][0:2]
    p2 = floorMeta[wallIndexNext][0:2]
    m = (p1 + p2) / 2
    DISNxt = -1
    DISPre = -1
    resPre = None
    resNxt = None
    for i in range(floorMeta.shape[0]):
        p3 = floorMeta[i][0:2]
        p4 = floorMeta[(i+1) % floorMeta.shape[0]][0:2]
        _p = twoInfLineIntersection(p1, p2, p3, p4)
        if _p is None:
            continue
        _p = np.array(_p)
        dis = np.linalg.norm(m - _p)
        if np.dot(p2 - p1, _p - m) > 0:
            if dis > DISNxt:
                DISNxt = dis
                resNxt = _p
        else:
            if dis > DISPre:
                DISPre = dis
                resPre = _p
    return resPre, resNxt

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
        if isDebug:
            print('no vertex can be seen...')
        return False
    """
    if np.dot(direction, probeTOt) <= 0:
        return False
    if np.dot(direction, probeTOt) / np.linalg.norm(direction) / np.linalg.norm(probeTOt) < cosAlpha:
        return False
    """
    if obj['coarseSemantic'] not in ['window', 'Window', 'door', 'Door']:
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
    px = ( (x1*y2-y1*x2)*(x3-x4)-(x1-x2)*(x3*y4-y3*x4) ) / D
    py = ( (x1*y2-y1*x2)*(y3-y4)-(y1-y2)*(x3*y4-y3*x4) ) / D
    return [px, py]

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

def redundancyRemove(hypotheses):
    res = []
    for i in range(0, len(hypotheses)):
        for j in range(i+1, len(hypotheses)):
            hi = hypotheses[i]
            hj = hypotheses[j]
            if np.linalg.norm(hi['probe'] - hj['probe']) < 0.01 and np.linalg.norm(hi['direction'] - hj['direction']) < 0.01:
                hypotheses[i]['toDelete'] = True
                break
    for h in hypotheses:
        if 'toDelete' not in h:
            res.append(h)
    return res
