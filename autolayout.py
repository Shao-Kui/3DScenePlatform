import os
import json
import time
import math
import torch
import numpy as np
from shapely.geometry.polygon import Polygon
from shapely.geometry import Point
from projection2d import process as p2d, connected_component
from rec_release import rotate_pos_prior, rotate_bb_local_para, loss_2, loss_4

with open('./latentspace/obj-semantic.json') as f:
    obj_semantic = json.load(f)
with open('./latentspace/name_to_ls.json') as f:
    name_to_ls = json.load(f)
with open('./latentspace/ls_to_name.json') as f:
    ls_to_name = json.load(f)

BANNED = ['switch', 'column', 'fireplace', 'pet', 'range_hood', 'heater']
leaderlist = ['double_bed', 'desk', 'coffee_table']
four_points_xz = torch.load("./latentspace/four_points_xz.pt")
ls = np.load("./latentspace/ls-release-2.npy")
PRIORS = "./latentspace/pos-orient-3/{}.json"
with open('./latentspace/nwdo-represent.json') as f:
    wallpriors = json.load(f)
priors = {}
priors['pos'] = {}
priors['ori'] = {}
REC_MAX = 20
SSIZE = 1000

def preload_prior(centername, objname):
    global SSIZE
    rng = np.random.default_rng()
    priorid = "{}-{}".format(centername, objname)
    if priorid not in priors['pos']:
        if not os.path.isfile(PRIORS.format(centername)):
            return
        with open(PRIORS.format(centername)) as f:
            thepriors = json.load(f)
            if objname not in thepriors:
                return
            theprior = np.array(thepriors[objname], dtype=np.float)
        while len(theprior) < SSIZE:
            theprior = np.vstack((theprior, theprior))
        rng.shuffle(theprior)
        priors['pos'][priorid] = torch.from_numpy(theprior[:, 0:3]).float()
        priors['ori'][priorid] = torch.from_numpy(theprior[:, 3].flatten()).float()

def heuristic_assign(dominator, o):
    priorid = "{}-{}".format(dominator['modelId'], o['modelId'])
    pos_prior = rotate_pos_prior(priors['pos'][priorid], torch.tensor(dominator['orient'], dtype=torch.float))
    ori_prior = priors['ori'][priorid]
    pindex = np.random.randint(len(pos_prior))
    o['translate'][0] = dominator['translate'][0] + pos_prior[pindex][0].item()
    o['translate'][1] = dominator['translate'][1] + pos_prior[pindex][1].item()
    o['translate'][2] = dominator['translate'][2] + pos_prior[pindex][2].item()
    o['orient'] = dominator['orient'] + ori_prior[pindex].item()

def heuristic_recur(pend_group, did, adj):
    dominator = pend_group[did]
    if dominator['isHeu']:
        return
    dominator['isHeu'] = True
    for oid in range(len(pend_group)):
        o = pend_group[oid]
        if o['isHeu']:
            continue
        if adj[did, oid] == 1.0:
            heuristic_assign(dominator, o)
    for oid in range(len(pend_group)):
        if adj[did, oid] == 1.0:
            heuristic_recur(pend_group, oid, adj)

def heuristic(cg):
    pend_group = cg['objList']
    adj = cg['csrrelation']
    # determine leader; 
    for oid in range(len(pend_group)):
        o = pend_group[oid]
        if o['coarseSemantic'] in leaderlist:
            cg['leaderID'] = oid
    if 'leaderID' not in cg:
        cg['leaderID'] = torch.argmax(torch.sum(adj, axis=1) + torch.sum(adj, axis=0)).item()
    dominator = pend_group[cg['leaderID']]
    # set leader to (0, 0, 0, 0)
    # keep input Y currently...
    pend_group[cg['leaderID']]['translate'] = [0.0, pend_group[cg['leaderID']]['translate'][1], 0.0]
    pend_group[cg['leaderID']]['rotate'] = [0.0, 0.0, 0.0]
    pend_group[cg['leaderID']]['orient'] = 0.0
    # get wall orient offset for leader; 
    doris = wallpriors[dominator['modelId']]['ori']
    if len(doris) != 0:
        cg['orient_offset'] = doris[np.random.randint(len(doris))]
    else:
        cg['orient_offset'] = 0.
    print('dominant obj: {} ({}). '.format(dominator['modelId'], dominator['coarseSemantic']))
    for o in pend_group:
        o['isHeu'] = False
    heuristic_recur(pend_group, cg['leaderID'], adj)

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

def wall_out_dis(bb, walls, wallid):
    wallid = wallid % len(walls)
    p1 = walls[wallid, 0:2]
    p2 = walls[(wallid+1) % len(walls), 0:2]
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
    p2 = walls[(wallid+1) % len(walls), 0:2]
    dets = np.ones(shape=(len(cg['bb']), 3, 3), dtype=np.float)
    dets[:, 0:2, 0] = p1
    dets[:, 0:2, 1] = p2
    dets[:, 0:2, 2] = cg['bb']
    dets = np.linalg.det(dets) / np.linalg.norm(p1 - p2)
    dets[dets > 0.] = 0.
    dets = np.abs(dets)
    dis = np.max(dets)
    t += walls[wallid, 2:4] * dis
    t += wall_out_dis(cg['bb'], walls, wallid-1)
    t += wall_out_dis(cg['bb'], walls, wallid+1)
    cg['translate'][0] = t[0]
    cg['translate'][2] = t[1]

def sceneSynthesis(rj):
    pend_obj_list = []
    bbindex = []
    # identifying objects to arrange; 
    for o in rj['objList']:
        if o is None or o['modelId'] not in obj_semantic:
            continue
        if 'coarseSemantic' in o:
            if o['coarseSemantic'] in BANNED:
                continue
        bbindex.append(name_to_ls[o['modelId']])
        pend_obj_list.append(o)
    # load priors; 
    csrrelation = torch.zeros((len(pend_obj_list), len(pend_obj_list)), dtype=torch.float)
    for center in pend_obj_list:
        for obj in pend_obj_list:
            preload_prior(center['modelId'], obj['modelId'])
    for centerid in range(len(pend_obj_list)):
        center = pend_obj_list[centerid]
        for objid in range(len(pend_obj_list)):
            if objid == centerid:
                csrrelation[centerid, objid] = 0.
                continue
            obj = pend_obj_list[objid]
            if "{}-{}".format(center['modelId'], obj['modelId']) in priors['pos']:
                csrrelation[centerid, objid] = 1.
                csrrelation[objid, centerid] = 1.
            else:
                csrrelation[centerid, objid] = 0.
                continue
    # partition coherent groups; 
    pend_groups = connected_component(np.arange(len(pend_obj_list)), csrrelation)
    cgs = []
    for pend_group in pend_groups:
        cg = {}
        cg['objList'] = [pend_obj_list[i] for i in pend_group]
        cg['csrrelation'] = csrrelation[pend_group][:, pend_group]
        cg['translate'] = [0.0, 0.0, 0.0]
        cg['orient'] = 0.0
        heuristic(cg)
        cgs.append(cg)
    # load and process room shapes; 
    room_meta = p2d('.', '/suncg/room/{}/{}f.obj'.format(rj['origin'], rj['modelId']))
    room_polygon = Polygon(room_meta[:, 0:2]) # requires python library 'shapely'
    room_shape = torch.from_numpy(room_meta[:, 0:2]).float()
    room_shape_norm = torch.from_numpy(room_meta).float()

    translate = torch.zeros((len(pend_obj_list), 3)).float()
    orient = torch.zeros((len(pend_obj_list))).float()
    scale = torch.zeros((len(pend_obj_list), 3)).float()
    
    for i in range(len(pend_obj_list)):
        translate[i][0] = pend_obj_list[i]['translate'][0]
        translate[i][1] = pend_obj_list[i]['translate'][1]
        translate[i][2] = pend_obj_list[i]['translate'][2]
        orient[i] = pend_obj_list[i]['orient']
        scale[i][0] = pend_obj_list[i]['scale'][0]
        scale[i][1] = pend_obj_list[i]['scale'][1]
        scale[i][2] = pend_obj_list[i]['scale'][2]
    bb = four_points_xz[bbindex].float()
    for i in range(len(pend_obj_list)):
        bb[i] = rotate_bb_local_para(bb[i], orient[i], scale[i][[0, 2]])
    bb_tran = translate.reshape(len(pend_obj_list), 1, 3)[:, :, [0, 2]] + bb
    # calculate bounding box of coherent groups; 
    for gid in range(len(pend_groups)):
        pend_group = pend_groups[gid]
        cg = cgs[gid]
        points = bb_tran[pend_group].reshape(-1, 2)
        maxp = torch.max(points, dim=0)[0]
        minp = torch.min(points, dim=0)[0]
        cg['bb'] = torch.zeros((4, 2), dtype=torch.float)
        cg['bb'][0] = maxp
        cg['bb'][1][0] = minp[0]
        cg['bb'][1][1] = maxp[1]
        cg['bb'][2] = minp
        cg['bb'][3][0] = maxp[0]
        cg['bb'][3][1] = minp[1]
    # assingning walls to each coherent group;
    # note that it is better to set segments to each group; (improvement for intern student :) ~~~ )
    wallindices = np.arange(len(room_shape), dtype=np.int)
    np.random.shuffle(wallindices)
    for index, cg in zip(range(len(cgs)), cgs):
        cg['wallid'] = wallindices[index % len(wallindices)]
        ratio = np.random.rand()
        p1 = room_shape[cg['wallid']]
        p2 = room_shape[(cg['wallid']+1) % len(room_shape)]
        p = ratio * p1 + (1 - ratio) * p2
        cg['translate'][0] = p[0].item()
        cg['translate'][2] = p[1].item()
        heuristic_wall(cg, room_meta)
    for cg in cgs:
        for o in cg['objList']:
            o['translate'][0], o['translate'][2] = rotate([0, 0], [o['translate'][0], o['translate'][2]], cg['orient'])
            o['orient'] += cg['orient']
            o['rotate'][0] = 0.0
            o['rotate'][1] = o['orient']
            o['rotate'][2] = 0.0
            o['translate'][0] += cg['translate'][0]
            o['translate'][1] += cg['translate'][1]
            o['translate'][2] += cg['translate'][2]
    # log coherent groups; 
    for i in range(len(pend_obj_list)):
        o = pend_obj_list[i]
        if 'coarseSemantic' not in o:
            break
        print(o['modelId'], o['coarseSemantic'])
        for j in range(len(pend_obj_list)):
            if csrrelation[i][j] == 1.0:
                print("--->>>", pend_obj_list[j]['modelId'], pend_obj_list[j]['coarseSemantic'])
    return rj

if __name__ == "__main__":
    with open('./examples/{}.json'.format("3f6688ae77eaebd28388f96efb31517c-l2")) as f:
        ex = json.load(f)
    print(sceneSynthesis(ex['rooms'][1]))