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


# rotate vector p by angle ori
def rotate_numpy(p, ori):
    d = np.array([np.cos(ori), np.sin(ori)])
    return np.array([p[0] * d[0] - p[1] * d[1], p[0] * d[1] + p[1] * d[0]]).T


# Insert a rectangle inside a simple polygon(not necessarily convex), which does not intersect with any block.
# density means the sample density, which means sample density times per length unit(1 meter)
def insert_new_obj(function_area: Polygon, room_polygon: Polygon, blocks, density=1):
    olist = np.array(list(function_area.exterior.coords))
    # First, the function area(rectangle) was put on the xy plane,
    # with an edge(bottom) along x-axis and its mid-point(anchor) exactly on the origin.
    # The length of the bottom is width
    # The rectangle will rotate with the anchor fixed.
    width = np.max(olist[:, 1]) - np.min(olist[:, 1])
    anchor = np.array([(np.max(olist[:, 0]) + np.min(olist[:, 0])) / 2, np.min(olist[:, 1])])

    # Expand the room polygon a little to deal with the floating number equal problem
    room_polygon_bigger = room_polygon.buffer(1e-6)

    # vertices list of the room polygon
    rlist = np.array(list(room_polygon.exterior.coords))
    # vector list of the room polygon
    diff = rlist[1:] - rlist[:-1]
    # length of edges of the room polygon
    dis = np.linalg.norm(diff, axis=1)
    # rotation angles(x-positive equals 0) of edges of the room polygon
    rot = np.arctan2(diff[:, 1], diff[:, 0]) + np.pi / 2

    # possible_obj = []
    # all_obj = []

    # try put the polygon at different edges at a random order
    idx = np.arange(rlist.shape[0] - 1)
    np.random.shuffle(idx)

    # Find random new positions on edges for anchor.
    for i in idx:
        # Random sample. A padding of width/2 is excluded, cause function areas inside the padding will go outside
        # the room.
        sample = np.random.uniform(width / dis[i] / 2, 1 - width / dis[i] / 2, int(dis[i] * density))

        # Consider room corner first
        if sample.shape[0] > 1:
            sample[0] = width / dis[i] / 2
            sample[1] = 1 - width / dis[i] / 2
            np.random.shuffle(sample[0:2])

        # Get the real position of these random points
        sample = sample.reshape(-1, 1) * diff[i].reshape(1, 2) + rlist[i]

        # plt.scatter(sample[:, 0], sample[:, 1], s=0.1)

        # attention! Because that we use shapely to rotate the polygon, we shift to x-based coordinates.
        # Thus, the angle rotated is "ori[i]-np.pi/2" instead of "np.pi/2 - ori[i]"
        new_function_area = affinity.rotate(function_area, rot[i] - np.pi / 2, origin=(0, 0), use_radians=True)
        new_anchor = rotate_numpy(anchor, rot[i] - np.pi / 2)

        # Put the function area on these points by anchor
        for s in sample:
            nwobj = affinity.translate(new_function_area, xoff=s[0] - new_anchor[0], yoff=s[1] - new_anchor[1])
            # all_obj.append(nwobj)
            # plt.scatter(s[0],s[1])
            # draw({
            #     'b': [room_polygon_bigger],
            #     'r': blocks,
            #     'g': [nwobj]
            # })
            # return None
            if room_polygon_bigger.contains(nwobj):
                for b in blocks:
                    if b.intersects(nwobj):
                        break
                else:
                    # draw({
                    #     'b': [room_polygon_bigger],
                    #     'r': blocks,
                    #     'g': [nwobj]
                    # })

                    return nwobj, np.pi / 2 - rot[i], [s[0] - new_anchor[0], s[1] - new_anchor[1]]
                    # possible_obj.append(nwobj)

    return None


def insert_objects(function_areas, room_polygon: Polygon, blocks, windows):
    # sort the function areas in descend order so that we can arrange the biggest one first
    area_idx = np.flip(np.argsort(np.array([p[0].area for p in function_areas])))

    rotations = area_idx.tolist()
    translations = area_idx.tolist()

    for i in area_idx:
        function_area = function_areas[i]
        # draw({
        #     'b': [room_polygon],
        #     'r': [b[0] for b in blocks] + [w[0] for w in windows],
        # })
        blocks_and_windows = [x[0] for x in blocks]
        # print('function area:', function_area)

        # the height of the function area can at most cover half of the window
        for x in windows:
            # print(x)
            if (x[1] + x[2]) / 2 < function_area[2]:
                blocks_and_windows.append(x[0])
                pass

        # try most 2^n times
        try_2_pow_times = 6

        for j in range(0, try_2_pow_times):
            new_positions = insert_new_obj(function_area[0], room_polygon, blocks_and_windows, 2 ** j)
            if new_positions is not None:
                # avoid overlap with the following function areas
                blocks.append([new_positions[0], function_area[1], function_area[2]])
                # get the results
                rotations[i] = new_positions[1]
                translations[i] = new_positions[2]
                break
        else:
            # if not succeed
            print('Failed')
            rotations[i] = 0
            translations[i] = [999, 999, 999]
    draw({
        'b': [room_polygon],
        'r': [b[0] for b in blocks] + [w[0] for w in windows],
    })
    return rotations, translations


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
    room = shapely.geometry.Polygon([(p[0], p[1]) for p in room_shape])

    function_areas = [[shapely.geometry.box(x[0], x[2], x[3], x[5]), x[1], x[4]] for x in function_areas]
    # blocks:  no function can intersect with these areas
    blocks = [[shapely.geometry.box(x[0], x[2], x[3], x[5]), x[1], x[4]] for x in blocks]

    # windows function areas can intersect with these areas partly(a shelf could cover the lower part of a window)
    windows = [[shapely.geometry.box(x[0], x[2], x[3], x[5]), x[1], x[4]] for x in windows]

    re = insert_objects(function_areas, room, blocks, windows)
    if re is not None:
        return re
