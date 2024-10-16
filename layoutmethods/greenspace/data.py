import os
import numpy as np
import json
from shapely.geometry import *
from shapely.affinity import *
from shapely.ops import *
import trimesh
from math import *
from tqdm import tqdm

EPS = 1e-2


def get_data():
    with open('object/validlist.txt', 'r') as valid_list_txt:
        with open('object/actual_size.json', 'r') as actual_size_json:
            with open('object/ref_size.json', 'r') as ref_size_json:
                with open('object/types.json', 'r') as types_json:
                    with open('object/forward.json', 'r') as forward_json:
                        types = json.load(types_json)
                        ref_size = json.load(ref_size_json)
                        actual_size = json.load(actual_size_json)
                        valid_list = [line.strip() for line in valid_list_txt.readlines()]
                        forward = json.load(forward_json)
                        data = {}
                        data['objs'] = {}
                        for name in valid_list:
                            if os.path.isdir('object/' + name):
                                print(name)
                                obj = {}
                                path = 'object/{}/{}.obj'.format(name, name)
                                mesh = trimesh.load(path, force='mesh')

                                vs, fs = mesh.vertices, mesh.faces
                                xl, zl, xh, zh = 1e9, 1e9, -1e9, -1e9
                                for v in vs:
                                    xl = min(xl, v[0])
                                    xh = max(xh, v[0])
                                    zl = min(zl, v[2])
                                    zh = max(zh, v[2])
                                obj['bbox'] = [xl, zl, xh, zh]
                                obj['size'] = [xh - xl, zh - zl]
                                obj['actual_size'] = actual_size[name]
                                obj['ref_size'] = ref_size[name]
                                obj['forward'] = forward[name]
                                obj['type'] = "none"
                                for type, names in types.items():
                                    if name in names:
                                        obj['type'] = type
                                        break

                                data['objs'][name] = obj
                        data['types'] = types

        with open('object/data.json'.format(name), 'w') as out:
            json.dump(data, out)


def rmdir(path):
    for root, dirs, files in os.walk(path):
        for file in files:
            os.remove(os.path.join(root, file))
        for dir in dirs:
            os.rmdir(os.path.join(root, dir))
        os.rmdir(root)


def clean_obj():
    for name in os.listdir('object'):
        if os.path.isdir('object/{}'.format(name)):
            for render_dir in os.listdir('object/{}'.format(name)):
                if os.path.isdir('object/{}/{}'.format(name, render_dir)):
                    rmdir('object/{}/{}'.format(name, render_dir))


def clean_outputs():
    if os.path.exists('log_outputs'):
        for name in os.listdir('log_outputs'):
            if os.path.isdir('log_outputs/{}'.format(name)):
                rmdir('log_outputs/{}'.format(name))
            else:
                os.remove('log_outputs/{}'.format(name))
    if os.path.exists('outputs'):
        for name in os.listdir('outputs'):
            if os.path.isdir('outputs/{}'.format(name)):
                rmdir('outputs/{}'.format(name))
            else:
                os.remove('outputs/{}'.format(name))
    if os.path.exists('visuals'):
        for name in os.listdir('visuals'):
            if os.path.isdir('visuals/{}'.format(name)):
                rmdir('visuals/{}'.format(name))
            else:
                os.remove('visuals/{}'.format(name))


# def add_objList():
#     for name in os.listdir('batch_2/outputs'):
#         path = 'batch_2/outputs/{}'.format(name)
#         if not os.path.isdir(path):
#             with open(path, 'r') as f:
#                 scene = json.load(f)
#                 for room in scene['rooms']:
#                     if 'objList' not in room:
#                         room['objList'] = []
#                 with open(path, 'w') as f:
#                     json.dump(scene, f)


def area_to_obj():
    for name in tqdm(os.listdir('batch_3/outputs')):
        path = 'batch_3/outputs/{}'.format(name)
        if not os.path.isdir(path):
            with open(path, 'r') as f:
                scene = json.load(f)
                for room in scene['rooms']:
                    if 'objList' not in room:
                        room['objList'] = []
                    if 'modelId' in room:
                        obj = {}
                        obj['modelId'] = scene['id'] + '_' + room['modelId']
                        obj['translate'] = [0, 0, 0]
                        obj['scale'] = [1, 1, 1]
                        obj['rotate'] = [0, 0, 0]
                        obj['orient'] = 0
                        obj['format'] = 'areaPlane'
                        obj['isSceneObj'] = False
                        obj['inDatabase'] = False
                        room['objList'].append(obj)
                with open(path, 'w') as f:
                    json.dump(scene, f)


if __name__ == '__main__':
    # clean_obj()
    clean_outputs()
    # get_data()
    # area_to_obj()
    pass