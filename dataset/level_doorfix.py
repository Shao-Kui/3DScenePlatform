import json
import os
import math
import numpy as np
from shapely.geometry.polygon import Polygon
from projection2d import processGeo as p2d
"""
This script is used to fix issues of 
'one door belongs to multiple rooms'; 
"""
with open('sk_to_ali.json') as f:
    sk_to_ali = json.load(f)
with open('full-obj-semantic_suncg.json') as f:
    suncg = json.load(f)

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
    block = {}
    block['modelId'] = o['modelId']
    block['coarseSemantic'] = o['coarseSemantic']
    block['max'] = o['bbox']['max'].copy()
    block['min'] = o['bbox']['min'].copy()
    block['windoorbb'] = []
    block['windoorbb'].append([block['max'][0], block['max'][2]])
    block['windoorbb'].append([block['min'][0], block['max'][2]])
    block['windoorbb'].append([block['min'][0], block['min'][2]])
    block['windoorbb'].append([block['max'][0], block['min'][2]])
    return block

with open('../latentspace/windoorblock.json') as f:
    windoorblock = json.load(f)

def areDoorsInRoom(level):
    level_doorfix = level.copy()
    # for each room in level, check each door; 
    for room in level_doorfix['rooms']:
        # inDatabase Check: 
        for o in room['objList']:
            if o['modelId'] in sk_to_ali or o['modelId'] in suncg:
                o['inDatabase'] = True
            else:
                o['inDatabase'] = False
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
                if obj['coarseSemantic'] not in ['door', 'window', 'Door', 'Window']:
                    continue
                block = windoorblock_f(obj)
                block_polygon = Polygon(block['windoorbb']).buffer(.06)
                if room_polygon.intersects(block_polygon) and obj not in room['objList']:
                    new_obj = obj.copy()
                    new_obj['roomId'] = room['roomId']
                    room['objList'].append(new_obj)
    return level_doorfix

def areDoorsInRoom2021(level):
    level_doorfix = level.copy()
    for room in level_doorfix['rooms']:
        room['blockList'] = []
    # for each room in level, check each door; 
    for room in level_doorfix['rooms']:
        # inDatabase Check: 
        for o in room['objList']:
            if o['modelId'] in sk_to_ali or o['modelId'] in suncg:
                o['inDatabase'] = True
            else:
                o['inDatabase'] = False
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
                if obj['coarseSemantic'] not in ['door', 'window', 'Door', 'Window']:
                    continue
                block = windoorblock_f(obj)
                block_polygon = Polygon(block['windoorbb']).buffer(.03)
                # for this time, we do not duplicate doors, instead we add roomIds to the obj. 
                if room_polygon.intersects(block_polygon):
                    if 'roomIds' not in obj:
                        obj['roomIds'] = []
                    obj['roomIds'].append(room['roomId'])
                    if obj not in room['objList']:
                        new_obj = obj.copy()
                        new_obj['roomId'] = room['roomId']
                        room['blockList'].append(new_obj)
    return level_doorfix

def batch():
    si = 0
    levelnames = os.listdir('./alilevel_oriFix')[si:]
    for levelname in levelnames:
        if si % 1000 == 0:
            print(f'start level {levelname}. ({si})')
        si += 1
        try:
            with open(f'./alilevel_oriFix/{levelname}') as f:
                level = json.load(f)
        except PermissionError:
            continue
        level_fix = areDoorsInRoom2021(level)
        with open(f'./Levels2021/{levelname}', 'w') as f:
            json.dump(level_fix, f)

def case1():
    with open('./case1.json') as f:
        case1 = json.load(f)
    case1_fix = areDoorsInRoom(case1)
    with open('./case1_fix.json', 'w') as f:
        json.dump(case1_fix, f)

if __name__ == '__main__':
    batch()
