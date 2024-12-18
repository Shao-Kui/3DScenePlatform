from pickle import TRUE
from re import L
from xmlrpc.client import NOT_WELLFORMED_ERROR
from jinja2 import Environment, FileSystemLoader
import json
import os
import numpy as np
from datetime import datetime
from subprocess import check_output
import shutil
import sys
import getopt
import numpy as np
import sk
import uuid
from itertools import combinations
from shapely.geometry.polygon import Polygon, Point
from layoutmethods.projection2d import processGeo as p2d
# the following code is for backend-rendering. 
# from celery import Celery
# app = Celery('tasks', backend='rpc://', broker='pyamqp://')

sysROOT = 'F:/3DIndoorScenePlatform/dataset/PathTracing'
ROOT = './dataset/PathTracing'
file_loader = FileSystemLoader('./')
env = Environment(loader=file_loader)
template = env.get_template('./assets/pathTracingTemplate.xml')
cameraType="perspective" # spherical
emitter="sky"
num_samples = 64
r_dir = 'batch1'
wallMaterial = True
REMOVELAMP = False
SAVECONFIG = False
NOWALL = False
USENEWWALL = False
CAMGEN = False
TRAV = False
AREACAM = False
WALLHEIGHT = 2.6

def autoPerspectiveCamera(scenejson):
    PerspectiveCamera = {}
    roomShape = []
    if AREACAM:
        for room in scenejson['rooms']:
            if 'areaShape' in room:
                roomShape += room['areaShape']
        roomShape = np.array(roomShape)
        wh = 0
    else:
        if 'roomShape' not in scenejson['rooms'][0]:
            room_meta = p2d('.', f'/dataset/room/{scenejson["origin"]}/{scenejson["rooms"][0]["modelId"]}f.obj')
            roomShape = room_meta[:, 0:2]
        else:
            roomShape = np.array(scenejson['rooms'][0]['roomShape'])
            for i in range(1, len(scenejson['rooms'])):
                room = scenejson['rooms'][i]
                roomShape = np.vstack((roomShape, room['roomShape']))
        wh = WALLHEIGHT
    lx = (np.max(roomShape[:, 0]) + np.min(roomShape[:, 0])) / 2
    lz = (np.max(roomShape[:, 1]) + np.min(roomShape[:, 1])) / 2
    camfovratio = np.tan((sk.DEFAULT_FOV/2) * np.pi / 180) 
    lx_length = (np.max(roomShape[:, 0]) - np.min(roomShape[:, 0]))
    lz_length = (np.max(roomShape[:, 1]) - np.min(roomShape[:, 1]))
    if lz_length > lx_length:
        PerspectiveCamera['up'] = [1,0,0]
        camHeight = wh + (np.max(roomShape[:, 0])/2 - np.min(roomShape[:, 0])/2) / camfovratio
        imgwidthratio = lz_length / lx_length
    else:
        PerspectiveCamera['up'] = [0,0,1]
        camHeight = wh + (np.max(roomShape[:, 1])/2 - np.min(roomShape[:, 1])/2) / camfovratio
        imgwidthratio = lx_length / lz_length
    PerspectiveCamera['origin'] = [lx, camHeight, lz]
    PerspectiveCamera['target'] = [lx, 0, lz]
    PerspectiveCamera['rotate'] = [0,0,0]
    PerspectiveCamera['fov'] = sk.DEFAULT_FOV
    PerspectiveCamera['focalLength'] = 35
    scenejson['PerspectiveCamera'] = PerspectiveCamera
    scenejson['canvas'] = {
        'height': 1080,
        'width': int(1080 * imgwidthratio)
    }
    return PerspectiveCamera

# @app.task
# def pathTracingPara(scenejson, sampleCount=64, dst=None):
#     return pathTracing(scenejson=scenejson, sampleCount=sampleCount, dst=dst)
def wallSplitByWindoors(wallPlane, block):
    # try clipping the wall plane into 4 parts;
    res = []
    dots = np.dot(wallPlane['norm'], np.identity(3))
    ignoreAxis = np.argmax(np.abs(dots))
    if ignoreAxis != 1:
        if block['bbox']['max'][2 - ignoreAxis] > wallPlane['bbox']['max'][2 - ignoreAxis] or block['bbox']['max'][2 - ignoreAxis] < wallPlane['bbox']['min'][2 - ignoreAxis]:
            return [wallPlane]     
        if block['bbox']['min'][2 - ignoreAxis] > wallPlane['bbox']['max'][2 - ignoreAxis] or block['bbox']['min'][2 - ignoreAxis] < wallPlane['bbox']['min'][2 - ignoreAxis]:
            return [wallPlane]  
    for clippingAxis in [0, 1, 2]:
        if clippingAxis == ignoreAxis:
            continue
        dmax = wallPlane['bbox']['max'][clippingAxis] - wallPlane['bbox']['min'][clippingAxis]
        d1 = wallPlane['bbox']['max'][clippingAxis] - block['bbox']['max'][clippingAxis]
        d2 = block['bbox']['min'][clippingAxis] - wallPlane['bbox']['min'][clippingAxis]
        if d1 > 0. and d1 < dmax:
            if clippingAxis == 1:
                bbox = {
                    'max': np.array([0, wallPlane['bbox']['max'][1], 0]),
                    'min': np.array([0, block['bbox']['max'][1], 0])
                }
                bbox['max'][2 - ignoreAxis] = block['bbox']['max'][2 - ignoreAxis]
                bbox['min'][2 - ignoreAxis] = block['bbox']['min'][2 - ignoreAxis]
                derive = 'top'
            else:
                bbox = {
                    'max': np.array([0, wallPlane['bbox']['max'][1], 0]),
                    'min': np.array([0, wallPlane['bbox']['min'][1], 0])
                }
                bbox['max'][clippingAxis] = wallPlane['bbox']['max'][clippingAxis]
                bbox['min'][clippingAxis] = block['bbox']['max'][clippingAxis]
                derive = 'right'
            bbox['max'][ignoreAxis] = wallPlane['bbox']['max'][ignoreAxis]
            bbox['min'][ignoreAxis] = wallPlane['bbox']['min'][ignoreAxis]
            ma = np.array([bbox['max'][0], bbox['max'][2]])
            mi = np.array([bbox['min'][0], bbox['min'][2]])
            if np.linalg.norm(ma - wallPlane['pre']) < np.linalg.norm(mi - wallPlane['pre']):
                pre = ma
                next = mi
            else:
                pre = mi
                next = ma
            res.append({
                'pre': pre,
                'next': next,
                'tl': np.array([pre[0], bbox['max'][1], pre[1]]), # top-left
                'bbox': bbox,
                'norm': wallPlane['norm'].copy(),
                'orient': wallPlane['orient'],
                'derive': derive
            })
        if d2 > 0. and d2 < dmax:
            if clippingAxis == 1:
                bbox = {
                    'max': np.array([0, block['bbox']['min'][1], 0]),
                    'min': np.array([0, wallPlane['bbox']['min'][1], 0])
                }
                bbox['max'][2 - ignoreAxis] = block['bbox']['max'][2 - ignoreAxis]
                bbox['min'][2 - ignoreAxis] = block['bbox']['min'][2 - ignoreAxis]
                derive = 'bottom'
            else:
                bbox = {
                    'max': np.array([0, wallPlane['bbox']['max'][1], 0]),
                    'min': np.array([0, wallPlane['bbox']['min'][1], 0])
                }
                bbox['max'][clippingAxis] = block['bbox']['min'][clippingAxis]
                bbox['min'][clippingAxis] = wallPlane['bbox']['min'][clippingAxis]
                derive = 'left'
            bbox['max'][ignoreAxis] = wallPlane['bbox']['max'][ignoreAxis]
            bbox['min'][ignoreAxis] = wallPlane['bbox']['min'][ignoreAxis]
            ma = np.array([bbox['max'][0], bbox['max'][2]])
            mi = np.array([bbox['min'][0], bbox['min'][2]])
            if np.linalg.norm(ma - wallPlane['pre']) < np.linalg.norm(mi - wallPlane['pre']):
                pre = ma
                next = mi
            else:
                pre = mi
                next = ma
            res.append({
                'pre': pre,
                'next': next,
                'tl': np.array([pre[0], bbox['max'][1], pre[1]]), # top-left
                'bbox': bbox,
                'norm': wallPlane['norm'].copy(),
                'orient': wallPlane['orient'],
                'derive': derive
            })
    if len(res) == 0:
        return [wallPlane]
    else:
        return res    

def isCubeIntersectsWithPlane(wallPlane, cubelinePairs):
    for cubelinePair in cubelinePairs:
        if sk.isSegIntersectsWithPlane(wallPlane['tl'], wallPlane['norm'], cubelinePair[0], cubelinePair[1]):
            return True
    return False

def pathTracing(scenejson, sampleCount=64, dst=None):
    now = datetime.now()
    dt_string = now.strftime("%Y-%m-%d %H-%M-%S")
    casename = ROOT + f'/{scenejson["origin"]}-{dt_string}-{uuid.uuid1()}'
    if 'PerspectiveCamera' not in scenejson or CAMGEN:
        autoPerspectiveCamera(scenejson)
    # if cameraType == 'orthographic':
    #     points = []
    #     for room in scenejson['rooms']:
    #         points += room['roomShape']
    #     v = np.array(points)
    #     l = np.min(v[:, 0])
    #     r = np.max(v[:, 0])
    #     u = np.min(v[:, 1])
    #     d = np.max(v[:, 1])
    #     orthViewLen = r - l
    #     scenejson["PerspectiveCamera"]['origin'] = [(r + l)/2, 50, (d + u)/2]
    #     scenejson["PerspectiveCamera"]['target'] = [(r + l)/2, 0,  (d + u)/2]
    #     scenejson["PerspectiveCamera"]['up'] = [0, 0, 1]
    #     scenejson['OrthCamera'] = {'x': orthViewLen / 2, 'y': orthViewLen / 2}
    #     scenejson["canvas"] = {'width': int((r - l) * 100), 'height': int((d - u) * 100)}
    if 'canvas' not in scenejson:
        scenejson['canvas'] = {}
        scenejson['canvas']['width'] = "1920"
        scenejson['canvas']['height'] = "1080"
    if 'focalLength' not in scenejson['PerspectiveCamera']:
        scenejson['PerspectiveCamera']['focalLength'] = 35
    scenejson['PerspectiveCamera']['focalLength'] = f"{scenejson['PerspectiveCamera']['focalLength']}mm"
    # re-organize scene json into Mitsuba .xml file: 
    scenejson["pcam"] = {}
    scenejson["pcam"]["origin"] = ', '.join([str(i) for i in scenejson["PerspectiveCamera"]["origin"]])
    scenejson["pcam"]["target"] = ', '.join([str(i) for i in scenejson["PerspectiveCamera"]["target"]])
    scenejson["pcam"]["up"] = ', '.join([str(i) for i in scenejson["PerspectiveCamera"]["up"]])
    scenejson['renderobjlist'] = []
    scenejson['renderroomobjlist'] = []
    scenejson['newroomobjlist'] = []
    scenejson['rendercubeobjlist'] = []
    blocks = []
    for room in scenejson['rooms']:
        if 'objList' not in room:
            room['objList'] = []
        if 'areaType' not in room:
            room['areaType'] = 'unknown'
        if 'id' in scenejson and os.path.exists(f'./dataset/area/{scenejson["id"]}/{room["modelId"]}.obj'):
            scenejson['renderroomobjlist'].append({
                'modelPath': f'../../area/{scenejson["id"]}/{room["modelId"]}.obj',
                'translate': [0,0,0],
                'rotate': [0,0,0],
                'scale': [1,1,1],
                'areaType': room['areaType']
            })
        for obj in room['objList']:
            if 'coarseSemantic' in obj:
                if obj['coarseSemantic'] in ['Door', 'Window', 'door', 'window']:
                    blocks.append(obj)
    for room in scenejson['rooms']:
        if USENEWWALL and 'roomShape' in room and not NOWALL:
            # for pre,index in zip(room['roomShape'], range(len(room['roomShape']))):
            #     next = room['roomShape'][(index+1)%len(room['roomShape'])]
            #     xScale = np.linalg.norm(np.array(next) - np.array(pre)) / 2
            #     yScale = 2
            #     pos = (np.array(next) + np.array(pre)) / 2

            #     scenejson['newroomobjlist'].append({
            #         'translate': [pos[0], yScale, pos[1]],
            #         'rotate': [0, room['roomOrient'][index], 0],
            #         'scale': [xScale,yScale,1]
            #     })
            initialWallPlanes = []
            if 'roomOrient' not in room:
                room['roomOrient'] = np.arctan2(np.array(room['roomNorm'])[:, 0], np.array(room['roomNorm'])[:, 1]).tolist()
            for pre,index in zip(room['roomShape'], range(len(room['roomShape']))):
                next = room['roomShape'][(index+1)%len(room['roomShape'])]
                initialWallPlanes.append({
                    'pre': np.array(pre), 
                    'next': np.array(next),
                    'tl': np.array([pre[0], WALLHEIGHT, pre[1]]), # top-left
                    'tr': np.array([next[0], WALLHEIGHT, next[1]]), # top-right
                    'bl': np.array([pre[0], 0., pre[1]]), # bottom-left
                    'br': np.array([next[0], 0., next[1]]), # bottom-right
                    'bbox': {
                        'max': np.array([np.max([pre[0], next[0]]), WALLHEIGHT, np.max([pre[1], next[1]])]),
                        'min': np.array([np.min([pre[0], next[0]]), 0.0, np.min([pre[1], next[1]])])
                    },
                    'norm': np.array([room['roomNorm'][index][0], 0., room['roomNorm'][index][1]]),
                    'orient': room['roomOrient'][index]
                })
            for block in blocks:
                eightPoints = np.array([
                    [block['bbox']['max'][0], block['bbox']['min'][1], block['bbox']['max'][2]],
                    [block['bbox']['min'][0], block['bbox']['min'][1], block['bbox']['max'][2]],
                    [block['bbox']['min'][0], block['bbox']['min'][1], block['bbox']['min'][2]],
                    [block['bbox']['max'][0], block['bbox']['min'][1], block['bbox']['min'][2]],
                    [block['bbox']['max'][0], block['bbox']['max'][1], block['bbox']['max'][2]],
                    [block['bbox']['min'][0], block['bbox']['max'][1], block['bbox']['max'][2]],
                    [block['bbox']['min'][0], block['bbox']['max'][1], block['bbox']['min'][2]],
                    [block['bbox']['max'][0], block['bbox']['max'][1], block['bbox']['min'][2]],
                ])
                cubelinePairs = list(combinations(eightPoints, 2))
                nextWallPlanes = []
                while len(initialWallPlanes) != 0:
                    wallPlane = initialWallPlanes.pop()
                    if isCubeIntersectsWithPlane(wallPlane, cubelinePairs):
                        nextWallPlanes += wallSplitByWindoors(wallPlane, block)
                    else:
                        nextWallPlanes.append(wallPlane)
                initialWallPlanes = nextWallPlanes
                nextWallPlanes = []
            for wallPlane in initialWallPlanes:
                pos = (wallPlane['bbox']['max'] + wallPlane['bbox']['min'])/2
                xScale = np.linalg.norm(wallPlane['next'] - wallPlane['pre']) / 2
                scenejson['newroomobjlist'].append({
                    'translate': pos.tolist(),
                    'rotate': [0, wallPlane['orient'], 0],
                    'scale': [
                        xScale, 
                        (wallPlane['bbox']['max'][1] - wallPlane['bbox']['min'][1])/2, 
                        1
                    ]
                })
            roomDiag = 10 * np.linalg.norm(np.max(room['roomShape'], axis=0) - np.min(room['roomShape'], axis=0))
            roomShape = room['roomShape'].copy()
            # print(room['roomId'], 'Init RoomShape: ', roomShape)
            roomShape = sk.regularizeRoomShape(roomShape)
            if len(roomShape) < 4:
                polytest = Polygon(roomShape)
                print(roomShape, polytest.area)
            i = 1
            while len(roomShape) != 0:
                roomNorm = sk.generateRoomNormals(roomShape)
                if not sk.checkClockwise(roomShape):
                    roomShape.reverse()
                    roomNorm.reverse()
                # print(roomShape)
                if len(roomShape) == 4:
                    ma = np.max(roomShape, axis=0)
                    mi = np.min(roomShape, axis=0)
                    pos = (ma + mi) / 2
                    scale = (ma - mi) / 2
                    scenejson['newroomobjlist'].append({'translate': [pos[0],0,pos[1]],'rotate': [np.pi/2, 0, 0],'scale': [scale[0],scale[1],1]})
                    break
                p0 = np.array(roomShape[i-1])
                p1 = np.array(roomShape[i])
                p2 = np.array(roomShape[i+1])
                n0 = np.array(roomNorm[i-1]) * roomDiag
                n1 = np.array(roomNorm[i]) * roomDiag
                n2 = np.array(roomNorm[i+1]) * roomDiag
                if not sk.isTwoLineSegIntersect(p0, p0 + n0, p2, p2 + n1):
                    i += 1
                    continue
                # if other walls block this intersection, we should also continue to the next iteration;
                # _mindis = np.Inf
                # for _i in range(len(roomShape)):
                #     __p = sk.twoInfLineIntersection(roomShape[_i], roomShape[(_i+1)%len(roomShape)], p2, p2 + n1)
                #     if __p is None:
                #        continue
                #     _dis = sk.pointToLineDistance(p2, roomShape[_i], roomShape[(_i+1)%len(roomShape)])
                #     if _dis < _mindis and roomShape[_i] != i:
                #         _mindis = _dis
                #         _p = __p
                #         tarI = roomShape[_i]
                # if tarI == (i-1+len(roomShape)) % len(roomShape):
                #     pstart = p0
                #     roomShape.insert(i+2, _p)
                # elif:
                #     pstart = sk.twoInfLineIntersection(p0, p1, _p, _p + n2)
                #     roomShape.insert(i, pstart)
                #     roomShape.insert(i+2, _p)
                _p = sk.twoInfLineIntersection(p0, p0 + n0, p2, p2 + n1)
                RIGHTSIGN = False
                for _index, p in zip(range(len(roomShape)), roomShape):
                    if _index in [i-1, i, i+1]:
                        continue
                    if not sk.isPointProjectedToLineSeg(p, p2, _p):
                        continue
                    value = sk.toLeftTest(p, p2, p2 + n1)
                    if value < -0.0000001:
                        # print('rightsign', p, p2, p2 + n1)
                        RIGHTSIGN = True
                        break
                if RIGHTSIGN:
                    i += 1
                    continue
                ma = np.max([p0, p1, p2, _p], axis=0)
                mi = np.min([p0, p1, p2, _p], axis=0)
                pos = (ma + mi) / 2
                scale = (ma - mi) / 2
                scenejson['newroomobjlist'].append({'translate': [pos[0],0,pos[1]],'rotate': [np.pi/2, 0, 0],'scale': [scale[0],scale[1],1]})
                if len(roomShape) == 4:
                    break
                polygon = Polygon([p0, p1, p2, _p])
                testlist = []
                # test whether the new point is overlap with an existing point;
                # pbefore = roomShape[(i-2+len(roomShape)) % len(roomShape)]
                # value0 = sk.toLeftTest(pbefore, p2, p2 + n1)
                # if value0 > -0.0000001 and value0 < 0.0000001:
                #     print(value0)
                #     testlist += [(i-2)%(len(roomShape)+1)]
                value1 = sk.toLeftTest(p2, _p, roomShape[(i+2)%len(roomShape)])
                DELETEP2 = False
                if value1 > -0.0000001 and value1 < 0.0000001:
                    DELETEP2 = True
                # p2 next;
                if np.dot(np.array(roomNorm[i+1]), n0) < 0:
                    testlist += [i+3]
                # if np.dot(np.array(roomNorm[(i-3)%len(roomShape)]), n0) < 0:
                #     print('yes')
                #     testlist += [(i-3)%(len(roomShape)+1)]
                roomShape.insert((i-1+len(roomShape)) % len(roomShape), _p)
                newroomShape = []
                testlist += [i-1, i, i+1, i+2]
                for _index, p in zip(range(len(roomShape)), roomShape):
                    _ip = (_index + len(roomShape) - 1) % len(roomShape)
                    _in = (_index + 1) % len(roomShape)
                    if polygon.covers(Point(p)):
                        if _ip in testlist and _in in testlist:
                            continue
                    if DELETEP2 and _index == i+2:
                        continue
                    newroomShape.append(p)
                roomShape = newroomShape
                if not sk.checkClockwise(roomShape):
                    roomShape.reverse()
                roomShape = sk.regularizeRoomShape(roomShape)
                i = 1
                if i+1 >= len(roomShape):
                    polytest = Polygon(roomShape)
                    print(roomShape, polytest.area)
                    break
        elif not USENEWWALL and not NOWALL:
            for cwf in ['w', 'f']:
                if os.path.exists(f'./dataset/room2021/{scenejson["origin"]}/{room["modelId"]}{cwf}.obj'):
                    scenejson['renderroomobjlist'].append({
                        'modelPath': f'../../room2021/{scenejson["origin"]}/{room["modelId"]}{cwf}.obj',
                        'translate': [0,0,0],
                        'rotate': [0,0,0],
                        'scale': [1,1,1]
                    })
        for obj in room['objList']:
            if obj['modelId'] == 'noUse':
                continue
            # if 'inDatabase' in obj:
            #     if not obj['inDatabase']:
            #         continue
            if sk.getobjCat(obj['modelId']) in ["Pendant Lamp", "Ceiling Lamp"] and REMOVELAMP:
                print('A lamp is removed. ')
                continue
            obj['modelPath'] = '../../object/{}/{}.obj'.format(obj['modelId'], obj['modelId'])
            if 'format' not in obj:
                obj['format'] = 'obj'
            if obj['format'] == 'glb':
                obj['modelPath'] = '../../../static/dataset/object/{}/{}.obj'.format(obj['modelId'], obj['startState'])
            if obj['format'] == 'sfy':
                obj['cubescale'] = [
                    (obj['bbox']['max'][0] - obj['bbox']['min'][0])/2,
                    (obj['bbox']['max'][1] - obj['bbox']['min'][1])/2,
                    (obj['bbox']['max'][2] - obj['bbox']['min'][2])/2
                ]
                obj['cubetranslate'] = [
                    (obj['bbox']['max'][0] + obj['bbox']['min'][0])/2,
                    (obj['bbox']['max'][1] + obj['bbox']['min'][1])/2,
                    (obj['bbox']['max'][2] + obj['bbox']['min'][2])/2
                ]
                scenejson['rendercubeobjlist'].append(obj)
                continue
            if os.path.exists('./dataset/object/{}/{}.obj'.format(obj['modelId'], obj['modelId'])):
                scenejson['renderobjlist'].append(obj)
                continue
            if 'startState' in obj and os.path.exists('./static/dataset/object/{}/{}.obj'.format(obj['modelId'], obj['startState'])):
                scenejson['renderobjlist'].append(obj)
                continue
    output = template.render(
        scenejson=scenejson, 
        PI=np.pi, 
        sampleCount=sampleCount, 
        cameraType=cameraType,
        wallMaterial=wallMaterial,
        emitter=emitter
    )
    if not os.path.exists(casename):
        os.makedirs(casename)
    with open(casename + '/scenejson.json', 'w') as f:
        json.dump(scenejson, f, default=sk.jsonDumpsDefault)
    with open(casename + '/renderconfig.xml', 'w') as f:
        f.write(output)
    check_output(f"mitsuba \"{casename + '/renderconfig.xml'}\"", shell=True)
    check_output(f"mtsutil tonemap -o \"{casename + '/render.png'}\" \"{casename + '/renderconfig.exr'}\" ", shell=True)
    if dst is not None:
        shutil.copy(casename + '/render.png', dst)
    if not SAVECONFIG:
        shutil.rmtree(casename)
    return casename

def batchTravDir(new_dir):
    filenames = os.listdir(f'./dataset/PathTracing/{new_dir}')
    for filename in filenames:
        pngfilename = filename.replace('.json', '.png')
        if os.path.isdir(f'./dataset/PathTracing/{new_dir}/{filename}'):
            batchTravDir(f'{new_dir}/{filename}')
        if '.json' not in filename:
            continue
        if os.path.exists(f'./dataset/PathTracing/{new_dir}/{pngfilename}'):
            continue
        print('start do :' + f'{new_dir}/{filename}')
        with open(f'./dataset/PathTracing/{new_dir}/{filename}') as f:
            try:
                casename = pathTracing(json.load(f), sampleCount=num_samples, dst=f'./dataset/PathTracing/{new_dir}/{pngfilename}')
            except Exception as e:
                print(e)
                continue

def batch():
    filenames = os.listdir(f'./dataset/PathTracing/{r_dir}')
    for filename in filenames:
        pngfilename = filename.replace('.json', '.png')
        if os.path.isdir(f'./dataset/PathTracing/{r_dir}/{filename}') and TRAV:
            batchTravDir(f'{r_dir}/{filename}')
        if '.json' not in filename:
            continue
        print('start do :' + filename)
        with open(f'./dataset/PathTracing/{r_dir}/{filename}') as f:
            try:
                casename = pathTracing(json.load(f), sampleCount=num_samples, dst=f'./dataset/PathTracing/{r_dir}/{pngfilename}')
            except Exception as e:
                print(e)
                continue
            # copy rendered imgs to the rdir: 
            # shutil.copy(casename + '/render.png', f'./dataset/PathTracing/{r_dir}/{pngfilename}')

# roomtypelist = ['MasterBedroom', 'LivingDinningRoom', 'KidsRoom', 'SecondBedroom', 'LivingRoom', 'DinningRoom']
roomtypelist = ['MasterBedroom']
mage4methods = ['ours', 'planit', '3dfront', 'gba']
# mage4methods = ['3dfront']
iddc = [0]
def mage4gen():
    for rt in roomtypelist:
        for i in iddc:
            pcam = None
            for m in mage4methods:
                print(rt, i, m)
                jsonpath = f'H:/D3UserStudy/static/mage/{rt}/{i}/{m}.json'
                if not os.path.exists(jsonpath):
                    continue
                with open(jsonpath) as f:
                    scenejson = json.load(f)
                if pcam is None:
                    # pcam = autoPerspectiveCamera(scenejson)
                    pcam = scenejson['PerspectiveCamera']
                else:
                    scenejson['PerspectiveCamera'] = pcam
                # if m != 'gba':
                #     continue
                try:
                    rendercasename = pathTracing(scenejson, sampleCount=num_samples)
                except Exception as e:
                    print(e)
                    continue
                pngfilename = jsonpath.replace('.json', '.png')
                shutil.copy(rendercasename + '/render.png', pngfilename)

def autoCameraSpher_allRoom():
    filenames = os.listdir(f'./dataset/PathTracing/{r_dir}')
    for filename in filenames:
        if '.json' not in filename:
            continue
        print('start do :' + filename)
        with open(f'./dataset/PathTracing/{r_dir}/{filename}') as f:
            sj = json.load(f)
            if 'canvas' not in sj:
                sj['canvas'] = {}
                sj['canvas']['width'] = "1309"
                sj['canvas']['width'] = "809"
            for rm in sj['rooms']:
                PerspectiveCamera = {}
                PerspectiveCamera['origin'] = (np.array(rm['bbox']['min']) + np.array(rm['bbox']['max'])) / 2
                PerspectiveCamera['target'] = PerspectiveCamera['origin'] + np.array([0,0,1]) # this is the directional vector used by Doc. Yu He. 
                PerspectiveCamera['up'] = np.array([0,1,0])
                PerspectiveCamera['origin'] = PerspectiveCamera['origin'].tolist()
                PerspectiveCamera['target'] = PerspectiveCamera['target'].tolist()
                PerspectiveCamera['up'] = PerspectiveCamera['up'].tolist()
                PerspectiveCamera['rotate'] = [0,0,0]
                sj['PerspectiveCamera'] = PerspectiveCamera
                casename = pathTracing(sj, sampleCount=num_samples)
                pngfilename = filename.replace('.json', '.png')
                shutil.copy(casename + '/render.png', f'./dataset/PathTracing/{r_dir}/{rm["roomId"]}-{pngfilename}')

defaultTast = batch
if __name__ == "__main__":
    # batch(sys.argv[1], sampleCount=int(sys.argv[2]))
    # with open('./dataset/PathTracing/4cc6dba0-a26e-42cb-a964-06cb78d60bae-l2685-dl (8).json') as f:
    #     pathTracing(json.load(f), sampleCount=4)

    # s: number of samples, the default is 64; 
    # d: the directory of scene-jsons; 
    try:
        opts, args = getopt.getopt(sys.argv[1:], "s:d:hc:", ["task=","wm=", "newwall=", "nowall=", "emitter=", "camgen=", "trav=", "areacam="])
    except getopt.GetoptError:
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('python pathTracing.py -d batch1 -s 256')
            sys.exit()
        elif opt in ("-s"):
            num_samples = int(arg)
        elif opt in ("-d"):
            r_dir = arg
        elif opt in ("-c"):
            cameraType = arg
        elif opt in ("--wm"):
            wallMaterial = bool(int(arg))
        elif opt in ("--newwall"):
            USENEWWALL = bool(int(arg))
        elif opt in ("--camgen"):
            CAMGEN = bool(int(arg))
        elif opt in ("--trav"):
            TRAV = bool(int(arg))
        elif opt in ("--nowall"):
            NOWALL = bool(int(arg))
        elif opt in ("--emitter"):
            emitter = arg
        elif opt in ("--areacam"):
            AREACAM = bool(int(arg))
        elif opt in ("--task"):
            # defaultTast = getattr(__name__, arg)
            defaultTast = globals()[arg]
    defaultTast()
