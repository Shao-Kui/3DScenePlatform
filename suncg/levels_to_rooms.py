import os
import json
import numpy as np
from projection2d import process as p2d

anchor = 0
for housename in os.listdir('./level_doorfix'):
    print(housename)
    anchor += 1
    levelnames = os.listdir(f'./level_doorfix/{housename}')
    for levelname in levelnames:
        with open(f'./level_doorfix/{housename}/{levelname}') as f:
            level = json.load(f)
        # split levels into sets of rooms while preserve structure of levels; 
        for room in level['rooms']:
            room_of_level = level.copy()
            room_of_level['rooms'] = [room.copy()]
            room_of_level['rooms'][0]['roomId'] = 0
            for o in room_of_level['rooms'][0]['objList']:
                if o is None:
                    room_of_level.remove(o)
                o['roomId'] = 0
                if 'coarseSemantic' in o: 
                    if o['coarseSemantic'] in ['stairs', 'column']:
                        room_of_level['rooms'][0]['objList'].remove(o)
            roomTypes = room['roomTypes']
            if len(roomTypes) == 0:
                roomtype = 'unknown'
            else:
                roomTypes.sort()
                roomtype = '_'.join(roomTypes)
            if not os.path.exists(f'./rooms/{roomtype}'):
                os.makedirs(f'./rooms/{roomtype}')
            # re-calculate the room bounding box; 
            try:
                room_meta = p2d('.', 'room/{}/{}f.obj'.format(room['origin'], room['modelId']))[:, 0:2]
            except Exception as e:
                print(e)
                continue
            room_of_level['bbox']['min'][0] = np.min(room_meta[:, 0])
            room_of_level['bbox']['max'][0] = np.max(room_meta[:, 0])
            room_of_level['bbox']['min'][2] = np.min(room_meta[:, 1])
            room_of_level['bbox']['max'][2] = np.max(room_meta[:, 1])
            roomname = f'{room["origin"]}-{level["id"]}-{room["roomId"]}'
            with open(f'./rooms/{roomtype}/{roomname}.json', 'w') as f:
                json.dump(room_of_level, f)