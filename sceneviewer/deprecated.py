import networkx as nx
def hamilton(scene):
    involvedRoomIds = []
    views = []
    # load existing views. 
    for fn in os.listdir(f'./latentspace/autoview/{scene["origin"]}'):
        if '.json' not in fn:
            continue
        with open(f'./latentspace/autoview/{scene["origin"]}/{fn}') as f:
            views.append(json.load(f))
    for view in views:
        view['isVisited'] = False
        if view['roomId'] not in involvedRoomIds:
            involvedRoomIds.append(view['roomId'])
    print(involvedRoomIds)
    res = []
    # deciding connections of a floorplan. 
    G = nx.Graph()
    for room in scene['rooms']:
        room['isVisited'] = False
        floorMeta = p2d('.', '/dataset/room/{}/{}f.obj'.format(room['origin'], room['modelId']))
        try:
            H = sk.getWallHeight(f"./dataset/room/{room['origin']}/{room['modelId']}w.obj")
        except:
            continue
        for door in room['objList']:
            if 'coarseSemantic' not in door:
                continue
            if door['coarseSemantic'] not in ['Door', 'door']:
                continue
            if len(door['roomIds']) < 2:
                continue
            # if door['roomIds'][0] not in involvedRoomIds and door['roomIds'][1] not in involvedRoomIds:
            #     continue
            x = (door['bbox']['min'][0] + door['bbox']['max'][0]) / 2
            z = (door['bbox']['min'][2] + door['bbox']['max'][2]) / 2
            DIS = np.Inf
            for wallIndex in range(floorMeta.shape[0]):
                wallIndexNext = ( wallIndex + 1 ) % floorMeta.shape[0]
                dis = sk.pointToLineDistance(np.array([x, z]), floorMeta[wallIndex, 0:2], floorMeta[wallIndexNext, 0:2])
                if dis < DIS:
                    DIS = dis
                    direction = np.array([floorMeta[wallIndex, 2], 0, floorMeta[wallIndex, 3]])
            translate = np.array([x, H/2, z])
            G.add_edge(door['roomIds'][0], door['roomIds'][1], translate=translate, direction=direction, directionToRoom=room['roomId'])
    pre = nx.dfs_predecessors(G)
    suc = nx.dfs_successors(G)
    print(pre, suc)
    # decide the s and t which are the start point and end point respectively. 
    # ndproom = list(nx.dfs_successors(G).keys())[0]
    # ndproom = views[0]['roomId']
    ndproom = involvedRoomIds[0]
    roomOrder = []
    while ndproom != -1:
        roomOrder.append(ndproom)
        scene['rooms'][ndproom]['isVisited'] = True
        ndproom = hamiltonNextRoom(ndproom, pre, suc, scene)
    for room in scene['rooms']:
        room['isVisited'] = False
    print(roomOrder)
    def subPath(s):
        if s == len(roomOrder) - 1:
            return (True, s)
        state = False
        start = roomOrder[s]
        s += 1
        while s < len(roomOrder) and roomOrder[s] != start: 
            if roomOrder[s] in involvedRoomIds and not scene['rooms'][roomOrder[s]]['isVisited']:
                state = True
            s += 1
        return (state, s)
    i = 0
    while i < len(roomOrder):
        state, s = subPath(i)
        if not state:
            roomOrder = roomOrder[0:i+1] + roomOrder[s+1:]
            i -= 1
        else:
            scene['rooms'][roomOrder[i]]['isVisited'] = True
        i += 1
    print(roomOrder)
    ndproom = roomOrder[0]
    for view in views:
        if view['roomId'] == ndproom:
            ndpNext = view
    # perform the algorithm of Angluin and Valiant. 
    for i in range(1, len(roomOrder)+1):
        while ndpNext is not None:
            ndp = ndpNext
            res.append(ndp)
            ndp['isVisited'] = True
            ndpNext = hamiltonNext(ndp, views, scene)
        if i == len(roomOrder):
            break
        lastndproom = roomOrder[i-1]
        ndproom = roomOrder[i]
        edge = G[lastndproom][ndproom]
        # if edge['direction'].dot(edge['translate'] - ndp['probe']) < 0:
        if edge['directionToRoom'] != ndproom:
            edge['direction'] = -edge['direction']
        ndpNext = {
            'roomId': ndproom,
            'probe': edge['translate'],
            'origin': edge['translate'].tolist(),
            'target': (edge['translate'] + edge['direction']).tolist(),
            'direction': edge['direction'].tolist()
        }
    """
    # for e in G.edges:
    #     if ndproom in e:
    #         edge = G[e[0]][e[1]]
    #         if ndproom != edge['directionToRoom']:
    #             edge['direction'] = -edge['direction']
    #         ndpNext = {
    #             'roomId': ndproom,
    #             'probe': edge['translate'],
    #             'origin': edge['translate'].tolist(),
    #             'target': (edge['translate'] + edge['direction']).tolist(),
    #             'direction': edge['direction'].tolist()
    #         }
    
    # perform the algorithm of Angluin and Valiant. 
    while not ndproom == -1:
        while ndpNext is not None:
            ndp = ndpNext
            res.append(ndp)
            ndp['isVisited'] = True
            ndpNext = hamiltonNext(ndp, views, scene)
        lastndproom = ndproom
        ndproom = hamiltonNextRoom(ndproom, pre, suc, scene)
        if ndproom == -1:
            break
        edge = G[lastndproom][ndproom]
        if edge['direction'].dot(edge['translate'] - ndp['probe']) < 0:
            edge['direction'] = -edge['direction']
        scene['rooms'][ndproom]['isVisited'] = True
        ndpNext = {
            'roomId': ndproom,
            'probe': edge['translate'],
            'origin': edge['translate'].tolist(),
            'target': (edge['translate'] + edge['direction']).tolist(),
            'direction': edge['direction'].tolist()
        }
    """
    with open(f'./latentspace/autoview/{scene["origin"]}/path', 'w') as f:
        json.dump(res, f, default=sk.jsonDumpsDefault)
    return res