import numpy as np
import torch
from relayout import *


def rotate_bb_local_np(points, angle, scale):
    result = points.copy()
    scaled = points.copy()
    scaled = scaled * scale
    result[:, 0] = np.cos(angle) * scaled[:, 0] + np.sin(angle) * scaled[:, 1]
    result[:, 1] = -np.sin(angle) * scaled[:, 0] + np.cos(angle) * scaled[:, 1]
    return result


def wall_out_dis(bb, walls, wallid):
    wallid = wallid % len(walls)
    p1 = walls[wallid, 0:2]
    p2 = walls[(wallid + 1) % len(walls), 0:2]
    dets = np.ones(shape=(len(bb), 3, 3), dtype=np.float)
    dets[:, 0:2, 0] = p1
    dets[:, 0:2, 1] = p2
    dets[:, 0:2, 2] = bb
    dets = np.linalg.det(dets) / np.linalg.norm(p1 - p2)
    dets[dets > 0.] = 0.
    dets = np.abs(dets)
    dets = np.max(dets)
    gradi = walls[wallid, 2:4] * dets
    return gradi


def heuristic_wall(cg, walls):
    print('start to place {} (dominator). '.format(cg['objList'][cg['leaderID']]['coarseSemantic']))
    walln = walls[:, 2:4]
    wallid = cg['wallid']
    # determine main direction w.r.t wall; 
    # currently, only one strategy exist, i.e., cg follows leader and leader orients 0.0; 
    # cg['orient'] = cg['orient_offset'] + np.arctan2(walln[wallid][0], walln[wallid][1])
    cg['orient'] = np.arctan2(walln[wallid][0], walln[wallid][1])
    # print('Offsets: ', cg['objList'][cg['leaderID']]['coarseSemantic'], cg['orient_offset'])
    t = np.array([cg['translate'][0], cg['translate'][2]], dtype=np.float)
    cg['bb'] = rotate_bb_local_np(cg['bb'].numpy(), cg['orient'], np.array([1., 1.], dtype=np.float))
    cg['bb'] += t
    p1 = walls[wallid, 0:2]
    p2 = walls[(wallid + 1) % len(walls), 0:2]
    dets = np.ones(shape=(len(cg['bb']), 3, 3), dtype=np.float)
    dets[:, 0:2, 0] = p1
    dets[:, 0:2, 1] = p2
    dets[:, 0:2, 2] = cg['bb']
    dets = np.linalg.det(dets) / np.linalg.norm(p1 - p2)
    dets[dets > 0.] = 0.
    dets = np.abs(dets)
    dis = np.max(dets)
    t += walls[wallid, 2:4] * dis
    t += wall_out_dis(cg['bb'], walls, wallid - 1)
    t += wall_out_dis(cg['bb'], walls, wallid + 1)
    cg['translate'][0] = t[0]
    cg['translate'][2] = t[1]


def naive_heuristic(cgs, room_meta, block=None):
    # pre-process room meta; 
    room_shape = torch.from_numpy(room_meta[:, 0:2]).float()
    room_shape_norm = torch.from_numpy(room_meta).float()
    # assingning walls to each coherent group; 
    wallindices = np.arange(len(room_shape), dtype=np.int)
    np.random.shuffle(wallindices)
    for index, cg in zip(range(len(cgs)), cgs):
        cg['wallid'] = wallindices[index % len(wallindices)]
        ratio = np.random.rand()
        p1 = room_shape[cg['wallid']]
        p2 = room_shape[(cg['wallid'] + 1) % len(room_shape)]
        p = ratio * p1 + (1 - ratio) * p2
        cg['translate'][0] = p[0].item()
        cg['translate'][2] = p[1].item()
        heuristic_wall(cg, room_meta)

def attempt_heuristic(cgs, room_polygon, blocks=None):
    # coded by Weiyu
    function_areas = []
    block_bb = []
    windows_bb = []

    for cg in cgs:
        # print(cg)
        t = cg['bb'].numpy()
        function_areas.append(
            [np.min(t[:, 0]), cg['ground'], np.min(t[:, 1]), np.max(t[:, 0]), cg['height'], np.max(t[:, 1])])

    for b in blocks:
        if b['coarseSemantic'] == 'door':
            block_bb.append(b['min'] + b['max'])
        else:
            windows_bb.append(b['min'] + b['max'])
        # print(b)

    """
    print(function_areas)
    print(room_polygon)
    print(block_bb)
    print(windows_bb)
    """
    print(block_bb)
    print(windows_bb)

    rotations, translations = try_possible_layout(function_areas, room_polygon, block_bb, windows_bb)
    # The translation data is two dimensional, so we add the y coordinate.
    for t in translations:
        t.insert(1, 0)

    # Change the rotation and translation.
    for i in range(len(rotations)):
        # attention here
        cgs[i]['orient'] = rotations[i]
        cgs[i]['translate'] = translations[i]
    pass
