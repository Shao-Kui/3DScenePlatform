import random
import os
from tqdm import tqdm
from math import *
import numpy as np
import sys
import matplotlib.pyplot as plt
from shapely.geometry import *
from shapely.affinity import *
from shapely.ops import *
import queue
import json
import imageio
from multiprocessing import Pool
from copy import deepcopy
from typing import List
import time
a = -2.65

b = 3.5

c = [(1, 2), (2, 3), (2.5, 5), (3, 10), (0, 10)]
print(translate(Polygon(c), 1, 1).exterior.coords[:])
print(Polygon(c).bounds)
c.sort()

# for name in os.listdir('object'):
#     if isdir('object/'+name) and ('_' not in name) and ('2' in name):
#         print(name)

p1 = Point(0, 0).buffer(1)
p2 = Point(1, 0).buffer(1)

# print(p1.distance(p2))

# print((-2) % 3.14)

poly = [[-1, 2], [-3, 4]]

# print([po * [2, 3] for po in poly])

# print((float)(np.random.randn(1) * min(1, 10 / sqrt(iter + 1))))


def top_parent(li: List[int], idx: int):
    pa = idx
    while li[pa] != -1:
        pa = li[pa]
        if pa == idx:
            return -2
    return pa


li = [-1, 0, 3, 1, 5, 4]
print(top_parent(li, 0), top_parent(li, 1), top_parent(li, 2), top_parent(li, 3), top_parent(li, 4), top_parent(li, 5))

print(random.uniform(0, -1))
