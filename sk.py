from base64 import encode
from re import L
from typing import Union
from unittest import case
from numpy.core.fromnumeric import shape
import trimesh
import os
import json
import numpy as np
from scipy.spatial.transform import Rotation as R
import torch
from shapely.geometry.polygon import Polygon, LineString, Point
import pathTracing as pt
from datetime import datetime
from itertools import chain, combinations
import time
import random
import copy
import math
from layoutmethods.projection2d import wall_distance_orient

AABBcache = {}
ASPECT = 16 / 9
DEFAULT_FOV = 55 # 75
with open('./dataset/objCatListAliv2.json') as f:
    objCatList = json.load(f)
with open('./dataset/objListCataAliv2.json') as f:
    objListCat = json.load(f)

# code is from https://github.com/mikedh/trimesh/issues/507
def as_mesh(scene_or_mesh):
    """
    Convert a possible scene to a mesh.
    If conversion occurs, the returned mesh has only vertex and face data.
    """
    if isinstance(scene_or_mesh, trimesh.Scene):
        if len(scene_or_mesh.geometry) == 0:
            mesh = None  # empty scene
        else:
            # we lose texture information here
            # for g in scene_or_mesh.geometry.values():
            #     if g.faces.shape[1] != 3:
            #         print(g.faces.shape)
            #         print(g.vertices)
            mesh = trimesh.util.concatenate(
                tuple(trimesh.Trimesh(vertices=g.vertices, faces=g.faces)
                    for g in scene_or_mesh.geometry.values()))
    else:
        # assert(isinstance(mesh, trimesh.Trimesh))
        mesh = scene_or_mesh
    return mesh

def load_AABB(i):
    if i in AABBcache:
        return AABBcache[i]
    if os.path.exists(f'./dataset/object/{i}/{i}-AABB.json'):
        try:
            with open(f'./dataset/object/{i}/{i}-AABB.json') as f:
                AABBcache[i] = json.load(f)
            return AABBcache[i]
        except json.decoder.JSONDecodeError as e:
            print(e)
    mesh = as_mesh(trimesh.load(f'./dataset/object/{i}/{i}.obj'))
    AABB = {}
    AABB['max'] = [0,0,0]
    AABB['min'] = [0,0,0]
    AABB['max'][0] = np.max(mesh.vertices[:, 0]).tolist()
    AABB['max'][1] = np.max(mesh.vertices[:, 1]).tolist()
    AABB['max'][2] = np.max(mesh.vertices[:, 2]).tolist()
    AABB['min'][0] = np.min(mesh.vertices[:, 0]).tolist()
    AABB['min'][1] = np.min(mesh.vertices[:, 1]).tolist()
    AABB['min'][2] = np.min(mesh.vertices[:, 2]).tolist()
    AABB['vertices'] = np.array(mesh.vertices)
    with open(f'./dataset/object/{i}/{i}-AABB.json', 'w') as f:
        json.dump(AABB, f, default=jsonDumpsDefault)
    AABBcache[i] = AABB
    return AABBcache[i]

def load_AABB_glb(i, state):
    if i in AABBcache:
        return AABBcache[i+state]
    if os.path.exists(f'./static/dataset/object/{i}/{state}-AABB.json'):
        try:
            with open(f'./static/dataset/object/{i}/{state}-AABB.json') as f:
                AABBcache[i+state] = json.load(f)
            return AABBcache[i+state]
        except json.decoder.JSONDecodeError as e:
            print(e)
    mesh = as_mesh(trimesh.load(f'./static/dataset/object/{i}/{state}.obj'))
    AABB = {}
    AABB['max'] = [0,0,0]
    AABB['min'] = [0,0,0]
    AABB['max'][0] = np.max(mesh.vertices[:, 0]).tolist()
    AABB['max'][1] = np.max(mesh.vertices[:, 1]).tolist()
    AABB['max'][2] = np.max(mesh.vertices[:, 2]).tolist()
    AABB['min'][0] = np.min(mesh.vertices[:, 0]).tolist()
    AABB['min'][1] = np.min(mesh.vertices[:, 1]).tolist()
    AABB['min'][2] = np.min(mesh.vertices[:, 2]).tolist()
    AABB['vertices'] = np.array(mesh.vertices)
    with open(f'./static/dataset/object/{i}/{state}-AABB.json', 'w') as f:
        json.dump(AABB, f, default=jsonDumpsDefault)
    AABBcache[i+state] = AABB
    return AABBcache[i+state]

def preloadAABB(obj):
    if 'startState' in obj:
        AABB = load_AABB_glb(obj['modelId'], obj['startState'])
    elif objectInDataset(obj['modelId']):
        AABB = load_AABB(obj['modelId'])
        if 'coarseSemantic' not in obj:
            obj['coarseSemantic'] = getobjCat(obj['modelId'])
    elif 'format' in obj and obj['format'] == 'sfy':
        AABB = obj['bbox']
    else:
        if 'coarseSemantic' in obj and obj['coarseSemantic'] in ['window', 'Window', 'door', 'Door']:
            AABB = obj['bbox']
        else:
            return
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

def preloadAABBs(scene):
    if 'PerspectiveCamera' not in scene:
        scene['PerspectiveCamera'] = {}
        scene['PerspectiveCamera']['fov'] = DEFAULT_FOV
    if 'canvas' not in scene:
        scene['canvas'] = {}
    for room in scene['rooms']:
        for obj in room['objList']:
            preloadAABB(obj)

def assignRoomIds(scenejson):
    for roomId, room in zip(range(len(scenejson['rooms'])), scenejson['rooms']):
        room['roomId'] = roomId
        for obj in room['objList']:
            obj['roomId'] = roomId

# https://stackoverflow.com/questions/1482308/how-to-get-all-subsets-of-a-set-powerset
def powerset(iterable):
    "powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))

def getWallHeight(meshPath):
    mesh = as_mesh(trimesh.load(meshPath))
    return np.max(mesh.vertices[:, 1]).tolist()

def getMeshVertices(meshPath):
    mesh = as_mesh(trimesh.load(meshPath))
    return mesh.vertices

def objectInDataset(modelId):
    if modelId == "":
        return False
    if os.path.exists(f'./dataset/object/{modelId}/'):
        return True
    else:
        return False

def jsonDumpsDefault(obj):
    if type(obj).__module__ == np.__name__:
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj.item()
    raise TypeError('Unknown type:', type(obj))

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

def isLineIntersectsWithEdges(line, floorMeta, isDebug=False):
    for i in range(floorMeta.shape[0]):
        l = LineString((floorMeta[i][0:2], floorMeta[(i+1)%floorMeta.shape[0]][0:2]))
        if isDebug:
            print(line, l, line.crosses(l))
        if line.crosses(l):
            return True
    return False

def checkClockwise(points):
    res = 0
    for i in range(len(points)):
        a = np.array(points[i])
        b = np.array(points[(i+1)%len(points)])
        c = np.array(points[(i+2)%len(points)])
        res += 0.5 * ((b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1]))
    if res > 0:
        return True
    else:
        return False

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

def generateRoomNormals(roomShape):
    wallSecIndices = np.arange(1, len(roomShape)).tolist() + [0]
    rv = np.array(roomShape)[:] - np.array(roomShape)[wallSecIndices]
    normals = rv[:, [1,0]]
    normals[:, 1] = -normals[:, 1]
    roomNorm = normals.tolist()
    return roomNorm

def regularizeRoomShape(roomShape):
    for i in range(len(roomShape)):
        p = roomShape[i]
        p1 = roomShape[(i-1)%len(roomShape)]
        p2 = roomShape[(i+1)%len(roomShape)]
        value = toLeftTest(p, p1, p2) * toLeftTest(p1, p, p2) * toLeftTest(p2, p, p1)
        # print('regularizeRoomShape', p, p1, p2, value, toLeftTest(p, p1, p2), toLeftTest(p1, p, p2), toLeftTest(p2, p, p1))
        if abs(value) < 0.0000001:
            newroomshape = []
            for j in range(len(roomShape)):
                if j == i:
                    continue
                newroomshape.append(roomShape[j])
            return regularizeRoomShape(newroomshape)
    for i in range(len(roomShape)):
        p = roomShape[i]
        p1 = roomShape[(i-1)%len(roomShape)]
        if np.linalg.norm(np.array(p) - np.array(p1)) < 0.0000001:
            newroomshape = []
            for j in range(len(roomShape)):
                if j == i:
                    continue
                newroomshape.append(roomShape[j])
            return regularizeRoomShape(newroomshape)
    return roomShape

def toLeftTest(p, p1, p2):
    # if p is to the left, returns a value greater than 0; 
    return (p[0] - p1[0])*(p2[1] - p1[1]) - (p[1] - p1[1])*(p2[0] - p1[0])

def isTwoLineSegCross(p1, p2, p3, p4):
    l1 = LineString((p1, p2))
    l2 = LineString((p3, p4))
    return l1.crosses(l2)

def isTwoLineSegIntersect(p1, p2, p3, p4):
    l1 = LineString((p1, p2))
    l2 = LineString((p3, p4))
    return l1.intersects(l2)

def pointToLineDistance(point, p1, p2):
    return np.linalg.norm(np.cross(p2-p1, p1-point)) / np.linalg.norm(p2-p1)

def isPointBetweenLineSeg(point, p1, p2):
    s = np.dot(p2 - p1, point - p1) / np.linalg.norm(p2 - p1)
    if 0 < s and s < np.linalg.norm(p2 - p1):
        return True
    else:
        return False

def isSegIntersectsWithPlane(p, norm, l0, l1):
    # we assume that the points and norms are in 3D;
    # We assuem that the vectors are in Numpy.ndarray form; 
    dot1 = np.dot(l0 - p, norm)
    dot2 = np.dot(l1 - p, norm)
    if dot1 * dot2 <= 0:
        return True
    else:
        return False

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

def isPointProjectedToLineSeg(p, p1, p2):
    p = np.array(p)
    p1 = np.array(p1)
    p2 = np.array(p2)
    value = np.dot(p2-p1, p2-p)/np.linalg.norm(p2-p1)
    value /= np.linalg.norm(p2-p1)
    if value <= 0.00001:
        return False
    if value >= 1.00001:
        return False
    return True

def pointProjectedToPlane(p, normal, startPoint):
    normal = normal / np.linalg.norm(normal)
    distanceToPlane = -np.dot(p - startPoint, normal)
    projectedP = p + distanceToPlane * normal
    return projectedP

def distanceToPlane(p, p1, p2, p3):
    normal = np.cross(p2 - p1, p3 - p1)
    normal = normal / np.linalg.norm(normal)
    return np.dot(p - p1, normal)

def rogrigues(v, k, theta):
    # returns v_rot. 
    return v * np.cos(theta) + np.cross(k, v) * np.sin(theta)

def rayCastsAABBs(probe, direction, objList):
    """
    Note that before calling this api, all the objects should have corresponding AABB. 
    """
    res = []
    for o in objList:
        if not objectInDataset(o['modelId']):
            continue
        probeToO = np.array(o['AABB']['center']) - probe
        magnitute = np.dot(probeToO, direction) / np.linalg.norm(direction)
        if magnitute <= 0:
            continue
        nP = probe + magnitute * (direction / np.linalg.norm(direction))
        if len(inside_test(nP.reshape(1, 3), o['AABB']['eightPoints'])) == 0:
            res.append({
                'obj': o,
                'dis': magnitute,
            })
    res.sort(key=lambda x : x['dis'])
    return res

def roomDiameter(floorMeta):
    floorMeta = floorMeta[:, 0:2]
    return np.max(np.linalg.norm(floorMeta[:, None, :] - floorMeta, axis=2))

import threading
class BaseThread(threading.Thread):
    def __init__(self, method_args=None, callback=None, callback_args=None, *args, **kwargs):
        target = kwargs.pop('target')
        super(BaseThread, self).__init__(target=self.target_with_callback, *args, **kwargs)
        self.method_args = method_args
        self.callback = callback
        self.method = target
        self.callback_args = callback_args

    def target_with_callback(self):
        self.method(*self.method_args)
        if self.callback is not None:
            self.callback(*self.callback_args)

def getobjCat(modelId):
    if modelId in objCatList:
        if len(objCatList[modelId]) > 0:
            return objCatList[modelId][0]
        else:
            return "Unknown Category"
    else:
        return "Unknown Category"

with open('./dataset/objCatListLG.json') as f:
    objCatListLG = json.load(f)
def getObjCatsLG(modelId):
    if modelId in objCatListLG:
        if len(objCatListLG[modelId]) > 0:
            return objCatListLG[modelId]
        else:
            return ["Unknown Category"]
    else:
        return ["Unknown Category"]

def rotate_pos_prior(points, angle):
    result = points.clone()
    result[:, 0] = torch.cos(angle) * points[:, 0] + torch.sin(angle) * points[:, 2]
    result[:, 2] = -torch.sin(angle) * points[:, 0] + torch.cos(angle) * points[:, 2]
    return result

def rotate_bb_local_para(points, angle, scale):
    result = points.clone()
    scaled = points.clone()
    scaled = scaled * scale
    result[:, 0] = torch.cos(angle) * scaled[:, 0] + torch.sin(angle) * scaled[:, 1]
    result[:, 1] = -torch.sin(angle) * scaled[:, 0] + torch.cos(angle) * scaled[:, 1]
    return result

def findNearestWalls(shape, p, isOrient=True):
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
    if len(_indicesList) < 1:
        print('Fatal Error! None-Closed Curve. ')
    # calculate normals:
    # calculate the wall orient
    wn = (shape - shapeEnd)[:, [1,0]]
    wn[:, 1] = -wn[:, 1]
    if isOrient:
        orients = np.arctan2(wn[:, 0], wn[:, 1])
    else:
        orients = wn
    return _indicesList, distances, orients

def extractGroup(objList, dom, modelIDs, originIndex):
    subs = []
    subPriors = []
    for obj in objList:
        if 'modelId' not in obj:
            continue
        if not objectInDataset(obj['modelId']):
            continue
        if obj['modelId'] == dom:
            domObj = obj
        if obj['modelId'] in modelIDs:
            subs.append(obj)
    # sub-objects: 
    for obj in subs:
        # the relative transtormation should be sth like an identical matrix. 
        relativeTranslate = np.array(obj['translate']) - np.array(domObj['translate'])
        relativeTranslate = R.from_euler('y', -domObj['orient'], degrees=False).as_matrix() @ relativeTranslate # rotate this translation
        relativeTranslate = relativeTranslate / np.array(domObj['scale'])
        relativeScale = np.array(obj['scale']) / np.array(domObj['scale'])
        relativeOrient = np.array(obj['orient']) - np.array(domObj['orient'])
        subPriors.append({
            'sub': obj['modelId'],
            'translate': relativeTranslate.tolist(),
            'orient': relativeOrient.tolist(),
            'scale': relativeScale.tolist()
        })
    if len(subPriors) > 25:
        subSetOfsubPriors = [subPriors]
    else:
        subSetOfsubPriors = list(powerset(subPriors))
        subSetOfsubPriors = subSetOfsubPriors[1:len(subSetOfsubPriors)]
    print(dom, modelIDs, originIndex, len(subSetOfsubPriors))
    if len(subSetOfsubPriors) > 75:
        subSetOfsubPriors = random.sample(subSetOfsubPriors, 75) + subSetOfsubPriors[len(subSetOfsubPriors)-1:len(subSetOfsubPriors)]
    if len(subSetOfsubPriors) == 0:
        return [], []
    res = []
    for subSet in subSetOfsubPriors:
        if len(subPriors) == len(list(subSet)):
            originConfig = [generateGroup(list(subSet), dom, [1,1,1], originIndex, True)]
            res += originConfig
        else:
            res += [generateGroup(list(subSet), dom, [1,1,1], originIndex, False)]
        res += [
            generateGroup(list(subSet), dom, [-1,1,1], originIndex, False), 
            generateGroup(list(subSet), dom, [-1,1,-1], originIndex, False), 
            generateGroup(list(subSet), dom, [1,1,-1], originIndex, False)
        ]
    return res, originConfig

def calCamUpVec(origin, target):
    # calculate the 'up' vector via the normal of plane 
    upInit = np.array([0., 1., 0.])
    normal = target - origin
    normal = normal / np.linalg.norm(normal, ord=2)
    up = upInit - np.sum(upInit * normal) * normal
    up = up / np.linalg.norm(up, ord=2)
    return up

def cgRender(newObjList, ma, mi, originIndex):
    now = datetime.now()
    dt_string = now.strftime("%Y-%m-%d %H-%M-%S")
    casename = f"{originIndex}-{'-'.join(map(lambda x: x['modelId'], newObjList))}"
    if len(casename) > 130:
        casename = casename[0:130] + 'c'
    scenejson = {'rooms': [{'objList': newObjList, 'modelId': 'null'}], "PerspectiveCamera": {}, 'origin': casename}
    # if os.path.exists(f"./layoutmethods/cgseries/{CURRENT_domID}/{CURRENT_seriesName}/{casename}.png"):
    #     return
    print(f"Rendring - {CURRENT_domID}/{CURRENT_seriesName}/{casename}.png")
    diag_length = np.linalg.norm(ma - mi) * 0.69
    center = (ma + mi)/2
    # [0.7946, 0.1876, 0.5774]
    # [-0.3035, 0.1876, 0.9342]
    # [-0.1876, 0.7947, 0.5774]
    # [0.4911, 0.7947, 0.3568]
    origin = np.array([0.4911, 0.7947, 0.3568]) * diag_length + center
    scenejson["PerspectiveCamera"]["origin"] = origin.tolist()
    scenejson["PerspectiveCamera"]["target"] = center.tolist()
    scenejson["PerspectiveCamera"]["up"] = calCamUpVec(np.array(scenejson["PerspectiveCamera"]["origin"]), np.array(scenejson["PerspectiveCamera"]["target"])).tolist()
    scenejson["PerspectiveCamera"]["fov"] = DEFAULT_FOV
    pt.emitter = 'sky'
    try:
        pt.pathTracing(scenejson, 16, f"./layoutmethods/cgseries/{CURRENT_domID}/{CURRENT_seriesName}/{casename}.png")
    except Exception as e:
        print(e)

def generateGroup(subPriors, domModelId, domScale=[1,1,1], originIndex=-1, isRender=False):
    res = {
        'subPriors': subPriors.copy(),
        'objects': [],
        'domScale': domScale
    }
    bbs = np.zeros(shape=(0,3))
    domObj = {'translate': [0,0,0], 'rotate': [0,0,0], 'orient': 0, 'scale': domScale, 'modelId': domModelId}
    preloadAABB(domObj)
    bbs = np.vstack((bbs, domObj['AABB']['eightPoints']))
    newObjList = [domObj]
    objPolyUnion = Polygon(domObj['AABB']['eightPoints'][0:4][:,[0,2]])
    for subPrior in subPriors:
        obj = {
            'translate': (np.array(subPrior['translate']) * np.array(domScale)).tolist(),
            'rotate': [0,subPrior['orient'],0],
            'scale': (np.array(subPrior['scale']) * np.array(domScale)).tolist(),
            'modelId': subPrior['sub']
        }
        preloadAABB(obj)
        bbs = np.vstack((bbs, obj['AABB']['eightPoints']))
        newObjList.append(obj)
        objPolyUnion = objPolyUnion.union(Polygon(obj['AABB']['eightPoints'][0:4][:,[0,2]]))
        res['objects'].append(obj['modelId'])
    ma = np.max(bbs, axis=0)
    mi = np.min(bbs, axis=0)
    gbb = np.array([[ma[0], ma[2]], [mi[0], ma[2]], [mi[0], mi[2]], [ma[0], mi[2]]])
    indicesList, distances, orients = findNearestWalls(gbb, np.array(domObj['translate'])[[0, 2]])
    # anchor: 
    res['anchorDis'] = distances[indicesList[0]]
    res['anchorOri'] = domObj['orient'] - orients[indicesList[0]]
    res['anchorOri'] = np.arctan2(np.sin(res['anchorOri']), np.cos(res['anchorOri']))
    # depth & left & right: 
    res['depthDis'] = distances[(indicesList[0]+2)%4]
    res['leftDis'] = distances[(indicesList[0]+1)%4]
    res['rightDis'] = distances[(indicesList[0]+3)%4]
    # constraints: area & #objects & space utilization... :
    res['area'] = (ma[0] - mi[0]) * (ma[2] - mi[2])
    res['objNum'] = len(res['objects'])
    res['catNum'] = len(list(dict.fromkeys(res['objects'])))
    res['dpAnchor'] = 0.
    res['dpLeft'] = 0.
    res['dpRight'] = 0.
    res['dpDepth'] = 0.
    for o in newObjList:
        if getobjCat(o['modelId']) in ['Shelf', 'Children Cabinet', 'Wine Cabinet', 'Bookcase / jewelry Armoire', 'Drawer Chest / Corner cabinet', 'Wardrobe', 'Dressing Table']:
            il, _d, _o = findNearestWalls(gbb, np.array(o['translate'])[[0, 2]])
            if il[0] == indicesList[0]:
                res['dpAnchor'] = 1.
            if il[0] == (indicesList[0]+1)%4:
                res['dpLeft'] = 1.
            if il[0] == (indicesList[0]+3)%4:
                res['dpRight'] = 1.
            if il[0] == (indicesList[0]+2)%4:
                res['dpDepth'] = 1.
    res['spaceUtil'] = objPolyUnion.area / res['area']
    res['originCG'] = originIndex
    # render groups: 
    if isRender:
        cgRender(newObjList, ma, mi, originIndex)
    return res

def getObjectsUpperLimit(l, k):
    l = l.copy()
    k = k.copy()
    res = []
    for i in k:
        if i in l:
            l.remove(i)
        res.append(i)
    return res + l

class cgDiff:
    def __init__(self, results):
        with open('./dataset/objCatListAliv2.json') as f:
            self.objCat = json.load(f)
        self.configs = results['configs']
        self.nConfigs = len(self.configs)
        domID = results['domID']
        self.objects = []
        for G in range(self.nConfigs):
            self.objects.append([domID] + self.configs[G]['objects'])

        maxObjNum = 20
        self.neighbors = []
        for G, cfg in enumerate(self.configs):
            nObj = len(self.objects[G])
            maxObjNum = max(maxObjNum, nObj)
            domScale = np.array(cfg['domScale'])
            edges = []
            for i in range(nObj-1):
                e = cfg['subPriors'][i]['translate'] * domScale
                e /= np.linalg.norm(e)
                edges.append(e)
            neighborG = [[[i+1, edges[i]] for i in range(nObj-1)]]
            for i in range(nObj-1):
                neighborG.append([[0, edges[i]]])
            self.neighbors.append(neighborG)

        self.preComputedEdgeKernel = np.zeros((self.nConfigs, self.nConfigs, maxObjNum, maxObjNum, maxObjNum, maxObjNum))
        self.skip = np.ones((self.nConfigs, self.nConfigs, maxObjNum, maxObjNum), dtype=bool)
        for Ga in range(self.nConfigs):
            for Gb in range(self.nConfigs):
                for r in range(len(self.objects[Ga])):
                    for s in range(len(self.objects[Gb])):
                        edgeKernel = np.zeros((maxObjNum, maxObjNum))
                        for rprime, e in self.neighbors[Ga][r]:
                            for sprime, f in self.neighbors[Gb][s]:
                                k_edge = np.dot(e, f)
                                if k_edge > 1e-6:
                                    edgeKernel[rprime, sprime] = k_edge
                                    self.skip[Ga, Gb, r, s] = False
                        self.preComputedEdgeKernel[Ga, Gb, r, s] = edgeKernel

        self.freq = np.zeros((self.nConfigs, maxObjNum))
        for G in range(self.nConfigs):
            for index, na in enumerate(self.objects[G]):
                for nb in self.objects[G]:
                    self.freq[G,index] += self.modelKernel(na, nb)
                self.freq[G,index] = 1 / self.freq[G,index]
                
        maxP = 5
        self.dp = np.zeros((maxP, self.nConfigs, self.nConfigs, maxObjNum, maxObjNum))
        for Ga in range(self.nConfigs):
            for Gb in range(self.nConfigs):
                for r in range(len(self.objects[Ga])):
                    for s in range(len(self.objects[Gb])):
                        self.dp[0, Ga, Gb, r, s] = self.finalModelKernel(Ga, Gb, r, s)
                        
        for p in range(1, maxP):
            for Ga in range(self.nConfigs):
                for Gb in range(self.nConfigs):
                    for r in range(len(self.objects[Ga])):
                        for s in range(len(self.objects[Gb])):
                            if self.dp[0, Ga, Gb, r, s] == 0 or self.skip[Ga, Gb, r, s]:
                                continue
                            self.dp[p, Ga, Gb, r, s] = self.dp[0, Ga, Gb, r, s] * np.sum(self.preComputedEdgeKernel[Ga, Gb, r, s] * self.dp[p-1, Ga, Gb])
                         
        self.graphKernel = np.sum(self.dp, axis=(-2, -1))
                        
        self.normalizedGraphKernel = np.zeros((maxP, self.nConfigs, self.nConfigs))
        for p in range(maxP):
            for Ga in range(self.nConfigs):
                for Gb in range(self.nConfigs):
                    self.normalizedGraphKernel[p, Ga, Gb] = self.graphKernel[p, Ga, Gb] / max(self.graphKernel[p, Ga, Ga], self.graphKernel[p, Gb, Gb])

        self.graphDistance = np.sqrt(2 - 2 * np.clip(self.normalizedGraphKernel, None, 1.0))
        results['similarity'] = self.graphDistance.tolist()

    def k_iden(self, r, s):
        # 1 if geo & texture else 0
        return r == s

    def k_tag(self, r, s):
        if(r not in self.objCat or s not in self.objCat):
            return 0
        if len(self.objCat[r]) == 0 or len(self.objCat[s]) == 0:
            return 0
        rCat = self.objCat[r][0].lower()
        sCat = self.objCat[s][0].lower()
        if rCat == sCat:
            return 1
        elif 'chair' in rCat and 'chair' in sCat:
            return 0.5
        elif 'sofa' in rCat and 'sofa' in sCat:
            return 0.5
        return 0

    def k_geo(self, r, s):
        return self.k_iden(r, s)
        # TODO: 3D Zernike descriptor
        # n = 100
        # drs = zernikeDistance(r, s)
        # k = 2 * drs / min(nthZernikeDistance(r, n), nthZernikeDistance(s, n))
        # return math.exp(-(k ** 2))

    def modelKernel(self, r, s):
        k_node = 0.1 * self.k_iden(r, s) + 0.6 * self.k_tag(r, s) + 0.3 * self.k_geo(r, s)
        return k_node

    def finalModelKernel(self, Ga, Gb, r, s):
        k_node = self.freq[Ga, r] * self.freq[Gb, s] * self.modelKernel(self.objects[Ga][r], self.objects[Gb][s])
        if k_node < 1e-6:
            k_node = 0
        return k_node

CURRENT_seriesName = None
CURRENT_domID = None
def cgs(domID, subIDs, seriesName):
    pt.SAVECONFIG = False
    global CURRENT_seriesName
    global CURRENT_domID
    CURRENT_seriesName = seriesName
    CURRENT_domID = domID
    filenames = os.listdir(f'./layoutmethods/cgseries/{domID}/{seriesName}') # init
    results = {
        'domID': domID,
        'anchorOris': [],
        'anchorDises': [],
        'depthDises': [],
        'leftDises': [],
        'rightDises': [],
        'areas': [],
        'objNums': [],
        'catNums': [],
        'spaceUtils': [],
        'dpAnchors' : [],
        'dpLefts' : [],
        'dpRights' : [],
        'dpDepths' : [],
        'originCGs': [],
        'configs': [],
        # 'originConfigs': [],
        'involvedObjects': [],
        'enabled': False
    }
    if subIDs is None:
        subIDs = []
        for filename in filenames:
            if '.json' not in filename:
                continue
            with open(f'./layoutmethods/cgseries/{domID}/{seriesName}/{filename}') as f:
                scenejson = json.load(f)
            if 'rooms' not in scenejson:
                continue
            for obj in scenejson['rooms'][0]['objList']:
                if obj['modelId'] != domID and obj['modelId'] not in subIDs:
                    subIDs.append(obj['modelId'])
    cgIndex = 0
    originConfigs = []
    for filename in filenames:
        if '.json' not in filename:
            continue
        try:
            with open(f'./layoutmethods/cgseries/{domID}/{seriesName}/{filename}') as f:
                scenejson = json.load(f)
        except:
            continue
        if 'rooms' not in scenejson:
            continue
        preloadAABBs(scenejson)
        configs, originConfig = extractGroup(scenejson['rooms'][0]['objList'], domID, subIDs, cgIndex) # e.g., '7644' ['3699', '7836', '2740', '2565']
        results['configs'] += configs
        originConfigs += originConfig
        cgIndex += 1
    resultOrigin = {'domID': results['domID'], 'configs': originConfigs}
    cgDiff(resultOrigin)
    resultOrigin['similarity'] = np.array(resultOrigin['similarity'])
    # results['diffMatrix'] = resultOrigin['similarity'][(resultOrigin['similarity'].shape[0]-1)].tolist()
    results['diffMatrix'] = (resultOrigin['similarity'][1] / np.max(resultOrigin['similarity'][1])).tolist()
    for config in results['configs']:
        results['anchorOris'].append(config['anchorOri'])
        results['anchorDises'].append(config['anchorDis'])
        results['depthDises'].append(config['depthDis'])
        results['leftDises'].append(config['leftDis'])
        results['rightDises'].append(config['rightDis'])
        results['objNums'].append(config['objNum'])
        results['areas'].append(config['area'])
        results['spaceUtils'].append(config['spaceUtil'])
        results['catNums'].append(config['catNum'])
        results['dpAnchors'].append(config['dpAnchor'])
        results['dpLefts'].append(config['dpLeft'])
        results['dpRights'].append(config['dpRight'])
        results['dpDepths'].append(config['dpDepth'])
        results['originCGs'].append(config['originCG'])
        results['involvedObjects'] = getObjectsUpperLimit(results['involvedObjects'], config['objects'])
    results['areas'] = listNormalization(results['areas'])
    results['objNums'] = listNormalization(results['objNums'])
    results['catNums'] = listNormalization(results['catNums'])
    results['spaceUtils'] = listNormalization(results['spaceUtils'])
    results['diffMatrix'] = listNormalization(results['diffMatrix'])
    with open(f'./layoutmethods/cgseries/{results["domID"]}/{seriesName}/result.json', 'w') as f:
        json.dump(results, f)

def listNormalization(l):
    l = np.array(l)
    l = l - np.min(l)
    l = l / (np.max(l) + 0.00005)
    return l.tolist()

def patternRefine():
    ppris = os.listdir('./latentspace/pos-orient-4')
    for ppri in ppris:
        modelId = ppri.split('.')[0]
        if getobjCat(modelId) == "Unknown Category":
            continue
        try:
            bb = load_AABB(modelId)
            with open(f'./latentspace/pos-orient-4/{ppri}') as f:
                pri = json.load(f)
        except:
            continue
        for cat in pri:
            if getobjCat(modelId) == 'Coffee Table' and cat == 'Three-seat / Multi-seat Sofa':
                pri[cat] = []
                zlength = bb['max'][2]-bb['min'][2]
                xlength = bb['max'][0]-bb['min'][0]
                # -z
                temp = -np.arange(zlength * 1.5, zlength * 3, 0.2)
                l = temp.shape[0]
                pri[cat] += np.hstack((np.full((l, 1),0), np.full((l, 1),0), temp.reshape(l, 1), np.full((l, 1),0))).tolist()
                # z
                temp = np.arange(zlength * 1.5, zlength * 3, 0.2)
                l = temp.shape[0]
                pri[cat] += np.hstack((np.full((l, 1),0), np.full((l, 1),0), temp.reshape(l, 1), np.full((l, 1),np.pi))).tolist()
                # -x
                temp = -np.arange(xlength * 1.5, xlength * 3, 0.2)
                l = temp.shape[0]
                pri[cat] += np.hstack((temp.reshape(l, 1), np.full((l, 1),0), np.full((l, 1),0), np.full((l, 1),np.pi/2))).tolist()
                # x
                temp = np.arange(xlength * 1.5, xlength * 3, 0.2)
                l = temp.shape[0]
                pri[cat] += np.hstack((temp.reshape(l, 1), np.full((l, 1),0), np.full((l, 1),0), np.full((l, 1),-np.pi/2))).tolist()       
            if getobjCat(modelId) == 'Coffee Table' and cat == 'TV Stand':
                pri[cat] = []
                zlength = bb['max'][2]-bb['min'][2]
                xlength = bb['max'][0]-bb['min'][0]
                # -z
                temp = -np.arange(zlength * 1.5, zlength * 4, 0.2)
                l = temp.shape[0]
                pri[cat] += np.hstack((np.full((l, 1),0), np.full((l, 1),0), temp.reshape(l, 1), np.full((l, 1),0))).tolist()
                # z
                temp = np.arange(zlength * 1.5, zlength * 4, 0.2)
                l = temp.shape[0]
                pri[cat] += np.hstack((np.full((l, 1),0), np.full((l, 1),0), temp.reshape(l, 1), np.full((l, 1),np.pi))).tolist()   
            with open(f'./latentspace/pos-orient-4/{ppri}', 'w') as f:
                json.dump(pri, f)

def cgsBatch():
    domObjectNames = os.listdir('./layoutmethods/cgseries')
    for domObjectName in domObjectNames:
        seriesNames = os.listdir(f'./layoutmethods/cgseries/{domObjectName}')
        for serseriesName in seriesNames:
            if os.path.exists(f'./layoutmethods/cgseries/{domObjectName}/{serseriesName}/result.json'):
                continue
            cgs(domObjectName, None, serseriesName)

def cgsUSRenderBatch():
    root = 'H:/D3UserStudy/static/planner'
    pt.SAVECONFIG = True
    pt.emitter = 'sky'
    subjectNames = os.listdir(root)
    with open('H:/D3UserStudy/static/quiz/quizplanner-template.json') as f:
        quizplanner = json.load(f)
        questionTemp = quizplanner['quizlist'][0]
        quizplanner['quizlist'] = []
    qid = 0
    for sname in subjectNames:
        fileNames = os.listdir(f'{root}/{sname}/')
        renderlist = []
        for fname in fileNames:
            if '.json' in fname:
                try:
                    with open(f'{root}/{sname}/{fname}') as f:
                        sj = json.load(f)
                        sj["originFname"] = fname.split(".")[0]
                        renderlist.append(sj)
                except:
                    continue
        if len(renderlist) == 0:
            continue
        for sj in renderlist:
            sj['PerspectiveCamera'] = renderlist[0]['PerspectiveCamera']
            sj["canvas"] = {"width": 1920,"height": 1080}
            print('Rendrring ' + f'{root}/{sname}/pt{sj["originFname"]}.png')
            if not os.path.exists(f'{root}/{sname}/pt{sj["originFname"]}.png'):
            # if True:
                pt.pathTracing(sj, 64, f'{root}/{sname}/pt{sj["originFname"]}.png')
        if len(renderlist) == 3:
            quizplanner['quizlist'].append(questionTemp.copy())
            quizplanner['quizlist'][qid]['userName'] = sname
            quizplanner['quizlist'][qid]['id'] = qid
            qid += 1
    with open('H:/D3UserStudy/static/quiz/quizplanner2023.json', 'w') as f:
        json.dump(quizplanner, f)

def analyzeAnswerPlanner():
    jsonNames = os.listdir('H:/D3UserStudy/answer-planner')
    tra = 0
    our = 0
    nts = 0
    for jName in jsonNames:
        with open(f'H:/D3UserStudy/answer-planner/{jName}', encoding='utf-8') as f:
            j = json.load(f)
        for q in j['quizlist']:
            if q['answer'] == 1:
                tra += 1
            if q['answer'] == 2:
                our += 1
            if q['answer'] == 'notsure':
                nts += 1
    print('Tra: ' + str(tra / (tra + our + nts)))
    print('Our: ' + str(our / (tra + our + nts)))
    print('Nts: ' + str(nts / (tra + our + nts)))

def renderGLBbatch():
    objlist = os.listdir('./static/dataset/object/')
    for objname in objlist:
        print(objname)
        if os.path.exists(f'./static/dataset/object/{objname}/render20origin/render-origin-0.png'):
            continue
        filelist = os.listdir(f'./static/dataset/object/{objname}')
        for fname in filelist:
            if '.obj' in fname:
                try:
                    renderModel20(objname, 'glb', fname.split('.')[0])
                except Exception as e:
                    print(e)

icosavn = np.loadtxt("./assets/icosavn", dtype=float)
# icosavn = torch.from_numpy(icosavn).float().to("cuda")
def renderModel20(objname, format='obj', stateName='origin'):
    RENDER20DIR = f'./dataset/object/{objname}/render20'
    OBJECTDIR = f'./dataset/object/{objname}/{objname}.obj'
    RENDERNAME = f'{RENDER20DIR}/render-{objname}'
    if format == 'glb':
        RENDER20DIR = f'./static/dataset/object/{objname}/render20{stateName}'
        OBJECTDIR = f'./static/dataset/object/{objname}/{stateName}.obj'
        RENDERNAME = f'{RENDER20DIR}/render-{stateName}'
    pt.SAVECONFIG = False
    obj = {'translate': [0,0,0],'rotate': [0,0,0],'scale': [1,1,1],'modelId': objname, 'startState': stateName,'format': format}
    if format == 'obj':
        AABB = load_AABB(objname)
    elif format == 'glb':
        AABB = load_AABB_glb(objname, stateName)
    objpath = OBJECTDIR
    mesh = as_mesh(trimesh.load(objpath))
    vertices = np.array(mesh.vertices)
    max_p = np.array(AABB['max'])
    min_p = np.array(AABB['min'])
    diag_length = np.linalg.norm(max_p - min_p)
    center = np.mean(vertices, axis=0)
    camera_positions = icosavn * diag_length + center
    with open('./examples/initth.json') as f:
        scenejson = json.load(f)
    for i, camera_position in zip(range(len(camera_positions)), camera_positions):
        scenejson = {'id': 'Ghost', 'rooms': [{'objList': [obj], 'modelId': 'null'}], "PerspectiveCamera": {}, 'origin': ''}
        scenejson['canvas'] = {'height': 384, 'width': 384}
        origin = camera_position
        scenejson["PerspectiveCamera"]["origin"] = origin.tolist()
        scenejson["PerspectiveCamera"]["target"] = center.tolist()
        scenejson["PerspectiveCamera"]["up"] = [0,1,0]
        scenejson["PerspectiveCamera"]["fov"] = DEFAULT_FOV
        if not os.path.exists(RENDER20DIR):
            os.makedirs(RENDER20DIR)
        pt.pathTracing(scenejson, 16, f'{RENDERNAME}-{i}.png')

def renderAnimationNodeResults(sjName):
    pt.SAVECONFIG = False
    pt.emitter = 'sky'
    pt.USENEWWALL = True
    pt.CAMGEN = True
    with open(f'./static/dataset/infiniteLayout/{sjName}.json') as f:
        sj = json.load(f)
    taID = sj['rooms'][0]['totalAnimaID']
    with open(f'./static/dataset/infiniteLayout/{taID}.json') as f:
        animationFile = json.load(f)
    if not os.path.exists(f'./static/dataset/infiniteLayout/{taID}img/'):
        os.makedirs(f'./static/dataset/infiniteLayout/{taID}img/')
    for origin_node in animationFile['index']:
        for tar in animationFile['index'][origin_node]:
            if not tar['anim_forward']:
                continue
            target_node = tar['target_node']
            with open(f'./static/dataset/infiniteLayout/{taID}/{tar["anim_id"]}.json') as f:
                animationjson = json.load(f)
            if not os.path.exists(f'./static/dataset/infiniteLayout/{taID}img/{origin_node}.png'):
                scenejson = copy.deepcopy(sj)
                for i in range(len(animationjson['actions'])-1, -1, -1):
                    for object in scenejson['rooms'][0]['objList']:
                        if 'sforder' not in object:
                            continue
                        if object['sforder'] == i:
                            break
                    for seq in reversed(animationjson['actions'][i]):
                        for a in reversed(seq):
                            if a['action'] == 'move':
                                object['translate'] = a['p1']
                            if a['action'] == 'rotate':
                                object['rotate'] = [0, a['r1'], 0]
                            if a['action'] == 'transform':
                                object['startState'] = a['s1']
                print(f'rendering {origin_node}')
                pt.pathTracing(scenejson, 16, f'./static/dataset/infiniteLayout/{taID}img/{origin_node}.png')
            if not os.path.exists(f'./static/dataset/infiniteLayout/{taID}img/{target_node}.png'):
                scenejson = copy.deepcopy(sj)
                for i in range(len(animationjson['actions'])):
                    for object in scenejson['rooms'][0]['objList']:
                        if 'sforder' not in object:
                            continue
                        if object['sforder'] == i:
                            break
                    for seq in animationjson['actions'][i]:
                        for a in seq:
                            if a['action'] == 'move':
                                object['translate'] = a['p2']
                            if a['action'] == 'rotate':
                                object['rotate'] = [0, a['r2'], 0]
                            if a['action'] == 'transform':
                                object['startState'] = a['s2']
                print(f'rendering {target_node}')
                pt.pathTracing(scenejson, 16, f'./static/dataset/infiniteLayout/{taID}img/{target_node}.png')

def renderAnimationResults(sjName):
    pt.SAVECONFIG = False
    pt.emitter = 'sky'
    pt.USENEWWALL = True
    pt.CAMGEN = True
    with open(f'./static/dataset/infiniteLayout/{sjName}.json') as f:
        sj = json.load(f)
    taID = sj['rooms'][0]['totalAnimaID']
    animationjsonnames = os.listdir(f'./static/dataset/infiniteLayout/{taID}')
    if not os.path.exists(f'./static/dataset/infiniteLayout/{taID}img/'):
        os.makedirs(f'./static/dataset/infiniteLayout/{taID}img/')
    for animationjsonname in animationjsonnames:
        if '.json' not in animationjsonname:
            continue
        scenejson = copy.deepcopy(sj)
        with open(f'./static/dataset/infiniteLayout/{taID}/{animationjsonname}') as f:
            animationjson = json.load(f)
        for i in range(len(animationjson['actions'])):
            for object in scenejson['rooms'][0]['objList']:
                if 'sforder' not in object:
                    continue
                if object['sforder'] == i:
                    break
            for seq in animationjson['actions'][i]:
                for a in seq:
                    if a['action'] == 'move':
                        object['translate'] = a['p2']
                    if a['action'] == 'rotate':
                        object['rotate'] = [0, a['r2'], 0]
                    if a['action'] == 'transform':
                        object['startState'] = a['s2']
                # if(a.action === 'rotate'){
                #     let r = [0, atsc(a.r2), 0]
                #     standardizeRotate(r, [0, atsc(a.r1), 0]);
                #     object3d.rotation.set(0, atsc(a.r1), 0);
                #     setTimeout(transformObject3DOnly, a.t[0] * 1000, object.key, r, 'rotation', true, a.t[1] - a.t[0], 'none');
                # }
                # if(a.action === 'transform'){
                #     setTimeout(objectToAction, a.t[0] * 1000, object3d, a.s2, a.t[1] - a.t[0], 'none');
                # }
        animationjsonname = animationjsonname.split('.')[0]
        print(f'rendering ./static/dataset/infiniteLayout/{taID}/{animationjsonname}.png')
        pt.pathTracing(scenejson, 16, f'./static/dataset/infiniteLayout/{taID}img/{animationjsonname}.png')
    pt.pathTracing(sj, 16, f'./static/dataset/infiniteLayout/{taID}img/center.png')

if __name__ == "__main__":
    start_time = time.time()
    # cgs('6453', None, '梳妆台哈哈')
    # cgs('7644', ['3699', '7836', '2740', '2565'], 'init')
    # cgs('652', None, 'zhangsk18-岳亮Super')
    # cgs('41', None, 'philip-abc')
    # cgs('3289', None, 'huangjk21-202403311风格')
    # cgs('5810', None, '新中式简约风')
    # cgs('1133', None, 'rkx-优雅田园风')
    # cgs('s__1319', None, 'zjt-zjt2')
    # cgs('s__1319', None, 'zjt-zjt3')

    cgs('s__541',None, 'zjt-zjt9')
    cgs('s__973',None, 'zjt-zjt13')

    # wall_distance_orient()
    # analyzeAnswerPlanner()
    # cgsBatch()
    # cgsUSRenderBatch()
    # cgs('5010', None, '李雪晴-灰色现代风')
    # renderModel20('streetbench2')
    # render_names=['new_shrub01','new_shrub02','new_shrub03','newTree1','newTree2','newTree3','newTree4','newTreeSmall','newTreeSmall2']
    # for name in render_names:
    #     renderModel20(name)

    # for modelId in ['story-TeacherChair']:
    #     try:
    #         renderModel20(modelId)
    #     except:
    #         print(modelId)

    # renderModel20('stool2bed2', 'glb', 'origin')
    # renderModel20('stool2bed2', 'glb', 'bed')
    # renderGLBbatch()
    # renderAnimationResults('sample3_origin')
    # renderAnimationResults('out_16_origin')
    # renderAnimationResults('out_11_origin')
    # renderAnimationResults('out_13_origin')
    # renderAnimationResults('out_14_origin')
    # renderAnimationResults('out_16_origin')
    # for i in range(0,482):
    #     if os.path.exists(f'./static/dataset/infiniteLayout/output0_{i}_origin.json'):
    #         renderAnimationResults(f'output0_{i}_origin')
    # renderModel20('story-StudentDeskBrokenA')
    # renderModel20('selling_holder_small')
    print("\r\n --- %s secondes --- \r\n" % (time.time() - start_time))
    # cgs('1133', None, '小太阳-灰色奢华土豪')

# 计算房间各类型的权重
def calculate_room_type_values(srcpath:str,dstpath:str):
    if not srcpath.endswith('.json'):
        return
    not_on_ground_factor = 0.5
    exist_factor = 0.7
    prior_factor = 0.3
    required_not_found_penalty = 0.25
    room_map = {
        "LivingDiningRoom":{"livingroom","diningroom"},
        "LivingRoom":{"livingroom"},
        "MasterBedroom":{"bedroom"},
        "Bedroom":{"bedroom"},
        "Library":{"office"},
        "DiningRoom":{"diningroom"},
        "SecondBedroom":{"bedroom"},
    }
    object_requirement = {
        "bedroom":["bed"],
        "diningroom":["diningtable","andchair"],
    }
    def wfunc(num):
        return num*num
    # Loading room occurence data
    objects = json.load(open('static/dataset/dynamic_objects_data.json'))
    objects_category_occurence = json.load(open('dataset/occurrenceCount/res_ratio.json'))
    with open('dataset/objCatListAliv2.json') as f:
        objCatListAliv2 = json.load(f)
    room_objects = {"livingroom","bedroom","diningroom","office"}
    newpath = dstpath
    def getObjCat(modelId):
        if len(objCatListAliv2[modelId]) == 0:
            return None
        else:
            return objCatListAliv2[modelId][0]
    def itemListHandler(lst, instr):
        if instr == 'scale':
            if len(lst) == 3:
                return {'objScaleX' : float(lst[0]),  'objScaleY' : float(lst[1]), 'objScaleZ' : float(lst[2])}
            else:
                return {}

        if instr == 'state':
            if len(lst) == 1:
                return {'currentState' : lst[0]}
            else:
                return {}
        
        if instr == 'gtrans':
            if len(lst) == 8:
                return {'attachedObjId' : lst[0], 'objPosX' : float(lst[1]), 'objPosY' : float(lst[2]), 'objPosZ' : float(lst[3]), 'objOriY' : float(lst[4]), 'objScaleX' : float(lst[5]), 'objScaleY' : float(lst[6]), 'objScaleZ' : float(lst[7])}
            elif len(lst) == 9:
                return {'attachedObjId' : lst[0], 'objPosX' : float(lst[1]), 'objPosY' : float(lst[2]), 'objPosZ' : float(lst[3]), 'objOriY' : float(lst[4]), 'objScaleX' : float(lst[5]), 'objScaleY' : float(lst[6]), 'objScaleZ' : float(lst[7]), 'currentState' : lst[8]}
            else:
                return {}

        if instr == 'wall':
            if len(lst) == 3:
                return {'nearestDistance' : float(lst[0]), 'secondDistance' : float(lst[1]), 'nearestOrient0' : float(lst[2])}
            else:
                return {}
        
        if instr == 'window' or instr == 'door':
            if len(lst) == 8:
                return {'distance' : float(lst[0]), 'objPosX' : float(lst[1]), 'objPosY' : float(lst[2]), 'objPosZ' : float(lst[3]), 'width' : float(lst[4]), 'height' : float(lst[5]), 'objOriY' : float(lst[6]), 'direction' : lst[7][1]}
            else:
                return {}
    def elementHandler(eleDict, element):
        if element.count('[') == 0:
            if 'relationName' in eleDict:
                return -1
            else:
                eleDict['relationName'] = element
            return 1
        idx = element.index('[')
        eleName = element[1:idx] #skip the blank space
        eleContent = element[idx+1:] #skip [
        lst = eleContent.split(':')[:-1] #skip ]
        if not(eleName in ['scale', 'state', 'gtrans', 'wall', 'window', 'door']):
            print('elementHandler : wrong attribute')
            return -1
        
        eleDict[eleName] = []
        for itms in lst:
            itmLst = itms[1:].split(',')[:-1] #get rid of '{ }'
            ret = itemListHandler(itmLst, eleName)
            if len(ret) :
                eleDict[eleName].append(ret)
            else:
                print('elementHandler : item %s length error'%(eleName))
                return -1

        return 1
    # TODO: after adding prior in room data delete this part

    def calarea(objpath):
        vertices = []
        try:
            objf=open(objpath,encoding='utf-8')
            for line in objf:
                if line.startswith("#"):
                    continue
                values = line.split()
                if len(values) == 0:
                    continue
                if values[0] == 'v':
                    v = list(map(float, values[1:4]))
                    vertices.append([v[0], v[1], v[2]])
        except:
            objf=open(objpath,encoding='gbk')
            for line in objf:
                if line.startswith("#"):
                    continue
                values = line.split()
                if len(values) == 0:
                    continue
                if values[0] == 'v':
                    v = list(map(float, values[1:4]))
                    vertices.append([v[0], v[1], v[2]])
        
        l0 = [a[0] for a in vertices]
        l2 = [a[2] for a in vertices]
        return (max(l0)-min(l0))*(max(l2)-min(l2))
    room_input = json.load(open(srcpath))
    for room in room_input["rooms"]:
        room_values = {key:0 for key in room_objects}
        roomtype_meet_requirement = set()
        # print(room['modelId']+":")
        totarea = 0
        for i in range(1,len(room['roomShape'])-1):
            totarea += (room['roomShape'][i][0]-room['roomShape'][0][0])*(room['roomShape'][i+1][1]-room['roomShape'][0][1])\
            -(room['roomShape'][i][1]-room['roomShape'][0][1])*(room['roomShape'][i+1][0]-room['roomShape'][0][0])
        totarea = abs(totarea) / 2
        fl=True
        wmap={}
        for obj in room["objList"]:
            # print(obj['modelId']+":")
            if os.path.exists('dataset/object/'+obj['modelId']):
                area = calarea('dataset/object/'+obj['modelId']+'/'+obj['modelId']+'.obj')
            elif os.path.exists('static/dataset/object/'+obj['modelId']): 
                area = calarea('static/dataset/object/'+obj['modelId']+'/'+obj['startState']+'.obj')
            else:
                continue
            area = obj['scale'][0]*obj['scale'][2]*area
            obj['area']=area
            w=area
            wmap[obj['modelId']+'_'+(obj['startState'] if 'startState' in obj else 'origin')]=w
            # print("w:"+str(w))
            obj_name = obj['modelId']+'_'+(obj['startState'] if 'startState' in obj else 'origin')
            if obj['modelId'] in objCatListAliv2 and getObjCat(obj['modelId']) != None:
                objcat = getObjCat(obj['modelId'])
                if objcat in objects_category_occurence:
                    for room_type in room_objects:
                        if room_type in object_requirement:
                            for required_object in object_requirement[room_type]:
                                if objcat.lower.replace(' ','').endswith(required_object):
                                    roomtype_meet_requirement.add(room_type)
                    for room_type in objects_category_occurence[objcat]:
                        if room_type in room_map:
                            for mapped_room_type in room_map[room_type]:
                                room_values[mapped_room_type]+=w*objects_category_occurence[objcat][room_type]/len(room_map[room_type])
                                # print((mapped_room_type,objects_category_occurence[getObjCat(obj['modelId'])][room_type]/len(room_map[room_type])))    
            elif obj_name in objects:
                # calculating room type
                if not 'startState' in obj:
                    objcat = ''
                elif obj['startState']== 'origin':
                    objcat = obj['modelId'].split('2')[-2]
                else:
                    objcat = obj['startState']
                objcat = objcat.lower().replace(' ','')
                for room_type in room_objects:
                    if room_type in object_requirement:
                        for required_object in object_requirement[room_type]:
                            if objcat.endswith(required_object):
                                roomtype_meet_requirement.add(room_type)
                for room_type in room_objects:
                    room_values[room_type]+=w*objects[obj_name]['labelvalue'][room_type]
                    # print((room_type,objects[obj_name]['labelvalue'][room_type]))
            else:
                print("object not found---------------")
        
        for key in room_values:
            room_values[key]=room_values[key]*exist_factor
        
        for obj in room['objList']:
            if 'attachedObj' in obj:
                temp_room_values={key:0 for key in room_values}
                obj_name = obj['modelId']+'_'+(obj['startState'] if 'startState' in obj else 'origin')
                if obj['modelId'] in objCatListAliv2 and getObjCat(obj['modelId']) != None:
                    objcat = getObjCat(obj['modelId'])
                    if objcat in objects_category_occurence:
                        for room_type in objects_category_occurence[objcat]:
                            if room_type in room_map:
                                for mapped_room_type in room_map[room_type]:
                                    temp_room_values[mapped_room_type]+=obj['area']*objects_category_occurence[objcat][room_type]/len(room_map[room_type])
                elif obj_name in objects:
                # calculating room type
                    for room_type in room_objects:
                        temp_room_values[room_type]+=obj['area']*objects[obj_name]['labelvalue'][room_type]
                        # print((room_type,objects[obj_name]['labelvalue'][room_type]))
                sub_room_values={key:0 for key in room_values}
                for subobj in obj['attachedObj']:
                    obj_name = subobj.replace('#','_')
                    if obj_name in objCatListAliv2 and getObjCat(obj_name) != None:
                        if getObjCat(obj_name) in objects_category_occurence:
                            objcat = getObjCat(obj_name)
                            for room_type in objects_category_occurence[objcat]:
                                if room_type in room_map:
                                    for mapped_room_type in room_map[room_type]:
                                        temp_room_values[mapped_room_type]+=wmap[obj_name+'_origin']*objects_category_occurence[objcat][room_type]/len(room_map[room_type])
                    elif obj_name in objects:
                    # calculating room type
                        for room_type in room_objects:
                            temp_room_values[room_type]+=wmap[obj_name]*objects[obj_name]['labelvalue'][room_type]
                            # print((room_type,objects[obj_name]['labelvalue'][room_type]))
                hasdifferentobj = False
                for subobj in obj['attachedObj']:
                    if subobj.replace('#','_')!=obj_name:
                        hasdifferentobj=True
                        break
                if not hasdifferentobj:
                    continue
                for key in room_values:
                    room_values[key]+=math.sqrt(temp_room_values[key])*math.sqrt(sub_room_values[key])*prior_factor
        
        for key in room_values:
            if key in object_requirement.keys() and not key in roomtype_meet_requirement:
                room_values[key]=room_values[key]*required_not_found_penalty
        output={"evaluation":[],"description":""}
        sv=0
        for key in room_values:
            sv+=wfunc(room_values[key])
        if sv==0:
            print("Cannot calculate")
        else:
            for key in room_values:
                room_values[key]=wfunc(room_values[key])/sv
            # print("Room type evaluation:")
            for key in room_values:
                # print(key+":"+str(room_values[key]))
                output['evaluation'].append({"room":key,"value":room_values[key]})
        sorted_room_values = [{"roomtype":key,"value":value} for key,value in room_values.items()]
        sorted_room_values.sort(key=lambda x:x['value'],reverse=True)
        description="The room type is "
        maincount=3
        for i in range(1,4):
            if sorted_room_values[i]["value"]/sorted_room_values[0]["value"]<0.7:
                maincount=i-1
                break
        if maincount==0:
            description += sorted_room_values[0]["roomtype"]
        else:
            description += "a combination of "
            for i in range(0,maincount-1):
                description+=sorted_room_values[i]["roomtype"]+", "
            description += sorted_room_values[maincount-1]["roomtype"]+" and "+sorted_room_values[maincount]["roomtype"]
        
        subcount=3
        for i in range(maincount+1,4):
            if sorted_room_values[i]["value"]/sorted_room_values[0]["value"]<0.4:
                subcount=i-1
                break
        if subcount!=maincount:
            description+=", with some functionality of "
            for i in range(maincount+1,subcount):
                description+=sorted_room_values[i]["roomtype"]+", "
            description+=sorted_room_values[subcount]["roomtype"]
            description+=" as well"
        description+="."
        # print(description)
        output['description']=description
        json.dump(output,open(newpath,"w"))

from typing import List, Optional
# 计算用于构建树结构的数据
def calculate_tree_data(path:str,groupName:str,globalMaxDiff:float=0.02):
    Room_label: int = 4
    Room_num: int = 10
    # norm = norm3
    class Layout:
        def __init__(self, room_label: int = 4):
            self.property = [0.0] * Room_label
            self.flag = ""
            self.id: str = ""

    class LayoutNode:
        def __init__(self):
            self.layout_set: List[Layout] = []
            self.parent: Optional['LayoutNode'] = None
            self.next_nodes: List['LayoutNode'] = []
            self.name: str = ""
            self.meta = {}

    def max_weight(node: Layout) -> int:
        max_num = 0
        max_ind = -1
        for i in range(len(node.property)):
            if node.property[i] > max_num:
                max_num = node.property[i]
                max_ind = i
        return max_ind

    def display_layout(l: Layout):
        print(" 编号为：", l.flag, " ", end="")
        print(" 权重为： ", end="")
        for i in range(len(l.property)):
            print(l.property[i], " ", end="")
        print()

    def display_index(ln: Optional[LayoutNode]):
        if ln is None:
            print("空指针")
        elif len(ln.layout_set) == 0:
            print("空")
        else:
            for l in ln.layout_set:
                print(l.flag, " ", end="")
            print()

    def display(origin: Optional[LayoutNode]):
        if origin is None:
            return
        print("")
        print("此布局结点的父母布局为：", end="")
        display_index(origin.parent)
        print("此布局结点的集合中的布局个数为", len(origin.layout_set), " ，编号为：", end="")
        display_index(origin)
        print("此布局的子布局结点共有", len(origin.next_nodes), "个")
        for node_ptr in origin.next_nodes:
            display(node_ptr)

    # 一个结点的集合中只有一个布局
    def norm1(l1: Layout, l2: Layout, j:int) -> bool:
        return False

    # 一个结点的集合中可以有多个布局，不过需要全部一样
    def norm2(l1: Layout, l2: Layout, j:int) -> bool:
        diff: int = 0
        for i in range(Room_label):
            diff += abs(l1.property[i] - l2.property[i])
        if diff <= 0:
            return True
        return False

    # 一个结点的集合中可以有多个布局，只要它们的1-范数小于等于参数maxDiff，默认为2
    def norm3(l1: Layout, l2: Layout, j:int, maxDiff:float = globalMaxDiff) -> bool:
        # return True
        diff = 0
        for i in range(Room_label):
            diff += abs(l1.property[i] - l2.property[i])
        if diff <= maxDiff:
            return True
        return False
    
    def norm4(l1: Layout, l2: Layout, j:int, maxDiff:float = globalMaxDiff, indexMin: float = 0.5)->bool:
        if norm3(l1, l2, j):    
            if l1.property[j] <= indexMin:
                return False
            return True
        return False

    anim_data = json.load(open(f'./static/dataset/infiniteLayout/{groupName}_anim.json'))
    anim_map={}
    for meta in anim_data["index"][anim_data['center']+'_0']:
        anim_map[meta['anim_id']]=meta

    def divide(nodes: List[Layout], parent: Optional[LayoutNode] = None):
        if len(nodes) == 0:
            return 0
        
        nodecnt = 1

        # room_label = len(nodes[0].property)
        nodes_vec = [[] for _ in range(Room_label)]
        for node in nodes:
            ind = max_weight(node)
            if ind == -1:
                continue
            nodes_vec[ind].append(node)

        for i in range(len(nodes_vec)):
            if len(nodes_vec[i]) == 0:
                continue
            nodes_vec[i].sort(key=lambda l: l.property[i])

            t = LayoutNode()
            t.layout_set.append(nodes_vec[i].pop())
            it = 0
            while it < len(nodes_vec[i]):
                if norm(nodes_vec[i][it], t.layout_set[0], i):
                    t.layout_set.append(nodes_vec[i].pop(it))
                else:
                    it += 1
            for j in range(len(nodes_vec[i])):
                nodes_vec[i][j].property[i] = 0

            if filterLayoutSet:
                it = 0
                while it < len(t.layout_set):
                    if t.layout_set[it].property[i] < filterValue :
                        t.layout_set.pop(it)
                    else:
                        it += 1

            if len(t.layout_set) == 0:
                continue

            t.parent = parent
            t.parent.next_nodes.append(t)

            # t.name = giveName()
            # t.name = "".join('房{} '.format(x.flag) for x in t.layout_set) + ":{}".format(len(t.layout_set))
            t.name = "房{}".format(t.layout_set[0].flag) + "等{}套".format(len(t.layout_set))
            t.meta = anim_map[int(t.layout_set[0].id)] if t.layout_set[0].id != anim_data['center']+'_0' else {'root':anim_data['center']+'_0'}
            nodecnt += divide(nodes_vec[i].copy(), t)
        return nodecnt

    def normalize_layout(t: Layout):
        total = sum(t.property)
        if total == 0:
            return
        for i in range(len(t.property)):
            t.property[i] *= (Room_label+1)
            t.property[i] //= total

    def random_layout(t: Layout):
        for i in range(len(t.property)):
            t.property[i] = random.randint(0, 5)
        normalize_layout(t)

    def treeMethod():
        random.seed()  # 生成随机布局

        n = 200  # 总布局结点数量
        # n = Room_num

        weightJsonUrl = path # 房间属性权重文件的文件夹
        
        files =  os.listdir(weightJsonUrl)
        n = len(files)

        nodes_all = [Layout() for _ in range(n+1)]
        temp_count = 0
        f = open(f'./static/dataset/infiniteLayout/{groupName}_origin_values.json')
        data = json.load(f)
        temp_count_weight = 0
        for weightInfoPair in data["evaluation"]:
            nodes_all[temp_count].property[temp_count_weight] = weightInfoPair['value']
            temp_count_weight += 1
            # print(weightInfoPair)
        nodes_all[temp_count].flag = f'/static/dataset/infiniteLayout/{groupName}_origin_values'
        nodes_all[temp_count].id = anim_data['center']+'_0'
        # print(nodes_all[temp_count].flag)
        temp_count += 1
        for filename in files:
            if filename == 'layoutTree.json':
                continue
            if not filename.endswith('.json'):
                continue
            f = open(weightJsonUrl + f"/{filename}")
            data = json.load(f)
            temp_count_weight = 0
            for weightInfoPair in data["evaluation"]:
                nodes_all[temp_count].property[temp_count_weight] = weightInfoPair['value']
                temp_count_weight += 1
                # print(weightInfoPair)
            nodes_all[temp_count].flag = f'/static/dataset/infiniteLayout/{groupName}_animimg/'+filename.replace('.json','')
            nodes_all[temp_count].id = filename.replace('.json','')
            # print(nodes_all[temp_count].flag)
            temp_count += 1


        # 读入所有布局结点操作
        # TODO

        # 测试用随机生成
        # for i in range(n):
        #     random_layout(nodes_all[i])
        #     nodes_all[i].flag = "{}".format(i)


        origin = LayoutNode()
        origin.name = "一切的起源"
        origin.layout_set.append(nodes_all[0])
        origin.meta = {"root": anim_data['center']+'_0'}


        for l in nodes_all:
            display_layout(l)

        nodes_all_1 = nodes_all[1:]

        returnvalue = divide(nodes_all_1, origin)

        rootDir = os.listdir('./')

        write_json(origin, path+"/{}.json".format('layoutTree'))

        return returnvalue
        
        # with open(path+"/{}.js".format('layoutTree'), 'w') as f:
        # # with open("{}.js".format(new_data), 'w') as f:
        #     f.write("data1='[")
        #     with open(path+"/{}.json".format('layoutTree')) as prefix:
        #         f.write(prefix.read())
        #     f.write("]';")


        # display(origin)

    def create_body(origin: LayoutNode):
        parent_name = "null"
        if origin.parent:
            parent_name = origin.parent.name
        dictionary = {
            "name" : origin.name,  "parent" : parent_name, "pics" : [x.flag for x in origin.layout_set],
            "meta" : origin.meta,
            # "children" : []
        }
        if(len(origin.next_nodes)):
            dictionary["children"] = []
            for x in origin.next_nodes:
                tmp = create_body(x)
                dictionary["children"].append(tmp)


        return dictionary
    
    def write_json(origin:LayoutNode, file_path):
        dictionary = create_body(origin)
        # print(dictionary)
        json_object = json.dumps(dictionary)
        with open(file_path, 'w') as outfile:
            outfile.write(json_object)

    Room_label: int = 4
    Room_num: int = 10
    norm = norm4
    filterLayoutSet = True
    filterValue = 0.03

    return treeMethod()