from typing import Union
from numpy.core.fromnumeric import shape
import trimesh
import os
import json
import numpy as np
from scipy.spatial.transform import Rotation as R
import torch
from shapely.geometry.polygon import Polygon, LineString, Point

AABBcache = {}
ASPECT = 16 / 9
DEFAULT_FOV = 75
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

def preloadAABB(obj):
    if objectInDataset(obj['modelId']):
        AABB = load_AABB(obj['modelId'])
        if 'coarseSemantic' not in obj:
            obj['coarseSemantic'] = getobjCat(obj['modelId'])
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

def getWallHeight(meshPath):
    mesh = as_mesh(trimesh.load(meshPath))
    return np.max(mesh.vertices[:, 1]).tolist()

def getMeshVertices(meshPath):
    mesh = as_mesh(trimesh.load(meshPath))
    return mesh.vertices

def objectInDataset(modelId):
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

def pointToLineDistance(point, p1, p2):
    return np.linalg.norm(np.cross(p2-p1, p1-point)) / np.linalg.norm(p2-p1)

def isPointBetweenLineSeg(point, p1, p2):
    s = np.dot(p2 - p1, point - p1) / np.linalg.norm(p2 - p1)
    if 0 < s and s < np.linalg.norm(p2 - p1):
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
    # calculate the wall orient; 
    wn = (shape - shapeEnd)[:, [1,0]]
    wn[:, 1] = -wn[:, 1]
    if isOrient:
        orients = np.arctan2(wn[:, 0], wn[:, 1])
    else:
        orients = wn
    return _indicesList, distances, orients

def extractGroup(objList, dom, modelIDs):
    subs = []
    subPriors = []
    for obj in objList:
        if 'modelId' not in obj:
            continue
        if obj['modelId'] == dom:
            domObj = obj
        if obj['modelId'] in modelIDs:
            subs.append(obj)
    # sub-objects: 
    for obj in subs:
        # the relative transtormation should be sth like an identical matrix. 
        relativeTranslate = np.array(obj['translate']) - np.array(domObj['translate'])
        relativeTranslate = R.from_euler('y', -domObj['orient'], degrees=False).as_matrix() @ relativeTranslate # rotate this translation; 
        relativeTranslate = relativeTranslate / np.array(domObj['scale'])
        relativeScale = np.array(obj['scale']) / np.array(domObj['scale'])
        relativeOrient = np.array(obj['orient']) - np.array(domObj['orient'])
        subPriors.append({
            'sub': obj['modelId'],
            'translate': relativeTranslate.tolist(),
            'orient': relativeOrient.tolist(),
            'scale': relativeScale.tolist()
        })
    return [
        generateGroup(subPriors, dom, [1,1,1]), 
        generateGroup(subPriors, dom, [-1,1,1]), 
        generateGroup(subPriors, dom, [-1,1,-1]), 
        generateGroup(subPriors, dom, [1,1,-1])
    ]

def generateGroup(subPriors, domModelId, domScale=[1,1,1]):
    res = {
        'subPriors': subPriors.copy(),
        'objects': [],
        'domScale': domScale
    }
    bbs = np.zeros(shape=(0,3))
    domObj = {'translate': [0,0,0], 'rotate': [0,0,0], 'orient': 0, 'scale': domScale, 'modelId': domModelId}
    preloadAABB(domObj)
    bbs = np.vstack((bbs, domObj['AABB']['eightPoints']))
    for subPrior in subPriors:
        obj = {
            'translate': (np.array(subPrior['translate']) * np.array(domScale)).tolist(),
            'rotate': [0,subPrior['orient'],0],
            'scale': (np.array(subPrior['scale']) * np.array(domScale)).tolist(),
            'modelId': subPrior['sub']
        }
        preloadAABB(obj)
        bbs = np.vstack((bbs, obj['AABB']['eightPoints']))
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
    # constraints: area & #objects & ... :
    res['area'] = (ma[0] - mi[0]) * (ma[2] - mi[2])
    res['objNum'] = len(res['objects'])
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

def cgs(domID, subIDs, seriesName):
    filenames = os.listdir(f'./layoutmethods/cgseries/{domID}/{seriesName}') # init
    results = {
        'domID': domID,
        'anchorDises': [],
        'depthDises': [],
        'leftDises': [],
        'rightDises': [],
        'areas': [],
        'objNums': [],
        'configs': [],
        'involvedObjects': [],
        'enabled': False
    }
    for filename in filenames:
        if '.json' not in filename:
            continue
        with open(f'./layoutmethods/cgseries/{domID}/{seriesName}/{filename}') as f:
            scenejson = json.load(f)
        preloadAABBs(scenejson)
        results['configs'] += extractGroup(scenejson['rooms'][0]['objList'], domID, subIDs) # e.g., '7644' ['3699', '7836', '2740', '2565']
    for config in results['configs']:
        results['anchorDises'].append(config['anchorDis'])
        results['depthDises'].append(config['depthDis'])
        results['leftDises'].append(config['leftDis'])
        results['rightDises'].append(config['rightDis'])
        results['objNums'].append(config['objNum'])
        results['areas'].append(config['area'])
        results['involvedObjects'] = getObjectsUpperLimit(results['involvedObjects'], config['objects'])
    with open(f'./layoutmethods/cgseries/{results["domID"]}/{seriesName}/result.json', 'w') as f:
        json.dump(results, f)
    # if not os.path.exists(f'./layoutmethods/cgseries/{results["domID"]}.json'):
    #     with open(f'./layoutmethods/cgseries/{results["domID"]}.json', 'w') as f:
    #         json.dump({seriesName: results}, f)
    # else:
    #     with open(f'./layoutmethods/cgseries/{results["domID"]}.json', 'r') as f:
    #         _t = json.load(f)
    #     with open(f'./layoutmethods/cgseries/{results["domID"]}.json', 'w') as f:
    #         _t[seriesName] = results
    #         json.dump(_t, f)

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

if __name__ == "__main__":
    cgs('7644', ['3699', '7836', '2740', '2565'], 'init')
