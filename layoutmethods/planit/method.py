from . import planit
from .data.dataset import create_dataset
from .scene_filter import run_filter
import json
import random
import shutil
import os

with open('./layoutmethods/planit/data/roomidtoplanitid2.json') as f:
    roomidtoplanitid = json.load(f)

def dirSwap(roomType):
    planit.roomType = roomType
    planit.cat_dir = f"{planit.model_dir}/{roomType}/nextcat_30.pt"
    planit.loc_dir = f"{planit.model_dir}/{roomType}/location_150.pt"
    planit.orient_dir = f"{planit.model_dir}/{roomType}/orient_500.pt"
    planit.dims_dir = f"{planit.model_dir}/{roomType}/dims_200.pt"
    planit.data_dir = f"{roomType}"
    planit.save_dir = f"{planit.model_root_dir}/results/{roomType}_release_test"

def getRoomIndex(modelId):
    if modelId in roomidtoplanitid:
        return roomidtoplanitid[modelId]
    else:
        return None

PLANITSKNAME = 'sk'
def createPlanITData(scenejson, roomType):
    if os.path.exists("./layoutmethods/planit/data/good"):
        shutil.rmtree("./layoutmethods/planit/data/good")
    if os.path.exists("./layoutmethods/planit/data/main"):
        shutil.rmtree("./layoutmethods/planit/data/main")
    with open(f'./layoutmethods/planit/data/3d_front/alilevel/{PLANITSKNAME}.json', 'w') as f:
        json.dump(scenejson, f)
    create_dataset()
    filter_description = [("good_house",)]
    run_filter(filter_description, "main", "good", 0, 0, 1, 0, 1)
    shutil.copy(f"./layoutmethods/planit/data/good/json/0.json", f"./layoutmethods/planit/data/{roomType}/json/{PLANITSKNAME}.json")
    shutil.copy(f"./layoutmethods/planit/data/good/0.jpg", f"./layoutmethods/planit/data/{roomType}/{PLANITSKNAME}.jpg")
    shutil.copy(f"./layoutmethods/planit/data/good/0.pkl", f"./layoutmethods/planit/data/{roomType}/{PLANITSKNAME}.pkl")

planitmodels = {}
planitRoomTypes = ['bedroom', 'livingdinning', 'master', 'kids', 'living', 'dinning', 'second']
def roomSynthesis(roomjson):
    modelId = roomjson['modelId']
    if modelId in roomidtoplanitid:
        room_id = roomidtoplanitid[modelId]['id']
        roomType = roomidtoplanitid[modelId]['rt']
    else:
        roomType = random.choice(planitRoomTypes)
        # with open(f'./dataset/alilevel_door2021/{roomjson["origin"]}.json') as f:
        #     scenejson = json.load(f)
        # scenejson['rooms'] = [roomjson]
        scenejson = {
            'origin': roomjson['origin'],
            'id': 'GHOST',
            'bbox': roomjson['bbox'],
            'rooms': [roomjson]
        }
        createPlanITData(scenejson, roomType)
        room_id = PLANITSKNAME
        print(f'New Room! Assigned {roomType}. ')
    """
    if roomType in ['Bedroom', 'SecondBedroom', 'ElderlyRoom', 'NannyRoom']:
        roomType = 'bedroom'
    elif roomType in ['LivingDiningRoom']:
        roomType = 'livingdinning'
    elif roomType in ['MasterBedroom']:
        roomType = 'master'
    elif roomType in ['KidsRoom']:
        roomType = 'kids'
    elif roomType in ['LivingRoom']:
        roomType = 'living'
    elif roomType in ['DiningRoom']:
        roomType = 'dinning'
    """
    dirSwap(roomType)
    if roomType in planitmodels:
        a = planitmodels[roomType]
    else:
        a = planit.SceneSynth(data_dir=planit.data_dir)
        planitmodels[roomType] = a
    return a.synth_room(room_id=room_id, save_dir=planit.save_dir)['rooms'][0]
