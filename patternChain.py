import json
import torch
import numpy as np
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.collections import PatchCollection
from copy import deepcopy

pendingList = []

# with open('./latentspace/name_to_ls.json') as f:
#     name_to_ls = json.load(f)
# with open('./latentspace/ls_to_name.json') as f:
#     ls_to_name = json.load(f)
with open('./latentspace/windoorblock.json') as f:
    windoorblock = json.load(f)
max_bb = torch.load('./latentspace/max_bb.pt').numpy()
min_bb = torch.load('./latentspace/min_bb.pt').numpy()
# four_points_xz = torch.load("./latentspace/four_points_xz.pt").numpy()

def transform_a_point(point, translate, angle, scale):
    result = point.copy()
    scaled = point.copy()
    scaled = point * scale
    result[0] =  np.cos(angle) * scaled[0] + np.sin(angle) * scaled[2]
    result[2] = -np.sin(angle) * scaled[0] + np.cos(angle) * scaled[2]
    return result + translate

def rotate_bb_local_np(points, angle, scale=np.array([1, 1])):
    result = points.copy()
    scaled = points.copy()
    scaled = scaled * scale
    result[:, 0] = np.cos(angle) * scaled[:, 0] + np.sin(angle) * scaled[:, 1]
    result[:, 1] = -np.sin(angle) * scaled[:, 0] + np.cos(angle) * scaled[:, 1]
    return result

def checkbb(bbs, ps, secs, lsfornextlevel, tier):
    if len(secs) == 0:
        return {}
    thisbb = bbs.pop()
    thisp = ps.pop()
    thissec = secs.pop()
    thisl = lsfornextlevel.pop()
    new_lfornextlevel = []
    if len(thisl) == 0:
        return checkbb(bbs.copy(), ps.copy(), secs.copy(), lsfornextlevel.copy(), tier.copy())
    # i denotes the chosen discrete prior; 
    i = thisl[np.random.randint(len(thisl))]
    prior1 = thisp[i]
    bb1 = rotate_bb_local_np(thisbb, prior1[3]) + prior1[[0, 2]]
    polygon1 = Polygon(bb1).buffer(.10)

    """
    # bb visualization; 
    fig,ax = plt.subplots(1)
    rect = patches.Polygon(bb1,True,alpha=0.4)
    vis_patches.append(rect)
    vp = PatchCollection(vis_patches, alpha=0.4)
    ax.add_collection(vp)
    # ax.add_patch(rect)
    plt.plot(thisp[:, 0], thisp[:, 2], 'ro', alpha=0.4)
    plt.show()
    """
    
    for (bb, p, sec, l) in zip(bbs, ps, secs, lsfornextlevel):
        # check all other discrete priors; 
        new_l = []
        for j in l:
            if j == i:
                continue
            prior2 = np.array(p[j])
            bb2 = rotate_bb_local_np(bb, prior2[3]) + prior2[[0, 2]]
            polygon2 = Polygon(bb2).buffer(.03)
            if not polygon1.intersects(polygon2) or tier[sec] != tier[thissec]:
                new_l.append(j)
        new_lfornextlevel.append(new_l)
    
    # recursively add the following discrete priors; 
    pendinglist = checkbb(bbs.copy(), ps.copy(), secs.copy(), new_lfornextlevel, tier.copy())
    if thissec not in pendinglist:
        pendinglist[thissec] = [i]
    else:
        pendinglist[thissec].append(i)
    return pendinglist

def patternChain(pri, secs, tier={'238': 0, '153': 0}):
    print(f'start to generate pattern chain: {pri} & {secs}')
    for s in secs:
        if s not in tier:
            tier[s] = 1
    secs.sort()
    ps = []
    bbs = []
    lsfornextlevel = []
    for sec in secs:
        with open('./latentspace/pos-orient-3/{}.json'.format(pri)) as f:
            p = np.array(json.load(f)[sec])
        ps.append(p)
        with open(f'./dataset/object/{sec}/{sec}-4p.json') as f:
            bbs.append(np.array(json.load(f)))
        lsfornextlevel.append(range(len(p)))
    res = []
    # vis_patches = []
    for i in range(500):
        # Create figure and axes
        # vis_patches = []
        r = checkbb(bbs.copy(), ps.copy(), secs.copy(), lsfornextlevel.copy(), tier.copy())
        checkr = deepcopy(r)
        try:
            for item in secs:
                checkr[item].pop()
        except Exception:
            continue
        if i % 20 == 0:
            print(r)
        res.append(r)
    print(f'A new hyper-relation is generated - {pri} & {secs}')
    if len(res) == 0:
        return
    with open('./latentspace/pos-orient-3/hyper/{}-{}.json'.format(pri, '_'.join(secs)), 'w') as f:
        json.dump(res, f)
