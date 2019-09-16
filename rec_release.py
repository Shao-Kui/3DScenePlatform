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
PRIORS = "E:/PyCharm Projects/SceneEmbedding/pos/{}.json"
priors = {}
priors['pos'] = {}
with open(PRIORS.format('403')) as f:
    atest = json.load(f)
with open('./latentspace/obj-semantic.json') as f:
    obj_semantic = json.load(f)
with open('./latentspace/name_to_ls.json') as f:
    name_to_ls = json.load(f)
with open('./latentspace/ls_to_name.json') as f:
    ls_to_name = json.load(f)
correlation_matrix_hack = torch.zeros((len(obj_semantic), len(obj_semantic)), dtype=torch.float)
correlation_matrix_hack[name_to_ls['403'], name_to_ls['318']] = 1.0
correlation_matrix_hack[name_to_ls['318'], name_to_ls['403']] = 1.0
MAX_ITERATION = 50
# ls_to_name = {}
# name_to_ls = {}
# index = 0
# for n in obj_semantic:
#     ls_to_name[index] = n
#     name_to_ls[n] = index
#     index += 1
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
                # loss += toLeftLoss(px=x[j][k][0], py=x[j][k][1],
                #                    qx=x[j][(k+1)%4][0], qy=x[j][(k+1)%4][1],
                #                    sx=x[i][l][0], sy=x[i][l][1])
    return loss

"""
Loss function of calculating crowdness of objects.
"""
def loss_2(x):
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

def sample_translateRela(child, obj):
    priorid = "{}-{}".format(obj['modelId'], child['modelId'])
    if priorid not in priors['pos']:
        with open(PRIORS.format(obj['modelId'])) as f:
            priors['pos'][priorid] = json.load(f)[child['modelId']]
    child['translateRela'] = priors['pos'][priorid][np.random.randint(len(priors['pos'][priorid]))]


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
                if correlation_matrix_hack[name_to_ls[existobj['modelId']], name_to_ls[o['modelId']]] == 1.0:
                    sample_translateRela(o, existobj)
                    print(o['translateRela'])
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
    for o in pend_obj_list:
        disturbance(o, 0.5, room_polygon)
    for i in range(len(pend_obj_list)):
        translate[i][0] = pend_obj_list[i]['translate'][0]
        translate[i][1] = pend_obj_list[i]['translate'][2]
        orient[i] = pend_obj_list[i]['orient']
    translate.requires_grad_()
    orient.requires_grad_()
    bbindex = []
    for o in pend_obj_list:
        bbindex.append(name_to_ls[o['modelId']])
        for child in o['children']:
            bbindex.append(name_to_ls[child['modelId']])
    bb = four_points_xz[bbindex].float()
    translate_full = torch.zeros((total_obj_num, 2)).float()
    index = 0
    for i in range(len(pend_obj_list)):
        o = pend_obj_list[i]
        translate_full[index] += translate[i]
        index += 1
        for child in o['children']:
            translate_full[index] += translate[i]
            offset = torch.tensor([child['translateRela'][0], child['translateRela'][2]], dtype=torch.float)
            translate_full[index] += offset
            index += 1
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
    for i in range(len(pend_obj_list)):
        for k in range(4):
            bb[i, k] = rotate_bb_local(bb[i, k], orient[i])
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
    with open('./examples/00e1559bdd1539323f3efba225af0531-l0.json') as f:
        ex = json.load(f)
    print(fa_layout_nxt(ex['rooms'][0]))