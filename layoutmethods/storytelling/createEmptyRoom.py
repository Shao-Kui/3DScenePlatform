import shapely
import geopandas as gpd
from shapely.geometry import Point,Polygon, MultiPolygon, LineString
import matplotlib.pyplot as plt
import json
import math
import numpy as np

STEP = 4
INDOOR_SIG = 1
OUTDOOR_SIG = 2
DOOR_SIG = 3
OUTDOOR_WIN_SING = 4
OUTDOOR_WIN_DOUB = 5

areaShapes = {'geometry': [
        Polygon([
            [8,2],[-4,2],[-4,-6],[8,-6]
        ]),
        Polygon([
            [8,6],[-8,6],[-8,2],[8,2]
        ]),
        Polygon([
            [-4, 2],[-8,2],[-8,-6],[ -4,-6]
        ])
    ]}

doors = [
    Point([8,4]),
    Point([-2,2]),
    Point([-6,2])
]

windowSingle = [
    Point([2,-6]),
    Point([-6,-6])
]

windowDouble = [
    Point([6,6]),
    Point([-2,6]),
    Point([-8,4]),
    Point([-2,-6]),
    Point([6,-6])
]

wallOutside = []
wallInside = []

doorAndWin = [
    {
        "list":doors,
        "modelName": "story-WallInterior_DoorwayNarrow"
    },
    {
        "list":windowSingle,
        "modelName": "story-WallOutside_2f_4m_WindowSingle_B"
    },
    {
        "list":windowDouble,
        "modelName": "story-WallOutside_2f_4m_WindowDouble_B"
    }
]

with open('./test/abandondedschool-r0.json') as f:
        sceneJson = json.load(f)

    
def addWallDoorWind(areaShapes, doors, windowSingle, windowDouble, wallOutside, wallInside):
    gdf = gpd.GeoDataFrame(areaShapes, crs="EPSG:4326")
    xmin = gdf.total_bounds[0]
    xmax = gdf.total_bounds[2]
    ymin = gdf.total_bounds[1]
    ymax = gdf.total_bounds[3]
    shapeList = areaShapes['geometry']
    
    for i in range(int(ymin + STEP/2), int(ymax), 4):
        wallOutside.append(Point(xmin, i)) 
        wallOutside.append(Point(xmax, i))
    for j in range(int(xmin + STEP/2), int(xmax), 4):
        wallOutside.append(Point(j, ymin))
        wallOutside.append(Point(j, ymax))
    wallOutside = list(set(wallOutside) - set(doors) - set(windowDouble) - set(windowSingle))
    doorAndWin.append({"list":wallOutside,"modelName":"story-WallOutside_2f_4m_B"})
    

    geoJson = json.loads(gdf.geometry.to_json())
    sceneJson['bbox']['min'] = [geoJson['bbox'][0], 0, geoJson['bbox'][1]]
    sceneJson['bbox']['max'] = [geoJson['bbox'][2], 3, geoJson['bbox'][3]]

    insideWallAlready = []
    rooms = []
    allSet = set(wallOutside) | set(doors) | set(windowDouble) | set(windowSingle)
    for areaShape in shapeList:
        roomWall = []
        room = {}
        areaShapeGeo = gpd.GeoSeries(areaShape)
        areaShapeJson = json.loads(areaShapeGeo.to_json())
        lo = areaShapeJson['features'][0]['geometry']['coordinates'][0]
        lo.pop()
        room['areaShape'] = lo
        room['roomShapeBBox'] = {}
        room['roomShapeBBox']['min'] = [areaShapeJson['bbox'][0],areaShapeJson['bbox'][1]]
        room['roomShapeBBox']['max'] = [areaShapeJson['bbox'][2],areaShapeJson['bbox'][3]]
        
        
        recXmin = room['roomShapeBBox']['min'][0]
        recYmin = room['roomShapeBBox']['min'][1]
        recXmax = room['roomShapeBBox']['max'][0]
        recYmax = room['roomShapeBBox']['max'][1]
        room['areaType'] = 'earth'
        room['layer'] = 1
        
        room['objList'] = []
        wallInside = []
        for i in  range(int(recYmin + STEP/2), int(recYmax), 4):
            roomWall.append(Point(recXmin, i))
            roomWall.append(Point(recXmax, i))
        for j in range(int(recXmin + STEP/2), int(recXmax), 4):
            roomWall.append(Point(j, recYmin))
            roomWall.append(Point(j, recYmax))
        wallInside = list(set(roomWall) - allSet)
        
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
                room['objList'].append(obj)
                insideWallAlready.append(w)

        for item in doorAndWin:
            for w in list(set(item['list']) & set(roomWall)):
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
                room['objList'].append(obj)
                item['list'].remove(w)
        rooms.append(room)
    sceneJson['rooms'] = rooms
    sceneString = json.dumps(sceneJson)
    with open('./test/abandondedschool-r1.json', "w") as outfile:
        outfile.write(sceneString)

if __name__ == "__main__":
    gdf = gpd.GeoDataFrame(areaShapes, crs="EPSG:4326")
    addWallDoorWind(areaShapes, doors, windowSingle, windowDouble, wallOutside, wallInside)
