import geopandas as gpd
import shapely
from shapely.geometry import Point,Polygon, MultiPolygon, LineString
import matplotlib.pyplot as plt
import json
import math
import numpy as np
import sys
from initialRoom import *
sys.path.append('..')
from relationHandler import *

OFFSET = 0.2
MAX_VISIBLE_AREA = 3
MIN_VISIBLE_AREA = 0.5
VIEWING_FRUSTUM_PILE = 3
VIEWING_FRUSTUM_LINE_SPACE = 0.3
VIEWING_FRUSTUM_INVREMENT = 0.2

def wall2Polygon(room):
    shapes = []
    if('roomShape' in room.keys()):
        for shape in room['roomShape']:
            shapes.append([shape[0],shape[1]])
    return Polygon(shapes)

def objOffset(polygon):
    objGeo = gpd.GeoSeries(polygon)
    offset = objGeo.buffer(OFFSET, cap_style = 2)
    return offset

def wallOffset(polygon):
    wallGeo = gpd.GeoSeries(polygon)
    offset = wallGeo.boundary.buffer(OFFSET, cap_style = 2)
    return offset

def connectivityNum(room,walls):
    if('areaShape' in room.keys()):
        roomPolygon = wall2Polygon(room)
        roomOffsetGeo = wallOffset(roomPolygon)
        allOffsetGeo = roomOffsetGeo

        fig, ax1 = plt.subplots()
        roomGeo = gpd.GeoSeries(roomPolygon)
        roomGeo.plot(ax = ax1, color = 'white')

        for obj in room['objList']:
            if('bbox' in obj.keys()):
                objPolygon = obj2Rectangle(obj)
                objOffsetGeo = objOffset(objPolygon)
                objOffsetGeo.plot(ax = ax1, color = 'pink')
                allOffsetGeo = allOffsetGeo.union(objOffsetGeo,align = True)
        
        for wall in walls:
            wallPolygon = obj2Rectangle(wall)
            wallOffsetGeo = objOffset(wallPolygon)
            wallOffsetGeo.plot(ax = ax1, color = 'pink')
            allOffsetGeo = allOffsetGeo.union(wallOffsetGeo,align = True)

        rest = roomGeo.difference(allOffsetGeo,align=True)
        j  = rest.to_json()
        y = json.loads(j)
        print(j)
        features = y['features']
        for feature in features:
            if ('geometry' in obj.keys()):
                coordinates = feature['geometry']['coordinates']
            else:
                return 0
            
        co = list(coordinates)
        connectionPart = float(len(co))
        return(connectionPart)
    
    else:
        return 0

def visiableDis(obj):
    interval = []
    length = (obj['originBbox']['max'][0] - obj['originBbox']['min'][0]) * obj['scale'][0]
    width = (obj['originBbox']['max'][1] - obj['originBbox']['min'][1]) * obj['scale'][1]
    hight = (obj['originBbox']['max'][2] - obj['originBbox']['min'][2]) * obj['scale'][2]
    area = math.sqrt(pow(length,2) + pow(width,2)) * hight
    interval.append(MIN_VISIBLE_AREA/area)
    interval.append(MAX_VISIBLE_AREA/area)
    return interval

class storyPoint:
    def __init__(self, name: str, storyIndex: int, intervalMin: float, intervalMax: float, polygon: Polygon):
        self.name = name
        self.storyIndex = storyIndex
        self.intervalMin = intervalMin
        self.intervalMax = intervalMax
        self.polygon = polygon
    def __repr__(self):
        return str((self.name, self.storyIndex))

def objExpandAd(obj):
    objProjection = obj2Rectangle(obj)
    objPro = gpd.GeoSeries(objProjection)
    objOff = objOffset(objProjection)
    # fig, ax1 = plt.subplots()
    
    # objOff.plot(ax = ax1, color = 'pink')
    # objPro.plot(ax = ax1, color = 'yellow')
    
    AABB = reloadAABB(obj)
    center = list(AABB['center'])

    # 对角线
    minP = Point([obj['bbox']['min'][0] ,obj['bbox']['min'][2] ])
    maxP = Point([obj['bbox']['max'][0] ,obj['bbox']['max'][2] ])
    b = minP.distance(maxP) / 2
    obj['b'] = b

    # offset 和 center的中点 上左下右
    a = []
    x = abs(float(objOff.bounds.maxx) - center[0]) / 2
    y = abs(float(objOff.bounds.maxy)- center[2]) / 2
    a.append([center[0], (center[2] + y)])
    a.append([(center[0] - x), center[2]])
    a.append([center[0], (center[2] - y)])
    a.append([(center[0] + x), center[2]])
    obj['a'] = a

    # offset对角线点 上左下右
    s = []
    s.append([float(objPro.bounds.minx),float(objOff.bounds.maxy)])
    s.append([float(objOff.bounds.minx),float(objPro.bounds.miny)])
    s.append([float(objPro.bounds.maxx),float(objOff.bounds.miny)])
    s.append([float(objOff.bounds.maxx),float(objPro.bounds.maxy)])
    obj['s'] = s

    # offset对角线长度
    ad = []
    for aa in a:
        i = a.index(aa)
        ss = s[i]
        p1 = Point(aa)
        p2 = Point(ss)
        dis = p1.distance(p2)
        ad.append(dis)
    obj['ad'] = ad
        #     l = gpd.GeoSeries(LineString([p1,p2]))
        #     l.plot(ax = ax1, color = 'red')
    
    if obj['surface'] == 'wall':
        v = []
        w = []
        vd = []
        width  = a[3][0] - a[1][0]
        for i in range(0, VIEWING_FRUSTUM_PILE - 1):
            # 每层中心
            vx = a[2][0]
            vy = a[2][1] + i * VIEWING_FRUSTUM_LINE_SPACE
            vp = Point([vx,vy])
            v.append([vx,vy])
            # 对角线点
            wx = vx + (width /2  + i * VIEWING_FRUSTUM_INVREMENT)
            wy = vy + VIEWING_FRUSTUM_LINE_SPACE / 2
            wp = Point([wx , wy])
            w.append([ wx , wy])
            # 对角线长
            vdis = vp.distance(wp)
            vd.append(vdis)
        obj['v'] = v
        obj['vd'] = vd
    
def access(obj1,obj2):
    # 1 in 2
    p = Point([obj1['translate'][0],obj1['translate'][2]])
    b = obj1['b']
    total = 0
    for a in obj2['a']:
        i = obj2['a'].index(a)
        f = max((1 - p.distance(Point(a)) / (b + obj2['ad'][i])),0)
        # if f != 0 :
        #     visualizeAccess(obj1)
        #     visualizeAccess(obj2)
        total += f
    return total

def accessibility(room):
    sum = 0
    for obj in room['objList']:
        if (obj['format'] == 'obj') & (obj['surface'] != 'ceiling'):
            objRest = [i for i in room['objList'] if i != obj]
            for r in objRest:
                if (r['format'] == 'obj') & (obj['surface'] != 'ceiling'):
                    sum += access(obj,r)
    return sum

def visualizeAccess(obj):
    objProjection = obj2Rectangle(obj)
    objPro = gpd.GeoSeries(objProjection)
    objOff = objOffset(objProjection)
    
    objOff.plot(ax = ax1, color = 'pink', alpha = 0.5)
    objPro.plot(ax = ax1, color = 'yellow', alpha = 0.5)
    s = obj['s']
    for aa in obj['a']:
        i = obj['a'].index(aa)
        ss = s[i]
        p1 = Point(aa)
        p2 = Point(ss)
        l = gpd.GeoSeries(LineString([p1,p2]))
        l.plot(ax = ax1, color = 'red')

def visibale(floorObj,wallObj):
    # floorobj in wallObj view frustum
    p = Point([floorObj['translate'][0],floorObj['translate'][2]])
    b = floorObj['b']
    total = 0
    for v in wallObj['v']:
        i = wallObj['v'].index(v)
        f = max((1 - p.distance(Point(v)) / (b + wallObj['vd'][i])),0)
        # if f != 0 :
        #     visualizeAccess(floorObj)
        #     visualizeAccess(wallObj)
        total += f
    return total

def visibility(room):
    sum = 0
    for obj in room['objList']:
        if (obj['format'] == 'obj') & (obj['surface'] == 'wall'):
            objRest = [i for i in room['objList'] if i != obj]
            for r in objRest:
                if (r['format'] == 'obj') & (obj['surface'] != 'ceiling'):
                    sum += visibale(r, obj)
    return sum
    
def initStoryFromJson(obj,story):
    name = obj['modelId']
    interval = visiableDis(obj)
    intervalMin = interval[0]
    intervalMax = interval[1]
    polygon = obj2Rectangle(obj)
    storyPointList = []
    for storyContent in obj['storyContents']:
        storyIndex = storyContent['storyIndex']
        sp = storyPoint(name,storyIndex,intervalMin,intervalMax,polygon)
        story.append(sp)
    return storyPointList

def storyObjList(room,story,other):
    for obj in room['objList']:
        if('type' in obj.keys() and obj['type'] == 'storypoint'):
            initStoryFromJson(obj,story)
        elif('bbox' in obj.keys()):
            other.append(obj2Rectangle(obj))
    sorted(story, key=lambda x: x.storyIndex)

def lineRectOverlap(sp1, sp2, obj):
    centroid1 = sp1.centroid
    centroid2 = sp2.centroid
    line = LineString([[centroid1.x,centroid1.y],[centroid2.x,centroid2.y]])
    lineGeo = gpd.GeoSeries(line)
    objGeo = gpd.GeoSeries(obj)
    return lineGeo.overlaps(objGeo)

def barrier(story,other):
    totalScore = 0
    for storyPoint in story:
        x = story.index(storyPoint)
        if((x+1) < len(story)):
            storyPointNext = story[x+1]
            for obj in other:
                totalScore += lineRectOverlap(storyPoint.polygon, storyPointNext.polygon, obj)
    if(len(story)): 
        return float(totalScore / len(story))
    else:
        return 0

def disControl(d,m,M,a):
    if(d < m):
        return pow(d/m, a)
    elif(m <= d <= M):
        return 1
    else:
        return pow(M/d, a)

def storyPointDetectable(story):
    totalScore = 0
    for storyPoint in story:
        x = story.index(storyPoint)
        if((x+1) < len(story)):
            storyPointNext = story[x+1]
            point1 = storyPoint.polygon.centroid
            point2 = storyPointNext.polygon.centroid
            d = point1.distance(point2)
            totalScore += disControl(d,storyPoint.intervalMin,storyPoint.intervalMax,2)
    if(len(story)): 
        return float(totalScore / len(story))
    else:
        return 0

def pairwise(mainObj, attackedObj):
    d_o = abs(mainObj['rotate'][1] - attackedObj['rotate'][1])
    d_p = Point(mainObj['translate']).distance(attackedObj['translate'])

def costFunction(sceneJson):
    # wallInRooms = getAllWallsInRoom(sceneJson)
    total = 0.0
    for room in sceneJson['rooms']:
        for obj in room['objList']:
            objExpandAd(obj)
    
    for room in sceneJson['rooms']:
        # i = sceneJson['rooms'].index(room)
        # walls = wallInRooms[i]
        # story = []
        # other = []
        # storyObjList(room,story,other)
        
        
        total += visibility(room) + accessibility(room)
        # total = total + connectivityNum(room,walls) + storyPointDetectable(story) + barrier(story,other)
    # plt.show()
    print(total)
    return total

allObjWallRelation = []
allObjPairwise = []

def addObjWallRelation(dataLine):
    data = {}
    data['modelId'] = dataLine['mainObjId']
    data['nearestDistance'] = dataLine['wall'][0]['nearestDistance']
    data['nearestOrient0'] = dataLine['wall'][0]['nearestOrient0']
    allObjWallRelation.append(data)

def addObjPairwise(dataLine):
    data = {}
    data['modelId'] = dataLine['mainObjId']
    data['attachedObjId'] = dataLine['gtrans'][0]['attachedObjId']
    data['relativeTrans'] = [dataLine['gtrans'][0]['objPosX'], dataLine['gtrans'][0]['objPosY'], dataLine['gtrans'][0]['objPosZ']]
    data['relativeRot'] = dataLine['gtrans'][0]['objOriY']
    allObjPairwise.append(data)

def prior(room):
    areaShape = room['roomShapeBbox']
    areaShape.append(areaShape[0])
    areaShape = np.array(areaShape)
    areaOrient = []
    areaLineString = []
    for i in range(0, len(areaShape) - 1):
        areaLineString.append(LineString([areaShape[i + 1],areaShape[i]]))
        l = areaShape[i] - areaShape[i + 1]
        w = np.linalg.norm(l)
        lnr = l / w
        o = -math.acos(lnr[0])
        areaOrient.append(o)

    for obj in room['objList']:
        if obj['format'] != 'instancedMesh':
            modelId = obj['modelId']
            areaDis = []
            objPoint = Point([obj['translate'][0],obj['translate'][2]])
            for l in areaLineString:
                areaDis.append(objPoint.distance(l))
            minDis = min(areaDis)
            i = areaDis.index(minDis)
            minOrei = areaOrient[i]
            for obj2 in allObjWallRelation:
                if modelId == obj2['modelId']:
                    dertaMinDis = abs(obj2['nearestDistance'] - minDis)
                    dertaOrient = abs(obj2['nearestOrient0'] - minOrei)

    
if __name__ == "__main__":
    with open('./stories/test.json') as f:
        sceneJson = json.load(f)
    costFunction(sceneJson)
    # fig, ax1 = plt.subplots()
    # for room in sceneJson['rooms']:
    # #     for obj in room['objList']:
    #         # prior(obj, room)
    #     for obj in room['objList']:
    #         objExpandAd(obj)
    
    # for room in sceneJson['rooms']:
    #     print(visibility(room))

    # plt.show()

    # fd = open("../object-spatial-relation-dataset.txt", 'r')
    # LINES = fd.readlines()

    # data = []
    # loadData(data, LINES)
    
    # for i in data:
    #     if i['relationName'] == ' story wall':
    #         addObjWallRelation(i)
            
    #     elif i['relationName'] == ' story pairwise':
    #         addObjPairwise(i)
    # print(allObjWallRelation)
    # fd.close()
    
    
    # fig, ax1 = plt.subplots()
    # for room in sceneJson['rooms']:
        # story = []
        # other = []
        # storyObjList(room,story,other)
        # connectivityNum(room)
        # storyPointDetectable(story)
        # barrier(story,other)
        # visibility(room)
    # plt.savefig("test/Geometry.jpg")
    # plt.show()