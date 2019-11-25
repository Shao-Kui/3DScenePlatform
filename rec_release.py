import json
import time
import torch
import math
import numpy as np
from shapely.geometry.polygon import Polygon
from shapely.geometry import Point
from projection2d import process as p2d
# from sk_loader import csrmatrix, ymatrix, obj_semantic, name_to_ls, ls_to_name, wallvector, cornervector
import matplotlib.pyplot as plt
BANNED = ['switch', 'column', 'fireplace', 'pet', 'range_hood', 'heater']
four_points_xz = torch.load("./latentspace/four_points_xz.pt")
ls = np.load("./latentspace/ls-release-2.npy")
PRIORS = "./latentspace/pos-orient-denoised/{}.json"
PRIORS_POS_ALT = "E:/PyCharm Projects/SceneEmbedding/pos/{}.json"
priors = {}
priors['pos'] = {}
priors['ori'] = {}

MAX_ITERATION = 10
REC_MAX = 20

def recommendation_ls_euclidean(objList):
    new_e_room = []
    for item in objList:
        if item is None:
            continue
        if item['modelId'] not in name_to_ls:
            continue
        new_e_room.append(item['modelId'])
    e_room = new_e_room
    dist = np.zeros((len(ls_to_name)))
    for item in e_room:
        test_point = ls[name_to_ls[item]].reshape(1, 2)
        dist += np.linalg.norm(ls - test_point, axis=1)
    indices = np.argsort(dist)
    counter = 0
    results = []
    for i in indices:
        if ls_to_name[str(i)] in e_room:
            continue
        results.append(ls_to_name[str(i)])
        counter += 1
        if counter >= REC_MAX:
            break
    return results

def pointInRectangleLoss_1(rec, p):
    loss = torch.tensor(1.0)
    for k in range(4):
        loss = loss * toLeftLoss(px=rec[k][0], py=rec[k][1],
                                 qx=rec[(k+1) % 4][0], qy=rec[(k+1) % 4][1],
                                 sx=p[0], sy=p[1])
    return loss

def disturbance(obj, scale, room_shape=None):
    if room_shape is not None:
        tx = obj['translate'][0] + np.random.randn() * scale
        tz = obj['translate'][2] + np.random.randn() * scale
        while not room_shape.contains(Point(tx, tz)):
            tx = obj['translate'][0] + np.random.randn() * scale
            tz = obj['translate'][2] + np.random.randn() * scale
        obj['translate'][0] = tx
        obj['translate'][2] = tz
        # randori = obj['orient'] + np.random.randn()
        # while randori > np.pi:
        #     randori -= 2 * np.pi
        # while randori < -np.pi:
        #     randori += 2 * np.pi
        # obj['orient'] = randori

def loss_2(x, yrelation=None):
    loss = torch.zeros((len(x), len(x), 4, 4, 3, 3), dtype=torch.float)
    for i in range(len(x)):
        for l in range(4):
            loss[i, :, l, :, 2, 0:2] = x[i, l]
        for k in range(4):
            loss[:, i, :, k, 0, 0:2] = x[i, k]
            loss[:, i, :, k, 1, 0:2] = x[i, (k+1)%4]
    for i in range(len(x)):
        loss[i, i, :, :, :, :] = 0
    loss[:, :, :, :, :, 2] = 1.0
    if yrelation is not None:
        loss = loss * yrelation.reshape((len(x), len(x), 1, 1, 1, 1))
    toleft = torch.max(torch.zeros((len(x), len(x), 4, 4), dtype=torch.float), torch.det(loss))
    return torch.sum(torch.prod(toleft, dim=3))

def loss_3(x, room_shape):
    # loss = torch.zeros((len(x), 4, 3, 3), dtype=torch.float)
    wall = torch.zeros((len(x), 4, len(room_shape), 3, 3), dtype=torch.float)
    sign = torch.zeros(len(x), 4, len(room_shape), dtype=torch.float)
    W = torch.zeros(len(room_shape), 2, 2)

    # calculate length of walls which may be moved to control function later
    i = torch.arange(1, len(room_shape)+1)
    i[len(room_shape)-1] = 0
    # print(i)
    room_length = torch.norm(room_shape - room_shape[i], dim=1)
    W[:, 0, :] = room_shape
    W[:, 1, :] = room_shape[i]

    wall[:, :, :, 0, 0:2] = room_shape
    wall[:, :, :, 1, 0:2] = room_shape[i]
    wall[:, :, :, 2, 0:2] = x.reshape(len(x), 4, 1, 2)

    # loss[:, :, :, 2] = 1.0
    wall[:, :, :, :, 2] = 1.0

    determinant = torch.det(wall)
    sign[determinant < 0.0] = 1.0
    min_result = torch.min(torch.abs(determinant) / room_length, dim=2)
    min_value = min_result[0]
    min_index = min_result[1]

    min_index = torch.arange(0, len(x)*4*len(room_shape), len(room_shape)) + min_index.flatten()
    sign = sign.flatten()[min_index].reshape(len(x), 4)
    # print(determinant / room_length)
    # print(min_value)
    # print(sign)
    return torch.sum(min_value * sign)

def loss_4(x, room_shape):
    wall = torch.zeros((len(x), 4, len(room_shape), 3, 3), dtype=torch.float)
    sign = torch.zeros(len(x), 4, len(room_shape), dtype=torch.float)
    W = torch.zeros(len(room_shape), 2, 2)
    i = torch.arange(1, len(room_shape)+1)
    i[len(room_shape)-1] = 0
    room_length = torch.norm(room_shape - room_shape[i], dim=1)
    wall[:, :, :, 0, 0:2] = room_shape
    wall[:, :, :, 1, 0:2] = room_shape[i]
    wall[:, :, :, 2, 0:2] = x.reshape(len(x), 4, 1, 2)
    wall[:, :, :, :, 2] = 1.0
    min_result = torch.min(torch.zeros((len(x), 4, len(room_shape)), dtype=torch.float), torch.det(wall))
    return torch.sum(torch.abs(min_result))

def rotate_bb_local_para(points, angle, scale):
    result = points.clone()
    scaled = points.clone()
    scaled = scaled * scale
    result[:, 0] = torch.cos(angle) * scaled[:, 0] + torch.sin(angle) * scaled[:, 1]
    result[:, 1] = -torch.sin(angle) * scaled[:, 0] + torch.cos(angle) * scaled[:, 1]
    return result

def rotate_pos_prior(points, angle):
    result = points.clone()
    result[:, 0] = torch.cos(angle) * points[:, 0] + torch.sin(angle) * points[:, 2]
    result[:, 2] = -torch.sin(angle) * points[:, 0] + torch.cos(angle) * points[:, 2]
    return result

def sample_translateRela(child, obj):
    priorid = "{}-{}".format(obj['modelId'], child['modelId'])
    if priorid not in priors['pos']:
        with open(PRIORS.format(obj['modelId'])) as f:
            priors['pos'][priorid] = json.load(f)[child['modelId']]
            priors['pos'][priorid] = np.squeeze(priors['pos'][priorid]).tolist()
        if len(priors['pos'][priorid]) == 0:
            with open(PRIORS_POS_ALT.format(obj['modelId'])) as f:
                priors['pos'][priorid] = json.load(f)[child['modelId']]
    child['translateRela'] = priors['pos'][priorid][np.random.randint(len(priors['pos'][priorid]))]

def collision_loss(translate, room_shape, yrelation=None, wallrelation=None, cornerrelation=None):
    loss = loss_2(translate, yrelation=yrelation)  # pairwise collision loss
    # loss += loss_3(translate, room_shape)  # nearest wall loss (Outside)
    loss += loss_4(translate, room_shape)  # not feasible for non-convex shape
    # loss += loss_wall(translate, room_shape, wallrelation)  # nearest wall loss (Inside)
    # loss += loss_corner(translate, room_shape, cornerrelation)  # nearest corner loss (Inside)
    return loss

def children_translate(pend_obj_list, translate, total_obj_num):
    translate_full = torch.zeros((total_obj_num, 2)).float()
    index = 0
    for i in range(len(pend_obj_list)):
        o = pend_obj_list[i]
        translate_full[index] += translate[i]
        index += 1
        for child in o['children']:
            translate_full[index] = translate[i]
            offset = torch.tensor([child['translateRela'][0], child['translateRela'][2]], dtype=torch.float)
            translate_full[index] += offset
            index += 1
    return translate_full

def distribution_loss(x, pos_priors, csrrelation=None):
    if csrrelation is None:
        csrrelation = torch.ones((len(x), len(x)))
    # x should be pure translations of pending objects.
    diff = x - x[:, None]  # each row i means centering obj i and other objects move to its relative position
    diff = pos_priors - diff.reshape(len(x), len(x), 1, 2)
    diff = torch.norm(diff, dim=3)
    hausdorff = torch.min(diff, dim=2)[0]
    return torch.sum(hausdorff * csrrelation)

def distribution_loss_orient(x, ori, pos_priors, ori_priors, csrrelation=None):
    if csrrelation is None:
        csrrelation = torch.ones((len(x), len(x)))
    # x should be pure translations of pending objects.
    diff = x - x[:, None]  # each row i means centering obj i and other objects move to its relative position
    diff = pos_priors - diff.reshape(len(x), len(x), 1, 2)

    diff = torch.norm(diff, dim=3)
    # diff = torch.sum(diff, dim=3) ** 2

    oridiff = torch.abs(ori - ori[:, None])
    oridiff.data[oridiff.data >  np.pi] -= 2 * np.pi
    oridiff.data[oridiff.data < -np.pi] += 2 * np.pi
    oridiff = torch.abs(oridiff)
    oridiff = torch.min(2 * np.pi - oridiff, oridiff)
    # oridiff = torch.abs(ori_priors - oridiff.reshape(len(x), len(x), 1))
    oridiff = torch.abs(ori_priors) - oridiff.reshape(len(x), len(x), 1)
    oridiff = torch.abs(oridiff)
    # oridiff = torch.min(2 * np.pi - oridiff, oridiff)
    oridiff = torch.exp(oridiff)

    hausdorff = torch.min(diff + oridiff, dim=2)
    # indexes = hausdorff[1].flatten() + (torch.arange(len(x) * len(x)) * len(ori_priors[0, 0]))
    # indexes = indexes.flatten()
    # print("Dis Part: \r\n", diff.data.flatten()[indexes].reshape(len(x), len(x)))
    # print("Ori Part: \r\n", oridiff.flatten()[indexes].reshape(len(x), len(x)))
    hausdorff = hausdorff[0]
    # print("Hau Part: \r\n", hausdorff)

    return loss_orth(ori) + torch.sum(hausdorff * csrrelation)

def loss_wall(x, room_shape, wrelation=None):
    if wrelation is None:
        wrelation = torch.zeros((len(x)), dtype=torch.float)
    wall = torch.zeros((len(x), 4, len(room_shape), 3, 3), dtype=torch.float)
    sign = torch.zeros(len(x), 4, len(room_shape), dtype=torch.float)
    W = torch.zeros(len(room_shape), 2, 2)
    i = torch.arange(1, len(room_shape)+1)
    i[len(room_shape)-1] = 0
    room_length = torch.norm(room_shape - room_shape[i], dim=1)
    wall[:, :, :, 0, 0:2] = room_shape
    wall[:, :, :, 1, 0:2] = room_shape[i]
    wall[:, :, :, 2, 0:2] = x.reshape(len(x), 4, 1, 2)
    wall[:, :, :, :, 2] = 1.0
    determinant = torch.det(wall)
    min_value = torch.min(torch.abs(determinant) / room_length, dim=2)[0]
    min_value = torch.min(min_value, dim=1)[0]
    return torch.sum(min_value * wrelation)

def loss_corner(x, room_shape, crelation=None):
    if crelation is None:
        crelation = torch.zeros((len(x)), dtype=torch.float)
    crelation = crelation.reshape(len(x), 1)
    wall = torch.zeros((len(x), 4, len(room_shape), 3, 3), dtype=torch.float)
    sign = torch.zeros(len(x), 4, len(room_shape), dtype=torch.float)
    W = torch.zeros(len(room_shape), 2, 2)
    i = torch.arange(1, len(room_shape)+1)
    i[len(room_shape)-1] = 0
    room_length = torch.norm(room_shape - room_shape[i], dim=1)
    wall[:, :, :, 0, 0:2] = room_shape
    wall[:, :, :, 1, 0:2] = room_shape[i]
    wall[:, :, :, 2, 0:2] = x.reshape(len(x), 4, 1, 2)
    wall[:, :, :, :, 2] = 1.0
    determinant = torch.det(wall)
    min_value = torch.topk(torch.abs(determinant) / room_length, k=2, dim=2, largest=False)[0]
    min_value = torch.min(min_value, dim=1)[0]
    return 3 * torch.sum(min_value * crelation)

def loss_orth(ori):
    diff = (ori[:, None] - torch.tensor([-np.pi, -np.pi/2, 0, np.pi/2, np.pi], dtype=torch.float)) ** 2
    diff = torch.min(diff, dim=1)[0]
    return 10.0 * torch.sum(diff)

def fa_layout_pro(rj):
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
    csrrelation = csrmatrix[bbindex][:, bbindex]
    yrelation = ymatrix[bbindex][:, bbindex]
    wallrelation = wallvector[bbindex]
    cornerrelation = cornervector[bbindex]
    csrrelation[diag_indices_] = 0.0
    SSIZE = 1000
    rng = np.random.default_rng()
    for centerid in range(len(pend_obj_list)):
        center = pend_obj_list[centerid]
        for objid in range(len(pend_obj_list)):
            obj = pend_obj_list[objid]
            priorid = "{}-{}".format(center['modelId'], obj['modelId'])
            if priorid not in priors['pos']:
                with open(PRIORS.format(center['modelId'])) as f:
                    if csrrelation[centerid, objid] == 0.0:
                        theprior = np.zeros((SSIZE, 4), dtype=np.float)
                    else:
                        theprior = np.array(json.load(f)[obj['modelId']], dtype=np.float)
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
            else:
                SSIZE = np.min((len(priors['pos'][priorid]), SSIZE))
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
    room_meta = p2d('.', '/suncg/room/{}/{}f.obj'.format(rj['origin'], rj['modelId']))
    room_polygon = Polygon(room_meta[:, 0:2])
    room_shape = torch.from_numpy(room_meta[:, 0:2]).float()
    room_shape_norm = torch.from_numpy(room_meta).float()
    translate = torch.zeros((len(pend_obj_list), 2)).float()
    orient = torch.zeros((len(pend_obj_list))).float()
    scale = torch.zeros((len(pend_obj_list), 3)).float()
    # for o in pend_obj_list:
    #     disturbance(o, 0.5, room_polygon)
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
    orient.requires_grad_()
    iteration = 0
    # loss = distribution_loss(translate, pos_priors[:, :, :, [0, 2]], csrrelation)
    start_time = time.time()
    loss = distribution_loss_orient(translate, orient, pos_priors[:, :, :, [0, 2]], ori_priors, csrrelation)
    c_loss = collision_loss(translate.reshape(len(pend_obj_list), 1, 2) + bb, room_shape, yrelation * (1 - csrrelation), wallrelation, cornerrelation)
    loss += c_loss
    while loss.item() > 0.0 and iteration < MAX_ITERATION:
        print("Start iteration {}...".format(iteration))
        loss.backward()
        # translate.data = translate.data - (1.0 / (1 + torch.sum(csrrelation, dim=1))).reshape(len(pend_obj_list), 1) * translate.grad * 0.05
        translate.data = translate.data - translate.grad * 0.05
        translate.grad = None
        # if orient.grad is not None:
        #     orient.data = orient.data - orient.grad * 0.01
        #     orient.data[orient.data >  np.pi] -= 2 * np.pi
        #     orient.data[orient.data < -np.pi] += 2 * np.pi
        #     orient.grad = None
        # loss = distribution_loss(translate, pos_priors[:, :, :, [0, 2]], csrrelation)
        loss = distribution_loss_orient(translate, orient, pos_priors[:, :, :, [0, 2]], ori_priors, csrrelation)
        c_loss = collision_loss(translate.reshape(len(pend_obj_list), 1, 2) + bb, room_shape, yrelation * (1 - csrrelation), wallrelation, cornerrelation)
        loss += c_loss
        iteration += 1
    print("--- %s seconds ---" % (time.time() - start_time))
    for i in range(len(pend_obj_list)):
        o = pend_obj_list[i]
        if 'coarseSemantic' not in o:
            break
        print(o['modelId'], o['coarseSemantic'])
        for j in range(len(pend_obj_list)):
            if csrrelation[i][j] == 1.0:
                print("--->>>", pend_obj_list[j]['modelId'], pend_obj_list[j]['coarseSemantic'])
    print(csrrelation)
    for i in range(len(pend_obj_list)):
        o = pend_obj_list[i]
        o['translate'][0] = translate[i][0].item()
        o['translate'][2] = translate[i][1].item()
        o['rotate'][0] = 0.0
        o['rotate'][1] = orient[i].item()
        o['rotate'][2] = 0.0
        o['orient'] = orient[i].item()
    return rj

if __name__ == "__main__":
    # with open('./examples/00e1559bdd1539323f3efba225af0531-l0.json') as f:
    #     ex = json.load(f)
    # print(fa_layout_nxt(ex['rooms'][3]))
    with open('./examples/00d0a6f041e710f2a198557cbad92e19-l0 - toleft - y.json') as f:
        ex = json.load(f)
    print(fa_layout_nxt(ex['rooms'][6]))
    # with open('./examples/00d0a6f041e710f2a198557cbad92e19-l0.json') as f:
    #     ex = json.load(f)
    # fa_layout_pro(ex['rooms'][6])

def fa_reshuffle(rj):
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
    room_meta = p2d('.', '/suncg/room/{}/{}f.obj'.format(rj['origin'], rj['modelId']))
    room_polygon = Polygon(room_meta[:, 0:2])
    room_shape = torch.from_numpy(room_meta[:, 0:2]).float()
    room_shape_norm = torch.from_numpy(room_meta).float()
    for o in pend_obj_list:
        disturbance(o, 0.5, room_polygon)
    for o in pend_obj_list:
        o['rotate'][0] = 0.0
        o['rotate'][1] = o['orient']
        o['rotate'][2] = 0.0
    return rj
