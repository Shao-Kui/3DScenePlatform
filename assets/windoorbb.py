import torch
import json

def AABB(objpath):
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

# note that this script assumes that objects are centred at (0,0,0) and oriented toward z-axis. 
with open('./full-obj-semantic.json') as f:
    objsemantics = json.load(f)
windoor = {}
for objname in objsemantics:
    if objsemantics[objname] == 'door' or objsemantics[objname] == 'window':
        print('Start to do {}, which is a {}...'.format(objname, objsemantics[objname]))
        windoor[objname] = {}
        windoor[objname]['modelId'] = objname
        objpath = '../suncg/object/{}/{}.obj'.format(objname, objname)
        max_p, min_p = AABB(objpath)
        # save AABB; 
        windoor[objname]['max'] = max_p
        windoor[objname]['min'] = min_p

        # expand AABB to block
        # note that we do not need height! 
        blockmax_x = max(abs(max_p[0]), abs(min_p[0]))
        blockmax_z = max(abs(max_p[2]), abs(min_p[2]))
        ma = [blockmax_x, blockmax_z]
        mi = [-blockmax_x, -blockmax_z]
        windoor[objname]['four_points_xz'] = [[0,0],[0,0],[0,0],[0,0]]
        windoor[objname]['four_points_xz'][0][0] = ma[0]
        windoor[objname]['four_points_xz'][0][1] = ma[1]
        windoor[objname]['four_points_xz'][1][0] = mi[0]
        windoor[objname]['four_points_xz'][1][1] = ma[1]
        windoor[objname]['four_points_xz'][2][0] = mi[0]
        windoor[objname]['four_points_xz'][2][1] = mi[1]
        windoor[objname]['four_points_xz'][3][0] = ma[0]
        windoor[objname]['four_points_xz'][3][1] = mi[1]
with open('./windoorblock.json', 'w') as f:
    json.dump(windoor, f)


