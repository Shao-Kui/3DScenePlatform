import matplotlib

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
from multiprocessing import Pool
from objectize import objectize
import os
from scipy import interpolate as interp
import cv2

MAX_NUM = 1000
PROCESS_COUNT = 10

WALLHEIGHT = 2.6
DEFAULT_FOV = 75

EPS = 1e-3
COMBINE_THRES = 0.1

MODEL_LIMIT = 1500

SEMICIRCLE_PARTS = 20
CURVE_PARTS = 10

WIDTH_L = 32
HEIGHT_L = 32


def vec(*args):
    if len(args) == 1:
        return np.array(args[0], "float32")
    return np.array(args, "float32")


def angle_between(v1: np.ndarray, v2: np.ndarray):
    """return the angle between two vectors in radian"""
    if np.linalg.norm(v1) == 0 or np.linalg.norm(v2) == 0:
        return 0
    angle = acos(max(min(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)), 1), -1))
    if angle > pi:
        angle = 2 * pi - angle
    return angle


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


def get_length(pos1: tuple, pos2: tuple):
    return sqrt((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2)


def tuple_in_list(t: tuple, l: list):
    for item in l:
        if (t[0] == item[0] and t[1] == item[1]) or (t[0] == item[1] and t[1] == item[0]):
            return True
    return False


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


def fill_areas(areas_types_and_polys, model_data: dict):
    results = []
    for i in range(len(areas_types_and_polys)):
        area_type, poly = areas_types_and_polys[i]
        if area_type == 0 or area_type > 15:
            results.append([])
            continue
        result = []
        polys = poly.simplify(0, False)
        polys = (
            [polys.simplify(0.1, True)]
            if isinstance(polys, Polygon)
            else [poly.simplify(0.1, True) for poly in polys.geoms]
        )
        for poly in polys:
            if not (isinstance(poly, Polygon) and len(list(poly.bounds)) == 4):
                result.append([])
                continue
            fill_result = fill_area(poly, area_type, model_data)
            result.append(fill_result)
        results.append(result)

    return results


def find_connected_components(grid: List[List[int]], n: int) -> List[list]:
    def is_valid(x, y):
        return 0 <= x < WIDTH_L and 0 <= y < HEIGHT_L

    def dfs(x, y, component_id):
        stack = [(x, y)]
        component = []

        dx_dys = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        while stack:
            current_x, current_y = stack.pop()
            if component_labels[current_x][current_y] != -1:
                continue

            component_labels[current_x][current_y] = component_id
            component.append((current_x, current_y))

            for dx, dy in dx_dys:
                new_x, new_y = current_x + dx, current_y + dy
                if is_valid(new_x, new_y) and grid[new_x][new_y] == grid[x][y]:
                    stack.append((new_x, new_y))

        return component

    component_labels = [[-1 for _ in range(HEIGHT_L)] for _ in range(WIDTH_L)]
    components = [[] for _ in range(n)]

    component_id = 0

    for x in range(WIDTH_L):
        for y in range(HEIGHT_L):
            if component_labels[x][y] == -1:
                component = dfs(x, y, component_id)
                components[grid[x][y]].append(component)
                component_id += 1

    return components


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


def color2type(color255):
    for i in range(len(colors)):
        if color255[0] == colors[i][0] and color255[1] == colors[i][1] and color255[2] == colors[i][2]:
            return i
    return -1


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


def output_scene(
    areas_types_and_polys,
    results: List[list],
    model_data: dict,
    name: str,
):
    out = {}
    out["origin"] = "{}_{}_{}".format(WIDTH_L * 2, HEIGHT_L * 2, name)
    out["id"] = "{}_{}_{}".format(WIDTH_L * 2, HEIGHT_L * 2, name)
    # out['islod'] = True
    out["bbox"] = {"min": [0, 0, 0], "max": [WIDTH_L * 2, 3, HEIGHT_L * 2]}
    out["up"] = [0, 1, 0]
    out["front"] = [0, 0, 1]
    rooms = []
    room_count = 0
    grass = model_data["types"]["grass"]
    drygrass = model_data["types"]["drygrass"]
    plant = model_data["types"]["plant"]

    for i in range(len(areas_types_and_polys)):
        type, poly = areas_types_and_polys[i]
        polys = poly.simplify(0, False)
        polys = [polys] if isinstance(polys, Polygon) else list(polys.geoms)
        for j in range(len(polys)):
            poly = polys[j]
            if type == 16:
                room = get_room(
                    poly.simplify(0, True),
                    "road1",
                    2,
                    "outputs/{}_{}_{}".format(WIDTH_L * 2, HEIGHT_L * 2, name),
                    room_count,
                )
                room["objList"] = []
                rooms.append(room)
                room_count += 1
                continue
            elif type == 17:
                room = get_room(
                    poly.simplify(0, True),
                    "road2",
                    1,
                    "outputs/{}_{}_{}".format(WIDTH_L * 2, HEIGHT_L * 2, name),
                    room_count,
                )
                room["objList"] = []
                rooms.append(room)
                room_count += 1
                continue

            area_type, terrainType = None, 0
            if type == 0:
                area_type = "water"
            elif type == 2 or type == 6:
                area_type = "garden"
            elif type % 4 == 0 or type % 4 == 2:
                area_type = "earth"
                terrainType = 1
            else:
                area_type = "grass"
                terrainType = 2
            room = get_room(
                poly.simplify(0.1, True),
                area_type,
                0,
                "outputs/{}_{}_{}".format(WIDTH_L * 2, HEIGHT_L * 2, name),
                room_count,
            )
            if room is None:
                continue
            objList = []
            if len(results[i]) > 0:
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
                    xcenter, zcenter = (model["bbox"][0] + model["bbox"][2]) / 2, (
                        model["bbox"][1] + model["bbox"][3]
                    ) / 2
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
            room["objList"] = objList
            rooms.append(room)
            room_count += 1

    out["rooms"] = rooms
    out["PerspectiveCamera"] = autoPerspectiveCamera(out)
    with open("outputs/{}_{}_{}.json".format(WIDTH_L * 2, HEIGHT_L * 2, name), "w") as out_f:
        json.dump(out, out_f)


def connect_roads(plan):
    for i in range(WIDTH_L - 1):
        for j in range(HEIGHT_L - 1):
            if (
                plan[i][j] == 16
                and plan[i + 1][j + 1] == 16
                and plan[i + 1][j] != 16
                and plan[i][j + 1] != 16
                and plan[i + 1][j] != 17
                and plan[i][j + 1] != 17
            ):
                if random.random() < 0.5:
                    plan[i + 1][j] = 16
                else:
                    plan[i][j + 1] = 16
            if (
                plan[i][j] == 17
                and plan[i + 1][j + 1] == 17
                and plan[i + 1][j] != 17
                and plan[i][j + 1] != 17
                and plan[i + 1][j] != 16
                and plan[i][j + 1] != 16
            ):
                if random.random() < 0.5:
                    plan[i + 1][j] = 17
                else:
                    plan[i][j + 1] = 17
            if (
                plan[i+1][j] == 16
                and plan[i][j + 1] == 16
                and plan[i][j] != 16
                and plan[i+1][j+1] != 16
                and plan[i][j] != 17
                and plan[i+1][j+1] != 17
            ):
                if random.random() < 0.5:
                    plan[i][j] = 16
                else:
                    plan[i+1][j+1] = 16
            if (
                plan[i+1][j] == 17
                and plan[i][j + 1] == 17
                and plan[i][j] != 17
                and plan[i+1][j+1] != 17
                and plan[i][j] != 16
                and plan[i+1][j+1] != 16
            ):
                if random.random() < 0.5:
                    plan[i][j] = 17
                else:
                    plan[i+1][j+1] = 17


def plan2scene(args):
    plan, model_data, idx = args
    connect_roads(plan)
    ### decide border edges
    border_edges = []
    for i in range(WIDTH_L):
        for j in range(HEIGHT_L):
            if i < WIDTH_L - 1 and plan[i][j] != plan[i + 1][j]:
                border_edges.append(((i + 1, j), (i + 1, j + 1)))
            if j < HEIGHT_L - 1 and plan[i][j] != plan[i][j + 1]:
                border_edges.append(((i, j + 1), (i + 1, j + 1)))
    border_edges.extend([((i, 0), (i + 1, 0)) for i in range(WIDTH_L)])
    border_edges.extend([((i, HEIGHT_L), (i + 1, HEIGHT_L)) for i in range(WIDTH_L)])
    border_edges.extend([((0, j), (0, j + 1)) for j in range(HEIGHT_L)])
    border_edges.extend([((WIDTH_L, j), (WIDTH_L, j + 1)) for j in range(HEIGHT_L)])

    ### decide control corners and group_points_list
    components = find_connected_components(plan, 18)
    area_centers_and_types = []
    for i in range(len(components)):
        for j in range(len(components[i])):
            component = components[i][j]
            minx, miny, maxx, maxy = 1e9, 1e9, -1, -1
            for p in component:
                minx = min(minx, p[0])
                miny = min(miny, p[1])
                maxx = max(maxx, p[0] + 1)
                maxy = max(maxy, p[1] + 1)
            area_centers_and_types.append(((minx + maxx) / 2, (miny + maxy) / 2, i))
    unit2bounds = [[None for _ in range(HEIGHT_L)] for _ in range(WIDTH_L)]
    for type in range(len(components)):
        for component in components[type]:
            minx, miny, maxx, maxy = 1e9, 1e9, -1, -1
            for p in component:
                minx = min(minx, p[0])
                miny = min(miny, p[1])
                maxx = max(maxx, p[0] + 1)
                maxy = max(maxy, p[1] + 1)
            for p in component:
                unit2bounds[p[0]][p[1]] = (minx, miny, maxx, maxy)

    control_corners = []
    point_cnt = {}
    for edge in border_edges:
        for point in edge:
            if point not in point_cnt:
                point_cnt[point] = 0
            point_cnt[point] += 1
    for point in point_cnt:
        if point_cnt[point] >= 3:
            control_corners.append(point)
            continue
        x, y = point
        units = [(x, y), (x - 1, y), (x, y - 1), (x - 1, y - 1)]
        type_cnts = {}
        for ux, uy in units:
            if ux < 0 or ux >= WIDTH_L or uy < 0 or uy >= HEIGHT_L:
                continue
            utype = plan[ux][uy]
            if utype not in type_cnts:
                type_cnts[utype] = 0
            type_cnts[utype] += 1
        valid = False
        for ux, uy in units:
            if ux < 0 or ux >= WIDTH_L or uy < 0 or uy >= HEIGHT_L:
                continue
            if type_cnts[plan[ux][uy]] != 1:
                continue
            xl, yl, xh, yh = unit2bounds[ux][uy]
            if xl == x or xh == x or yl == y or yh == y:
                valid = True
                break
        if valid:
            control_corners.append(point)

    border_edge_group = {}
    for edge in border_edges:
        border_edge_group[edge] = -1
    group_points_list = []
    group_cnt = 0
    for x, y in control_corners:
        start_corner = (x, y)
        edges = [((x, y), (x + 1, y)), ((x, y), (x, y + 1)), ((x - 1, y), (x, y)), ((x, y - 1), (x, y))]
        for edge in edges:
            if not (edge in border_edge_group and border_edge_group[edge] == -1):
                continue
            # starting from this edge, find all edges in the same group
            border_edge_group[edge] = group_cnt
            now_corner = edge[0] if edge[0] != start_corner else edge[1]
            group_points = [start_corner, now_corner]
            while now_corner not in control_corners:
                nx, ny = now_corner
                next_edges = [
                    ((nx, ny), (nx + 1, ny)),
                    ((nx, ny), (nx, ny + 1)),
                    ((nx - 1, ny), (nx, ny)),
                    ((nx, ny - 1), (nx, ny)),
                ]
                for next_edge in next_edges:
                    if (next_edge in border_edge_group) and border_edge_group[next_edge] == -1:
                        border_edge_group[next_edge] = group_cnt
                        now_corner = next_edge[0] if next_edge[0] != now_corner else next_edge[1]
                        group_points.append(now_corner)
                        break
            group_cnt += 1
            group_points_list.append(group_points)

    ### generate continuous edges
    refined_point_list, point2idx = set(), {}
    refined_group_points_list = []
    poly = Polygon([(0, 0), (WIDTH_L, 0), (WIDTH_L, HEIGHT_L), (0, HEIGHT_L)])
    for i in range(len(group_points_list)):
        group_points = group_points_list[i]
        x_list, y_list = [], []
        for j in range(len(group_points)):
            x_list.append(group_points[j][0])
            y_list.append(group_points[j][1])
            if j < len(group_points) - 1:
                x_list.append((group_points[j][0] + group_points[j + 1][0]) / 2)
                y_list.append((group_points[j][1] + group_points[j + 1][1]) / 2)
        weights = [1 for _ in range(len(x_list))]
        weights[0] = 1e5
        weights[-1] = 1e5
        tck, _ = interp.splprep(
            [x_list, y_list], s=len(x_list), k=min(max(3, len(x_list) // 2), min(5, len(x_list) - 1)), w=weights
        )
        xx, yy = interp.splev(np.linspace(0, 1, (len(group_points) - 1) * 3), tck, der=0)
        refined_group_points = (
            [(x_list[0], y_list[0])] + [(xx[k], yy[k]) for k in range(1, len(xx) - 1)] + [(x_list[-1], y_list[-1])]
        )
        for j in range(len(refined_group_points)):
            refined_point_list.add(refined_group_points[j])
        refined_group_points_list.append(refined_group_points)
        for j in range(len(refined_group_points) - 1):
            x1, x2, y1, y2 = (
                refined_group_points[j][0],
                refined_group_points[j + 1][0],
                refined_group_points[j][1],
                refined_group_points[j + 1][1],
            )
            normalx, normaly = y2 - y1, x1 - x2
            sqrtxy = sqrt(normalx**2 + normaly**2)
            normalx, normaly = 1e-4 * normalx / sqrtxy, 1e-4 * normaly / sqrtxy
            diff_poly = Polygon(
                [
                    (x1 + normalx, y1 + normaly),
                    (x1 - normalx, y1 - normaly),
                    (x2 - normalx, y2 - normaly),
                    (x2 + normalx, y2 + normaly),
                ]
            )
            poly = poly.difference(diff_poly)
    refined_point_list = list(refined_point_list)
    for i, point in enumerate(refined_point_list):
        point2idx[point] = i
    for i in range(len(refined_group_points_list)):
        group_points = refined_group_points_list[i]
        group_edges = []
        for j in range(len(group_points) - 1):
            group_edges.append((point2idx[group_points[j]], point2idx[group_points[j + 1]]))

    ### decide regions
    areas_types_and_polys = []
    polys = [poly] if isinstance(poly, Polygon) else list(poly.geoms)
    for poly in polys:
        if isinstance(poly, Polygon):
            minx, miny, maxx, maxy = poly.bounds
            centerx, centery = (minx + maxx) / 2, (miny + maxy) / 2
            mindis, minidx = 1e9, -1
            for i in range(len(area_centers_and_types)):
                dis = abs(area_centers_and_types[i][0] - centerx) + abs(area_centers_and_types[i][1] - centery)
                if dis < mindis:
                    mindis, minidx = dis, i
            scaled_poly = scale(poly, 2, 2, origin=(0, 0))
            areas_types_and_polys.append((area_centers_and_types[minidx][2], scaled_poly))

    ### fill areas and generate scene
    res = fill_areas(areas_types_and_polys, model_data)
    output_scene(areas_types_and_polys, res, model_data, str(idx))


def main():
    if not os.path.exists("outputs"):
        os.makedirs("outputs")
    model_data_json = open("object/data.json", "r")
    model_data = json.load(model_data_json)
    plans = []
    for name in os.listdir("evaluate"):
        if name.endswith(".png"):
            with open("evaluate/" + name, "rb") as f:
                img = cv2.imread("evaluate/" + name)
                plan = []
                for i in range(img.shape[0]):
                    plan.append([])
                    for j in range(img.shape[1]):
                        plan[-1].append(color2type(tuple((img[i][j])[::-1])))
                plans.append(plan)
    plans = plans[:MAX_NUM]
    with Pool(PROCESS_COUNT) as p:
        _ = list(
            tqdm(p.imap(plan2scene, [(plans[idx], model_data, idx) for idx in range(len(plans))]), total=len(plans))
        )
    # for idx in tqdm(range(len(plans))):
    #     plan2scene((plans[idx], model_data, idx))
    model_data_json.close()


if __name__ == "__main__":
    main()
