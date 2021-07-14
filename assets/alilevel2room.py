import os
import json
from shapely.geometry.polygon import Polygon
from shapely.geometry import Point
from projection2d import processGeo as p2d
import shutil

with open('./dataset/sk_to_ali.json') as f:
    sk_to_ali = json.load(f)
with open('./dataset/full-obj-semantic_suncg.json') as f:
    suncg = json.load(f)

def alilevel2room():
    AREA = {}
    levelnames = os.listdir('./dataset/alilevel_windoorFix')
    for levelname in levelnames:
        with open(f'./dataset/alilevel_windoorFix/{levelname}') as f:
            level = json.load(f)
        for room in level['rooms']:
            if len(room['roomTypes']) == 0:
                roomtype = 'Unknown'
            else:
                roomtype = room['roomTypes'][0]
            newlevel = level.copy()
            newlevel['rooms'] = [room]
            if(len(room['objList']) != 0):
                newlevel['bbox'] = room['bbox']
            newlevel['rooms'][0]['roomId'] = 0
            try:
                newlevel['rooms'][0]['area'] = Polygon(p2d(f'./dataset/room/{newlevel["origin"]}', f'{newlevel["rooms"][0]["modelId"]}f.obj')).area
            except Exception as e:
                newlevel['rooms'][0]['area'] = 0.0
                print(e)
            for o in newlevel['rooms'][0]['objList']:
                o['roomId'] = 0
                if o['modelId'] in sk_to_ali or o['modelId'] in suncg:
                    o['inDatabase'] = True
                else:
                    o['inDatabase'] = False
            if not os.path.exists(f'./dataset/alilevel_inRooms/{roomtype}'):
                os.makedirs(f'./dataset/alilevel_inRooms/{roomtype}')
            if roomtype not in AREA:
                AREA[roomtype] = {}
            samefileindex = 0
            finalfilename = f'./dataset/alilevel_inRooms/{roomtype}/{roomtype}-{newlevel["origin"]}-{samefileindex}.json'
            while os.path.exists(finalfilename):
                samefileindex += 1
                finalfilename = f'./dataset/alilevel_inRooms/{roomtype}/{roomtype}-{newlevel["origin"]}-{samefileindex}.json'
            with open(finalfilename, 'w') as f:
                json.dump(newlevel, f)
            AREA[roomtype][f'{roomtype}-{newlevel["origin"]}-{samefileindex}'] = newlevel['rooms'][0]['area']
    with open('./dataset/AREA.json', 'w') as f:
        json.dump(AREA, f)

def AREAAnalysis(rt, deleteobj=True):
    with open('./dataset/AREA.json') as f:
        AREA = json.load(f)
    masterbedroom = sorted(AREA[rt].items(), key=lambda item: item[1], reverse=True)
    if rt in ['DiningRoom', 'LivingRoom', 'SecondBedroom']:
        masterbedroom = list(filter(lambda item: item[1] < 29.9, masterbedroom))
        masterbedroom = masterbedroom[0:60]
    elif rt in ['MasterBedroom']:
        masterbedroom = list(filter(lambda item: item[1] > 24.1 and item[1] < 29.0, masterbedroom))
    elif rt in ['LivingDiningRoom']:
        masterbedroom = list(filter(lambda item: item[1] < 36 and item[1] > 34, masterbedroom))
    else:
        masterbedroom = masterbedroom[0:60]
    # print(masterbedroom[0], masterbedroom[19])
    masterbedroom = dict(masterbedroom)
    if not os.path.exists(f'C:/Users/ljm/Desktop/untitled2/showncases_us1/{rt}'):
        os.makedirs(f'C:/Users/ljm/Desktop/untitled2/showncases_us1/{rt}')
    for filename in masterbedroom:
        if deleteobj:
            with open(f'./dataset/alilevel_inRooms/{rt}/{filename}.json') as f:
                config = json.load(f)
            newobjlist = []
            for obj in config['rooms'][0]['objList']:
                if obj['coarseSemantic'] not in ['Window', 'Door', 'window', 'door']:
                    continue
                newobjlist.append(obj)
            config['rooms'][0]['objList'] = newobjlist
            with open(f'C:/Users/ljm/Desktop/untitled2/showncases_us1/{rt}/{filename}.json', 'w') as f:
                json.dump(config, f)
        else:
            shutil.copy(f'./dataset/alilevel_inRooms/{rt}/{filename}.json', f'C:/Users/ljm/Desktop/untitled2/showncases_us1/{rt}/{filename}.json')

if __name__ == "__main__":
    # alilevel2room()
    AREAAnalysis('MasterBedroom')
    AREAAnalysis('LivingDiningRoom')
    AREAAnalysis('SecondBedroom')
    AREAAnalysis('DiningRoom')
    AREAAnalysis('LivingRoom')
    AREAAnalysis('KidsRoom')
    # AREAAnalysis('Library')
