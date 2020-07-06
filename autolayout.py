import os
import json
import time
import math
import torch
import random
import threading
import numpy as np
from alutil import naive_heuristic, attempt_heuristic, rotate_bb_local_np
from shapely.geometry.polygon import Polygon
from shapely.geometry import Point
from projection2d import process as p2d, connected_component
from rec_release import rotate_pos_prior, rotate_bb_local_para, loss_2, loss_4
import patternChain

with open('./latentspace/obj-semantic.json') as f:
    obj_semantic = json.load(f)
with open('./latentspace/name_to_ls.json') as f:
    name_to_ls = json.load(f)
with open('./latentspace/ls_to_name.json') as f:
    ls_to_name = json.load(f)
with open('./latentspace/windoorblock.json') as f:
    windoorblock = json.load(f)
max_bb = torch.load('./latentspace/max_bb.pt')
min_bb = torch.load('./latentspace/min_bb.pt')
# , 'picture_frame'
BANNED = ['switch', 'column', 'fireplace', 'pet', 'range_hood', 'heater']
leaderlist = ['double_bed', 'desk', 'coffee_table']
NaiveChainList = ['kitchen_cabinet', 'shelving']
four_points_xz = torch.load("./latentspace/four_points_xz.pt")
ls = np.load("./latentspace/ls-release-2.npy")
PRIORS = "./latentspace/pos-orient-3/{}.json"
with open('./latentspace/nwdo-represent.json') as f:
    wallpriors = json.load(f)
priors = {}
priors['pos'] = {}
priors['ori'] = {}
priors['chain'] = {}
priors['nextchain'] = {}
priors['chainlength'] = {}
HYPER = './latentspace/pos-orient-3/hyper/{}-{}.json'
REC_MAX = 20
SSIZE = 1000

def preload_prior(centername, objname):
    global SSIZE
    rng = np.random.default_rng()
    priorid = "{}-{}".format(centername, objname)
    priors['nextchain'][priorid] = []
    if priorid not in priors['pos']:
        priors['chainlength'][priorid] = 1
        if os.path.isfile(PRIORS.format(priorid)):
            with open(PRIORS.format(priorid)) as f:
                priors['chain'][priorid] = json.load(f)
                priors['nextchain'][priorid] = priors['chain'][priorid][np.random.randint(len(priors['chain'][priorid]))].copy()
                priors['chainlength'][priorid] = len(priors['chain'][priorid][np.random.randint(len(priors['chain'][priorid]))])
        if not os.path.isfile(PRIORS.format(centername)):
            return
        with open(PRIORS.format(centername)) as f:
            thepriors = json.load(f)
            if objname not in thepriors:
                return
            theprior = np.array(thepriors[objname], dtype=np.float)
        while len(theprior) < SSIZE:
            theprior = np.vstack((theprior, theprior))
        # rng.shuffle(theprior)
        priors['pos'][priorid] = torch.from_numpy(theprior[:, 0:3]).float()
        priors['ori'][priorid] = torch.from_numpy(theprior[:, 3].flatten()).float()

def heuristic_assign(dominator, o, pindex=None, usechain=True):
    priorid = "{}-{}".format(dominator['modelId'], o['modelId'])
    pos_prior = rotate_pos_prior(priors['pos'][priorid], torch.tensor(dominator['orient'], dtype=torch.float))
    ori_prior = priors['ori'][priorid]
    if pindex is None:
        pindex = np.random.randint(len(pos_prior))
    # if pattern chains exist between two pending objects, we sample a pattern chain for relative transformations; 
    if priorid in priors['chain'] and usechain:
        print('use a pattern chain')
        if len(priors['nextchain'][priorid]) == 0: 
            # warning: we should delete objects beyond the pattern chain; 
            priors['nextchain'][priorid] = priors['chain'][priorid][np.random.randint(len(priors['chain'][priorid]))].copy()
        pindex = priors['nextchain'][priorid].pop(0)
    o['translate'][0] = dominator['translate'][0] + pos_prior[pindex][0].item() * dominator['scale'][0]
    o['translate'][1] = dominator['translate'][1] + pos_prior[pindex][1].item() * dominator['scale'][1]
    o['translate'][2] = dominator['translate'][2] + pos_prior[pindex][2].item() * dominator['scale'][2]
    o['orient'] = dominator['orient'] + ori_prior[pindex].item()
    o['isHeu'] = True

def heuristic_recur(pend_group, did, adj):
    dominator = pend_group[did]
    # check if hyper priors are available; 
    relatedIndeces = np.where(adj[did] == 1.)[0]
    relatednames = []
    for i in relatedIndeces:
        relatednames.append(pend_group[i]['modelId'])
    relatednames.sort()
    rnms = '_'.join(relatednames)
    pth = HYPER.format(pend_group[did]['modelId'], rnms)
    if os.path.exists(pth):
        print('Assembling hyper priors...')
        with open(pth) as f:
            hyperps = json.load(f)
        hyperp = hyperps[np.random.randint(len(hyperps))].copy()
        for i in relatedIndeces:
            o = pend_group[i]
            if o['isHeu']:
                continue
            try:
                pindex = hyperp[o['modelId']].pop()
            except Exception as e:
                print(e)
                continue
            heuristic_assign(dominator, o, pindex, False)
    else:
        if len(set(relatednames)) > 1 and rnms not in patternChain.pendingList and pend_group[did]['coarseSemantic'] in ['coffee_table', 'dining_table']:
            patternChain.pendingList.append(rnms)
            threading.Thread(target=patternChain.patternChain, args=(pend_group[did]['modelId'], relatednames)).start()
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
        # cg['leaderID'] = torch.argmax(torch.sum(adj, axis=1) + torch.sum(adj, axis=0)).item()
        # cg['leaderID'] = torch.argmax(torch.sum(adj, axis=1)).item()
        ao = pend_group[0]
        while ao['myparent'] is not None:
            ao = ao['myparent']
        cg['leaderID'] = pend_group.index(ao)
    dominator = pend_group[cg['leaderID']]
    print(dominator['coarseSemantic'])
    # set leader to (0, 0, 0, 0)
    # keep input Y currently...
    pend_group[cg['leaderID']]['translate'] = [0.0, pend_group[cg['leaderID']]['translate'][1], 0.0]
    pend_group[cg['leaderID']]['rotate'] = [0.0, 0.0, 0.0]
    pend_group[cg['leaderID']]['orient'] = 0.0
    # get wall orient offset for leader; 
    doris = wallpriors[dominator['modelId']]['ori']
    if len(doris) != 0:
        cg['orient_offset'] = doris[np.random.randint(len(doris))]
        # pend_group[cg['leaderID']]['orient'] += cg['orient_offset']
    else:
        cg['orient_offset'] = 0.
    print('dominant obj: {} ({}). '.format(dominator['modelId'], dominator['coarseSemantic']))
    # initially, all objects are not arranged; 
    for o in pend_group:
        o['isHeu'] = False
    pend_group[cg['leaderID']]['isHeu'] = True
    heuristic_recur(pend_group, cg['leaderID'], adj)

def rotate(origin, point, angle):
    ox = origin[0]
    oy = origin[1]
    px = point[0]
    py = point[1]
    qx = ox + math.cos(angle) * (px - ox) + math.sin(angle) * (py - oy)
    qy = oy - math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy)
    return qx, qy

'''
:param point: the given point in a 3D space
:param translate: the translation in 3D
:param angle: the rotation angle on XOZ plain
:param scale: the scale in 3D
'''
def transform_a_point(point, translate, angle, scale):
    result = point.clone()
    scaled = point.clone()
    scaled = point * scale
    result[0] =  torch.cos(angle) * scaled[0] + torch.sin(angle) * scaled[2]
    result[2] = -torch.sin(angle) * scaled[0] + torch.cos(angle) * scaled[2]
    return result + translate

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

def sceneSynthesis(rj):
    print(rj['origin'])
    pend_obj_list = []
    bbindex = []
    blocks = []
    random.shuffle(rj['objList'])
    # identifying objects to arrange; 
    for o in rj['objList']:
        if o is None:
            continue
        if 'coarseSemantic' not in o:
            continue
        if o['coarseSemantic'] in BANNED:
            continue
        if o['coarseSemantic'] == 'door' or o['coarseSemantic'] == 'window':
            blocks.append(windoorblock_f(o))
        if o['modelId'] not in obj_semantic:
            continue
        bbindex.append(name_to_ls[o['modelId']])
        o['childnum'] = {}
        o['myparent'] = None
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
                continue
            obj = pend_obj_list[objid]
            # if the obj has a parent, we have to continue; 
            # because if multiple parents exist, two parent may share a same child while another child has no parent;
            if obj['myparent'] is not None:
                continue
            pid = "{}-{}".format(center['modelId'], obj['modelId'])
            if pid in priors['pos']:
                print(pid)
                if obj['modelId'] not in center['childnum']:
                    center['childnum'][obj['modelId']] = 0
                if center['childnum'][obj['modelId']] >= priors['chainlength'][pid]:
                    continue
                csrrelation[centerid, objid] = 1.
                obj['myparent'] = center
                center['childnum'][obj['modelId']] += 1
    # partition coherent groups; 
    pend_groups = connected_component(np.arange(len(pend_obj_list)), csrrelation)
    cgs = []
    for pend_group in pend_groups:
        cg = {}
        cg['objList'] = [pend_obj_list[i] for i in pend_group]
        cg['csrrelation'] = csrrelation[pend_group][:, pend_group]
        cg['translate'] = [0.0, 0.0, 0.0]
        cg['orient'] = 0.0
        # determine layouts of each group; 
        heuristic(cg)
        # the following code is for chain pattern; 
        # if only one object exists in a cg && the object follows chain layout, 
        # e.g., kitchen cabinet, shelving, etc; 
        if len(cg['objList']) == 1 and cg['objList'][0]['coarseSemantic'] in NaiveChainList:
            cg['chain'] = cg['objList'][0]['coarseSemantic']
        else:
            cg['chain'] = 'n'
        cgs.append(cg)
    # load and process room shapes; 
    room_meta = p2d('.', '/suncg/room/{}/{}f.obj'.format(rj['origin'], rj['modelId']))
    room_polygon = Polygon(room_meta[:, 0:2]) # requires python library 'shapely'
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
    max_points = max_bb[bbindex].float()
    min_points = min_bb[bbindex].float()
    for i in range(len(pend_obj_list)):
        bb[i] = rotate_bb_local_para(bb[i], orient[i], scale[i][[0, 2]])
        max_points[i] = transform_a_point(max_points[i], translate[i], orient[i], scale[i])
        min_points[i] = transform_a_point(min_points[i], translate[i], orient[i], scale[i])
    bb_tran = translate.reshape(len(pend_obj_list), 1, 3)[:, :, [0, 2]] + bb # note that bbs are around (0,0,0) after heuristic(cg)
    # calculate bounding box of coherent groups; 
    for gid in range(len(pend_groups)):
        pend_group = pend_groups[gid]
        cg = cgs[gid]
        points = bb_tran[pend_group].reshape(-1, 2)
        max_points_of_cg = max_points[pend_group]
        min_points_of_cg = min_points[pend_group]
        maxp = torch.max(points, dim=0)[0]
        minp = torch.min(points, dim=0)[0]
        cg['bb'] = torch.zeros((4, 2), dtype=torch.float)
        cg['bb'][0] = maxp
        cg['bb'][1][0] = minp[0]
        cg['bb'][1][1] = maxp[1]
        cg['bb'][2] = minp
        cg['bb'][3][0] = maxp[0]
        cg['bb'][3][1] = minp[1]
        cg['height'] = torch.max(max_points_of_cg, dim=0)[0][1].item()
        cg['ground'] = torch.min(min_points_of_cg, dim=0)[0][1].item()
    # generate
    attempt_heuristic(cgs, room_meta, blocks)
    for cg in cgs:
        if cg['objList'][cg['leaderID']]['coarseSemantic'] in ['sink', 'dressing_table', 'picture_frame', 'television', 'mirror', 'clock', 'dining_table']:
            cg['translate'][0] += np.sin(cg['orient']) * 0.08
            cg['translate'][2] += np.cos(cg['orient']) * 0.08
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