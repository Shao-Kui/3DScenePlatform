import matplotlib.pyplot as plt
import numpy as np
import triangle as tr
from shapely.geometry import *
from shapely.affinity import *
from shapely.ops import *

# Define the outer polygon
outer_vertices = [[0, 0], [2, 0], [2, 1], [1, 1], [1, 2], [2, 2], [2, 3], [1, 3], [1, 4], [3, 4], [3, 3], [4, 3],
                  [4, 2], [3, 2], [3, 1], [4, 1], [4, -1], [0, -1]]

# Define the segments of the outer polygon
segments = [(i, (i + 1) % len(outer_vertices)) for i in range(len(outer_vertices))]

# Define the inner polygon (hole)
inner_vertices = [[(2.5, -0.5), (3.5, -0.5), (3.5, 0.5), (2.5, 0.5)],
                  [(1.5, 1.25), (2.5, 1.25), (2.5, 2.5), (2.25, 2.5), (2.25, 1.75), (1.5, 1.75)]]

poly = Polygon(outer_vertices)

# Define the segments of the inner polygon (hole)
# inner_segments = []
for inner in inner_vertices:
    base = len(segments)
    segments += [(i + base, (i + 1) % len(inner) + base) for i in range(len(inner))]
    poly = poly.difference(Polygon(inner))

print(segments)

vertices = np.concatenate([outer_vertices] + inner_vertices)

res = tr.triangulate({
    'vertices': np.concatenate([outer_vertices] + inner_vertices),
    'segments': segments,
}, 'p')

actual_triangles = []
for triangle in res['triangles']:
    p1, p2, p3 = vertices[triangle[0]], vertices[triangle[1]], vertices[triangle[2]]
    center = ((p1[0] + p2[0] + p3[0]) / 3, (p1[1] + p2[1] + p3[1]) / 3)
    if Point(center).within(poly):
        actual_triangles.append(triangle)

A = dict(vertices=vertices, segments=segments)
B = dict(vertices=vertices, triangles=actual_triangles)

tr.compare(plt, A, B)

plt.savefig('tri.png')

# print(triangles['triangles'])
# print(triangles['vertices'])
