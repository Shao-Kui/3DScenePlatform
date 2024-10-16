import os
import numpy as np
import json
from shapely.geometry import *
from shapely.affinity import *
from shapely.ops import *
import trimesh
from math import *

EPS = 1e-2


def get_data():
    with open('dataset.json', 'r') as dataset_json:
        with open('object/validlist.txt', 'r') as valid_list_txt:
            valid_list = [line.strip() for line in valid_list_txt.readlines()]
            dataset = json.load(dataset_json)
            for name in os.listdir('object'):
                if os.path.isdir('object/' + name) and name in valid_list:
                    print(name)
                    names = name.split('2')
                    state_count = len(names)
                    states = ['origin']
                    for na in names:
                        if os.path.exists('object/{}/{}.obj'.format(name, na)):
                            states.append(na)

                    obj = {}
                    obj['data'] = []
                    for state in states:
                        path = 'object/{}/{}.obj'.format(name, state)
                        mesh = trimesh.load(path, force='mesh')

                        vs, fs = mesh.vertices, mesh.faces

                        polygons = []

                        for f in fs:
                            verts = [vs[f[0]], vs[f[1]], vs[f[2]]]
                            verts = [(verts[0], verts[2]) for verts in verts]
                            polygons.append(Polygon(verts))

                        poly = unary_union(polygons)
                        if isinstance(poly, MultiPolygon):
                            poly = poly.convex_hull
                        points = poly.exterior.coords
                        res = [points[0], points[1]]

                        for i in range(2, len(points)):
                            last_ang = atan2(res[-1][1] - res[-2][1], res[-1][0] - res[-2][0])
                            ang = atan2(points[i][1] - res[-1][1], points[i][0] - res[-1][0])
                            if abs(last_ang - ang) < EPS:
                                res[-1] = points[i]
                            else:
                                res.append(points[i])

                        data = {}
                        data['name'] = state
                        data['poly'] = res
                        # data['attribute'] = [0, 1]
                        data['forward'] = 0
                        data['priors'] = []

                        for data_obj in dataset:
                            if data_obj['mainObjId'] == name and data_obj['state'][0]['currentState'] == state:
                                prior = {}
                                prior['gtrans'] = []
                                prior['wall'] = []
                                prior['window'] = []
                                prior['door'] = []
                                if 'gtrans' in data_obj:
                                    for relation in data_obj['gtrans']:
                                        if 'currentState' in relation:
                                            prior['gtrans'].append(relation)
                                if 'wall' in data_obj:
                                    prior['wall'] += data_obj['wall']
                                if 'window' in data_obj:
                                    prior['window'] += data_obj['window']
                                if 'door' in data_obj:
                                    prior['door'] += data_obj['door']
                                data['priors'].append(prior)

                        obj['data'].append(data)

                    obj['relation'] = [[-2 for i in range(state_count)] for j in range(state_count)]
                    for i in range(state_count):
                        obj['relation'][i][i] = 0

                    with open('object/{}_data.json'.format(name), 'w') as out:
                        json.dump(obj, out)


def rmdir(path):
    if os.path.exists(path):
        os.system('rm -r \"{}\"'.format(path))


def clean():
    for name in os.listdir('object'):
        if os.path.isdir('object/{}'.format(name)):
            for render_dir in os.listdir('object/{}'.format(name)):
                if os.path.isdir('object/{}/{}'.format(name, render_dir)):
                    rmdir('object/{}/{}'.format(name, render_dir))


if __name__ == '__main__':
    # get_data()
    # clean()
    pass
