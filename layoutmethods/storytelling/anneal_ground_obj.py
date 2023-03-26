import json
import random
import math
from constraints import *
from copy import deepcopy

random.seed() #随机种子
no_op_cnt = 0

with open("stories/test.json", "r", encoding="utf-8") as fp:
    data = json.load(fp) #读入初始数据
    for i in range(len(data["rooms"])):
        for j in range(len(data["rooms"][i]["objList"])):
            if ("format" in data["rooms"][i]["objList"][j] and (data["rooms"][i]["objList"][j]["format"] == "obj") and (data["rooms"][i]["objList"][j]["surface"] == "floor")):
                if ("originBbox" in data["rooms"][i]["objList"][j]): #将bbox修改为当前位置]
                    print(str(i) + "   " + str(j))
                    if (data["rooms"][i]["objList"][j]["rotate"][1] == 0):
                        data["rooms"][i]["objList"][j]["bbox"]["max"][0] = data["rooms"][i]["objList"][j]["translate"][0] + data["rooms"][i]["objList"][j]["originBbox"]["max"][0]
                        data["rooms"][i]["objList"][j]["bbox"]["max"][1] = data["rooms"][i]["objList"][j]["translate"][1] + data["rooms"][i]["objList"][j]["originBbox"]["max"][1]
                        data["rooms"][i]["objList"][j]["bbox"]["max"][2] = data["rooms"][i]["objList"][j]["translate"][2] + data["rooms"][i]["objList"][j]["originBbox"]["max"][2]
                        data["rooms"][i]["objList"][j]["bbox"]["min"][0] = data["rooms"][i]["objList"][j]["translate"][0] + data["rooms"][i]["objList"][j]["originBbox"]["min"][0]
                        data["rooms"][i]["objList"][j]["bbox"]["min"][1] = data["rooms"][i]["objList"][j]["translate"][1] + data["rooms"][i]["objList"][j]["originBbox"]["min"][1]
                        data["rooms"][i]["objList"][j]["bbox"]["min"][2] = data["rooms"][i]["objList"][j]["translate"][2] + data["rooms"][i]["objList"][j]["originBbox"]["min"][2]
                    elif (data["rooms"][i]["objList"][j]["rotate"][1] == -math.pi / 2):
                        data["rooms"][i]["objList"][j]["bbox"]["max"][0] = data["rooms"][i]["objList"][j]["translate"][0] - data["rooms"][i]["objList"][j]["originBbox"]["max"][2]
                        data["rooms"][i]["objList"][j]["bbox"]["max"][1] = data["rooms"][i]["objList"][j]["translate"][1] + data["rooms"][i]["objList"][j]["originBbox"]["max"][1]
                        data["rooms"][i]["objList"][j]["bbox"]["max"][2] = data["rooms"][i]["objList"][j]["translate"][2] + data["rooms"][i]["objList"][j]["originBbox"]["max"][0]
                        data["rooms"][i]["objList"][j]["bbox"]["min"][0] = data["rooms"][i]["objList"][j]["translate"][0] - data["rooms"][i]["objList"][j]["originBbox"]["min"][2]
                        data["rooms"][i]["objList"][j]["bbox"]["min"][1] = data["rooms"][i]["objList"][j]["translate"][1] + data["rooms"][i]["objList"][j]["originBbox"]["min"][1]
                        data["rooms"][i]["objList"][j]["bbox"]["min"][2] = data["rooms"][i]["objList"][j]["translate"][2] + data["rooms"][i]["objList"][j]["originBbox"]["min"][0]
                    elif (data["rooms"][i]["objList"][j]["rotate"][1] == math.pi):
                        data["rooms"][i]["objList"][j]["bbox"]["max"][0] = data["rooms"][i]["objList"][j]["translate"][0] - data["rooms"][i]["objList"][j]["originBbox"]["max"][0]
                        data["rooms"][i]["objList"][j]["bbox"]["max"][1] = data["rooms"][i]["objList"][j]["translate"][1] + data["rooms"][i]["objList"][j]["originBbox"]["max"][1]
                        data["rooms"][i]["objList"][j]["bbox"]["max"][2] = data["rooms"][i]["objList"][j]["translate"][2] - data["rooms"][i]["objList"][j]["originBbox"]["max"][2]
                        data["rooms"][i]["objList"][j]["bbox"]["min"][0] = data["rooms"][i]["objList"][j]["translate"][0] - data["rooms"][i]["objList"][j]["originBbox"]["min"][0]
                        data["rooms"][i]["objList"][j]["bbox"]["min"][1] = data["rooms"][i]["objList"][j]["translate"][1] + data["rooms"][i]["objList"][j]["originBbox"]["min"][1]
                        data["rooms"][i]["objList"][j]["bbox"]["min"][2] = data["rooms"][i]["objList"][j]["translate"][2] - data["rooms"][i]["objList"][j]["originBbox"]["min"][2]
                    elif (data["rooms"][i]["objList"][j]["rotate"][1] == math.pi / 2):
                        data["rooms"][i]["objList"][j]["bbox"]["max"][0] = data["rooms"][i]["objList"][j]["translate"][0] + data["rooms"][i]["objList"][j]["originBbox"]["max"][2]
                        data["rooms"][i]["objList"][j]["bbox"]["max"][1] = data["rooms"][i]["objList"][j]["translate"][1] + data["rooms"][i]["objList"][j]["originBbox"]["max"][1]
                        data["rooms"][i]["objList"][j]["bbox"]["max"][2] = data["rooms"][i]["objList"][j]["translate"][2] - data["rooms"][i]["objList"][j]["originBbox"]["max"][0]
                        data["rooms"][i]["objList"][j]["bbox"]["min"][0] = data["rooms"][i]["objList"][j]["translate"][0] + data["rooms"][i]["objList"][j]["originBbox"]["min"][2]
                        data["rooms"][i]["objList"][j]["bbox"]["min"][1] = data["rooms"][i]["objList"][j]["translate"][1] + data["rooms"][i]["objList"][j]["originBbox"]["min"][1]
                        data["rooms"][i]["objList"][j]["bbox"]["min"][2] = data["rooms"][i]["objList"][j]["translate"][2] - data["rooms"][i]["objList"][j]["originBbox"]["min"][0]

    data_init = deepcopy(data) #备份初始数据
    data_best = deepcopy(data)
    print("init end")

def val(data):
    return costFunction(data)

def max(a, b):
    if a > b:
        return a
    return b

def min(a, b):
    if a > b:
        return b
    return a

round = 0 #退火轮数
T = 2000 #初始温度
dT = 0.9 #退火速度
eps = 1e-14 #最终温度
TRANSLATE_MAX = 5
SCALE_MAX = 2

def conflict_s(cnt, max_x, max_y, max_z, min_x, min_y, min_z):
    for i in range(0, cnt):
        for j in range(i + 1, cnt):
            if (max_x[i] > min_x[j] and min_x[i] < max_x[j] and max_y[i] > min_y[j] and min_y[i] < max_y[j] and max_z[i] > min_z[j] and min_z[i] < max_z[j]): #判断条件
                print("obj-conflict")
                print ("room:" + str(i_num[i]) + "obj:" + str(j_num[i]) + "max_x:" + str(max_x[i]) + "max_y" + str(max_y[i]) + "max_z" + str(max_z[i]) + "min_x:" + str(min_x[i]) + "min_y" + str(min_y[i]) + "min_z" + str(min_z[i])) #输出冲突房间/物体序号以及对应bbox参数
                print ("room:" + str(i_num[j]) + "obj:" + str(j_num[j]) + "max_x:" + str(max_x[j]) + "max_y" + str(max_y[j]) + "max_z" + str(max_z[j]) + "min_x:" + str(min_x[j]) + "min_y" + str(min_y[j]) + "min_z" + str(min_z[j]))
                return True
    return False

while (T > eps):
    data_next = deepcopy(data) #退火过程
    flag = False #本次扰动是否已经导致了冲突
    round += 1
    cnt = 0 #待调整物品个数
    i_num = [] #房间号
    j_num = [] #物体号
    max_x = [] #bbox大值
    max_y = []
    max_z = []
    min_x = [] #bbox小值
    min_y = []
    min_z = []
    for i in range(len(data_next["rooms"])):
        for j in range(len(data_next["rooms"][i]["objList"])):
            if ("format" in data["rooms"][i]["objList"][j] and (data["rooms"][i]["objList"][j]["format"] == "obj") and (data["rooms"][i]["objList"][j]["surface"] == "floor")):
                rand_num = random.random()
                dr1 = 0
                if (rand_num < 0.05):

                    #随机扰动与处理
                    rand_num = random.random()
                    dt0 = (rand_num * 10 + data_init["rooms"][i]["objList"][j]["translate"][0] - 5 - data_next["rooms"][i]["objList"][j]["translate"][0] ) * T / 2000
                    #y轴上不进行位移
                    rand_num = random.random()
                    dt2 = (rand_num * 10 + data_init["rooms"][i]["objList"][j]["translate"][2] - 5 - data_next["rooms"][i]["objList"][j]["translate"][2] ) * T / 2000

                    data_next["rooms"][i]["objList"][j]["translate"][0] += dt0
                    data_next["rooms"][i]["objList"][j]["translate"][2] += dt2

                    rand_num = random.random()
                    ds0 = (rand_num * SCALE_MAX - data_next["rooms"][i]["objList"][j]["scale"][0]) * T / 2000
                    rand_num = random.random()
                    ds1 = (rand_num * SCALE_MAX - data_next["rooms"][i]["objList"][j]["scale"][1]) * T / 2000
                    rand_num = random.random()
                    ds2 = (rand_num * SCALE_MAX - data_next["rooms"][i]["objList"][j]["scale"][2]) * T / 2000

                    data_next["rooms"][i]["objList"][j]["scale"][0] += ds0
                    data_next["rooms"][i]["objList"][j]["scale"][1] += ds1
                    data_next["rooms"][i]["objList"][j]["scale"][2] += ds2

                    #只进行y轴上的旋转，并旋转pi/2的倍数
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

                #更新next的bbox数据
                if ("bbox" in data["rooms"][i]["objList"][j]):
                    #考虑平移和缩放
                    vector_x = data["rooms"][i]["objList"][j]["bbox"]["max"][0] - data["rooms"][i]["objList"][j]["translate"][0]
                    vector_y = data["rooms"][i]["objList"][j]["bbox"]["max"][1] - data["rooms"][i]["objList"][j]["translate"][1]
                    vector_z = data["rooms"][i]["objList"][j]["bbox"]["max"][2] - data["rooms"][i]["objList"][j]["translate"][2]
                    vector_x *= data_next["rooms"][i]["objList"][j]["scale"][0] / data["rooms"][i]["objList"][j]["scale"][0]
                    vector_y *= data_next["rooms"][i]["objList"][j]["scale"][1] / data["rooms"][i]["objList"][j]["scale"][1]
                    vector_z *= data_next["rooms"][i]["objList"][j]["scale"][2] / data["rooms"][i]["objList"][j]["scale"][2]
                    data_next["rooms"][i]["objList"][j]["bbox"]["max"][0] = data_next["rooms"][i]["objList"][j]["translate"][0] + vector_x
                    data_next["rooms"][i]["objList"][j]["bbox"]["max"][1] = data_next["rooms"][i]["objList"][j]["translate"][1] + vector_y
                    data_next["rooms"][i]["objList"][j]["bbox"]["max"][2] = data_next["rooms"][i]["objList"][j]["translate"][2] + vector_z

                    vector_x = data["rooms"][i]["objList"][j]["translate"][0] - data["rooms"][i]["objList"][j]["bbox"]["min"][0]
                    vector_y = data["rooms"][i]["objList"][j]["translate"][1] - data["rooms"][i]["objList"][j]["bbox"]["min"][1]
                    vector_z = data["rooms"][i]["objList"][j]["translate"][2] - data["rooms"][i]["objList"][j]["bbox"]["min"][2]
                    vector_x *= data_next["rooms"][i]["objList"][j]["scale"][0] / data["rooms"][i]["objList"][j]["scale"][0]
                    vector_y *= data_next["rooms"][i]["objList"][j]["scale"][1] / data["rooms"][i]["objList"][j]["scale"][1]
                    vector_z *= data_next["rooms"][i]["objList"][j]["scale"][2] / data["rooms"][i]["objList"][j]["scale"][2]
                    data_next["rooms"][i]["objList"][j]["bbox"]["min"][0] = data_next["rooms"][i]["objList"][j]["translate"][0] - vector_x
                    data_next["rooms"][i]["objList"][j]["bbox"]["min"][1] = data_next["rooms"][i]["objList"][j]["translate"][1] - vector_y
                    data_next["rooms"][i]["objList"][j]["bbox"]["min"][2] = data_next["rooms"][i]["objList"][j]["translate"][2] - vector_z
                    #考虑旋转
                    if (dr1 == math.pi*3 / 2):
                        vector_x = data_next["rooms"][i]["objList"][j]["bbox"]["max"][0] - data_next["rooms"][i]["objList"][j]["translate"][0]
                        vector_z = data_next["rooms"][i]["objList"][j]["bbox"]["max"][2] - data_next["rooms"][i]["objList"][j]["translate"][2]
                        data_next["rooms"][i]["objList"][j]["bbox"]["max"][0] = data_next["rooms"][i]["objList"][j]["translate"][0] - vector_z
                        data_next["rooms"][i]["objList"][j]["bbox"]["max"][2] = data_next["rooms"][i]["objList"][j]["translate"][2] + vector_x

                        vector_x = data_next["rooms"][i]["objList"][j]["bbox"]["min"][0] - data_next["rooms"][i]["objList"][j]["translate"][0]
                        vector_z = data_next["rooms"][i]["objList"][j]["bbox"]["min"][2] - data_next["rooms"][i]["objList"][j]["translate"][2]
                        data_next["rooms"][i]["objList"][j]["bbox"]["min"][0] = data_next["rooms"][i]["objList"][j]["translate"][0] - vector_z
                        data_next["rooms"][i]["objList"][j]["bbox"]["min"][2] = data_next["rooms"][i]["objList"][j]["translate"][2] + vector_x
                    elif (dr1 == math.pi):
                        vector_x = data_next["rooms"][i]["objList"][j]["bbox"]["max"][0] - data_next["rooms"][i]["objList"][j]["translate"][0]
                        vector_z = data_next["rooms"][i]["objList"][j]["bbox"]["max"][2] - data_next["rooms"][i]["objList"][j]["translate"][2]
                        data_next["rooms"][i]["objList"][j]["bbox"]["max"][0] = data_next["rooms"][i]["objList"][j]["translate"][0] - vector_z
                        data_next["rooms"][i]["objList"][j]["bbox"]["max"][2] = data_next["rooms"][i]["objList"][j]["translate"][2] - vector_x

                        vector_x = data_next["rooms"][i]["objList"][j]["bbox"]["min"][0] - data_next["rooms"][i]["objList"][j]["translate"][0]
                        vector_z = data_next["rooms"][i]["objList"][j]["bbox"]["min"][2] - data_next["rooms"][i]["objList"][j]["translate"][2]
                        data_next["rooms"][i]["objList"][j]["bbox"]["min"][0] = data_next["rooms"][i]["objList"][j]["translate"][0] - vector_z
                        data_next["rooms"][i]["objList"][j]["bbox"]["min"][2] = data_next["rooms"][i]["objList"][j]["translate"][2] - vector_x
                    elif (dr1 == math.pi / 2):
                        vector_x = data_next["rooms"][i]["objList"][j]["bbox"]["max"][0] - data_next["rooms"][i]["objList"][j]["translate"][0]
                        vector_z = data_next["rooms"][i]["objList"][j]["bbox"]["max"][2] - data_next["rooms"][i]["objList"][j]["translate"][2]
                        data_next["rooms"][i]["objList"][j]["bbox"]["max"][0] = data_next["rooms"][i]["objList"][j]["translate"][0] + vector_z
                        data_next["rooms"][i]["objList"][j]["bbox"]["max"][2] = data_next["rooms"][i]["objList"][j]["translate"][2] - vector_x

                        vector_x = data_next["rooms"][i]["objList"][j]["bbox"]["min"][0] - data_next["rooms"][i]["objList"][j]["translate"][0]
                        vector_z = data_next["rooms"][i]["objList"][j]["bbox"]["min"][2] - data_next["rooms"][i]["objList"][j]["translate"][2]
                        data_next["rooms"][i]["objList"][j]["bbox"]["min"][0] = data_next["rooms"][i]["objList"][j]["translate"][0] + vector_z
                        data_next["rooms"][i]["objList"][j]["bbox"]["min"][2] = data_next["rooms"][i]["objList"][j]["translate"][2] - vector_x
                    
                    #导入conflict判断数据
                    cnt += 1
                    i_num.append(i)
                    j_num.append(j)
                    #调整max为大 min为小
                    max_x.append(max(data_next["rooms"][i]["objList"][j]["bbox"]["max"][0], data_next["rooms"][i]["objList"][j]["bbox"]["min"][0]))
                    min_x.append(min(data_next["rooms"][i]["objList"][j]["bbox"]["max"][0], data_next["rooms"][i]["objList"][j]["bbox"]["min"][0]))
                    max_y.append(max(data_next["rooms"][i]["objList"][j]["bbox"]["max"][1], data_next["rooms"][i]["objList"][j]["bbox"]["min"][1]))
                    min_y.append(min(data_next["rooms"][i]["objList"][j]["bbox"]["max"][1], data_next["rooms"][i]["objList"][j]["bbox"]["min"][1]))
                    max_z.append(max(data_next["rooms"][i]["objList"][j]["bbox"]["max"][2], data_next["rooms"][i]["objList"][j]["bbox"]["min"][2]))
                    min_z.append(min(data_next["rooms"][i]["objList"][j]["bbox"]["max"][2], data_next["rooms"][i]["objList"][j]["bbox"]["min"][2]))
                    #并判断是否在房间里，不在则丢弃本次改动
                    if not (max_x[cnt - 1] < max(data_next["rooms"][i]["roomShapeBBox"]["max"][0], data_next["rooms"][i]["roomShapeBBox"]["min"][0]) and
                        min_x[cnt - 1] > min(data_next["rooms"][i]["roomShapeBBox"]["max"][0], data_next["rooms"][i]["roomShapeBBox"]["min"][0]) and
                        max_z[cnt - 1] < max(data_next["rooms"][i]["roomShapeBBox"]["max"][1], data_next["rooms"][i]["roomShapeBBox"]["min"][1]) and
                        min_z[cnt - 1] > min(data_next["rooms"][i]["roomShapeBBox"]["max"][1], data_next["rooms"][i]["roomShapeBBox"]["min"][1])):
                        flag = True
                        print("room-conflict " + str(i) + "   " + str(j))
                        break
        if (flag):
            break    

    if (conflict_s(cnt, max_x, max_y, max_z, min_x, min_y, min_z) or flag): #若有冲突直接跳过
        T *= dT
        no_op_cnt += 1
        if (no_op_cnt == 50):
            no_op_cnt = 0
            data = deepcopy(data_best)
        print("conflict")
        print(str(round) + "round end")
        continue

    val1 = -costFunction(data_next)
    val2 = -costFunction(data)

    if val1 > val2:
        print("val update to" + str(val1))
        data = deepcopy(data_next)
        data_best = deepcopy(data_next)
        no_op_cnt = 0
    else:
        rand_num = random.random()
        if (rand_num < math.exp(200000000 * (val1 - val2) / T)):
            print("still accept and value update to" + str(val1))
            data = deepcopy(data_next)
        no_op_cnt += 1
        if (no_op_cnt == 50):
            no_op_cnt = 0
            data = deepcopy(data_best)
    T *= dT
    print(str(round) + "round end")
print("optimize end")

with open("./candidate.json", "w", encoding="utf-8") as fw:
    print("done")
    print("begin:" + str(-costFunction(data_init)))
    print("end:" + str(-costFunction(data)))
    json.dump(data, fw)