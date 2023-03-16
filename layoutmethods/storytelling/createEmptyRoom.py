import shapely
import geopandas as gpd
from shapely.geometry import Point,Polygon, MultiPolygon, LineString
import matplotlib.pyplot as plt
import json
import math
import numpy as np
import os
import re
import codecs
import csv

STEP = 4
INDOOR_SIG = 1
OUTDOOR_SIG = 2
DOOR_SIG = 3
OUTDOOR_WIN_SING = 4
OUTDOOR_WIN_DOUB = 5

wallOutside = []
wallInside = []

scene1 = {
    "theme": "abandondedschool",
    "areaShapes": [
        Polygon([[8,2],[-4,2],[-4,-6],[8,-6]]),
        Polygon([[8,6],[-8,6],[-8,2],[8,2]]),
        Polygon([[-4, 2],[-8,2],[-8,-6],[ -4,-6]])
        ],
    "doorAndWin": [
        {
            "type": "door",
            "list": [Point([8,4]),Point([-2,2]),Point([-6,2])],
            "modelName": "story-WallInterior_DoorwayNarrow"
        },
        {
            "type": "windowSingle",
            "list": [Point([2,-6]),Point([-6,-6])],
            "modelName": "story-WallOutside_2f_4m_WindowSingle_B"
        },
        {
            "type": "windowDouble",
            "list": [Point([6,6]),Point([-2,6]),Point([-8,4]),Point([-2,-6]),Point([6,-6])],
            "modelName": "story-WallOutside_2f_4m_WindowDouble_B"
        }
    ]
    
}

def createEmptyRoom(scene):
    with open('./prop/template.json') as f:
        sceneJson = json.load(f)

    themeName = scene['theme']
    doorAndWin = scene['doorAndWin']
    door = next(item for item in doorAndWin if item['type'] == 'door')['list']
    windowSingle = next(item for item in doorAndWin if item['type'] == 'windowSingle')['list']
    windowDouble = next(item for item in doorAndWin if item['type'] == 'windowDouble')['list']
    sceneJson['origin'] = themeName
    areaShapes = gpd.GeoSeries(scene['areaShapes'])
    areaShapeJson = json.loads(areaShapes.to_json())
    xmin = areaShapeJson['bbox'][0]
    ymin = areaShapeJson['bbox'][1]
    xmax = areaShapeJson['bbox'][2]
    ymax = areaShapeJson['bbox'][3]

    sceneJson['bbox']['min'] = [xmin, 0, ymin]
    sceneJson['bbox']['max'] = [xmax, 3, ymax]

    wallOutside = []
    for i in range(int(ymin + STEP/2), int(ymax), 4):
        wallOutside.append(Point(xmin, i)) 
        wallOutside.append(Point(xmax, i))
    for j in range(int(xmin + STEP/2), int(xmax), 4):
        wallOutside.append(Point(j, ymin))
        wallOutside.append(Point(j, ymax))
    wallOutside = list(set(wallOutside) - set(door) - set(windowDouble) - set(windowSingle))
    doorAndWin.append({"list":wallOutside,"modelName":"story-WallOutside_2f_4m_B"})
    insideWallAlready = []
    rooms = []
    allSet = set(wallOutside) | set(door) | set(windowDouble) | set(windowSingle)
    
    for feature in areaShapeJson['features']:
        room = {}

        lo = feature['geometry']['coordinates'][0]
        # for i in range(0,len(lo)-1,1):
        #     dx = lo[i+1] - lo[i]
        #     dy = lo[i+1] - lo[i]
        lo.pop()
        room['areaShape'] = lo

        recXmin = feature['bbox'][0]
        recYmin = feature['bbox'][1]
        recXmax = feature['bbox'][2]
        recYmax = feature['bbox'][3]
        room['roomShapeBBox'] = {}
        room['roomShapeBBox']['min'] = [recXmin,recYmin]
        room['roomShapeBBox']['max'] = [recXmax,recYmax]

        roomAllWall = []
        
        for i in  range(int(recYmin + STEP/2), int(recYmax), 4):
            roomAllWall.append(Point(recXmin, i))
            roomAllWall.append(Point(recXmax, i))
        for j in range(int(recXmin + STEP/2), int(recXmax), 4):
            roomAllWall.append(Point(j, recYmin))
            roomAllWall.append(Point(j, recYmax))
        wallInside = list(set(roomAllWall) - allSet)

        room['objList'] = []
        for w in wallInside:
            obj = {}
            if not insideWallAlready.count(w):
                obj['modelId'] = 'story-WallInside_4m'
                obj['translate'] = [w.x, 0, w.y]
                obj['scale'] = [1,1,1]
                if w.x == recXmin:
                    obj['rotate'] = [0, -0.5 * math.pi, 0]
                elif w.x ==  recXmax:
                    obj['rotate'] = [0, 0.5 * math.pi, 0]
                elif w.y == recYmin:
                    obj['rotate'] = [0, -math.pi, 0]
                else:
                    obj['rotate'] = [0, 0, 0]
                obj['format'] = 'instancedMesh'
                room['objList'].append(obj)
                insideWallAlready.append(w)

        for item in doorAndWin:
            for w in list(set(item['list']) & set(roomAllWall)):
                obj = {}
                obj['modelId'] = item['modelName']
                obj['translate'] = [w.x, 0, w.y]
                if w.x == xmin:
                    obj['rotate'] = [0, -0.5 * math.pi, 0]
                elif w.x ==  xmax:
                    obj['rotate'] = [0, 0.5 * math.pi, 0]
                elif w.y == ymin:
                    obj['rotate'] = [0, -math.pi, 0]
                else:
                    obj['rotate'] = [0, 0, 0]
                obj['scale'] = [1, 1, 1]
                obj['format'] = 'instancedMesh'
                room['objList'].append(obj)
                item['list'].remove(w)

        room['areaType'] = 'earth'
        room['layer'] = 1
        rooms.append(room)

    sceneJson['rooms'] = rooms
    sceneString = json.dumps(sceneJson)
    with open('./stories/'+ themeName + '-empty.json', "w") as outfile:
        outfile.write(sceneString)

def getObjBboxAndSurface(base):
    surface = []
    with open('./test/contactSurface.csv', encoding='utf-8-sig') as f:
        sf = csv.DictReader(f)
        surface = list(sf)
    for root, ds, fs in os.walk(base):
        for f in fs:
            if f.endswith('-AABB.json'):
                modelId = f.split('-AABB.json')[0]
                js = {}
                s = next(item for item in surface if item['modelId'] == modelId)['surface']
                fullname = os.path.join(root,f)
                with open(fullname) as f:
                    aabbJson = json.load(f)
                    js['modelId'] = modelId
                    js['bbox'] = {'max': aabbJson['max'],'min': aabbJson['min']}
                    js['surface'] = s
                yield js
                # yield modelId

def writeBboxSurface(base):
    allObjBbox = {}
    bboxList = []
    for i in getObjBboxAndSurface(base):
        bboxList.append(i)
    allObjBbox = bboxList
    with open("./prop/allBboxSurface.json", "w", encoding="utf-8") as fw:
        json.dump(allObjBbox, fw)

def addBboxSurface2SceneJson(sceneJsonName):
    with open('./stories/' + sceneJsonName) as f:
        sceneJson =  json.load(f)
    with open('./prop/allBboxSurface.json') as f:
        bboxJson = json.load(f)
    for room in sceneJson['rooms']:
        for obj in room['objList']:
            modelId = obj['modelId']
            j = next(item for item in bboxJson if item['modelId'] == modelId)
            obj['originBbox'] = j['bbox']
            obj['surface'] = j['surface']
    with open('./stories/' + sceneJsonName, "w", encoding="utf-8") as fw:
        json.dump(sceneJson, fw)   

def addStoryContent2SceneJson(themeName, sceneJsonName):
    with open(sceneJsonName) as f:
        sceneJson = json.load(f)
    with open('./stories/' + themeName + '-story.json') as f:
        storyJson = json.load(f)
    
    for room in sceneJson['rooms']:
        for obj in room['objList']:
            for storyPoint in storyJson['story']:
                if(storyPoint['modelId'] == obj['modelId']):
                    if('type' in obj.keys() and obj['type'] != 'storypoint'):
                        obj['type'] = 'storypoint'
                    if not ('storyContents' in obj.keys()):
                        data = {}
                        data['storyContents'] = storyPoint['storyContents']
                        obj.update(data)
                    storyJson['story'].remove(storyPoint)

    sceneString = json.dumps(sceneJson)
    with open(sceneJsonName, "w") as outfile:
        outfile.write(sceneString)

if __name__ == "__main__":
    # createEmptyRoom(scene1)
    # addBboxSurface2SceneJson('abandondedschool-r0.json')
    # base = 'C:/Users/Yike Li/Desktop/storyModelsJson/'
    # writeBboxSurface(base)
    addStoryContent2SceneJson('abandondedschool', 'abandondedschool-r0.json')