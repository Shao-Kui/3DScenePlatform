import numpy as np
import triangle as tr
from shapely.geometry import *
from shapely.affinity import *
from shapely.ops import *
import os


def objectize(
    polygon,
    holes,
    texture_name,
    layer,
    dir_name,
    idx,
):
    if not os.path.exists(dir_name):
        os.mkdir(dir_name)
    segments = [(i, (i + 1) % len(polygon)) for i in range(len(polygon))]
    poly = Polygon(polygon)
    for hole in holes:
        base = len(segments)
        segments += [(i + base, (i + 1) % len(hole) + base) for i in range(len(hole))]
        poly = poly.difference(Polygon(hole))
    vertices = np.concatenate([polygon] + holes)

    res = tr.triangulate({'vertices': vertices, 'segments': segments}, 'p')
    # triangles = Delaunay(polygon).simplices
    actual_triangles = []
    for triangle in res['triangles']:
        p1, p2, p3 = vertices[triangle[0]], vertices[triangle[1]], vertices[triangle[2]]
        center = ((p1[0] + p2[0] + p3[0]) / 3, (p1[1] + p2[1] + p3[1]) / 3)
        if Point(center).within(poly):
            actual_triangles.append(triangle)

    # Write the .obj and .mtl files
    with open('{}/{}.obj'.format(dir_name, idx), 'w') as obj_file:
        obj_file.write('mtllib ./{}.mtl\n'.format(idx))
        # Write the vertices to the .obj file
        for vertex in vertices:
            obj_file.write('v {} {} {}\n'.format(vertex[0], layer * 0.01, vertex[1]))
        # Write the texture coordinates to the .obj file
        for vertex in vertices:
            obj_file.write('vt {} {}\n'.format(vertex[0], vertex[1]))
        # Write the normals to the .obj file
        for _ in range(len(vertices)):
            obj_file.write('vn 0 1 0\n')
        # Write the faces to the .obj file
        obj_file.write('usemtl {}/{}\n'.format(dir_name, idx))
        for triangle in actual_triangles:
            obj_file.write('f {}/{}/{} {}/{}/{} {}/{}/{}\n'.format(triangle[0] + 1, triangle[0] + 1, triangle[0] + 1,
                                                                   triangle[2] + 1, triangle[2] + 1, triangle[2] + 1,
                                                                   triangle[1] + 1, triangle[1] + 1, triangle[1] + 1))

    with open('{}/{}.mtl'.format(dir_name, idx), 'w') as mtl_file:
        # Write the material definition to the .mtl file
        mtl_file.write('newmtl {}/{}\n'.format(dir_name, idx))
        mtl_file.write('Ka 1.0 1.0 1.0\n')
        mtl_file.write('Kd 1.0 1.0 1.0\n')
        mtl_file.write('Ks 0.0 0.0 0.0\n')
        mtl_file.write('map_Kd ../../GeneralTexture/{}.jpg\n'.format(texture_name))


if __name__ == '__main__':
    polygon = [[0, 0], [2, 0], [2, 1], [1, 1], [1, 2], [2, 2], [2, 3], [1, 3], [1, 4], [3, 4], [3, 3], [4, 3], [4, 2],
               [3, 2], [3, 1], [4, 1], [4, -1], [0, -1]]
    holes = [[(2.5, -0.5), (3.5, -0.5), (3.5, 0.5), (2.5, 0.5)],
             [(1.5, 1.25), (2.5, 1.25), (2.5, 2.5), (2.25, 2.5), (2.25, 1.75), (1.5, 1.75)]]
    objectize(polygon, holes, 'polygon', 0)
