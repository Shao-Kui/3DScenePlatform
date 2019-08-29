import numpy as np
from math import asin, atan2, pi


def correlation_atan(theta):
    while theta > pi/2:
        theta = theta - pi
    while theta < -pi/2:
        theta = theta + pi
    return theta


def decompose16(matrix):
    matrix = np.array(matrix).reshape(4, 4)
    if np.linalg.det(matrix[0:3, 0:3]) < 0:
        matrix[0:3, 0] *= -1
    T = matrix[3, 0:3].copy()
    matrix[3, 0:3] = 0
    matrix = matrix.T
    S = np.linalg.norm(matrix, axis=0)[0:3]
    matrix[0:3] = matrix[0:3] / np.linalg.norm(matrix, axis=0)
    if matrix[0, 2] < 1:
        if matrix[0, 2] > -1:
            thetaY = asin(matrix[0, 2])
            thetaX = atan2(-matrix[1, 2], matrix[2, 2])
            thetaZ = atan2(-matrix[0, 1], matrix[0, 0])
        else:
            thetaY = -pi / 2
            thetaX = -atan2(matrix[1, 0], matrix[1, 1])
            thetaZ = 0
    else:
        thetaY = pi / 2
        thetaX = atan2(-matrix[1, 0], matrix[1, 1])
        thetaZ = 0
    return T, S, np.array([thetaX, thetaY, thetaZ], dtype=np.float)


def decompose16_debug(matrix):
    matrix = np.array(matrix).reshape(4, 4)
    if np.linalg.det(matrix[0:3, 0:3]) < 0:
        matrix[0:3, 0] *= -1
    T = matrix[3, 0:3].copy()
    matrix[3, 0:3] = 0
    matrix = matrix.T
    S = np.linalg.norm(matrix, axis=0)[0:3]
    matrix[0:3] = matrix[0:3] / np.linalg.norm(matrix, axis=0)
    print(matrix[0:3, 0:3])
    if matrix[0, 2] < 1:
        if matrix[0, 2] > -1:
            thetaY = asin(matrix[0, 2])
            thetaX = atan2(-matrix[1, 2], matrix[2, 2])
            thetaZ = atan2(-matrix[0, 1], matrix[0, 0])
        else:
            thetaY = -pi / 2
            thetaX = -atan2(matrix[1, 0], matrix[1, 1])
            thetaZ = 0
    else:
        thetaY = pi / 2
        thetaX = atan2(-matrix[1, 0], matrix[1, 1])
        thetaZ = 0
    return T, S, np.array([thetaX, thetaY, thetaZ], dtype=np.float)

def decompose16_XZY(matrix):
    matrix = np.array(matrix).reshape(4, 4)
    xflip = int(np.linalg.det(matrix) < 0)
    translate = matrix[3, :3]
    transform = matrix[:3, :3]
    if xflip:
        transform[:, 0] *= -1
    # transform=transform*[[1,-1,1]] # remove this line after re-extract!
    scale = ((transform ** 2).sum(axis=0)) ** 0.5
    transform /= [scale]
    rotate = np.array([np.arctan2(-transform[1, 2], transform[1, 1]), np.arctan2(-transform[2, 0], transform[0, 0]),
                       np.arcsin(transform[1, 0])])
    return translate, scale, rotate
