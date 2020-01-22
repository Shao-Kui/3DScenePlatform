import numpy as np
import shapely
from shapely import affinity
from shapely.geometry import Polygon, box
import matplotlib.pyplot as plt


def draw(ps):
    ax = plt.gca()
    ax.invert_yaxis()
    ax.set_aspect(1)
    for c in ps:
        for p in ps[c]:
            x, y = p.exterior.xy
            plt.plot(x, y, c=c)
    # plt.show()


def rotate_numpy(p, ori):
    d = np.array([np.cos(ori), np.sin(ori)])
    return np.array([p[0] * d[0] - p[1] * d[1], p[0] * d[1] + p[1] * d[0]]).T


def insert_new_obj(obj: Polygon, room_polygon: Polygon, blocks, density=1):
    olist = np.array(list(obj.exterior.coords))
    w = np.max(olist[:, 1]) - np.min(olist[:, 1])
    anchor = np.array([(np.max(olist[:, 0]) + np.min(olist[:, 0])) / 2, np.min(olist[:, 1])])

    room_polygon_bigger = room_polygon.buffer(1e-6)

    rlist = np.array(list(room_polygon.exterior.coords))
    diff = rlist[1:] - rlist[:-1]
    dis = np.linalg.norm(diff, axis=1)
    ori = np.arctan2(diff[:, 1], diff[:, 0]) + np.pi / 2

    # possible_obj = []
    # all_obj = []
    idx = np.arange(rlist.shape[0] - 1)
    np.random.shuffle(idx)

    for i in idx:
        sample = np.random.uniform(w / dis[i] / 2, 1 - w / dis[i] / 2, int(dis[i] * density))

        if sample.shape[0] > 1:
            sample[0] = w / dis[i] / 2
            sample[1] = 1 - w / dis[i] / 2
            np.random.shuffle(sample[0:2])
        sample = sample.reshape(-1, 1) * diff[i].reshape(1, 2) + rlist[i]
        # plt.scatter(sample[:, 0], sample[:, 1], s=0.1)
        # attention! Because that we use shapely to rotate the polygon, we shift to x-based coordinates.
        # Thus, the angle rotated is "ori[i]-np.pi/2" instead of "np.pi/2 - ori[i]"
        nobj = affinity.rotate(obj, ori[i] - np.pi / 2, origin=(0, 0), use_radians=True)
        nanchor = rotate_numpy(anchor, ori[i] - np.pi / 2)
        for s in sample:
            nwobj = affinity.translate(nobj, xoff=s[0] - nanchor[0], yoff=s[1] - nanchor[1])
            # all_obj.append(nwobj)
            # plt.scatter(s[0],s[1])
            # draw({
            #     'b': [room_polygon_bigger],
            #     'r': blocks,
            #     'g': [nwobj]
            # })
            # return None
            if room_polygon_bigger.contains(nwobj):
                ok = True
                for b in blocks:
                    if b.intersects(nwobj):
                        ok = False
                        break
                if ok:
                    # draw({
                    #     'b': [room_polygon_bigger],
                    #     'r': blocks,
                    #     'g': [nwobj]
                    # })
                    return nwobj, np.pi / 2 - ori[i], [s[0] - nanchor[0], s[1] - nanchor[1]]
                    # possible_obj.append(nwobj)

    return None


def insert_objects(objs, room_polygon: Polygon, blocks, windows):
    area_idx = np.flip(np.argsort(np.array([p[0].area for p in objs])))

    ori = area_idx.tolist()
    tra = area_idx.tolist()
    for i in area_idx:
        o = objs[i]
        # draw({
        #     'b': [room_polygon],
        #     'r': [b[0] for b in blocks] + [w[0] for w in windows],
        # })
        b = [x[0] for x in blocks]
        print('obj', o)

        for x in windows:
            print(x)
            if (x[1] + x[2]) / 2 < o[2]:
                b.append(x[0])
                pass
        cnt = 0

        while cnt <= 5:
            no = insert_new_obj(o[0], room_polygon, b, 2 ** cnt)
            if no is not None:
                blocks.append([no[0], o[1], o[2]])
                ori[i] = no[1]
                tra[i] = no[2]
                break
            cnt += 1
        if cnt == 6:
            print('Failed')
            ori[i] = 0
            tra[i] = [0, 0, 0]
    draw({
        'b': [room_polygon],
        'r': [b[0] for b in blocks] + [w[0] for w in windows],
    })
    return ori, tra


# room = shapely.geometry.box(1, 1, 20, 20)
# obj = [
#     shapely.geometry.box(0, 0, 3, 3),
#     shapely.geometry.box(0, 0, 8, 8),
#     shapely.geometry.box(0, 0, 4, 10),
#     shapely.geometry.box(0, 0, 4, 6),
#     shapely.geometry.box(0, 0, 4, 6),
# ]
# bl = [
#     shapely.geometry.box(2, 3, 5, 6),
#     shapely.geometry.box(10, 10, 14, 14)
# ]


# print(insert_objects(obj, room, bl))


def try_possible_layout(function_areas, room_shape, blocks, windows):
    room = shapely.geometry.Polygon([(p[0],p[1]) for p in room_shape])

    fa = [[shapely.geometry.box(x[0], x[2], x[3], x[5]), x[1], x[4]] for x in function_areas]
    bs = [[shapely.geometry.box(x[0], x[2], x[3], x[5]), x[1], x[4]] for x in blocks]
    ws = [[shapely.geometry.box(x[0], x[2], x[3], x[5]), x[1], x[4]] for x in windows]

    re = insert_objects(fa, room, bs, ws)
    if re is not None:
        return re
