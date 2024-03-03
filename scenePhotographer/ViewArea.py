import numpy as np
import shapely
import json
from shapely.ops import unary_union

def PointInsidePolygon(point, polygon):
    return polygon.contains(point) or polygon.boundary.contains(point)
def PointProjectToXoZ(ori, p):
    # only for ViewArea
    p, ori = np.array(p), np.array(ori)
    p[2] = min(p[2], ori[2] - 1e-5)
    k = ori[2] / (ori[2] - p[2])
    return p * (1 - k) + ori * k
def PolygonProjectToXoZ(ori, polygon):
    # only for ViewArea
    ori = np.array(ori)
    return [PointProjectToXoZ(ori, np.array(p)) for p in polygon]
def Normalize(v):
    # only for ViewArea
    v = np.array(v)
    len = np.linalg.norm(v)
    if len < 1e-9:
        return np.zeros_like(v)
    return v / len

def ViewArea(room, scene, pcam):
    """
        return the area (projected in the vertical direction) of all visible floor of a given room
    """

    # red axis : x
    # green axis : y
    # blue axis : z
    print(pcam.get('origin'))
    ori = np.array(pcam.get('origin'))
    
    roomShape = room['roomShape']
    room_shape_polygon = shapely.Polygon(room['roomShape'])
    if not PointInsidePolygon(shapely.Point(ori[0], ori[2]), room_shape_polygon):
        return 0

    direction = np.array([0., 0., 1.])
    if 'target' in pcam:
        direction = np.array(pcam['target']) - ori
    elif 'direction' in pcam:
        direction = np.array(pcam['direction'])
    
    up = np.array(pcam.get('up'))
    up, direction = Normalize(up), Normalize(direction)
    horizontal = np.cross(direction, up)

    obj_block_bboxes = []
    
    # objects as block
    for obj in room.get('objList', []):
        if 'bbox' in obj:
            obj_block_bboxes.append(obj['bbox'])
        
    projected_block_area = []
    for bbox in obj_block_bboxes:
        # caculate 6 surface
        x1, y1, z1 = bbox['min'][0], bbox['min'][1], bbox['min'][2]
        x2, y2, z2 = bbox['max'][0], bbox['max'][1], bbox['max'][2]

        s1 = PolygonProjectToXoZ(ori, [(x1, y1, z1), (x1, y2, z1), (x1, y2, z2), (x1, y1, z2)])
        s2 = PolygonProjectToXoZ(ori, [(x2, y1, z1), (x2, y2, z1), (x2, y2, z2), (x2, y1, z2)])
        s3 = PolygonProjectToXoZ(ori, [(x1, y1, z1), (x2, y1, z1), (x2, y1, z2), (x1, y1, z2)])
        s4 = PolygonProjectToXoZ(ori, [(x1, y2, z1), (x2, y2, z1), (x2, y2, z2), (x1, y2, z2)])
        s5 = PolygonProjectToXoZ(ori, [(x1, y1, z1), (x2, y1, z1), (x2, y2, z1), (x1, y2, z1)])
        s6 = PolygonProjectToXoZ(ori, [(x1, y1, z2), (x2, y1, z2), (x2, y2, z2), (x1, y2, z2)])

        projected_block_area.append(shapely.Polygon(s1))
        projected_block_area.append(shapely.Polygon(s2))
        projected_block_area.append(shapely.Polygon(s3))
        projected_block_area.append(shapely.Polygon(s4))
        projected_block_area.append(shapely.Polygon(s5))
        projected_block_area.append(shapely.Polygon(s6))

    # walls as block
    wall_height = scene.get('coarseWallHeight', 2.6)
    for id, p2 in enumerate(roomShape):
        p1 = roomShape[-1] if id == 0 else roomShape[id - 1]
        x1, z1 = p1[0], p1[1]
        x2, z2 = p2[0], p2[1]
        s = PolygonProjectToXoZ(ori, [(x1, z1, 0), (x2, z2, 0), (x2, z2, wall_height), (x1, z1, wall_height)])
        projected_block_area.append(shapely.Polygon(s))

    # get the 4 corners of visible points on xOz without any block

    angle_h = pcam['theta']
    angle_w = np.arctan(np.tan(angle_h / 2) * 16 / 9) * 2

    insight_corners = []
    for i, j in [(-1, -1), (1, -1), (1, 1), (-1, 1)]:
        pt = PointProjectToXoZ(ori, ori + direction + up * i * np.tan(angle_h / 2) + horizontal * j * np.tan(angle_w / 2))
        insight_corners.append(pt)
    insight_area = shapely.Polygon(insight_corners)

    res = room_shape_polygon.intersection(insight_area).area
    if len(projected_block_area):
        all_block_union = unary_union(projected_block_area).intersection(insight_area)
        res -= all_block_union.area

    return res

if __name__ == '__main__':
    room = 'C:\\Users\\evan\\Desktop\\zhx_workspace\\SceneViewer\\test_20230821\\rooms1.json'
    pcam = 'D:\\zhx_workspace\\3DScenePlatformDev\\latentspace\\autoview\\0ec97239-1e30-4334-8d60-e21fb2f91f8f\\sfy-rooms1-0-ClusterOrthorhombic-21.json'
    with open(room) as f:
        scene = json.load(f)
    with open(pcam) as f:
        pcam = json.load(f)
    print(ViewArea(scene['rooms'][0],scene,pcam))