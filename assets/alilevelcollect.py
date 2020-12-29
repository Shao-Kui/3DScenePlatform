import json
import os

levelnames = os.listdir('../dataset/alilevel/')
with open('../dataset/sk_to_ali.json') as f:
    objnames = json.load(f)

def ocl():
    objCatList = {}
    with open('../dataset/sk_to_ali.json') as f:
        objnames = json.load(f)
    for objname in objnames:
        objCatList[objname] = []
    for levelname in levelnames:
        with open(f'../dataset/alilevel/{levelname}') as f:
            level = json.load(f)
        for room in level['rooms']:
            for obj in room['objList']:
                if obj['modelId'] not in objCatList:
                    continue
                # labels = obj['coarseSemantic'].split(' / ')
                # for label in labels:
                #     label = label.replace(' ', '_')
                #     if label not in objCatList[obj['modelId']]:
                #         objCatList[obj['modelId']].append(label)
                if obj['coarseSemantic'] not in objCatList[obj['modelId']]:
                    objCatList[obj['modelId']].append(obj['coarseSemantic'])
    with open('./objCatListAliv2.json', 'w') as f:
        json.dump(objCatList, f)
    with open('./objListCat.json', 'w') as f:
        json.dump(objListCat, f)

ocl()

def roomCatlistGen():
    with open('./objCatListAli.json') as f:
        objCatList = json.load(f)
    res = {'unknown': []}
    roomTypeDemo = {}
    for levelname in levelnames:
        with open(f'../dataset/alilevel/{levelname}') as f:
            level = json.load(f)
        for room in level['rooms']:
            # get category list; 
            catlist = []
            for obj in room['objList']:
                if obj['modelId'] not in objnames:
                    continue
                cats = objCatList[obj['modelId']]
                for cat in cats:
                    catlist.append(cat)
            # if the room type is not encountered yet, create it; 
            catstr = '\'' + ' '.join(catlist) + '\''
            if catstr == '\'\'':
                continue
            for rt in room['roomTypes']:
                if not os.path.exists(f'./roomtypecats/{rt}/'):
                    os.makedirs(f'./roomtypecats/{rt}/')
                if rt not in res:
                    res[rt] = []
                if rt not in roomTypeDemo:
                    roomTypeDemo[rt] = []
            for rt in room['roomTypes']:
                res[rt].append(catstr)
                # with open(f'./roomtypecats/{rt}/{room["origin"]}-{room["roomId"]}-{room["modelId"]}-{room["id"]}.txt', 'w') as f:
                #     f.write(' '.join(catlist))
            if len(room['roomTypes']) == 0:
                res['unknown'].append(catstr)
    for r in res:
        with open(f'./roomtypecats/{r}.txt', 'w') as f:
            f.write('\r\n'.join(res[r])) 
    with open('./roomTypeDemo.json', 'w') as f:
        json.dump(roomTypeDemo, f)
