import json
from pattern import *
from params import *
from shelfmodels import *

sys.path.append('E:/3DScenePlatformDev')
os.chdir('../../')
import pathTracing as pt
os.chdir('layoutmethods/trafficflow/')

TARGET_NUMBER = SET_NUMBER
HEIGHT_RATIO = 0.76
CANVAS_WIDTH = 1000

origin = 'result'
id = "10000"


def transformSingle(patternList: list, wallPatternList: list, space: TwoDimSpace, xlow: float, xhigh: float,
                    zlow: float, zhigh: float, xlen: float, zlen: float, name: str):
    modelChoices = []

    # set basic contents
    out = {}
    out['origin'] = origin
    out['id'] = id
    out['islod'] = True
    out['bbox'] = {"min": [xlow, 0, zlow], "max": [xhigh, 3, zhigh]}
    out['up'] = [0, 1, 0]
    out['front'] = [0, 0, 1]

    # configure the room
    room = {}
    room['id'] = id + '_0'
    room['modelId'] = "Bathroom-6473"
    room['roomTypes'] = ["Bathroom"]
    room['bbox'] = {"min": [xlow, 0, zlow], "max": [xhigh, 3, zhigh]}
    room['origin'] = origin
    room['roomId'] = 0

    room['roomShape'] = [[(float)(point[0]), (float)(point[1])] for point in space.pointList]
    room['roomNorm'] = []
    for k in range(len(space.pointList)):
        n = norm(rot(space.pointList[(k + 1) % len(space.pointList)] - space.pointList[k], pi / 2))
        room['roomNorm'].append([(float)(n[0]), (float)(n[1])])
    room['roomOrient'] = [
        pi / 2 - atan2(room['roomNorm'][k][1], room['roomNorm'][k][0]) for k in range(len(room['roomNorm']))
    ]
    room['roomShapeBBox'] = {"max": [xhigh, zhigh], "min": [xlow, zlow]}
    shelfs = []
    objList = []
    key = 0
    for pattern in patternList:
        if pattern.type == EMPTY:
            modelChoices.append(None)
            continue
        groups = [[] for k in range(100)]
        for shelf in pattern.shelfs:
            groups[shelf.group].append(shelf)
        groupCount = 0
        for group in groups:
            if len(group) > 0:
                groupCount += 1
        modelGroup = None
        if groupCount <= 5:
            modelGroup = lessChoices[random.randint(0, len(lessChoices) - 1)]
        else:
            modelGroup = moreChoices[random.randint(0, len(moreChoices) - 1)]
        modelChoices.append(modelGroup)
        modelGroupLen = len(modelGroup)
        random.shuffle(modelGroup)
        for k in range(len(groups)):
            if len(groups[k]) > 0:
                for shelf in groups[k]:
                    shelf.model = modelGroup[k % modelGroupLen].id
                    shelfs.append(shelf)

    for wpattern in wallPatternList:
        modelGroup = modelChoices[wpattern.follow]
        modelGroupLen = len(modelGroup)
        random.shuffle(modelGroup)
        for shelf in wpattern.shelfs:
            shelf.model = modelGroup[k % modelGroupLen].id
            shelfs.append(shelf)

    for shelf in shelfs:
        width, length = 0.0, 0.0
        xtrans, ztrans = 0.0, 0.0
        model = allModels[shelf.model]
        obj = {}
        obj['modelId'] = model.name
        obj['roomId'] = 0
        if shelf.towards == X_POS:
            width = shelf.xl
            length = shelf.yl
            obj['orient'] = pi / 2
        elif shelf.towards == Y_POS:
            width = shelf.yl
            length = shelf.xl
            obj['orient'] = 0
        elif shelf.towards == X_NEG:
            width = shelf.xl
            length = shelf.yl
            obj['orient'] = -pi / 2
        elif shelf.towards == Y_NEG:
            width = shelf.yl
            length = shelf.xl
            obj['orient'] = pi
        else:
            length = shelf.xl
            width = shelf.yl
            obj['orient'] = -shelf.rotate + pi / 2

        obj['rotate'] = [0, obj['orient'], 0]
        obj['scale'] = [length / model.length, length / model.length, width / model.width]
        xtrans = -cos(obj['orient']) * model.xcenter * obj['scale'][0] - sin(
            obj['orient']) * model.zcenter * obj['scale'][2]
        ztrans = sin(obj['orient']) * model.xcenter * obj['scale'][0] - cos(
            obj['orient']) * model.zcenter * obj['scale'][2]
        key += 1
        obj['key'] = (str)(key)
        obj['translate'] = [shelf.x + xtrans, 0, shelf.y + ztrans]
        objList.append(obj)

    # entrance and exit doors
    entrance = space.entranceNorm * door.width / 2 + space.entrancePoint
    ent = {}
    ent['modelId'] = door.name
    ent['roomId'] = 0
    ent['scale'] = [ROAD_WIDTH / door.length, 0.8, 1]
    ent['orient'] = -atan2(space.entranceNorm[1], space.entranceNorm[0]) + pi / 2
    ent['rotate'] = [0, ent['orient'], 0]
    ent['key'] = 'entrance'
    ent['translate'] = [entrance[0], 0, entrance[1]]
    exit = space.exitNorm * door.width / 2 + space.exitPoint
    ex = {}
    ex['modelId'] = door.name
    ex['roomId'] = 0
    ex['scale'] = [ROAD_WIDTH / door.length, 0.8, 1]
    ex['orient'] = -atan2(space.exitNorm[1], space.exitNorm[0]) + pi / 2
    ex['rotate'] = [0, ex['orient'], 0]
    ex['key'] = 'exit'
    ex['translate'] = [exit[0], 0, exit[1]]
    objList.append(ent)
    objList.append(ex)

    # entrance and exit holes
    entHole = {}
    entHole['modelId'] = 'noUse'
    entHole['roomId'] = 0
    entHole['scale'] = [1, 1, 1]
    entHole['orient'] = 0
    entHole['rotate'] = [0, 0, 0]
    entHole['key'] = 'entranceHole'
    entHole['translate'] = [0, 0, 0]
    entHole['bbox'] = {
        "min": [space.entrancePoint[0] - ROAD_WIDTH / 2, 0, space.entrancePoint[1] - ROAD_WIDTH / 2],
        "max": [space.entrancePoint[0] + ROAD_WIDTH / 2, 2, space.entrancePoint[1] + ROAD_WIDTH / 2]
    }
    entHole['coarseSemantic'] = 'Door'
    exHole = {}
    exHole['modelId'] = 'noUse'
    exHole['roomId'] = 0
    exHole['scale'] = [1, 1, 1]
    exHole['orient'] = 0
    exHole['rotate'] = [0, 0, 0]
    exHole['key'] = 'exitHole'
    exHole['translate'] = [0, 0, 0]
    exHole['bbox'] = {
        "min": [space.exitPoint[0] - ROAD_WIDTH / 2, 0, space.exitPoint[1] - ROAD_WIDTH / 2],
        "max": [space.exitPoint[0] + ROAD_WIDTH / 2, 2, space.exitPoint[1] + ROAD_WIDTH / 2]
    }
    exHole['coarseSemantic'] = 'Door'
    objList.append(entHole)
    objList.append(exHole)

    room['objList'] = objList
    room['blockList'] = []
    rooms = [room]
    out['rooms'] = rooms

    # configure the cameras
    camera = {}
    camera['fov'] = 75
    camera['focalLength'] = 35
    camera['rotate'] = [-pi / 2, 0, 0]
    camera['up'] = [0, 0, -1]
    camera['roomId'] = 0
    camera['target'] = [(xlow + xhigh) / 2, 0, (zlow + zhigh) / 2]
    camHeight = min(xlen, zlen) * HEIGHT_RATIO
    camera['origin'] = [(xlow + xhigh) / 2, camHeight, (zlow + zhigh) / 2]
    out['PerspectiveCamera'] = camera
    orthCamera = {}
    orthCamera['x'] = (max(xlen, zlen) + 0.8) / 2
    orthCamera['y'] = orthCamera['x']
    out["OrthCamera"] = orthCamera
    # configure the canvas
    canvas = {'width': CANVAS_WIDTH, 'height': (int)(CANVAS_WIDTH / xlen * zlen)}
    out['canvas'] = canvas

    # dump to file
    outf = open(name + '.json', 'w')
    json.dump(out, outf)
    outf.close()
    return out


def transformLog(setNum: int, index: int):
    random.seed()
    for i in range(len(allModels)):
        allModels[i].id = i

    round = 1000
    scenes = []
    while True:
        if os.path.exists('log_models/' + (str)(setNum) + '_' + (str)(index) + '_' + (str)(round) + '.npy'):
            model = np.load('log_models/' + (str)(setNum) + '_' + (str)(index) + '_' + (str)(round) + '.npy',
                            allow_pickle=True).tolist()
            space = TwoDimSpace(model[0][0], model[0][1], model[0][2], model[0][3], model[0][4])
            context = model[1]
            xlow = space.boundbox.bounds[0]
            xhigh = space.boundbox.bounds[2]
            zlow = space.boundbox.bounds[1]
            zhigh = space.boundbox.bounds[3]
            xlen = xhigh - xlow
            zlen = zhigh - zlow
            bestList = context[3]
            bestWallList = context[11]
            name = 'log_scenes/' + (str)(setNum) + '_' + (str)(index) + '_' + (str)(round)
            scenes.append(transformSingle(bestList, bestWallList, space, xlow, xhigh, zlow, zhigh, xlen, zlen, name))
        else:
            break
        round += 1000
    os.chdir('../../')
    print('log pt start')
    for i in range(len(scenes)):
        round = i * 1000 + 1000
        pt.SAVECONFIG = False
        pt.USENEWWALL = True
        pt.cameraType = 'perspective'
        pt.pathTracing(
            scenes[i], 64,
            'layoutmethods/trafficflow/log_images/' + (str)(setNum) + '_' + (str)(index) + '_' + (str)(round) + '.png')
        pt.cameraType = 'orthographic'
        pt.pathTracing(
            scenes[i], 64, 'layoutmethods/trafficflow/log_images/' + (str)(setNum) + '_' + (str)(index) + '_' +
            (str)(round) + '_orth.png')
        print('log pt ' + (str)(round))
    os.chdir('layoutmethods/trafficflow/')


def transform(trial: int):
    random.seed()

    for i in range(len(allModels)):
        allModels[i].id = i
    if os.path.exists('models/full' + (str)(TARGET_NUMBER) + '_' + (str)(trial) + '.npy'):
        model = np.load('models/full' + (str)(TARGET_NUMBER) + '_' + (str)(trial) + '.npy', allow_pickle=True).tolist()
        space = TwoDimSpace(model[0][0], model[0][1], model[0][2], model[0][3], model[0][4])
        context = model[
            1]  # net[0],bestNet[1],patternList[2],bestList[3],totalcost[4],bestCost[5],totalCostList[6],nowIterRound[7],bestIterRound[8],ctionProbabilities[9],sinceLastBest[10],wallPatterns[11]
        xlow = space.boundbox.bounds[0]
        xhigh = space.boundbox.bounds[2]
        zlow = space.boundbox.bounds[1]
        zhigh = space.boundbox.bounds[3]
        xlen = xhigh - xlow
        zlen = zhigh - zlow
        scenes = []
        for i in range(TARGET_NUMBER):
            bestList = context[i][3]
            bestWallList = context[i][11]
            name = 'scenes/' + origin + (str)(trial * TARGET_NUMBER + i)
            scenes.append(transformSingle(bestList, bestWallList, space, xlow, xhigh, zlow, zhigh, xlen, zlen, name))

        os.chdir('../../')
        print('pt start')
        for i in range(TARGET_NUMBER):
            pt.SAVECONFIG = False
            pt.USENEWWALL = True
            pt.cameraType = 'perspective'
            pt.pathTracing(scenes[i], 4,
                           'layoutmethods/trafficflow/images/images_' + (str)(trial * TARGET_NUMBER + i) + '.png')
            pt.cameraType = 'orthographic'
            pt.pathTracing(scenes[i], 4,
                           'layoutmethods/trafficflow/images/images_' + (str)(trial * TARGET_NUMBER + i) + '_orth.png')
            print('pt ' + (str)(trial * TARGET_NUMBER + i))
        os.chdir('layoutmethods/trafficflow/')
    else:
        print("no model available")


if __name__ == '__main__':
    inp=input('choice:')
    if 'log' in inp:
        setNum=input('setNum:')
        index=input('index:')
        transformLog(setNum,index)
    else:
        trial=input('trial:')
        transform(trial)
