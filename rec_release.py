import json
import numpy as np
ls = np.load("./latentspace/ls-release-2.npy")
with open('./latentspace/obj-semantic.json') as f:
    obj_semantic = json.load(f)
ls_to_name = {}
name_to_ls = {}
index = 0
for n in obj_semantic:
    ls_to_name[index] = n
    name_to_ls[n] = index
    index += 1
REC_MAX = 20

# with open('./examples/00e1559bdd1539323f3efba225af0531-l0.json') as f:
#     objL = json.load(f)
#     objL = objL['rooms'][3]['objList']


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


# print(recommendation_ls_euclidean(objL))
