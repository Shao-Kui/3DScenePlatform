import torch
import json
import os
with open('./test/name_to_ls.json') as f:
    name_to_ls = json.load(f)
with open('./test/obj-semantic.json') as f:
    obj_semantic = json.load(f)
max_bb = torch.zeros((len(obj_semantic), 3))
min_bb = torch.zeros((len(obj_semantic), 3))


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
    ns = os.listdir("D:/suncg/object")
    for objname in ns:
        if objname not in obj_semantic:
            continue
        objpath = 'D:/suncg/object/{}/{}.obj'.format(objname, objname)
        if os.path.exists(objpath):
            ma, mi = find_bounding_box(objpath)
            max_bb[name_to_ls[objname]] = ma
            min_bb[name_to_ls[objname]] = mi
    torch.save(max_bb, './test/max_bb.pt')
    torch.save(min_bb, './test/min_bb.pt')
