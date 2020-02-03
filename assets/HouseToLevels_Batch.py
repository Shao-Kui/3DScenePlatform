import json
import transform3d
import os

with open('./full-obj-semantic.json') as f:
    obj_semantic = json.load(f)

def house_to_level(h):
    levels = []
    for level in h['levels']:
        new_level = dict()
        if 'bbox' not in level:
            # print("Fail to process: " + fpath)
            # return
            new_level['bbox'] = {
                "min": [
                38.50499669793999,
                -0.04999999888241291,
                36.02499675337231
                ],
                "max": [
                53.289941837950785,
                2.7399999387562293,
                50.219884877498075
                ]
            }
        else:
            new_level['bbox'] = level['bbox']
        new_level['origin'] = h['id']
        new_level['id'] = level['id']
        new_level['up'] = h['up']
        new_level['front'] = h['front']
        new_level['rooms'] = []
        nodes = level["nodes"]
        # To generate according room id for each object.
        room_id = 0
        for node in nodes:
            if node['type'] == 'Room':
                node['origin'] = h['id']
                node['roomId'] = room_id
                node['objList'] = []
                nodeIndices = node.pop('nodeIndices', None)
                if nodeIndices is None:
                    continue
                for i in nodeIndices:
                    index = int(i)
                    if 'modelId' not in nodes[index]:
                        continue
                    node['objList'].append(nodes[index])
                for obj in node['objList']:
                    if 'modelId' not in obj:
                        continue
                    matrix = obj.pop('transform', None)
                    if None in matrix:
                        continue
                    T, S, R = transform3d.decompose16(matrix)
                    obj['translate'] = T.tolist()
                    obj['scale'] = S.tolist()
                    obj['rotate'] = R.tolist()
                    obj['rotateOrder'] = 'XYZ'
                    obj['orient'] = transform3d.orient(matrix)
                    if obj['modelId'] in obj_semantic:
                        obj['coarseSemantic'] = obj_semantic[obj['modelId']]
                    obj['roomId'] = room_id
                    # pop some unneeded features:
                    obj.pop('materials', None)
                    obj.pop('valid', None)
                    obj.pop('state', None)
                node.pop('type', None)
                node.pop('valid', None)
                new_level['rooms'].append(node)
                room_id += 1
        levels.append(new_level)
    return levels

def process(fpath):
    print("start to process: " + fpath)
    with open(fpath) as f:
        h = json.load(f)
    levels = house_to_level(h)
    for new_level in levels:
        with open("F:/3DIndoorScenePlatform/suncg/level/{}/{}-l{}.json".format(h['id'], h['id'], new_level['id']), 'w')\
                as f:
            json.dump(new_level, f)
            # print("saved {}. ".format(level['id']))

def process_single_house(fpath, outputdir='./'):
    with open(fpath) as f:
        h = json.load(f)
    levels = house_to_level(h)
    for new_level in levels:
        with open("./{}-l{}.json".format(h['id'], new_level['id']), 'w')\
                as f:
            json.dump(new_level, f)

process_single_house('./synth/0_1_5_final_3.json')

# names = os.listdir('D:/suncg/house')
# interruptid = 0
# for n in names[interruptid:]:
#     if not os.path.exists('F:/3DIndoorScenePlatform/suncg/level/' + n):
#         os.mkdir('F:/3DIndoorScenePlatform/suncg/level/' + n)
#     process('D:/suncg/house/{}/house.json'.format(n))
#     print("Finished : {}. ".format(interruptid))
#     interruptid += 1
