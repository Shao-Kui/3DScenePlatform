import numpy as np
import shapely
from shapely.geometry import Polygon, box
import matplotlib.pyplot as plt


def draw(ps):
    ax = plt.gca()
    ax.invert_yaxis()
    for c in ps:
        for p in ps[c]:
            x, y = p.exterior.xy
            plt.plot(x, y, c=c)
    plt.show()
    pass


def insert_new_obj(obj: Polygon, room_polygon: Polygon, blocks):
    plist = np.array(list(room_polygon.exterior.coords))
    diff = plist[1:]    - plist[:-1]
    print(diff)



    draw({'b': [room_polygon], 'r': blocks, 'g': [obj]})

    c = room_polygon.length


room = Polygon([
    (1, 1), (1, 20), (20, 20), (20, 1)
])
obj = Polygon([
    (0, 0), (0, 5), (5, 5), (5, 0)
])
bl = [
    Polygon([(1, 1), (1, 3), (3, 3), (3, 1)]),
    Polygon([(10, 0), (10, 5), (15, 5), (15, 0)])
]

insert_new_obj(obj, room, bl)


def try_possible_layout(function_areas, room_shape, blocks):
    room = Polygon([(r[0], r[1]) for r in room_shape])

    fap = [Polygon([(f[0], f[1]) for f in fa]) for fa in function_areas]

    bs = np.array([b['windoorbb'] for b in blocks])
    bs2d = np.delete(bs, 1, axis=2)
    bp = [shapely.geometry.box(x[0][0], x[0][1], x[1][0], x[1][1]) for x in bs2d]

    draw({'b': [room], 'r': bp, 'g': fap})

    plt.show()

    pass
