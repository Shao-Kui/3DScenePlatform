import json
import torch
import math
import numpy as np
from shapely.geometry.polygon import Polygon
from shapely.geometry import Point
from projection2d import process as p2d
import matplotlib.pyplot as plt

four_points_xz = torch.load("./latentspace/four_points_xz.pt")
ls = np.load("./latentspace/ls-release-2.npy")
PRIORS = "./latentspace/pos-orient-denoised/{}.json"
PRIORS_POS_ALT = "E:/PyCharm Projects/SceneEmbedding/pos/{}.json"
priors = {}
priors['pos'] = {}
priors['ori'] = {}
with open('./latentspace/obj-semantic.json') as f:
    obj_semantic = json.load(f)
with open('./latentspace/name_to_ls.json') as f:
    name_to_ls = json.load(f)
with open('./latentspace/ls_to_name.json') as f:
    ls_to_name = json.load(f)
csrmatrix = torch.from_numpy(np.load("./latentspace/csrmatrix.npy")).float()
ymatrix = torch.from_numpy(np.load("./latentspace/ymatrix.npy")).float()
ymatrix[name_to_ls['271'], name_to_ls['267']] = 1.0
ymatrix[name_to_ls['267'], name_to_ls['271']] = 1.0
MAX_ITERATION = 100
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
        if ls_to_name[i] in e_room:
            continue
        results.append(ls_to_name[i])
        counter += 1
        if counter >= REC_MAX:
            break
    return results

def toLeftLoss(px, py, qx, qy, sx, sy):
    return torch.max(torch.tensor(0.0), px * qy - py * qx + qx * sy - qy * sx + sx * py - sy * px)

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

def loss_1(x):
    loss = torch.tensor(0.0)
    for i in range(len(x)):
        for j in range(len(x)):
            if i == j:
                continue
            for l in range(4):
                loss += pointInRectangleLoss_1(x[j], x[i][l])
    return loss

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

def rotate_bb_local(point, angle):
    """
    Rotate a point counterclockwise by a given angle around a given origin.
    The angle should be given in radians.
    Assuming origin is zero.
    modified from: https://stackoverflow.com/questions/34372480/rotate-point-about-another-point-in-degrees-python
    """
    result = point.clone()
    result[0] = torch.cos(angle) * point[0] - torch.sin(angle) * point[1]
    result[1] = torch.sin(angle) * point[0] + torch.cos(angle) * point[1]
    return result

def rotate_bb_local_para(points, angle):
    result = points.clone()
    result[:, 0] = torch.cos(angle) * points[:, 0] - torch.sin(angle) * points[:, 1]
    result[:, 1] = torch.sin(angle) * points[:, 0] + torch.cos(angle) * points[:, 1]
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

def collision_loss(translate, room_shape, yrelation=None):
    loss = loss_2(translate, yrelation=yrelation)
    loss += loss_4(translate, room_shape)
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

def fa_layout_pro(rj):
    pend_obj_list = []
    final_obj_list = []
    bbindex = []
    ol = rj['objList']
    for o in ol:
        if o is None:
            continue
        if o['modelId'] not in obj_semantic:
            final_obj_list.append(o)
        else:
            bbindex.append(name_to_ls[o['modelId']])
            pend_obj_list.append(o)
    diag_indices_ = (torch.arange(len(pend_obj_list)), torch.arange(len(pend_obj_list)))
    csrrelation = csrmatrix[bbindex][:, bbindex]
    yrelation = ymatrix[bbindex][:, bbindex]
    csrrelation[diag_indices_] = 0.0

    SSIZE = 1000
    rng = np.random.default_rng()
    for centerid in range(len(pend_obj_list)):
        center = pend_obj_list[centerid]
        for objid in range(len(pend_obj_list)):
            obj = pend_obj_list[objid]
            priorid = "{}-{}".format(center['modelId'], obj['modelId'])
            if priorid not in priors['pos']:
                if csrrelation[centerid, objid] == 0:
                    priors['pos'][priorid] = torch.zeros((SSIZE, 3), dtype=torch.float)
                    continue
                with open(PRIORS.format(center['modelId'])) as f:
                    theprior = np.array(json.load(f)[obj['modelId']], dtype=np.float)
                    while len(theprior)  < SSIZE:
                        theprior = np.vstack((theprior, theprior))
                    rng.shuffle(theprior)
                    priors['pos'][priorid] = theprior[:, 0:3]
                    priors['ori'][priorid] = theprior[:, 3].flatten()
                    if len(priors['pos'][priorid]) <= 10:
                        csrrelation[centerid, objid] = 0
                        priors['pos'][priorid] = torch.zeros((SSIZE, 3), dtype=torch.float)
                        continue
                SSIZE = np.min((len(priors['pos'][priorid]), SSIZE))
                priors['pos'][priorid] = torch.from_numpy(priors['pos'][priorid]).float()
                priors['pos'][priorid] = rotate_bb_local_para(priors['pos'][priorid], torch.tensor(center['orient'], dtype=torch.float))
                priors['ori'][priorid] = torch.from_numpy(priors['ori'][priorid]).float()
                priors['ori'][priorid] = priors['ori'][priorid] + torch.tensor(center['orient'], dtype=torch.float)
            else:
                SSIZE = np.min((len(priors['pos'][priorid]), SSIZE))
    pos_priors = torch.zeros(len(pend_obj_list), len(pend_obj_list), SSIZE, 3)
    for centerid in range(len(pend_obj_list)):
        center = pend_obj_list[centerid]
        for objid in range(len(pend_obj_list)):
            obj = pend_obj_list[objid]
            priorid = "{}-{}".format(center['modelId'], obj['modelId'])
            pos_priors[centerid, objid] = priors['pos'][priorid][0: SSIZE]
    room_meta = p2d('.', '/suncg/room/{}/{}f.obj'.format(rj['origin'], rj['modelId']))
    room_polygon = Polygon(room_meta[:, 0:2])
    room_shape = torch.from_numpy(room_meta[:, 0:2]).float()
    translate = torch.zeros((len(pend_obj_list), 2)).float()
    orient = torch.zeros((len(pend_obj_list))).float()
    # for o in pend_obj_list:
    #     disturbance(o, 0.5, room_polygon)
    for i in range(len(pend_obj_list)):
        translate[i][0] = pend_obj_list[i]['translate'][0]
        translate[i][1] = pend_obj_list[i]['translate'][2]
        orient[i] = pend_obj_list[i]['orient']

    bb = four_points_xz[bbindex].float()
    for i in range(len(pend_obj_list)):
        bb[i] = rotate_bb_local_para(bb[i], orient[i])

    translate.requires_grad_()
    orient.requires_grad_()
    # time for collision detection
    iteration = 0
    loss = distribution_loss(translate, pos_priors[:, :, :, [0, 2]], csrrelation)
    c_loss = collision_loss(translate.reshape(len(pend_obj_list), 1, 2) + bb, room_shape, yrelation * (1 - csrrelation))
    loss += c_loss
    while loss.item() > 0.0 and iteration < MAX_ITERATION:
        print("Start iteration {}...".format(iteration))
        loss.backward()
        translate.data = translate.data - translate.grad * np.random.randint(1, 6) * 0.01
        translate.grad = None
        loss = distribution_loss(translate, pos_priors[:, :, :, [0, 2]], csrrelation)
        c_loss = collision_loss(translate.reshape(len(pend_obj_list), 1, 2) + bb, room_shape, yrelation * (1 - csrrelation))
        loss += c_loss
        iteration += 1

    for i in range(len(pend_obj_list)):
        o = pend_obj_list[i]
        o['translate'][0] = translate[i][0].item()
        o['translate'][2] = translate[i][1].item()
    return rj

def fa_layout_nxt(rj):
    pend_obj_list = []
    final_obj_list = []
    ol = rj['objList']
    total_obj_num = 0
    for o in ol:
        if o is None:
            continue
        if o['modelId'] not in obj_semantic:
            final_obj_list.append(o)
        else:
            total_obj_num += 1
            isRoot = True
            for existobj in pend_obj_list:
                if csrmatrix[name_to_ls[existobj['modelId']], name_to_ls[o['modelId']]] == 1.0:
                    sample_translateRela(o, existobj)
                    existobj['children'].append(o)
                    isRoot = False
                    break
            if isRoot:
                o['children'] = []
                pend_obj_list.append(o)
    room_meta = p2d('.', '/suncg/room/{}/{}f.obj'.
    format(rj['origin'], rj['modelId']))
    room_polygon = Polygon(room_meta[:, 0:2])
    room_shape = torch.from_numpy(room_meta[:, 0:2]).float()
    translate = torch.zeros((len(pend_obj_list), 2)).float()
    orient = torch.zeros((len(pend_obj_list))).float()
    # for o in pend_obj_list:
    #     disturbance(o, 0.5, room_polygon)
    for i in range(len(pend_obj_list)):
        translate[i][0] = pend_obj_list[i]['translate'][0]
        translate[i][1] = pend_obj_list[i]['translate'][2]
        orient[i] = pend_obj_list[i]['orient']
    translate.requires_grad_()
    orient.requires_grad_()
    bbindex = []
    for o in pend_obj_list:
        bbindex.append(name_to_ls[o['modelId']])
        print(o['modelId'])
        for child in o['children']:
            print(" --- ", child['modelId'])
            bbindex.append(name_to_ls[child['modelId']])
    bb = four_points_xz[bbindex].float()
    csrrelation = csrmatrix[bbindex][:, bbindex]
    yrelation = ymatrix[bbindex][:, bbindex]
    print(yrelation)
    bi = 0
    for o in pend_obj_list:
        bb[bi] = rotate_bb_local_para(bb[bi], torch.tensor(o['orient'], dtype=torch.float))
        bi += 1
        for child in o['children']:
            bb[bi] = rotate_bb_local_para(bb[bi], torch.tensor(child['orient'], dtype=torch.float))
            bi += 1
    translate_full = children_translate(pend_obj_list, translate, total_obj_num)

    # time for collision detection
    iteration = 0
    loss = collision_loss(translate_full.reshape(total_obj_num, 1, 2) + bb, room_shape, yrelation)
    while loss.item() > 0.0 and iteration < MAX_ITERATION:
        loss.backward()
        translate.data = translate.data - translate.grad * 0.05
        translate.grad = None
        translate_full = children_translate(pend_obj_list, translate, total_obj_num)
        loss = collision_loss(translate_full.reshape(total_obj_num, 1, 2) + bb, room_shape, yrelation)
        iteration += 1

    for i in range(len(pend_obj_list)):
        o = pend_obj_list[i]
        o['translate'][0] = translate[i][0].item()
        o['translate'][2] = translate[i][1].item()
        for child in o['children']:
            child['translate'][0] = translate[i][0].item() + child['translateRela'][0]
            child['translate'][2] = translate[i][1].item() + child['translateRela'][2]
    return rj

def fa_layout(rj):
    pend_obj_list = []
    final_obj_list = []
    ol = rj['objList']
    for o in ol:
        if o is None:
            continue
        if o['modelId'] not in obj_semantic:
            final_obj_list.append(o)
        else:
            pend_obj_list.append(o)
    room_meta = p2d('.', '/suncg/room/{}/{}f.obj'.
    format(rj['origin'], rj['modelId']))
    room_polygon = Polygon(room_meta[:, 0:2])
    room_shape = torch.from_numpy(room_meta[:, 0:2]).float()
    translate = torch.zeros((len(pend_obj_list), 2)).float()
    orient = torch.zeros((len(pend_obj_list))).float()
    for i in range(len(pend_obj_list)):
        translate[i][0] = pend_obj_list[i]['translate'][0]
        translate[i][1] = pend_obj_list[i]['translate'][2]
        orient[i] = pend_obj_list[i]['orient']
    bbindex = []
    for o in pend_obj_list:
        bbindex.append(name_to_ls[o['modelId']])
    bb = four_points_xz[bbindex].float()
    # Rotate bb with respect to Y-orient of objects, may requires parallel later
    # for i in range(len(pend_obj_list)):
    #     for k in range(4):
    #         bb[i, k] = rotate_bb_local(bb[i, k], orient[i])
    for i in range(len(pend_obj_list)):
        bb[i] = rotate_bb_local_para(bb[i], orient[i])
    translate.requires_grad_()
    orient.requires_grad_()
    loss = loss_2(translate.reshape(len(pend_obj_list), 1, 2) + bb)
    loss += loss_4(translate.reshape(len(pend_obj_list), 1, 2) + bb, room_shape)
    # print(translate.reshape(len(pend_obj_list), 1, 2) + bb)
    # torch.save(translate.reshape(len(pend_obj_list), 1, 2) + bb, './tryp.pt')
    iteration = 0
    while loss.item() > 0.0 and iteration < MAX_ITERATION:
        loss.backward()
        translate.data = translate.data - translate.grad * 0.05
        translate.grad = None
        loss = loss_2(translate.reshape(len(pend_obj_list), 1, 2) + bb)
        loss += loss_4(translate.reshape(len(pend_obj_list), 1, 2) + bb, room_shape)
        iteration += 1
        # print(loss)
    # currently, we dont consider rotation

    # calculate loss for cross object collision

    # then calculate loss for object vs room collision
    for i in range(len(pend_obj_list)):
        o = pend_obj_list[i]
        o['translate'][0] = translate[i][0].item()
        o['translate'][2] = translate[i][1].item()
        # disturbance(o, 0.5, room_shape)
        final_obj_list.append(o)
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
