import torch
import json
import os
with open('./name_to_ls.json') as f:
    name_to_ls = json.load(f)
with open('./ls_to_name.json') as f:
    ls_to_name = json.load(f)
max_bb = torch.zeros((len(name_to_ls), 3))
min_bb = torch.zeros((len(name_to_ls), 3))
four_points_xz = torch.zeros((len(name_to_ls), 4, 2))


def find_bounding_box(objpath):
    print("start to process {}. ".format(objpath))
    vertices = []
    with open(objpath) as objf:
        for line in objf:
            if line.startswith("#"):
                continue
            values = line.split()
            if len(values) == 0:
                continue
            if values[0] == 'v':
                v = list(map(float, values[1:4]))
                vertices.append([v[0], v[1], v[2]])
    vertices = torch.Tensor(vertices).to('cuda')
    max_p = torch.max(vertices, dim=0)[0]
    min_p = torch.min(vertices, dim=0)[0]
    print("result max is {}, and min is {}. ".format(max_p, min_p))
    return max_p, min_p


if __name__ == "__main__":
    ns = os.listdir("./object")
    for objname in ns:
        objpath = './object/{}/{}.obj'.format(objname, objname)
        if os.path.exists(objpath):
            print(objpath)
            ma, mi = find_bounding_box(objpath)
            max_bb[name_to_ls[objname]] = ma
            min_bb[name_to_ls[objname]] = mi
            print(ma[[0, 2]])
            four_points_xz[name_to_ls[objname]][0] = ma[[0, 2]]
            four_points_xz[name_to_ls[objname]][1][0] = mi[0]
            four_points_xz[name_to_ls[objname]][1][1] = ma[2]
            four_points_xz[name_to_ls[objname]][2] = mi[[0, 2]]
            four_points_xz[name_to_ls[objname]][3][0] = ma[0]
            four_points_xz[name_to_ls[objname]][3][1] = mi[2]
    torch.save(max_bb, 'max_bb.pt')
    torch.save(min_bb, 'min_bb.pt')
    torch.save(four_points_xz, 'four_points_xz.pt')
