import shapely
import geopandas as gpd
from shapely.geometry import Point,Polygon, MultiPolygon, LineString
from shapely import box
import matplotlib.pyplot as plt
import json
import math
import numpy as np
import os
import re
import codecs
import csv
from scipy.spatial.transform import Rotation as R
import numpy as np
import random

STEP = 4
MAX_WALL_HEIGHT = 4.576642


wallOutside = []
wallInside = []

scene1 = {
    "theme": "abandondedschool",
    "areaShapes": [
        Polygon([[8,2],[-4,2],[-4,-6],[8,-6]]),
        Polygon([[8,6],[-8,6],[-8,2],[8,2]])
        ],
    "doorAndWin": [
        {
            "type": "door",
            "list": [Point([8,4]),Point([-2,2]),Point([-6,2])],
            "modelName": "story-WallInterior_DoorwayNarrow",
            "coarseSemantic": "Door",
        },
        {
            "type": "windowSingle",
            "list": [Point([2,-6])],
            "modelName": "story-WallOutside_2f_4m_WindowSingle_B",
            "coarseSemantic": "Window"
        },
        {
            "type": "windowDouble",
            "list": [Point([6,6]),Point([-2,6]),Point([-8,4]),Point([-2,-6]),Point([6,-6])],
            "modelName": "story-WallOutside_2f_4m_WindowDouble_B",
            "coarseSemantic": "Window"
        }
    ]
    
}

# def initialRoomShape(room):
    # fig, ax1 = plt.subplots()
   
    # append = [
    #     ,
    #     
    # ]

    #     area = gpd.GeoSeries(Polygon(room['roomShape']))
    #     area.plot(ax = ax1, color = 'pink')
    # plt.show()

def createEmptyRoom(scene):
    with open('./prop/template.json') as f:
        sceneJson = json.load(f)
    with open('./prop/allBboxSurface.json') as f:
        bboxJson  = json.load(f)

    themeName = scene['theme']
    doorAndWin = scene['doorAndWin']
    door = next(item for item in doorAndWin if item['type'] == 'door')['list']
    
    allOutWall = doorAndWin[1:3]
    windowSingle = next(item for item in doorAndWin if item['type'] == 'windowSingle')['list']
    windowDouble = next(item for item in doorAndWin if item['type'] == 'windowDouble')['list']
    
    areaShapes = gpd.GeoSeries(scene['areaShapes'])
    areaShapeJson = json.loads(areaShapes.to_json())
    xmin = areaShapeJson['bbox'][0]
    ymin = areaShapeJson['bbox'][1]
    xmax = areaShapeJson['bbox'][2]
    ymax = areaShapeJson['bbox'][3]

    sceneJson['origin'] = themeName
    sceneJson['bbox']['min'] = [xmin, 0, ymin]
    sceneJson['bbox']['max'] = [xmax, MAX_WALL_HEIGHT, ymax]

    wallOutside = []
    for i in range(int(ymin + STEP/2), int(ymax), 4):
        wallOutside.append(Point(xmin, i)) 
        wallOutside.append(Point(xmax, i))
    for j in range(int(xmin + STEP/2), int(xmax), 4):
        wallOutside.append(Point(j, ymin))
        wallOutside.append(Point(j, ymax))
    wallOutside = list(set(wallOutside) - set(door) - set(windowDouble) - set(windowSingle))
    allOutWall.append({"list":wallOutside,"modelName":"story-WallOutside_2f_4m_B"})
    rooms = []
    allSet = set(wallOutside) | set(door) | set(windowDouble) | set(windowSingle)
    
    for feature in areaShapeJson['features']:
        room = {}

        # sceneJson
        lo = feature['geometry']['coordinates'][0]
        lo.pop()
        room['areaShape'] = lo

        recXmin = feature['bbox'][0]
        recYmin = feature['bbox'][1]
        recXmax = feature['bbox'][2]
        recYmax = feature['bbox'][3]

        # sceneJson
        # room['roomShapeBBox'] = {}
        # room['roomShapeBBox']['min'] = [recXmin,recYmin]
        # room['roomShapeBBox']['max'] = [recXmax,recYmax]

        roomAllWall = []
        
        for i in  range(int(recYmin + STEP/2), int(recYmax), 4):
            roomAllWall.append(Point(recXmin, i))
            roomAllWall.append(Point(recXmax, i))
        for j in range(int(recXmin + STEP/2), int(recXmax), 4):
            roomAllWall.append(Point(j, recYmin))
            roomAllWall.append(Point(j, recYmax))
        wallInside = list(set(roomAllWall) - allSet)
        doorInside = list(set(roomAllWall) & set(door))

        room['objList'] = []
        for w in wallInside:
            obj = {}
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
            addBboxSurface2Scene(obj,bboxJson)
            room['objList'].append(obj)
        
        for d in doorInside:
            obj = {}
            obj['modelId'] = 'story-WallInterior_DoorwayNarrow'
            obj['translate'] = [d.x, 0, d.y]
            obj['scale'] = [1,1,1]
            if d.x == recXmin:
                obj['rotate'] = [0, -0.5 * math.pi, 0]
            elif d.x ==  recXmax:
                obj['rotate'] = [0, 0.5 * math.pi, 0]
            elif d.y == recYmin:
                obj['rotate'] = [0, -math.pi, 0]
            else:
                obj['rotate'] = [0, 0, 0]
            obj['format'] = 'instancedMesh'
            addBboxSurface2Scene(obj,bboxJson)
            room['objList'].append(obj)        

        for item in allOutWall:
            for w in list(set(item['list']) & set(roomAllWall)):
                obj = {}
                obj['modelId'] = item['modelName']
                if 'coarseSemantic' in item.keys():
                    obj['coarseSemantic'] = item['coarseSemantic']
                # print(w.x)
                obj['translate'] = [float(w.x), 0, float(w.y)]
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
                addBboxSurface2Scene(obj,bboxJson)
                item['list'].remove(w)

        room['areaType'] = 'earth'
        room['layer'] = 1
        room['roomShapeBBox'] = {}
        
        areaShape = room['areaShape']
        area = gpd.GeoSeries(Polygon(areaShape))
        for obj in room['objList']:
            objRect = obj2Rectangle(obj)
            area = area.difference(objRect,align=True)
        room['roomShapeBBox']['max'] = list([float(area.bounds.minx),float(area.bounds.miny)])
        room['roomShapeBBox']['min'] = list([float(area.bounds.maxx),float(area.bounds.maxy)])

        rooms.append(room)

    sceneJson['rooms'] = rooms
    sceneString = json.dumps(sceneJson)
    with open('./stories/'+ themeName + '-empty.json', "w") as outfile:
        outfile.write(sceneString)

def getObjBbox(base):
    for root, ds, fs in os.walk(base):
        for f in fs:
            if f.endswith('-AABB.json'):
                modelId = f.split('-AABB.json')[0]
                js = {}
                
                fullname = os.path.join(root,f)
                with open(fullname) as f:
                    aabbJson = json.load(f)
                    js['modelId'] = modelId
                    js['bbox'] = {'max': aabbJson['max'],'min': aabbJson['min']}
                    # js['surface'] = s
                yield js

def writeBboxSurface(base):
    surface = []
    with open('./prop/contactSurface.csv', encoding='utf-8-sig') as f:
        sf = csv.DictReader(f)
        # sw = csv.writer(f)
        surface = list(sf)
    
    allObjBbox = {}
    bboxList = []
    for i in getObjBbox(base):
        js = i
        for item in surface:
            if item['modelId'] == js['modelId']:
                js['surface'] = item['surface']
                break
        else:
            js['surface'] = 'floor'
            # sw.writerow([js['modelId'],'floor'])
        bboxList.append(i)
    # s = next(item for item in surface if item['modelId'] == modelId)['surface']
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
            for item in bboxJson:
                if  item['modelId'] == modelId:
                    obj['originBbox'] = item['bbox']
                    reloadAABB(obj)
                    obj['surface'] = item['surface']
                    break
            else:
                print("cann't find", modelId, "in allBboxSurface.json")
    with open('./stories/' + sceneJsonName, "w", encoding="utf-8") as fw:
        json.dump(sceneJson, fw)   

def addBboxSurface2Scene(obj, bboxJson):
    modelId = obj['modelId']
    j = next(item for item in bboxJson if item['modelId'] == modelId)
    obj['originBbox'] = j['bbox']
    reloadAABB(obj)
    obj['surface'] = j['surface']

def addStoryContent2SceneJson(themeName, sceneJsonName):
    with open('./stories/' + sceneJsonName) as f:
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
    with open('./stories/' + sceneJsonName, "w") as outfile:
        outfile.write(sceneString)

def addStoryContent2Scene(obj, storyJson):
    modelId = obj['modelId']
    for storyPoint in storyJson['story']:
        if(storyPoint['modelId'] == obj['modelId']):
            if('type' in obj.keys() and obj['type'] != 'storypoint'):
                obj['type'] = 'storypoint'
            if not ('storyContents' in obj.keys()):
                data = {}
                data['storyContents'] = storyPoint['storyContents']
                obj.update(data)
            storyJson['story'].remove(storyPoint)

def getWallProjection(sceneJson,wallInRooms):
    walls = []
    rooms = []
    for room in sceneJson['rooms']:
        rooms.append(Polygon(room['areaShape']))
        for obj in room['objList']:
            if obj['format'] == 'instancedMesh':
                o = reloadAABB(obj)
                p1 = Point(o['eightPoints'][3][0],o['eightPoints'][3][2])
                p2 = Point(o['eightPoints'][2][0],o['eightPoints'][2][2])
                line1 = LineString([p1,p2])
                p1 = Point(o['eightPoints'][0][0],o['eightPoints'][0][2])
                p2 = Point(o['eightPoints'][1][0],o['eightPoints'][1][2])
                line2 = LineString([p2,p1])
                if (obj['modelId'] == 'story-WallInside_4m') :
                    walls.append(line1)
                    walls.append(line2)
                if (obj['modelId'] == 'story-WallOutside_2f_4m_B'):
                    walls.append(line1)
    for r in rooms:
        subwall = []
        for w in walls:
            if r.contains(w.centroid):
                subwall.append(w)
        wallInRooms.append(subwall)
    
    combineWallProjection(wallInRooms)

def combineWallProjection(wallInRooms):
    for wir in wallInRooms:
        for w in wir:
            wnext = [i for i in wir if i != w]
            for wn in wnext:
                if((wn.centroid.x == w.centroid.x) & (abs(wn.centroid.y - w.centroid.y) == 4) | (wn.centroid.y == w.centroid.y) & (abs(wn.centroid.x - w.centroid.x) == 4)):
                    bds = gpd.GeoSeries(wn).union(gpd.GeoSeries(w)).bounds
                    p1 = Point(bds.minx,bds.miny)
                    p2 = Point(bds.maxx,bds.maxy)
                    i = wir.index(w)
                    l = list(w.coords)
                    if (l[0][0] < l[1][0]) | (l[0][1] < l[1][1]):
                        w = LineString([p1,p2])
                    elif (l[0][0] > l[1][0]) | (l[0][1] > l[1][1]):
                        w = LineString([p2,p1])
                    wir[i] = w
                    wir.remove(wn)

def addWallProjection2Scene(sceneJson,wallInRooms):
    for room in sceneJson['rooms']:
        i = sceneJson['rooms'].index(room)
        wr = gpd.GeoSeries(wallInRooms[i])
        wallShapeJson = json.loads(wr.to_json())
        wallShapes = []
        for feature in wallShapeJson['features']:
            wallShape = {}
            wallShape = feature['geometry']['coordinates']
            wallShapes.append(wallShape)
        room['wallShapes'] = wallShapes

def addAllJsonData(sceneJsonName,storyJsonName):
    with open(sceneJsonName) as f:
        sceneJson =  json.load(f)
    with open('./prop/allBboxSurface.json') as f:
        bboxJson  = json.load(f)
    with open(storyJsonName) as f:
        storyJson = json.load(f)
    for room in sceneJson['rooms']:
        for obj in room['objList']:
            addBboxSurface2Scene(obj,bboxJson)
            addStoryContent2Scene(obj,storyJson)
    wallInRooms = []
    getWallProjection(sceneJson, wallInRooms)
    addWallProjection2Scene(sceneJson, wallInRooms)
    with open(sceneJsonName, "w", encoding="utf-8") as fw:
        json.dump(sceneJson, fw)   

def addWallShapes2SceneJson(sceneJson):
    walls = []
    rooms = []
    for room in sceneJson['rooms']:
        rooms.append(Polygon(room['areaShape']))
        for obj in room['objList']:
            if (obj['modelId'] == 'story-WallInside_4m') :
                o = reloadAABB(obj)
                p1 = Point(o['eightPoints'][3][0],o['eightPoints'][3][2])
                p2 = Point(o['eightPoints'][2][0],o['eightPoints'][2][2])
                walls.append(LineString([p1,p2]))
                p1 = Point(o['eightPoints'][0][0],o['eightPoints'][0][2])
                p2 = Point(o['eightPoints'][1][0],o['eightPoints'][1][2])
                walls.append(LineString([p2,p1]))
            if (obj['modelId'] == 'story-WallOutside_2f_4m_B'):
                o = reloadAABB(obj)
                p1 = Point(o['eightPoints'][3][0],o['eightPoints'][3][2])
                p2 = Point(o['eightPoints'][2][0],o['eightPoints'][2][2])
                walls.append(LineString([p1,p2]))
    
    wallInRooms = []
    for r in rooms:
        subwall = []
        for w in walls:
            if r.contains(w.centroid):
                subwall.append(w)
        wallInRooms.append(subwall)

    for wir in wallInRooms:
        for w in wir:
            wnext = [i for i in wir if i != w]
            for wn in wnext:
                if((wn.centroid.x == w.centroid.x) & (abs(wn.centroid.y - w.centroid.y) == 4) | (wn.centroid.y == w.centroid.y) & (abs(wn.centroid.x - w.centroid.x) == 4)):
                    bds = gpd.GeoSeries(wn).union(gpd.GeoSeries(w)).bounds
                    p1 = Point(bds.minx,bds.miny)
                    p2 = Point(bds.maxx,bds.maxy)
                    i = wir.index(w)
                    l = list(w.coords)
                    if (l[0][0] < l[1][0]) | (l[0][1] < l[1][1]):
                        w = LineString([p1,p2])
                    elif (l[0][0] > l[1][0]) | (l[0][1] > l[1][1]):
                        w = LineString([p2,p1])
                    wir[i] = w
                    wir.remove(wn)

    for room in sceneJson['rooms']:
        i = sceneJson['rooms'].index(room)
        wr = gpd.GeoSeries(wallInRooms[i])
        wallShapeJson = json.loads(wr.to_json())
        wallShapes = []
        for feature in wallShapeJson['features']:
            wallShape = {}
            wallShape = feature['geometry']['coordinates']
            wallShapes.append(wallShape)
        room['wallShapes'] = wallShapes

def reloadAABB(obj):
    eightPoints = np.array([
        [obj['originBbox']['max'][0], obj['originBbox']['min'][1], obj['originBbox']['max'][2]],
        [obj['originBbox']['min'][0], obj['originBbox']['min'][1], obj['originBbox']['max'][2]],
        [obj['originBbox']['min'][0], obj['originBbox']['min'][1], obj['originBbox']['min'][2]],
        [obj['originBbox']['max'][0], obj['originBbox']['min'][1], obj['originBbox']['min'][2]],
        [obj['originBbox']['max'][0], obj['originBbox']['max'][1], obj['originBbox']['max'][2]],
        [obj['originBbox']['min'][0], obj['originBbox']['max'][1], obj['originBbox']['max'][2]],
        [obj['originBbox']['min'][0], obj['originBbox']['max'][1], obj['originBbox']['min'][2]],
        [obj['originBbox']['max'][0], obj['originBbox']['max'][1], obj['originBbox']['min'][2]],
    ])
    scale = np.array(obj['scale'])
    rX = R.from_euler('x', obj['rotate'][0], degrees=False).as_matrix()
    rY = R.from_euler('y', obj['rotate'][1], degrees=False).as_matrix()
    rZ = R.from_euler('z', obj['rotate'][2], degrees=False).as_matrix()
    rotate = rZ @ rY @ rX
    translate = np.array(obj['translate'])
    center = (np.array(obj['originBbox']['max']) + np.array(obj['originBbox']['min'])) / 2
    center = rotate @ (center * scale) + translate
    eightPoints = eightPoints * scale
    eightPoints = rotate @ eightPoints.T
    eightPoints = eightPoints.T + translate
    obj['bbox'] = {
        'min': list(eightPoints[2]),
        'max': list(eightPoints[4])
    }
    return {
        'eightPoints': eightPoints,
        'center': center
    }

def getAllWallsInRoom(sceneJson):
    walls = []
    rooms = []
    for room in sceneJson['rooms']:
        rooms.append(Polygon(room['areaShape']))
        for obj in room['objList']:
            if obj['format'] == 'instancedMesh':
                walls.append(obj)
    wallInRooms = []
    for r in rooms:
        subwall = []
        for w in walls:
            rect = obj2Rectangle(w)
            if bool(r.intersects(rect)):
                subwall.append(w)
        wallInRooms.append(subwall)
    return wallInRooms

def initialObjPosition(sceneJsonPath):
    with open(sceneJsonPath) as f:
        sceneJson =  json.load(f)

    fig, ax1 = plt.subplots()
    wallObjList = getAllWallsInRoom(sceneJson)
    
    for room in sceneJson['rooms']:
        i = sceneJson['rooms'].index(room)
        objOnWall = wallObjList[i]
        objOnCeiling = wallObjList[i]
        objOnFloor = wallObjList[i]
        for w in objOnWall:
            w = gpd.GeoSeries(obj2Rectangle(w))
            w.plot(ax = ax1, color = 'pink')
        wallShapes = room['wallShapes']
        for w in wallShapes:
            o = gpd.GeoSeries(LineString(w))
            o.plot(ax = ax1, color = 'red')
        for obj in room['objList']:
            if obj['format'] == 'obj':
                if obj['surface'] == 'wall':
                    randomPositionOnWall(obj, room)
                    while(colisionDetectWithList(obj,objOnWall)):
                        randomPositionOnWall(obj, room)
                    objOnWall.append(obj)
                    o = gpd.GeoSeries(obj2Rectangle(obj).buffer(0.1))
                    o.plot(ax = ax1, color = 'blue')
                elif obj['surface'] == 'ceiling':
                    randomPositionOnCeiling(obj,room)
                    while(colisionDetectWithList(obj,objOnCeiling)):
                        randomPositionOnCeiling(obj, room)
                    objOnCeiling.append(obj)
                    o = gpd.GeoSeries(obj2Rectangle(obj))
                    o.plot(ax = ax1, color = 'green')
                elif obj['surface'] == 'floor':
                    randomPositionOnFloor(obj,room)
                    while(colisionDetectWithList(obj,objOnFloor)):
                        randomPositionOnFloor(obj, room)
                    objOnFloor.append(obj)
                    o = gpd.GeoSeries(obj2Rectangle(obj))
                    o.plot(ax = ax1, color = 'yellow')
        # break
    
    with open(sceneJsonPath, "w", encoding="utf-8") as fw:
        json.dump(sceneJson, fw)
    plt.show()

def colisionDetectWithList(obj,objList):
    for o in objList:
        if colisionDetect(obj,o):
            print(obj['modelId'],o['modelId'])
            return True
        elif objList.index(o) == (len(objList) - 1):
            return False


def randomPositionInAreaShape(obj, room):
    areaShape = room['areaShape']
    area = Polygon(areaShape)
    b = area.bounds
    x = random.uniform(b[0],b[2])
    y = random.uniform(b[1],b[3])
    obj['translate'][0] = x
    obj['translate'][2] = y

def randomPositionOnFloor(obj,room):
    randomPositionInAreaShape(obj,room)
    obj['translate'][1] = 0
    reloadAABB(obj)

def randomPositionOnCeiling(obj,room):
    randomPositionInAreaShape(obj,room)
    obj['translate'][1] = MAX_WALL_HEIGHT
    reloadAABB(obj)

def randomPositionOnWall(obj, room):
    wallShapes = room['wallShapes']
    index = random.randint(0,len(wallShapes)-1)
    wall = wallShapes[index]
    dx = int(wall[1][0] - wall[0][0])
    dy = int(wall[1][1] - wall[0][1])
    if (dy == 0) & (dx > 0):
        obj['rotate'] = [0, 0, 0]
        obj['translate'][0] = random.uniform(wall[0][0],wall[1][0])
        obj['translate'][1] = MAX_WALL_HEIGHT / 2
        obj['translate'][2] = wall[0][1]
    elif (dy == 0) & (dx < 0):
        obj['rotate'] = [0, -math.pi, 0]
        obj['translate'][0] = random.uniform(wall[1][0],wall[0][0])
        obj['translate'][1] = MAX_WALL_HEIGHT / 2
        obj['translate'][2] = wall[0][1]
    elif (dx == 0) & (dy > 0):
        obj['rotate'] = [0, -0.5 * math.pi, 0]
        obj['translate'][0] = wall[0][0]
        obj['translate'][1] = MAX_WALL_HEIGHT / 2
        obj['translate'][2] = random.uniform(wall[1][1],wall[0][1])
    else:
        obj['rotate'] = [0, 0.5 * math.pi, 0]
        obj['translate'][0] = wall[0][0]
        obj['translate'][1] = MAX_WALL_HEIGHT / 2
        obj['translate'][2] = random.uniform(wall[0][1],wall[1][1])
    reloadAABB(obj)

def obj2Rectangle(obj):
    minx = min(obj['bbox']['min'][0],obj['bbox']['max'][0])
    maxx = max(obj['bbox']['min'][0],obj['bbox']['max'][0])
    miny = min(obj['bbox']['min'][2],obj['bbox']['max'][2])
    maxy = max(obj['bbox']['min'][2],obj['bbox']['max'][2])
    return box(minx,miny,maxx,maxy)
    

def colisionDetect(obj1,obj2):
    rect1 = obj2Rectangle(obj1)
    rect2 = obj2Rectangle(obj2)
    return bool(rect1.intersects(rect2))

if __name__ == "__main__":
    # 通过模板json和形状初始化一个空房间
    # createEmptyRoom(scene1)

    # 根据本地的AABBjson文件和./prop/中输入的contact Surface得到allBboxSurface json,如无表明接触面，则默认接触地面
    # base = 'C:/Users/Yike Li/Desktop/storyModelsJson/'
    # writeBboxSurface(base)

    # # # sceneJson添加surface和bbox
    # addBboxSurface2SceneJson('test4.json')

    # 弃用，已并到addAllJsonData中。添加storycontent
    # addStoryContent2SceneJson('abandondedschool', 'abandondedschool-r0.json')

    # 弃用，已并到addAllJsonData中。sceneJson添加墙壁shape
    # with open('./stories/test4.json') as f:
    #     sceneJson =  json.load(f)
    # addWallShapes2SceneJson(sceneJson)
    # sceneString = json.dumps(sceneJson)
    # with open('./stories/test4.json', "w") as outfile:
    #     outfile.write(sceneString)

    # 给sceneJson添加上述三个surface和bbox，storycontent，wallshape
    # addAllJsonData('','')

    

    # 
    initialObjPosition('./stories/test4.json')
    # ['story-CardboardBoxes','story-CardboardBoxes-point','story-Locker-point','story-Lockers','story-studentDesks1','story-studentDesks2'
    # 'story-studentDesks3','story-studentDesks4-point','story-ToileT_Urinals','story-Toilet-point','story-Toilets']