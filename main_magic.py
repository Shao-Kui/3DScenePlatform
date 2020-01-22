from flask import Blueprint, request
import numpy as np
import json

app_magic = Blueprint('app_magic', __name__)

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
        result = smart_op.find_placement_and_rotate_given_category(request.json["origin"], 0, request.json["modelId"],
                                                                   objs, request.json["category"],
                                                                   request.json["objectName"])
        d = {'translate': [result[0][0], result[0][1], result[0][2]],
             'rotate': [result[1][0], result[1][1], result[1][2]]}
        return json.dumps(d)
    if request.method == 'GET':
        return "Do not support using GET to using magic add. "
