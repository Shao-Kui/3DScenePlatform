import sys
import json
import torch
import numpy as np
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.collections import PatchCollection
"""
This code tries a brute-force way to build a dpc index; 
"""
# pri = '452'
# sec = '450'
# pri = '654'
# sec = '255'
# pri = '75'
# sec = '233'
# pri = '403'
# sec = 's__2100'
with open('../obj_coarse_semantic.json') as f:
    obj_semantic = json.load(f)
with open('../name_to_ls.json') as f:
    name_to_ls = json.load(f)
with open('../ls_to_name.json') as f:
    ls_to_name = json.load(f)
# with open('../windoorblock.json') as f:
#     windoorblock = json.load(f)
# max_bb = torch.load('../max_bb.pt').numpy()
# min_bb = torch.load('../min_bb.pt').numpy()
four_points_xz = torch.load("../four_points_xz.pt").numpy()

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

def checkbb(bb, priors, l):
    # termination; 
    if len(l) == 0:
        return list()

    # i denotes the chosen discrete prior; 
    i = l[np.random.randint(len(l))]
    newlevelitem = {}
    newlevelitem['id'] = i
    lfornextlevel = []
    prior1 = priors[i]
    bb1 = rotate_bb_local_np(bb, prior1[3]) + prior1[[0, 2]]
    polygon1 = Polygon(bb1).buffer(.15)

    """
    # bb visualization; 
    fig,ax = plt.subplots(1)
    rect = patches.Polygon(bb1,True,alpha=0.4)
    vis_patches.append(rect)
    vp = PatchCollection(vis_patches, alpha=0.4)
    ax.add_collection(vp)
    # ax.add_patch(rect)
    plt.plot(priors[:, 0], priors[:, 2], 'ro', alpha=0.4)
    plt.show()
    """

    # check all other discrete priors; 
    for j in l:
        if j == i:
            continue
        prior2 = np.array(priors[j])
        bb2 = rotate_bb_local_np(bb, prior2[3]) + prior2[[0, 2]]
        polygon2 = Polygon(bb2).buffer(.05)
        if not polygon1.intersects(polygon2):
            lfornextlevel.append(j)
    
    # recursively add the following discrete priors; 
    pendinglist = checkbb(bb, priors, lfornextlevel)
    pendinglist.append(i)
    return pendinglist

def patternChainHomo(pri, sec, expectedLength=2):
    with open('./{}.json'.format(pri)) as f:
        p = np.array(json.load(f)[sec])
    # MAXL = len(p)
    # sec_max_bb = max_bb[name_to_ls[sec]]
    # sec_min_bb = min_bb[name_to_ls[sec]]
    bb = four_points_xz[name_to_ls[sec]]
    res = []
    vis_patches = []
    for i in range(500):
        # Create figure and axes
        vis_patches = []
        r = checkbb(bb, p, range(len(p)))
        if len(r) < expectedLength:
            continue
        if i % 100 == 0:
            print(r)
        res.append(r)
    # print(res)
    with open('{}-{}.json'.format(pri, sec), 'w') as f:
        json.dump(res, f)

if __name__ == "__main__":
    patternChainHomo(sys.argv[1], sys.argv[2], int(sys.argv[3]))
