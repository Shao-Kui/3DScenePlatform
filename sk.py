import trimesh
import os
import json
import numpy as np
from shapely.geometry.polygon import Polygon, LineString, Point

AABBcache = {}

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
    with open(f'./dataset/object/{i}/{i}-AABB.json', 'w') as f:
        json.dump(AABB, f)
    AABBcache[i] = AABB
    return AABBcache[i]

def getWallHeight(meshPath):
    mesh = as_mesh(trimesh.load(meshPath))
    return np.max(mesh.vertices[:, 1]).tolist()

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

def isLineIntersectsWithEdges(line, floorMeta):
    for i in range(floorMeta.shape[0]):
        l = LineString((floorMeta[i][0:2], floorMeta[(i+1)%floorMeta.shape[0]][0:2]))
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
