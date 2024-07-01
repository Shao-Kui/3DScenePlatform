from operator import mod
from types import MethodType
from flask import Blueprint, request, send_file
import numpy as np
import os
import json
import random
from shapely.geometry.polygon import Polygon
from shapely.geometry import Point
from layoutmethods.projection2d import processGeo as p2d, getobjCat, objCatList, roomTypeDemo, objListCat, categoryRelation, wallRelation, categoryCodec
from sketch_retrieval.generate_descriptor import sketch_search, sketch_search_suncg, sketch_search_non_suncg
import sk

app_magic = Blueprint('app_magic', __name__)

def priorTransform(p, translate, orient, scale):
    p = np.array(p)
    translate = np.array(translate)
    orient = np.array(orient)
    scale = np.array(scale)
    result = p.copy()
    result[:, [0,1,2]] *= scale
    result[:, 0] =  np.cos(orient) * p[:, 0] + np.sin(orient) * p[:, 2]
    result[:, 2] = -np.sin(orient) * p[:, 0] + np.cos(orient) * p[:, 2]
    result[:, [0,1,2]] += translate
    result[:, 3] += orient # transformations include orientations; 
    return result.tolist()

SWAP_RESTART = True
@app_magic.route("/mageAddSwapInstance", methods=['POST'])
def mageAddSwapInstance():
    insname = request.json['insname']
    existList = request.json['existList']
    inscat = getobjCat(insname)
    # a special mechanism for wall objects and categories with only one object;  
    if(len(objListCat[inscat]) <= 1):
        wallalternative = ["313", "781", "124", "633"]
        newinsname = insname
        if insname in wallalternative:
            while newinsname == insname:
                newinsname = random.choice(wallalternative) 
        return newinsname
    # the following algorithm alleviate both IO and user satisfaction; 
    insindex = existList.index(insname)
    while insindex < len(existList):
        existi = existList[insindex]
        insindex += 1
        if inscat == getobjCat(existi) and insname != existi:
            return existi
    # if being executed till then, means we do not find another newinsname; 
    global SWAP_RESTART
    if SWAP_RESTART:
        for existi in existList:
            if inscat == getobjCat(existi) and insname != existi:
                SWAP_RESTART = not SWAP_RESTART
                return existi 
    else:
        newinsname = random.choice(objListCat[inscat])
        while newinsname == insname:
            newinsname = random.choice(objListCat[inscat])
        SWAP_RESTART = not SWAP_RESTART
        return newinsname
    # if being executed till then, means we still dont find another newinsname; 
    newinsname = random.choice(objListCat[inscat])
    while newinsname == insname:
        newinsname = random.choice(objListCat[inscat])
    SWAP_RESTART = not SWAP_RESTART
    return newinsname

@app_magic.route("/priors_of_wall", methods=['POST'])
def priors_of_wall():
    rj = request.json
    res = {'object': [], 'mapping': {}, 'coarseSemantic': {}}
    if 'auxiliaryWallObj' in rj:
        res_prev = rj['auxiliaryWallObj']
        res['emptyChoice'] = res_prev['emptyChoice']
    else:
        res_prev = res.copy()
        res['emptyChoice'] = '781'
        res['object'].append(res['emptyChoice'])
        # res['categoryCodec'] = categoryCodec
    for obj in rj['objList']:
        if 'key' not in obj:
            continue
        if obj['key'] in res_prev['mapping']:
            res['mapping'][obj['key']] = res_prev['mapping'][obj['key']]
            continue
        _mageAddW = wallRelation[getobjCat(obj['modelId'])]['_mageAddWall']
        if len(_mageAddW) == 0:
            res['mapping'][obj['key']] = 'null'
            continue
        else:
            res['mapping'][obj['key']] = random.choice(objListCat[random.choice(_mageAddW)])
    # filling objects to be loaded to the front-end; 
    for thekey in res['mapping']:
        if res['mapping'][thekey] not in res['object']:
            if res['mapping'][thekey] == 'null':
                continue
            res['object'].append(res['mapping'][thekey])
    for newobjname in res['object']:
        res['coarseSemantic'][newobjname] = getobjCat(newobjname)
    return json.dumps(res)

@app_magic.route("/priors_of_roomShape", methods=['POST'])
def priors_of_roomShape():
    rj = request.json
    existingCatList = []
    for obj in rj['objList']:
        if obj is None:
            continue
        if 'modelId' not in obj:
            continue
        if obj['modelId'] not in objCatList:
            continue
        if len(objCatList[obj['modelId']]) == 0:
            continue
        if objCatList[obj['modelId']][0] not in existingCatList:
            existingCatList.append(objCatList[obj['modelId']][0])
    existingPendingCatList = existingCatList.copy()
    res = {'object': [], 'prior': [], 'index': [], 'coarseSemantic': {}, 'catMask': []}
    if 'auxiliaryDomObj' in rj:
        if 'heyuindex' in rj['auxiliaryDomObj']:
            res['heyuindex'] = rj['auxiliaryDomObj']['heyuindex']
        for objname in rj['auxiliaryDomObj']['object']:
            if objCatList[objname][0] not in existingPendingCatList:
                existingPendingCatList.append(objCatList[objname][0])
    # print(existingCatList)
    # print(existingPendingCatList)
    # load and process room shapes; 
    # room_meta = p2d('.', f'/dataset/room/{rj["origin"]}/{rj["modelId"]}f.obj')
    # room_meta = room_meta[:, 0:2]
    room_meta = np.array(rj["roomShape"])
    wallSecIndices = np.arange(1, len(room_meta)).tolist() + [0]
    res['room_meta'] = room_meta.tolist()
    rv = room_meta[:] - room_meta[wallSecIndices]
    normals = rv[:, [1,0]]
    normals[:, 1] = -normals[:, 1]
    res['room_orient'] = np.arctan2(normals[:, 0], normals[:, 1]).tolist()
    res['room_oriNormal'] = normals.tolist()
    # room_polygon = Polygon(room_meta[:, 0:2]) # requires python library 'shapely'
    # currently, we hack few available coherent groups...
    roomTypeSuggestedList = []
    categoryList = []
    for rt in rj['roomTypes']:
        if 'heyuindex' not in res:
            res['heyuindex'] = np.random.randint(len(roomTypeDemo[rt]))
        categoryList += roomTypeDemo[rt][res['heyuindex']]
        break
    for cat in categoryList:
        if cat in existingCatList:
            continue
        roomTypeSuggestedList.append(random.choice(objListCat[cat]))
    if 'auxiliaryDomObj' not in rj: # if this is the first time calling this function for the pending room...
        res['object'] = roomTypeSuggestedList
    else:
        # re-fuel the pending object list; 
        for newobjname in roomTypeSuggestedList:
            if objCatList[newobjname][0] in existingPendingCatList:
                continue
            rj['auxiliaryDomObj']['object'].append(newobjname)
        res['object'] = rj['auxiliaryDomObj']['object'].copy()
        for objname in rj['auxiliaryDomObj']['object']:
            # if the specific instance is already in the room;
            if objCatList[objname][0] in existingCatList: 
                res['object'].remove(objname)

    if len(res['object']) == 0: # if a recommendation list is full: 
        pass

    # load wall priors; 
    for obj in res['object']:
        with open(f'./latentspace/wdot-4/{obj}.json') as f:
            wallpri = json.load(f)
            res['prior'] += wallpri
            res['index'] += np.full(len(wallpri), obj).tolist()
            # res['catMask'] += np.full(len(wallpri), categoryCodec[getobjCat(obj)]).tolist()
    for newobjname in res['object']:
        res['coarseSemantic'][newobjname] = getobjCat(newobjname)
    return json.dumps(res)

if __name__ == "__main__":
    priors_of_roomShape()

# process priors of secondary objects; 
@app_magic.route("/priors_of_objlist", methods=['POST', 'GET'])
def priors_of_objlist():
    if request.method == 'GET':
        return "Please refer to POST method for acquiring priors. "
    # indexIndicator = 0
    # 'existPair': ['i_dom-c_sec': 'i_sec']
    res = {'prior': [], 'index': [], 'object': [], 'existPair': {}, 'belonging': [], 'coarseSemantic': {}, 'catMask': []}
    room_json = request.json
    if 'auxiliarySecObj' in room_json:
        aso = room_json['auxiliarySecObj']
    else:
        aso = res.copy()
    # note that we currently do not consider a dominant object with two copies; 
    instancePairCount = {}
    for obj in room_json['objList']:
        if 'mageAddDerive' not in obj:
            continue
        if obj['mageAddDerive'] == "":
            continue
        if obj['mageAddDerive'] not in instancePairCount:
            instancePairCount[obj['mageAddDerive']] = 1
        else:
            instancePairCount[obj['mageAddDerive']] += 1
    for obj in room_json['objList']: # for each existing object: 
        if obj is None:
            continue
        if 'modelId' not in obj:
            continue
        ppri = f'./latentspace/pos-orient-4/{obj["modelId"]}.json'
        if os.path.exists(ppri):
            with open(ppri) as f:
                pri = json.load(f)
        else:
            continue
        for c_sec in pri:
            # e.g., Loveseat Sofa; 
            if c_sec not in categoryRelation[getobjCat(obj['modelId'])]:
                continue
            pairid = f'{obj["modelId"]}-{c_sec}'
            if pairid in aso['existPair']:
                objname = aso['existPair'][pairid]
            else:
                if 'share' in categoryRelation[getobjCat(obj['modelId'])][c_sec]: 
                    objname = random.choice(objListCat[
                        random.choice(categoryRelation[getobjCat(obj['modelId'])][c_sec]['share'])
                    ])
                    # print(f'selected: {objname} of {getobjCat(objname)}')
                else:
                    objname = random.choice(objListCat[c_sec])
            pairInsid = f'{obj["modelId"]}-{objname}'
            res['existPair'][pairid] = objname
            if objname not in res['object']:
                res['object'].append(objname)
            if pairInsid in instancePairCount and 'max' in categoryRelation[getobjCat(obj['modelId'])][c_sec]:
                if instancePairCount[pairInsid] >= categoryRelation[getobjCat(obj['modelId'])][c_sec]['max']:
                    continue
            # the following priors are involved in real-time calculation; 
            res['prior'] += priorTransform(pri[c_sec], obj['translate'], obj['orient'], obj['scale'])
            res['index'] += np.full(len(pri[c_sec]), objname).tolist()
            res['catMask'] += np.full(len(pri[c_sec]), categoryCodec[getobjCat(objname)]).tolist()
            res['belonging'] += np.full(len(pri[c_sec]), obj["modelId"]).tolist()
        # for objname in pri:
        #     if objname not in res['object']:
        #         res['object'].append(objname)
        #     res['prior'] += priorTransform(pri[objname], obj['translate'], obj['orient'], obj['scale'])
        #     res['index'] += np.full(len(pri[objname]), objname).tolist()
            # np.arange(indexIndicator, indexIndicator + len(pri[objname])).tolist()
            # indexIndicator = indexIndicator + len(pri[objname])
    # print(instancePairCount)
    for newobjname in res['object']:
        res['coarseSemantic'][newobjname] = getobjCat(newobjname)
    return json.dumps(res)

@app_magic.route("/magic_add", methods=['POST', 'GET'])
def magic_add():
    objs = []
    if request.method == 'POST':
        room_json = request.json["roomjson"]
        thetranslate = np.array(request.json["translate"])
        # if no object is in the room, 
        if len(room_json['objList']) == 0:
            # then infer the first object; 
            ret['valid'] = 0
            return json.dumps(ret)
        # find the nearest object; 
        odis = 1000000
        ret = {}
        nearestObj = None
        for obj in room_json['objList']:
            dis = np.linalg.norm(thetranslate - np.array(obj['translate']))
            if dis < odis:
                odis = dis
                nearestObj = obj
        # if no object in the room; 
        if nearestObj is None:
            # infer the first object
            ret['valid'] = 0
            return json.dumps(ret)
        ret['valid'] = 1
        return json.dumps(ret)

    if request.method == 'GET':
        return "Do not support using GET to using magic add. "

@app_magic.route("/magic_position", methods=['POST', 'GET'])
def magic_position():
    objs = []
    if request.method == 'POST':
        # for o in request.json["objList"]:
        #     if o is not None:
        #         objs.append(o)
        # with open('./mp.json', 'w') as f:
        #     json.dump({"objList":objs, "translate": request.json["translate"]}, f)
        # result = smart_op.find_category_and_rotate_given_placement("_",0,"_",objs,request.json["translate"])
        # d = {'cat':result[0], 'rotate':[result[1][0], result[1][1], result[1][2]]}
        # models=orm.query_models(result[0],(0,1))
        # ret=[{"id":m.id,"name":m.name,"semantic":m.category.wordnetSynset,"thumbnail":"/thumbnail/%d"%(m.id,)} for m in models]
        # if len(ret) == 0:
        #     return json.dumps({'valid':0})
        # ret = ret[0]
        # ret['rotate'] = d['rotate']
        # ret['valid'] = 1
        # return json.dumps(ret)
        room_json = request.json["roomjson"]
        thetranslate = np.array(request.json["translate"])
        hid = room_json['origin']
        with open('./suncg/level/{}/{}-l0.json'.format(hid, hid)) as f:
            origin_room_json = json.load(f)['rooms'][room_json['roomId']]
        odis = 10000
        ret = {}
        for obj in origin_room_json['objList']:
            dis = np.linalg.norm(thetranslate - np.array(obj['translate']))
            if dis < odis:
                odis = dis
                ret['name'] = obj['modelId']
                ret['rotate'] = obj['rotate']
                ret['scale'] = obj['scale']
        ret['valid'] = 1
        return json.dumps(ret)

    if request.method == 'GET':
        return "Do not support using GET to using magic add. "

@app_magic.route("/magic_category", methods=['POST', 'GET'])
def magic_category():
    objs = []
    if request.method == 'POST':
        for o in request.json["objList"]:
            if o is not None:
                objs.append(o)
        with open('./mp.json', 'w') as f:
            json.dump({"objList": objs, "category": request.json["category"], "origin": request.json["origin"],
                       "modelId": request.json["modelId"]}, f)
        result = smart_op.find_placement_and_rotate_given_category(request.json["origin"], 0, request.json["modelId"], objs, request.json["category"], request.json["objectName"])
        d = {'translate': [result[0][0], result[0][1], result[0][2]], 'rotate': [result[1][0], result[1][1], result[1][2]]}
        return json.dumps(d)
    if request.method == 'GET':
        return "Do not support using GET to using magic add. "

@app_magic.route("/mageAddSingle", methods=['POST', 'GET'])
def mageAddSingle():
    tarObj = request.json['tarObj']
    res = {'subPrior': [], 'domPrior': [], 'belonging': []}
    for room in request.json['rooms']:
        for obj in room['objList']:
            if obj is None:
                continue
            if 'modelId' not in obj:
                continue
            ppri = f'./latentspace/pos-orient-4/{obj["modelId"]}.json'
            if os.path.exists(ppri):
                with open(ppri) as f:
                    pri = json.load(f)
            else:
                continue
            for c_sec in pri:
                if c_sec != sk.getobjCat(tarObj) or c_sec not in categoryRelation[getobjCat(obj['modelId'])]:
                    continue
                res['subPrior'] += priorTransform(pri[c_sec], obj['translate'], obj['orient'], obj['scale'])
                res['belonging'] += np.full(len(pri[c_sec]), obj["modelId"]).tolist()
    with open(f'./latentspace/wdot-4/{tarObj}.json') as f:
        res['domPrior'] += json.load(f)
    return json.dumps(res)

with open('./latentspace/name_to_ls_suncgonly.json') as f:
    name_to_ls = json.load(f)
with open('./latentspace/ls_to_name_suncgonly.json') as f:
    ls_to_name = json.load(f)
with open('./dataset/obj_coarse_semantic.json') as f:
    obj_coarse_semantic = json.load(f)
ls = np.load("./latentspace/ls-release-2.npy")

@app_magic.route("/rec_ls_euc", methods=['POST'])
def recommendation_ls_euclidean():
    e_room = []
    for modelId in request.json:
        if modelId in name_to_ls:
            e_room.append(modelId)
            continue
        e_room.append(sketch_search_suncg(f'./dataset/object/{modelId}/render20/render-{modelId}-10.png', k=1)[0])
    dist = np.zeros((len(ls_to_name)))
    for item in e_room:
        test_point = ls[name_to_ls[item]].reshape(1, 2)
        dist += np.linalg.norm(ls - test_point, axis=1)
    indices = np.argsort(dist)
    counter = 0
    elements = []
    existObjects = []
    for i in indices:
        if ls_to_name[str(i)] in e_room:
            continue
        modelId = ls_to_name[str(i)]
        # modelId = sketch_search_non_suncg(f'H:/ObjectLibrary/{modelId}/render20/render-{modelId}-10.png', k=1)[0]
        # if sk.getobjCat(modelId) == sk.getobjCat(e_room[0]):
        #     continue
        if obj_coarse_semantic[modelId] == obj_coarse_semantic[e_room[0]]:
            continue
        if modelId in existObjects:
            continue
        else:
            existObjects.append(modelId)
        elements.append({
            'index': counter,
            'modelId': modelId,
            'x': ls[i, 0],
            'y': ls[i, 1],
            'coarseSemantic': sk.getobjCat(modelId)
        })
        counter += 1
        if counter >= 20:
            break
    subeles = []
    for modelId in request.json:
        if sk.getobjCat(modelId) in categoryRelation:
            for cat in categoryRelation[sk.getobjCat(modelId)]:
                if len(objListCat[cat]) >= 5:
                    subeles += random.sample(objListCat[cat], 5)
                else:
                    subeles += objListCat[cat]
    # subeles += random.sample(objListCat['King-size Bed'], 1)
    for modelId in subeles:
        if modelId in name_to_ls:
            suncgid = modelId
        else:
            suncgid = sketch_search_suncg(f'./dataset/object/{modelId}/render20/render-{modelId}-10.png', k=1)[0]
        i = name_to_ls[str(suncgid)]
        elements.append({
            'index': counter,
            'modelId': modelId,
            'x': ls[i, 0],
            'y': ls[i, 1],
            'coarseSemantic': sk.getobjCat(modelId)
        }) 
        counter += 1
    return json.dumps(elements)

# code is from: https://stackoverflow.com/questions/55392019/get-random-points-within-polygon-corners
def random_points_within(poly, num_points):
    min_x, min_y, max_x, max_y = poly.bounds
    points = []
    while len(points) < num_points:
        random_point = Point([random.uniform(min_x, max_x), random.uniform(min_y, max_y)])
        if (random_point.within(poly)):
            points.append(random_point)
    res = []
    for point in points:
        res.append([point.x, point.y])
    return res

@app_magic.route("/magic_samplepoints", methods=['POST', 'GET'])
def mageAddAuto():
    rj = request.json
    room_meta = p2d('.', f'/dataset/room/{rj["origin"]}/{rj["modelId"]}f.obj')
    room_meta = room_meta[:, 0:2]
    samples = random_points_within(Polygon(room_meta), 500)
    return json.dumps(samples)

@app_magic.route("/availableCGS/<domObjName>", methods=['GET'])
def availableCGS(domObjName):
    if os.path.exists(f'./layoutmethods/cgseries/{domObjName}/'):
        return json.dumps(os.listdir(f'./layoutmethods/cgseries/{domObjName}/'))
    else:
        return json.dumps([])

@app_magic.route("/cgsPreview/<domObjName>/<seriesName>", methods=['GET'])
def cgsPreview(domObjName, seriesName):
    ls = os.listdir(f'./layoutmethods/cgseries/{domObjName}/{seriesName}/')
    imageNames = []
    for l in ls:
        if '.png' in l:
            imageNames.append(l)
    res = max(imageNames, key=lambda x:len(x)) 
    return send_file(f'./layoutmethods/cgseries/{domObjName}/{seriesName}/{res}')

CGSList_Bed = []
for cgsdom in ['1034','1040','1050','1217','1238','1262','1305','1397','1409','1526','1677','3169','4338','4478','4912','5010','5259','5312','5608','6200','6313','9226','9416','9778']:
    for cgsseries in os.listdir(f'./layoutmethods/cgseries/{cgsdom}'):
        CGSList_Bed.append({'dom': cgsdom, 'series': cgsseries})
CGSList_Cof = []
for cgsdom in ['1023','1025','1049','1240','1359','1394','1484','1806','1830','1908','10126','10198','10216','10487','10909','2624','2919','4314','5933','7644','7896','8493','9532']:
    for cgsseries in os.listdir(f'./layoutmethods/cgseries/{cgsdom}'):
        CGSList_Cof.append({'dom': cgsdom, 'series': cgsseries})
CGSList_Din = []
for cgsdom in ['1041','1133','1198','1993','10568','2096','3118','3429','4839','6824','8983','9363','9704']:
    for cgsseries in os.listdir(f'./layoutmethods/cgseries/{cgsdom}'):
        CGSList_Din.append({'dom': cgsdom, 'series': cgsseries})
@app_magic.route("/getCGSCat/<cat>", methods=['GET'])
def getCGSCat(cat):
    if cat == 'CGS-床':
        return json.dumps(CGSList_Bed) 
    elif cat == 'CGS-茶几':
        return json.dumps(CGSList_Cof)
    elif cat == 'CGS-餐桌':
        return json.dumps(CGSList_Din)
    return json.dumps([])

@app_magic.route("/getCGS/<domObjName>/<seriesName>", methods=['GET'])
def getCGS(domObjName, seriesName):
    with open(f'./layoutmethods/cgseries/{domObjName}/{seriesName}/result.json') as f:
        return json.dumps(json.load(f)) 

@app_magic.route("/coherent_group_series", methods=['POST'])
def coherent_group_series():
    if not os.path.exists(f'./layoutmethods/cgseries/{request.json["domID"]}/'):
        return json.dumps({})
    else:
        seriesNames = os.listdir(f'./layoutmethods/cgseries/{request.json["domID"]}/')
        if len(seriesNames) == 0:
            return json.dumps({})
        else:
            if 'seriesName' in request.json:
                seriesName = request.json['seriesName']
            else:
                seriesName = random.choice(seriesNames)
            with open(f'./layoutmethods/cgseries/{request.json["domID"]}/{seriesName}/result.json') as f:
                return json.dumps(json.load(f))
    # with open(f'./layoutmethods/cgseries/{request.json["domID"]}/index.json') as f:
    #     cgseries = json.load(f)
    # return json.dumps(random.choice(cgseries))
