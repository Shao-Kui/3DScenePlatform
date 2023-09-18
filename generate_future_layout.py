import random
import os
from tqdm import tqdm
from math import *
import numpy as np
import sys
import math
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
from shapely.geometry import *
from shapely.affinity import *
from shapely.ops import *
import shapely.speedups
shapely.speedups.enable()
import queue
import json
import imageio
from multiprocessing import Pool
from copy import deepcopy
from typing import List
from time import time
from numba import jit

# scene constants
WALLHEIGHT = 2.6
DEFAULT_FOV = 75

# global
PROCESS_COUNT = 8
SCENE_COUNT_THRES = 1000  # limit for scenes
MAX_ITER = 3000
FORCE_ITER_THRES = 20
FORCE_COST_THRES = 1

ACCEPT_THRE = 0.5

EPS = 1e-4

# generation
BIG_DIV = 4096
NEAR_THRES = 0.1  # meter
DISCRETE_STEP = 0.25  # meter
MOVE_SPEED = 4  # meter per second
ROTATE_SPEED = pi  # radian per second
TRANSFORM_TIME = 1  # second

# video
FRAME_TIME_STEP = 0.05  # second
FPS = 20

global_colors = [(0.8, 0, 0), (0, 0.8, 0), (0, 0, 0.8), (0.8, 0.8, 0), (0.8, 0, 0.8),
                 (0, 0.8, 0.8)] + [(0, 0, 0) for i in range(100)]  # 0red, 1green, 2blue, 3yellow, 4purple, 5cyan


class SpaceColumn:
    def __init__(self, x: float, ymin: float, ymax: float, towards: int):
        self.x = x
        self.ymin = ymin
        self.ymax = ymax
        self.towards = towards


class SpaceRow:
    def __init__(self, y: float, xmin: float, xmax: float, towards: int):
        self.y = y
        self.xmin = xmin
        self.xmax = xmax
        self.towards = towards


class Door:
    def __init__(self, p: np.ndarray, towards: int, width: float, height: float):
        self.p = p
        self.towards = towards
        self.width = width
        self.height = height
        xmin, xmax, ymin, ymax = 0, 0, 0, 0
        if towards == 0:
            xmin, xmax = p[0] - width / 2, p[0] + width / 2
            ymin, ymax = p[2], p[2] + width
        elif towards == 1:
            xmin, xmax = p[0], p[0] + width / 2
            ymin, ymax = p[2] - width / 2, p[2] + width / 2
        elif towards == 2:
            xmin, xmax = p[0] - width / 2, p[0] + width / 2
            ymin, ymax = p[2] - width, p[2]
        else:
            xmin, xmax = p[0] - width / 2, p[0]
            ymin, ymax = p[2] - width / 2, p[2] + width / 2
        self.domain = Polygon([(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax)])


class Window:
    def __init__(self, p: np.ndarray, towards: int, width: float, height: float):
        self.p = p
        self.towards = towards
        self.width = width
        self.height = height


class TwoDimSpace:
    def __init__(self, pointList: List[np.ndarray], doors: List[Door], windows: List[Window]):
        self.pointList = pointList
        self.boundbox = Polygon(pointList)
        self.boundary = LinearRing(pointList)
        self.doors = doors
        self.windows = windows
        self.xl, self.yl, self.xh, self.yh = float('inf'), float('inf'), float('-inf'), float('-inf')
        for p in pointList:
            self.xl = min(self.xl, p[0])
            self.xh = max(self.xh, p[0])
            self.yl = min(self.yl, p[1])
            self.yh = max(self.yh, p[1])
        self.walls = []
        self.wallstrings = []
        for i in range(len(pointList)):
            w0, w1 = pointList[i], pointList[(i + 1) % len(pointList)]
            self.wallstrings.append(LineString([w0, w1]))
            x0, y0, x1, y1 = w0[0], w0[1], w1[0], w1[1]
            if abs(x0 - x1) < 1e-4:
                if y0 > y1:
                    self.walls.append(SpaceColumn(x0, y1, y0, 1))
                else:
                    self.walls.append(SpaceColumn(x0, y0, y1, 3))
            else:
                if x0 < x1:
                    self.walls.append(SpaceRow(y0, x0, x1, 0))
                else:
                    self.walls.append(SpaceRow(y0, x1, x0, 2))

    def visualize(self):
        plt.plot([point[0] for point in self.boundary.coords], [point[1] for point in self.boundary.coords],
                 color=(0, 0, 0),
                 linewidth=4)


class Attribute:
    def __init__(self, gtrans: List[dict], wall: List[dict], window: List[dict], door: List[dict]):
        self.gtrans = gtrans
        self.wall = wall
        self.window = window
        self.door = door


class ModuleState:
    def __init__(self, poly: Polygon, attribute_list: List[Attribute], forward: float, name: str):
        self.poly = poly
        self.attribute_list = attribute_list
        self.forward = forward
        self.name = name


class TransformableModule:
    def __init__(self, name: str, sforder: int, state_list: List[ModuleState], state_relation_list: list,
                 init_p: np.ndarray, init_y: float, init_rotation: float, scale: np.ndarray, init_state: int,
                 color: tuple):
        self.name = name
        self.sforder = sforder
        self.state_list = state_list
        self.state_relation_list = state_relation_list
        self.state = init_state
        self.p = init_p
        self.y = init_y
        self.rotation = init_rotation
        self.scale = scale
        # self.if_moving = False
        self.seq_list = []
        self.color = color
        self.target_state = -1
        self.target_attribute = -1
        self.gtrans_valid = True
        self.importance = 1
        self.action_count = 0
        self.end = False

    def move_action(self,
                    target_state: int,
                    target_p: np.ndarray,
                    target_rotation: float,
                    space: TwoDimSpace,
                    obstacles: List[Polygon],
                    end_obstacles: List[Polygon],
                    far_p_check: bool = False):
        rotate_angle = (target_rotation - self.rotation) % (2 * pi)
        if rotate_angle > pi:
            rotate_angle -= pi * 2
        if_rotate = False if abs(rotate_angle) < EPS else True
        if_transform = (self.state != target_state)
        relation = self.state_relation_list[self.state][target_state]
        info = TransformInfo(if_rotate, if_transform, relation, rotate_angle, 0)
        seq, far_p = get_path(self.sforder, rotate(self.state_list[self.state].poly, -self.rotation, (0, 0), True),
                              rotate(self.state_list[target_state].poly, -target_rotation, (0, 0), True), info, self.p,
                              target_p, self.y, self.rotation, target_rotation, self.state_list[self.state].name,
                              self.state_list[target_state].name, space, obstacles, end_obstacles, far_p_check, self.name == 'sofa2bench')
        if seq == None:
            # print('fail')
            pass
        else:
            # print('success')
            # print(seq.path)
            # print(seq.info.if_rotate, seq.info.if_transform, seq.info.order, seq.info.p)
            pass
        return seq, far_p

    def interpolate(self, t1: float, t2: float, t: float, p1: np.ndarray, p2: np.ndarray):
        ratio = (t - t1) / (t2 - t1)
        x = p1[0] + ratio * (p2[0] - p1[0])
        y = p1[1] + ratio * (p2[1] - p1[1])
        return (x, y)

    def visualize(self, time: float):
        target_seq = None
        length = len(self.seq_list)
        keep_i = length
        for i in range(length):
            seq = self.seq_list[i]
            if seq.start_time <= time and seq.end_time > time:
                target_seq = seq
                break
            elif seq.start_time > time:
                keep_i = i
                break
        if target_seq == None and keep_i < length:
            poly = self.seq_list[keep_i].poly1.exterior.coords
            plt.fill([point[0] + self.seq_list[keep_i].p1[0] for point in poly],
                     [point[1] + self.seq_list[keep_i].p1[1] for point in poly],
                     color=self.color)
        elif target_seq == None and keep_i == length:
            poly = rotate(self.state_list[self.state].poly, -self.rotation, (0, 0), True).exterior.coords
            plt.fill([point[0] + self.p[0] for point in poly], [point[1] + self.p[1] for point in poly],
                     color=self.color)
        else:
            assert isinstance(target_seq, ActionSequence)
            for i in range(len(target_seq.timelist) - 1):
                if target_seq.timelist[i] <= time and target_seq.timelist[i + 1] > time:
                    if target_seq.transform_i == i:
                        pos = target_seq.path[i]
                        plt.fill([point[0] + pos[0] for point in target_seq.poly1.exterior.coords],
                                 [point[1] + pos[1] for point in target_seq.poly1.exterior.coords],
                                 color=(0.5, 0.5, 0.5))
                    elif target_seq.transform_i == -1 or target_seq.transform_i > i:
                        pos = self.interpolate(target_seq.timelist[i], target_seq.timelist[i + 1], time,
                                               target_seq.path[i], target_seq.path[i + 1])
                        plt.fill([point[0] + pos[0] for point in target_seq.poly1.exterior.coords],
                                 [point[1] + pos[1] for point in target_seq.poly1.exterior.coords],
                                 color=self.color)
                    else:
                        pos = self.interpolate(target_seq.timelist[i], target_seq.timelist[i + 1], time,
                                               target_seq.path[i], target_seq.path[i + 1])
                        plt.fill([point[0] + pos[0] for point in target_seq.poly2.exterior.coords],
                                 [point[1] + pos[1] for point in target_seq.poly2.exterior.coords],
                                 color=self.color)


class TransformInfo:
    def __init__(self, if_rotate: bool, if_transform: bool, relation: int, rotate_angle: float, order: int, p=(0, 0)):
        self.if_rotate = if_rotate
        self.if_transform = if_transform
        self.relation = relation  # 0 for poly1=poly2, 1 for poly1>poly2, -1 for poly1<poly2, -2 for irregular
        self.rotate_angle = rotate_angle  # in radian
        self.order = order  # 1 for rotate first, -1 for transform first
        self.p = p  # the point where the action takes place


class ActionSequence:
    def __init__(self, sforder: int, poly1: Polygon, poly2: Polygon, p1: np.ndarray, p2: np.ndarray, y: float,
                 rotation1: float, rotation2: float, state1: str, state2: str, path: List[np.ndarray],
                 info: TransformInfo):
        self.sforder = sforder
        self.poly1 = poly1  # rotated
        self.poly2 = poly2  # rotated
        self.p1 = p1
        self.p2 = p2
        self.y = y
        self.rotation1 = rotation1
        self.rotation2 = rotation2
        self.state1 = state1
        self.state2 = state2
        self.info = info

        # simplify the path
        old_transform_i = path.index(info.p) if (info.if_rotate or info.if_transform) else -1
        new_path = [path[0]]
        last_dir, new_dir = -1, -1  # 0 for right, 1 for up, 2 for left, 3 for down
        for i in range(1, len(path)):
            x_diff, y_diff = path[i][0] - path[i - 1][0], path[i][1] - path[i - 1][1]
            if abs(x_diff) < EPS:
                if y_diff > 0:
                    new_dir = 1
                else:
                    new_dir = 3
            else:
                if x_diff > 0:
                    new_dir = 0
                else:
                    new_dir = 2
            if new_dir == last_dir:
                if i - 1 == old_transform_i:  # keep the transform point
                    new_path.append(path[i])
                else:
                    new_path[-1] = path[i]
            else:
                new_path.append(path[i])
                last_dir = new_dir
        if info.if_rotate or info.if_transform:
            self.transform_i = new_path.index(info.p)
            new_path.insert(self.transform_i, info.p)
        else:
            self.transform_i = -1
        self.path = new_path

        # get the timelist
        timelist = [0]
        for i in range(1, len(new_path)):
            if i == self.transform_i + 1:
                total_trans_time = 0
                if info.if_transform:
                    total_trans_time += TRANSFORM_TIME
                if info.if_rotate:
                    total_trans_time += abs(info.rotate_angle) / ROTATE_SPEED
                timelist.append(timelist[i - 1] + total_trans_time)
            else:
                dis = math.dist(new_path[i], new_path[i - 1])
                timelist.append(timelist[i - 1] + dis / MOVE_SPEED)
        self.timelist = timelist
        self.keep_time = 0
        self.start_time = 0
        self.end_time = 0
        # print(timelist)
        # print(new_path)

    def set_start_time(self, start_time: float):
        self.start_time = start_time
        self.timelist = [time + start_time for time in self.timelist]
        self.end_time = self.timelist[-1]


def process(mods: List[TransformableModule], space: TwoDimSpace):
    length = len(mods)
    name_list = []
    for mod in mods:
        state_name = mod.name + '#' + mod.state_list[mod.target_state].name
        name_list.append(state_name)
    
    # print(name_list)
    
    f = [False for _ in range(1 << length)]
    f[0] = True
    f_subject_to = []
    f_target_attributes = []
    for i in range(1 << length):
        f_subject_to.append([-1 for _ in range(length)])
        f_target_attributes.append([-1 for _ in range(length)])
    
    for i in range(length):
        mod = mods[i]
        for idx in range(len(mod.state_list[mod.target_state].attribute_list)):
            attribute = mod.state_list[mod.target_state].attribute_list[idx]
            gtrans = attribute.gtrans
            if gtrans is None:
                continue
            for sta in range(1 << length):
                ch = sta
                if (ch & (1 << i)) == 0:
                    continue
                ch -= (1 << i)
                valid = True
                glist = []
                for relation in gtrans:
                    target_name = relation['attachedObjId'] + '#' + relation['currentState']
                    for j in range(length):
                        if name_list[j] == target_name and (ch & (1 << j)) != 0:
                            ch -= (1 << j)
                            glist.append(j)
                            break
                if len(glist) == len(gtrans) and f[ch]:
                    f[sta] = True
                    f_subject_to[sta] = f_subject_to[ch].copy()
                    for j in range(len(glist)):
                        f_subject_to[sta][glist[j]] = i
                    f_target_attributes[sta] = f_target_attributes[ch].copy()
                    f_target_attributes[sta][i] = idx
    cnt = [0 for _ in range(1 << length)]
    for i in range(1, 1 << length):
        cnt[i] = cnt[i - (i & -i)] + 1
    for i in range(length, -1, -1):
        for sta in range(1 << length):
            if cnt[sta] == i and f[sta]:
                success = action_2(mods, space, subject_to=f_subject_to[sta], target_attributes=f_target_attributes[sta])
                if success:
                    return True, f_target_attributes[sta]
    return False, []

def preprocess(mods: List[TransformableModule]):
    all_names = []
    all_name_dict = {}
    length = len(mods)
    # print("length:", length)
    for mod in mods:
        state_name = mod.name + '#' + mod.state_list[mod.target_state].name
        # print(state_name)
        all_names.append(state_name)
        if state_name not in all_name_dict:
            all_name_dict[state_name] = 1
        else:
            all_name_dict[state_name] += 1

    # try to find at least one valid relation
    rand_list = [k for k in range(length)]
    random.shuffle(rand_list)
    subject_to = [-1 for k in range(length)]
    target_attributes = [-1 for k in range(length)]

    for i in range(length):
        i_idx = rand_list[i]
        mod = mods[i_idx]
        state_name = mod.name + '#' + mod.state_list[mod.target_state].name
        att_idx_list = [k for k in range(len(mod.state_list[mod.target_state].attribute_list))]
        random.shuffle(att_idx_list)

        match = False
        for att_idx in att_idx_list:
            attribute = mod.state_list[mod.target_state].attribute_list[att_idx]
            name_dict = {}
            gtrans = attribute.gtrans
            if len(gtrans) == 0:
                continue
            for relation in gtrans:
                target_name = relation['attachedObjId'] + '#' + relation['currentState']
                if target_name not in name_dict:
                    name_dict[target_name] = 1
                else:
                    name_dict[target_name] += 1

            name_dict_copy = deepcopy(name_dict)
            if state_name in name_dict:  # consider itself
                name_dict[state_name] += 1
            for name in all_name_dict:
                if name in name_dict:
                    name_dict[name] -= all_name_dict[name]
            valid = True
            for name in name_dict:
                if name_dict[name] > 0:
                    valid = False
                    break
            if not valid:
                continue
            i_top_parent = top_parent(subject_to, i_idx)
            subject_to_bk = deepcopy(subject_to)
            for j in range(length):
                if i == j:
                    continue
                j_idx = rand_list[j]
                name = all_names[j_idx]
                if name not in name_dict_copy:
                    continue
                if subject_to[j_idx] != -1 or i_top_parent == top_parent(subject_to, j_idx):
                    continue
                subject_to[j_idx] = i_idx
                name_dict_copy[name] -= 1
                if name_dict_copy[name] == 0:
                    name_dict_copy.pop(name)
            match = len(name_dict_copy) == 0
            if match:
                target_attributes[i_idx] = att_idx
                break
            else:
                subject_to = subject_to_bk

    # if 'teapoy2chair#origin' in all_name_dict and 'sofa2bed#origin' in all_name_dict and all_name_dict[
    #         'sofa2bed#origin'] == 2:
    #     print(target_attributes)
    return subject_to, target_attributes


def intersect_check(poly: Polygon, space: TwoDimSpace, obstacles: List[Polygon], check_block: bool = True):
    '''return False if not valid'''
    if poly.intersects(space.boundbox) and (not poly.intersects(space.boundary)):
        if check_block:
            for door in space.doors:
                if poly.intersects(door.domain):
                    return False
        for obs in obstacles:
            if poly.intersects(obs):
                return False
        return True
    return False


def to_obstacles(mods: List[TransformableModule], exclude_idx: int):
    obstacles = []
    for i in range(len(mods)):
        if i != exclude_idx:
            poly = translate(rotate(mods[i].state_list[mods[i].state].poly, -mods[i].rotation, (0, 0), True),
                             mods[i].p[0], mods[i].p[1])
            obstacles.append(poly)
    return obstacles


def get_all_paths(start_mods: List[TransformableModule], end_mods: List[TransformableModule], space: TwoDimSpace):
    # st = time()
    length = len(start_mods)
    # ori_mods = deepcopy(start_mods)
    end_path_valid = [False for k in range(length)]
    end_obstacles = to_obstacles(end_mods, -1)
    for i in range(length):
        start_mod = start_mods[i]
        obstacles = to_obstacles(end_mods, i)
        res, far_p = start_mod.move_action(end_mods[i].state, end_mods[i].p, end_mods[i].rotation, space, obstacles,
                                           end_obstacles)
        if res != None:
            end_path_valid[i] = True

    finished = [False for k in range(length)]
    moved = [False for k in range(length)]
    seqs = []
    time_now = 0
    global_success = True
    while True:
        not_fin_list = []
        pri_list = []
        for i in range(length):
            if not finished[i]:
                if end_path_valid[i] == False:
                    pri_list.append(i)
                else:
                    not_fin_list.append(i)
        if len(not_fin_list) == 0 and len(pri_list) == 0:
            break
        random.shuffle(pri_list)
        random.shuffle(not_fin_list)
        pri_list += not_fin_list
        candidate_idx = []
        target_idx = None

        farthest_move_idx, farthest_move_dis, farthest_p = None, 0, None
        for idx in pri_list:
            start_mod = start_mods[idx]
            obstacles = to_obstacles(start_mods, idx)
            seq, far_p = start_mod.move_action(start_mod.target_state, end_mods[idx].p, end_mods[idx].rotation, space,
                                               obstacles, end_obstacles, True)
            if seq == None:
                far_move_dis = abs((far_p - start_mod.p)[0]) + abs((far_p - start_mod.p)[1])
                if far_move_dis > farthest_move_dis and moved[idx] == False:
                    farthest_move_dis = far_move_dis
                    farthest_move_idx = idx
                    farthest_p = far_p
            if seq != None and end_path_valid[idx] == False:  # can move now, but cannot move in the end
                target_idx = idx
                break
            elif seq != None:  # can move now and in the end
                candidate_idx.append(idx)

        if target_idx == None and len(candidate_idx) == 0:  # tmp fail
            if farthest_move_idx == None:  # give up
                global_success = False
                break
            # move one as far as possible
            # print('ex move')
            start_mod = start_mods[farthest_move_idx]
            obstacles = to_obstacles(start_mods, farthest_move_idx)
            seq, far_p = start_mod.move_action(start_mod.state, farthest_p, start_mod.rotation, space, obstacles,
                                               end_obstacles)
            if seq == None:  # unexpected
                global_success = False
                break
            seq = crosspath_decision(seq, seqs)
            time_now = max(time_now, seq.end_time)
            if len(start_mod.seq_list) > 0:
                seq.keep_time = start_mod.seq_list[-1].end_time
            start_mod.seq_list.append(seq)
            seqs.append(seq)
            start_mod.p = seq.p2
            moved[farthest_move_idx] = True
            continue
        elif target_idx == None:
            target_idx = candidate_idx[0]  # choose the first one

        finished[target_idx] = True
        moved = [False for k in range(length)]
        start_mod = start_mods[target_idx]
        obstacles = to_obstacles(start_mods, target_idx)
        seq, far_p = start_mod.move_action(start_mod.target_state, end_mods[target_idx].p,
                                           end_mods[target_idx].rotation, space, obstacles, end_obstacles)
        seq = crosspath_decision(seq, seqs)
        time_now = max(time_now, seq.end_time)
        if len(start_mod.seq_list) > 0:
            seq.keep_time = start_mod.seq_list[-1].end_time
        start_mod.seq_list.append(seq)
        seqs.append(seq)
        start_mod.p = seq.p2
        start_mod.rotation = seq.rotation2
        start_mod.state = start_mod.target_state

    # print(time() - st)
    return global_success, time_now


def get_path(sforder: int, poly1: Polygon, poly2: Polygon, info: TransformInfo, p1: np.ndarray, p2: np.ndarray,
             path_y: float, rotation1: float, rotation2: float, state1: str, state2: str, space: TwoDimSpace,
             obstacles: List[Polygon], end_obstacles: List[Polygon], far_p_check: bool, hack_bound: bool):
    # start_t = time()
    if_rotate, if_transform, relation = info.if_rotate, info.if_transform, info.relation
    xl, yl, xh, yh = space.xl, space.yl, space.xh, space.yh
    x1, y1, x2, y2 = p1[0], p1[1], p2[0], p2[1]
    if (not intersect_check(translate(poly1, x1, y1), space, obstacles, False)):
        return None, np.array([x1, y1], 'float32')
    r1, r2 = -1, -1
    for p in poly1.exterior.coords:
        r1 = max(r1, sqrt(p[0]**2 + p[1]**2))
    for p in poly2.exterior.coords:
        r2 = max(r2, sqrt(p[0]**2 + p[1]**2))
    rmin = min(r1, r2)

    minlen, len1, len2 = min(min(poly1.bounds[2] - poly1.bounds[0], poly1.bounds[3] - poly1.bounds[1]),
                             min(poly2.bounds[2] - poly2.bounds[0], poly2.bounds[3] - poly2.bounds[1])), max(
                                 poly1.bounds[2] - poly1.bounds[0],
                                 poly1.bounds[3] - poly1.bounds[1]), max(poly2.bounds[2] - poly2.bounds[0],
                                                                         poly2.bounds[3] - poly2.bounds[1])
    blank = deepcopy(space.boundbox)
    for obs in obstacles:
        blank = blank.difference(obs)
    blank_1, blank_2 = deepcopy(blank), deepcopy(blank)
    blank, blank_1, blank_2 = blank.buffer(-minlen / 2), blank_1.buffer(-len1), blank_2.buffer(-len2)
    point1, point2 = Point(x1, y1), Point(x2, y2)
    if isinstance(blank, MultiPolygon) and len(blank.geoms) > 1:
        p1_inside, p2_inside = -1, -1
        for i in range(len(blank.geoms)):
            if blank.geoms[i].contains(point1):
                p1_inside = i
            if blank.geoms[i].contains(point2):
                p2_inside = i
        if p1_inside >= 0 and p2_inside >= 0 and p1_inside != p2_inside:
            return None, np.array([x1, y1], 'float32')

    # get the web structure
    x_web, y_web = {}, {}
    x_web[0], y_web[0] = x1, y1

    xl_index, yl_index, xh_index, yh_index = float('inf'), float('inf'), float('-inf'), float('-inf')
    xtarget_index, ytarget_index = 0, 0

    x_index, x_now = 0, x1
    while True:
        x_index -= 1
        if (x_now - DISCRETE_STEP - x2) * (x_now - x2) >= 0:
            x_now -= DISCRETE_STEP
        else:
            x_now = x2
        if abs(x_now - x2) < EPS:
            xtarget_index = x_index
        if x_now > xl:
            x_web[x_index] = x_now
        else:
            xl_index = x_index + 1
            break
    x_index, x_now = 0, x1
    while True:
        x_index += 1
        if (x_now + DISCRETE_STEP - x2) * (x_now - x2) >= 0:
            x_now += DISCRETE_STEP
        else:
            x_now = x2
        if abs(x_now - x2) < EPS:
            xtarget_index = x_index
        if x_now < xh:
            x_web[x_index] = x_now
        else:
            xh_index = x_index - 1
            break
    y_index, y_now = 0, y1
    while True:
        y_index -= 1
        if (y_now - DISCRETE_STEP - y2) * (y_now - y2) >= 0:
            y_now -= DISCRETE_STEP
        else:
            y_now = y2
        if abs(y_now - y2) < EPS:
            ytarget_index = y_index
        if y_now > yl:
            y_web[y_index] = y_now
        else:
            yl_index = y_index + 1
            break
    y_index, y_now = 0, y1
    while True:
        y_index += 1
        if (y_now + DISCRETE_STEP - y2) * (y_now - y2) >= 0:
            y_now += DISCRETE_STEP
        else:
            y_now = y2
        if abs(y_now - y2) < EPS:
            ytarget_index = y_index
        if y_now < yh:
            y_web[y_index] = y_now
        else:
            yh_index = y_index - 1
            break

    check_flag1, check_flag2 = [[[False for j in range(yh_index - yl_index + 1)]
                                 for i in range(xh_index - xl_index + 1)] for k in range(2)]
    pre_index1, pre_index2 = [[[None for j in range(yh_index - yl_index + 1)] for i in range(xh_index - xl_index + 1)]
                              for k in range(2)]

    pri_quene = queue.PriorityQueue()

    reachable_index1, reachable_index2, reachable_index3 = [(0, 0)], [(xtarget_index, ytarget_index)], []
    path_index, path_index1, path_index2, path_index3 = [], [], [], []

    if xtarget_index != 0 or ytarget_index != 0:
        # forward(1)
        pri_quene.put((abs(x1 - x2) + abs(y1 - y2), (0, 0, 0, -1)))
        check_flag1[0][0] = check_flag2[xtarget_index][ytarget_index] = True
        while not pri_quene.empty():
            pos = pri_quene.get()
            x_index, y_index, turn_count, last_dir = (int)(pos[1][0]), (int)(pos[1][1]), (int)(pos[1][2]), (int)(
                pos[1][3])

            new_index = [(x_index + 1, y_index), (x_index, y_index + 1), (x_index - 1, y_index), (x_index, y_index - 1)]
            k = 0
            for new_x_index, new_y_index in new_index:
                if new_x_index >= xl_index and new_x_index <= xh_index and new_y_index >= yl_index and new_y_index <= yh_index and check_flag1[
                        new_x_index][new_y_index] == False:
                    check_flag1[new_x_index][new_y_index] = True
                    new_x, new_y = x_web[new_x_index], y_web[new_y_index]
                    if Point(new_x, new_y).within(blank_1) or intersect_check(translate(poly1, new_x, new_y), space,
                                                                              obstacles, False):
                        reachable_index1.append((new_x_index, new_y_index))
                        new_turn_count = turn_count + 1 if k != last_dir else turn_count
                        pri_quene.put(
                            (abs(new_x - x1) + abs(new_y - y1) + abs(new_x - x2) + abs(new_y - y2) + new_turn_count,
                             (new_x_index, new_y_index, new_turn_count, k)))
                        pre_index1[new_x_index][new_y_index] = (x_index, y_index)
                        if new_x_index == xtarget_index and new_y_index == ytarget_index:  # reach the target
                            break
                k += 1
        if pre_index1[xtarget_index][ytarget_index] != None:
            # print('forward path succeed')
            x_index, y_index = xtarget_index, ytarget_index
            while x_index != 0 or y_index != 0:
                path_index1.append((x_index, y_index))
                x_index, y_index = pre_index1[x_index][y_index]
            path_index1.append((0, 0))
            path_index1 = path_index1[::-1]

        if not intersect_check(translate(poly2, x2, y2), space, obstacles, False):
            far_p, far_dis = None, 0
            if far_p_check:
                for index in reachable_index1:
                    x, y = x_web[index[0]], y_web[index[1]]
                    if not intersect_check(translate(poly1, x, y), space, end_obstacles, False):
                        continue
                    dis = abs(x - x1) + abs(y - y1)
                    if dis > far_dis:
                        far_dis = dis
                        far_p = (x, y)
            return None, np.array(far_p, 'float32')
        # backward(2)
        pri_quene.put((abs(x1 - x2) + abs(y1 - y2), (xtarget_index, ytarget_index, 0, -1)))
        while not pri_quene.empty():
            pos = pri_quene.get()
            x_index, y_index, turn_count, last_dir = (int)(pos[1][0]), (int)(pos[1][1]), (int)(pos[1][2]), (int)(
                pos[1][3])

            new_index = [(x_index + 1, y_index), (x_index, y_index + 1), (x_index - 1, y_index), (x_index, y_index - 1)]
            k = 0
            for new_x_index, new_y_index in new_index:
                if new_x_index >= xl_index and new_x_index <= xh_index and new_y_index >= yl_index and new_y_index <= yh_index and check_flag2[
                        new_x_index][new_y_index] == False:
                    check_flag2[new_x_index][new_y_index] = True
                    new_x, new_y = x_web[new_x_index], y_web[new_y_index]
                    if Point(new_x, new_y).within(blank_2) or intersect_check(translate(poly2, new_x, new_y), space,
                                                                              obstacles, False):
                        reachable_index2.append((new_x_index, new_y_index))
                        new_turn_count = turn_count + 1 if k != last_dir else turn_count
                        pri_quene.put(
                            (abs(new_x - x1) + abs(new_y - y1) + abs(new_x - x2) + abs(new_y - y2) + new_turn_count,
                             (new_x_index, new_y_index, new_turn_count, k)))
                        pre_index2[new_x_index][new_y_index] = (x_index, y_index)
                        if new_x_index == 0 and new_y_index == 0:  # reach the origin
                            break
                k += 1
        if pre_index2[0][0] != None:
            # print('backward path succeed')
            x_index, y_index = 0, 0
            while x_index != xtarget_index or y_index != ytarget_index:
                path_index2.append((x_index, y_index))
                x_index, y_index = pre_index2[x_index][y_index]
            path_index2.append((xtarget_index, ytarget_index))
            path_index2 = path_index2[::-1]

    reachable_index3 = list(set(reachable_index1).intersection(set(reachable_index2)))
    path_index3 = list(set(path_index1).intersection(set(path_index2)))

    if hack_bound:
        idx3_remove = []
        for idx in reachable_index3:
            new_poly1 = scale(poly1, 1.2, 2.5)
            new_poly2 = scale(poly2, 1.2, 2.5)
            new_poly = new_poly1.union(new_poly2)
            new_x, new_y = x_web[idx[0]], y_web[idx[1]]
            if not intersect_check(translate(new_poly, new_x, new_y), space, obstacles, False):
                idx3_remove.append(idx)
        for idx in idx3_remove:
            reachable_index3.remove(idx)

    # get the full path
    seq, far_p = None, None
    new_info = info
    if if_rotate == False:
        if relation == 0:  # the easiest
            if len(path_index1) > 0:
                path = [(x_web[index[0]], y_web[index[1]]) for index in path_index1]
                seq = ActionSequence(sforder, poly1, poly2, p1, p2, path_y, rotation1, rotation2, state1, state2, path,
                                     new_info)
        elif relation == 1:  # transform immediately
            if len(path_index2) > 0:
                path = [(x_web[index[0]], y_web[index[1]]) for index in path_index2[::-1]]
                new_info.p = (x1, y1)
                seq = ActionSequence(sforder, poly1, poly2, p1, p2, path_y, rotation1, rotation2, state1, state2, path,
                                     new_info)
        elif relation == -1:  # transform at the end
            if len(path_index1) > 0:
                path = [(x_web[index[0]], y_web[index[1]]) for index in path_index1]
                new_info.p = (x2, y2)
                seq = ActionSequence(sforder, poly1, poly2, p1, p2, path_y, rotation1, rotation2, state1, state2, path,
                                     new_info)
        else:  # pick a point and transform
            if len(reachable_index3) > 0:
                if len(path_index3) > 0:
                    transform_index = path_index3[0]
                    path_index = path_index1[:path_index1.index(transform_index
                                                                )] + path_index2[path_index2.index(transform_index)::-1]
                else:
                    mindis = float('inf')
                    transform_index = None
                    for id in reachable_index3:
                        dis = abs(x_web[id[0]] - x1) + abs(x_web[id[0]] - x2) + abs(y_web[id[1]] -
                                                                                    y1) + abs(y_web[id[1]] - y2)
                        if dis < mindis:
                            transform_index = id
                            mindis = dis
                    x_index, y_index = transform_index
                    path_index1, path_index2 = [], []
                    while x_index != 0 or y_index != 0:
                        path_index1.append((x_index, y_index))
                        x_index, y_index = pre_index1[x_index][y_index]
                    path_index1.append((0, 0))
                    x_index, y_index = transform_index
                    while x_index != xtarget_index or y_index != ytarget_index:
                        path_index2.append((x_index, y_index))
                        x_index, y_index = pre_index2[x_index][y_index]
                    path_index2.append((xtarget_index, ytarget_index))
                    path_index = path_index1[::-1] + path_index2[1:]
                path = [(x_web[index[0]], y_web[index[1]]) for index in path_index]
                new_info.p = (x_web[transform_index[0]], y_web[transform_index[1]])
                seq = ActionSequence(sforder, poly1, poly2, p1, p2, path_y, rotation1, rotation2, state1, state2, path,
                                     new_info)
    else:
        if len(reachable_index3) > 0:
            blank_3 = deepcopy(space.boundbox)
            for obs in obstacles:
                blank_3 = blank_3.difference(obs)
            blank_3 = blank_3.buffer(-rmin)
            mindis = float('inf')
            transform_index = None
            for id in path_index3:
                if Point(x_web[id[0]], y_web[id[1]]).within(blank_3):
                    dis = abs(x_web[id[0]] - x1) + abs(x_web[id[0]] - x2) + abs(y_web[id[1]] - y1) + abs(y_web[id[1]] -
                                                                                                         y2)
                    if dis < mindis:
                        transform_index = id
                        mindis = dis
            if transform_index == None:
                for id in reachable_index3:
                    if Point(x_web[id[0]], y_web[id[1]]).within(blank_3):
                        dis = abs(x_web[id[0]] - x1) + abs(x_web[id[0]] - x2) + abs(y_web[id[1]] -
                                                                                    y1) + abs(y_web[id[1]] - y2)
                        if dis < mindis:
                            transform_index = id
                            mindis = dis
            if transform_index != None:
                x_index, y_index = transform_index
                path_index1, path_index2 = [], []
                while x_index != 0 or y_index != 0:
                    path_index1.append((x_index, y_index))
                    x_index, y_index = pre_index1[x_index][y_index]
                path_index1.append((0, 0))
                x_index, y_index = transform_index
                while x_index != xtarget_index or y_index != ytarget_index:
                    path_index2.append((x_index, y_index))
                    x_index, y_index = pre_index2[x_index][y_index]
                path_index2.append((xtarget_index, ytarget_index))
                path_index = path_index1[::-1] + path_index2[1:]
                path = [(x_web[index[0]], y_web[index[1]]) for index in path_index]
                new_info.p = (x_web[transform_index[0]], y_web[transform_index[1]])
                if relation == 0 or relation == 1:
                    new_info.order = -1
                elif relation == -1:
                    new_info.order = 1
                else:  # rotate when the radius is small
                    if r1 < r2:
                        new_info.order = 1
                    else:
                        new_info.order = -1
                seq = ActionSequence(sforder, poly1, poly2, p1, p2, path_y, rotation1, rotation2, state1, state2, path,
                                     new_info)

    if seq is None:
        far_dis = 0
        if far_p_check:
            for index in reachable_index1:
                x, y = x_web[index[0]], y_web[index[1]]
                if not intersect_check(translate(poly1, x, y), space, end_obstacles, False):
                    continue
                dis = abs(x - x1) + abs(y - y1)
                if dis > far_dis:
                    far_dis = dis
                    far_p = (x, y)
    # print(time() - start_t)
    return seq, np.array(far_p, 'float32')


def parse_scene(scene: json, scene_name: str):
    origin = deepcopy(scene)
    origin_room = origin['rooms'][0]['objList']
    origin['rooms'][0]['totalAnimaID'] = '{}_anim'.format(scene_name)
    origin['PerspectiveCamera'] = autoPerspectiveCamera(origin)
    room = scene['rooms'][0]
    shape = room['roomShape']
    doors = []
    windows = []

    objects = room['objList']
    mods = []
    global_count = 0
    # use_global_count = True
    obj_i = 0
    for obj in objects:
        if not 'format' in obj:
            pass
        elif obj['format'] == 'glb':
            name = obj['modelId']
            start_state = obj['startState']
            init_p = np.array([obj['translate'][0], obj['translate'][2]], 'float32')
            init_y = obj['translate'][1]
            init_rotation = (obj['orient']) % (2 * pi)
            scale = np.array(obj['scale'], 'float32')

            module_data_json = open('./static/dataset/object_json/{}_data.json'.format(name), 'r')
            module_data = json.load(module_data_json)
            relation_list = module_data['relation']
            state_list = []
            init_state = 0
            idx = 0
            for data in module_data['data']:
                if data['name'] == start_state:
                    init_state = idx
                attribute_list = []
                for attribute in data['priors']:
                    gtrans = attribute['gtrans']
                    wall = attribute['wall']
                    window = attribute['window']
                    door = attribute['door']
                    attribute_list.append(Attribute(gtrans, wall, window, door))
                scaled_poly = [(poly_p[0] * scale[0], poly_p[1] * scale[2]) for poly_p in data['poly']]
                state_list.append(ModuleState(Polygon(scaled_poly), attribute_list, data['forward'], data['name']))
                idx += 1
            # if use_global_count:
            mods.append(
                TransformableModule(name, global_count, state_list, relation_list, init_p, init_y, init_rotation, scale,
                                    init_state, global_colors[global_count]))
            origin_room[obj_i]['sforder'] = global_count
            global_count += 1
            # else:
            #     mods.append(
            #         TransformableModule(sforder, state_list, relation_list, init_p, init_y, init_rotation, init_state,
            #                             global_colors[global_count]))
            module_data_json.close()
        elif obj['format'] == 'Window' or obj['format'] == 'Door':
            p = np.array(obj['translate'], 'float32')
            width = max(obj['bbox']['max'][0] - obj['bbox']['min'][0], obj['bbox']['max'][2] - obj['bbox']['min'][2])
            height = obj['bbox']['max'][1] - obj['bbox']['min'][1]
            towards = None
            if abs(obj['rotate'][1] % (2 * pi)) < 1e-2:
                towards = 0
            elif abs(obj['rotate'][1] % (2 * pi) - pi / 2) < 1e-2:
                towards = 1
            elif abs(obj['rotate'][1] % (2 * pi) - pi) < 1e-2:
                towards = 2
            else:
                towards = 3
            if obj['format'] == 'Window':
                windows.append(Window(p, towards, width, height))
            else:
                doors.append(Door(p, towards, width, height))
        obj_i += 1
    space = TwoDimSpace(shape, doors, windows)

    with open('./static/dataset/infinitelayout/{}_origin.json'.format(scene_name), 'w') as out:
        json.dump(origin, out)
    return space, mods


def output_scene(mods: List[TransformableModule], scene: json, idx: int, scene_name: str, target_attributes: list):
    # out = deepcopy(scene)
    out = {}
    out['origin'] = scene['origin']
    out['id'] = idx
    out['actions'] = []
    for mod in mods:
        # obj_info = {}
        # obj_info['sforder'] = mod.sforder
        seqs = []
        for seq in mod.seq_list:
            actions = []
            assert isinstance(seq, ActionSequence)
            for i in range(len(seq.path) - 1):
                act = {}
                if i == seq.transform_i:
                    if seq.info.if_rotate and seq.info.if_transform:
                        if seq.info.order == 1:  # rotate first
                            act['action'] = 'rotate'
                            act['r1'] = seq.rotation1
                            act['r2'] = seq.rotation2
                            act['t'] = (seq.timelist[i], seq.timelist[i + 1] - TRANSFORM_TIME)
                            actions.append(act)
                            act = {}
                            act['action'] = 'transform'
                            act['s1'] = seq.state1
                            act['s2'] = seq.state2
                            act['t'] = (seq.timelist[i + 1] - TRANSFORM_TIME, seq.timelist[i + 1])
                        else:
                            act['action'] = 'transform'
                            act['s1'] = seq.state1
                            act['s2'] = seq.state2
                            act['t'] = (seq.timelist[i], seq.timelist[i] + TRANSFORM_TIME)
                            actions.append(act)
                            act = {}
                            act['action'] = 'rotate'
                            act['r1'] = seq.rotation1
                            act['r2'] = seq.rotation2
                            act['t'] = (seq.timelist[i] + TRANSFORM_TIME, seq.timelist[i + 1])
                    elif seq.info.if_rotate:
                        act['action'] = 'rotate'
                        act['r1'] = seq.rotation1
                        act['r2'] = seq.rotation2
                        act['t'] = (seq.timelist[i], seq.timelist[i + 1])
                    else:
                        act['action'] = 'transform'
                        act['s1'] = seq.state1
                        act['s2'] = seq.state2
                        act['t'] = (seq.timelist[i], seq.timelist[i + 1])
                else:
                    act['action'] = 'move'
                    act['p1'] = ((float)(seq.path[i][0]), seq.y, (float)(seq.path[i][1]))
                    act['p2'] = ((float)(seq.path[i + 1][0]), seq.y, (float)(seq.path[i + 1][1]))
                    act['t'] = (seq.timelist[i], seq.timelist[i + 1])
                actions.append(act)
            seqs.append(actions)
        # obj_info['seqs'] = seqs
        out['actions'].append(seqs)

    with open('./static/dataset/infinitelayout/{}_anim/{}.json'.format(scene_name, idx), 'w') as outf:
        json.dump(out, outf)

    origin = deepcopy(scene)
    origin_objects = origin['rooms'][0]['objList']
    mod_idx = 0
    for obj in origin_objects:
        if obj['format'] == 'glb':
            obj['translate'] = [(float)(mods[mod_idx].p[0]), mods[mod_idx].y, float(mods[mod_idx].p[1])]
            obj['rotate'] = [0, mods[mod_idx].rotation, 0]
            obj['orient'] = mods[mod_idx].rotation
            obj['startState'] = mods[mod_idx].state_list[mods[mod_idx].state].name

            if target_attributes[mod_idx] != -1:
                mod = mods[mod_idx]
                attribute = mod.state_list[mod.target_state].attribute_list[target_attributes[mod_idx]]
                obj['attachedObj'] = [relation['attachedObjId'] + '#' + relation['currentState'] for relation in attribute.gtrans]
            else:
                obj['attachedObj'] = []
            mod_idx += 1

    with open('./static/dataset/infinitelayout/{}_scenes/{}.json'.format(scene_name, idx), 'w') as testf:
        json.dump(origin, testf)

def output_scene_2(mods: List[TransformableModule], scene: json, idx: int, scene_name: str, target_attributes: list):
    origin = deepcopy(scene)
    origin_objects = origin['rooms'][0]['objList']
    mod_idx = 0
    for obj in origin_objects:
        if obj['format'] == 'glb':
            obj['translate'] = [(float)(mods[mod_idx].p[0]), mods[mod_idx].y, float(mods[mod_idx].p[1])]
            obj['rotate'] = [0, mods[mod_idx].rotation, 0]
            obj['orient'] = mods[mod_idx].rotation
            obj['startState'] = mods[mod_idx].state_list[mods[mod_idx].state].name

            #if target_attributes[mod_idx] != -1:
            #    mod = mods[mod_idx]
            #    attribute = mod.state_list[mod.target_state].attribute_list[target_attributes[mod_idx]]
            #    obj['attachedObj'] = [relation['attachedObjId'] + '#' + relation['currentState'] for relation in attribute.gtrans]
            #else:
            #    obj['attachedObj'] = []
            
            mod_idx += 1

    with open('outputs/{}_scenes/{}.json'.format(scene_name, idx), 'w') as testf:
        json.dump(origin, testf)


def visualize(mods: List[TransformableModule], space: TwoDimSpace, time: float, name: str):
    width = space.boundary.bounds[2] - space.boundary.bounds[0]
    height = space.boundary.bounds[3] - space.boundary.bounds[1]
    if width < height:
        plt.figure(figsize=(10, height / width * 10))
    else:
        plt.figure(figsize=(width / height * 10, 10))
    space.visualize()
    for mod in mods:
        mod.visualize(time)
    plt.xlabel('x')
    plt.ylabel('y')
    ax = plt.gca()
    ax.invert_yaxis()
    plt.savefig(name)
    plt.clf()
    plt.close()


def samplevideo(mods: List[TransformableModule], space: TwoDimSpace, start_time: float, end_time: float, idx: int):
    dir_idx = idx % PROCESS_COUNT
    if not os.path.exists('tmp_images/{}'.format(dir_idx)):
        os.mkdir('tmp_images/{}'.format(dir_idx))
    maxf = (int)((end_time - start_time) / FRAME_TIME_STEP)
    # pool = Pool(8)
    for f in range(maxf):
        t = f * FRAME_TIME_STEP + start_time
        # pool.apply_async(visualize, (mods, space, t, 'tmp_images/{}/{}.png'.format(dir_idx, f)))
        visualize(mods, space, t, 'tmp_images/{}/{}.png'.format(dir_idx, f))
    # pool.close()
    # pool.join()

    images = []
    for f in range(maxf):
        images.append(imageio.imread('tmp_images/{}/{}.png'.format(dir_idx, f)))
    imageio.mimsave('{}.mp4'.format('videos/sample{}'.format(idx)), images, fps=FPS)
    print('sample{} finish'.format(idx))


def crosspath(seq: ActionSequence, ref: ActionSequence):
    if seq.sforder == ref.sforder:
        return [(-10000, ref.end_time)]
    polygons1, polygons2 = [], []
    ref_poly = seq.poly1
    r1, r2 = -1, -1
    for p in seq.poly1.exterior.coords:
        r1 = max(r1, sqrt(p[0]**2 + p[1]**2))
    for p in seq.poly2.exterior.coords:
        r1 = max(r1, sqrt(p[0]**2 + p[1]**2))
    for p in ref.poly1.exterior.coords:
        r2 = max(r2, sqrt(p[0]**2 + p[1]**2))
    for p in ref.poly2.exterior.coords:
        r2 = max(r2, sqrt(p[0]**2 + p[1]**2))

    len1, len2 = len(seq.path), len(ref.path)

    for i in range(len1 - 1):
        if i == seq.transform_i:
            polygons1.append(Point(seq.path[i]).buffer(r1))
            ref_poly = seq.poly2
        else:
            p1, p2 = seq.path[i], seq.path[i + 1]
            xl, yl, xh, yh = ref_poly.bounds
            xl = min(p1[0] + xl, p2[0] + xl)
            yl = min(p1[1] + yl, p2[1] + yl)
            xh = max(p1[0] + xh, p2[0] + xh)
            yh = max(p1[1] + yh, p2[1] + yh)
            bound_poly = Polygon([(xl, yl), (xh, yl), (xh, yh), (xl, yh)])
            polygons1.append(bound_poly)

    ref_poly = ref.poly1
    for i in range(len2 - 1):
        if i == ref.transform_i:
            polygons2.append(Point(ref.path[i]).buffer(r2))
            ref_poly = ref.poly2
        else:
            p1, p2 = ref.path[i], ref.path[i + 1]
            xl, yl, xh, yh = ref_poly.bounds
            xl = min(p1[0] + xl, p2[0] + xl)
            yl = min(p1[1] + yl, p2[1] + yl)
            xh = max(p1[0] + xh, p2[0] + xh)
            yh = max(p1[1] + yh, p2[1] + yh)
            bound_poly = Polygon([(xl, yl), (xh, yl), (xh, yh), (xl, yh)])
            polygons2.append(bound_poly)

    ban_list = []
    for i in range(len1 - 1):
        for j in range(len2 - 1):
            if polygons1[i].intersects(polygons2[j]):
                poly = polygons1[i].intersection(polygons2[j])
                a1, a2, b1, b2 = seq.timelist[i], seq.timelist[i + 1], ref.timelist[j], ref.timelist[j + 1]
                if i != seq.transform_i or i == len1 - 2:
                    poly_a1 = Polygon([
                        (point[0] + seq.path[i][0], point[1] + seq.path[i][1])
                        for point in (seq.poly1.exterior.coords if i < seq.transform_i else seq.poly2.exterior.coords)
                    ])
                    poly_a2 = Polygon([
                        (point[0] + seq.path[i + 1][0], point[1] + seq.path[i + 1][1])
                        for point in (seq.poly1.exterior.coords if i < seq.transform_i else seq.poly2.exterior.coords)
                    ])
                    if i == len1 - 2 and poly_a2.intersects(poly):
                        a2 = 10000
                    a1 += poly_a1.distance(poly) / MOVE_SPEED
                    a2 -= poly_a2.distance(poly) / MOVE_SPEED
                if j != ref.transform_i or j == 0:
                    poly_b1 = Polygon([
                        (point[0] + ref.path[j][0], point[1] + ref.path[j][1])
                        for point in (ref.poly1.exterior.coords if j < ref.transform_i else ref.poly2.exterior.coords)
                    ])
                    poly_b2 = Polygon([
                        (point[0] + ref.path[j + 1][0], point[1] + ref.path[j + 1][1])
                        for point in (ref.poly1.exterior.coords if j < ref.transform_i else ref.poly2.exterior.coords)
                    ])
                    if j == 0 and poly_b1.intersects(poly):
                        b1 = ref.keep_time
                    b1 += poly_b1.distance(poly) / MOVE_SPEED
                    b2 -= poly_b2.distance(poly) / MOVE_SPEED
                ban_list.append((b1 - a2, b2 - a1))
    return ban_list


def crosspath_decision(seq: ActionSequence, seqs: List[ActionSequence]):
    ban = [(-10000, 0)]
    for ref in seqs:
        ban += crosspath(seq, ref)
    min_valid_time = inf
    for i in range(len(ban)):
        success_flag = True
        for j in range(len(ban)):
            if i == j:
                continue
            if ban[i][1] >= ban[j][0] and ban[i][1] <= ban[j][1]:
                success_flag = False
                break
        if success_flag:
            min_valid_time = min(ban[i][1], min_valid_time)

    seq.set_start_time(min_valid_time)
    return seq


def get_totalcost(mods: List[TransformableModule], space: TwoDimSpace):
    totalcost = 0

    for mod in mods:
        if mod.target_attribute == -1:
            continue

        check_flag = [False for k in range(len(mods))]

        # gtrans relation
        if not mod.gtrans_valid:
            totalcost += 10000
        else:
            gtrans = mod.state_list[mod.target_state].attribute_list[mod.target_attribute].gtrans
            for relation in gtrans:
                for i in range(len(mods)):
                    other_mod = mods[i]
                    if other_mod != mod and check_flag[i] == False and other_mod.name == relation[
                            'attachedObjId'] and other_mod.state_list[
                                other_mod.target_state].name == relation['currentState']:
                        rel_p, rel_rot = other_mod.p - mod.p, other_mod.rotation - mod.rotation
                        rel_p = rot(rel_p, -mod.rotation) / np.array([mod.scale[0], mod.scale[2]], 'float32')
                        p_diff = rel_p - np.array([relation['objPosX'], relation['objPosZ']], 'float32')
                        rot_diff = (rel_rot - relation['objOriY']) % (2 * pi)
                        if rot_diff > pi:
                            rot_diff = 2 * pi - rot_diff
                        totalcost += rot_diff * rot_diff + p_diff[0] * p_diff[0] + p_diff[1] * p_diff[
                            1]  #  cost evaluation
                        check_flag[i] = True
                        break

        # wall
        wall = mod.state_list[mod.target_state].attribute_list[mod.target_attribute].wall
        if len(wall) == 1:
            dis1, dis2, ori1 = wall[0]['nearestDistance'], wall[0]['secondDistance'], wall[0]['nearestOrient0']
            nearest_dis_diff, nearest_ang_diff, nearest_index = 100, 1, 0
            second_dis_diff = 100
            p_point = Point(mod.p)
            for i in range(len(space.walls)):
                wall, wallstring = space.walls[i], space.wallstrings[i]
                angle1 = (wall.towards * pi / 2 - ori1 - mod.rotation) % (2 * pi)
                if angle1 > pi:
                    angle1 = 2 * pi - angle1
                if angle1 < pi / 4:
                    wall_dis = wallstring.distance(p_point)
                    if wall.towards % 2 == 0:
                        wall_dis /= mod.scale[2]  # z
                    else:
                        wall_dis /= mod.scale[0]  # x
                    if abs(wall_dis - dis1) < nearest_dis_diff:
                        nearest_dis_diff = abs(wall_dis - dis1)
                        nearest_ang_diff = angle1
                        nearest_index = i
            for i in range(len(space.walls)):
                if i == nearest_index:
                    continue
                wallstring = space.wallstrings[i]
                wall_dis = wallstring.distance(p_point)
                if wall.towards % 2 == 0:
                    wall_dis /= mod.scale[2]  # z
                else:
                    wall_dis /= mod.scale[0]  # x
                if abs(wall_dis - dis2) < second_dis_diff:
                    second_dis_diff = abs(wall_dis - dis2)

                # elif ((wall.towards - 1) % 4) * pi / 2 - ori2 < EPS:
                #     wall_dis = wallstring.distance(poly)
                #     if abs(wall_dis - dis2) < dis_diff2:
                #         dis_diff2 = abs(wall_dis - dis2)
            totalcost += nearest_dis_diff * nearest_dis_diff + second_dis_diff * second_dis_diff / 2 + nearest_ang_diff * nearest_ang_diff * 10

        # window and door
        # window=mod.state_list[mod.target_state].attribute_list[mod.target_attribute].window
        # if len(window)>0:

    return totalcost


def action_optimize(mods: List[TransformableModule], space: TwoDimSpace, totalcost: float, iter: int):
    total_importance = 0
    for mod in mods:
        total_importance += mod.importance
    rand_num = random.randint(0, total_importance - 1)
    target_idx = -1
    for i in range(len(mods)):
        rand_num -= mods[i].importance
        if rand_num < 0:
            target_idx = i
            break
    mod = mods[target_idx]

    ori_p, ori_rotation = deepcopy(mod.p), deepcopy(mod.rotation)
    rand_num = random.randint(0, 23)
    if rand_num < 10:
        mod.p = np.array([mod.p[0] + float(np.random.randn(1)), mod.p[1]], 'float32')
    elif rand_num < 20:
        mod.p = np.array([mod.p[0], mod.p[1] + float(np.random.randn(1))], 'float32')
    elif rand_num < 24:
        mod.rotation = (rand_num - 10) * pi / 2
    else:
        mod.rotation += random.random() * 2 * pi - pi
    target_poly = translate(rotate(mod.state_list[mod.target_state].poly, -mod.rotation, (0, 0), True), mod.p[0],
                            mod.p[1])
    obstacles = to_obstacles(mods, target_idx)
    if not intersect_check(target_poly, space, obstacles):  # reject
        mod.p, mod.rotation = ori_p, ori_rotation
        return totalcost
    else:
        newcost = get_totalcost(mods, space)
        if newcost < totalcost or exp((totalcost - newcost) * 10 / max(sqrt(iter), 10)) > ACCEPT_THRE:  # accept
            pass
        else:  # reject
            mod.p, mod.rotation = ori_p, ori_rotation
        return newcost


def action_transform(mods: List[TransformableModule], space: TwoDimSpace):
    target_idx = random.randint(0, len(mods) - 1)
    mod = mods[target_idx]
    obstacles = to_obstacles(mods, target_idx)
    if mod.state != mod.target_state:
        target_poly = translate(rotate(mod.state_list[mod.target_state].poly, mod.rotation, (0, 0), True), mod.p[0],
                                mod.p[1])
        if intersect_check(target_poly, space, obstacles):
            mod.state = mod.target_state
            return

    ori_p, ori_rotation = deepcopy(mod.p), deepcopy(mod.rotation)
    rand_num = random.randint(0, 23)
    if rand_num < 10:
        mod.p = np.array([mod.p[0] + (float)(np.random.randn(1)), mod.p[1]], 'float32')
    elif rand_num < 20:
        mod.p = np.array([mod.p[0], mod.p[1] + (float)(np.random.randn(1))], 'float32')
    elif rand_num < 24:
        mod.rotation = (rand_num - 10) * pi / 2
    else:
        mod.rotation += random.random() * 2 * pi - pi
    target_poly = translate(rotate(mod.state_list[mod.target_state].poly, -mod.rotation, (0, 0), True), mod.p[0],
                            mod.p[1])
    if not intersect_check(target_poly, space, obstacles):
        mod.p, mod.rotation = ori_p, ori_rotation


def wall_relative(nearest_dis: float, second_dis: float, nearest_rot: float, poly_bounds: tuple, scalex: float,
                  scalez: float, space: TwoDimSpace, force_second: bool):
    wall_count = len(space.walls)
    rand_num = random.randint(0, wall_count - 1)
    wall = space.walls[rand_num]
    second_wall = space.walls[(rand_num + 1) % wall_count if random.randint(0, 1) == 0 else (rand_num - 1) % wall_count]
    target_rot = wall.towards * pi / 2 + nearest_rot
    nearest_dis *= sqrt((sin(nearest_rot) * scalex)**2 + (cos(nearest_rot) * scalez)**2)
    second_dis *= sqrt((sin(nearest_rot) * scalez)**2 + (cos(nearest_rot) * scalex)**2)

    target_x, target_y = None, None
    if wall.towards == 0:
        target_y = wall.y + nearest_dis
    elif wall.towards == 1:
        target_x = wall.x + nearest_dis
    elif wall.towards == 2:
        target_y = wall.y - nearest_dis
    else:
        target_x = wall.x - nearest_dis
    if force_second:
        if second_wall.towards == 0:
            target_y = second_wall.y + second_dis
        elif second_wall.towards == 1:
            target_x = second_wall.x + second_dis
        elif second_wall.towards == 2:
            target_y = second_wall.y - second_dis
        else:
            target_x = second_wall.x - second_dis
    else:
        xl, yl, xh, yh = bound_rot_estimate(poly_bounds, target_rot)
        if target_x is None:
            target_x = random.uniform(wall.xmin - xl + 1e-2, wall.xmax - xh - 1e-2)
        else:
            target_y = random.uniform(wall.ymin - yl + 1e-2, wall.ymax - yh - 1e-2)
    return np.array([target_x, target_y], 'float32'), target_rot

def wall_relative_2(nearest_dis: float, second_dis: float, nearest_rot: float, poly_bounds: tuple, scalex: float, scalez: float, space: TwoDimSpace, force_all: bool):
    wall_count = len(space.walls)
    rand_num = random.randint(0, wall_count - 1)
    wall = space.walls[rand_num]
    second_wall = space.walls[(rand_num + 1) % wall_count if random.randint(0, 1) == 0 else (rand_num - 1) % wall_count]
    target_rot = wall.towards * pi / 2 + nearest_rot
    nearest_dis *= sqrt((sin(nearest_rot) * scalex)**2 + (cos(nearest_rot) * scalez)**2)
    second_dis *= sqrt((sin(nearest_rot) * scalez)**2 + (cos(nearest_rot) * scalex)**2)

    target_x, target_y = None, None

    if force_all:
        if wall.towards == 0:
            target_y = wall.y + nearest_dis
        elif wall.towards == 1:
            target_x = wall.x + nearest_dis
        elif wall.towards == 2:
            target_y = wall.y - nearest_dis
        else:
            target_x = wall.x - nearest_dis
        if second_wall.towards == 0:
            target_y = second_wall.y + second_dis
        elif second_wall.towards == 1:
            target_x = second_wall.x + second_dis
        elif second_wall.towards == 2:
            target_y = second_wall.y - second_dis
        else:
            target_x = second_wall.x - second_dis
        return np.array([target_x, target_y], 'float32'), target_rot
    
    if random.randint(0, 1) == 0:
        if wall.towards == 0:
            target_y = wall.y + nearest_dis
        elif wall.towards == 1:
            target_x = wall.x + nearest_dis
        elif wall.towards == 2:
            target_y = wall.y - nearest_dis
        else:
            target_x = wall.x - nearest_dis
        xl, yl, xh, yh = bound_rot_estimate(poly_bounds, target_rot)
        if target_x is None:
            target_x = random.uniform(wall.xmin - xl + 1e-2, wall.xmax - xh - 1e-2)
        else:
            target_y = random.uniform(wall.ymin - yl + 1e-2, wall.ymax - yh - 1e-2)
    else:
        if second_wall.towards == 0:
            target_y = second_wall.y + second_dis
        elif second_wall.towards == 1:
            target_x = second_wall.x + second_dis
        elif second_wall.towards == 2:
            target_y = second_wall.y - second_dis
        else:
            target_x = second_wall.x - second_dis
        xl, yl, xh, yh = bound_rot_estimate(poly_bounds, target_rot)
        if target_x is None:
            target_x = random.uniform(second_wall.xmin - xl + 1e-2, second_wall.xmax - xh - 1e-2)
        else:
            target_y = random.uniform(second_wall.ymin - yl + 1e-2, second_wall.ymax - yh - 1e-2)

    return np.array([target_x, target_y], 'float32'), target_rot

def stick_to_the_wall(poly: Polygon, space: TwoDimSpace, obstacles: List[Polygon],
                      attribute_list: List[Attribute]):  # TODO: consider door and window
    wall_count = len(space.walls)
    nearest_rot = 0
    att_list = deepcopy(attribute_list)
    random.shuffle(att_list)
    for att in att_list:
        if len(att.wall) > 0:
            nearest_rot = att.wall[0]['nearestOrient0']
            break
    target_poly, target_x, target_y, target_rot = None, None, None, None

    for k in range(100):
        rand_num = random.randint(0, wall_count - 1)
        wall = space.walls[rand_num]
        target_rot = wall.towards * pi / 2 + nearest_rot
        rot_poly = rotate(poly, -target_rot, (0, 0), True)
        xl, yl, xh, yh = rot_poly.bounds
        if wall.towards == 0:
            target_y = wall.y - yl + 1e-2
            target_x = random.uniform(wall.xmin - xl + 1e-2, wall.xmax - xh - 1e-2)
        elif wall.towards == 1:
            target_x = wall.x - xl + 1e-2
            target_y = random.uniform(wall.ymin - yl + 1e-2, wall.ymax - yh - 1e-2)
        elif wall.towards == 2:
            target_y = wall.y - yh - 1e-2
            target_x = random.uniform(wall.xmin - xl + 1e-2, wall.xmax - xh - 1e-2)
        else:
            target_x = wall.x - xh - 1e-2
            target_y = random.uniform(wall.ymin - yl + 1e-2, wall.ymax - yh - 1e-2)
        target_poly = translate(rot_poly, target_x, target_y)
        if intersect_check(target_poly, space, obstacles):
            return True, np.array([target_x, target_y], 'float32'), target_rot, target_poly

    return False, None, None, None


def action_2(mods: List[TransformableModule], space: TwoDimSpace, subject_to: List[int], target_attributes: List[int]):
    length = len(mods)
    for mod in mods:
        mod.state = mod.target_state
    # Fixed. But why?
    # top_parents = [top_parent(subject_to, k) for k in range(length)]
    top_idxes, main_idxes = set(), set()
    for i in range(length):
        # if top_parent[i] == i:
        if subject_to[i] == -1:
            top_idxes.add(i)
        if target_attributes[i] != -1:
            main_idxes.add(i)
    top_idxes , main_idxes = (list)(top_idxes), (list)(main_idxes)

    #print("subject_to", subject_to)
    #print("target_attributes", target_attributes)
    #print("top", top_idxes)
    #print("main", main_idxes)
    #assert top_idxes == main_idxes

    # sort by size
    size = [0 for _ in range(length)]
    for i in range(length):
        main_poly = mod.state_list[mod.target_state].poly
        size[i] = main_poly.area
    top_idxes.sort(key = lambda x: size[x], reverse=True)

    # TODO: considerate wall etc.

    completed = [False for _ in range(length)]
    placed_polys = []
    for idx in top_idxes:
        mod = mods[idx]
        poly_bounds, scalex, scalez = mod.state_list[mod.target_state].poly.bounds, mod.scale[0], mod.scale[2]
        # try:
        attribute = mod.state_list[mod.target_state].attribute_list[target_attributes[idx]]
        # except:
        #     print(len(mod.state_list[mod.target_state].attribute_list),target_attributes)
        #     raise AttributeError
            # exit(1)
        gtrans, wall_rel, door_rel, window_rel = attribute.gtrans, attribute.wall, attribute.door, attribute.window

        tmp_completed = [idx]
        completed[idx] = True

        subs, rel_sub_ps, rel_sub_rots = [], [], []
        for relation in gtrans:
            for i in range(length):
                target = mods[i]
                if i != idx and not completed[i] and target.name == relation['attachedObjId'] and target.state_list[target.target_state].name == relation['currentState']:
                    rel_p = np.array([relation['objPosX'] * scalex, relation['objPosZ'] * scalez], 'float32')
                    rel_rot = relation['objOriY']
                    subs.append(i)
                    rel_sub_ps.append(rel_p)
                    rel_sub_rots.append(rel_rot)
                    completed[i] = True
                    tmp_completed.append(i)
                    break

        place_success = False

        # place once
        for k in range(100):
            main_p, main_rot = None, None
            if len(wall_rel) > 0:
                wall_dict = wall_rel[0]
                nearest_dis, second_dis, nearest_rot = wall_dict['nearestDistance'], wall_dict['secondDistance'], wall_dict['nearestOrient0']
                main_p, main_rot = wall_relative_2(nearest_dis, second_dis, nearest_rot, poly_bounds, scalex, scalez, space, k < 50)
                # wall_relative: place the object relative to the wall randomly
            else:
                space_xl, space_yl, space_xh, space_yh = space.xl, space.yl, space.xh, space.yh
                main_rot = random.randint(0, 3) * pi / 2
                xl, yl, xh, yh = bound_rot_estimate(poly_bounds, main_rot)
                main_p = np.array([random.uniform(space_xl - xl + 1e-2, space_xh - xh - 1e-2), random.uniform(space_yl - yl + 1e-2, space_yh - yh - 1e-2)], 'float32')
                # TODO: condiser door and window

            main_poly = translate(rotate(mod.state_list[mod.target_state].poly, -main_rot, (0, 0), True), main_p[0], main_p[1])
            if not intersect_check(main_poly, space, placed_polys):
                continue
            
            sub_success = True
            sub_polys, sub_ps, sub_rots = [], [], []
            for i in range(len(subs)): 
                sub_mod = mods[subs[i]]
                sub_p = main_p + rot(rel_sub_ps[i], main_rot)
                sub_rot = main_rot + rel_sub_rots[i]
                sub_poly = translate(rotate(sub_mod.state_list[sub_mod.target_state].poly, -sub_rot, (0, 0), True), sub_p[0], sub_p[1])
                if not intersect_check(sub_poly, space, placed_polys):
                    sub_success = False
                    break
                sub_polys.append(sub_poly)
                sub_ps.append(sub_p)
                sub_rots.append(sub_rot)
            if not sub_success:
                continue

            mod.p, mod.rotation = main_p, main_rot
            for i in range(len(subs)):
                sub_mod = mods[subs[i]]
                sub_mod.p, sub_mod.rotation = sub_ps[i], sub_rots[i]
            place_success = True
            placed_polys.append(main_poly)
            placed_polys += sub_polys
            break

        if not place_success:
            # TODO: memory
            for i in tmp_completed:
                completed[i] = False
            continue
    
    for i in range(length):
        if completed[i] == True:
            continue
        mod = mods[i]
        place_success, target_p, target_rot, target_poly = stick_to_the_wall(mod.state_list[mod.target_state].poly, space, placed_polys, mod.state_list[mod.target_state].attribute_list)
        if not place_success:
            return False
        mod.p, mod.rotation = target_p, target_rot
        placed_polys.append(target_poly)
        completed[i] = True
    
    return True

def action(mods: List[TransformableModule], space: TwoDimSpace, subject_to: List[int], target_attributes: List[int]):
    length = len(mods)
    for mod in mods:
        mod.state = mod.target_state
    top_parents = [top_parent(subject_to, k) for k in range(length)]
    top_idxes, main_idxes = set(), set()
    for i in range(length):
        if top_parents[i] != i:
            top_idxes.add(top_parents[i])
        if target_attributes[i] != -1:
            main_idxes.add(i)
    nottop_main_idxes = list(main_idxes - top_idxes)
    top_idxes, main_idxes = (list)(top_idxes), (list)(main_idxes)
    random.shuffle(top_idxes)

    completed = [False for i in range(length)]
    placed_polys = []
    wall_count, door_count, window_count = len(space.walls), len(space.doors), len(space.windows)
    for idx in top_idxes:
        mod = mods[idx]
        poly_bounds, scalex, scalez = mod.state_list[mod.target_state].poly.bounds, mod.scale[0], mod.scale[2]
        attribute = mod.state_list[mod.target_state].attribute_list[target_attributes[idx]]
        gtrans, wall_rel, door_rel, window_rel = attribute.gtrans, attribute.wall, attribute.door, attribute.window
        tmp_completed = [idx]
        completed[idx] = True

        subs, rel_sub_ps, rel_sub_rots = [], [], []
        for relation in gtrans:
            for i in range(length):
                other_mod = mods[i]
                if i != idx and completed[i] == False and other_mod.name == relation[
                        'attachedObjId'] and other_mod.state_list[
                            other_mod.target_state].name == relation['currentState']:
                    rel_p = np.array([relation['objPosX'] * scalex, relation['objPosZ'] * scalez], 'float32')
                    rel_rot = relation['objOriY']
                    subs.append(i)
                    rel_sub_ps.append(rel_p)
                    rel_sub_rots.append(rel_rot)
                    completed[i] = True
                    tmp_completed.append(i)

        place_success = False
        # sub_count = 0
        for k in range(100):
            # place the main obj
            main_p, main_rot = None, None
            if len(wall_rel) > 0:
                wall_dict = wall_rel[0]
                nearest_dis, second_dis, nearest_rot = wall_dict['nearestDistance'], wall_dict[
                    'secondDistance'], wall_dict['nearestOrient0']
                main_p, main_rot = wall_relative(nearest_dis, second_dis, nearest_rot, poly_bounds, scalex, scalez,
                                                 space, k < 50)
            else:  # TODO: consider door and window
                space_xl, space_yl, space_xh, space_yh, = space.xl, space.yl, space.xh, space.yh
                main_rot = random.randint(0, 3) * pi / 2
                xl, yl, xh, yh = bound_rot_estimate(poly_bounds, main_rot)
                main_p = np.array([
                    random.uniform(space_xl - xl + 1e-2, space_xh - xh - 1e-2),
                    random.uniform(space_yl - yl + 1e-2, space_yh - yh - 1e-2)
                ], 'float32')

            main_poly = translate(rotate(mod.state_list[mod.target_state].poly, -main_rot, (0, 0), True), main_p[0],
                                  main_p[1])
            if not intersect_check(main_poly, space, placed_polys):
                # if len(wall_rel) > 0:
                #     print(main_p, main_rot, wall_rel[0]['nearestDistance'], wall_rel[0]['secondDistance'],
                #           wall_rel[0]['nearestOrient0'], poly_bounds, scalex, scalez, mod.name, mod.state,
                #           target_attributes[idx])
                continue
            # sub_count += 1
            # place the sub objs
            sub_success = True
            sub_polys, sub_ps, sub_rots = [], [], []
            for i in range(len(subs)):
                sub_mod = mods[subs[i]]
                sub_p = main_p + rot(rel_sub_ps[i], main_rot)
                sub_rot = main_rot + rel_sub_rots[i]
                sub_poly = translate(rotate(sub_mod.state_list[sub_mod.target_state].poly, -sub_rot, (0, 0), True),
                                     sub_p[0], sub_p[1])
                if not intersect_check(sub_poly, space, placed_polys):
                    # print(mod.name, mod.state, target_attributes[idx], main_p, main_rot, sub_p, sub_rot,
                    #       sub_poly.bounds)
                    sub_success = False
                    break
                sub_polys.append(sub_poly)
                sub_ps.append(sub_p)
                sub_rots.append(sub_rot)
            if not sub_success:
                continue

            # success
            mod.p, mod.rotation = main_p, main_rot
            for i in range(len(subs)):
                sub_mod = mods[subs[i]]
                sub_mod.p, sub_mod.rotation = sub_ps[i], sub_rots[i]
            place_success = True
            placed_polys.append(main_poly)
            placed_polys += sub_polys
            break
        # print(sub_count)
        if not place_success:
            # print('main fail')
            # return False
            for i in tmp_completed:
                completed[i] = False
            continue

        # continue for 1 layer
        for i in subs:
            if i not in nottop_main_idxes:
                continue
            mod = mods[i]
            scalex, scalez = mod.scale[0], mod.scale[2]
            attribute = mod.state_list[mod.target_state].attribute_list[target_attributes[idx]]
            gtrans, wall_rel, door_rel, window_rel = attribute.gtrans, attribute.wall, attribute.door, attribute.window

            for relation in gtrans:
                for j in range(length):
                    other_mod = mods[j]
                    if j != i and completed[j] == False and other_mod.name == relation[
                            'attachedObjId'] and other_mod.state_list[
                                other_mod.target_state].name == relation['currentState']:
                        rel_p = np.array([relation['objPosX'] * scalex, relation['objPosZ'] * scalez], 'float32')
                        rel_rot = relation['objOriY']
                        sub_p = mod.p + rot(rel_p, mod.rotation)
                        sub_rot = mod.rotation + rel_rot
                        sub_poly = translate(
                            rotate(other_mod.state_list[other_mod.target_state].poly, -sub_rot, (0, 0), True), sub_p[0],
                            sub_p[1])
                        if not intersect_check(sub_poly, space, placed_polys):
                            continue
                        other_mod.p, other_mod.rotation = sub_p, sub_rot
                        placed_polys.append(sub_poly)
                        completed[j] = True

    for i in range(length):
        if completed[i] == True:
            continue
        mod = mods[i]
        place_success, target_p, target_rot, target_poly = stick_to_the_wall(
            mod.state_list[mod.target_state].poly, space, placed_polys, mod.state_list[mod.target_state].attribute_list)
        if not place_success:
            return False
        mod.p, mod.rotation = target_p, target_rot
        placed_polys.append(target_poly)
        completed[i] = True

    return True


def single_search(mods: List[TransformableModule], space: TwoDimSpace, scene: json, idx: int, scene_name: str,
                  branch_node: tuple):
    origin_mods = deepcopy(mods)

    success, target_attributes = process(mods, space)

    # subject_to, target_attributes = preprocess(mods)
    # success = action(mods, space, subject_to, target_attributes)
    if not success:
        print('cannot place')
        return False, None, idx, branch_node

    ## skip

    #print("succeed")
    #output_scene_2(origin_mods, scene, idx, scene_name, target_attributes)
    #return True, mods, idx, branch_node

    # get path
    path_success, time_now = get_all_paths(origin_mods, mods, space)
    if not path_success:
        print('fail')
        return False, None, idx, branch_node
    else:
        print('succeed')
        # samplevideo(origin_mods, space, 0, time_now + 1, idx)
        output_scene(origin_mods, scene, idx, scene_name, target_attributes)
        return True, mods, idx, branch_node


def search(mods: List[TransformableModule], space: TwoDimSpace, scene: json, scene_name: str):
    mod_len = len(mods)
    branches = []
    # choices = [[] for i in range(mod_len)]
    # derivation_counts = []
    total_count = 1
    start_node = (tuple)([mod.state for mod in mods])
    start_layout_node = (start_node, 0)

    for i in range(mod_len):
        mod = mods[i]
        # derivation_count = 0
        # for j in range(len(mod.state_list)):
        #     state = mod.state_list[j]
        #     if len(state.attribute_list) == 0:
        #         choices[i].append((j, -1))
        #         derivation_count += 1
        #     else:
        #         for k in range(len(state.attribute_list)):
        #             choices[i].append((j, k))
        #             derivation_count += 1
        # derivation_counts.append(derivation_count)
        total_count *= len(mod.state_list)
    print(total_count)
    if total_count <= SCENE_COUNT_THRES:
        for idx in range(total_count):
            branches.append([])
            remain = idx
            for i in range(mod_len):
                state = remain % len(mods[i].state_list)
                remain //= len(mods[i].state_list)
                branches[idx].append(state)
    else:
        ratio = total_count / SCENE_COUNT_THRES
        for idx in range(SCENE_COUNT_THRES):
            branches.append([])
            remain = min((int)((idx + random.random()) * ratio), total_count - 1)
            for i in range(mod_len):
                state = remain % len(mods[i].state_list)
                remain //= len(mods[i].state_list)
                branches[idx].append(state)

    branch_nodes = [start_node]
    branch_nodes_mods_dict = {}
    branch_nodes_mods_dict[start_node] = [mods]
    layout_nodes_anim_dict = {}
    layout_nodes_anim_dict[(start_node, 0)] = []

    pool_results = []
    success_counts = [0 for i in range(len(branches))]
    result_count = 0
    for k in tqdm(range(10)):
        pool = Pool(PROCESS_COUNT)
        for idx in range(len(branches)):
            if success_counts[idx] >= 1:
                continue
            # for idx in range(10):
            branch = branches[idx]
            branch_node = (tuple)(branch)
            if branch_node == start_node:
                continue
            mod_list = deepcopy(mods)
            for i in range(mod_len):
                mod_list[i].target_state = branch[i]
                # mod_list[i].target_attribute = 0
            pool_results.append(
                pool.apply_async(single_search, (mod_list, space, scene, idx * 10 + k, scene_name, branch_node)))
            # success_count = 0
            # for k in range(10):
            #     mod_list_copy = deepcopy(mod_list) if k < 9 else mod_list
            #     res = single_search(mod_list_copy, space, scene, idx * 10 + k, scene_name, branch_node)
            #     if res[0] == True:
            #         pool_results.append(res)
            #         success_count += 1
            #     if success_count == 3:
            #         break
        pool.close()
        pool.join()
        for i in range(result_count, len(pool_results)):
            pool_results[i] = pool_results[i].get()
            success, res_mods, idx, branch_node = pool_results[i]
            if success:
                success_counts[idx // 10] += 1
        result_count = len(pool_results)

    for res in pool_results:
        success, res_mods, idx, branch_node = res  #.get()
        if success:
            if branch_node in branch_nodes_mods_dict:
                branch_nodes_mods_dict[branch_node].append(res_mods)
            else:
                branch_nodes.append(branch_node)
                branch_nodes_mods_dict[branch_node] = [res_mods]
            layout_idx = len(branch_nodes_mods_dict[branch_node]) - 1
            layout_node = (branch_node, layout_idx)
            layout_nodes_anim_dict[start_layout_node].append([layout_node, idx, True])  # forward
            layout_nodes_anim_dict[layout_node] = [[start_layout_node, idx, False]]  # inverse

    animation_json = {}
    animation_json['state_encoding'] = []
    for mod in mods:
        mod_info = [state.name for state in mod.state_list]
        animation_json['state_encoding'].append(mod_info)
    animation_json['center'] = tuple2str(start_node)
    indexes = {}
    for src_layout_node in layout_nodes_anim_dict:
        for item in layout_nodes_anim_dict[src_layout_node]:
            target_layout_node, idx, forward = item
            src_branch_node, src_layout_idx = src_layout_node[0], src_layout_node[1]
            src_branch_str = tuple2str(src_branch_node)
            src_layout_str = src_branch_str + '_' + (str)(src_layout_idx)
            content = {}
            # content['src_layout'] = src_layout_idx
            content['target_node'] = tuple2str(target_layout_node[0]) + '_' + (str)(target_layout_node[1])
            # content['target_layout'] = target_layout_node[1]
            content['anim_id'] = idx
            content['anim_forward'] = forward
            if src_layout_str in indexes:
                indexes[src_layout_str].append(content)
            else:
                indexes[src_layout_str] = [content]
    animation_json['index'] = indexes

    with open('./static/dataset/infinitelayout/{}_anim.json'.format(scene_name), 'w') as anim_f:
        json.dump(animation_json, anim_f)


def main(groupName:str='sample3',scenejson:any=None):
    np.random.seed()
    random.seed()
    space, mods = None, None
    name = groupName
    if os.path.exists('./static/dataset/infinitelayout/{}_anim'.format(name)):
        for file in os.listdir('./static/dataset/infinitelayout/{}_anim'.format(name)):
            os.remove('./static/dataset/infinitelayout/{}_anim'.format(name, file))
    else:
        os.mkdir('./static/dataset/infinitelayout/{}_anim'.format(name))
    if os.path.exists('./static/dataset/infinitelayout/{}_scenes'.format(name)):
        for file in os.listdir('./static/dataset/infinitelayout/{}_scenes'.format(name)):
            os.remove('./static/dataset/infinitelayout/{}_scenes/{}'.format(name, file))
    else:
        os.mkdir('./static/dataset/infinitelayout/{}_scenes'.format(name))
    if scenejson == None:
        with open('./static/dataset/infinitelayout/{}_origin.json'.format(groupName), 'r') as scene:
            scenejson = json.load(scene)
    space, mods = parse_scene(scenejson, name)

    search(mods, space, scenejson, name)


def autoPerspectiveCamera(scenejson):
    PerspectiveCamera = {}
    roomShape = np.array(scenejson['rooms'][0]['roomShape'])
    lx = (np.max(roomShape[:, 0]) + np.min(roomShape[:, 0])) / 2
    lz = (np.max(roomShape[:, 1]) + np.min(roomShape[:, 1])) / 2
    camfovratio = np.tan((DEFAULT_FOV / 2) * np.pi / 180)
    lx_length = (np.max(roomShape[:, 0]) - np.min(roomShape[:, 0]))
    lz_length = (np.max(roomShape[:, 1]) - np.min(roomShape[:, 1]))
    if lz_length > lx_length:
        PerspectiveCamera['up'] = [1, 0, 0]
        camHeight = WALLHEIGHT + (np.max(roomShape[:, 0]) / 2 - np.min(roomShape[:, 0]) / 2) / camfovratio
    else:
        PerspectiveCamera['up'] = [0, 0, 1]
        camHeight = WALLHEIGHT + (np.max(roomShape[:, 1]) / 2 - np.min(roomShape[:, 1]) / 2) / camfovratio
    PerspectiveCamera['origin'] = [lx, camHeight, lz]
    PerspectiveCamera['target'] = [lx, 0, lz]
    PerspectiveCamera['up'] = [0, 0, 1]
    PerspectiveCamera['rotate'] = [0, 0, 0]
    PerspectiveCamera['fov'] = DEFAULT_FOV
    PerspectiveCamera['focalLength'] = 35
    scenejson['PerspectiveCamera'] = PerspectiveCamera
    return PerspectiveCamera


def bound_rot_estimate(bounds: tuple, angle: float):
    res = []
    addition, residual = (int)(angle / (pi / 2)), angle % (pi / 2)
    for i in range(4):
        res.append(
            abs(bounds[(i + addition) % 4]) * cos(residual) + abs(bounds[(i + 1 + addition) % 4]) * sin(residual))
    res[0], res[1] = -res[0], -res[1]
    return res


def top_parent(li: List[int], idx: int):
    pa = idx
    while li[pa] != -1:
        pa = li[pa]
        if pa == idx:
            return -2
    return pa


@jit(nopython=True)
def tuple2str(tup: tuple):
    ret = ''
    for item in (list)(tup):
        ret += (str)(item)
    return ret


@jit(nopython=True)
def rot(point: np.ndarray, angle: float):
    """rotate a vector counter-clockwise, angle is in radian"""
    return np.array([point[0] * cos(angle) + point[1] * sin(angle), -point[0] * sin(angle) + point[1] * cos(angle)],
                    'float32')


if __name__ == '__main__':
    main(groupName='output0_105')

    pass

# def action_a(mod: TransformableModule, space: TwoDimSpace, obstacles: List[Polygon], seqs: List[ActionSequence]):
#     state = mod.state_list[mod.target_state]
#     poly = state.poly
#     att = mod.target_attribute
#     if att == 0:  # near the wall
#         # check first
#         wall_count = len(space.pointList)
#         now_poly = rotate(poly, -mod.rotation, (0, 0), True).exterior.coords
#         now_poly = Polygon([(point[0] + mod.p[0], point[1] + mod.p[1]) for point in now_poly])
#         for i in range(wall_count):
#             if now_poly.distance(space.wallstrings[i]) < EPS * 100:
#                 mod.end = True
#                 return False, None

#         # action
#         success_flag = False
#         target_p, target_rotation = None, None

#         for k in range(50):  # try many times
#             randnum = random.randint(0, wall_count - 1)
#             wall = space.walls[randnum]
#             # w0, w1 = space.pointList[randnum], space.pointList[(randnum + 1) % wall_count]
#             # wall_norm = atan2(w1[1] - w0[1], w1[0] - w0[1]) + pi / 2
#             assert isinstance(wall, SpaceColumn) or isinstance(wall, SpaceRow)
#             rotation = (wall.towards * pi / 2 - state.forward) % (2 * pi)
#             rotated_poly = rotate(poly, rotation, (0, 0), True)
#             xl, yl, xh, yh = rotated_poly.bounds
#             # bounded_poly = Polygon([(xl, yl), (xh, yl), (xh, yh), (xl, yh)])
#             px, py = None, None
#             if wall.towards == 0:
#                 px = wall.x - xl + EPS
#                 if wall.ymax - wall.ymin > yh - yl:
#                     py = random.random() * (wall.ymax - yh - wall.ymin + yl) + (wall.ymin - yl)
#                 else:
#                     continue
#             elif wall.towards == 1:
#                 py = wall.y - yl + EPS
#                 if wall.xmax - wall.xmin > xh - xl:
#                     px = random.random() * (wall.xmax - xh - wall.xmin + xl) + (wall.xmin - xl)
#                 else:
#                     continue
#             elif wall.towards == 2:
#                 px = wall.x - xh - EPS
#                 if wall.ymax - wall.ymin > yh - yl:
#                     py = random.random() * (wall.ymax - yh - wall.ymin + yl) + (wall.ymin - yl)
#                 else:
#                     continue
#             elif wall.towards == 3:
#                 py = wall.y - yh - EPS
#                 if wall.xmax - wall.xmin > xh - xl:
#                     px = random.random() * (wall.xmax - xh - wall.xmin + xl) + (wall.xmin - xl)
#                 else:
#                     continue
#             target_poly = Polygon([(coo[0] + px, coo[1] + py) for coo in rotated_poly.exterior.coords])
#             if intersect_check(target_poly, space, obstacles):
#                 target_p = (px, py)
#                 target_rotation = rotation
#                 success_flag = True
#                 break

#         if success_flag:
#             res = mod.move_action(mod.target_state, target_p, target_rotation, space, obstacles)
#             if res == None:
#                 return False, None
#             else:
#                 res = crosspath_decision(res, seqs)
#                 mod.end = True
#                 return True, res
#         else:
#             return False, None

#     elif att == 1:  # near another obj
#         # check first
#         obs_count = len(obstacles)
#         now_poly = rotate(poly, mod.rotation, (0, 0), True).exterior.coords
#         now_poly = Polygon([(point[0] + mod.p[0], point[1] + mod.p[1]) for point in now_poly])
#         for obs in obstacles:
#             if now_poly.distance(obs) < NEAR_THRES:
#                 return False, None

#         # action
#         success_flag = False
#         target_p, target_rotation = None, None

#         for k in range(50):  # try many times
#             randnum = random.randint(0, obs_count - 1)
#             obs = obstacles[randnum]
#             oxl, oyl, oxh, oyh = obs.bounds
#             rotation = 0
#             rotated_poly = rotate(poly, rotation, (0, 0), True)
#             xl, yl, xh, yh = rotated_poly.bounds
#             bxl, byl, bxh, byh = oxl - xh + xl - NEAR_THRES, oyl - yh + yl - NEAR_THRES, oxh + xh - xl + NEAR_THRES, oyh + yh - yl + NEAR_THRES
#             bxlen, bylen = bxh - bxl, byh - byl
#             for l in range(50):
#                 px, py = random.random() * bxlen + bxl, random.random() * bylen + byl
#                 target_poly = Polygon([(coo[0] + px, coo[1] + py) for coo in rotated_poly.exterior.coords])
#                 if intersect_check(target_poly, space, obstacles) and target_poly.distance(obs) < NEAR_THRES:
#                     target_p = (px, py)
#                     target_rotation = rotation
#                     success_flag = True
#                     break
#             if success_flag:
#                 break

#         if success_flag:
#             res = mod.move_action(mod.target_state, target_p, target_rotation, space, obstacles)
#             if res == None:
#                 return False, None
#             else:
#                 res = crosspath_decision(res, seqs)
#                 return True, res
#         else:
#             return False, None
#     else:
#         return False, None
