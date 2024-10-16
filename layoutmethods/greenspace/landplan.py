import matplotlib
import time

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
import os
from collections import Counter
import cv2

VISUALIZE = True
GEN_NUM = 50000
SPLIT = 25
PROCESS_COUNT = 10

EPS = 1e-3
SUB_ROAD_WIDTH = 2
MAIN_ROAD_WIDTH = 2.5
WIDTH = 64
HEIGHT = 64
WIDTH_L = 32
HEIGHT_L = 32

MAX_CIRCUIT_TRY = 100
POPULATION_SIZE = 100
CROSS_RATE = 0.8
MUTATION_RATE = 0.5
MAX_GENERATION = 1000

MODEL_LIMIT = 1500

SEMICIRCLE_PARTS = 20
CURVE_PARTS = 10


def p(x: float, y: float):
    """a point or a vector"""
    return np.array([x, y])


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
    angle = acos(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))
    if angle > pi:
        angle = 2 * pi - angle
    return angle


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
    if graph.nodes[edge[0]]["pos"][0] == 0 and graph.nodes[edge[1]]["pos"][0] == 0:
        return True
    elif graph.nodes[edge[0]]["pos"][0] == WIDTH and graph.nodes[edge[1]]["pos"][0] == WIDTH:
        return True
    elif graph.nodes[edge[0]]["pos"][1] == 0 and graph.nodes[edge[1]]["pos"][1] == 0:
        return True
    elif graph.nodes[edge[0]]["pos"][1] == HEIGHT and graph.nodes[edge[1]]["pos"][1] == HEIGHT:
        return True
    return False


def split_region(graph: nx.Graph, regions: List[tuple], idx: int):
    region = regions[idx]
    xl, yl, xh, yh = (
        graph.nodes[region[0]]["pos"][0],
        graph.nodes[region[0]]["pos"][1],
        graph.nodes[region[1]]["pos"][0],
        graph.nodes[region[2]]["pos"][1],
    )
    width, height = xh - xl, yh - yl
    curr_count = graph.number_of_nodes()

    split_type = None  # 0: split x, 1: split y
    if width / height > 2:
        split_type = 0
    elif height / width > 2:
        split_type = 1
    else:
        split_type = random.randint(0, 1)
    if split_type == 0:
        ratio = random.uniform(1 / 3, 2 / 3)
        if width * ratio < MAIN_ROAD_WIDTH * 2 or width * (1 - ratio) < MAIN_ROAD_WIDTH * 2:
            return False
        graph.add_nodes_from([curr_count, curr_count + 1])
        graph.nodes[curr_count]["pos"] = (xl + width * ratio, yl)
        graph.nodes[curr_count + 1]["pos"] = (xl + width * ratio, yh)
        # graph.remove_edges_from([(region[0], region[1]), (region[2], region[3])])
        # graph.add_edges_from([(region[0], curr_count), (curr_count, region[1]), (region[2], curr_count + 1),
        #                       (curr_count + 1, region[3]), (curr_count, curr_count + 1)])
        regions.append((region[0], curr_count, curr_count + 1, region[3]))
        regions.append((curr_count, region[1], region[2], curr_count + 1))
        regions.remove(region)
    else:
        ratio = random.uniform(1 / 3, 2 / 3)
        if height * ratio < MAIN_ROAD_WIDTH * 2 or height * (1 - ratio) < MAIN_ROAD_WIDTH * 2:
            return False
        graph.add_nodes_from([curr_count, curr_count + 1])
        graph.nodes[curr_count]["pos"] = (xl, yl + height * ratio)
        graph.nodes[curr_count + 1]["pos"] = (xh, yl + height * ratio)
        # graph.remove_edges_from([(region[0], region[3]), (region[1], region[2])])
        # graph.add_edges_from([(region[0], curr_count), (curr_count, region[3]), (region[1], curr_count + 1),
        #                       (curr_count + 1, region[2]), (curr_count, curr_count + 1)])
        regions.append((region[0], region[1], curr_count + 1, curr_count))
        regions.append((curr_count, curr_count + 1, region[2], region[3]))
        regions.remove(region)
    return True


def color2type(color255):
    colors = [
        (0, 204, 255),
        (233, 233, 233),
        (255, 0, 72),
        (255, 186, 0),
        (0, 168, 36),
        (153, 191, 0),
        (191, 0, 67),
        (191, 143, 0),
        (0, 0, 0),
        (51, 64, 0),
        (64, 0, 22),
        (64, 48, 0),
        (0, 84, 18),
        (102, 128, 0),
        (128, 0, 45),
        (128, 96, 0),
        (102, 102, 102),
        (153, 153, 153),
    ]
    for i in range(len(colors)):
        if color255[0] == colors[i][0] and color255[1] == colors[i][1] and color255[2] == colors[i][2]:
            return i
    return -1


def generate_landplan(graph, circuits, chosen_edges, main_edges, code, idx):
    fig, ax = plt.subplots(figsize=(32, HEIGHT / WIDTH * 32), dpi=32, layout="tight")
    ### plot the areas
    circuits = [circuit for circuit in circuits if len(circuit) > 2]
    count = len(circuits)
    polys = [Polygon([graph.nodes[node]["pos"] for node in circuit]).simplify(0, True) for circuit in circuits]
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
    ### plot the sub roads
    for edge in chosen_edges:
        if edge in main_edges:
            continue
        p1, p2 = graph.nodes[edge[0]]["pos"], graph.nodes[edge[1]]["pos"]
        p1, p2 = p(p1[0], p1[1]), p(p2[0], p2[1])
        tangent = norm(p2 - p1)
        pointList = []
        for k in range(SEMICIRCLE_PARTS + 1):
            pointList.append(p1 + rot(tangent, k * pi / SEMICIRCLE_PARTS + pi / 2) * SUB_ROAD_WIDTH / 2)
        for k in range(SEMICIRCLE_PARTS + 1):
            pointList.append(p2 + rot(tangent, k * pi / SEMICIRCLE_PARTS - pi / 2) * SUB_ROAD_WIDTH / 2)
        plt.fill([x[0] for x in pointList], [x[1] for x in pointList], c=(0.6, 0.6, 0.6))
    ### plot the main roads
    for edge in main_edges:
        p1, p2 = graph.nodes[edge[0]]["pos"], graph.nodes[edge[1]]["pos"]
        p1, p2 = p(p1[0], p1[1]), p(p2[0], p2[1])
        tangent = norm(p2 - p1)
        pointList = []
        for k in range(SEMICIRCLE_PARTS + 1):
            pointList.append(p1 + rot(tangent, k * pi / SEMICIRCLE_PARTS + pi / 2) * MAIN_ROAD_WIDTH / 2)
        for k in range(SEMICIRCLE_PARTS + 1):
            pointList.append(p2 + rot(tangent, k * pi / SEMICIRCLE_PARTS - pi / 2) * MAIN_ROAD_WIDTH / 2)
        plt.fill([x[0] for x in pointList], [x[1] for x in pointList], c=(0.4, 0.4, 0.4))

    ax.set_xlim(0, WIDTH)
    ax.set_ylim(0, HEIGHT)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_visible(False)

    fig.canvas.draw()
    image = np.frombuffer(fig.canvas.tostring_argb(), dtype=np.uint8)
    width, height = fig.canvas.get_width_height()
    image = image.reshape((height, width, 4))
    image = image[:, :, [1, 2, 3, 0]]

    cell_height = height // HEIGHT_L
    cell_width = width // WIDTH_L

    dominant_colors = [[None for _ in range(WIDTH_L)] for _ in range(HEIGHT_L)]
    dominant_types = [[None for _ in range(WIDTH_L)] for _ in range(HEIGHT_L)]

    for i in range(HEIGHT_L):
        for j in range(WIDTH_L):
            cell = image[i * cell_height : (i + 1) * cell_height, j * cell_width : (j + 1) * cell_width]
            pixels = cell.reshape(-1, 4)
            pixel_counts = Counter(map(tuple, pixels))
            dominant_color = pixel_counts.most_common(1)[0][0]
            dominant_colors[i][j] = dominant_color
            dominant_types[i][j] = color2type(dominant_color)

    # plt.savefig("landplan/{}_{}_{}_origin.png".format(WIDTH, HEIGHT, idx), bbox_inches='tight', pad_inches=0)
    plt.close()
    ### write the dominant colors to a png file
    dominant_colors = np.array(dominant_colors, dtype=np.uint8)
    cv2.imwrite("landplan/{}_{}_{}.png".format(WIDTH, HEIGHT, idx), cv2.cvtColor(dominant_colors, cv2.COLOR_RGBA2BGRA))
    ### write the dominant types to a json file
    with open("landplan/{}_{}_{}.json".format(WIDTH, HEIGHT, idx), "w") as f:
        json.dump(dominant_types, f)


def get_line(graph: nx.Graph, n1: int, n2: int):
    x1, y1, x2, y2 = (
        graph.nodes[n1]["pos"][0],
        graph.nodes[n1]["pos"][1],
        graph.nodes[n2]["pos"][0],
        graph.nodes[n2]["pos"][1],
    )
    coord_and_node = []
    if x1 == x2:
        for node in graph.nodes:
            if graph.nodes[node]["pos"][0] == x1 and min(y1, y2) <= graph.nodes[node]["pos"][1] <= max(y1, y2):
                coord_and_node.append((graph.nodes[node]["pos"][1], node))
    else:
        for node in graph.nodes:
            if graph.nodes[node]["pos"][1] == y1 and min(x1, x2) <= graph.nodes[node]["pos"][0] <= max(x1, x2):
                coord_and_node.append((graph.nodes[node]["pos"][0], node))
    coord_and_node.sort()
    nodes = []
    for i in range(len(coord_and_node)):
        nodes.append(coord_and_node[i][1])
    return nodes


def connect(graph: nx.Graph, n1: int, n2: int):
    nodes = get_line(graph, n1, n2)
    for i in range(len(nodes) - 1):
        graph.add_edge(nodes[i], nodes[i + 1])


def connect_graph(graph: nx.Graph, split: int):
    connect(graph, 0, 1)
    connect(graph, 1, 2)
    connect(graph, 2, 3)
    connect(graph, 3, 0)
    for i in range(split):
        connect(graph, 4 + i * 2, 4 + i * 2 + 1)


def division_evaluate(
    graph: nx.Graph, chosen_graph: nx.Graph, isolated_nodes: List[int], chosen_edges: List[tuple], polys
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
                xl, yl, xh, yh = (
                    min(x1, x2) - EPS / 2,
                    min(y1, y2) - EPS / 2,
                    max(x1, x2) + EPS / 2,
                    max(y1, y2) + EPS / 2,
                )
                road_poly = Polygon([(xl, yl), (xh, yl), (xh, yh), (xl, yh)])
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
    max_area_ratio = np.sum((areas[labels == max_idx])) / (WIDTH * HEIGHT)
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
    lines = [get_line(graph, i, (i + 1) % 4) for i in range(4)]
    for line in lines:
        for i in range(len(line) - 1):
            chosen_graph.remove_edge(line[i], line[i + 1])
    for line in lines:
        connect_count = 0
        for node in line:
            if chosen_graph.degree(node) > 0:
                connect_count += 1
        if connect_count == 0:
            score4 += 2
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


def order_lines(graph: nx.Graph, split: int, chosen_edges: List[tuple]):
    length_and_lines = []
    for i in range(split):
        line = get_line(graph, 4 + i * 2, 4 + i * 2 + 1)
        length = get_length(graph.nodes[4 + i * 2]["pos"], graph.nodes[4 + i * 2 + 1]["pos"])
        length_and_lines.append((length, line))
    length_and_lines.sort()

    accept_thres = 0.5
    major_length_and_lines = [length_and_line for length_and_line in length_and_lines[-split // 5 :]][::-1]
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


def order_circuits(graph: nx.Graph, chosen_edges: List[tuple]):
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
            chosen_graph.remove_edge(edge[0], edge[1])
            remove_tuple(edge, chosen_edges)
            isolated_nodes.remove(edge[0])
            isolated_nodes.remove(edge[1])

    isolated_nodes = list(isolated_nodes)
    poly = get_spaces(graph, chosen_edges, EPS)
    best_graph, best_edges, min_score = None, None, float("inf")
    for k in range(MAX_CIRCUIT_TRY):
        new_graph, new_edges, score = division_evaluate(
            graph, deepcopy(chosen_graph), deepcopy(isolated_nodes), deepcopy(chosen_edges), deepcopy(poly)
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
                if get_length(p, graph.nodes[node]["pos"]) < EPS:
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
                score2 += adjacent_length / (WIDTH + HEIGHT)
            elif code[i] == 8 and (code[adjacent_node] == 0 or code[adjacent_node] == 1 or code[adjacent_node] == 3):
                score2 += adjacent_length / (WIDTH + HEIGHT)
            bit_d = bit_diff(code[i], code[adjacent_node])
            if bit_d > 2:
                score2 += adjacent_length * (bit_d - 2) / (WIDTH + HEIGHT)

    # general and self compatibility
    total_area = WIDTH * HEIGHT
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


def get_main_sub_edges(graph: nx.Graph, split: int, chosen_edges: List[tuple]):
    chosen_graph = nx.Graph()
    chosen_graph.add_nodes_from(graph.nodes)
    chosen_graph.add_edges_from(chosen_edges)

    chosen_length_and_lines = []
    for i in range(split):
        line = get_line(graph, 4 + i * 2, 4 + i * 2 + 1)
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

    border_lines = [get_line(graph, i, (i + 1) % 4) for i in range(4)]
    for line in border_lines:
        for i in range(len(line) - 1):
            chosen_graph.remove_edge(line[i], line[i + 1])

    sorted_connected_components = sorted(nx.connected_components(chosen_graph), key=len, reverse=True)
    for i in range(1, len(sorted_connected_components)):
        for node in sorted_connected_components[i]:
            chosen_graph.remove_node(node)

    ignored_border_lines = []
    for i in range(4):
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
            if not chosen_graph.has_edge(line[i], line[i + 1]):
                continue
            chosen_graph.remove_edge(line[i], line[i + 1])
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
        chosen_graph.remove_edge(edge[0], edge[1])

    main_edges = list(chosen_graph.edges)
    sub_edges = []
    for edge in chosen_edges:
        if not tuple_in_list(edge, main_edges):
            sub_edges.append(edge)
    return main_edges, sub_edges


def genetic_area_choose(graph: nx.Graph, circuits: List[list]):
    count = len(circuits)
    polys = [Polygon([graph.nodes[node]["pos"] for node in circuit]).simplify(0, True) for circuit in circuits]
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


def solve_circle(p1_, p2_, t_):
    # given two points p1, p2 and the tangent line t at p1, find the center of the circle
    p1, p2, t = p(p1_[0], p1_[1]), p(p2_[0], p2_[1]), p(t_[0], t_[1])
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
    expand_times = (int)(len(expand_edges) * 1.5)
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
        p1, p2 = p(p1[0], p1[1]), p(p2[0], p2[1])
        normal = norm(rot(p2 - p1, pi / 2))
        bias = random.uniform(-0.6, 0.6) * sqrt(weights[i])
        mid = (p1 + p2) / 2 + normal * bias
        idx = len(graph.nodes)

        # modify
        graph.add_node(idx, pos=(mid[0], mid[1]))
        graph.remove_edge(edge[0], edge[1])
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
        p0, p1, p2 = p(p0[0], p0[1]), p(p1[0], p1[1]), p(p2[0], p2[1])
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
            p11, p12, p13 = p(p11[0], p11[1]), p(p12[0], p12[1]), p(p13[0], p13[1])
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
            p11, p12, p13 = p(p11[0], p11[1]), p(p12[0], p12[1]), p(p13[0], p13[1])
            if angle_between(p13 - p11, p11 - p12) > pi / 3:
                break
            string2.append(next)
        if string1[-1] == string2[-1]:
            if len(string1) > len(string2):
                string1 = string1[:-1]
            else:
                string2 = string2[:-1]
        p1, p2 = graph.nodes[string1[-1]]["pos"], graph.nodes[string2[-1]]["pos"]
        p1, p2 = p(p1[0], p1[1]), p(p2[0], p2[1])
        if get_length(p1, p0) < get_length(p2, p0):
            angle = angle_between(p2 - p1, p2 - p0)
        else:
            angle = angle_between(p2 - p1, p1 - p0)
        if angle > pi / 2:
            angle = pi - angle
        if angle < pi / 12:
            continue
        for i in range(len(string1) - 1):
            graph.remove_edge(string1[i], string1[i + 1])
            subgraph.remove_edge(string1[i], string1[i + 1])
            remove_tuple((string1[i], string1[i + 1]), chosen_edges)
            if tuple_in_list((string1[i], string1[i + 1]), main_edges):
                remove_tuple((string1[i], string1[i + 1]), main_edges)
        for i in range(len(string2) - 1):
            graph.remove_edge(string2[i], string2[i + 1])
            subgraph.remove_edge(string2[i], string2[i + 1])
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

    # add benches
    main_edge_and_lengths = []
    for main_edge in main_edges:
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
        bench_num = min((WIDTH + HEIGHT) // 30, longest_nums)
        count = 0
        best_score = float("inf")
        border_points = [(0, 0), (0, HEIGHT), (WIDTH, HEIGHT), (WIDTH, 0)]
        for edge_idxes in itertools.permutations([k for k in range(longest_nums)], bench_num):
            edges, lengths = [longest_edges[k] for k in edge_idxes], [main_edge_and_lengths[k][0] for k in edge_idxes]
            for repeat in range(100):
                positions_and_forwards = []
                for i in range(bench_num):
                    p1, p2 = p(graph.nodes[edges[i][0]]["pos"][0], graph.nodes[edges[i][0]]["pos"][1]), p(
                        graph.nodes[edges[i][1]]["pos"][0], graph.nodes[edges[i][1]]["pos"][1]
                    )
                    toward = get_toward(p1, p2)
                    tangent = norm(p2 - p1)
                    angle = pi / 2 - atan2(tangent[1], tangent[0])
                    normal = p(tangent[1], -tangent[0])
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
    poly = Polygon([(0, 0), (WIDTH, 0), (WIDTH, HEIGHT), (0, HEIGHT)])
    for edge in chosen_edges:
        x1, x2, y1, y2 = (
            graph.nodes[edge[0]]["pos"][0],
            graph.nodes[edge[1]]["pos"][0],
            graph.nodes[edge[0]]["pos"][1],
            graph.nodes[edge[1]]["pos"][1],
        )
        xl, yl, xh, yh = (
            min(x1, x2) - road_width / 2,
            min(y1, y2) - road_width / 2,
            max(x1, x2) + road_width / 2,
            max(y1, y2) + road_width / 2,
        )
        road_poly = Polygon([(xl, yl), (xh, yl), (xh, yh), (xl, yh)])
        poly = poly.difference(road_poly)
    return poly


def gen_landplan(args):
    model_data, idx = args
    regions = []
    graph = nx.Graph()
    graph.add_nodes_from([i for i in range(4)])
    graph.nodes[0]["pos"] = (0, 0)
    graph.nodes[1]["pos"] = (WIDTH, 0)
    graph.nodes[2]["pos"] = (WIDTH, HEIGHT)
    graph.nodes[3]["pos"] = (0, HEIGHT)
    regions.append((0, 1, 2, 3))
    for k in range(SPLIT):
        rand_num = random.randint(0, len(regions) - 1)
        while split_region(graph, regions, rand_num) is False:
            rand_num = random.randint(0, len(regions) - 1)
    connect_graph(graph, SPLIT)

    edges = np.array(graph.edges)
    border_edges = [tuple(edge) for edge in edges if is_border_edge(graph, edge)]
    inner_edges = [tuple(edge) for edge in edges if not is_border_edge(graph, edge)]
    random.shuffle(inner_edges)
    chosen_edges = inner_edges[: len(inner_edges) // 2] + border_edges

    order_lines(graph, SPLIT, chosen_edges)
    chosen_edges = order_circuits(graph, chosen_edges)

    circuits = get_simple_circuits(graph, chosen_edges)
    main_edges, sub_edges = get_main_sub_edges(graph, SPLIT, deepcopy(chosen_edges))
    area_codes = genetic_area_choose(graph, circuits)
    graph, circuits, chosen_edges, main_edges = fill_areas_curve(graph, circuits, chosen_edges, main_edges, [])
    generate_landplan(graph, circuits, chosen_edges, main_edges, area_codes, idx)
    # print("Plan {} generated".format(idx))


def main():
    random.seed()
    if not os.path.exists("landplan"):
        os.mkdir("landplan")
    model_data_json = open("object/data.json", "r")
    model_data = json.load(model_data_json)
    # pool = Pool(PROCESS_COUNT)
    # for i in range(GEN_NUM):
    #     # pool.apply_async(gen_landplan, (model_data, i))
    #     gen_landplan(model_data, i)
    # pool.close()
    # pool.join()
    with Pool(PROCESS_COUNT) as pool:
        r = list(tqdm(pool.imap(gen_landplan, [(model_data, i) for i in range(16800,GEN_NUM)]), total=GEN_NUM-16800))
    model_data_json.close()


if __name__ == "__main__":
    main()
