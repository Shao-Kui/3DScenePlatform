import os
import json
import time
import math
import torch
import random
import trimesh
import threading
import numpy as np
from alutil import naive_heuristic, attempt_heuristic, rotate_bb_local_np
from shapely.geometry.polygon import Polygon
from shapely.geometry import Point
from projection2d import processGeo as p2d, connected_component, getobjCat
from rec_release import rotate_pos_prior, rotate_bb_local_para, loss_2, loss_4
import patternChainv2 as patternChain

with open('./latentspace/obj_coarse_semantic.json') as f:
    obj_semantic = json.load(f)
with open('./latentspace/name_to_ls.json') as f:
    name_to_ls = json.load(f)
with open('./latentspace/ls_to_name.json') as f:
    ls_to_name = json.load(f)
with open('./latentspace/windoorblock.json') as f:
    windoorblock = json.load(f)
BANNED = ['switch', 'column', 'fireplace', 'pet', 'range_hood', 'heater','curtain', 'person', 
'Pendant Lamp', 'Ceiling Lamp']
leaderlist = ['double_bed', 'desk', 'coffee_table', 'King-size Bed', 'Coffee Table']
hyperleaders = ['coffee_table', 'dining_table', 'Coffee Table', 'Dining Table', 'King-size Bed', 'Corner/Side Table']
NaiveChainList = ['kitchen_cabinet', 'shelving']
PRIORS = "./latentspace/pos-orient-4/{}.json"
with open('./latentspace/nwdo-represent.json') as f:
    wallpriors = json.load(f)
priors = {}
priors['pos'] = {}
priors['ori'] = {}
HYPER = './latentspace/pos-orient-3/hyper/{}-{}.json'
bbcache = {}
AABBcache = {}

def preload_prior(centername, objname):
    # rng = np.random.default_rng()
    priorid = "{}-{}".format(centername, objname)
    if priorid not in priors['pos']:
        if not os.path.isfile(PRIORS.format(centername)):
            return
        with open(PRIORS.format(centername)) as f:
            thepriors = json.load(f)
            if getobjCat(objname) not in thepriors:
                return
            theprior = np.array(thepriors[getobjCat(objname)], dtype=np.float)
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
    # if priorid in priors['chain'] and usechain:
    #     if len(priors['nextchain'][priorid]) == 0: 
    #         # warning: we should delete objects beyond the pattern chain; 
    #         priors['nextchain'][priorid] = priors['chain'][priorid][np.random.randint(len(priors['chain'][priorid]))].copy()
    #     pindex = priors['nextchain'][priorid].pop(0)
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
    print(rnms)
    pth = HYPER.format(pend_group[did]['modelId'], rnms)
    if os.path.exists(pth):
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
        # 3D-sized of subordinate objects are different, so individual hyper-relations are still needed; 
        if rnms not in patternChain.pendingList and pend_group[did]['coarseSemantic'] in hyperleaders: # len(set(relatednames)) > 1 and
            patternChain.pendingList.append(rnms)
            print(f'Start to generating hyper relations for {pend_group[did]["modelId"]} ...')
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
        # for oid in range(len(pend_group)):
        #     o = pend_group[oid]
        #     print(o)
        #     if o['id'] == ao['id']:
        #         cg['leaderID'] = oid
        cg['leaderID'] = pend_group.index(ao)
    dominator = pend_group[cg['leaderID']]
    # set leader to (0, 0, 0, 0)
    # keep input Y currently...
    pend_group[cg['leaderID']]['translate'] = [0.0, pend_group[cg['leaderID']]['translate'][1], 0.0]
    pend_group[cg['leaderID']]['rotate'] = [0.0, 0.0, 0.0]
    pend_group[cg['leaderID']]['orient'] = 0.0
    # get wall orient offset for leader; 
    if dominator['modelId'] in wallpriors:
        doris = wallpriors[dominator['modelId']]['ori']
    else:
        doris = [0.0, 0.0]
    if len(doris) != 0:
        cg['orient_offset'] = doris[np.random.randint(len(doris))]
        # pend_group[cg['leaderID']]['orient'] += cg['orient_offset']
    else:
        cg['orient_offset'] = 0.
    # print('dominant obj: {} ({}). '.format(dominator['modelId'], dominator['coarseSemantic']))
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
    block = {}
    block['modelId'] = o['modelId']
    block['coarseSemantic'] = o['coarseSemantic']
    block['max'] = o['bbox']['max'].copy()
    block['min'] = o['bbox']['min'].copy()
    return block

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

def load_boundingbox(i):
    if i in bbcache:
        return bbcache[i]
    if os.path.exists(f'./dataset/object/{i}/{i}-4p.json'):
        try:
            with open(f'./dataset/object/{i}/{i}-4p.json') as f:
                bbcache[i] = json.load(f)
            return bbcache[i]
        except json.decoder.JSONDecodeError as e:
            print(e)
    mesh = as_mesh(trimesh.load(f'./dataset/object/{i}/{i}.obj'))
    bb = np.zeros(shape=(4,2)).tolist()
    bb[0][0] = np.max(mesh.vertices[:, 0]).tolist()
    bb[0][1] = np.max(mesh.vertices[:, 2]).tolist()
    bb[1][0] = np.min(mesh.vertices[:, 0]).tolist()
    bb[1][1] = np.max(mesh.vertices[:, 2]).tolist()
    bb[2][0] = np.min(mesh.vertices[:, 0]).tolist()
    bb[2][1] = np.min(mesh.vertices[:, 2]).tolist()
    bb[3][0] = np.max(mesh.vertices[:, 0]).tolist()
    bb[3][1] = np.min(mesh.vertices[:, 2]).tolist()
    with open(f'./dataset/object/{i}/{i}-4p.json', 'w') as f:
        json.dump(bb, f)
    bbcache[i] = bb
    return bbcache[i]

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

def sceneSynthesis(rj):
    print(rj['origin'])
    start_time = time.time()
    pend_obj_list = []
    bbindex = []
    blocks = []
    random.shuffle(rj['objList'])
    # bounding boxes of given furniture objects; 
    boundingboxes = []
    max_points = []
    min_points = []
    # identifying objects to arrange; 
    for o in rj['objList']:
        if o is None:
            # print('this is a None object; ')
            continue
        if 'modelId' not in o:
            continue
        if 'coarseSemantic' not in o:
            o['coarseSemantic'] = getobjCat(o['modelId'])
        if o['coarseSemantic'] in BANNED:
            # print('a given object is not a furniture;' )
            continue
        if o['coarseSemantic'] == 'door' or o['coarseSemantic'] == 'window' or o['coarseSemantic'] == 'Door' or o['coarseSemantic'] == 'Window':
            blocks.append(windoorblock_f(o))
            continue
        try:
            boundingboxes.append(load_boundingbox(o['modelId']))
        except Exception as e:
            continue
        aabb = load_AABB(o['modelId'])
        max_points.append(aabb['max'])
        min_points.append(aabb['min'])
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
                if obj['modelId'] not in center['childnum']:
                    center['childnum'][obj['modelId']] = 0
                # if center['childnum'][obj['modelId']] >= priors['chainlength'][pid]:
                #     continue
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
        if cg['objList'][cg['leaderID']]['modelId'] in ['781'] and cg['objList'][cg['leaderID']]['translate'][1] == 0:
            cg['objList'][cg['leaderID']]['translate'][1] = 1.04
        cgs.append(cg)
    # load and process room shapes; 
    room_meta = p2d('.', '/dataset/room/{}/{}f.obj'.format(rj['origin'], rj['modelId']))
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
    bb = torch.tensor(boundingboxes).float()
    max_points = torch.tensor(max_points).float()
    min_points = torch.tensor(min_points).float()
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
    # generate layout of coherent groups; 
    attempt_heuristic(cgs, room_meta, blocks)
    for cg in cgs:
        # the following code is reserving for lifting of each coherent group; 
        cg['translate'][0] += np.sin(cg['orient']) * 0.08
        cg['translate'][2] += np.cos(cg['orient']) * 0.08
        # if cg['objList'][cg['leaderID']]['coarseSemantic'] in ['sink', 'dressing_table', 'picture_frame', 'television', 'mirror', 'clock', 'dining_table']:
        #     cg['translate'][0] += np.sin(cg['orient']) * 0.08
        #     cg['translate'][2] += np.cos(cg['orient']) * 0.08
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
        # (o['modelId'], o['coarseSemantic'])
        # for j in range(len(pend_obj_list)):
        #     if csrrelation[i][j] == 1.0:
        #         print("--->>>", pend_obj_list[j]['modelId'], pend_obj_list[j]['coarseSemantic'])
    print("\r\n --- %s secondes --- \r\n" % (time.time() - start_time))
    return rj

if __name__ == "__main__":
    with open('./examples/{}.json'.format("4cc6dba0-a26e-42cb-a964-06cb78d60bae-l2685-dl (20)")) as f:
        ex = json.load(f)
    sceneSynthesis(ex['rooms'][3])
    # print()
