import json
import random
import os
import sys
import numpy as np
import math

if len(sys.argv) == 2:
    id = sys.argv[1].split('.')[0]
else:
    id = ''
    base_str = 'ABCDEFGHIGKLMNOPQRSTUVWXYZabcdefghigklmnopqrstuvwxyz0123456789'
    length = len(base_str) - 1
    for i in range(10):
        id += base_str[random.randint(0, length)]

data = {
    "origin":
    id,
    "id":
    id,
    "bbox": {
        "min": [0, 0, 0],
        "max": [6.5, 3, 4.5]
    },
    "up": [0, 1, 0],
    "front": [0, 0, 1],
    "rooms": [
        {
            "id":
            "6.5_4.5_78_0",
            "modelId":
            "Bathroom-6473",
            "roomTypes": ["Bathroom"],
            "bbox": {
                "min": [0, 0, 0],
                "max": [6.5, 3, 4.5]
            },
            "origin":
            "roomframe",
            "roomId":
            0,
            "roomShape": [[0, 0], [6.5, 0], [6.5, 4.5], [0, 4.5]],
            "roomNorm": [[6.123233995736766e-17, 1], [-1, 6.123233995736766e-17], [-6.123233995736766e-17, -1],
                         [1, -6.123233995736766e-17]],
            "roomOrient": [0, -1.5707963267948966, 3.141592653589793, 1.5707963267948966],
            "roomShapeBBox": {
                "max": [6.5, 4.5],
                "min": [0, 0]
            },
            "objList": [
                {
                    "modelId": "126",
                    "roomId": 0,
                    "scale": [1.4285714528998552, 1.0000000146882202, 0.6857142681978191],
                    "orient": 0,
                    "rotate": [0, 0, 0],
                    "key": "17dff201-295b-4bb0-aa5c-9ebb8a340a01",
                    "translate": [1.7999999999999998, 0.8, -0.06],
                    "bbox": {
                        "min": [1.3, 0.8, -0.12],
                        "max": [2.3, 2.2, 0]
                    },
                    "inDatabase": False,
                    "format": "Window",
                    "coarseSemantic": "Window"
                },
                {
                    "modelId": "126",
                    "roomId": 0,
                    "scale": [1.4285714528998554, 1.0000000146882202, 0.6857142681978198],
                    "orient": 0,
                    "rotate": [0, -1.5707963267948966, 0],
                    "key": "0b7438ea-5e35-4eea-a9b9-8204741b3715",
                    "translate": [6.5600000000000005, 0.8, 1.125],
                    "bbox": {
                        "min": [6.5, 0.8, 0.625],
                        "max": [6.62, 2.2, 1.625]
                    },
                    "inDatabase": False,
                    "format": "Window",
                    "coarseSemantic": "Window"
                },
                {
                    "modelId": "126",
                    "roomId": 0,
                    "scale": [1.4285714528998554, 1.0000000146882202, 0.6857142681978198],
                    "orient": 0,
                    "rotate": [0, -1.5707963267948966, 0],
                    "key": "01b6ccfd-433a-41cd-8def-6cf4c0b81570",
                    "translate": [6.5600000000000005, 0.8, 3.375],
                    "bbox": {
                        "min": [6.5, 0.8, 2.875],
                        "max": [6.62, 2.2, 3.875]
                    },
                    "inDatabase": False,
                    "format": "Window",
                    "coarseSemantic": "Window"
                },
                {
                    "modelId": "214",
                    "roomId": 0,
                    "scale": [0.7693432338894608, 1.037735903149512, 0.14457866397731786],
                    "orient": 0,
                    "rotate": [0, 3.141592653589793, 0],
                    "key": "6c14f752-c136-4cda-9c2f-b8ced39f05e8",
                    "translate": [3.35, 0, 4.5600000000000005],
                    "bbox": {
                        "min": [2.95, 0, 4.5],
                        "max": [3.75, 2.2, 4.62]
                    },
                    "inDatabase": False,
                    "format": "Door",
                    "coarseSemantic": "Door"
                },
            ],
            "blockList": [{
                "modelId": "noUse",
                "roomId": 0,
                "scale": [1, 1, 1],
                "orient": 0,
                "rotate": [0, 0, 0],
                "key": "Window",
                "translate": [0, 0, 0],
                "bbox": {
                    "min": [1.3, 0.8, -0.12],
                    "max": [2.3, 2.2, 0]
                },
                "inDatabase": False,
                "format": "Window",
                "coarseSemantic": "Window"
            }, {
                "modelId": "noUse",
                "roomId": 0,
                "scale": [1, 1, 1],
                "orient": 0,
                "rotate": [0, 0, 0],
                "key": "Window",
                "translate": [0, 0, 0],
                "bbox": {
                    "min": [6.5, 0.8, 0.625],
                    "max": [6.62, 2.2, 1.625]
                },
                "inDatabase": False,
                "format": "Window",
                "coarseSemantic": "Window"
            }, {
                "modelId": "noUse",
                "roomId": 0,
                "scale": [1, 1, 1],
                "orient": 0,
                "rotate": [0, 0, 0],
                "key": "Window",
                "translate": [0, 0, 0],
                "bbox": {
                    "min": [6.5, 0.8, 2.875],
                    "max": [6.62, 2.2, 3.875]
                },
                "inDatabase": False,
                "format": "Window",
                "coarseSemantic": "Window"
            }, {
                "modelId": "noUse",
                "roomId": 0,
                "scale": [1, 1, 1],
                "orient": 0,
                "rotate": [0, 0, 0],
                "key": "Door",
                "translate": [0, 0, 0],
                "bbox": {
                    "min": [2.95, 0, 4.5],
                    "max": [3.75, 2.2, 4.62]
                },
                "inDatabase": False,
                "format": "Door",
                "coarseSemantic": "Door"
            }],
        },
    ],
    "PerspectiveCamera": {
        "fov": 75,
        "focalLength": 35,
        "origin": [3.2499999999999893, 6.998104679979006, 2.2500069984157407],
        "rotate": [-1.570795326639436, -1.5229362517602531e-9, 0],
        "target": [3.25, 0, 2.25],
        "roomId": 0,
        "up": [1.5229362517594917e-9, 0.0000010000444491950354, -0.9999999999994998]
    },
    "canvas": {
        "width": 960,
        "height": 578
    }
}

file_list = os.listdir('./object')

for i in range(random.randint(4, 8)):
    file_name = file_list[random.randint(0, len(file_list) - 1)]
    obj = {}
    with open(os.path.join('./object', file_name), 'r') as f:
        js = json.load(f)
        obj['modelId'] = file_name.split('_')[0]
        obj['translate'] = [random.uniform(0, 5), 0, random.uniform(0, 5)]
        obj['scale'] = [np.random.normal(1, 0.1), np.random.normal(1, 0.1), np.random.normal(1, 0.1)]
        obj['roomId'] = 0
        # obj['rotate'] = [random.randint(0, 3) * math.pi / 2, random.randint(0, 3) * math.pi / 2, 0]
        # obj['orient'] = random.randint(0, 3) * math.pi / 2
        obj['rotate'] = [0, 0, 0]
        obj['orient'] = 0
        obj['key'] = id + '_' + str(i)
        obj['format'] = 'glb'
        obj['startState'] = js['data'][random.randint(0, len(js['data']) - 1)]['name']
        obj['isSceneObj'] = True
        obj['isDatabase'] = True
    data['rooms'][0]['objList'].append(obj)

json_str = json.dumps(data, indent=4)
with open('./scenes/' + id + '.json', 'w') as f:
    f.write(json_str)