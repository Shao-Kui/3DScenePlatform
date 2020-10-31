import numpy as np
from math import asin, atan2, pi, copysign, sin, cos

def quaternion_to_euler(qlist):
    q = {}
    q['x'] = qlist[0]
    q['y'] = qlist[1]
    q['z'] = qlist[2]
    q['w'] = qlist[3]

    # roll (x-axis rotation)
    sinr_cosp = 2 * (q['w'] * q['x'] + q['y'] * q['z'])
    cosr_cosp = 1 - 2 * (q['x'] * q['x'] + q['y'] * q['y'])
    roll = atan2(sinr_cosp, cosr_cosp)

    # pitch (y-axis rotation)
    sinp = 2 * (q['w'] * q['y'] - q['z'] * q['x'])
    if abs(sinp) >= 1:
        pitch = copysign(np.pi / 2, sinp) # use 90 degrees if out of range
    else:
        pitch = asin(sinp)

    # yaw (z-axis rotation)
    siny_cosp = 2 * (q['w'] * q['z'] + q['x'] * q['y'])
    cosy_cosp = 1 - 2 * (q['y'] * q['y'] + q['z'] * q['z'])
    yaw = atan2(siny_cosp, cosy_cosp)

    return (roll, pitch, yaw)

# print(quaternion_to_euler([0,1,0,0]))
# print(quaternion_to_euler([0,-0.70711,0,0.70711]))
# print(quaternion_to_euler([0,-0.70711,0,-0.70711]))
# print(quaternion_to_euler([0,-1,0,0]))

def correlation_atan(theta):
    while theta > pi/2:
        theta = theta - pi
    while theta < -pi/2:
        theta = theta + pi
    return theta

def decompose16(matrix):
    matrix = np.array(matrix, dtype=np.float).reshape(4, 4)
    # print(matrix[0:3, 0:3])
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

def orient(matrix):
    matrix = np.array(matrix, dtype=np.float).reshape(4, 4)
    if np.linalg.det(matrix[0:3, 0:3]) < 0:
        matrix[0:3, 0] *= -1
    T = matrix[3, 0:3].copy()
    matrix[3, 0:3] = 0
    matrix = matrix.T
    S = np.linalg.norm(matrix, axis=0)[0:3]
    matrix[0:3] = matrix[0:3] / np.linalg.norm(matrix, axis=0)
    return atan2(matrix[0, 2], matrix[2, 2])

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
print(orient33(euler_to_matrix(3.141592653589793, 0, 3.141592653589793)))

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
