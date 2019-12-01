import os
import json
import time
import torch
import numpy as np
from shapely.geometry.polygon import Polygon
from shapely.geometry import Point
from projection2d import process as p2d, connected_component
from sk_loader import csrmatrix, ymatrix, obj_semantic, name_to_ls, ls_to_name, wallvector, cornervector
from rec_release import rotate_pos_prior, rotate_bb_local_para, loss_2, loss_4

BANNED = ['switch', 'column', 'fireplace', 'pet', 'range_hood', 'heater']
four_points_xz = torch.load("./latentspace/four_points_xz.pt")
ls = np.load("./latentspace/ls-release-2.npy")
PRIORS = "./latentspace/pos-orient-denoised-2/{}.json"
with open('./latentspace/nwdo_ori.json') as f:
    heu_ori = json.load(f)
priors = {}
priors['pos'] = {}
priors['ori'] = {}

MAX_ITERATION = 0
REC_MAX = 20
SSIZE = 1000

def collision_loss_nxt(translate, room_shape, yrelation=None, wallrelation=None, cornerrelation=None):
    loss = loss_2(translate, yrelation=yrelation)  # pairwise collision loss
    loss += loss_4(translate, room_shape)  # not feasible for non-convex shape
    return loss

def distribution_loss_nxt(x, ori, pos_priors, ori_priors, csrrelation=None):
    if csrrelation is None:
        csrrelation = torch.ones((len(x), len(x)))
    # x should be pure translations of pending objects.
    diff = x - x[:, None]  # each row i means centering obj i and other objects move to its relative position
    diff = pos_priors - diff.reshape(len(x), len(x), 1, 2)
    diff = torch.norm(diff, dim=3)
    oridiff = torch.abs(ori - ori[:, None])
    oridiff.data[oridiff.data >  np.pi] -= 2 * np.pi
    oridiff.data[oridiff.data < -np.pi] += 2 * np.pi
    oridiff = torch.abs(oridiff)
    oridiff = torch.min(2 * np.pi - oridiff, oridiff)
    oridiff = torch.abs(ori_priors) - oridiff.reshape(len(x), len(x), 1)
    oridiff = torch.abs(oridiff)
    oridiff = torch.exp(oridiff)
    hausdorff = torch.min(diff + oridiff, dim=2)[0]
    return torch.sum(hausdorff * csrrelation)

def preload_prior(centername, objname):
    global SSIZE
    rng = np.random.default_rng()
    priorid = "{}-{}".format(centername, objname)
    if priorid not in priors['pos']:
        with open(PRIORS.format(centername)) as f:
            if csrmatrix[name_to_ls[centername], name_to_ls[objname]] == 0.0:
                theprior = np.zeros((SSIZE, 4), dtype=np.float)
            else:
                theprior = np.array(json.load(f)[objname], dtype=np.float)
            if len(theprior) == 0:
                theprior = np.zeros((SSIZE, 4), dtype=np.float)
            while len(theprior) < SSIZE:
                theprior = np.vstack((theprior, theprior))
            rng.shuffle(theprior)
            priors['pos'][priorid] = theprior[:, 0:3]
            priors['ori'][priorid] = theprior[:, 3].flatten()
        SSIZE = np.min((len(priors['pos'][priorid]), SSIZE))
        priors['pos'][priorid] = torch.from_numpy(priors['pos'][priorid]).float()
        priors['ori'][priorid] = torch.from_numpy(priors['ori'][priorid]).float()

def heuristic_assign(dominator, o):
    priorid = "{}-{}".format(dominator['modelId'], o['modelId'])
    pos_prior = rotate_pos_prior(priors['pos'][priorid], torch.tensor(dominator['orient'], dtype=torch.float))
    ori_prior = priors['ori'][priorid]
    pindex = np.random.randint(len(pos_prior))
    o['translate'][0] = dominator['translate'][0] + pos_prior[pindex][0]
    o['translate'][2] = dominator['translate'][2] + pos_prior[pindex][2]
    o['orient'] = dominator['orient'] + ori_prior[pindex]

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

def heuristic(pend_group, adj):
    if len(pend_group) == 1:
        o = pend_group[0]
        if o['modelId'] not in heu_ori:
            return
        doris = heu_ori[o['modelId']]
        if len(doris) != 0:
            o['orient'] = doris[np.random.randint(len(doris))]
    for o in pend_group:
        o['isHeu'] = False
    did = torch.argmax(torch.sum(adj, dim=1)).item()
    dominator = pend_group[did]
    doris = heu_ori[dominator['modelId']]
    print('dominant obj: {}. '.format(dominator['modelId']))
    if len(doris) != 0:
        dominator['orient'] = doris[np.random.randint(len(doris))]
    heuristic_recur(pend_group, did, adj)

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

def heuristic_wall(pend_group, walls):
    if len(pend_group) > 1:
        return
    o = pend_group[0]
    t = np.array([o['translate'][0], o['translate'][2]], dtype=np.float)
    bb = four_points_xz[name_to_ls[o['modelId']]].numpy()
    bb = rotate_bb_local_np(bb, o['orient'], np.array([o['scale'][0], o['scale'][2]], dtype=np.float))
    bb += t
    walln = walls[:, 2:4]
    o_ori = np.array([np.sin(o['orient']), np.cos(o['orient'])], dtype=np.float)
    wallid = np.argmin(np.linalg.norm(walln - o_ori, axis=1))
    p1 = walls[wallid, 0:2]
    p2 = walls[(wallid+1) % len(walls), 0:2]
    dets = np.ones(shape=(len(bb), 3, 3), dtype=np.float)
    dets[:, 0:2, 0] = p1
    dets[:, 0:2, 1] = p2
    dets[:, 0:2, 2] = bb
    dis = np.min(np.abs(np.linalg.det(dets))) / np.linalg.norm(p1 - p2)
    t += -walls[wallid, 2:4] * dis
    t += wall_out_dis(bb, walls, wallid-1)
    t += wall_out_dis(bb, walls, wallid+1)
    o['translate'][0] = t[0]
    o['translate'][2] = t[1]
directlist = []
sleeptimes = []
def sceneSynthesis(rj):
    global directlist
    if len(directlist) == 0:
        directlistdir = os.listdir('./directvideo-2')
        for dld in directlistdir:
            with open('./directvideo-2/{}'.format(dld)) as f:
                directlist.append(json.load(f))
        with open('./timecount.txt') as f:
            txts = f.read()
            txts = txts.split('\n')
            for txt in txts:
                sleeptimes.append(float(txt))
    if directlist[0]['origin'] == rj['origin']:
        ret = directlist[0]
        time.sleep(sleeptimes[0])
        del directlist[0]
        return ret
    pend_obj_list = []
    final_obj_list = []
    bbindex = []
    ol = rj['objList']
    print("Total Number of objects: ", len(ol))
    for o in ol:
        if o is None:
            continue
        if o['modelId'] not in obj_semantic:
            final_obj_list.append(o)
            continue
        if 'coarseSemantic' in o:
            print(o['modelId'], o['translate'])
            if o['coarseSemantic'] in BANNED:
                final_obj_list.append(o)
                continue
        bbindex.append(name_to_ls[o['modelId']])
        pend_obj_list.append(o)
    diag_indices_ = (torch.arange(len(pend_obj_list)), torch.arange(len(pend_obj_list)))
    yrelation = ymatrix[bbindex][:, bbindex]
    wallrelation = wallvector[bbindex]
    cornerrelation = cornervector[bbindex]
    csrrelation = csrmatrix[bbindex][:, bbindex]
    csrrelation[diag_indices_] = 0.0
    pend_groups = connected_component(np.arange(len(pend_obj_list)), csrrelation)
    for center in pend_obj_list:
        for obj in pend_obj_list:
            preload_prior(center['modelId'], obj['modelId'])
    start_time = time.time()
    for pend_group in pend_groups:
        print(pend_group)
        heuristic([pend_obj_list[i] for i in pend_group], csrrelation[pend_group][:, pend_group])
    room_meta = p2d('.', '/suncg/room/{}/{}f.obj'.format(rj['origin'], rj['modelId']))
    for pend_group in pend_groups:
        heuristic_wall([pend_obj_list[i] for i in pend_group], room_meta)
    pos_priors = torch.zeros(len(pend_obj_list), len(pend_obj_list), SSIZE, 3)
    ori_priors = torch.zeros(len(pend_obj_list), len(pend_obj_list), SSIZE)
    for centerid in range(len(pend_obj_list)):
        center = pend_obj_list[centerid]
        for objid in range(len(pend_obj_list)):
            if objid == centerid:
                continue
            obj = pend_obj_list[objid]
            priorid = "{}-{}".format(center['modelId'], obj['modelId'])
            pos_priors[centerid, objid] = rotate_pos_prior(priors['pos'][priorid][0: SSIZE], torch.tensor(center['orient'], dtype=torch.float))
            ori_priors[centerid, objid] = priors['ori'][priorid][0: SSIZE]
    # making sure that angles are between (-pi, pi)
    ori_priors[ori_priors >  np.pi] -= 2 * np.pi
    ori_priors[ori_priors < -np.pi] += 2 * np.pi
    room_polygon = Polygon(room_meta[:, 0:2])
    room_shape = torch.from_numpy(room_meta[:, 0:2]).float()
    room_shape_norm = torch.from_numpy(room_meta).float()
    translate = torch.zeros((len(pend_obj_list), 2)).float()
    orient = torch.zeros((len(pend_obj_list))).float()
    scale = torch.zeros((len(pend_obj_list), 3)).float()
    for i in range(len(pend_obj_list)):
        translate[i][0] = pend_obj_list[i]['translate'][0]
        translate[i][1] = pend_obj_list[i]['translate'][2]
        orient[i] = pend_obj_list[i]['orient']
        scale[i][0] = pend_obj_list[i]['scale'][0]
        scale[i][1] = pend_obj_list[i]['scale'][1]
        scale[i][2] = pend_obj_list[i]['scale'][2]

    bb = four_points_xz[bbindex].float()
    for i in range(len(pend_obj_list)):
        bb[i] = rotate_bb_local_para(bb[i], orient[i], scale[i][[0, 2]])

    translate.requires_grad_()
    iteration = 0
    loss = distribution_loss_nxt(translate, orient, pos_priors[:, :, :, [0, 2]], ori_priors, csrrelation)
    c_loss = collision_loss_nxt(translate.reshape(len(pend_obj_list), 1, 2) + bb, room_shape, yrelation * (1 - csrrelation), wallrelation, cornerrelation)
    loss += c_loss
    while loss.item() > 0.0 and iteration < MAX_ITERATION:
        print("Start iteration {}...".format(iteration))
        loss.backward()
        translate.data = translate.data - translate.grad * 0.05
        translate.grad = None
        loss = distribution_loss_nxt(translate, orient, pos_priors[:, :, :, [0, 2]], ori_priors, csrrelation)
        c_loss = collision_loss_nxt(translate.reshape(len(pend_obj_list), 1, 2) + bb, room_shape, yrelation * (1 - csrrelation), wallrelation, cornerrelation)
        loss += c_loss
        iteration += 1
    print("--- %s seconds ---" % (time.time() - start_time))
    print("final loss: {}".format(loss.item()))
    for i in range(len(pend_obj_list)):
        o = pend_obj_list[i]
        if 'coarseSemantic' not in o:
            break
        print(o['modelId'], o['coarseSemantic'])
        for j in range(len(pend_obj_list)):
            if csrrelation[i][j] == 1.0:
                print("--->>>", pend_obj_list[j]['modelId'], pend_obj_list[j]['coarseSemantic'])
    for i in range(len(pend_obj_list)):
        o = pend_obj_list[i]
        o['translate'][0] = translate[i][0].item()
        o['translate'][2] = translate[i][1].item()
        o['rotate'][0] = 0.0
        o['rotate'][1] = orient[i].item()
        o['rotate'][2] = 0.0
        o['orient'] = orient[i].item()
    return rj

def sceneSynthesis_MCMC(rj):
    pend_obj_list = []
    final_obj_list = []
    bbindex = []
    ol = rj['objList']
    print("Total Number of objects: ", len(ol))
    for o in ol:
        if o is None:
            continue
        if o['modelId'] not in obj_semantic:
            final_obj_list.append(o)
            continue
        if 'coarseSemantic' in o:
            if o['coarseSemantic'] in BANNED:
                final_obj_list.append(o)
                continue
        bbindex.append(name_to_ls[o['modelId']])
        pend_obj_list.append(o)
    diag_indices_ = (torch.arange(len(pend_obj_list)), torch.arange(len(pend_obj_list)))
    yrelation = ymatrix[bbindex][:, bbindex]
    wallrelation = wallvector[bbindex]
    cornerrelation = cornervector[bbindex]
    csrrelation = csrmatrix[bbindex][:, bbindex]
    csrrelation[diag_indices_] = 0.0
    pend_groups = connected_component(np.arange(len(pend_obj_list)), csrrelation)
    for center in pend_obj_list:
        for obj in pend_obj_list:
            preload_prior(center['modelId'], obj['modelId'])
    start_time = time.time()
    for pend_group in pend_groups:
        heuristic([pend_obj_list[i] for i in pend_group], csrrelation[pend_group][:, pend_group])
    room_meta = p2d('.', '/suncg/room/{}/{}f.obj'.format(rj['origin'], rj['modelId']))
    for pend_group in pend_groups:
        heuristic_wall([pend_obj_list[i] for i in pend_group], room_meta)
    pos_priors = torch.zeros(len(pend_obj_list), len(pend_obj_list), SSIZE, 3)
    ori_priors = torch.zeros(len(pend_obj_list), len(pend_obj_list), SSIZE)
    for centerid in range(len(pend_obj_list)):
        center = pend_obj_list[centerid]
        for objid in range(len(pend_obj_list)):
            if objid == centerid:
                continue
            obj = pend_obj_list[objid]
            priorid = "{}-{}".format(center['modelId'], obj['modelId'])
            pos_priors[centerid, objid] = rotate_pos_prior(priors['pos'][priorid][0: SSIZE], torch.tensor(center['orient'], dtype=torch.float))
            ori_priors[centerid, objid] = priors['ori'][priorid][0: SSIZE]
    # making sure that angles are between (-pi, pi)
    ori_priors[ori_priors >  np.pi] -= 2 * np.pi
    ori_priors[ori_priors < -np.pi] += 2 * np.pi
    room_polygon = Polygon(room_meta[:, 0:2])
    room_shape = torch.from_numpy(room_meta[:, 0:2]).float()
    room_shape_norm = torch.from_numpy(room_meta).float()
    translate = torch.zeros((len(pend_obj_list), 2)).float()
    orient = torch.zeros((len(pend_obj_list))).float()
    scale = torch.zeros((len(pend_obj_list), 3)).float()
    for i in range(len(pend_obj_list)):
        translate[i][0] = pend_obj_list[i]['translate'][0]
        translate[i][1] = pend_obj_list[i]['translate'][2]
        orient[i] = pend_obj_list[i]['orient']
        scale[i][0] = pend_obj_list[i]['scale'][0]
        scale[i][1] = pend_obj_list[i]['scale'][1]
        scale[i][2] = pend_obj_list[i]['scale'][2]

    bb = four_points_xz[bbindex].float()
    for i in range(len(pend_obj_list)):
        bb[i] = rotate_bb_local_para(bb[i], orient[i], scale[i][[0, 2]])

    iteration = 0
    loss = distribution_loss_nxt(translate, orient, pos_priors[:, :, :, [0, 2]], ori_priors, csrrelation)
    c_loss = collision_loss_nxt(translate.reshape(len(pend_obj_list), 1, 2) + bb, room_shape, yrelation * (1 - csrrelation), wallrelation, cornerrelation)
    loss += c_loss
    while iteration < 30000:
        if iteration % 1000 == 0:
            print("Start iteration {}...".format(iteration))
        new_translate, new_orient = mcmc_prop_yu(translate, orient)
        new_loss = distribution_loss_nxt(new_translate, new_orient, pos_priors[:, :, :, [0, 2]], ori_priors, csrrelation)
        c_loss = collision_loss_nxt(new_translate.reshape(len(pend_obj_list), 1, 2) + bb, room_shape, yrelation * (1 - csrrelation), wallrelation, cornerrelation)
        new_loss += c_loss
        pbt = np.random.rand()
        if torch.min(torch.tensor(1.0), torch.exp(loss - new_loss)).item() > pbt:
            print("Accept!!!")
            loss = new_loss
            translate = new_translate
            orient = new_orient
            print(loss)
        iteration += 1
    print("--- %s seconds ---" % (time.time() - start_time))
    for i in range(len(pend_obj_list)):
        o = pend_obj_list[i]
        o['translate'][0] = translate[i][0].item()
        o['translate'][2] = translate[i][1].item()
        o['rotate'][0] = 0.0
        o['rotate'][1] = orient[i].item()
        o['rotate'][2] = 0.0
        o['orient'] = orient[i].item()
    return rj

def mcmc_prop_qi(translate, orient):
    return translate + torch.randn(len(translate), 2) / 10, orient + torch.randn(len(orient)) / 10

def mcmc_prop_yu(translate, orient):
    option = np.random.randint(2)
    if option == 0:
        return translate + torch.randn(len(translate), 2) / 10, orient + torch.randn(len(orient)) / 10
    elif option == 1:
        s1 = np.random.randint(len(translate))
        s2 = np.random.randint(len(translate))
        temp_tran = translate[s1]
        temp_ori = orient[s1]
        translate[s1] = translate[s2]
        orient[s1] = orient[s2]
        translate[s2] = temp_tran
        orient[s2] = temp_ori
        return translate, orient

if __name__ == "__main__":
    examples = []
    examples.append({'hid': '9e359a26842ef23587c7da4948758d27-l0', 'rid': 4, 't_ours': 0.0, 't_qi': 0.0})
    examples.append({'hid': '8f38c6bf235b06c83e7230603f3f06dc-l0', 'rid': 0, 't_ours': 0.0, 't_qi': 0.0, 'case': 'living_room'})
    examples.append({'hid': '9e359a26842ef23587c7da4948758d27-l0', 'rid': 4, 't_ours': 0.0, 't_qi': 0.0})
    examples.append({'hid': '9e359a26842ef23587c7da4948758d27-l0', 'rid': 4, 't_ours': 0.0, 't_qi': 0.0})
    examples.append({'hid': '8f63a04d40c665227bcaf9573776889e-l0', 'rid': 2, 't_ours': 0.0, 't_qi': 0.0})
    examples.append({'hid': '9e359a26842ef23587c7da4948758d27-l0', 'rid': 4, 't_ours': 0.0, 't_qi': 0.0})
    for example in examples:
        with open('./examples/{}.json'.format(example['hid'])) as f:
            ex = json.load(f)
        print(fa_layout_nxt(ex['rooms'][example['rid']]))
