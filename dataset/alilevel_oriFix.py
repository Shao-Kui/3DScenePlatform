import numpy as np
import os
import json
from math import asin, atan2, pi, copysign, sin, cos

def orient33(matrix):
    # print(np.linalg.det(matrix[0:3, 0:3]))
    return atan2(matrix[0, 2], matrix[2, 2])

def euler_to_matrix(thetaX, thetaY, thetaZ):
    X = np.array([[1,0,0],[0,cos(thetaX),-sin(thetaX)],[0,sin(thetaX),cos(thetaX)]])
    Y = np.array([[cos(thetaY),0,sin(thetaY)],[0,1,0],[-sin(thetaY),0,cos(thetaY)]])
    Z = np.array([[cos(thetaZ),-sin(thetaZ),0],[sin(thetaZ),cos(thetaZ),0],[0,0,1]])
    return Z @ Y @ X

print(orient33(euler_to_matrix(3.14,0,3.14)))
print(orient33(euler_to_matrix(0,1.57,0)))

levelnames = os.listdir('./alilevel')
for levelname in levelnames:
    with open(f'./alilevel/{levelname}') as f:
        level = json.load(f)
    for room in level['rooms']:
        for obj in room['objList']:
            obj['orient'] = orient33(euler_to_matrix(obj['rotate'][0], obj['rotate'][1], obj['rotate'][2]))
    with open(f'./alilevel_oriFix/{levelname}', 'w') as f:
        json.dump(level, f)
