import geopandas as gpd
import shapely
from shapely.geometry import Point,Polygon, MultiPolygon, LineString
import matplotlib.pyplot as plt
import json
import math

OFFSET = 0.2
MAX_VISIBLE_AREA = 3
MIN_VISIBLE_AREA = 0.5

with open('test/0e3f92e0-8f04-4643-a737-23603f438e68-r4.json') as f:
    sceneJson = json.load(f)

def obj2Polygon(obj):
    x = obj['orient'] / math.pi * 180 / 90
    isClose = math.isclose(x,0,rel_tol= 1e-14) or math.isclose(x,1,rel_tol= 1e-14) or math.isclose(x,-1,rel_tol= 1e-14) or math.isclose(x,2,rel_tol= 1e-14) or math.isclose(x,-2,rel_tol= 1e-14)
    if(isClose):
        return Polygon([
        [obj['bbox']['min'][0],obj['bbox']['min'][2]],
        [obj['bbox']['min'][0],obj['bbox']['max'][2]],
        [obj['bbox']['max'][0],obj['bbox']['max'][2]],
        [obj['bbox']['max'][0],obj['bbox']['min'][2]]
    ])
    else:
        return shapely.affinity.rotate(Polygon([
            [obj['bbox']['min'][0],obj['bbox']['min'][2]],
            [obj['bbox']['min'][0],obj['bbox']['max'][2]],
            [obj['bbox']['max'][0],obj['bbox']['max'][2]],
            [obj['bbox']['max'][0],obj['bbox']['min'][2]]
        ]), -obj['orient'], use_radians=True)

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

def connectivityNum(room):
    if('roomShape' in room.keys()):
        roomPolygon = wall2Polygon(room)
        roomOffsetGeo = wallOffset(roomPolygon)
        allOffsetGeo = roomOffsetGeo

        roomGeo = gpd.GeoSeries(roomPolygon)

        # visualize
        roomGeo.plot(ax = ax1, color = 'green')
        roomOffsetGeo.plot(ax = ax1, color = 'white')
        roomGeo.boundary.plot(ax = ax1, color = 'slategrey')
        # visualize

        for obj in room['objList']:
            if('bbox' in obj.keys()):
                objPolygon = obj2Polygon(obj)
                objOffsetGeo = objOffset(objPolygon)
                allOffsetGeo = allOffsetGeo.union(objOffsetGeo,align = True)
                objGeo = gpd.GeoSeries(objPolygon)
                # visualize
                objOffsetGeo.plot(ax = ax1, color = 'pink')
                objGeo.plot(ax = ax1, color = 'blue')
                # visualize
        rest = roomGeo.difference(allOffsetGeo,align=True)
        j  = rest.to_json()
        y = json.loads(j)
        features = y['features']
        for feature in features:
            coordinates = feature['geometry']['coordinates']
            
        co = list(coordinates)
        connectionPart = len(co)
        return(connectionPart)

def visiableDis(obj):
    interval = []
    length = obj['bbox']['max'][0] - obj['bbox']['min'][0]
    width = obj['bbox']['max'][1] - obj['bbox']['min'][1]
    hight = obj['bbox']['max'][2] - obj['bbox']['min'][2]
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
    
        
def initStoryFromJson(obj,story):
    name = obj['modelId']
    interval = visiableDis(obj)
    intervalMin = interval[0]
    intervalMax = interval[1]
    polygon = obj2Polygon(obj)
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
            other.append(obj2Polygon(obj))
    sorted(story, key=lambda x: x.storyIndex)

def lineRectOverlap(sp1, sp2, obj):
    centroid1 = sp1.centroid
    centroid2 = sp2.centroid
    line = LineString([[centroid1.x,centroid1.y],[centroid2.x,centroid2.y]])
    lineGeo = gpd.GeoSeries(line)
    objGeo = gpd.GeoSeries(obj)
    # visualize
    lineGeo.plot(ax = ax1, color = 'red')
    # visualize
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
        return totalScore / len(story)
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
        return totalScore / len(story)
    else:
        return 0

if __name__ == "__main__":
    fig, ax1 = plt.subplots()
    for room in sceneJson['rooms']:
        story = []
        other = []
        storyObjList(room,story,other)
        connectivityNum(room)
        storyPointDetectable(story)
        barrier(story,other)
    plt.savefig("test/0e3f92e0-8f04-4643-a737-23603f438e68-r3-Geometry.jpg")
    plt.show()