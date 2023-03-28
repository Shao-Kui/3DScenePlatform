import json
import random
import math
from constraints import *
from copy import deepcopy

FILE = "stories/test3.json"
no_op_round = 0
round = 0
T = 2000
dT = 0.9
eps = 1e-14

random.seed()

def max(a, b):
    if (a > b):
        return a
    return b

def min(a, b):
    if (a > b):
        return b
    return a

def val(data):
    return costFunction(data)

def conflict(cnt, bbox_max, bbox_min, i_num, j_num):
    for i in range(0, cnt):
        for j in range(i + 1, cnt):
            if (bbox_max[i][0] > bbox_min[j][0] and bbox_min[i][0] < bbox_max[j][0] and
                bbox_max[i][1] > bbox_min[j][1] and bbox_min[i][1] < bbox_max[j][1] and
                bbox_max[i][2] > bbox_min[j][2] and bbox_min[i][2] < bbox_max[j][2]):
                print(str(i_num[i]) + " " + str(j_num[i]) + "物体" + str(i_num[j]) + " " + str(j_num[j]) + "物体碰撞")
                return True
    return False

#第一次读入初始化，约定初态scale=1，旋转值为-pi/2，0，pi/2，pi
with open(FILE, "r", encoding="utf-8") as fp:
    data = json.load(fp)
    for i in range(len(data["rooms"])):
        for j in range(len(data["rooms"][i]["objList"])):
            if (("format" in data["rooms"][i]["objList"][j]) and (data["rooms"][i]["objList"][j]["format"] == "obj") and (data["rooms"][i]["objList"][j]["surface"] == "floor")):
                if ("originBbox" in data["rooms"][i]["objList"][j]):
                    x_1 = 0 
                    x_2 = 0
                    z_1 = 0 
                    z_2 = 0
                    y_1 = data["rooms"][i]["objList"][j]["translate"][1] + data["rooms"][i]["objList"][j]["originBbox"]["max"][1]
                    y_2 = data["rooms"][i]["objList"][j]["translate"][1] + data["rooms"][i]["objList"][j]["originBbox"]["min"][1]
                    if (data["rooms"][i]["objList"][j]["rotate"][1] == -math.pi / 2):
                        x_1 = data["rooms"][i]["objList"][j]["translate"][0] - data["rooms"][i]["objList"][j]["originBbox"]["max"][2]
                        z_1 = data["rooms"][i]["objList"][j]["translate"][2] + data["rooms"][i]["objList"][j]["originBbox"]["max"][0]
                        x_2 = data["rooms"][i]["objList"][j]["translate"][0] - data["rooms"][i]["objList"][j]["originBbox"]["min"][2]
                        z_2 = data["rooms"][i]["objList"][j]["translate"][2] + data["rooms"][i]["objList"][j]["originBbox"]["min"][0]
                    elif (data["rooms"][i]["objList"][j]["rotate"][1] == 0):
                        x_1 = data["rooms"][i]["objList"][j]["translate"][0] + data["rooms"][i]["objList"][j]["originBbox"]["max"][0]
                        z_1 = data["rooms"][i]["objList"][j]["translate"][2] + data["rooms"][i]["objList"][j]["originBbox"]["max"][2]
                        x_2 = data["rooms"][i]["objList"][j]["translate"][0] + data["rooms"][i]["objList"][j]["originBbox"]["min"][0]
                        z_2 = data["rooms"][i]["objList"][j]["translate"][2] + data["rooms"][i]["objList"][j]["originBbox"]["min"][2]
                    elif (data["rooms"][i]["objList"][j]["rotate"][1] == math.pi / 2):
                        x_1 = data["rooms"][i]["objList"][j]["translate"][0] + data["rooms"][i]["objList"][j]["originBbox"]["max"][2]
                        z_1 = data["rooms"][i]["objList"][j]["translate"][2] - data["rooms"][i]["objList"][j]["originBbox"]["max"][0]
                        x_2 = data["rooms"][i]["objList"][j]["translate"][0] + data["rooms"][i]["objList"][j]["originBbox"]["min"][2]
                        z_2 = data["rooms"][i]["objList"][j]["translate"][2] - data["rooms"][i]["objList"][j]["originBbox"]["min"][0]
                    else:
                        x_1 = data["rooms"][i]["objList"][j]["translate"][0] - data["rooms"][i]["objList"][j]["originBbox"]["max"][0]
                        z_1 = data["rooms"][i]["objList"][j]["translate"][2] - data["rooms"][i]["objList"][j]["originBbox"]["max"][2]
                        x_2 = data["rooms"][i]["objList"][j]["translate"][0] - data["rooms"][i]["objList"][j]["originBbox"]["min"][0]
                        z_2 = data["rooms"][i]["objList"][j]["translate"][2] - data["rooms"][i]["objList"][j]["originBbox"]["min"][2]
                    data["rooms"][i]["objList"][j]["bbox"]["max"][0] = max(x_1, x_2)
                    data["rooms"][i]["objList"][j]["bbox"]["max"][1] = max(y_1, y_2)
                    data["rooms"][i]["objList"][j]["bbox"]["max"][2] = max(z_1, z_2)
                    data["rooms"][i]["objList"][j]["bbox"]["min"][0] = min(x_1, x_2)
                    data["rooms"][i]["objList"][j]["bbox"]["min"][1] = min(y_1, y_2)
                    data["rooms"][i]["objList"][j]["bbox"]["min"][2] = min(z_1, z_2)
    data_best = deepcopy(data)
    data_init = deepcopy(data)

while (T > eps):
    data_next = deepcopy(data)
    round += 1
    print(str(round) + "轮开始")
    flag = False
    cnt = 0
    i_num = []
    j_num = []
    bbox_max = []
    bbox_min = []
    for i in range(len(data_next["rooms"])):
        for j in range(len(data_next["rooms"][i]["objList"])):
            if (("format" in data_next["rooms"][i]["objList"][j]) and (data_next["rooms"][i]["objList"][j]["format"] == "obj") and (data_next["rooms"][i]["objList"][j]["surface"] == "floor")):
                rand_num = random.random()
                if (rand_num < 0.05):
                    rand_num = random.random()
                    dt0 = (rand_num * 10 - 5) * T / 2000
                    rand_num = random.random()
                    dt2 = (rand_num * 10 - 5) * T / 2000
                    data_next["rooms"][i]["objList"][j]["translate"][0] += dt0
                    data_next["rooms"][i]["objList"][j]["translate"][2] += dt2
                    rand_num = random.random()
                    ds0 = (rand_num - data_next["rooms"][i]["objList"][j]["scale"][0] + 0.5) * T / 2000
                    rand_num = random.random()
                    ds1 = (rand_num - data_next["rooms"][i]["objList"][j]["scale"][1] + 0.5) * T / 2000
                    rand_num = random.random()
                    ds2 = (rand_num - data_next["rooms"][i]["objList"][j]["scale"][2] + 0.5) * T / 2000
                    data_next["rooms"][i]["objList"][j]["scale"][0] += ds0
                    data_next["rooms"][i]["objList"][j]["scale"][1] += ds1
                    data_next["rooms"][i]["objList"][j]["scale"][2] += ds2
                    dr1 = 0
                    rand_num = random.random()
                    if (rand_num < 0.25):
                        dr1 = math.pi / 2
                    elif (rand_num < 0.50):
                        dr1 = math.pi
                    elif (rand_num < 0.75):
                        dr1 = math.pi * 3 / 2
                    else:
                        dr1 = 0
                    data_next["rooms"][i]["objList"][j]["rotate"][1] += dr1
                    data_next["rooms"][i]["objList"][j]["rotate"][1] %= (2 * math.pi)
                    data_next["rooms"][i]["objList"][j]["rotate"][1] -= math.pi
                    if ("bbox" in data_next["rooms"][i]["objList"][j]):
                        vector_x1 = data["rooms"][i]["objList"][j]["bbox"]["max"][0] - data["rooms"][i]["objList"][j]["translate"][0]
                        vector_y1 = data["rooms"][i]["objList"][j]["bbox"]["max"][1] - data["rooms"][i]["objList"][j]["translate"][1]
                        vector_z1 = data["rooms"][i]["objList"][j]["bbox"]["max"][2] - data["rooms"][i]["objList"][j]["translate"][2]
                        vector_x2 = data["rooms"][i]["objList"][j]["bbox"]["min"][0] - data["rooms"][i]["objList"][j]["translate"][0]
                        vector_y2 = data["rooms"][i]["objList"][j]["bbox"]["min"][1] - data["rooms"][i]["objList"][j]["translate"][1]
                        vector_z2 = data["rooms"][i]["objList"][j]["bbox"]["min"][2] - data["rooms"][i]["objList"][j]["translate"][2]
                        vector_x1 *= data_next["rooms"][i]["objList"][j]["scale"][0] / data["rooms"][i]["objList"][j]["scale"][0]
                        vector_y1 *= data_next["rooms"][i]["objList"][j]["scale"][1] / data["rooms"][i]["objList"][j]["scale"][1]
                        vector_z1 *= data_next["rooms"][i]["objList"][j]["scale"][2] / data["rooms"][i]["objList"][j]["scale"][2]
                        vector_x2 *= data_next["rooms"][i]["objList"][j]["scale"][0] / data["rooms"][i]["objList"][j]["scale"][0]
                        vector_y2 *= data_next["rooms"][i]["objList"][j]["scale"][1] / data["rooms"][i]["objList"][j]["scale"][1]
                        vector_z2 *= data_next["rooms"][i]["objList"][j]["scale"][2] / data["rooms"][i]["objList"][j]["scale"][2]
                        y1 = data["rooms"][i]["objList"][j]["translate"][1] + vector_y1
                        y2 = data["rooms"][i]["objList"][j]["translate"][1] + vector_y2
                        x1 = 0
                        x2 = 0 
                        z1 = 0 
                        z2 = 0
                        if (dr1 == -math.pi / 2):
                            x1 = data["rooms"][i]["objList"][j]["translate"][0] - vector_z1
                            z1 = data["rooms"][i]["objList"][j]["translate"][2] + vector_x1
                            x2 = data["rooms"][i]["objList"][j]["translate"][0] - vector_z2
                            z2 = data["rooms"][i]["objList"][j]["translate"][2] + vector_x2
                        elif (dr1 == 0):
                            x1 = data["rooms"][i]["objList"][j]["translate"][0] + vector_x1
                            z1 = data["rooms"][i]["objList"][j]["translate"][2] + vector_z1
                            x2 = data["rooms"][i]["objList"][j]["translate"][0] + vector_x2
                            z2 = data["rooms"][i]["objList"][j]["translate"][2] + vector_z2
                        elif (dr1 == math.pi / 2):
                            x1 = data["rooms"][i]["objList"][j]["translate"][0] + vector_z1
                            z1 = data["rooms"][i]["objList"][j]["translate"][2] - vector_x1
                            x2 = data["rooms"][i]["objList"][j]["translate"][0] + vector_z2
                            z2 = data["rooms"][i]["objList"][j]["translate"][2] - vector_x2
                        elif (dr1 == math.pi):
                            x1 = data["rooms"][i]["objList"][j]["translate"][0] - vector_x1
                            z1 = data["rooms"][i]["objList"][j]["translate"][2] - vector_z1
                            x2 = data["rooms"][i]["objList"][j]["translate"][0] - vector_x2
                            z2 = data["rooms"][i]["objList"][j]["translate"][2] - vector_z2
                        data_next["rooms"][i]["objList"][j]["bbox"]["max"][0] = max(x1, x2)
                        data_next["rooms"][i]["objList"][j]["bbox"]["max"][1] = max(y1, y2)
                        data_next["rooms"][i]["objList"][j]["bbox"]["max"][2] = max(z1, z2)
                        data_next["rooms"][i]["objList"][j]["bbox"]["min"][0] = min(x1, x2)
                        data_next["rooms"][i]["objList"][j]["bbox"]["min"][1] = min(y1, y2)
                        data_next["rooms"][i]["objList"][j]["bbox"]["min"][2] = min(z1, z2)
                if ("bbox" in data_next["rooms"][i]["objList"][j]):
                    bbox_max.append(data_next["rooms"][i]["objList"][j]["bbox"]["max"])
                    bbox_min.append(data_next["rooms"][i]["objList"][j]["bbox"]["min"])
                    i_num.append(i)
                    j_num.append(j)
                    cnt += 1
                if not (bbox_max[cnt - 1][0] < max(data_next["rooms"][i]["roomShapeBBox"]["max"][0], data_next["rooms"][i]["roomShapeBBox"]["min"][0]) and
                        bbox_min[cnt - 1][0] > min(data_next["rooms"][i]["roomShapeBBox"]["max"][0], data_next["rooms"][i]["roomShapeBBox"]["min"][0]) and
                        bbox_max[cnt - 1][2] < max(data_next["rooms"][i]["roomShapeBBox"]["max"][1], data_next["rooms"][i]["roomShapeBBox"]["min"][1]) and
                        bbox_min[cnt - 1][2] > min(data_next["rooms"][i]["roomShapeBBox"]["max"][1], data_next["rooms"][i]["roomShapeBBox"]["min"][1])):
                    print(str(i) + " " + str(j) + " 物体不在房间内")
                    flag = True
                    break
        if (flag):
            break
    if (flag or conflict(cnt, bbox_max, bbox_min, i_num, j_num)):
        T *= dT
        print(str(round) + "轮结束，冲突")
        no_op_round += 1
        if (no_op_round == 50):
            no_op_round = 0
            data = deepcopy(data_best)
            print("回滚")
        continue 

    val1 = -costFunction(data_next)
    val2 = -costFunction(data)

    if (val1 > val2):
        no_op_round = 0
        data = deepcopy(data_next)
        data_best = deepcopy(data_next)
        print(str(round) + "轮结束，优化")
    else:
        no_op_round += 1
        rand_num = random.random()
        if (rand_num < math.exp(2000000 * (val1 - val2) / T)):
            data = deepcopy(data_next)
            print(str(round) + "轮结束，负优化，仍接受")
        else:
            print(str(round) + "轮结束，负优化，不接受")
        if (no_op_round == 50):
            no_op_round = 0
            data = deepcopy(data_best)
            print("回滚")
    T *= dT

with open("./candidate.json", "w", encoding="utf-8") as fw:
    print("done")
    print("begin:" + str(-costFunction(data_init)))
    print("end:" + str(-costFunction(data_best)))
    json.dump(data_best, fw)
         