import matplotlib
from random_poly import generate_polygon

matplotlib.use("agg")
import matplotlib.pyplot as plt
import numpy as np
from math import *
from tqdm import tqdm
import networkx as nx
import random
from copy import deepcopy
from typing import List
from shapely.geometry import *
from shapely.affinity import *
from shapely.ops import *
import json
from sklearn.cluster import KMeans
import itertools
from multiprocessing import Pool
from objectize import objectize
import os

os.environ["OMP_NUM_THREADS"] = "1"

VISUALIZE = True
GEN_NUM = 10
SPLIT = 25
PROCESS_COUNT = 10

WALLHEIGHT = 2.6
DEFAULT_FOV = 75

EPS = 1e-3
COMBINE_THRES = 0.1
SUB_ROAD_WIDTH = 1.5
MAIN_ROAD_WIDTH = 2.5

MAX_CIRCUIT_TRY = 100
POPULATION_SIZE = 100
CROSS_RATE = 0.8
MUTATION_RATE = 0.5
MAX_GENERATION = 1000

MODEL_LIMIT = 1500

SEMICIRCLE_PARTS = 20
CURVE_PARTS = 10

# site_bound = [(0, 0), (50, 0), (50, 50), (25, 50), (25, 30), (0, 30)]
# site_bound = [(0, 0), (40, 0), (40, 30), (60, 30), (60, 0), (90, 0), (90, 60), (20, 60), (20, 30), (0, 30)]
# site_bound = [(0, 0), (80, 0), (80, 50), (30, 50), (30, 30), (50, 30), (50, 20), (30, 20), (30, 29), (0, 29)]
# site_bound = generate_polygon(center=(40, 40), avg_radius=40, irregularity=0.5, spikiness=0.2, num_vertices=16)
# site_bound = [(int(x[0]), int(x[1])) for x in site_bound]
### circle
# site_bound = []
# for i in range(360):
#     site_bound.append((40 + 40 * cos(i * pi / 180), 40 + 40 * sin(i * pi / 180)))
# site_bound = [(0, 0), (64, 0), (64, 64), (0, 64)]
### two semi-circles + tunnel
# for i in range(37):
#     site_bound.append((30 + 30 * cos(i * pi / 36+pi/2), 30 + 30 * sin(i * pi / 36+pi/2)))
# site_bound.extend([(30, 10),(50,10)])
# for i in range(37):
#     site_bound.append((50 + 30 * cos(i * pi / 36-pi/2), 30 + 30 * sin(i * pi / 36-pi/2)))
# site_bound.extend([(50, 50),(30,50)])
### V-shape
site_bound = [(0, 50), (35, 0), (70, 50), (50, 50), (35, 30), (20, 50)]
site_poly = Polygon(site_bound)
site_area = site_poly.area
site_xl, site_yl, site_xh, site_yh = site_poly.bounds
site_xl, site_xh, site_yl, site_yh = int(site_xl), int(site_xh), int(site_yl), int(site_yh)
site_width, site_height = site_xh - site_xl, site_yh - site_yl


def vec(*args):
    if len(args) == 1:
        return np.array(args[0], "float32")
    return np.array(args, "float32")


def remove_edge(graph: nx.Graph, edge: tuple):
    if edge in graph.edges:
        graph.remove_edge(edge[0], edge[1])
    elif (edge[1], edge[0]) in graph.edges:
        graph.remove_edge(edge[1], edge[0])
    else:
        assert False


def norm(vector: np.ndarray):
    """return the normalized vector"""
    if np.linalg.norm(vector) > 0:
        return vector / np.linalg.norm(vector)
    return vector


def rot(point: np.ndarray, angle: float):
    """rotate a vector counter-clockwise, angle is in radian"""
    return np.array(
        [point[0] * cos(angle) + point[1] * sin(angle), -point[0] * sin(angle) + point[1] * cos(angle)], "float32"
    )


def angle_between(v1: np.ndarray, v2: np.ndarray):
    """return the angle between two vectors in radian"""
    if np.linalg.norm(v1) == 0 or np.linalg.norm(v2) == 0:
        return 0
    angle = acos(max(min(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)), 1), -1))
    if angle > pi:
        angle = 2 * pi - angle
    return angle


def angle_diff(ang1: float, ang2: float):
    """return the difference between two angles in radian"""
    diff = ((ang1 - ang2) % (2 * pi) + 2 * pi) % (2 * pi)
    if diff > pi:
        diff = 2 * pi - diff
    return diff


def get_toward(pos1, pos2):
    if abs(pos1[0] - pos2[0]) < abs(pos1[1] - pos2[1]):
        if pos1[1] < pos2[1]:
            return 0
        else:
            return 2
    else:
        if pos1[0] < pos2[0]:
            return 1
        else:
            return 3


def get_length(pos1: tuple, pos2: tuple):
    return sqrt((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2)


def tuple_in_list(t: tuple, l: list):
    for item in l:
        if (t[0] == item[0] and t[1] == item[1]) or (t[0] == item[1] and t[1] == item[0]):
            return True
    return False


def remove_tuple(t: tuple, l: list):
    for item in l:
        if (t[0] == item[0] and t[1] == item[1]) or (t[0] == item[1] and t[1] == item[0]):
            l.remove(item)
            return
    assert False


def bit_diff(code1: int, code2: int):
    return bin(code1 ^ code2).count("1")


def cross(code1: List[int], code2: List[int]):
    length = len(code1) * 4
    loc = random.randint(1, length - 1)
    code1_bk = deepcopy(code1)
    code1[loc // 4] = (code1[loc // 4] >> (4 - loc % 4) << (4 - loc % 4)) | (code2[loc // 4] & (15 >> (loc % 4)))
    code2[loc // 4] = (code2[loc // 4] >> (4 - loc % 4) << (4 - loc % 4)) | (code1_bk[loc // 4] & (15 >> (loc % 4)))
    code1[loc // 4 + 1 :] = code2[loc // 4 + 1 :]
    code2[loc // 4 + 1 :] = code1_bk[loc // 4 + 1 :]
    return code1, code2


def mutate(code: List[int]):
    length = len(code) * 4
    loc = random.randint(0, length - 1)
    code[loc // 4] = code[loc // 4] ^ (8 >> (loc % 4))
    return code


def is_border_edge(graph: nx.Graph, edge: tuple):
    # decide whether an edge is a border edge on the site_bound
    p1, p2 = graph.nodes[edge[0]]["pos"], graph.nodes[edge[1]]["pos"]
    # pxl, pxh = min(p1[0], p2[0]), max(p1[0], p2[0])
    # pyl, pyh = min(p1[1], p2[1]), max(p1[1], p2[1])
    for i in range(len(site_bound)):
        s1, s2 = site_bound[i], site_bound[(i + 1) % len(site_bound)]
        t1, proj1 = projection(p1, s1, s2)
        t2, proj2 = projection(p2, s1, s2)
        if (
            -EPS <= t1 <= 1 + EPS
            and -EPS <= t2 <= 1 + EPS
            and np.linalg.norm(proj1 - p1) < EPS
            and np.linalg.norm(proj2 - p2) < EPS
        ):
            return True
    return False


def projection(p, p1, p2):
    # project point p onto line p1p2
    p1, p2 = np.array(p1), np.array(p2)
    if np.linalg.norm(p1 - p2) < EPS:
        return p1
    t = np.dot(p - p1, p2 - p1) / np.dot(p2 - p1, p2 - p1)
    return t, p1 + t * (p2 - p1)


def get_minimum_rotated_rectangle(polygon: Polygon, tolerance=1e-1):
    # Get the minimum area enclosing rectangle (convex hull-based)
    min_rotated_rect = polygon.minimum_rotated_rectangle
    min_area = min_rotated_rect.area
    # Initialize lists to store possible rectangles and their areas
    areas, rectangles = [], []
    # Calculate the tolerance boundary
    tolerance_area = min_area * (1 + tolerance)
    # Perform a convex hull operation (shapely function) to compute enclosing boxes
    convex_hull = polygon.convex_hull
    hull_points = np.array(convex_hull.exterior.coords)

    # Iterate over each edge of the convex hull
    for i in range(len(hull_points)):
        # Vector for the current edge
        edge = hull_points[(i + 1) % len(hull_points)] - hull_points[i]
        edge_angle = np.arctan2(edge[1], edge[0])

        # Rotation matrix to align edge with the x-axis
        rotation_matrix = np.array(
            [[np.cos(-edge_angle), -np.sin(-edge_angle)], [np.sin(-edge_angle), np.cos(-edge_angle)]]
        )
        # Rotate all points by this angle
        rotated_points = np.dot(hull_points, rotation_matrix.T)

        # Get the min/max x and y values
        min_x = np.min(rotated_points[:, 0])
        max_x = np.max(rotated_points[:, 0])
        min_y = np.min(rotated_points[:, 1])
        max_y = np.max(rotated_points[:, 1])

        # Calculate the corners of the bounding box
        corners = np.array([[min_x, min_y], [max_x, min_y], [max_x, max_y], [min_x, max_y]])
        # Rotate the corners back
        unrotated_corners = np.dot(corners, rotation_matrix)
        # Calculate area of the bounding box
        area = (max_x - min_x) * (max_y - min_y)
        if area < tolerance_area:
            areas.append(area)
            rectangles.append(unrotated_corners)
    # If we have multiple valid rectangles within tolerance, pick one randomly
    if len(rectangles) > 1:
        rec = random.choice(rectangles)
        return Polygon(rec)
    else:
        return min_rotated_rect


def split_region(graph: nx.Graph, regions: list, idx: int):
    region = regions[idx]
    num_points = len(region)
    points = [graph.nodes[region[i]]["pos"] for i in range(num_points)]
    new_points = []
    for i in range(num_points):
        p1, p2 = points[i], points[(i + 1) % num_points]
        on_line_points = []
        for n in graph.nodes:
            if n in region:
                continue
            p = graph.nodes[n]["pos"]
            t, proj = projection(p, p1, p2)
            if 0 <= t <= 1 and np.linalg.norm(p - proj) < EPS:
                on_line_points.append(n)
        on_line_points.sort(key=lambda x: np.linalg.norm(graph.nodes[x]["pos"] - p1))
        new_points.append(p1)
        new_points.extend([graph.nodes[n]["pos"] for n in on_line_points])
    # Create a polygon from the region points
    poly = Polygon(new_points)
    if not poly.is_valid or poly.area == 0:
        return False  # Invalid polygon, cannot split

    # rect = poly.minimum_rotated_rectangle
    rect = get_minimum_rotated_rectangle(poly)
    rec_points = list(rect.exterior.coords)[:-1]  # Exclude the repeated last point
    rec_points = [vec(x) for x in rec_points]

    # Calculate length and width of the rectangle
    length = get_length(rec_points[0], rec_points[1])
    width = get_length(rec_points[1], rec_points[2])

    # Determine split type based on rectangle dimensions
    if length > width * 1.5:
        split_type = 0  # Split along the longer side
    elif width > length * 1.5:
        split_type = 1  # Split along the shorter side
    else:
        split_type = random.randint(0, 1)  # Randomly choose split type if ratios are not extreme

    if split_type == 0:
        # Split along the length
        p1, p2, p3 = rec_points[0], rec_points[1], rec_points[2]
        best_t = -1
        for i in range(num_points):
            t, proj = projection(new_points[i], p1, p2)
            if 1 / 3 <= t <= 2 / 3:
                if best_t < 0 or abs(t - 0.5) < abs(best_t - 0.5):
                    best_t = t
        if best_t < 0:
            best_t = random.uniform(1 / 3, 2 / 3)
        if length * best_t < MAIN_ROAD_WIDTH * 2 or length * (1 - best_t) < MAIN_ROAD_WIDTH * 2:
            return False  # Split would create regions too small
    else:
        # Split along the width
        p1, p2, p3 = rec_points[1], rec_points[2], rec_points[3]
        best_t = -1
        for i in range(num_points):
            t, proj = projection(new_points[i], p1, p2)
            if 1 / 3 <= t <= 2 / 3:
                if best_t < 0 or abs(t - 0.5) < abs(best_t - 0.5):
                    best_t = t
        if best_t < 0:
            best_t = random.uniform(1 / 3, 2 / 3)
        if width * best_t < MAIN_ROAD_WIDTH * 2 or width * (1 - best_t) < MAIN_ROAD_WIDTH * 2:
            return False  # Split would create regions too small

    # remove existing edges
    # for i in range(num_points):
    #     if (region[i], region[(i + 1) % num_points]) in graph.edges:
    #         graph.remove_edge(region[i], region[(i + 1) % num_points])
    #     elif (region[(i + 1) % num_points], region[i]) in graph.edges:
    #         graph.remove_edge(region[(i + 1) % num_points], region[i])
    # Define the split line
    split_vector = p3 - p2
    p_t1 = p1 + best_t * (p2 - p1) - 0.1 * split_vector
    p_t2 = p_t1 + 1.2 * split_vector
    split_line = LineString([p_t1, p_t2])
    split_result = split(poly, split_line)
    # split
    new_regions = []
    for po in split_result.geoms:
        po = po.buffer(-1e-4)
        if isinstance(po, MultiPolygon):
            po_list = list(po.geoms)
        else:
            po_list = [po]
        for po in po_list:
            if po.area < 1e-4:
                continue
            new_region = []
            for i in range(len(po.exterior.coords) - 1):
                p1 = vec(po.exterior.coords[i])
                already_exist = False
                for j in range(len(graph.nodes)):
                    p2 = vec(graph.nodes[j]["pos"])
                    if np.linalg.norm(p1 - p2) < COMBINE_THRES:
                        already_exist = True
                        new_region.append(j)
                        break
                if not already_exist:
                    graph.add_node(len(graph.nodes), pos=vec(p1[0], p1[1]))
                    new_region.append(len(graph.nodes) - 1)
            # deduplicate
            for i in range(len(new_region) - 1, -1, -1):
                if new_region[i] == new_region[(i + 1) % len(new_region)]:
                    new_region.pop(i)
            # add edges
            # for i in range(len(new_region)):
            #     n1, n2 = new_region[i], new_region[(i + 1) % len(new_region)]
            #     graph.add_edge(min(n1, n2), max(n1, n2))
            if len(new_region) >= 3:
                new_regions.append(new_region)

    regions.pop(idx)
    regions.extend(new_regions)

    return True


def visualize_raw(graph: nx.Graph, idx: int):
    fig,ax=plt.subplots(figsize=(10, site_height / site_width * 10), layout="tight")
    pos = nx.get_node_attributes(graph, "pos")
    for node in graph.nodes:
        plt.scatter(
            pos[node][0],
            pos[node][1],
            c="black",
        )
        # plt.text(pos[node][0], pos[node][1], str(node), fontsize=12)
    for edge in graph.edges:
        plt.plot([pos[edge[0]][0], pos[edge[1]][0]], [pos[edge[0]][1], pos[edge[1]][1]], c="black", linewidth=1)
    dir = "visuals/{}_{}_{}".format(site_width, site_height, idx)
    if not os.path.exists(dir):
        os.mkdir(dir)
    ax.set_xlim(site_xl-1, site_xh+1)
    ax.set_ylim(site_yl-1, site_yh+1)
    ax.axis('off')
    plt.savefig("{}/graph_raw.png".format(dir))
    plt.clf()
    plt.close()


def visualize_chosen_edges(graph: nx.Graph, chosen_edges: list, name: str, idx: int):
    plt.figure(figsize=(10, site_height / site_width * 10), layout="tight")
    pos = nx.get_node_attributes(graph, "pos")
    for node in graph.nodes:
        plt.scatter(
            pos[node][0],
            pos[node][1],
            c="black",
        )
    for edge in graph.edges:
        if tuple_in_list(edge, chosen_edges):
            plt.plot([pos[edge[0]][0], pos[edge[1]][0]], [pos[edge[0]][1], pos[edge[1]][1]], c="red", linewidth=8)
        else:
            plt.plot([pos[edge[0]][0], pos[edge[1]][0]], [pos[edge[0]][1], pos[edge[1]][1]], c="black", linewidth=1)
    dir = "visuals/{}_{}_{}".format(site_width, site_height, idx)
    if not os.path.exists(dir):
        os.mkdir(dir)
    plt.savefig("{}/graph_{}.png".format(dir, name))
    plt.clf()
    plt.close()


def visualize(graph: nx.Graph, chosen_edges: list, main_edges: list, sub_edges: list, idx: int):
    plt.figure(figsize=(10, site_height / site_width * 10), layout="tight")
    pos = nx.get_node_attributes(graph, "pos")
    for node in graph.nodes:
        plt.scatter(
            pos[node][0],
            pos[node][1],
            c="black",
        )
    for edge in graph.edges:
        if tuple_in_list(edge, main_edges):
            plt.plot([pos[edge[0]][0], pos[edge[1]][0]], [pos[edge[0]][1], pos[edge[1]][1]], c="red", linewidth=8)
        elif tuple_in_list(edge, sub_edges):
            plt.plot([pos[edge[0]][0], pos[edge[1]][0]], [pos[edge[0]][1], pos[edge[1]][1]], c="blue", linewidth=5)
        else:
            plt.plot([pos[edge[0]][0], pos[edge[1]][0]], [pos[edge[0]][1], pos[edge[1]][1]], c="black", linewidth=1)
    # nx.draw(graph, pos, with_labels=True)
    dir = "visuals/{}_{}_{}".format(site_width, site_height, idx)
    if not os.path.exists(dir):
        os.mkdir(dir)
    plt.savefig("{}/graph.png".format(dir))
    plt.clf()
    plt.close()


def visualize_areas(graph: nx.Graph, circuits: List[list], code: List[int], idx: int):
    count = len(circuits)
    polys = [Polygon([graph.nodes[node]["pos"] for node in circuit]).simplify(0, True) for circuit in circuits]
    plt.figure(figsize=(10, site_height / site_width * 10), layout="tight")
    for i in range(count):
        color = None
        if code[i] == 0:
            color = (0, 204, 255)
        elif code[i] == 1:
            color = (233, 233, 233)
        elif code[i] == 2:
            color = (255, 0, 72)
        elif code[i] == 3:
            color = (255, 186, 0)
        elif code[i] == 4:
            color = (0, 168, 36)
        elif code[i] == 5:
            color = (153, 191, 0)
        elif code[i] == 6:
            color = (191, 0, 67)
        elif code[i] == 7:
            color = (191, 143, 0)
        elif code[i] == 8:
            color = (0, 0, 0)
        elif code[i] == 9:
            color = (51, 64, 0)
        elif code[i] == 10:
            color = (64, 0, 22)
        elif code[i] == 11:
            color = (64, 48, 0)
        elif code[i] == 12:
            color = (0, 84, 18)
        elif code[i] == 13:
            color = (102, 128, 0)
        elif code[i] == 14:
            color = (128, 0, 45)
        elif code[i] == 15:
            color = (128, 96, 0)
        color = tuple([x / 255 for x in color])
        plt.fill(*polys[i].exterior.xy, c=color)
    dir = "visuals/{}_{}_{}".format(site_width, site_height, idx)
    if not os.path.exists(dir):
        os.mkdir(dir)
    plt.savefig("{}/areas.png".format(dir))
    plt.clf()
    plt.close()


def division_evaluate(
    graph: nx.Graph, chosen_graph: nx.Graph, inner_lines, isolated_nodes: List[int], chosen_edges: List[tuple], polys
):
    random.shuffle(isolated_nodes)
    for node in isolated_nodes:
        if chosen_graph.degree(node) > 1:
            continue
        curr_node = node
        while True:
            neighbors = list(graph.__getitem__(curr_node).keys())
            random.shuffle(neighbors)
            for neighbor in neighbors:
                if tuple_in_list((curr_node, neighbor), chosen_edges):
                    continue
                chosen_graph.add_edge(curr_node, neighbor)
                chosen_edges.append((curr_node, neighbor))
                x1, x2, y1, y2 = (
                    graph.nodes[curr_node]["pos"][0],
                    graph.nodes[neighbor]["pos"][0],
                    graph.nodes[curr_node]["pos"][1],
                    graph.nodes[neighbor]["pos"][1],
                )
                dx, dy = x2 - x1, y2 - y1
                x1, x2, y1, y2 = x1 - dx * EPS, y2 - dy * EPS, x2 + dx * EPS, y2 + dy * EPS
                norm_vec = norm(vec(y2 - y1, x1 - x2))
                road_poly = Polygon(
                    [
                        [x1 - norm_vec[0] * SUB_ROAD_WIDTH / 2, y1 - norm_vec[1] * SUB_ROAD_WIDTH / 2],
                        [x2 - norm_vec[0] * SUB_ROAD_WIDTH / 2, y2 - norm_vec[1] * SUB_ROAD_WIDTH / 2],
                        [x2 + norm_vec[0] * SUB_ROAD_WIDTH / 2, y2 + norm_vec[1] * SUB_ROAD_WIDTH / 2],
                        [x1 + norm_vec[0] * SUB_ROAD_WIDTH / 2, y1 + norm_vec[1] * SUB_ROAD_WIDTH / 2],
                    ]
                )
                polys = polys.difference(road_poly)
                curr_node = neighbor
                break
            if chosen_graph.degree(curr_node) > 1:
                break

    ### evaluation
    score1, score2, score3, score4 = [0 for _ in range(4)]
    polys = (
        [polys.simplify(0, False)] if isinstance(polys, Polygon) else [poly.simplify(0, False) for poly in polys.geoms]
    )

    # area ratios
    areas = np.array([poly.area for poly in polys]).reshape(-1, 1)
    kmeans = KMeans(n_clusters=3, n_init="auto")
    labels = kmeans.fit(areas).labels_
    max_idx, min_idx = np.argmax(kmeans.cluster_centers_), np.argmin(kmeans.cluster_centers_)
    min_count_ratio = len(areas[labels == min_idx]) / len(polys)
    if min_count_ratio > 0.5:
        score1 += (min_count_ratio - 0.5) * 10
    max_area_ratio = np.sum((areas[labels == max_idx])) / site_area
    score1 += (max_area_ratio - 1 / 2) ** 2 * 10

    # polygon simplicity
    num_sides = [len(poly.exterior.coords) // 2 for poly in polys]
    extra_sides = 0
    for num_side in num_sides:
        if num_side > 3:
            extra_sides += (num_side - 3) ** 1.5
    score2 = extra_sides / len(polys)
    # polygon diversity
    num_sides_set = set(num_sides)
    score3 = -len(num_sides_set) / 5

    # network connectivity
    for line in inner_lines:
        connect_count = 0
        for node in line:
            if chosen_graph.degree(node) > 0:
                connect_count += 1
        if connect_count == 0:
            score4 += 1.5
        elif connect_count > 2:
            score4 += (connect_count - 2) * 0.5
    all_nodes = list(chosen_graph.nodes)
    for node in all_nodes:
        if chosen_graph.degree(node) == 0:
            chosen_graph.remove_node(node)
    score4 += nx.number_connected_components(chosen_graph) * 2

    score = score1 + score2 + score3 + score4
    # print(score1, score2, score3, score4, score)
    return chosen_graph, chosen_edges, score


def order_lines(graph: nx.Graph, split: int, inner_lines: List[int], chosen_edges: List[tuple]):
    length_and_lines = []
    for i in range(len(inner_lines)):
        length = get_length(graph.nodes[inner_lines[i][0]]["pos"], graph.nodes[inner_lines[i][-1]]["pos"])
        length_and_lines.append((length, inner_lines[i]))
    length_and_lines.sort()

    accept_thres = 0.5
    major_length_and_lines = [length_and_line for length_and_line in length_and_lines[-split // 4 :]][::-1]
    for length, line in major_length_and_lines:
        chosen_length = 0
        for i in range(len(line) - 1):
            n1, n2 = line[i], line[i + 1]
            if tuple_in_list((n1, n2), chosen_edges):
                chosen_length += get_length(graph.nodes[n1]["pos"], graph.nodes[n2]["pos"])
        if chosen_length > length * accept_thres:
            for i in range(len(line) - 1):
                n1, n2 = line[i], line[i + 1]
                if not tuple_in_list((n1, n2), chosen_edges):
                    chosen_edges.append((n1, n2))
            accept_thres += 0.3
        else:
            for i in range(len(line) - 1):
                n1, n2 = line[i], line[i + 1]
                if (n1, n2) in chosen_edges:
                    chosen_edges.remove((n1, n2))
                elif (n2, n1) in chosen_edges:
                    chosen_edges.remove((n2, n1))
            accept_thres -= 0.3


def order_circuits(graph: nx.Graph, inner_lines, chosen_edges: List[tuple]):
    chosen_graph = nx.Graph()
    chosen_graph.add_nodes_from(graph.nodes)
    chosen_graph.add_edges_from(chosen_edges)

    all_circuits = nx.cycle_basis(chosen_graph)
    circuit_edges = []
    circuit_nodes = set()
    for circuit in all_circuits:
        for i in range(len(circuit)):
            n1, n2 = circuit[i], circuit[(i + 1) % len(circuit)]
            circuit_nodes.add(n1)
            circuit_nodes.add(n2)
            if not tuple_in_list((n1, n2), circuit_edges):
                circuit_edges.append((n1, n2))

    non_circuit_edges = []
    non_circuit_nodes = set()
    for edge in chosen_edges:
        if not tuple_in_list(edge, circuit_edges):
            non_circuit_edges.append(edge)
            if edge[0] not in circuit_nodes:
                non_circuit_nodes.add(edge[0])
            if edge[1] not in circuit_nodes:
                non_circuit_nodes.add(edge[1])

    isolated_nodes = set()
    for node in non_circuit_nodes:
        if chosen_graph.degree(node) == 1:
            isolated_nodes.add(node)

    for edge in non_circuit_edges:
        if edge[0] in isolated_nodes and edge[1] in isolated_nodes:
            non_circuit_edges.remove(edge)
            remove_edge(chosen_graph, (edge[0], edge[1]))
            remove_tuple(edge, chosen_edges)
            isolated_nodes.remove(edge[0])
            isolated_nodes.remove(edge[1])

    isolated_nodes = list(isolated_nodes)
    poly = get_spaces(graph, chosen_edges, EPS)
    best_graph, best_edges, min_score = None, None, float("inf")
    for k in range(MAX_CIRCUIT_TRY):
        new_graph, new_edges, score = division_evaluate(
            graph, deepcopy(chosen_graph), inner_lines, deepcopy(isolated_nodes), deepcopy(chosen_edges), deepcopy(poly)
        )
        if score < min_score:
            min_score = score
            # best_graph = new_graph
            best_edges = new_edges
    return best_edges


def get_simple_circuits(graph: nx.Graph, chosen_edges: List[tuple]):
    polys = get_spaces(graph, chosen_edges, EPS)
    polys = [polys] if isinstance(polys, Polygon) else list(polys.geoms)
    circuits = []
    for poly in polys:
        circuit = []
        coords = list(poly.exterior.coords)[:-1]
        for p in coords:
            for node in graph.nodes:
                if get_length(p, graph.nodes[node]["pos"]) < EPS * 20:
                    if node not in circuit:
                        circuit.append(node)
                    break
        circuits.append(circuit)
    return circuits


def genetic_evaluate(
    code: List[int], areas: List[int], num_sides: List[int], adjacents: List[list], adjacent_lengths: List[list]
):
    # - 水面：0000 平面
    # - 草地：0001 平面
    # - 花园：0010 低矮
    # - 花草：0011 平面，种带花的草
    # - 灌木：0100 低矮
    # - 灌草：0101 灌木围周围（不围满），其余种草
    # - 灌花：0110 低矮，灌木和花木按一定规则种
    # - 灌花草：0111 灌木围周围（不围满），其余种花草
    # - 树林：1000 高大，高密度的树
    # - 树草：1001 以草为主，零散种一些大树小树
    # - 树花：1010 以花木作为过渡，其余部分种密度一般的大树小树
    # - 树花草：1011 - 以花草为主，零散种一些大树小树
    # - 树灌：1100 以灌木作为过渡，其余部分种密度一般的大树小树
    # - 树灌草：1101 草-灌木-小树-大树
    # - 树灌花：1110 灌木+花木-小树-大树
    # - 树灌花草：1111 花草-灌木-小树-大树

    score1, score2, score3, score4 = [0 for i in range(4)]
    count = len(code)

    # self compatibility(polygon)
    for i in range(count):
        if (code[i] == 2 or code[i] == 4 or code[i] == 6) and num_sides[i] // 2 > 3:
            score1 += 2

    # adjacent compatibility
    for i in range(count):
        for j in range(len(adjacents[i])):
            adjacent_node = adjacents[i][j]
            adjacent_length = adjacent_lengths[i][j]
            if code[i] == 0 and code[adjacent_node] > 0 and code[adjacent_node] & 1 == 0:
                score2 += adjacent_length / (site_width + site_height)
            elif code[i] == 8 and (code[adjacent_node] == 0 or code[adjacent_node] == 1 or code[adjacent_node] == 3):
                score2 += adjacent_length / (site_width + site_height)
            bit_d = bit_diff(code[i], code[adjacent_node])
            if bit_d > 2:
                score2 += adjacent_length * (bit_d - 2) / (site_width + site_height)

    # general and self compatibility
    total_area = site_area
    water, grass, flower, bush, tree = [0 for i in range(5)]
    water_c, grass_c, flower_c, bush_c, tree_c = [0 for i in range(5)]
    exist_flag = [0 for i in range(16)]
    WATER_MIN = 400
    TREE_MIN = 400
    FLOWER_MAX = 350
    BUSH_MAX = 400
    for i in range(count):
        c, a = code[i], areas[i]
        if c == 0:
            water += a
            water_c += 1
            if a < WATER_MIN:
                score1 += (WATER_MIN - a) * 0.01
        elif c == 1:
            grass += a
            grass_c += 1
        elif c == 2:
            flower += a
            flower_c += 1
            if a > FLOWER_MAX:
                score1 += (a - FLOWER_MAX) * 0.01
        elif c == 3:
            grass += a * 0.7
            flower += a * 0.3
            grass_c += 1
            flower_c += 1
            if a * 0.3 > FLOWER_MAX:
                score1 += (a * 0.3 - FLOWER_MAX) * 0.01
        elif c == 4:
            bush += a
            bush_c += 1
            if a > BUSH_MAX:
                score1 += (a - BUSH_MAX) * 0.01
        elif c == 5:
            bush += a * 0.2
            grass += a * 0.8
            bush_c += 1
            grass_c += 1
            if a * 0.2 > BUSH_MAX:
                score1 += (a * 0.2 - BUSH_MAX) * 0.01
        elif c == 6:
            bush += a * 0.5
            flower += a * 0.5
            bush_c += 1
            flower_c += 1
            if a * 0.5 > FLOWER_MAX:
                score1 += (a * 0.5 - FLOWER_MAX) * 0.01
            if a * 0.5 > BUSH_MAX:
                score1 += (a * 0.5 - BUSH_MAX) * 0.01
        elif c == 7:
            bush += a * 0.2
            grass += a * 0.6
            flower += a * 0.2
            bush_c += 1
            grass_c += 1
            flower_c += 1
            if a * 0.2 > BUSH_MAX:
                score1 += (a * 0.2 - BUSH_MAX) * 0.01
            if a * 0.2 > FLOWER_MAX:
                score1 += (a * 0.2 - FLOWER_MAX) * 0.01
        elif c == 8:
            tree += a
            tree_c += 1
            if a < TREE_MIN:
                score1 += (TREE_MIN - a) * 0.01
        elif c == 9:
            tree += a * 0.3
            grass += a * 0.7
            tree_c += 1
            grass_c += 1
            if a * 0.3 < TREE_MIN:
                score1 += (TREE_MIN - a * 0.3) * 0.01
        elif c == 10:
            tree += a * 0.8
            flower += a * 0.2
            tree_c += 1
            flower_c += 1
            if a * 0.2 > FLOWER_MAX:
                score1 += (a * 0.2 - FLOWER_MAX) * 0.01
            if a * 0.8 < TREE_MIN:
                score1 += (TREE_MIN - a * 0.8) * 0.01
        elif c == 11:
            tree += a * 0.2
            grass += a * 0.6
            flower += a * 0.2
            tree_c += 1
            grass_c += 1
            flower_c += 1
            if a * 0.2 > FLOWER_MAX:
                score1 += (a * 0.2 - FLOWER_MAX) * 0.01
        elif c == 12:
            tree += a * 0.8
            bush += a * 0.2
            tree_c += 1
            bush_c += 1
            if a * 0.2 > BUSH_MAX:
                score1 += (a * 0.2 - BUSH_MAX) * 0.01
            if a * 0.8 < TREE_MIN:
                score1 += (TREE_MIN - a * 0.8) * 0.01
        elif c == 13:
            tree += a * 0.7
            bush += a * 0.2
            grass += a * 0.1
            tree_c += 1
            bush_c += 1
            grass_c += 1
            if a * 0.2 > BUSH_MAX:
                score1 += (a * 0.2 - BUSH_MAX) * 0.01
            if a * 0.7 < TREE_MIN:
                score1 += (TREE_MIN - a * 0.7) * 0.01
        elif c == 14:
            tree += a * 0.8
            bush += a * 0.1
            flower += a * 0.1
            tree_c += 1
            bush_c += 1
            flower_c += 1
            if a * 0.1 > FLOWER_MAX:
                score1 += (a * 0.1 - FLOWER_MAX) * 0.01
            if a * 0.1 > BUSH_MAX:
                score1 += (a * 0.1 - BUSH_MAX) * 0.01
            if a * 0.8 < TREE_MIN:
                score1 += (TREE_MIN - a * 0.8) * 0.01
        elif c == 15:
            tree += a * 0.2
            bush += a * 0.1
            grass += a * 0.5
            flower += a * 0.2
            tree_c += 1
            bush_c += 1
            grass_c += 1
            flower_c += 1
            if a * 0.2 > FLOWER_MAX:
                score1 += (a * 0.2 - FLOWER_MAX) * 0.01
            if a * 0.1 > BUSH_MAX:
                score1 += (a * 0.1 - BUSH_MAX) * 0.01
        exist_flag[c] = 1

    if grass / total_area < 0.25:
        score3 += (0.25 - grass / total_area) * 20
    if tree / total_area < 0.35:
        score3 += (0.35 - tree / total_area) * 30
    if flower / total_area > 0.15:
        score3 += (flower / total_area - 0.15) * 20
    if bush / total_area > 0.15:
        score3 += (bush / total_area - 0.15) * 15
    if water_c > 2:
        score3 += 2

    # diversity
    score4 += max((10 - sum(exist_flag)) * 0.4, 0)
    if water_c == 0:
        score4 += 2
    if grass_c == 0:
        score4 += 2
    if flower_c == 0:
        score4 += 2
    if bush_c == 0:
        score4 += 2
    if tree_c == 0:
        score4 += 2

    score = 100 / (score1 + score2 + score3 + score4 + 0.1)
    # print(score1, score2, score3,score4, score)
    return score


def get_main_sub_edges(graph: nx.Graph, border_lines, inner_lines, chosen_edges: List[tuple]):
    chosen_graph = nx.Graph()
    chosen_graph.add_nodes_from(graph.nodes)
    chosen_graph.add_edges_from(chosen_edges)

    for line in border_lines:
        for i in range(len(line) - 1):
            remove_edge(chosen_graph, (line[i], line[i + 1]))
    chosen_length_and_lines = []
    for i in range(len(inner_lines)):
        line = inner_lines[i]
        if line in border_lines:
            continue
        start = -1
        length = 0
        for j in range(len(line) - 1):
            if tuple_in_list((line[j], line[j + 1]), chosen_edges):
                if start == -1:
                    start = j
                    length = get_length(graph.nodes[line[j]]["pos"], graph.nodes[line[j + 1]]["pos"])
                else:
                    length += get_length(graph.nodes[line[j]]["pos"], graph.nodes[line[j + 1]]["pos"])
            else:
                if start != -1:
                    chosen_length_and_lines.append((length, line[start : j + 1]))
                    start = -1
                    length = 0
        if start != -1:
            chosen_length_and_lines.append((length, line[start:]))
    chosen_length_and_lines.sort(key=lambda x: x[0])
    sorted_connected_components = sorted(nx.connected_components(chosen_graph), key=len, reverse=True)
    for i in range(1, len(sorted_connected_components)):
        for node in sorted_connected_components[i]:
            chosen_graph.remove_node(node)

    ignored_border_lines = []
    for i in range(len(border_lines)):
        border_line = border_lines[i]
        connect_flag = False
        for j in range(len(border_line)):
            if chosen_graph.has_node(border_line[j]) and chosen_graph.degree[border_line[j]] > 0:
                connect_flag = True
                break
        if not connect_flag:
            ignored_border_lines.append(border_line)

    for length, line in chosen_length_and_lines:
        finish = False
        for i in range(len(line) - 1):
            if not tuple_in_list((line[i], line[i + 1]), list(chosen_graph.edges)):
                continue
            remove_edge(chosen_graph, (line[i], line[i + 1]))
            valid = True
            fin = True
            for border_line in border_lines:
                if border_line in ignored_border_lines:
                    continue
                connect_num = 0
                for j in range(len(border_line)):
                    if chosen_graph.has_node(border_line[j]) and chosen_graph.degree[border_line[j]] > 0:
                        connect_num += 1
                if connect_num == 0:
                    valid = False
                    break
                if connect_num > 1:
                    fin = False
            if not valid:
                chosen_graph.add_edge(line[i], line[i + 1])
                continue
            if chosen_graph.degree(line[i]) == 0:
                chosen_graph.remove_node(line[i])
                continue
            elif chosen_graph.degree(line[i + 1]) == 0:
                chosen_graph.remove_node(line[i + 1])
                continue

            if nx.number_connected_components(chosen_graph) > 1:
                chosen_graph.add_edge(line[i], line[i + 1])
                continue

            if fin:
                circuits = nx.cycle_basis(chosen_graph)
                if len(circuits) == 0:  # finish
                    finish = True
                    break
        if finish:
            break
    for line in border_lines:
        for i in range(len(line) - 1):
            chosen_graph.add_edge(line[i], line[i + 1])

    all_circuits = nx.cycle_basis(chosen_graph)
    circuit_edges = []
    for circuit in all_circuits:
        for i in range(len(circuit)):
            n1, n2 = circuit[i], circuit[(i + 1) % len(circuit)]
            if not tuple_in_list((n1, n2), circuit_edges):
                circuit_edges.append((n1, n2))

    non_circuit_edges = []
    for edge in chosen_graph.edges:
        if not tuple_in_list(edge, circuit_edges):
            non_circuit_edges.append(edge)
    for edge in non_circuit_edges:
        remove_edge(chosen_graph, (edge[0], edge[1]))

    main_edges = list(chosen_graph.edges)
    sub_edges = []
    for edge in chosen_edges:
        if not tuple_in_list(edge, main_edges):
            sub_edges.append(edge)
    return main_edges, sub_edges


def genetic_area_choose(graph: nx.Graph, circuits: List[list]):
    count = len(circuits)
    polys = [Polygon([graph.nodes[node]["pos"] for node in circuit]).simplify(0, False) for circuit in circuits]
    num_sides = [len(poly.exterior.coords) for poly in polys]
    areas = [poly.area for poly in polys]
    perimeters = [poly.length for poly in polys]
    adjacents = [[] for _ in range(len(circuits))]
    adjacent_lengths = [[0 for j in range(len(circuits))] for i in range(len(circuits))]

    circuit_edges = [
        [(circuit[i], circuit[(i + 1) % len(circuit)]) for i in range(len(circuit))] for circuit in circuits
    ]
    for edge in graph.edges:
        idxes = []
        for i in range(len(circuits)):
            if tuple_in_list(edge, circuit_edges[i]):
                idxes.append(i)
            if len(idxes) == 2:
                break
        if len(idxes) == 2:
            length = get_length(graph.nodes[edge[0]]["pos"], graph.nodes[edge[1]]["pos"])
            adjacent_lengths[idxes[0]][idxes[1]] += length
            adjacent_lengths[idxes[1]][idxes[0]] += length
    for i in range(len(circuits)):
        for j in range(len(circuits)):
            if i == j:
                continue
            if adjacent_lengths[i][j] > 0:
                adjacents[i].append(j)
    adjacent_ratios = [
        [adjacent_lengths[i][j] / perimeters[i] for j in range(len(circuits))] for i in range(len(circuits))
    ]

    # perform genetic algorithm
    population = [[random.randint(0, 15) for _ in range(count)] for k in range(POPULATION_SIZE)]
    max_val, max_code = 0, None
    for k in range(MAX_GENERATION):
        # select
        vals = [genetic_evaluate(code, areas, num_sides, adjacents, adjacent_lengths) for code in population]

        argmax = np.argmax(vals)
        if vals[argmax] > max_val:
            max_val = vals[argmax]
            max_code = population[argmax]
        sum_vals = sum(vals)
        choose_counts = [val / sum_vals * POPULATION_SIZE for val in vals]
        new_population = []
        for i in range(len(choose_counts)):
            for j in range(int(choose_counts[i])):
                new_population.append(deepcopy(population[i]))
            choose_counts[i] -= int(choose_counts[i])
        choose_count_and_idx = [(choose_counts[i], i) for i in range(len(choose_counts))]
        choose_count_and_idx.sort(key=lambda x: x[0], reverse=True)
        for i in range(POPULATION_SIZE - len(new_population)):
            new_population.append(deepcopy(population[choose_count_and_idx[i][1]]))

        # cross and mutate
        random.shuffle(new_population)
        cross_pair_count = int(POPULATION_SIZE * CROSS_RATE / 2)
        for i in range(cross_pair_count):
            new_population[2 * i], new_population[2 * i + 1] = cross(new_population[2 * i], new_population[2 * i + 1])
        random.shuffle(new_population)
        mutate_count = int(POPULATION_SIZE * MUTATION_RATE)
        for i in range(mutate_count):
            new_population[i] = mutate(new_population[i])
        population = new_population
        # print(max_val)
    # print(max_val, max_code)
    return max_code


def fill_fence(pos1: tuple, pos2: tuple, length: float, fence_type: str):
    res = []
    p1, p2 = vec(pos1[0], pos1[1]), vec(pos2[0], pos2[1])
    toward = (get_toward(pos1, pos2) + 1) % 4
    p_length = get_length(pos1, pos2)
    if p_length < length * 0.4:
        pass
    elif p_length < length:
        res.append((((p1 + p2) / 2)[0], ((p1 + p2) / 2)[1], toward, p_length / length, fence_type))
    else:
        unit_length, units = None, None
        for i in range(max(1, int(p_length / length / 1.2)), max(2, int(p_length / length) + 2)):
            if p_length / length / i < 1.2:
                unit_length, units = p_length / length / i, i
                break
        for i in range(units):
            p3 = p1 + (p2 - p1) * (i + 0.5) / units
            res.append((p3[0], p3[1], toward, unit_length, fence_type))
    return res


def random_fill_area(
    poly: Polygon,
    width: float,
    height: float,
    ratio: float,
    minscale: float = 0.8,
    maxscale: float = 1.2,
    exist_polys: List[Polygon] = [],
):
    tree_debug = False
    if width >= 3 and height >= 3:
        tree_debug = True
    positions_and_scales = []
    base_poly = Polygon(
        [(-width / 2, -height / 2), (width / 2, -height / 2), (width / 2, height / 2), (-width / 2, height / 2)]
    )
    area, area_bound = 0, poly.area * ratio
    xl, yl, xh, yh = poly.bounds
    continious_fail = 0
    contain_count = 0
    # if tree_debug:
    #     print('len:', len(exist_polys))
    for i in range(MODEL_LIMIT * 2):
        continious_fail += 1
        random_scale = random.uniform(minscale, maxscale)
        scaled_poly = scale(base_poly, random_scale, random_scale)
        for k in range(50):
            x = random.uniform(xl + random_scale * width / 2, xh - random_scale * width / 2)
            y = random.uniform(yl + random_scale * height / 2, yh - random_scale * height / 2)
            translated_poly = translate(scaled_poly, x, y)
            valid = poly.contains(translated_poly)
            if valid:
                contain_count += 1
                for existing_poly in exist_polys:
                    if translated_poly.intersects(existing_poly):
                        valid = False
                        break
            if valid:
                positions_and_scales.append((x, y, random_scale))
                exist_polys.append(translated_poly)
                area += scaled_poly.area
                continious_fail = 0
                break
        if continious_fail > 50 or len(positions_and_scales) == MODEL_LIMIT or area > area_bound:
            # if tree_debug:
            #     print("tree debug", continious_fail, len(positions_and_scales), poly.area, contain_count)
            break
    return positions_and_scales, exist_polys


def random_fill_area_free(
    poly: Polygon, width: float, height: float, ratio: float, minscale: float = 0.8, maxscale: float = 1.2
):
    positions_and_scales = []
    base_poly = Polygon(
        [(-width / 2, -height / 2), (width / 2, -height / 2), (width / 2, height / 2), (-width / 2, height / 2)]
    )
    area, area_bound = 0, poly.area * ratio
    xl, yl, xh, yh = poly.bounds
    for i in range(MODEL_LIMIT * 2):
        random_scale = random.uniform(minscale, maxscale)
        scaled_poly = scale(base_poly, random_scale, random_scale)
        for k in range(50):
            x = random.uniform(xl + random_scale * width / 2, xh - random_scale * width / 2)
            y = random.uniform(yl + random_scale * height / 2, yh - random_scale * height / 2)
            translated_poly = translate(scaled_poly, x, y)
            valid = poly.contains(translated_poly)
            if valid:
                positions_and_scales.append((x, y, random_scale))
                area += scaled_poly.area
                break
        if len(positions_and_scales) == MODEL_LIMIT or area > area_bound:
            break
    return positions_and_scales


def full_fill_area(poly: Polygon, width: float, height: float):
    positions_and_scales = []
    base_poly = Polygon(
        [(-width / 2, -height / 2), (width / 2, -height / 2), (width / 2, height / 2), (-width / 2, height / 2)]
    )
    width_floating, height_floating = width * 0.05, height * 0.05
    xl, yl, xh, yh = poly.bounds
    predifined_positions = []
    y = yl + random.uniform(0, height / 2) + height / 2 + height_floating
    while y < yh:
        x = xl + random.uniform(0, width / 2) + width / 2 + width_floating
        while x < xh:
            predifined_positions.append(
                (
                    x + random.uniform(-width_floating, width_floating),
                    y + random.uniform(-height_floating, height_floating),
                )
            )
            x += width + width_floating * 2 + random.uniform(0, width_floating)
        y += height + height_floating * 2 + random.uniform(0, height_floating)

    count = 0
    for position in predifined_positions:
        x, y = position
        random_scale = random.uniform(0.9, 1.1)
        scaled_poly = scale(base_poly, random_scale, random_scale)
        translated_poly = translate(scaled_poly, x, y)
        valid = poly.contains(translated_poly)
        if valid:
            positions_and_scales.append((x, y, random_scale))
            count += 1
        if count > MODEL_LIMIT:
            break

    return positions_and_scales


def border_fill_area(poly: Polygon, width: float, height: float, max_layer: int, spaced_layer: int):
    positions_and_scales = []
    base_poly = Polygon(
        [(-width / 2, -height / 2), (width / 2, -height / 2), (width / 2, height / 2), (-width / 2, height / 2)]
    )
    # xl, yl, xh, yh = poly.bounds
    boundary = list(poly.exterior.coords[:-1])
    if LinearRing(boundary).is_ccw:
        boundary = boundary[::-1]
    existing_polys = []
    count = 0
    rand_num = random.randint(0, len(boundary) - 1)
    ommited_edges = [rand_num] if len(boundary) < 6 else [rand_num, (rand_num + 1) % len(boundary)]
    for i in range(len(boundary)):
        if i in ommited_edges:
            continue
        p0, p1, p2, p3 = (
            boundary[i - 1],
            boundary[i],
            boundary[(i + 1) % len(boundary)],
            boundary[(i + 2) % len(boundary)],
        )
        p0, p1, p2, p3 = vec(p0[0], p0[1]), vec(p1[0], p1[1]), vec(p2[0], p2[1]), vec(p3[0], p3[1])
        left_spaced, right_spaced = (
            angle_between(p0 - p1, p2 - p1) < pi * 2 / 3,
            angle_between(p3 - p2, p1 - p2) < pi * 2 / 3,
        )
        tang = norm(p2 - p1)
        normal = rot(tang, pi / 2)
        length = get_length(p1, p2)
        rotation = -atan2(tang[1], tang[0])
        if length < width:
            continue
        nx = int(length / width)
        layers = random.randint(1, max_layer)
        jl = spaced_layer if left_spaced else 0
        jh = nx - spaced_layer if right_spaced else nx
        for j in range(jl, jh):
            for k in range(spaced_layer, layers):
                pos = p1 + tang * (j + 0.51) * width + normal * (k + 0.51) * height
                x, y = pos[0], pos[1]
                random_scale = random.uniform(0.9, 1.0)
                scaled_poly = scale(base_poly, random_scale, random_scale)
                translated_poly = translate(scaled_poly, x, y)
                rotated_poly = rotate(translated_poly, rotation, origin=(x, y))
                valid = poly.contains(rotated_poly)
                if valid:
                    for existing_poly in existing_polys:
                        if rotated_poly.intersects(existing_poly):
                            valid = False
                            break
                if valid:
                    positions_and_scales.append((x, y, random_scale))
                    existing_polys.append(rotated_poly)
                    count += 1

        if count > MODEL_LIMIT:
            break

    return positions_and_scales, existing_polys


def mix_fill_area(poly: Polygon, w1: float, h1: float, w2: float, h2: float, ratio1: float):
    pos1_and_scales, pos2_and_scales = [], []
    ref_ratio = ratio1 if ratio1 < 0.5 else 1 - ratio1
    poly_area = poly.area
    exterior = list(poly.exterior.coords[:-1])
    best_ratio, best_i, best_j = -1, None, None
    for i in range(len(exterior) - 2):
        for j in range(i + 2, len(exterior)):
            if i == 0 and j == len(exterior) - 1:
                continue
            poly1, poly2 = Polygon(exterior[i : j + 1]), Polygon(exterior[: i + 1] + exterior[j:])
            if poly1.is_valid and poly2.is_valid and (poly1.area + poly2.area) / poly_area < 1.01:
                ratio = poly1.area / poly_area
                ratio = ratio if ratio < 0.5 else 1 - ratio
                if abs(ratio - ref_ratio) < abs(best_ratio - ref_ratio):
                    best_ratio, best_i, best_j = ratio, i, j
    if best_i is None or best_j is None:
        if ratio1 > 0.5:
            pos1_and_scales, _ = random_fill_area(poly, w1, h1, ratio1, 0.8, 1.2, [])
        else:
            pos2_and_scales, _ = random_fill_area(poly, w2, h2, 1 - ratio1, 0.8, 1.2, [])
        return pos1_and_scales, pos2_and_scales
    poly1, poly2 = Polygon(exterior[best_i : best_j + 1]), Polygon(exterior[: best_i + 1] + exterior[best_j:])
    if abs(poly1.area / poly_area - ratio1) < abs(poly2.area / poly_area - ratio1):
        pos1_and_scales = full_fill_area(poly1, w1, h1)
        pos2_and_scales = full_fill_area(poly2, w2, h2)
    else:
        pos1_and_scales = full_fill_area(poly2, w1, h1)
        pos2_and_scales = full_fill_area(poly1, w2, h2)
    return pos1_and_scales, pos2_and_scales


def fill_area(poly: Polygon, code: int, model_data: dict):
    # - 水面：0000 平面
    # - 草地：0001 平面
    # - 花园：0010 低矮
    # - 花草：0011 平面，种带花的草
    # - 灌木：0100 低矮
    # - 灌草：0101 灌木围周围（不围满），其余种草
    # - 灌花：0110 低矮，灌木和花木按一定规则种
    # - 灌花草：0111 灌木围周围（不围满），其余种花草
    # - 树林：1000 高大，高密度的树
    # - 树草：1001 以草为主，零散种一些大树小树
    # - 树花：1010 以花木作为过渡，其余部分种密度一般的大树小树
    # - 树花草：1011 - 以花草为主，零散种一些大树小树
    # - 树灌：1100 以灌木作为过渡，其余部分种密度一般的大树小树
    # - 树灌草：1101 草-灌木-小树-大树
    # - 树灌花：1110 灌木+花木-小树-大树
    # - 树灌花草：1111 花草-灌木-小树-大树
    # print('code:', code)
    big_tree = model_data["types"]["big_tree"]
    small_tree = model_data["types"]["small_tree"]
    shrub = model_data["types"]["shrub"]
    flower = model_data["types"]["flower"]
    rock = model_data["types"]["rock"]
    grass = model_data["types"]["grass"]
    drygrass = model_data["types"]["drygrass"]
    result = []
    if code == 0:
        rock_type = random.choice(rock)
        model = model_data["objs"][rock_type]
        ref_size = model["ref_size"]
        positions_and_scales, _ = random_fill_area(poly, ref_size[0], ref_size[1], 0.01, 0.8, 1.2, [])
        for pos_and_scale in positions_and_scales:
            result.append((rock_type, pos_and_scale))
    elif code == 1:
        drygrass_type = random.choice(drygrass)
        model = model_data["objs"][drygrass_type]
        ref_size = model["ref_size"]
        positions_and_scales = random_fill_area_free(poly, ref_size[0], ref_size[1], 0.2)
        for pos_and_scale in positions_and_scales:
            result.append((drygrass_type, pos_and_scale))
    elif code == 2:
        flower_type = random.choice(flower)
        model = model_data["objs"][flower_type]
        ref_size = model["ref_size"]
        positions_and_scales = full_fill_area(poly, ref_size[0], ref_size[1])
        for pos_and_scale in positions_and_scales:
            result.append((flower_type, pos_and_scale))
    elif code == 3:
        flower_type = random.choice(flower)
        model = model_data["objs"][flower_type]
        ref_size = model["ref_size"]
        positions_and_scales, _ = random_fill_area(poly, ref_size[0], ref_size[1], 0.3, 0.8, 1.2, [])
        for pos_and_scale in positions_and_scales:
            result.append((flower_type, pos_and_scale))
    elif code == 4:
        shrub_type = random.choice(shrub)
        model = model_data["objs"][shrub_type]
        ref_size = model["ref_size"]
        positions_and_scales = full_fill_area(poly, ref_size[0], ref_size[1])
        for pos_and_scale in positions_and_scales:
            result.append((shrub_type, pos_and_scale))
    elif code == 5:
        shrub_type = random.choice(shrub)
        model = model_data["objs"][shrub_type]
        ref_size = model["ref_size"]
        positions_and_scales, _ = border_fill_area(poly, ref_size[0], ref_size[1], 3, 0)
        for pos_and_scale in positions_and_scales:
            result.append((shrub_type, pos_and_scale))
    elif code == 6:
        shrub_type, flower_type = random.choice(shrub), random.choice(flower)
        shrub_model, flower_model = model_data["objs"][shrub_type], model_data["objs"][flower_type]
        shrub_size, flower_size = shrub_model["ref_size"], flower_model["ref_size"]
        shrub_positions_and_scales, flower_positions_and_scales = mix_fill_area(
            poly, shrub_size[0], shrub_size[1], flower_size[0], flower_size[1], 0.5
        )
        for pos_and_scale in shrub_positions_and_scales:
            result.append((shrub_type, pos_and_scale))
        for pos_and_scale in flower_positions_and_scales:
            result.append((flower_type, pos_and_scale))
    elif code == 7:
        shrub_type, flower_type = random.choice(shrub), random.choice(flower)
        shrub_model, flower_model = model_data["objs"][shrub_type], model_data["objs"][flower_type]
        shrub_size, flower_size = shrub_model["ref_size"], flower_model["ref_size"]
        shrub_positions_and_scales, shrub_polys = border_fill_area(poly, shrub_size[0], shrub_size[1], 3, 0)
        flower_positions_and_scales, _ = random_fill_area(
            poly, flower_size[0], flower_size[1], 0.2, 0.8, 1.2, shrub_polys
        )
        for pos_and_scale in shrub_positions_and_scales:
            result.append((shrub_type, pos_and_scale))
        for pos_and_scale in flower_positions_and_scales:
            result.append((flower_type, pos_and_scale))
    elif code == 8:
        tree_type, grass_type = (
            random.choice(big_tree) if random.random() < 0.8 else random.choice(small_tree)
        ), random.choice(grass)
        tree_model, grass_model = model_data["objs"][tree_type], model_data["objs"][grass_type]
        tree_size, grass_size = tree_model["ref_size"], grass_model["ref_size"]
        tree_positions_and_scales, _ = random_fill_area(poly, tree_size[0], tree_size[1], 0.6, 0.8, 1.2, [])
        grass_positions_and_scales = random_fill_area_free(poly, grass_size[0], grass_size[1], 0.4, 0.2, 0.5)
        for pos_and_scale in tree_positions_and_scales:
            result.append((tree_type, pos_and_scale))
        for pos_and_scale in grass_positions_and_scales:
            result.append((grass_type, pos_and_scale))
    elif code == 9:
        tree_type = random.choice(big_tree) if random.random() < 0.8 else random.choice(small_tree)
        model = model_data["objs"][tree_type]
        ref_size = model["ref_size"]
        positions_and_scales, _ = random_fill_area(poly, ref_size[0], ref_size[1], 0.2, 0.8, 1.2, [])
        for pos_and_scale in positions_and_scales:
            result.append((tree_type, pos_and_scale))
    elif code == 10:
        tree_type, flower_type, grass_type = (
            random.choice(big_tree) if random.random() < 0.5 else random.choice(small_tree),
            random.choice(flower),
            random.choice(grass),
        )
        tree_model, flower_model, grass_model = (
            model_data["objs"][tree_type],
            model_data["objs"][flower_type],
            model_data["objs"][grass_type],
        )
        tree_size, flower_size, grass_size = tree_model["ref_size"], flower_model["ref_size"], grass_model["ref_size"]
        flower_positions_and_scales, flower_polys = border_fill_area(poly, flower_size[0], flower_size[1], 6, 0)
        tree_positions_and_scales, _ = random_fill_area(poly, tree_size[0], tree_size[1], 0.6, 0.8, 1.2, [])
        grass_positions_and_scales = random_fill_area_free(poly, grass_size[0], grass_size[1], 0.4, 0.2, 0.5)
        for pos_and_scale in tree_positions_and_scales:
            result.append((tree_type, pos_and_scale))
        for pos_and_scale in flower_positions_and_scales:
            result.append((flower_type, pos_and_scale))
        for pos_and_scale in grass_positions_and_scales:
            result.append((grass_type, pos_and_scale))
    elif code == 11:
        tree_type, flower_type = (
            random.choice(big_tree) if random.random() < 0.5 else random.choice(small_tree)
        ), random.choice(flower)
        tree_model, flower_model = model_data["objs"][tree_type], model_data["objs"][flower_type]
        tree_size, flower_size = tree_model["ref_size"], flower_model["ref_size"]
        tree_positions_and_scales, tree_polys = random_fill_area(poly, tree_size[0], tree_size[1], 0.1, 0.8, 1.2, [])
        flower_positions_and_scales, _ = random_fill_area(poly, flower_size[0], flower_size[1], 0.2, 0.8, 1.2, [])
    elif code == 12:
        tree_type, shrub_type, grass_type = (
            random.choice(big_tree) if random.random() < 0.8 else random.choice(small_tree),
            random.choice(shrub),
            random.choice(grass),
        )
        tree_model, shrub_model, grass_model = (
            model_data["objs"][tree_type],
            model_data["objs"][shrub_type],
            model_data["objs"][grass_type],
        )
        tree_size, shrub_size, grass_size = tree_model["ref_size"], shrub_model["ref_size"], grass_model["ref_size"]
        shrub_positions_and_scales, shrub_polys = border_fill_area(poly, shrub_size[0], shrub_size[1], 3, 0)
        tree_positions_and_scales, _ = random_fill_area(poly, tree_size[0], tree_size[1], 0.6, 0.8, 1.2, shrub_polys)
        grass_positions_and_scales = random_fill_area_free(poly, grass_size[0], grass_size[1], 0.4, 0.2, 0.5)
        for pos_and_scale in tree_positions_and_scales:
            result.append((tree_type, pos_and_scale))
        for pos_and_scale in shrub_positions_and_scales:
            result.append((shrub_type, pos_and_scale))
        for pos_and_scale in grass_positions_and_scales:
            result.append((grass_type, pos_and_scale))
    elif code == 13:
        tree_type, shrub_type = (
            random.choice(big_tree) if random.random() < 0.5 else random.choice(small_tree)
        ), random.choice(shrub)
        tree_model, shrub_model = model_data["objs"][tree_type], model_data["objs"][shrub_type]
        tree_size, shrub_size = tree_model["ref_size"], shrub_model["ref_size"]
        shrub_positions_and_scales, shrub_polys = border_fill_area(poly, shrub_size[0], shrub_size[1], 3, 1)
        tree_positions_and_scales, _ = random_fill_area(poly, tree_size[0], tree_size[1], 0.6, 0.8, 1.2, shrub_polys)
        for pos_and_scale in tree_positions_and_scales:
            result.append((tree_type, pos_and_scale))
        for pos_and_scale in shrub_positions_and_scales:
            result.append((shrub_type, pos_and_scale))
    elif code == 14:
        tree_type, shrub_type, flower_type, grass_type = (
            random.choice(big_tree) if random.random() < 0.5 else random.choice(small_tree),
            random.choice(shrub),
            random.choice(flower),
            random.choice(grass),
        )
        tree_model, shrub_model, flower_model, grass_model = (
            model_data["objs"][tree_type],
            model_data["objs"][shrub_type],
            model_data["objs"][flower_type],
            model_data["objs"][grass_type],
        )
        tree_size, shrub_size, flower_size, grass_size = (
            tree_model["ref_size"],
            shrub_model["ref_size"],
            flower_model["ref_size"],
            grass_model["ref_size"],
        )
        flower_layers = int(min(shrub_size[0] * 2 / flower_size[0], shrub_size[1] * 2 / flower_size[1]))
        flower_positions_and_scales, flower_polys = border_fill_area(
            poly, flower_size[0], flower_size[1], flower_layers, 0
        )
        shrub_positions_and_scales, shrub_polys = border_fill_area(poly, shrub_size[0], shrub_size[1], 4, 2)
        tree_positions_and_scales, _ = random_fill_area(poly, tree_size[0], tree_size[1], 0.6, 0.8, 1.2, shrub_polys)
        grass_positions_and_scales = random_fill_area_free(poly, grass_size[0], grass_size[1], 0.4, 0.2, 0.5)
        for pos_and_scale in tree_positions_and_scales:
            result.append((tree_type, pos_and_scale))
        for pos_and_scale in shrub_positions_and_scales:
            result.append((shrub_type, pos_and_scale))
        for pos_and_scale in flower_positions_and_scales:
            result.append((flower_type, pos_and_scale))
        for pos_and_scale in grass_positions_and_scales:
            result.append((grass_type, pos_and_scale))
    else:
        tree_type, shrub_type, flower_type = (
            random.choice(big_tree) if random.random() < 0.5 else random.choice(small_tree),
            random.choice(shrub),
            random.choice(flower),
        )
        tree_model, shrub_model, flower_model = (
            model_data["objs"][tree_type],
            model_data["objs"][shrub_type],
            model_data["objs"][flower_type],
        )
        tree_size, shrub_size, flower_size = tree_model["ref_size"], shrub_model["ref_size"], flower_model["ref_size"]
        shrub_positions_and_scales, shrub_polys = border_fill_area(poly, shrub_size[0], shrub_size[1], 3, 1)
        tree_positions_and_scales, tree_polys = random_fill_area(
            poly, tree_size[0], tree_size[1], 0.1, 0.8, 1.2, shrub_polys
        )
        flower_positions_and_scales, _ = random_fill_area(
            poly, flower_size[0], flower_size[1], 0.2, 0.8, 1.2, shrub_polys
        )
        for pos_and_scale in tree_positions_and_scales:
            result.append((tree_type, pos_and_scale))
        for pos_and_scale in shrub_positions_and_scales:
            result.append((shrub_type, pos_and_scale))
        for pos_and_scale in flower_positions_and_scales:
            result.append((flower_type, pos_and_scale))

    return result


def fill_areas(graph: nx.Graph, circuits: List[list], main_edges: List[tuple], codes: List[int], model_data: dict):
    results, fence_positions_and_forwards = [], []
    fence = model_data["types"]["fence"]
    fence_type = random.choice(fence)
    fence_model = model_data["objs"][fence_type]
    fence_length = max(fence_model["ref_size"][0], fence_model["ref_size"][1])
    protected_edges = []
    for i in range(len(circuits)):
        result = []
        coords = [graph.nodes[node]["pos"] for node in circuits[i]]
        polys = Polygon(coords).simplify(0, False)
        for j in range(len(coords)):
            p1, p2 = coords[j], coords[(j + 1) % len(coords)]
            road_width = SUB_ROAD_WIDTH
            if tuple_in_list((circuits[i][j], circuits[i][(j + 1) % len(circuits[i])]), main_edges):
                road_width = MAIN_ROAD_WIDTH
            p1, p2 = vec(p1[0], p1[1]), vec(p2[0], p2[1])
            tangent = norm(p2 - p1)
            pointList = []
            for k in range(SEMICIRCLE_PARTS + 1):
                pointList.append(p1 + rot(tangent, k * pi / SEMICIRCLE_PARTS + pi / 2) * road_width / 2)
            for k in range(SEMICIRCLE_PARTS + 1):
                pointList.append(p2 + rot(tangent, k * pi / SEMICIRCLE_PARTS - pi / 2) * road_width / 2)
            road_poly = Polygon(pointList)
            polys = polys.difference(road_poly)

        polys = (
            [polys.simplify(0.1, True)]
            if isinstance(polys, Polygon)
            else [poly.simplify(0.1, True) for poly in polys.geoms]
        )
        protected_flag = False
        for poly in polys:
            if not (isinstance(poly, Polygon) and len(list(poly.bounds)) == 4):
                result.append([])
                continue
            fill_result = fill_area(poly, codes[i], model_data)
            result.append(fill_result)
            coords = poly.exterior.coords
            add_fence = False
            if (codes[i] == 2 or codes[i] == 4 or codes[i] == 6) and len(coords) // 2 < 4 and poly.length < 32:
                add_fence = True
            if codes[i] > 8 and len(coords) // 2 < 4 and poly.length < 40:
                for tup in fill_result:
                    if (
                        model_data["objs"][tup[0]]["type"] == "big_tree"
                        or model_data["objs"][tup[0]]["type"] == "small_tree"
                    ):
                        add_fence = True
                        break
            protected_nodes = []
            if add_fence:
                protected_flag = True
                for j in range(len(coords)):
                    p1, p2 = coords[j], coords[(j + 1) % len(coords)]
                    fence_positions_and_forwards += fill_fence(p1, p2, fence_length, fence_type)
        results.append(result)
        if protected_flag:
            for j in range(len(circuits[i])):
                protected_edges.append((circuits[i][j], circuits[i][(j + 1) % len(circuits[i])]))

    return results, fence_positions_and_forwards, protected_edges


def solve_circle(p1_, p2_, t_):
    # given two points p1, p2 and the tangent line t at p1, find the center of the circle
    p1, p2, t = vec(p1_[0], p1_[1]), vec(p2_[0], p2_[1]), vec(t_[0], t_[1])
    mid = (p1 + p2) / 2
    length = get_length(p1, p2)
    angle = angle_between(t, p2 - p1)
    t_normal = norm(rot(t, pi / 2))
    if angle > pi / 2:
        angle = pi - angle
    if angle_between(t_normal, p2 - p1) > pi / 2:
        t_normal = -t_normal
    radius = length / (2 * sin(angle))
    center = p1 + radius * t_normal
    # print(p1, p2, t, center)
    ang1 = atan2(p1[1] - center[1], p1[0] - center[0])
    ang2 = atan2(p2[1] - center[1], p2[0] - center[0])
    if ang1 - ang2 > pi:
        ang2 += 2 * pi
    elif ang2 - ang1 > pi:
        ang1 += 2 * pi
    result_points = []
    for i in range(1, CURVE_PARTS):
        ang = ang1 + (ang2 - ang1) * i / CURVE_PARTS
        x = center[0] + radius * cos(ang)
        y = center[1] + radius * sin(ang)
        result_points.append((x, y))
    return result_points


def fill_areas_curve(
    graph: nx.Graph,
    circuits: List[list],
    chosen_edges: List[tuple],
    main_edges: List[tuple],
    protected_edges: List[int],
):
    # print('circuits start:', circuits)
    expand_edges = []
    for edge in chosen_edges:
        if (not tuple_in_list(edge, protected_edges)) and (not is_border_edge(graph, edge)):
            expand_edges.append(edge)
    expand_times = (int)(len(expand_edges) / 2)
    for t in range(expand_times):
        weights, total_weight = [], 0
        for i in range(len(expand_edges)):
            p1, p2 = graph.nodes[expand_edges[i][0]]["pos"], graph.nodes[expand_edges[i][1]]["pos"]
            weight = get_length(p1, p2)
            weights.append(weight)
            total_weight += weight**2
        rand = random.uniform(0, total_weight)
        edge = expand_edges[-1]
        for i in range(len(expand_edges)):
            if rand < weights[i] ** 2:
                edge = expand_edges[i]
                break
            else:
                rand -= weights[i] ** 2
        p1, p2 = graph.nodes[edge[0]]["pos"], graph.nodes[edge[1]]["pos"]
        p1, p2 = vec(p1[0], p1[1]), vec(p2[0], p2[1])
        normal = norm(rot(p2 - p1, pi / 2))
        bias = random.uniform(-0.6, 0.6) * sqrt(weights[i])
        mid = (p1 + p2) / 2 + normal * bias
        idx = len(graph.nodes)

        # modify
        graph.add_node(idx, pos=(mid[0], mid[1]))
        remove_edge(graph, (edge[0], edge[1]))
        graph.add_edge(edge[0], idx)
        graph.add_edge(idx, edge[1])
        remove_tuple(edge, expand_edges)
        expand_edges.append((edge[0], idx))
        expand_edges.append((idx, edge[1]))
        remove_tuple(edge, chosen_edges)
        chosen_edges.append((edge[0], idx))
        chosen_edges.append((idx, edge[1]))
        if tuple_in_list(edge, main_edges):
            remove_tuple(edge, main_edges)
            main_edges.append((edge[0], idx))
            main_edges.append((idx, edge[1]))
        for i in range(len(circuits)):
            for j in range(len(circuits[i])):
                if (circuits[i][j] == edge[0] and circuits[i][(j + 1) % len(circuits[i])] == edge[1]) or (
                    circuits[i][j] == edge[1] and circuits[i][(j + 1) % len(circuits[i])] == edge[0]
                ):
                    circuits[i].insert(j + 1, idx)
                    break

    # print('circuits before:', circuits)
    # print('chosen edges before:', chosen_edges)
    subgraph = nx.Graph()
    subgraph.add_nodes_from(graph.nodes)
    subgraph.add_edges_from(chosen_edges)
    expand_nodes = []
    for edge in chosen_edges:
        if (not tuple_in_list(edge, protected_edges)) and (not is_border_edge(graph, edge)):
            if (not edge[0] in expand_nodes) and subgraph.degree(edge[0]) == 2:
                expand_nodes.append(edge[0])
            if (not edge[1] in expand_nodes) and subgraph.degree(edge[1]) == 2:
                expand_nodes.append(edge[1])
    for node in expand_nodes:
        if subgraph.degree(node) != 2:
            continue
        n1, n2 = subgraph.neighbors(node)
        p0, p1, p2 = graph.nodes[node]["pos"], graph.nodes[n1]["pos"], graph.nodes[n2]["pos"]
        p0, p1, p2 = vec(p0[0], p0[1]), vec(p1[0], p1[1]), vec(p2[0], p2[1])
        is_main = tuple_in_list((node, n1), main_edges)
        angle = angle_between(p1 - p0, p2 - p0)
        if angle > pi * 2 / 3:
            continue
        string1, string2 = [node, n1], [node, n2]
        while True:
            n11, n12 = string1[-1], string1[-2]
            p11, p12 = graph.nodes[n11]["pos"], graph.nodes[n12]["pos"]
            if subgraph.degree(n11) != 2:
                break
            if get_length(graph.nodes[n11]["pos"], p0) > 4:
                break
            neighbors = list(subgraph.neighbors(n11))
            next = neighbors[0] if neighbors[0] != n12 else neighbors[1]
            p13 = graph.nodes[next]["pos"]
            p11, p12, p13 = vec(p11[0], p11[1]), vec(p12[0], p12[1]), vec(p13[0], p13[1])
            if angle_between(p13 - p11, p11 - p12) > pi / 3:
                break
            string1.append(next)
        while True:
            n11, n12 = string2[-1], string2[-2]
            p11, p12 = graph.nodes[n11]["pos"], graph.nodes[n12]["pos"]
            if subgraph.degree(n11) != 2:
                break
            if get_length(graph.nodes[n11]["pos"], p0) > 4:
                break
            neighbors = list(subgraph.neighbors(n11))
            next = neighbors[0] if neighbors[0] != n12 else neighbors[1]
            p13 = graph.nodes[next]["pos"]
            p11, p12, p13 = vec(p11[0], p11[1]), vec(p12[0], p12[1]), vec(p13[0], p13[1])
            if angle_between(p13 - p11, p11 - p12) > pi / 3:
                break
            string2.append(next)
        if string1[-1] == string2[-1]:
            if len(string1) > len(string2):
                string1 = string1[:-1]
            else:
                string2 = string2[:-1]
        p1, p2 = graph.nodes[string1[-1]]["pos"], graph.nodes[string2[-1]]["pos"]
        p1, p2 = vec(p1[0], p1[1]), vec(p2[0], p2[1])
        if get_length(p1, p0) < get_length(p2, p0):
            angle = angle_between(p2 - p1, p2 - p0)
        else:
            angle = angle_between(p2 - p1, p1 - p0)
        if angle > pi / 2:
            angle = pi - angle
        if angle < pi / 12:
            continue
        for i in range(len(string1) - 1):
            remove_edge(graph, (string1[i], string1[i + 1]))
            remove_edge(subgraph, (string1[i], string1[i + 1]))
            remove_tuple((string1[i], string1[i + 1]), chosen_edges)
            if tuple_in_list((string1[i], string1[i + 1]), main_edges):
                remove_tuple((string1[i], string1[i + 1]), main_edges)
        for i in range(len(string2) - 1):
            remove_edge(graph, (string2[i], string2[i + 1]))
            remove_edge(subgraph, (string2[i], string2[i + 1]))
            remove_tuple((string2[i], string2[i + 1]), chosen_edges)
            if tuple_in_list((string2[i], string2[i + 1]), main_edges):
                remove_tuple((string2[i], string2[i + 1]), main_edges)
        check = []
        for i in range(len(circuits)):
            check_flag = False
            j = 0
            while j < len(circuits[i]):
                if (
                    (circuits[i][j] != string1[-1])
                    and (circuits[i][j] != string2[-1])
                    and ((circuits[i][j] in string1) or (circuits[i][j] in string2))
                ):
                    circuits[i].remove(circuits[i][j])
                    check_flag = True
                else:
                    j += 1
            if check_flag:
                check.append(i)

        idx = len(graph.nodes)
        if get_length(p1, p0) < get_length(p2, p0):
            points = solve_circle(p2, p1, p2 - p0)
            # print([p2] + points + [p1])
            for i in range(len(points)):
                graph.add_node(idx + i, pos=(points[i][0], points[i][1]))
                subgraph.add_node(idx + i, pos=(points[i][0], points[i][1]))
                if i == 0:
                    graph.add_edge(string2[-1], idx + i)
                    subgraph.add_edge(string2[-1], idx + i)
                    chosen_edges.append((string2[-1], idx + i))
                    if is_main:
                        main_edges.append((string2[-1], idx + i))
                elif i > 0:
                    graph.add_edge(idx + i - 1, idx + i)
                    subgraph.add_edge(idx + i - 1, idx + i)
                    chosen_edges.append((idx + i - 1, idx + i))
                    if is_main:
                        main_edges.append((idx + i - 1, idx + i))
                if i == len(points) - 1:
                    graph.add_edge(idx + i, string1[-1])
                    subgraph.add_edge(idx + i, string1[-1])
                    chosen_edges.append((idx + i, string1[-1]))
                    if is_main:
                        main_edges.append((idx + i, string1[-1]))
            for i in range(len(circuits)):
                if not i in check:
                    continue
                if circuits[i][0] == string1[-1] and circuits[i][-1] == string2[-1]:
                    circuits[i].extend([idx + i for i in range(len(points))])
                elif circuits[i][0] == string2[-1] and circuits[i][-1] == string1[-1]:
                    circuits[i].extend([idx + i for i in range(len(points) - 1, -1, -1)])
                else:
                    for j in range(len(circuits[i]) - 1):
                        if circuits[i][j] == string1[-1] and circuits[i][j + 1] == string2[-1]:
                            for k in range(len(points)):
                                circuits[i].insert(j + 1 + k, idx + len(points) - 1 - k)
                            break
                        elif circuits[i][j] == string2[-1] and circuits[i][j + 1] == string1[-1]:
                            for k in range(len(points)):
                                circuits[i].insert(j + 1 + k, idx + k)
                            break
        else:
            points = solve_circle(p1, p2, p1 - p0)
            # print([p1] + points + [p2])
            for i in range(len(points)):
                graph.add_node(idx + i, pos=(points[i][0], points[i][1]))
                subgraph.add_node(idx + i, pos=(points[i][0], points[i][1]))
                if i == 0:
                    graph.add_edge(string1[-1], idx + i)
                    subgraph.add_edge(string1[-1], idx + i)
                    chosen_edges.append((string1[-1], idx + i))
                    if is_main:
                        main_edges.append((string1[-1], idx + i))
                elif i > 0:
                    graph.add_edge(idx + i - 1, idx + i)
                    subgraph.add_edge(idx + i - 1, idx + i)
                    chosen_edges.append((idx + i - 1, idx + i))
                    if is_main:
                        main_edges.append((idx + i - 1, idx + i))
                if i == len(points) - 1:
                    graph.add_edge(idx + i, string2[-1])
                    subgraph.add_edge(idx + i, string2[-1])
                    chosen_edges.append((idx + i, string2[-1]))
                    if is_main:
                        main_edges.append((idx + i, string2[-1]))
            for i in range(len(circuits)):
                if not i in check:
                    continue
                if circuits[i][0] == string2[-1] and circuits[i][-1] == string1[-1]:
                    circuits[i].extend([idx + i for i in range(len(points))])
                elif circuits[i][0] == string1[-1] and circuits[i][-1] == string2[-1]:
                    circuits[i].extend([idx + i for i in range(len(points) - 1, -1, -1)])
                else:
                    for j in range(len(circuits[i]) - 1):
                        if circuits[i][j] == string2[-1] and circuits[i][j + 1] == string1[-1]:
                            for k in range(len(points)):
                                circuits[i].insert(j + 1 + k, idx + len(points) - 1 - k)
                            break
                        elif circuits[i][j] == string1[-1] and circuits[i][j + 1] == string2[-1]:
                            for k in range(len(points)):
                                circuits[i].insert(j + 1 + k, idx + k)
                            break
    # print('circuits after:', circuits)
    # print('chosen edges after:', chosen_edges)
    return graph, circuits, chosen_edges, main_edges


def essential_points_evaluate(points: List[tuple], borders: List[tuple]):
    nearest_dis = []
    if len(points) > 1:
        for i in range(len(points)):
            dis = float("inf")
            for j in range(len(points)):
                if i != j:
                    dis = min(dis, sqrt((points[i][0] - points[j][0]) ** 2 + (points[i][1] - points[j][1]) ** 2))
            nearest_dis.append(dis)
    for i in range(len(borders)):
        dis = float("inf")
        for j in range(len(points)):
            dis = min(dis, sqrt((borders[i][0] - points[j][0]) ** 2 + (borders[i][1] - points[j][1]) ** 2))
        nearest_dis.append(dis)
    # if isnan(np.var(nearest_dis)) or isnan(np.mean(nearest_dis)):
    #     print(points, nearest_dis)
    return 10 - len(points) + np.var(nearest_dis) / np.mean(nearest_dis)


def add_elements(graph: nx.Graph, circuits: List[list], main_edges: List[tuple], codes: List[int], model_data: dict):
    bench = model_data["types"]["bench"]
    bench_type = random.choice(bench)
    bench_model = model_data["objs"][bench_type]
    bench_length, bench_width = max(bench_model["ref_size"][0], bench_model["ref_size"][1]), min(
        bench_model["ref_size"][0], bench_model["ref_size"][1]
    )

    bridge_edges = []
    for i in range(len(circuits)):
        for j in range(i + 1, len(circuits)):
            if codes[i] != 0 or codes[j] != 0:
                continue
            intersection = set(circuits[i]) & set(circuits[j])
            for k in range(len(circuits[i]) - 1):
                if circuits[i][k] in intersection and circuits[i][k + 1] in intersection:
                    bridge_edges.append((circuits[i][k], circuits[i][k + 1]))

    # add benches
    main_edge_and_lengths = []
    for main_edge in main_edges:
        if tuple_in_list(main_edge, bridge_edges):
            continue
        if is_border_edge(graph, main_edge):
            continue
        p1, p2 = graph.nodes[main_edge[0]]["pos"], graph.nodes[main_edge[1]]["pos"]
        length = get_length(p1, p2)
        if length > bench_length:
            main_edge_and_lengths.append((length, main_edge))
    bench_positions_and_forwards = []
    if len(main_edge_and_lengths) > 0:
        main_edge_and_lengths.sort(key=lambda x: x[0], reverse=True)
        longest_nums = min(max(len(main_edge_and_lengths) // 3, 4), len(main_edge_and_lengths))
        longest_edges = [main_edge_and_lengths[i][1] for i in range(longest_nums)]
        bench_num = min((site_width + site_height) // 30, longest_nums)
        count = 0
        best_score = float("inf")
        border_points = site_bound
        for edge_idxes in itertools.permutations([k for k in range(longest_nums)], bench_num):
            edges, lengths = [longest_edges[k] for k in edge_idxes], [main_edge_and_lengths[k][0] for k in edge_idxes]
            for repeat in range(100):
                positions_and_forwards = []
                for i in range(bench_num):
                    p1, p2 = vec(graph.nodes[edges[i][0]]["pos"][0], graph.nodes[edges[i][0]]["pos"][1]), vec(
                        graph.nodes[edges[i][1]]["pos"][0], graph.nodes[edges[i][1]]["pos"][1]
                    )
                    toward = get_toward(p1, p2)
                    tangent = norm(p2 - p1)
                    angle = pi / 2 - atan2(tangent[1], tangent[0])
                    normal = vec(tangent[1], -tangent[0])
                    length = lengths[i]
                    side = random.choice([1, -1])
                    forward = angle - pi / 2 if side == 1 else angle + pi / 2
                    if length > bench_length * 3 + MAIN_ROAD_WIDTH:
                        start_length = random.uniform(
                            MAIN_ROAD_WIDTH / 2, length - bench_length * 2.5 - MAIN_ROAD_WIDTH / 2
                        )
                        pos1 = (
                            p1
                            + tangent * (start_length + bench_length * 0.5)
                            + normal * side * (MAIN_ROAD_WIDTH - bench_width) / 2
                        )
                        pos2 = (
                            p1
                            + tangent * (start_length + bench_length * 2)
                            + normal * side * (MAIN_ROAD_WIDTH - bench_width) / 2
                        )
                        positions_and_forwards.append((pos1[0], pos1[1], forward, bench_type))
                        positions_and_forwards.append((pos2[0], pos2[1], forward, bench_type))
                    elif length > bench_length + MAIN_ROAD_WIDTH:
                        start_length = random.uniform(MAIN_ROAD_WIDTH / 2, length - bench_length - MAIN_ROAD_WIDTH / 2)
                        pos = (
                            p1
                            + tangent * (start_length + bench_length * 0.5)
                            + normal * side * (MAIN_ROAD_WIDTH - bench_width) / 2
                        )
                        positions_and_forwards.append((pos[0], pos[1], forward, bench_type))
                essential_points = [
                    (positions_and_forwards[i][0], positions_and_forwards[i][1])
                    for i in range(len(positions_and_forwards))
                ]
                if len(essential_points) == 0:
                    continue
                score = essential_points_evaluate(essential_points, border_points)
                if score < best_score:
                    best_score = score
                    bench_positions_and_forwards = positions_and_forwards
            count += 1
            if count > 500:
                break

    return bench_positions_and_forwards


def get_spaces(graph: nx.Graph, chosen_edges: List[tuple], road_width: int):
    poly = deepcopy(site_poly)
    for edge in chosen_edges:
        x1, x2, y1, y2 = (
            graph.nodes[edge[0]]["pos"][0],
            graph.nodes[edge[1]]["pos"][0],
            graph.nodes[edge[0]]["pos"][1],
            graph.nodes[edge[1]]["pos"][1],
        )
        dx, dy = x2 - x1, y2 - y1
        x1, x2, y1, y2 = x1 - dx * EPS, x2 + dx * EPS, y1 - dy * EPS, y2 + dy * EPS
        norm_vec = norm(vec(y2 - y1, x1 - x2))
        road_poly = Polygon(
            [
                (x1 + norm_vec[0] * road_width / 2, y1 + norm_vec[1] * road_width / 2),
                (x2 + norm_vec[0] * road_width / 2, y2 + norm_vec[1] * road_width / 2),
                (x2 - norm_vec[0] * road_width / 2, y2 - norm_vec[1] * road_width / 2),
                (x1 - norm_vec[0] * road_width / 2, y1 - norm_vec[1] * road_width / 2),
            ]
        )
        poly = poly.difference(road_poly)
    return poly


def fill_texture(poly: Polygon):
    new_poly = deepcopy(poly)
    new_poly = new_poly.simplify(0, False)
    results = []
    xl, yl, xh, yh = new_poly.bounds
    x, y = xl + 0.01, yl + 0.01
    while x + 0.2 < xh:
        width = min(0.4, xh - x - 0.01)
        while y + 0.2 < yh:
            height = None
            success = False
            for i in range(6):
                height = 1.2 - i * 0.2
                points = [Point(x, y), Point(x + width, y), Point(x + width, y + height), Point(x, y + height)]
                all_inside = True
                for point in points:
                    if not new_poly.contains(point):
                        all_inside = False
                        break
                if all_inside:
                    success = True
                    break
            if success:
                results.append((x, y, width, height))
            y += height
        x += width
        y = yl + 0.01
    return results


def get_room(poly: Polygon, area_type: str, layer: int, dir_name: str, idx: int):
    pointList = [np.array(point) for point in poly.exterior.coords[:-1]]
    if len(pointList) < 3:
        return None
    interiors = [list(interior.coords[:-1]) for interior in poly.interiors]
    room = {}
    room["areaShape"] = [[(float)(point[0]), (float)(point[1])] for point in pointList]
    room["interior"] = [[[(float)(point[0]), (float)(point[1])] for point in interior] for interior in interiors]
    # room['roomNorm'] = []
    # for k in range(len(pointList)):
    #     n = norm(rot(pointList[(k + 1) % len(pointList)] - pointList[k], -pi / 2))
    #     room['roomNorm'].append([(float)(n[0]), (float)(n[1])])
    # room['roomOrient'] = [
    #     pi / 2 - atan2(room['roomNorm'][k][1], room['roomNorm'][k][0]) for k in range(len(room['roomNorm']))
    # ]
    # room['roomShapeBBox'] = {
    #     'min': [min(point[0] for point in pointList),
    #             min(point[1] for point in pointList)],
    #     'max': [max(point[0] for point in pointList),
    #             max(point[1] for point in pointList)]
    # }
    texture_name = ""
    if area_type == "water":
        texture_name = "13"
    elif area_type == "garden":
        texture_name = "flower01"
    elif area_type == "earth":
        texture_name = "earth01"
    elif area_type == "grass":
        texture_name = "grass02"
    elif area_type == "road1":
        texture_name = "road01"
    elif area_type == "road2":
        texture_name = "road02"

    room["bbox"] = {
        "min": [min(point[0] for point in pointList), 0, min(point[1] for point in pointList)],
        "max": [max(point[0] for point in pointList), 3, max(point[1] for point in pointList)],
    }

    objectize(pointList, interiors, texture_name, layer, dir_name, idx)
    room["areaType"] = area_type
    room["layer"] = layer
    room["modelId"] = str(idx)
    room["objList"] = []

    return room


# def output_scene_empty(name: str):
#     out = {}
#     out["origin"] = "{}_{}_{}_0".format(site_width, site_height, name)
#     out["id"] = "{}_{}_{}_0".format(site_width, site_height, name)
#     out["bbox"] = {"min": [site_xl, 0, site_yl], "max": [site_xh, 3, site_yh]}
#     out["up"] = [0, 1, 0]
#     out["front"] = [0, 0, 1]
#     rooms = []
#     empty_poly = deepcopy(site_poly)
#     room = get_room(empty_poly, "earth", 0, "log_outputs/{}_{}_{}_0".format(site_width, site_height, name), 0)
#     rooms.append(room)

#     out["rooms"] = rooms
#     out["PerspectiveCamera"] = autoPerspectiveCamera(out)
#     with open("log_outputs/{}_{}_{}_0.json".format(site_width, site_height, name), "w") as out_f:
#         json.dump(out, out_f)


# def output_scene_step2(graph: nx.Graph, circuits: List[list], name: str):
#     out = {}
#     out["origin"] = "{}_{}_{}_1".format(site_width, site_height, name)
#     out["id"] = "{}_{}_{}_1".format(site_width, site_height, name)
#     out["bbox"] = {"min": [site_xl, 0, site_yl], "max": [site_xh, 3, site_yh]}
#     out["up"] = [0, 1, 0]
#     out["front"] = [0, 0, 1]
#     rooms = []
#     room_count = 0
#     road_polys = None
#     for i in range(len(circuits)):
#         coords = [graph.nodes[node]["pos"] for node in circuits[i]]
#         polys = Polygon(coords).simplify(0, False)
#         for j in range(len(coords)):
#             p1, p2 = coords[j], coords[(j + 1) % len(coords)]
#             road_width = 0.5
#             p1, p2 = vec(p1[0], p1[1]), vec(p2[0], p2[1])
#             tangent = norm(p2 - p1)
#             pointList = []
#             for k in range(SEMICIRCLE_PARTS + 1):
#                 pointList.append(p1 + rot(tangent, k * pi / SEMICIRCLE_PARTS + pi / 2) * road_width / 2)
#             for k in range(SEMICIRCLE_PARTS + 1):
#                 pointList.append(p2 + rot(tangent, k * pi / SEMICIRCLE_PARTS - pi / 2) * road_width / 2)
#             road_poly = Polygon(pointList)
#             polys = polys.difference(road_poly)
#             if road_polys is None:
#                 road_polys = road_poly
#             else:
#                 road_polys = road_polys.union(road_poly)

#         polys = [polys] if isinstance(polys, Polygon) else list(polys.geoms)
#         for j in range(len(polys)):
#             poly = polys[j]
#             room = get_room(
#                 poly.simplify(0, False),
#                 "earth",
#                 0,
#                 "log_outputs/{}_{}_{}_1".format(site_width, site_height, name),
#                 room_count,
#             )
#             if room is None:
#                 continue
#             rooms.append(room)
#             room_count += 1

#     road_polys = [road_polys] if isinstance(road_polys, Polygon) else list(road_polys.geoms)
#     for road_poly in road_polys:
#         room = get_room(
#             road_poly.simplify(0, False),
#             "road1",
#             2,
#             "log_outputs/{}_{}_{}_1".format(site_width, site_height, name),
#             room_count,
#         )
#         rooms.append(room)
#         room_count += 1

#     out["rooms"] = rooms
#     out["PerspectiveCamera"] = autoPerspectiveCamera(out)
#     with open("log_outputs/{}_{}_{}_1.json".format(site_width, site_height, name), "w") as out_f:
#         json.dump(out, out_f)


# def output_scene_step3(graph: nx.Graph, circuits: List[list], main_edges: List[tuple], name: str):
#     out = {}
#     out["origin"] = "{}_{}_{}_2".format(site_width, site_height, name)
#     out["id"] = "{}_{}_{}_2".format(site_width, site_height, name)
#     out["bbox"] = {"min": [site_xl, 0, site_yl], "max": [site_xh, 3, site_yh]}
#     out["up"] = [0, 1, 0]
#     out["front"] = [0, 0, 1]
#     rooms = []
#     room_count = 0
#     main_road_polys, sub_road_polys = None, None
#     for i in range(len(circuits)):
#         coords = [graph.nodes[node]["pos"] for node in circuits[i]]
#         polys = Polygon(coords).simplify(0, False)
#         for j in range(len(coords)):
#             p1, p2 = coords[j], coords[(j + 1) % len(coords)]
#             is_main = tuple_in_list((circuits[i][j], circuits[i][(j + 1) % len(circuits[i])]), main_edges)
#             road_width = MAIN_ROAD_WIDTH if is_main else SUB_ROAD_WIDTH
#             p1, p2 = vec(p1[0], p1[1]), vec(p2[0], p2[1])
#             tangent = norm(p2 - p1)
#             pointList = []
#             for k in range(SEMICIRCLE_PARTS + 1):
#                 pointList.append(p1 + rot(tangent, k * pi / SEMICIRCLE_PARTS + pi / 2) * road_width / 2)
#             for k in range(SEMICIRCLE_PARTS + 1):
#                 pointList.append(p2 + rot(tangent, k * pi / SEMICIRCLE_PARTS - pi / 2) * road_width / 2)
#             road_poly = Polygon(pointList)
#             polys = polys.difference(road_poly)
#             if is_main:
#                 if main_road_polys is None:
#                     main_road_polys = road_poly
#                 else:
#                     main_road_polys = main_road_polys.union(road_poly)
#             else:
#                 if sub_road_polys is None:
#                     sub_road_polys = road_poly
#                 else:
#                     sub_road_polys = sub_road_polys.union(road_poly)

#         polys = [polys] if isinstance(polys, Polygon) else list(polys.geoms)
#         for j in range(len(polys)):
#             poly = polys[j]
#             room = get_room(
#                 poly.simplify(0, False),
#                 "earth",
#                 0,
#                 "log_outputs/{}_{}_{}_2".format(site_width, site_height, name),
#                 room_count,
#             )
#             if room is None:
#                 continue
#             rooms.append(room)
#             room_count += 1

#     main_road_polys = [main_road_polys] if isinstance(main_road_polys, Polygon) else list(main_road_polys.geoms)
#     sub_road_polys = [sub_road_polys] if isinstance(sub_road_polys, Polygon) else list(sub_road_polys.geoms)
#     for main_road_poly in main_road_polys:
#         room = get_room(
#             main_road_poly.simplify(0, False),
#             "road1",
#             2,
#             "log_outputs/{}_{}_{}_2".format(site_width, site_height, name),
#             room_count,
#         )
#         rooms.append(room)
#         room_count += 1
#     for sub_road_poly in sub_road_polys:
#         room = get_room(
#             sub_road_poly.simplify(0, False),
#             "road2",
#             1,
#             "log_outputs/{}_{}_{}_2".format(site_width, site_height, name),
#             room_count,
#         )
#         rooms.append(room)
#         room_count += 1
#         room["objList"] = []

#     out["rooms"] = rooms
#     out["PerspectiveCamera"] = autoPerspectiveCamera(out)
#     with open("log_outputs/{}_{}_{}_2.json".format(site_width, site_height, name), "w") as out_f:
#         json.dump(out, out_f)


def output_scene(
    graph: nx.Graph,
    circuits: List[list],
    main_edges: List[tuple],
    codes: List[int],
    results: List[list],
    model_data: dict,
    benches: List[tuple],
    fences: List[tuple],
    name: str,
):
    out = {}
    out["origin"] = "{}_{}_{}".format(site_width, site_height, name)
    out["id"] = "{}_{}_{}".format(site_width, site_height, name)
    # out['islod'] = True
    out["bbox"] = {"min": [site_xl, 0, site_yl], "max": [site_xh, 3, site_yh]}
    out["up"] = [0, 1, 0]
    out["front"] = [0, 0, 1]
    # out_step4 = deepcopy(out)
    # out_step4["origin"] = "{}_{}_{}_3".format(site_width, site_height, name)
    # out_step4["id"] = "{}_{}_{}_3".format(site_width, site_height, name)
    rooms, rooms_step4 = [], []
    room_count = 0
    main_road_polys, sub_road_polys = None, None
    grass = model_data["types"]["grass"]
    drygrass = model_data["types"]["drygrass"]
    plant = model_data["types"]["plant"]
    bridge_type = model_data["types"]["road"][0]
    bridge_model = model_data["objs"][bridge_type]

    ### decide bridges
    bridge_edges = []
    for i in range(len(circuits)):
        for j in range(i + 1, len(circuits)):
            if codes[i] != 0 or codes[j] != 0:
                continue
            intersection = set(circuits[i]) & set(circuits[j])
            for k in range(len(circuits[i]) - 1):
                if circuits[i][k] in intersection and circuits[i][k + 1] in intersection:
                    bridge_edges.append((circuits[i][k], circuits[i][k + 1]))

    for i in range(len(circuits)):
        coords = [graph.nodes[node]["pos"] for node in circuits[i]]
        polys = Polygon(coords).simplify(0, False)
        for j in range(len(coords)):
            if tuple_in_list((circuits[i][j], circuits[i][(j + 1) % len(circuits[i])]), bridge_edges):
                continue
            p1, p2 = coords[j], coords[(j + 1) % len(coords)]
            is_main = tuple_in_list((circuits[i][j], circuits[i][(j + 1) % len(circuits[i])]), main_edges)
            road_width = MAIN_ROAD_WIDTH if is_main else SUB_ROAD_WIDTH
            # x1, x2, y1, y2 = p1[0], p2[0], p1[1], p2[1]
            # xl, yl, xh, yh = min(x1, x2) - road_width / 2, min(y1, y2) - road_width / 2, max(
            #     x1, x2) + road_width / 2, max(y1, y2) + road_width / 2
            # pointList = [np.array(point) for point in [(xl, yl), (xh, yl), (xh, yh), (xl, yh)]]
            p1, p2 = vec(p1[0], p1[1]), vec(p2[0], p2[1])
            tangent = norm(p2 - p1)
            pointList = []
            for k in range(SEMICIRCLE_PARTS + 1):
                pointList.append(p1 + rot(tangent, k * pi / SEMICIRCLE_PARTS + pi / 2) * road_width / 2)
            for k in range(SEMICIRCLE_PARTS + 1):
                pointList.append(p2 + rot(tangent, k * pi / SEMICIRCLE_PARTS - pi / 2) * road_width / 2)
            road_poly = Polygon(pointList)
            polys = polys.difference(road_poly)
            if is_main:
                if main_road_polys is None:
                    main_road_polys = road_poly
                else:
                    main_road_polys = main_road_polys.union(road_poly)
            else:
                if sub_road_polys is None:
                    sub_road_polys = road_poly
                else:
                    sub_road_polys = sub_road_polys.union(road_poly)

        polys = [polys] if isinstance(polys, Polygon) else list(polys.geoms)
        for j in range(len(polys)):
            poly = polys[j]
            area_type, terrainType = None, 0
            if codes[i] == 0:
                area_type = "water"
            elif codes[i] == 2 or codes[i] == 6:
                area_type = "garden"
            elif codes[i] % 4 == 0 or codes[i] % 4 == 2:
                area_type = "earth"
                terrainType = 1
            else:
                area_type = "grass"
                terrainType = 2
            room = get_room(
                poly.simplify(0.1, True),
                area_type,
                0,
                "outputs/{}_{}_{}".format(site_width, site_height, name),
                room_count,
            )
            # room_step4 = get_room(
            #     poly.simplify(0.1, True),
            #     area_type,
            #     0,
            #     "log_outputs/{}_{}_{}_3".format(site_width, site_height, name),
            #     room_count,
            # )
            if room is None:
                continue
            objList, objList_step4 = [], []
            for obj_tuple in results[i][j]:
                obj = {}
                obj["modelId"] = obj_tuple[0]
                model = model_data["objs"][obj_tuple[0]]
                xscale, zscale = (
                    model["ref_size"][0] * obj_tuple[1][2] / model["actual_size"][0],
                    model["ref_size"][1] * obj_tuple[1][2] / model["actual_size"][1],
                )
                yscale = sqrt(xscale * zscale) if model["type"] != "grass" else random.uniform(0.35, 0.5)
                obj_y = 0 if model["type"] != "rock" else random.uniform(-0.4, 0) * yscale
                random_rotate, rotate_ang = model["ref_size"][0] == model["ref_size"][1], 0
                if random_rotate:
                    rotate_ang = random.randint(0, 3) * pi / 2
                xcenter, zcenter = (model["bbox"][0] + model["bbox"][2]) / 2, (model["bbox"][1] + model["bbox"][3]) / 2
                xcenter, zcenter = xcenter * cos(rotate_ang) + zcenter * sin(rotate_ang), -xcenter * sin(
                    rotate_ang
                ) + zcenter * cos(rotate_ang)
                obj["translate"] = [obj_tuple[1][0] - xcenter * xscale, obj_y, obj_tuple[1][1] - zcenter * zscale]
                obj["scale"] = [xscale, yscale, zscale]
                obj["roomId"] = room_count
                obj["rotate"] = [0, rotate_ang, 0]
                obj["orient"] = rotate_ang
                obj["format"] = "instancedMesh"
                obj["isSceneObj"] = True
                obj["inDatabase"] = True
                objList.append(obj)
                if model["type"] == "grass":
                    objList_step4.append(obj)
            if terrainType == 2:
                grass_type = random.choice(grass)
                grass_model = model_data["objs"][grass_type]
                grass_actual_size = grass_model["actual_size"]
                grass_datas = fill_texture(poly)
                for grass_data in grass_datas:
                    obj = {}
                    obj["modelId"] = grass_type
                    xscale, zscale = grass_data[2] / grass_actual_size[0], grass_data[3] / grass_actual_size[1]
                    obj["translate"] = [
                        grass_data[0] + grass_data[2] / 2 * xscale,
                        0,
                        grass_data[1] + grass_data[3] / 2 * zscale,
                    ]
                    rotate_ang = random.randint(0, 3) * pi / 2
                    yscale = random.uniform(0.35, 0.5)
                    obj["scale"] = [xscale, yscale, zscale]
                    obj["roomId"] = room_count
                    obj["rotate"] = [0, 0, 0]
                    obj["orient"] = 0
                    obj["format"] = "instancedMesh"
                    obj["isSceneObj"] = True
                    obj["inDatabase"] = True
                    objList.append(obj)
                    objList_step4.append(obj)
            elif terrainType == 1:
                drygrass_type, plant_type = random.choice(drygrass), random.choice(plant)
                drygrass_model, plant_model = model_data["objs"][drygrass_type], model_data["objs"][plant_type]
                drygrass_ref_size, plant_ref_size = drygrass_model["ref_size"], plant_model["ref_size"]
                drygrass_positions_and_scales = random_fill_area_free(
                    poly, drygrass_ref_size[0], drygrass_ref_size[1], 0.1, 0.5, 1
                )
                plant_positions_and_scales = random_fill_area_free(
                    poly, plant_ref_size[0], plant_ref_size[1], 0.05, 0.5, 1
                )
                for drygrass_position in drygrass_positions_and_scales:
                    obj = {}
                    obj["modelId"] = drygrass_type
                    xscale, zscale = (
                        drygrass_ref_size[0] * drygrass_position[2] / drygrass_model["actual_size"][0],
                        drygrass_ref_size[1] * drygrass_position[2] / drygrass_model["actual_size"][1],
                    )
                    yscale = sqrt(xscale * zscale)
                    obj["translate"] = [
                        drygrass_position[0] - (drygrass_model["bbox"][0] + drygrass_model["bbox"][2]) / 2 * xscale,
                        0,
                        drygrass_position[1] - (drygrass_model["bbox"][1] + drygrass_model["bbox"][3]) / 2 * zscale,
                    ]
                    obj["scale"] = [xscale, yscale, zscale]
                    obj["roomId"] = room_count
                    obj["rotate"] = [0, 0, 0]
                    obj["orient"] = 0
                    obj["format"] = "instancedMesh"
                    obj["isSceneObj"] = True
                    obj["inDatabase"] = True
                    objList.append(obj)
                    objList_step4.append(obj)
                for plant_position in plant_positions_and_scales:
                    obj = {}
                    obj["modelId"] = plant_type
                    xscale, zscale = (
                        plant_ref_size[0] * plant_position[2] / plant_model["actual_size"][0],
                        plant_ref_size[1] * plant_position[2] / plant_model["actual_size"][1],
                    )
                    yscale = sqrt(xscale * zscale)
                    obj["translate"] = [
                        plant_position[0] - (plant_model["bbox"][0] + plant_model["bbox"][2]) / 2 * xscale,
                        0,
                        plant_position[1] - (plant_model["bbox"][1] + plant_model["bbox"][3]) / 2 * zscale,
                    ]
                    obj["scale"] = [xscale, yscale, zscale]
                    obj["roomId"] = room_count
                    obj["rotate"] = [0, 0, 0]
                    obj["orient"] = 0
                    obj["format"] = "instancedMesh"
                    obj["isSceneObj"] = True
                    obj["inDatabase"] = True
                    objList.append(obj)
                    objList_step4.append(obj)
            room["objList"] = objList
            rooms.append(room)
            # room_step4["objList"] = objList_step4
            # rooms_step4.append(room_step4)
            room_count += 1

    ### add bridges
    for bridge_edge in bridge_edges:
        p1, p2 = graph.nodes[bridge_edge[0]]["pos"], graph.nodes[bridge_edge[1]]["pos"]
        p1, p2 = vec(p1), vec(p2)
        tang = norm(p2 - p1)
        center_pos, ori = (p1 + p2) / 2, atan2(tang[1], tang[0])
        bridge_length = get_length(p1, p2) + 0.1
        obj = {}
        obj["modelId"] = bridge_type
        xscale, zscale = (
            SUB_ROAD_WIDTH / bridge_model["actual_size"][0],
            bridge_length / bridge_model["actual_size"][1],
        )
        yscale = 1
        obj["translate"] = [
            center_pos[0] - (bridge_model["bbox"][0] + bridge_model["bbox"][2]) / 2 * xscale,
            0,
            center_pos[1] - (bridge_model["bbox"][1] + bridge_model["bbox"][3]) / 2 * zscale,
        ]
        obj["scale"] = [xscale, yscale, zscale]
        obj["roomId"] = 0
        obj["rotate"] = [0, -ori - pi / 2, 0]
        obj["orient"] = -ori - pi / 2
        obj["format"] = "instancedMesh"
        obj["isSceneObj"] = True
        obj["inDatabase"] = True
        rooms[0]["objList"].append(obj)

    main_road_polys = (
        []
        if main_road_polys is None
        else ([main_road_polys] if isinstance(main_road_polys, Polygon) else list(main_road_polys.geoms))
    )
    sub_road_polys = (
        []
        if sub_road_polys is None
        else ([sub_road_polys] if isinstance(sub_road_polys, Polygon) else list(sub_road_polys.geoms))
    )
    for main_road_poly in main_road_polys:
        room = get_room(
            main_road_poly.simplify(0, True),
            "road1",
            2,
            "outputs/{}_{}_{}".format(site_width, site_height, name),
            room_count,
        )
        # room_step4 = get_room(
        #     main_road_poly.simplify(0, False),
        #     "road1",
        #     2,
        #     "log_outputs/{}_{}_{}_3".format(site_width, site_height, name),
        #     room_count,
        # )
        # rooms_step4.append(room_step4)
        objList = []
        for bench_data in benches:
            obj = {}
            obj["modelId"] = bench_data[3]
            model = model_data["objs"][bench_data[3]]
            xscale, zscale = (
                model["ref_size"][0] / model["actual_size"][0],
                model["ref_size"][1] / model["actual_size"][1],
            )
            yscale = sqrt(xscale * zscale)
            rotate_ang = bench_data[2] - model["forward"] * pi / 2
            xcenter, zcenter = (model["bbox"][0] + model["bbox"][2]) / 2, (model["bbox"][1] + model["bbox"][3]) / 2
            xcenter, zcenter = xcenter * cos(rotate_ang) + zcenter * sin(rotate_ang), -xcenter * sin(
                rotate_ang
            ) + zcenter * cos(rotate_ang)
            obj["translate"] = [bench_data[0] - xcenter * xscale, 0, bench_data[1] - zcenter * zscale]
            obj["scale"] = [xscale, yscale, zscale]
            obj["roomId"] = room_count
            obj["rotate"] = [0, rotate_ang, 0]
            obj["orient"] = rotate_ang
            obj["format"] = "instancedMesh"
            obj["isSceneObj"] = True
            obj["inDatabase"] = True
            objList.append(obj)
        for fence_data in fences:
            obj = {}
            obj["modelId"] = fence_data[4]
            model = model_data["objs"][fence_data[4]]
            xscale, zscale = (
                model["ref_size"][0] / model["actual_size"][0],
                model["ref_size"][1] / model["actual_size"][1],
            )
            if model["ref_size"][0] > model["ref_size"][1]:
                xscale *= fence_data[3]
            else:
                zscale *= fence_data[3]
            rotate_ang = (fence_data[2] - model["forward"]) * pi / 2
            xcenter, zcenter = (model["bbox"][0] + model["bbox"][2]) / 2, (model["bbox"][1] + model["bbox"][3]) / 2
            xcenter, zcenter = xcenter * cos(rotate_ang) + zcenter * sin(rotate_ang), -xcenter * sin(
                rotate_ang
            ) + zcenter * cos(rotate_ang)
            obj["translate"] = [fence_data[0] - xcenter * xscale, 0, fence_data[1] - zcenter * zscale]
            obj["scale"] = [xscale, 1, zscale]
            obj["roomId"] = room_count
            obj["rotate"] = [0, rotate_ang, 0]
            obj["orient"] = rotate_ang
            obj["format"] = "instancedMesh"
            obj["isSceneObj"] = True
            obj["inDatabase"] = True
            objList.append(obj)
        room["objList"] = objList
        rooms.append(room)
        room_count += 1
    for sub_road_poly in sub_road_polys:
        room = get_room(
            sub_road_poly.simplify(0, False),
            "road2",
            1,
            "outputs/{}_{}_{}".format(site_width, site_height, name),
            room_count,
        )
        # room_step4 = get_room(
        #     sub_road_poly.simplify(0, False),
        #     "road2",
        #     1,
        #     "log_outputs/{}_{}_{}_3".format(site_width, site_height, name),
        #     room_count,
        # )
        rooms.append(room)
        # rooms_step4.append(room_step4)
        room_count += 1

    out["rooms"] = rooms
    out["PerspectiveCamera"] = autoPerspectiveCamera(out)
    # out_step4["rooms"] = rooms_step4
    # out_step4["PerspectiveCamera"] = autoPerspectiveCamera(out_step4)
    with open("outputs/{}_{}_{}.json".format(site_width, site_height, name), "w") as out_f:
        json.dump(out, out_f)
    # with open("log_outputs/{}_{}_{}_3.json".format(site_width, site_height, name), "w") as out_f:
    #     json.dump(out_step4, out_f)


def autoPerspectiveCamera(scenejson):
    PerspectiveCamera = {}
    xl, yl, xh, yh = (
        scenejson["bbox"]["min"][0],
        scenejson["bbox"]["min"][2],
        scenejson["bbox"]["max"][0],
        scenejson["bbox"]["max"][2],
    )
    lx = (xh + xl) / 2
    lz = (yh + yl) / 2
    camfovratio = np.tan((DEFAULT_FOV / 2) * np.pi / 180)
    lx_length = xh - xl
    lz_length = yh - yl
    if lz_length > lx_length:
        PerspectiveCamera["up"] = [1, 0, 0]
        camHeight = WALLHEIGHT + (xh / 2 - xl / 2) / camfovratio
    else:
        PerspectiveCamera["up"] = [0, 0, 1]
        camHeight = WALLHEIGHT + (yh / 2 - yl / 2) / camfovratio
    PerspectiveCamera["origin"] = [lx, camHeight, lz]
    PerspectiveCamera["target"] = [lx, 0, lz]
    PerspectiveCamera["up"] = [0, 0, 1]
    PerspectiveCamera["rotate"] = [0, 0, 0]
    PerspectiveCamera["fov"] = DEFAULT_FOV
    PerspectiveCamera["focalLength"] = 35
    scenejson["PerspectiveCamera"] = PerspectiveCamera
    return PerspectiveCamera


def fix_region(graph, regions):
    num_nodes = len(graph.nodes)
    new_regions = []
    for region in regions:
        new_region = []
        for i in range(len(region)):
            p1, p2 = graph.nodes[region[i]]["pos"], graph.nodes[region[(i + 1) % len(region)]]["pos"]
            proj_node_list, t_list = [], []
            for j in range(num_nodes):
                if j == region[i] or j == region[(i + 1) % len(region)]:
                    continue
                p = graph.nodes[j]["pos"]
                if Point(p).distance(LineString([p1, p2])) < EPS:
                    t, proj = projection(p, p1, p2)
                    if 0 <= t <= 1:
                        proj_node_list.append(j)
                        t_list.append(t)
            new_region.append(region[i])
            if len(proj_node_list) > 0:
                # sort based on t
                proj_node_list = [x for _, x in sorted(zip(t_list, proj_node_list))]
                for j in range(len(proj_node_list)):
                    new_region.append(proj_node_list[j])
        new_regions.append(new_region)
    return new_regions


def construct_graph(boundary):
    # undirected graph
    graph = nx.Graph()
    graph.add_nodes_from([i for i in range(len(boundary))])
    for i in range(len(boundary)):
        graph.nodes[i]["pos"] = vec(boundary[i])
    regions = [[i for i in range(len(boundary))]]
    for k in range(SPLIT):
        areas = [Polygon([graph.nodes[i]["pos"] for i in region]).area for region in regions]
        rand_num = random.choices(range(len(areas)), weights=areas, k=1)[0]
        while split_region(graph, regions, rand_num) is False:
            rand_num = random.choices(range(len(areas)), weights=areas, k=1)[0]

    regions = fix_region(graph, regions)
    # connect the edges
    for region in regions:
        for i in range(len(region)):
            n1, n2 = region[i], region[(i + 1) % len(region)]
            n1, n2 = min(n1, n2), max(n1, n2)
            if not graph.has_edge(n1, n2):
                graph.add_edge(n1, n2)
    return graph, regions


def get_lines(graph):
    border_lines, inner_lines = [], []
    for node in graph.nodes:
        # try to find a longest line starting from node
        p = graph.nodes[node]["pos"]
        neighbors = list(graph.neighbors(node))
        # is_starting = True
        # for i in range(len(neighbors)):
        #     n1, p1 = neighbors[i], graph.nodes[neighbors[i]]["pos"]
        #     argtan1 = atan2(p[1] - p1[1], p[0] - p1[0])
        #     # if is_border_edge(graph, (node, n1)):
        #     #     continue
        #     for j in range(i + 1, len(neighbors)):
        #         n2, p2 = neighbors[j], graph.nodes[neighbors[j]]["pos"]
        #         argtan2 = atan2(p2[1] - p1[1], p2[0] - p1[0])
        #         # if is_border_edge(graph, (node, n2)):
        #         #     continue
        #         if abs(argtan1 - argtan2) < EPS:
        #             is_starting = False
        #             break
        #     if not is_starting:
        #         break
        # if is_starting:
        for n in neighbors:
            p1 = graph.nodes[n]["pos"]
            line = [node, n]
            is_border = is_border_edge(graph, (node, n))
            curr_node = n
            argtan = atan2(p[1] - p1[1], p[0] - p1[0])
            while True:
                next_node = None
                for neighbor in graph.neighbors(curr_node):
                    if neighbor in line:
                        continue
                    new_is_border = is_border_edge(graph, (curr_node, neighbor))
                    if new_is_border != is_border:
                        continue
                    next_p = graph.nodes[neighbor]["pos"]
                    argtan2 = atan2(p[1] - next_p[1], p[0] - next_p[0])
                    if angle_diff(argtan, argtan2) < EPS:
                        next_node = neighbor
                        break
                if next_node is None:
                    break
                else:
                    line.append(next_node)
                    curr_node = next_node
            contained = False
            if is_border:
                for border_line in border_lines:
                    if set(line) - set(border_line) == set():
                        contained = True
                        break
                if not contained:
                    border_lines.append(line)
            else:
                for inner_line in inner_lines:
                    if set(line) - set(inner_line) == set():
                        contained = True
                        break
                if not contained:
                    inner_lines.append(line)

    return border_lines, inner_lines


def gen_scene(args):
    model_data, idx, seed = args
    random.seed(seed + idx)
    name = str(idx)
    graph, regions = construct_graph(site_bound)
    border_lines, inner_lines = get_lines(graph)
    # print(border_lines, inner_lines)
    if VISUALIZE:
        visualize_raw(graph, idx)

    edges = np.array(graph.edges)
    border_edges = [tuple(edge) for edge in edges if is_border_edge(graph, edge)]
    inner_edges = [tuple(edge) for edge in edges if not is_border_edge(graph, edge)]
    random.shuffle(inner_edges)
    chosen_edges = inner_edges[: len(inner_edges) // 2] + border_edges
    if VISUALIZE:
        visualize_chosen_edges(graph, chosen_edges, "first_chosen", idx)

    order_lines(graph, SPLIT, inner_lines, chosen_edges)
    if VISUALIZE:
        visualize_chosen_edges(graph, chosen_edges, "ordered_chosen", idx)
    chosen_edges = order_circuits(graph, inner_lines, chosen_edges)
    if VISUALIZE:
        visualize_chosen_edges(graph, chosen_edges, "circuits_chosen", idx)

    circuits = get_simple_circuits(graph, chosen_edges)
    # print(circuits)
    main_edges, sub_edges = get_main_sub_edges(graph, border_lines, inner_lines, deepcopy(chosen_edges))
    if VISUALIZE:
        visualize(graph, chosen_edges, main_edges, sub_edges, idx)
    area_codes = genetic_area_choose(graph, circuits)
    if VISUALIZE:
        visualize_areas(graph, circuits, area_codes, idx)
    fill_results, fences, protected_edges = fill_areas(graph, circuits, main_edges, area_codes, model_data)
    graph, circuits, chosen_edges, main_edges = fill_areas_curve(
        graph, circuits, chosen_edges, main_edges, protected_edges
    )
    if VISUALIZE:
        visualize_areas(graph, circuits, area_codes, idx)
    fill_results, fences, protected_edges = fill_areas(graph, circuits, main_edges, area_codes, model_data)
    benches = add_elements(graph, circuits, main_edges, area_codes, model_data)
    output_scene(graph, circuits, main_edges, area_codes, fill_results, model_data, benches, fences, name)
    print("Scene {} generated".format(idx))


def main(seed):
    # global site_bound
    # site_bound = generate_polygon(center=(50, 50),
    #                     avg_radius=50,
    #                     irregularity=0.9,
    #                     spikiness=0.2,
    #                     num_vertices=32)
    if not os.path.exists("outputs"):
        os.mkdir("outputs")
    if not os.path.exists("visuals"):
        os.mkdir("visuals")
    # if not os.path.exists("log_outputs"):
    #     os.mkdir("log_outputs")
    model_data_json = open("object/data.json", "r")
    model_data = json.load(model_data_json)
    # with Pool(PROCESS_COUNT) as p:
    # _ = list(tqdm(p.imap(gen_scene, [(model_data, i, seed) for i in range(GEN_NUM)]), total=GEN_NUM))
    pool = Pool(PROCESS_COUNT)
    for i in range(GEN_NUM):
        pool.apply_async(gen_scene, args=((model_data, i, seed),))
    pool.close()
    pool.join()
    # for i in range(GEN_NUM):
    #     gen_scene((model_data, i, seed))
    model_data_json.close()


if __name__ == "__main__":
    main(129)
    # for i in range(100):
    #     print('-------------------', i)
    #     main(i)
