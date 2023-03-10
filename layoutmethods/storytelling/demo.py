import json
import random
import math
from constraints import *
from copy import deepcopy

random.seed()
with open("test/0e3f92e0-8f04-4643-a737-23603f438e68-r4.json", "r", encoding="utf-8") as fp:
    #print(type(fp))
    data = json.load(fp)
    data_init = deepcopy(data)
    # print(data)
    print("init end")

def val(data):
    return 0

round = 0 #退火轮数
T = 2000 #初始温度
dT = 0.99 #退火速度
eps = 1e-14 #最终温度
TRANSLATE_MAX = 5
SCALE_MAX = 2

while (T > eps):
    data_next = deepcopy(data) #退火过程
    round += 1
    for i in range(len(data_next["rooms"])):
        for j in range(len(data_next["rooms"][i]["objList"])):
            rand_num = random.random()
            dt0 = (rand_num * 10 + data_init["rooms"][i]["objList"][j]["translate"][0] - 5 - data_next["rooms"][i]["objList"][j]["translate"][0] ) * T / 2000
            #print(dt0)
            rand_num = random.random()
            dt1 = (rand_num * 10 + data_init["rooms"][i]["objList"][j]["translate"][1] - 5 - data_next["rooms"][i]["objList"][j]["translate"][1] ) * T / 2000
            rand_num = random.random()
            dt2 = (rand_num * 10 + data_init["rooms"][i]["objList"][j]["translate"][2] - 5 - data_next["rooms"][i]["objList"][j]["translate"][2] ) * T / 2000
            #print(data_next["rooms"][i]["objList"][j]["translate"][0])
            data_next["rooms"][i]["objList"][j]["translate"][0] += dt0
            #print(data_next["rooms"][i]["objList"][j]["translate"][0])
            data_next["rooms"][i]["objList"][j]["translate"][1] += dt1
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
            rand_num = random.random()
            dr0 = 0
            rand_num = random.random()
            dr1 = rand_num * math.pi * T / 1000
            rand_num = random.random()
            dr2 = 0
            data_next["rooms"][i]["objList"][j]["rotate"][0] += dr0
            data_next["rooms"][i]["objList"][j]["rotate"][0] %= (2 * math.pi)
            data_next["rooms"][i]["objList"][j]["rotate"][0] -= math.pi
            data_next["rooms"][i]["objList"][j]["rotate"][1] += dr1
            data_next["rooms"][i]["objList"][j]["rotate"][1] %= (2 * math.pi)
            data_next["rooms"][i]["objList"][j]["rotate"][1] -= math.pi
            data_next["rooms"][i]["objList"][j]["rotate"][2] += dr2
            data_next["rooms"][i]["objList"][j]["rotate"][2] %= (2 * math.pi)
            data_next["rooms"][i]["objList"][j]["rotate"][2] -= math.pi
            #break
        #break
    val1 = costFunction(data_next)
    # print(val1)
    val2 = costFunction(data)
    # print(val2)
    if val1 > val2:
        print("set as" + str(val1))
        data = deepcopy(data_next)
    else:
        rand_num = random.random()
        if (rand_num < math.exp(200000000 * (val1 - val2) / T)):
            print("still accept")
            data = deepcopy(data_next)
    T *= dT
    print(str(round) + " end")
print("optimize end")

with open("./candidate.json", "w", encoding="utf-8") as fw:
    json.dump(data, fw)
    print("done")