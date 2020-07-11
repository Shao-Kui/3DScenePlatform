import json
import sys
import torch
import os
import numpy as np
from shapely.geometry import Polygon, Point
from shapely.affinity import translate
SUNCG_OBJ_ROOT = 'E:/WebStorm Projects/3dscene-midterm/suncg/object'

def AABB(objname):
    objpath = f'../../suncg/object/{objname}/{objname}.obj'
    vertices = []
    with open(objpath) as objf:
        for line in objf:
            if line.startswith("#"): continue
            values = line.split()
            if len(values) == 0:
                continue
            if values[0] == 'v':
                v = list(map(float, values[1:4]))
                vertices.append([v[0], v[1], v[2]])
    vertices = torch.Tensor(vertices).to('cuda')
    max_p = torch.max(vertices, dim=0)[0]
    min_p = torch.min(vertices, dim=0)[0]
    return max_p.tolist(), min_p.tolist()

def contour(objname):
    contourdir = os.path.join(SUNCG_OBJ_ROOT, objname, objname + '-contour.json')
    with open(contourdir, 'r') as fc:
        contour = json.load(fc)
    uni = Point()
    for c in contour:
        uni = uni.union(Polygon(c))
    return uni

if __name__ == "__main__":
    pri = sys.argv[1]
    sec = sys.argv[2]
    pri_aabb = AABB(pri)
    sec_aabb = AABB(sec)
    pri_uni = contour(pri)
    sec_uni = contour(sec)
    # print(pri_uni.area, sec_uni.area, pri_uni.union(translate(sec_uni, 0.7, 0.8)).area)
    res = []
    num = 2000
    xs = np.random.uniform(pri_aabb[0][0], pri_aabb[1][0], num)
    zs = np.random.uniform(pri_aabb[0][2], pri_aabb[1][2], num)
    for i in range(num):
        if pri_uni.intersects(Point((xs[i], zs[i]))):
            if pri_uni.union(translate(sec_uni, xs[i], zs[i])).area == pri_uni.area:
                res.append([xs[i], pri_aabb[0][1], zs[i], np.random.uniform(-np.pi, np.pi)])
    print(len(res))
    """
    with open(f'E:\\PyCharm Projects\\innerDesign\\pos-orient-denoised-2\\{pri}.json') as f:
        platformpattern = json.load(f)
    platformpattern[sec] = res
    with open(f'E:\\PyCharm Projects\\innerDesign\\pos-orient-denoised-2\\{pri}.json', 'w') as f:
        json.dump(platformpattern, f)
    with open(f'../pos-orient-denoised-2/{pri}.json') as f:
        platformpattern = json.load(f)
    platformpattern[sec] = res
    with open(f'../pos-orient-denoised-2/{pri}.json', 'w') as f:
        json.dump(platformpattern, f)
    """
    if os.path.isfile(f'./{pri}.json'):
       with open(f'./{pri}.json') as f:
           assembling = json.load(f)
    else:
        assembling = {}
    assembling[sec] = res
    with open(f'./{pri}.json', 'w') as f:
        json.dump(assembling, f) 
