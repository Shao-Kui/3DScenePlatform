from flask import Blueprint, request
import json
import numpy as np
import os
import orm
from rec_release import recommendation_ls_euclidean

app_ls = Blueprint('app_ls', __name__)
LATENT_SPACE_ROOT = './latentspace'
ls = np.load(os.path.join(LATENT_SPACE_ROOT, 'ls.npy'))
with open('./latentspace/obj-semantic.json') as f:
    obj_semantic = json.load(f)
with open("./latentspace/ls_to_name.json", 'r') as f:
    ls_to_name = json.load(f)
with open("./latentspace/name_to_ls.json", 'r') as f:
    name_to_ls = json.load(f)

def instance(name, cor):
    re = {
        "modelId": name,
        "translate": [
            cor[0],
            cor[1],
            cor[2]
        ],
        "scale": [
            1,
            1,
            1
        ],
        "rotate": [
            0,
            0,
            0
        ],
        "coarseSemantic": obj_semantic[name],
        "bbox": {
            "min": [
                cor[0] - 1,
                cor[1] - 1,
                cor[2] - 1
            ],
            "max": [
                cor[0] + 1,
                cor[1] + 1,
                cor[2] + 1
            ]
        }}
    return re

@app_ls.route("/palette_recommendation", methods=['POST', 'GET'])
def palette_recommendation():
    if request.method == 'POST':
        rec_results = recommendation_ls_euclidean(request.json)
        result = []
        for item in rec_results:
            m = orm.query_model_by_name(item)
            ret = {"id": m.id, "name": m.name, "semantic": m.category.wordnetSynset,
                   "thumbnail": "/thumbnail/%d" % (m.id,)}
            result.append(ret)
        print(result)
        return json.dumps(result)
    if request.method == 'GET':
        return "Do not support using GET to using recommendation. "

@app_ls.route("/latent_space/<obj_id>/<x>/<y>/<z>/")
def latent_space(obj_id, x, y, z):
    x = float(x)
    y = float(y)
    z = float(z)
    idx = name_to_ls[obj_id]
    dis = ls.copy()
    dis = dis - dis[idx]
    dis = np.linalg.norm(dis, axis=1)
    rc = np.argsort(dis)[1:51]

    rn = [instance(ls_to_name[str(i)], [(ls[i] - ls[idx])[0].item()*100 + x,
                                        y,
                                       (ls[i] - ls[idx])[1].item()*100 + z]) for i in rc]
    return json.dumps(rn)
