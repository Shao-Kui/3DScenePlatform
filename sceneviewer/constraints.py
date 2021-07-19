import numpy as np
from sceneviewer.utils import calCamUpVec,isObjectInSight,isPointOnVisualPlanes
import sk
from sk import ASPECT,getobjCat

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
    h['thirdObjList_rb'] = [o['obj']['modelId'] for o in res]
    if len(res) == 0:
        h['thirdHasObj_rb'] = False
        h['thirdFirstObj_rb'] = '-1'
    else:
        h['thirdHasObj_rb'] = True
        h['thirdFirstObj_rb'] = res[0]['obj']['modelId']

    # the left-bottom:
    lb = anchor - stepHeight * stepUp - stepWidth * stepRight - h['probe']
    lb /= np.linalg.norm(lb)
    res = sk.rayCastsAABBs(h['probe'], lb, room['objList'])
    h['thirdObjList_lb'] = [o['obj']['modelId'] for o in res]
    if len(res) == 0:
        h['thirdHasObj_lb'] = False
        h['thirdFirstObj_lb'] = '-1'
    else:
        h['thirdHasObj_lb'] = True
        h['thirdFirstObj_lb'] = res[0]['obj']['modelId']

    # middle:
    mid = anchor - h['probe']
    res = sk.rayCastsAABBs(h['probe'], mid, room['objList'])
    h['thirdObjList_mid'] = [o['obj']['modelId'] for o in res]
    if len(res) == 0:
        h['thirdHasObj_mid'] = False
        h['thirdFirstObj_mid'] = '-1'
    else:
        h['thirdHasObj_mid'] = True
        h['thirdFirstObj_mid'] = res[0]['obj']['modelId']

def numSeenObjs(room, h, probe, direction, floorMeta, theta, isDebug=False):
    h['numObjBeSeen'] = 0
    h['objBeSeen'] = []
    h['objBeSeenDis'] = []
    h['objBeSeenDisRelative'] = []
    for obj in room['objList']:
        if not sk.objectInDataset(obj['modelId']):
            continue
        # if room['roomId'] == 2 and h['type'] == 'threeWall_thin' and obj['modelId'] == '2327' and h['wallIndex'] == 3 and h['wallJndex'] == 1:
        #     print(isObjectInSight(obj, probe, direction, floorMeta, theta, room['objList'], True))
        if isObjectInSight(obj, probe, direction, floorMeta, theta, room['objList'], isDebug):
            h['numObjBeSeen'] += 1
            h['objBeSeen'].append(obj['modelId'])
            # further check the distance from the probe to the object. 
            normalDis = min(
                abs(sk.distanceToPlane(probe, obj['AABB']['eightPoints'][7], obj['AABB']['eightPoints'][6], obj['AABB']['eightPoints'][4])), # up
                abs(sk.distanceToPlane(probe, obj['AABB']['eightPoints'][0], obj['AABB']['eightPoints'][1], obj['AABB']['eightPoints'][3])), # down
                abs(sk.distanceToPlane(probe, obj['AABB']['eightPoints'][7], obj['AABB']['eightPoints'][4], obj['AABB']['eightPoints'][3])),
                abs(sk.distanceToPlane(probe, obj['AABB']['eightPoints'][4], obj['AABB']['eightPoints'][5], obj['AABB']['eightPoints'][0])),
                abs(sk.distanceToPlane(probe, obj['AABB']['eightPoints'][5], obj['AABB']['eightPoints'][1], obj['AABB']['eightPoints'][6])),
                abs(sk.distanceToPlane(probe, obj['AABB']['eightPoints'][6], obj['AABB']['eightPoints'][2], obj['AABB']['eightPoints'][7]))
            )
            h['objBeSeenDis'].append(normalDis)
            h['objBeSeenDisRelative'].append(normalDis / np.linalg.norm(probe - obj['AABB']['center']))

def secondNearestWallDis(h, floorMeta):
    pass

def isObjHalfCovered(h, room):
    pass
    h['isHalfCoverd'] = False
    h['halfCoverdObj'] = []
    probe = h['probe']
    direction = h['direction']
    theta = h['theta']
    objList = room['objList']
    for obj in objList:
        seenVertices = 0
        for vertex in obj['AABB']['eightPoints']:
            if isPointOnVisualPlanes(vertex, probe, direction, theta, ASPECT):
                seenVertices += 1
        # if all vertices are not seen. 
        if seenVertices == 0 and len(sk.inside_test([np.array(obj['AABB']['center']) - probe], obj['AABB']['eightPoints'])) == 0:
            h['isHalfCoverd'] = True
            h['halfCoverdObj'].append(obj['modelId'])

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
            # signpp = False
            # signpn = False
            # signnp = False
            # signnn = False
            # for vertex in obj['AABB']['eightPoints']:
            #     probeTOt = vertex - h['probe']
            #     # the projected vector w.r.t vertical and horizontal VPs. 
            #     projVPv = -np.dot(nVPv, probeTOt) * nVPv + probeTOt
            #     projVPh = -np.dot(nVPh, probeTOt) * nVPh + probeTOt
            #     ct = np.dot(h['direction'], projVPv) / np.linalg.norm(h['direction']) / np.linalg.norm(projVPv)
            #     cp = np.dot(h['direction'], projVPh) / np.linalg.norm(h['direction']) / np.linalg.norm(projVPh)
            #     one = np.dot(nVPv, probeTOt)
            #     two = np.dot(nVPh, probeTOt)
            #     if ct < cosTheta and cp < cosPhi:
            #         if one > 0 and two > 0:
            #             signpp = True
            #         elif one > 0 and two < 0:
            #             signpn = True
            #         elif one < 0 and two > 0:
            #             signnp = True
            #         else:
            #             signnn = True
            # if signpp and signpn and signnp and signnn:
            #     h['coveredBy'] = obj['modelId']
            #     h['isObjCovered'] = True
            #     return True
    return False


def tarWindoorArea2021(h, scene, floorMeta, theta, isDebug=False):
    totalWindoorArea = 0.0
    totalWindoorNum = 0.
    totalWinNum = 0.
    totalDoorNum = 0.
    totalWinArea = 0.
    totalDoorArea = 0.
    h['windoorBeSeen'] = []
    for r in scene['rooms']:
        for obj in r['objList']:
            if 'coarseSemantic' not in obj:
                continue
            if obj['coarseSemantic'] not in ['window', 'Window', 'door', 'Door']:
                continue
            if 'roomIds' in obj:
                if h['roomId'] not in obj['roomIds']:
                    continue
            else:
                if h['roomId'] != obj['roomId']:
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
            h['windoorBeSeen'].append(obj['modelId'])
    h['totalWindoorArea'] = totalWindoorArea
    h['totalWindoorNum'] = totalWindoorNum
    h['totalWinNum'] = totalWinNum
    h['totalDoorNum'] = totalDoorNum
    h['totalWinArea'] = totalWinArea
    h['totalDoorArea'] = totalDoorArea

def layoutConstraint(h, room, theta, aspect=ASPECT):
    h['layoutDirection'] = 0.
    for obj in room['objList']:
        if 'coarseSemantic' not in obj:
            continue
        if getobjCat(obj['modelId']) not in ['L-shaped Sofa', 'Kids Bed', 'King-size Bed','Wardrobe','Desk']:
            continue
        objDirection = np.array([np.sin(obj['orient']), np.cos(obj['orient'])])
        camDirection = np.array([h['direction'][0], h['direction'][2]])
        camDirection /= np.linalg.norm(camDirection, ord=2)
        h['layoutDirection'] += -np.dot(objDirection, camDirection)

def wallNormalOffset(h, floorMeta):
    direction = np.array([h['direction'][0], h['direction'][2]])
    direction /= np.linalg.norm(direction)
    if h['type'] == 'twoWallPerspective':
        res = 1.
    elif h['type'] == 'againstMidWall':
        res = np.dot(direction, floorMeta[h['wallIndex']][2:4])
    else:
        res = np.dot(direction, floorMeta[h['wallJndex']][2:4])
    h['wallNormalOffset'] = -np.arccos(res) / np.pi
