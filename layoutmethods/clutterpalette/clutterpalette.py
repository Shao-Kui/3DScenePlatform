import os
import json
import random

categories = ['Coffee Table', 'Nightstand', 'TV Stand', 'Corner/Side Table', 'armchair', 'Sideboard / Side Cabinet / Console table', 'Three-seat / Multi-seat Sofa', 'Loveseat Sofa', 'Dining Chair', 'Dining Table', 'Single bed', 'Wardrobe', 'Drawer Chest / Corner cabinet', 'King-size Bed', 'Lounge Chair / Cafe Chair / Office Chair', 'Bookcase / jewelry Armoire', 'Desk', 'Dressing Table', 'Round End Table', 'Kids Bed', 'Footstool / Sofastool / Bed End Stool / Stool', 'Wine Cabinet', 'Shelf', 'Children Cabinet', 'Bunk Bed', 'L-shaped Sofa', 'Dressing Chair', 'Classic Chinese Chair', 'Barstool', 'Chaise Longue Sofa', 'Lazy Sofa', 'Bed Frame']

roomTypes = ['Aisle', 'Auditorium', 'Balcony', 'Bathroom', 'Bedroom', 'CloakRoom', 'Corridor', 
'Courtyard', 'DiningRoom', 'ElderlyRoom', 'EquipmentRoom', 'Garage', 'Hallway', 'KidsRoom', 
'Kitchen', 'LaundryRoom', 'Library', 'LivingDiningRoom', 'LivingRoom', 'Lounge', 'MasterBathroom', 
'MasterBedroom', 'NannyRoom', 'non', 'none', 'SecondBathroom', 'SecondBedroom', 'Stairwell', 
'StorageRoom', 'Terrace']

cat2idx = {}
for idx, cat in enumerate(categories):
    cat2idx[cat] = idx

rt2idx = {}
for idx, rt in enumerate(roomTypes):
    rt2idx[rt] = idx

median = [1, 2, 1, 2, 1, 1, 1, 1, 4, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]

with open('./layoutmethods/clutterpalette/prob/category_ratio_log10.json') as f:
    category_ratio = json.load(f)
with open('./layoutmethods/clutterpalette/prob/conditional_scene_prob_log10.json') as f:
    cond_scene_prob = json.load(f)
with open('./layoutmethods/clutterpalette/prob/co_occurence_log10.json') as f:
    co_occur_prob = json.load(f)
with open('./dataset/objListCataAliv4.json') as f:
    objListCat = json.load(f)
with open('./dataset/objCatListAliv2.json') as f:
    objCatListAliv2 = json.load(f)

def getObjCat(modelId):
    if len(objCatListAliv2[modelId]) == 0:
        return None
    else:
        return objCatListAliv2[modelId][0]

def clutter_prior(Yi):
    return category_ratio[Yi]

def conditional_scene_prob(w, Yi):
    return cond_scene_prob[Yi][w]

def conditional_supporter_prob(s, Yi):
    # all objects are on the floor
    return 0

def co_occurence_prob(nj, Yj, Yi):
    if nj == 0:
        return 3
    return co_occur_prob[Yi][Yj][nj > median[Yj]]

def co_occur(bbox, pos):
    # distance < 1.5m
    x1, y1, z1 = bbox["min"]
    x2, y2, z2 = bbox["max"]
    if x1 > pos['x'] + 1.5 or pos['x'] > x2 + 1.5:
        return False
    if z1 > pos['z'] + 1.5 or pos['z'] > z2 + 1.5:
        return False
    return True

def clutterpaletteQuery(room, pos):
    roomtype = room['roomTypes'][0]
    if roomtype == 'Storage':
        roomtype = 'StorageRoom'
    w = rt2idx[roomtype]
    neighborhood = {}
    for obj in room['objList']:
        # please make sure all obj['coarseSemantic'] && obj['bbox'] are provided
        # print(obj)
        if 'coarseSemantic' not in obj:
            obj['coarseSemantic'] = getObjCat(obj['modelId'])
        cat = obj['coarseSemantic']
        if cat not in categories:
            # skip Door, Window, Lamp
            continue
        if co_occur(obj['bbox'], pos):
            Yj = cat2idx[cat]
            if Yj not in neighborhood:
                neighborhood[Yj] = 1
            else:
                neighborhood[Yj] += 1
    score = {}
    for Yi in range(len(categories)):
        score[Yi] = clutter_prior(Yi) + conditional_scene_prob(w, Yi) + conditional_supporter_prob('floor', Yi)
        for Yj in neighborhood:
            score[Yi] += co_occurence_prob(neighborhood[Yj], Yj, Yi)
    score = dict(sorted(score.items(), key=lambda item: item[1], reverse=True))
    results = []
    for Yi in score:
        cat = categories[Yi]
        objList = random.sample(objListCat[cat], k=min(5, len(objListCat[cat])))
        # print(Yi, cat, score[Yi], objList)
        secondaryCatalogItems = []
        for obj in objList:
            secondaryCatalogItems.append({"name":obj, "semantic": cat, "thumbnail":f"/thumbnail/{obj}"})
        modelId = objList[0]
        results.append({"name":modelId, "semantic": cat, "thumbnail":f"/thumbnail/{modelId}", "status": "clutterpaletteCategory", "secondaryCatalogItems": json.dumps(secondaryCatalogItems)})
    # print(results)
    return results