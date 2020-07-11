import json
import torch
import numpy as np
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.collections import PatchCollection
from copy import deepcopy
"""
This code tries a brute-force way to build a dpc index; 
"""
# pri = '549'
# secs = ['116', 's__588', 's__587', '235']
# tier = {'235': 0}
pri = '551'
secs = ['259', '259', '261', '153', '258']
tier = {'238': 0, '153': 0}
# default tier is 1; 
for s in secs:
    if s not in tier:
        tier[s] = 1
secs.sort()
ps = []
bbs = []
lsfornextlevel = []
with open('../obj-semantic.json') as f:
    obj_semantic = json.load(f)
with open('../name_to_ls.json') as f:
    name_to_ls = json.load(f)
with open('../ls_to_name.json') as f:
    ls_to_name = json.load(f)
with open('../windoorblock.json') as f:
    windoorblock = json.load(f)
max_bb = torch.load('../max_bb.pt').numpy()
min_bb = torch.load('../min_bb.pt').numpy()
four_points_xz = torch.load("../four_points_xz.pt").numpy()
for sec in secs:
    with open('./{}.json'.format(pri)) as f:
        p = np.array(json.load(f)[sec])
    ps.append(p)
    bbs.append(four_points_xz[name_to_ls[sec]])
    lsfornextlevel.append(range(len(p)))

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

def checkbb(bbs, ps, secs, lsfornextlevel):
    if len(secs) == 0:
        return {}
    thisbb = bbs.pop()
    thisp = ps.pop()
    thissec = secs.pop()
    thisl = lsfornextlevel.pop()
    new_lfornextlevel = []
    if len(thisl) == 0:
        return checkbb(bbs.copy(), ps.copy(), secs.copy(), lsfornextlevel.copy())
    # i denotes the chosen discrete prior; 
    i = thisl[np.random.randint(len(thisl))]
    prior1 = thisp[i]
    bb1 = rotate_bb_local_np(thisbb, prior1[3]) + prior1[[0, 2]]
    polygon1 = Polygon(bb1).buffer(.15)

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
            polygon2 = Polygon(bb2).buffer(.05)
            if not polygon1.intersects(polygon2) or tier[sec] != tier[thissec]:
                new_l.append(j)
        new_lfornextlevel.append(new_l)
    
    # recursively add the following discrete priors; 
    pendinglist = checkbb(bbs.copy(), ps.copy(), secs.copy(), new_lfornextlevel)
    if thissec not in pendinglist:
        pendinglist[thissec] = [i]
    else:
        pendinglist[thissec].append(i)
    return pendinglist

res = []
vis_patches = []
for i in range(2000):
    # Create figure and axes
    vis_patches = []
    r = checkbb(bbs.copy(), ps.copy(), secs.copy(), lsfornextlevel.copy())
    checkr = deepcopy(r)
    try:
        for item in secs:
            checkr[item].pop()
    except Exception as e:
        print(e)
        continue
    print(r)
    res.append(r)
print(res)
with open('{}-{}.json'.format(pri, '_'.join(secs)), 'w') as f:
    json.dump(res, f)
with open('./hyper/{}-{}.json'.format(pri, '_'.join(secs)), 'w') as f:
    json.dump(res, f)
