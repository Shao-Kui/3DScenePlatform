import json
import os
import math
import numpy as np
from shapely.geometry.polygon import Polygon
from projection2d import process as p2d
"""
This script is used to fix issues of 
'one door belongs to multiple rooms'; 
"""
def rotate_bb_local_np(points, angle, scale):
    result = points.copy()
    scaled = points.copy()
    scaled = scaled * scale
    result[:, 0] = np.cos(angle) * scaled[:, 0] + np.sin(angle) * scaled[:, 1]
    result[:, 1] = -np.sin(angle) * scaled[:, 0] + np.cos(angle) * scaled[:, 1]
    return result

def rotate(origin, point, angle):
    ox = origin[0]
    oy = origin[1]
    px = point[0]
    py = point[1]
    qx = ox + math.cos(angle) * (px - ox) + math.sin(angle) * (py - oy)
    qy = oy - math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy)
    return qx, qy

def windoorblock_f(o):
    currentwindoor = windoorblock[o['modelId']]
    block = {}
    block['modelId'] = o['modelId']
    block['coarseSemantic'] = o['coarseSemantic']
    block['max'] = currentwindoor['max'].copy()
    block['min'] = currentwindoor['min'].copy()
    block['max'][0] = block['max'][0] * o['scale'][0]
    block['max'][1] = block['max'][1] * o['scale'][1]
    block['max'][2] = block['max'][2] * o['scale'][2]
    block['min'][0] = block['min'][0] * o['scale'][0]
    block['min'][1] = block['min'][1] * o['scale'][1]
    block['min'][2] = block['min'][2] * o['scale'][2]
    block['max'][0], block['max'][2] = rotate([0,0], [block['max'][0], block['max'][2]], o['orient'])
    block['min'][0], block['min'][2] = rotate([0,0], [block['min'][0], block['min'][2]], o['orient'])
    block['max'][0] = block['max'][0] + o['translate'][0]
    block['max'][1] = block['max'][1] + o['translate'][1]
    block['max'][2] = block['max'][2] + o['translate'][2]
    block['min'][0] = block['min'][0] + o['translate'][0]
    block['min'][1] = block['min'][1] + o['translate'][1]
    block['min'][2] = block['min'][2] + o['translate'][2]
    for i in range(0, 3):
        new_max = max(block['max'][i], block['min'][i])
        new_min = min(block['max'][i], block['min'][i])
        block['max'][i] = new_max
        block['min'][i] = new_min
    windoorbb = np.array(currentwindoor['four_points_xz'], dtype=np.float)
    block['windoorbb'] = rotate_bb_local_np(windoorbb, o['orient'], np.array([o['scale'][0], o['scale'][2]], dtype=np.float))
    block['windoorbb'][:, 0] += o['translate'][0]
    block['windoorbb'][:, 1] += o['translate'][2]
    return block

with open('../latentspace/windoorblock.json') as f:
    windoorblock = json.load(f)

def areDoorsInRoom(level):
    level_doorfix = level.copy()
    # for each room in level, check each door; 
    for room in level_doorfix['rooms']:
        if not os.path.exists('room/{}/{}f.obj'.format(room['origin'], room['modelId'])):
            continue
        try:
            room_meta = p2d('.', 'room/{}/{}f.obj'.format(room['origin'], room['modelId']))
            room_polygon = Polygon(room_meta[:, 0:2]) # requires python library 'shapely'
        except Exception as e:
            print(e)
            continue
        for r in level['rooms']:
            for obj in r['objList']:
                if obj is None:
                    continue
                if 'coarseSemantic' not in obj:
                    continue
                if obj['coarseSemantic'] != 'door':
                    continue
                block = windoorblock_f(obj)
                block_polygon = Polygon(block['windoorbb']).buffer(.05)
                if room_polygon.intersects(block_polygon) and obj not in room['objList']:
                    new_obj = obj.copy()
                    new_obj['roomId'] = room['roomId']
                    room['objList'].append(new_obj)
    return level_doorfix

def batch():
    si = 3062
    housenames = os.listdir('./level')[si:]
    for housename in housenames:
        print(f'start house {si}. ')
        si += 1
        for levelname in os.listdir(f'./level/{housename}'):
            try:
                with open(f'./level/{housename}/{levelname}') as f:
                    print(f'./level/{housename}/{levelname}')
                    level = json.load(f)
            except PermissionError:
                continue
            level_fix = areDoorsInRoom(level)
            if not os.path.exists(f'./level_doorfix/{housename}'):
                os.makedirs(f'./level_doorfix/{housename}')
            with open(f'./level_doorfix/{housename}/{levelname}', 'w') as f:
                json.dump(level_fix, f)

def case1():
    with open('./case1.json') as f:
        case1 = json.load(f)
    case1_fix = areDoorsInRoom(case1)
    with open('./case1_fix.json', 'w') as f:
        json.dump(case1_fix, f)

if __name__ == '__main__':
    batch()
