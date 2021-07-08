
def autoViewFromPatterns(room):
    pcam = {}
    roomType = room['roomTypes'][0]
    for obj in room['objList']:
        obj['roomType'] = roomType
    room['objList'].sort(key=keyObjectKeyFunction, reverse=True)
    if len(room['objList']) == 0:
        return None
    theDom = room['objList'][0]
    # find a random pattern of object room['objList'][0];
    try:
        with open(f"./latentspace/pos-orient-5/{theDom['modelId']}.json") as f:
            pattern = random.choice(random.choice(list(json.load(f).items()))[1])
            print(pattern)
    except Exception as e:
        print(e)
        return None
    # rotate & scale the prior; 
    pattern['translate'] = sk.transform_a_point(np.array(pattern['translate']), theDom['translate'], theDom['orient'], theDom['scale'])
    # camTranslate = np.array(theDom['translate']) + pattern['translate']
    camTranslate = pattern['translate'].copy()
    pcam["origin"] = (camTranslate.copy()).tolist()
    # calculate the vector toward the 'target'; 
    theta = theDom['orient'] + pattern['orient']
    camTarget = camTranslate.copy()
    camTarget[0] += np.sin(theta)
    camTarget[2] += np.cos(theta)
    pcam["target"] = (camTarget.copy()).tolist()
    # calculate the 'up' vector via the normal of plane;    
    pcam["up"] = calCamUpVec(camTranslate, camTarget).tolist()
    # get the object AABB bounding box; 
    subAABB = sk.load_AABB(pattern['sub'])
    tall = subAABB['max'][1] * pattern['scale'][1]
    pcam["origin"][1] = tall
    pcam["target"][1] = tall
    return pcam

def autoViewTwoPointPerspective(room, scene):
    fov = scene['PerspectiveCamera']['fov']
    # change the fov/2 to Radian. 
    theta = (np.pi * fov / 180) / 2
    floorMeta = p2d('.', '/dataset/room/{}/{}f.obj'.format(room['origin'], room['modelId']))
    floorPoly = Polygon(floorMeta[:, 0:2])
    H = sk.getWallHeight(f"./dataset/room/{room['origin']}/{room['modelId']}w.obj")
    pcams = []
    for wallIndex in range(floorMeta.shape[0]):
        pcam = {}
        # find the longest diagonal w.r.t 'floorMeta[wallIndex][0:2]'. 
        wallDiagIndex = findTheLongestDiagonal(wallIndex, floorMeta, floorPoly)
        # wallDiagIndex = longestDiagonalSimple(wallIndex, floorMeta, floorPoly)
        targetWallWindoorArea = 0.
        for r in scene['rooms']:
            for obj in r['objList']:
                targetWallWindoorArea += calWindoorArea(obj, floorMeta[(wallDiagIndex+floorMeta.shape[0]-1)%floorMeta.shape[0]][0:2], floorMeta[wallDiagIndex][0:2])
        for r in scene['rooms']:
            for obj in r['objList']:
                targetWallWindoorArea += calWindoorArea(obj, floorMeta[wallDiagIndex][0:2], floorMeta[(wallDiagIndex+1)%floorMeta.shape[0]][0:2])
        # calculate the direction of the diagonal. 
        """
        v = (floorMeta[wallDiagIndex][0:2] - floorMeta[wallIndex][0:2]).tolist()
        v.insert(1, 0.)
        v /= np.linalg.norm(np.array(v), ord=2)
        k = np.cross(v, np.array([0, 1, 0]))
        k /= np.linalg.norm(k, ord=2)
        direction = v * np.cos(-theta) + np.cross(k, v) * np.sin(-theta)
        direction /= np.linalg.norm(direction)
        """
        v = (floorMeta[wallDiagIndex][0:2] - floorMeta[wallIndex][0:2]).tolist()
        v.insert(1, 0.)
        v /= np.linalg.norm(np.array(v), ord=2)
        probe = np.array([floorMeta[wallIndex][0], H / 2, floorMeta[wallIndex][1]])
        direction = groundShifting(probe, floorMeta, floorPoly, np.array(v), theta, H)
        pcam['probe'] = probe
        pcam['direction'] = direction
        pcam['viewLength'] = np.linalg.norm(v, ord=2)
        pcam['targetWallWindoorArea'] = targetWallWindoorArea
        pcam['theta'] = theta
        pcam['roomId'] = room['roomId']
        pcam['wallIndex'] = wallIndex
        pcam['type'] = 'twoPointPerspective'
        numSeenObjs(room, pcam, probe, direction, floorMeta, theta)
        tarWindoorArea2021(pcam, scene, floorMeta, theta)
        pcams.append(pcam)
    # pcams.sort(key=probabilityTPP, reverse=True)
    return pcams

def autoViewRodrigues(room, fov):
    # change the fov/2 to Radian. 
    theta = (np.pi * fov / 180) / 2
    # the the floor meta. 
    floorMeta = p2d('.', '/dataset/room/{}/{}f.obj'.format(room['origin'], room['modelId']))
    wallIndex = np.random.choice(floorMeta.shape[0])
    wallIndexNext = ( wallIndex + 1 ) % floorMeta.shape[0]
    middlePoint = (floorMeta[wallIndex][0:2] + floorMeta[wallIndexNext][0:2]) / 2
    middlePoint += floorMeta[wallIndex][2:4] * 0.005
    # the height of the wall. 
    H = sk.getWallHeight(f"./dataset/room/{room['origin']}/{room['modelId']}w.obj")
    origin = middlePoint.tolist()
    origin.insert(1, H)
    # the normal of the wall. 
    normal = floorMeta[wallIndex][2:4].tolist()
    normal.insert(1, 0.)
    # apply Rogrigues Formula. 
    v = np.array(normal)
    v /= np.linalg.norm(v, ord=2)
    k = (floorMeta[wallIndex][0:2] - floorMeta[wallIndexNext][0:2]).tolist()
    k.insert(1, 0.)
    k = np.array(k)
    k /= np.linalg.norm(k, ord=2)
    target = v * np.cos(-theta) + np.cross(k, v) * np.sin(-theta)
    # construct the perspective camera. 
    pcam = {}
    pcam["origin"] = origin
    pcam["target"] = (np.array(origin) + target).tolist()
    pcam["up"] = calCamUpVec(np.array(pcam["origin"]), np.array(pcam["target"])).tolist()
    return pcam

def autoViewTwoPoint(room):
    floorMeta = p2d('.', '/dataset/room/{}/{}f.obj'.format(room['origin'], room['modelId']))
    # note that the result anchor point is 'walllIndexNext'. 
    wallIndex = np.random.choice(floorMeta.shape[0])
    wallIndexNext = ( wallIndex + 1 ) % floorMeta.shape[0]
    direction = floorMeta[wallIndex][2:4] + floorMeta[wallIndexNext][2:4]
    direction /= np.linalg.norm(direction, ord=2)
    origin = (floorMeta[wallIndexNext][0:2] + direction * 0.05).tolist()
    origin.insert(1, CAMHEI)
    target = (floorMeta[wallIndexNext][0:2] + direction * (0.05+TARDIS)).tolist()
    target.insert(1, CAMHEI)
    pcam = {}
    pcam["origin"] = origin
    pcam["target"] = target
    pcam["up"] = calCamUpVec(np.array(pcam["origin"]), np.array(pcam["target"])).tolist()
    return pcam