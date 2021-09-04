"""
This is used to transform 3d-furture format data to suncg format data
Author : slothfulxtx
Date : 2020/08/06
Details : 
    The mesh objects in 3d-future dataset compose of two parts, including furniture and components of the sence.
    The furniture models can be found in the directory 3D-FUTURE-MODEL/jid/, while the components of the scene 
    are given in the form of .json files instead of .obj files. Thus we need to extract the components from json 
    first, and then convert them to the form of .obj. In the process of converting data, we generate the scene 
    folder whose structure are shown as follow 
    
    |- house
    |   |- 0b508d29-c18c-471b-8711-3f114819ea74.json
    |- backgroundobj
        |- 0b508d29-c18c-471b-8711-3f114819ea74
            |- 5031ce7f-343a-41c8-b8ce-e2e943398df5X53357662.obj
    |- background
        |- 0b508d29-c18c-471b-8711-3f114819ea74 
            |- DiningRoom-13252
                |- wall.obj
                |- floor.obj
                |- ceil.obj
"""

import json
import trimesh
import numpy as np
import math
import os
import argparse
from tqdm import tqdm
import math
import igl
from shutil import copyfile
import sys
from math import atan2, copysign, asin
from math import pi, copysign, sin, cos
INF = 1e9

with open('ali_to_sk.json') as f:
    ali_to_sk = json.load(f)
with open('../latentspace/obj_coarse_semantic.json') as f:
    obj_coarse_semantic = json.load(f)


def Min3d(aa, bb):
    c = []
    for a, b in zip(aa, bb):
        c.append(a if a < b else b)
    return c


def Max3d(aa, bb):
    c = []
    for a, b in zip(aa, bb):
        c.append(a if a > b else b)
    return c


def split_path(paths):
    filepath, tempfilename = os.path.split(paths)
    filename, extension = os.path.splitext(tempfilename)
    return filepath, filename, extension


def write_obj_with_tex(savepath, vert, face, vtex, ftcoor, imgpath=None):
    filepath2, filename, extension = split_path(savepath)
    with open(savepath, 'w') as fid:
        fid.write('mtllib '+filename+'.mtl\n')
        fid.write('usemtl a\n')
        for v in vert:
            fid.write('v %f %f %f\n' % (v[0], v[1], v[2]))
        for vt in vtex:
            fid.write('vt %f %f\n' % (vt[0], vt[1]))
        face = face + 1
        ftcoor = ftcoor + 1
        for f, ft in zip(face, ftcoor):
            fid.write('f %d/%d %d/%d %d/%d\n' %
                      (f[0], ft[0], f[1], ft[1], f[2], ft[2]))
    filepath, filename2, extension = split_path(imgpath)
    if os.path.exists(imgpath) and not os.path.exists(filepath2+'/'+filename+extension):
        copyfile(imgpath, filepath2+'/'+filename+extension)
    if imgpath is not None:
        with open(filepath2+'/'+filename+'.mtl', 'w') as fid:
            fid.write('newmtl a\n')
            fid.write('map_Kd '+filename+extension)


def myconcatenate(a, b=None):
    """
    Concatenate two or more meshes.
    Parameters
    ------------
    a : trimesh.Trimesh
      Mesh or list of meshes to be concatenated
      object, or list of such
    b : trimesh.Trimesh
      Mesh or list of meshes to be concatenated
    Returns
    ----------
    result : trimesh.Trimesh
      Concatenated mesh
    """
    if b is None:
        b = []
    # stack meshes into flat list
    meshes = np.append(a, b)

    # if there is only one mesh just return the first
    if len(meshes) == 1:
        return meshes[0].copy()

    # extract the trimesh type to avoid a circular import
    # and assert that both inputs are Trimesh objects
    from trimesh.util import type_named, append_faces
    trimesh_type = type_named(meshes[0], 'Trimesh')

    # append faces and vertices of meshes
    vertices, faces = append_faces(
        [m.vertices.copy() for m in meshes],
        [m.faces.copy() for m in meshes])

    # only save face normals if already calculated
    face_normals = None
    if all('face_normals' in m._cache for m in meshes):
        face_normals = np.vstack(
            [m.face_normals for m in meshes])

    try:
        # concatenate visuals
        uv = np.concatenate([m.visual.uv for m in meshes])
        visual = trimesh.visual.TextureVisuals(uv=uv)
        # visual = meshes[0].visual.concatenate(
        # [m.visual for m in meshes[1:]])
    except BaseException:
        print('shit!!')
        visual = None
    # create the mesh object
    mesh = trimesh_type(vertices=vertices,
                        faces=faces,
                        face_normals=face_normals,
                        visual=visual,
                        process=False)

    return mesh


def rotation_matrix(axis, theta):
    axis = np.asarray(axis)
    axis = axis / math.sqrt(np.dot(axis, axis))
    a = math.cos(theta / 2.0)
    b, c, d = -axis * math.sin(theta / 2.0)
    aa, bb, cc, dd = a * a, b * b, c * c, d * d
    bc, ad, ac, ab, bd, cd = b * c, a * d, a * c, a * b, b * d, c * d
    return np.array([[aa + bb - cc - dd, 2 * (bc + ad), 2 * (bd - ac)],
                     [2 * (bc - ad), aa + cc - bb - dd, 2 * (cd + ab)],
                     [2 * (bd + ac), 2 * (cd - ab), aa + dd - bb - cc]])


def quaternion_to_euler(qlist):
    q = {}
    q['x'] = qlist[0]
    q['y'] = qlist[1]
    q['z'] = qlist[2]
    q['w'] = qlist[3]

    # roll (x-axis rotation)
    sinr_cosp = 2 * (q['w'] * q['x'] + q['y'] * q['z'])
    cosr_cosp = 1 - 2 * (q['x'] * q['x'] + q['y'] * q['y'])
    roll = atan2(sinr_cosp, cosr_cosp)

    # pitch (y-axis rotation)
    sinp = 2 * (q['w'] * q['y'] - q['z'] * q['x'])
    if abs(sinp) >= 1:
        pitch = copysign(np.pi / 2, sinp)  # use 90 degrees if out of range
    else:
        pitch = asin(sinp)

    # yaw (z-axis rotation)
    siny_cosp = 2 * (q['w'] * q['z'] + q['x'] * q['y'])
    cosy_cosp = 1 - 2 * (q['y'] * q['y'] + q['z'] * q['z'])
    yaw = atan2(siny_cosp, cosy_cosp)

    return (roll, pitch, yaw)


def orient33(matrix):
    # print(np.linalg.det(matrix[0:3, 0:3]))
    return atan2(matrix[0, 2], matrix[2, 2])


def euler_to_matrix(thetaX, thetaY, thetaZ):
    X = np.array([[1, 0, 0], [0, cos(thetaX), -sin(thetaX)],
                 [0, sin(thetaX), cos(thetaX)]])
    Y = np.array([[cos(thetaY), 0, sin(thetaY)], [
                 0, 1, 0], [-sin(thetaY), 0, cos(thetaY)]])
    Z = np.array([[cos(thetaZ), -sin(thetaZ), 0],
                 [sin(thetaZ), cos(thetaZ), 0], [0, 0, 1]])
    return Z @ Y @ X


def add_new_line(p):
    with open(p) as f:
        fl = f.read()
    fl += '\n'
    with open(p, 'w') as f:
        f.write(fl)


def main(args):
    with open(args.category_map_file_path, "r")as f:
        future2suncg_cat = json.load(f)

    filenames = os.listdir(args.FRONT_path)

    if not os.path.exists(args.save_path):
        os.mkdir(args.save_path)
    if not os.path.exists(os.path.join(args.save_path, "alilevel2021")):
        os.mkdir(os.path.join(args.save_path, "alilevel2021"))
    if not os.path.exists(os.path.join(args.save_path, "room2021")):
        os.mkdir(os.path.join(args.save_path, "room2021"))
    if not os.path.exists(os.path.join(args.save_path, "backgroundobj")):
        os.mkdir(os.path.join(args.save_path, "backgroundobj"))
    filenames = os.listdir('F:/3DFurniture/3D-FRONT')
    # DEBUG
    # filenames = [
    #     '00f2a7e7-a994-4734-8104-8cb81560beb0.json',
    #     '1aab0a4b-760c-4489-b012-da6cefdca8a4.json',
    #     '5c0a1757-e14e-4901-a3a3-498537689821.json',
    #     '4c1b75c2-351b-4b6b-a7df-c867a2d9b3d6.json',
    #     '274ef293-2cf8-4c9a-8125-814f91d0bc83.json',
    #     '641eaf99-ec77-40a6-bef8-2ff72ef2b1d1.json',
    #     '7b2fae3d-5455-4dae-b174-7643ca83b1dc.json',
    #     '06a3196e-a2a2-4952-a5c6-034afcc18e15.json',
    #     '7e07a2a4-fead-40b8-8172-a430c150b733.json',
    #     'be5538a6-455b-486f-a46a-fd03d864587e.json'
    #     ]

    for sceneIdx, filename in tqdm(enumerate(filenames)):

        # create path to save generated models of the scene
        if not os.path.exists(os.path.join(args.save_path, "backgroundobj", filename[:-5])):
            os.mkdir(os.path.join(args.save_path,
                     "backgroundobj", filename[:-5]))
        if not os.path.exists(os.path.join(args.save_path, "room2021", filename[:-5])):
            os.mkdir(os.path.join(args.save_path, "room2021", filename[:-5]))
        with open(os.path.join(args.FRONT_path, filename), 'r', encoding='utf-8') as f:
            frontJson = json.load(f)

        suncgJson = {}

        suncgJson["origin"] = frontJson["uid"]
        suncgJson["id"] = str(sceneIdx)
        suncgJson["bbox"] = {
            "min": [INF, INF, INF],
            "max": [-INF, -INF, -INF]
        }
        suncgJson["up"] = [0, 1, 0]
        suncgJson["front"] = [0, 0, 1]
        suncgJson["rooms"] = []

        meshList = frontJson["mesh"]
        meshes = {}

        for mesh in meshList:
            meshes[mesh["uid"]] = mesh
            xyz = np.reshape(mesh['xyz'], (-1, 3)).astype(np.float64)
            face = np.reshape(mesh['faces'], (-1, 3))
            normal = np.reshape(mesh['normal'], (-1, 3))
            uv = np.reshape(mesh['uv'], (-1, 2))
            # if future2suncg_cat[mesh["type"]] == "Object":
            if mesh["type"] in ["Window", "Door"]:
                # With respect to components of the scene, we extract windows and doors and consider them as isolate objects
                # like other furnitures, which follows the rule of SunCG dataset.
                bgopath = os.path.join(
                    args.save_path, "backgroundobj", filename[:-5], mesh["uid"].replace('/', 'X')+".obj")
                trimesh.Trimesh(
                    # vertices=xyz, faces=face, vertex_normals=normal).export(bgopath)
                    vertices=xyz, faces=face, vertex_normals=normal, visual=trimesh.visual.TextureVisuals(uv=uv)).export(bgopath)
                add_new_line(bgopath)

        furnitureList = frontJson["furniture"]
        furnitures = {}
        for furniture in furnitureList:
            # We add each valid furniture models to the result and ignore others.
            if "valid" in furniture and furniture["valid"]:
                furnitures[furniture["uid"]] = furniture

        scene = frontJson["scene"]
        rooms = scene["room"]

        room_obj_cnt = 0

        for roomIdx, front_room in enumerate(rooms):
            suncg_room = {
                "id": "%d_%d" % (sceneIdx, room_obj_cnt),
                "modelId": front_room["instanceid"],
                "roomTypes": [front_room["type"]],
                "bbox": {
                    "min": [INF, INF, INF],
                    "max": [-INF, -INF, -INF]
                },
                "origin": frontJson["uid"],
                "roomId": roomIdx,
                "objList": []
            }
            if not os.path.exists(os.path.join(args.save_path, "room2021", filename[:-5])):
                os.mkdir(os.path.join(args.save_path, "room2021", filename[:-5]))
            wallObjs = []
            ceilObjs = []
            floorObjs = []
            room_obj_cnt += 1

            # For each meshes in the room, we roughly split them into two category, scene and objects.
            # Each furniture in the room of 3d-future dataset is categorized as objects of SunCG dataset,
            # as well as windows and doors of 3d-future dataset. The other models of the same category
            # is merged into one model and considered as the scene of SunCG dataset.
            for childIdx, child in enumerate(front_room["children"]):
                if child["ref"] not in meshes and child["ref"] not in furnitures:
                    continue
                # and future2suncg_cat[meshes[child["ref"]]["type"]] != "Object":
                if child["ref"] in meshes:
                    if future2suncg_cat[meshes[child["ref"]]["type"]] == "Wall":
                        Objs = wallObjs
                    elif future2suncg_cat[meshes[child["ref"]]["type"]] == "Floor":
                        Objs = floorObjs
                    elif future2suncg_cat[meshes[child["ref"]]["type"]] == "Ceil":
                        Objs = ceilObjs
                    else:
                        # assert False
                        Objs = wallObjs

                    mesh = meshes[child["ref"]]
                    vs = np.reshape(mesh['xyz'], (-1, 3)).astype(np.float64)
                    face = np.reshape(mesh['faces'], (-1, 3))
                    normal = np.reshape(mesh['normal'], (-1, 3))
                    uv = np.reshape(mesh['uv'], (-1, 2))
                    pos = child['pos']
                    rot = child['rot']
                    scale = child['scale']
                    vs = vs.astype(np.float64) * scale
                    ref = [0, 0, 1]
                    axis = np.cross(ref, rot[1:])
                    theta = np.arccos(np.dot(ref, rot[1:]))*2
                    if np.sum(axis) != 0 and not math.isnan(theta):
                        R = rotation_matrix(axis, theta)
                        vs = np.transpose(vs)
                        vs = np.matmul(R, vs)
                        vs = np.transpose(vs)
                    vs = vs + pos
                    Objs.append(trimesh.Trimesh(vertices=vs, faces=face,
                                                vertex_normals=normal, visual=trimesh.visual.TextureVisuals(uv=uv)))  # , vertex_colors=uv))

                    if meshes[child["ref"]]["type"] not in ['Window', "Door"]:
                        # If this mesh is a window or door, we collect it and process later.
                        continue
                # We create a object in the form of SunCG dataset.
                suncg_obj = {
                    "id": "%d_%d" % (sceneIdx, room_obj_cnt),
                    "type": "Object",
                    "modelId": meshes[child["ref"]]["uid"].replace('/', 'X') if child["ref"] in meshes else furnitures[child["ref"]]["jid"],
                    "bbox": {
                        "min": [INF, INF, INF],
                        "max": [-INF, -INF, -INF]
                    },
                    "translate": child["pos"],
                    "scale": child["scale"],
                    "rotate": quaternion_to_euler(child["rot"]),
                    "rotateOrder": "XYZ",
                    "orient": quaternion_to_euler(child["rot"])[1],
                    "coarseSemantic": meshes[child["ref"]]["type"] if child["ref"] in meshes else furnitures[child["ref"]]["category"],
                    "roomId": roomIdx
                }
                suncg_obj['orient'] = orient33(euler_to_matrix(
                    suncg_obj['rotate'][0], suncg_obj['rotate'][1], suncg_obj['rotate'][2]))
                # convert modelId in consistent with the platform;
                if suncg_obj['modelId'] in ali_to_sk:
                    suncg_obj['modelId'] = ali_to_sk[suncg_obj['modelId']]
                if suncg_obj['modelId'] not in obj_coarse_semantic:
                    suncg_obj['inDatabase'] = False
                room_obj_cnt += 1
                obj_path = None
                if child["ref"] in meshes:
                    obj_path = os.path.join(
                        args.save_path, "backgroundobj", filename[:-5], meshes[child["ref"]]["uid"].replace('/', 'X')+".obj")
                if child["ref"] in furnitures:
                    obj_path = os.path.join(
                        args.FUTURE_path, furnitures[child["ref"]]["jid"], "raw_model.obj")
                assert obj_path is not None
                assert os.path.exists(obj_path)

                # some .obj files are not provided by ali, so here we need to skip them;
                try:
                    v, vt, _, faces, ftc, _ = igl.read_obj(obj_path)
                except Exception as e:
                    print(e)
                    continue
                # print("???")
                # sys.stdout,sys.stderr = stdout,stderr

                # We convert the coordinate representation of 3d-future models to the form of suncg coordinate.
                pos, rot, scale = child["pos"], child["rot"], child["scale"]
                v = v.astype(np.float64) * scale
                ref = [0, 0, 1]
                axis = np.cross(ref, rot[1:])
                theta = np.arccos(np.dot(ref, rot[1:]))*2
                if np.sum(axis) != 0 and not math.isnan(theta):
                    R = rotation_matrix(axis, theta)
                    v = np.transpose(v)
                    v = np.matmul(R, v)
                    v = np.transpose(v)
                v = v + pos
                assert v.shape[1:] == (3,)
                lb = v.min(axis=0)
                ub = v.max(axis=0)
                suncg_obj["bbox"]["min"] = list(lb)
                suncg_obj["bbox"]["max"] = list(ub)
                suncg_room["objList"].append(suncg_obj)

                suncg_room["bbox"]["min"] = Min3d(
                    suncg_room["bbox"]["min"], suncg_obj["bbox"]["min"])
                suncg_room["bbox"]["max"] = Max3d(
                    suncg_room["bbox"]["max"], suncg_obj["bbox"]["max"])

            # adding a new line is because of a bug of three.js library...
            wfcroot = os.path.join(
                args.save_path, "room2021", filename[:-5], front_room["instanceid"])
            # We merge the components of the scene into three models, including wall, floor and ceil.
            if len(wallObjs) > 0:
                tmp = myconcatenate(wallObjs)
                tmp.vertex_normals
                tmp.export(wfcroot+"w.obj")
                add_new_line(wfcroot+"w.obj")
            if len(floorObjs) > 0:
                tmp = myconcatenate(floorObjs)
                tmp.vertex_normals
                tmp.export(wfcroot+"f.obj")
                add_new_line(wfcroot+"f.obj")

            if len(ceilObjs) > 0:
                tmp = myconcatenate(ceilObjs)
                tmp.vertex_normals
                tmp.export(wfcroot+"c.obj")
                add_new_line(wfcroot+"c.obj")

            # if not os.path.exists(os.path.join(args.save_path,"room_alipart",filename[:-5])):
            #     os.makedirs(os.path.join(args.save_path,"room_alipart",filename[:-5]))
            # allcwfs = wallObjs + floorObjs + ceilObjs
            # allcwfroot = os.path.join(args.save_path,"room_alipart",filename[:-5])
            # for obj in allcwfs:
            #     obj.export(allcwfroot + f'{} + ')

            suncgJson["rooms"].append(suncg_room)
            suncgJson["bbox"]["min"] = Min3d(
                suncgJson["bbox"]["min"], suncg_room["bbox"]["min"])
            suncgJson["bbox"]["max"] = Max3d(
                suncgJson["bbox"]["max"], suncg_room["bbox"]["max"])

        with open(os.path.join(args.save_path, "alilevel2021", filename), "w") as f:
            json.dump(suncgJson, f)
        # break


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--FUTURE_path',
        default='../../3D-FUTURE-model',
        help='path to 3D FUTURE'
    )
    parser.add_argument(
        '--FRONT_path',
        default='../../3D-FRONT',
        help='path to 3D FRONT'
    )

    parser.add_argument(
        '--save_path',
        default='F:/3DIndoorScenePlatform/dataset',
        help='path to save result dir'
    )
    parser.add_argument(
        '--category_map_file_path',
        default='3d2suncg_cat_map.json',
        help='path to save result dir'
    )

    args = parser.parse_args()
    main(args)
