import numpy as np
import copy
import json
import math
import cv2
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from shapely.geometry import Point, Polygon
import tqdm

RENDERWIDTH = 600
SAMPLESIZE = 30
ASPECT = 16 / 9
R = 0
DELTA = 1
JSON_FILE = 'FEEAC78A-42F2-4274-9942-CE0EE0134FAB'
RANK = 0
METHOD = "ClusterOrthorhombic"
PREFIX = rf'D:\zhx_workspace\3DScenePlatformDev\latentspace\sfy\{JSON_FILE}\sfy-{JSON_FILE}-{R}-{METHOD}-{RANK}'
IMG_PREFIX = rf'C:\Users\evan\Desktop\zhx_workspace\SceneViewer\result_0116\2_new\{JSON_FILE}\sfy-{JSON_FILE}-{R}-{METHOD}-{RANK}'
def normalize(v):
    if np.linalg.norm(v) == 0:
        return np.zeros(v.shape)
    return v/np.linalg.norm(v)

def findBBox(roomShape):
    right_up = [-1000,-1000]
    left_down = [100000,100000]
    for wall in roomShape:
        if wall[0]>right_up[0]:
            right_up[0] = wall[0]
        if wall[0] < left_down[0]:
            left_down[0] = wall[0]
        if wall[1] > right_up[1]:
            right_up[1] = wall[1]
        if wall[1] < left_down[1]:
            left_down[1] = wall[1]
    return np.array([right_up,left_down])

def volumeObj(obj1):
    v1_max = np.array(obj1['bbox']['max'])
    v1_min = np.array(obj1['bbox']['min'])
    _v1 = v1_max - v1_min
    
    return abs(_v1[0]*_v1[1]*_v1[2])

def SpacePoint2Canva(pcam, point):
    """
        return the position by [x(width),y(height)] of pixel onto that the point is projeceted
    """
    theta = pcam['theta']
    o = np.array(pcam['origin'])

    p = np.array(point)
    d = np.array(pcam['direction'])
    d = normalize(d)
    u = np.array(pcam['up'])
    u = normalize(u)
    n = np.cross(u , d)

    """
         Assume that direction, origin and up are normalized
    """
    # v = (p - o) / np.dot(p - o, d)
    
    
    # h = np.tan(theta / 2)
    # w = h * ASPECT
    
    # x = np.dot(v, n) / h * (RENDERWIDTH / 2)
    # y = np.dot(v, u) / w * (RENDERWIDTH / 2 / ASPECT)


    v_nd = (p-o)-u*(np.dot(p-o,u))

    v_nd = normalize(v_nd)
    v_ud = (p-o)-n*(np.dot(p-o,n))

    v_ud = normalize(v_ud)
    
    
    h = np.tan(theta)
    w = h* ASPECT
    

    if np.tan(np.arccos(np.dot(v_nd,n))) == 0 or np.tan(np.arccos(np.dot(v_ud,u))) == 0:
        return np.array([2,2])

    x = 1/np.tan(np.arccos(np.dot(v_nd,n)))/w
    y = 1/np.tan(np.arccos(np.dot(v_ud,u)))/h
    


    return np.array([x, y])

def calcABCFromLine2d(x0, y0, x1, y1):
    a = y0 - y1
    b = x1 - x0
    c = x0*y1 - x1*y0
    return a, b, c

def getLineCrossPoint(line1, line2):
    # x1y1x2y2
    a0, b0, c0 = calcABCFromLine2d(*line1)
    a1, b1, c1 = calcABCFromLine2d(*line2)
    D = a0 * b1 - a1 * b0
    if D == 0:
        return None
    x = (b0 * c1 - b1 * c0) / D
    y = (a1 * c0 - a0 * c1) / D
    # print(x, y)
    return x, y

def distDotToLine(dot, line):
    x1 = line[0][0]
    y1 = line[0][1]
    x2 = line[1][0]
    y2 = line[1][1]
    x0 = dot[0]
    y0 = dot[1]
    return np.fabs(((y1 - y2) * x0 - (x1 - x2) * y0 + (x1 * y2 - x2 * y1)) / np.sqrt(np.power(y1 - y2, 2) + np.power(x1 - x2, 2)))


def getWeight(angle):
    tmp:float = np.inf
    for i in [-2, -1, 0, 1, 2]:
        tmp = np.fmin(tmp, 2. * np.fabs(angle + i * np.pi / 2 - np.pi / 4))
    return np.cos(tmp)


def rotate(v, theta):
    # theta in radian
    v = np.array(v)
    rMatrix = np.array([
        [math.cos(theta),-math.sin(theta)],
        [math.sin(theta),math.cos(theta)]
    ])
    return np.matmul(rMatrix,v)

def pcamInObj(eightPoints,pcam):
    origin = np.array(pcam['origin'])
    eightPoints = eightPoints.T
    xmin,ymin,zmin = np.min(eightPoints[0]),np.min(eightPoints[1]),np.min(eightPoints[2])
    xmax,ymax,zmax = np.max(eightPoints[0]),np.max(eightPoints[1]),np.max(eightPoints[2])
    if origin[0] < xmin or origin[0] > xmax:
        return False
    if origin[1] < ymin or origin[1] > ymax:
        return False
    if origin[2] < zmin or origin[2] > zmax:
        return False
    return True
    
def ptInObj(eightPoints,origin):
    eightPoints = eightPoints.T
    xmin,ymin,zmin = np.min(eightPoints[0]),np.min(eightPoints[1]),np.min(eightPoints[2])
    xmax,ymax,zmax = np.max(eightPoints[0]),np.max(eightPoints[1]),np.max(eightPoints[2])
    if origin[0] < xmin or origin[0] > xmax:
        return False
    if origin[1] < ymin or origin[1] > ymax:
        return False
    if origin[2] < zmin or origin[2] > zmax:
        return False
    return True


def pcamInRoom(room,pcam):
    direct = normalize(pcam['direction'])
    origin = np.array(pcam['origin'])+0.01*direct
    origin_2d = Point(origin[0],origin[2])
    roomShape = Polygon(room['roomShape'])
    if roomShape.contains(origin_2d):
        return True
    return False

def pointInside(pt, face):
    v0 = face[2]-face[0]
    v1 = face[1]-face[0]
    v2 = pt - face[0]

    d00 = np.dot(v0,v0)
    d01 = np.dot(v0,v1)
    d02 = np.dot(v0,v2)
    d11 = np.dot(v1,v1)
    d12 = np.dot(v1,v2)

    u = (d11*d02-d01*d12)/(d00*d11-d01*d01)
    v = (d00*d12-d01*d02)/(d00*d11-d01*d01)
    if u<0 or u>1:
        return False
    if v<0 or v>1:
        return False
    return u+v<=1

def maxSight(room,origin, direction,pt,idx = -1):
    objs = room['objList']
    pt = np.array(pt)
    max_len = np.linalg.norm(pt-origin)

    for i,ob in enumerate(objs):
        if 'bbox' not in ob or 'coarseSemantic' not in ob:
            continue
        if i == idx:
            # an obj will not be covered by its faces
            continue
        # print(ob['coarseSemantic'])
        AABB = ob['bbox']
        eightPoints = np.array([
            [AABB['max'][0], AABB['min'][1], AABB['max'][2]],
            [AABB['min'][0], AABB['min'][1], AABB['max'][2]],
            [AABB['min'][0], AABB['min'][1], AABB['min'][2]],
            [AABB['max'][0], AABB['min'][1], AABB['min'][2]],
            [AABB['max'][0], AABB['max'][1], AABB['max'][2]],
            [AABB['min'][0], AABB['max'][1], AABB['max'][2]],
            [AABB['min'][0], AABB['max'][1], AABB['min'][2]],
            [AABB['max'][0], AABB['max'][1], AABB['min'][2]],
        ])
        faces = np.array([
            [0,1,2,3], 
            [4,5,6,7], 
            [1,2,6,5], 
            [0,3,7,4], 
            [0,1,5,4],
            [2,3,7,6]
        ]) 
        for face_idx in faces:
            face = np.array([
                eightPoints[face_idx[0]],
                eightPoints[face_idx[1]],
                eightPoints[face_idx[2]],
                eightPoints[face_idx[3]],
            ])

            normal = np.cross(face[2]-face[0],face[1]-face[0])
            normal = normalize(normal)
            d = -np.dot(normal,face[0])
            if abs(np.dot(normal,direction)) == 0:
                continue
            t_cross = -(d+np.dot(normal,origin))/np.dot(normal,direction)
            if t_cross<=1e-4:
                continue
            pt_cross= origin+t_cross*direction
            if not pointInside(pt_cross,[face[0],face[1],face[2]]) and not pointInside(pt_cross,[face[0],face[2],face[3]]):
                continue
            if t_cross<max_len:
                max_len = t_cross
    return max_len


def maxSightWithWall(room, origin, direction, flag = False):
    objs = room['objList']
    direction = np.array(direction)
    origin = np.array(origin)
    # origin[1] = 0.75
    max_len = 1e8
    for i,ob in enumerate(objs):
        if 'bbox' not in ob or 'coarseSemantic' not in ob or ob['coarseSemantic'] == 'Door' or ob['coarseSemantic'] == 'Window':
            continue
        # print(ob['coarseSemantic'])
        AABB = ob['bbox']
        eightPoints = np.array([
            [AABB['max'][0], AABB['min'][1], AABB['max'][2]],
            [AABB['min'][0], AABB['min'][1], AABB['max'][2]],
            [AABB['min'][0], AABB['min'][1], AABB['min'][2]],
            [AABB['max'][0], AABB['min'][1], AABB['min'][2]],
            [AABB['max'][0], AABB['max'][1], AABB['max'][2]],
            [AABB['min'][0], AABB['max'][1], AABB['max'][2]],
            [AABB['min'][0], AABB['max'][1], AABB['min'][2]],
            [AABB['max'][0], AABB['max'][1], AABB['min'][2]],
        ])
        if flag and ptInObj(eightPoints,origin):
            continue
    
        faces = np.array([
            [0,1,2,3], 
            [4,5,6,7], 
            [1,2,6,5], 
            [0,3,7,4], 
            [0,1,5,4],
            [2,3,7,6]
        ]) 
        for face_idx in faces:
            face = np.array([
                eightPoints[face_idx[0]],
                eightPoints[face_idx[1]],
                eightPoints[face_idx[2]],
                eightPoints[face_idx[3]],
            ])

            normal = np.cross(face[2]-face[0],face[1]-face[0])
            normal = normalize(normal)
            d = -np.dot(normal,face[0])
            if abs(np.dot(normal,direction)) == 0:
                continue
            t_cross = -(d+np.dot(normal,origin))/np.dot(normal,direction)
            pt_cross= origin+t_cross*direction
            if t_cross<0:
                continue
            if not pointInside(pt_cross,[face[0],face[1],face[2]]) and not pointInside(pt_cross,[face[0],face[2],face[3]]):
                continue
            if t_cross<max_len:
                max_len = t_cross

    roomShape = room['roomShape']
    
    H=2.6
    num_edges = len(roomShape)
    for i, pt_xz in enumerate(roomShape):
        pt_next_xz = roomShape[int(i+1)%num_edges]
        face = np.array([
            [pt_xz[0],H,pt_xz[1]],
            [pt_next_xz[0],H,pt_next_xz[1]],
            [pt_next_xz[0],0,pt_next_xz[1]],
            [pt_xz[0],0,pt_xz[1]]
        ])
        normal = np.cross(face[2]-face[0],face[1]-face[0])
        normal = normalize(normal)
        d = -np.dot(normal,face[0])
        if abs(np.dot(normal,direction)) < 1e-5:
            continue
        t_cross = -(d+np.dot(normal,origin))/np.dot(normal,direction)
        
        pt_cross= origin+t_cross*direction
        if not pointInside(pt_cross,[face[0],face[1],face[2]]) and not pointInside(pt_cross,[face[0],face[2],face[3]]):
            continue
        if t_cross<=0:
            continue
        if t_cross<max_len:
            max_len = t_cross

    bbox = findBBox(roomShape)
    ru = bbox[0]
    ld = bbox[1]
    face1 = np.array([
        [ru[0],H,ru[1]],
        [ru[0],H,ld[1]],
        [ld[0],H,ld[1]],
        [ld[0],H,ru[1]]
    ])
    face2 = np.array([
        [ru[0],0,ru[1]],
        [ru[0],0,ld[1]],
        [ld[0],0,ld[1]],
        [ld[0],0,ru[1]]
    ])
    for face in [face1,face2]:
        normal = np.cross(face[2]-face[0],face[1]-face[0])
        normal = normalize(normal)
        d = -np.dot(normal,face[0])
        if abs(np.dot(normal,direction)) < 1e-5:
            continue
        t_cross = -(d+np.dot(normal,origin))/np.dot(normal,direction)
        if t_cross<=0:
            continue
        if t_cross<max_len:
            max_len = t_cross

    return max_len

def isPointCovered(room, pt, pcam,idx=-1):
    objs = room['objList']
    pt =np.array(pt)
    ori = np.array(pcam['origin'])
    probe_direction = normalize(pt -ori)
    intersect_point = ori+probe_direction*maxSight(room, ori,probe_direction,pt,idx=idx)
    if np.linalg.norm(pt- intersect_point) > 1e-2:
        return True
    return False

        

        
def ObjinDirection(center, pcam):
    theta = pcam['theta']
    o = np.array(pcam['origin'])
    p = np.array(center)
    d = np.array(pcam['direction'])
    d = normalize(d)

    if np.dot(p-o,d) >= 0:
        return True
    return False
    

def isInCanva(point):
    if abs(point[0]) < 1 and abs(point[1]) < 1:    
        return True
    return False





def linesDynamics(room, scene, pcam, isDebug = False):
    global ASPECT
    ASPECT = pcam['ratio']
    if not pcamInRoom(room,pcam):
        return 0
    d = normalize(np.array(pcam['direction']))
    # o = np.array(pcam['origin'])
    # up = normalize(np.array(pcam['up']))
    objects:list = copy.deepcopy(room['objList'])
    
    lines:list = []
    canvas =[]
    if isDebug:
        canvas = np.zeros([int(RENDERWIDTH/ASPECT),RENDERWIDTH,3],np.int8) #cv2.imread(IMG_PREFIX+'.jpg')

    
    for ob in objects:
        if 'bbox' not in ob:
            continue
        vmax = np.array(ob['bbox']['max'])
        vmin = np.array(ob['bbox']['min'])
        
        for i in range(0, 8):
            be = np.array([0., 0., 0.])
            for j in [0, 1, 2]:
                if (i>>j & 1):
                    be[j] = vmax[j]
                else:
                    be[j] = vmin[j]
            for j in [0, 1, 2]:
                if (not((i>>j & 1))) and vmax[j] != vmin[j]:
                    en = copy.deepcopy(be)
                    en[j] = vmax[j]
                    v = normalize(en - be)
                    # print(d, v, np.dot(d, v))
                    if (np.fabs(np.dot(d, v)) > 0.8):
                        d1 = SpacePoint2Canva(pcam, be)
                        d2 = SpacePoint2Canva(pcam, en)
                        # print(np.pi/2-np.arccos(np.dot(d, v)), getWeight(np.pi/2-np.arccos(np.dot(d, v))))
                        if (isInCanva(d1) or isInCanva(d2)) and (not isPointCovered(room,be,pcam) or not isPointCovered(room,en,pcam) ) :
                            lines.append([d1, d2])
    for line in lines:
        pt1,pt2 = line[0],line[1]
        pt1 = (int(-pt1[0]*RENDERWIDTH/2+RENDERWIDTH/2),int(-pt1[1]*RENDERWIDTH/2/ASPECT+RENDERWIDTH/2/ASPECT))
        pt2 = (int(-pt2[0]*RENDERWIDTH/2+RENDERWIDTH/2),int(-pt2[1]*RENDERWIDTH/2/ASPECT+RENDERWIDTH/2/ASPECT))
        if isDebug:
            cv2.line(canvas,pt1,pt2,[255,255,255],2)
    if isDebug:
        cv2.imshow('canvas',canvas)
        cv2.waitKey(0)
        # cv2.imwrite('test3.jpg',canvas)
    
    
    crosspoint:list = []
    length = 0
    for line1 in lines:
        for line2 in lines:
            p = np.array(getLineCrossPoint([line1[0][0], line1[0][1], line1[1][0], line1[1][1]],[line2[0][0], line2[0][1], line2[1][0], line2[1][1]]))
            if p.all() != None:
                # print(p)
                crosspoint.append(p)
                length += 1

    # print(len(crosspoint))
    if len(crosspoint) == 0:
        return 0
    center = np.mean(crosspoint, axis = 0)
    # print('here')
    center =(-center[0]*RENDERWIDTH/2+RENDERWIDTH/2,-center[1]*RENDERWIDTH/2/ASPECT+RENDERWIDTH/2/ASPECT)

    

    # dist:list = []
    # for p in crosspoint:
    #     dist.append(np.sqrt(np.dot(p -c, p - c)))

    # print(center)
    up = np.array([0., 1.])
    _sum:float = 0.
    for line in lines:
        pt1,pt2 = line[0],line[1]
        pt1 = (-pt1[0]*RENDERWIDTH/2+RENDERWIDTH/2,-pt1[1]*RENDERWIDTH/2/ASPECT+RENDERWIDTH/2/ASPECT)
        pt2 = (-pt2[0]*RENDERWIDTH/2+RENDERWIDTH/2,-pt2[1]*RENDERWIDTH/2/ASPECT+RENDERWIDTH/2/ASPECT)
        line_r = [pt1,pt2]
        # print(line[0], line[1])
        if distDotToLine(center, line_r) <= DELTA:
            # print(line[0], line[1], up)
            # print(np.dot(up, normalize(line[1] - line[0])))
            angle = np.arccos(np.dot(up, normalize(line[1] - line[0])))
            # print(angle, getWeight(angle))
            _sum += getWeight(angle)
    return _sum





def linesConvergeScore(room, scene, pcam,isDebug = False):
    if not pcamInRoom(room,pcam):
        return 0
    d = np.array(pcam['direction'])
    d = normalize(d)
    objects:list = copy.deepcopy(room['objList'])
    
    lines:list = []
    canvas =[]
    if isDebug:
        canvas = np.zeros([int(RENDERWIDTH/ASPECT),RENDERWIDTH,3],np.int8) #cv2.imread(IMG_PREFIX+'.jpg')

    for ob in objects:
        if 'bbox' not in ob or 'coarseSemantic' not in ob or ob['coarseSemantic'] == 'Window' or ob['coarseSemantic'] == 'Door':
            continue

        vmax = np.array(ob['bbox']['max'])
        vmin = np.array(ob['bbox']['min'])
        
        for i in range(0, 8):
            be = np.array([0., 0., 0.])
            for j in [0, 1, 2]:
                if (i>>j & 1):
                    be[j] = vmax[j]
                else:
                    be[j] = vmin[j]
            for j in [0, 1, 2]:
                if (not((i>>j & 1))):
                    en = copy.deepcopy(be)
                    en[j] = vmax[j]
                    v = normalize(en - be)
                    
                    if (abs(np.dot(d, v)) > 0.8):
                        lines.append([SpacePoint2Canva(pcam, be), SpacePoint2Canva(pcam, en)])
    
    for line in lines:
        pt1,pt2 = line[0],line[1]
        pt1 = (int(-pt1[0]*RENDERWIDTH/2+RENDERWIDTH/2),int(-pt1[1]*RENDERWIDTH/2/ASPECT+RENDERWIDTH/2/ASPECT))
        pt2 = (int(-pt2[0]*RENDERWIDTH/2+RENDERWIDTH/2),int(-pt2[1]*RENDERWIDTH/2/ASPECT+RENDERWIDTH/2/ASPECT))
        if isDebug:
            cv2.line(canvas,pt1,pt2,[255,255,255],2)
    if isDebug:
        cv2.imshow('canvas',canvas)
        cv2.waitKey(0)
        # cv2.imwrite('test3.jpg',canvas)

    crosspoint:list = []
    length = 0
    for line1 in lines:
        for line2 in lines:
            p = np.array(getLineCrossPoint([line1[0][0], line1[0][1], line1[1][0], line1[1][1]],[line2[0][0], line2[0][1], line2[1][0], line2[1][1]]))
            if p.all() != None:
                crosspoint.append(p)
                length += 1
    c = np.average(crosspoint) if len(crosspoint) else 0

    dist:list = []
    for p in crosspoint:
        dist.append(np.sqrt(np.dot(p -c, p - c)))
    coff = np.average(dist) if len(crosspoint) else 0
    return 1 / (1 + coff)


def symmetryScore(room, scene, pcam,isDebug = False):
    global ASPECT
    ASPECT = pcam['ratio']
    if not pcamInRoom(room,pcam):
        return 0
    objects:list = copy.deepcopy(room['objList'])
    
    sumsize:float = 0.
    sum = np.array([0., 0.])
    canvas =[]
    if isDebug:
        canvas = np.zeros([int(RENDERWIDTH/ASPECT),RENDERWIDTH,3],np.int8) #cv2.imread(IMG_PREFIX+'.jpg')

    num = 0
    for i,ob in enumerate(objects):
        if 'bbox' not in ob or 'coarseSemantic' not in ob or ob['coarseSemantic'] == 'Window' or ob['coarseSemantic'] == 'Door':
            continue
        AABB = ob['bbox']
        eightPoints = np.array([
            [AABB['max'][0], AABB['min'][1], AABB['max'][2]],
            [AABB['min'][0], AABB['min'][1], AABB['max'][2]],
            [AABB['min'][0], AABB['min'][1], AABB['min'][2]],
            [AABB['max'][0], AABB['min'][1], AABB['min'][2]],
            [AABB['max'][0], AABB['max'][1], AABB['max'][2]],
            [AABB['min'][0], AABB['max'][1], AABB['max'][2]],
            [AABB['min'][0], AABB['max'][1], AABB['min'][2]],
            [AABB['max'][0], AABB['max'][1], AABB['min'][2]],
        ])
        if pcamInObj(eightPoints,pcam):
            return 0
        # center = (np.array(ob['bbox']['min']) + np.array(ob['bbox']['max'])) / 2 
        # pos = SpacePoint2Canva(pcam, center)
        # if isDebug:
        #     cv2.circle(canvas,(int(-pos[0]*RENDERWIDTH/2+RENDERWIDTH/2),int(-pos[1]*RENDERWIDTH/2/ASPECT+RENDERWIDTH/2/ASPECT)),7,[255,255,255],3)

        for center in eightPoints:
            pos = SpacePoint2Canva(pcam, center)
            if  ObjinDirection(center,pcam) and isInCanva(pos) and not isPointCovered(room,center,pcam):
                num+=1
                if isDebug:
                    cv2.circle(canvas,(int(-pos[0]*RENDERWIDTH/2+RENDERWIDTH/2),int(-pos[1]*RENDERWIDTH/2/ASPECT+RENDERWIDTH/2/ASPECT)),2,[255,255,255],5)
                # vol = volumeObj(ob)
                sum = sum + pos #* vol / np.linalg.norm(center - pcam['origin'])
                sumsize += 1
    if isDebug:
        cv2.imshow('canvas',canvas)
        cv2.waitKey(0)

        cv2.imwrite('test2.bmp',canvas)

    if sumsize == 0:
        return 0
    sum /= sumsize
    
    x_bias = abs(sum[0])
    if num <= 1:
        return 0

    # return 1 - (np.sqrt(np.abs(sum[0]))+np.abs(sum[1])) / (np.sqrt(RENDERWIDTH / 2) + RENDERWIDTH / 2 / ASPECT)
    return np.exp(-x_bias)

def amountOfInformation(room,scene,pcam,isDebug = False):
    global ASPECT
    ASPECT = pcam['ratio']
    if not pcamInRoom(room,pcam):
        return 0
    objects:list = copy.deepcopy(room['objList'])
    infor_sum = 0
    canvas =[]
    if isDebug:
        canvas = np.zeros([int(RENDERWIDTH/ASPECT),RENDERWIDTH,3],np.int8) #cv2.imread(IMG_PREFIX+'.jpg')
    sum_vol = 0
    for i,ob in enumerate(objects):
        if 'bbox' not in ob or 'coarseSemantic' not in ob or ob['coarseSemantic'] == 'Window' or ob['coarseSemantic'] == 'Door':
            continue
        AABB = ob['bbox']
        eightPoints = np.array([
            [AABB['max'][0], AABB['min'][1], AABB['max'][2]],
            [AABB['min'][0], AABB['min'][1], AABB['max'][2]],
            [AABB['min'][0], AABB['min'][1], AABB['min'][2]],
            [AABB['max'][0], AABB['min'][1], AABB['min'][2]],
            [AABB['max'][0], AABB['max'][1], AABB['max'][2]],
            [AABB['min'][0], AABB['max'][1], AABB['max'][2]],
            [AABB['min'][0], AABB['max'][1], AABB['min'][2]],
            [AABB['max'][0], AABB['max'][1], AABB['min'][2]],
        ])
        if pcamInObj(eightPoints,pcam):
            return 0
        center = (np.array(ob['bbox']['min']) + np.array(ob['bbox']['max'])) / 2
        vol = volumeObj(ob) 
        sum_vol+=vol
        origin = np.array(pcam['origin'])
        dist = np.linalg.norm(center-origin)
        points_in_canvas = 0
        for pt in eightPoints:
            pos = SpacePoint2Canva(pcam, pt)
            if ObjinDirection(pt,pcam) and isInCanva(pos) and not isPointCovered(room, pt, pcam,i):
                if isDebug:
                    cv2.circle(canvas,(int(-pos[0]*RENDERWIDTH/2+RENDERWIDTH/2),int(-pos[1]*RENDERWIDTH/2/ASPECT+RENDERWIDTH/2/ASPECT)),2,[255,255,255],10)
                points_in_canvas+=1
        
        # 公式
        # print(vol*(points_in_canvas/8)/dist)
        infor_sum +=(points_in_canvas/8)*vol

    if isDebug:
        cv2.imshow('canvas',canvas)
        cv2.waitKey(0)
        # cv2.imwrite('test1.jpg',canvas)
    return infor_sum/sum_vol 


def shapeOfView(room, scene, pcam, isDebug=False):
    global ASPECT
    ASPECT = pcam['ratio']
    if not pcamInRoom(room,pcam):
        return 0
    camera_height = pcam['origin'][1]
    direction = np.array(pcam['direction'])
    direction = normalize(direction)
    direction = np.array([direction[0],direction[2]])
    horizontal_fov = np.arctan(np.tan(pcam['theta']) * ASPECT)

    d = np.array(pcam['direction'])
    u = np.array(pcam['up'])
    h = np.cross(u,d)
    h = normalize(h)

    
    delta_theta = horizontal_fov/15
    direct_array = np.linspace(-horizontal_fov,horizontal_fov,int(2*horizontal_fov/delta_theta)+1)
    sum_sight = 0.

    vertical_fov = pcam['theta']
    vertical_delta_theta = pcam['theta']/15
    vertical_direct_array = np.linspace(-vertical_fov,vertical_fov,int(2*vertical_fov/vertical_delta_theta)+1)
    prob2plane = SAMPLESIZE/np.tan(horizontal_fov)/2
    test_img_copy = np.zeros([int(SAMPLESIZE/ASPECT),SAMPLESIZE],float)
    _sum = 0
    for x in (range(int(SAMPLESIZE/ASPECT))):
        for y in range(SAMPLESIZE):
            probe_direction = d*prob2plane+h*(SAMPLESIZE/2-y)+u*(SAMPLESIZE/2/ASPECT-x)
            probe_direction = normalize(probe_direction)
            sight = maxSightWithWall(room,pcam['origin'],probe_direction)
            _sum+=sight
            test_img_copy[x,y] = sight

    test_img = np.zeros([int(SAMPLESIZE/ASPECT),SAMPLESIZE],np.uint8)
    max_t = np.max(test_img_copy)
    min_t = np.min(test_img_copy)
    delta_v = vertical_fov/(SAMPLESIZE/ASPECT/2)
    delta_h = horizontal_fov/(SAMPLESIZE/2)


    

    np.savetxt('test_copy.txt',test_img_copy)
    for x in (range(int(SAMPLESIZE/ASPECT))):
        for y in range(SAMPLESIZE):
            test_img[x,y] = (test_img_copy[x,y]-min_t)/(max_t-min_t)*255
    np.savetxt('test.txt',test_img)
    # cv2.imwrite(f'testimg_{SAMPLESIZE}.jpg',test_img)
    if isDebug:
        cv2.imshow('',test_img)
        cv2.waitKey(0)



    # for theta in direct_array: 
    #     probe_direction = rotate(direction,theta)
    #     probe_direction = [probe_direction[0], 0 ,probe_direction[1]]
        
    #     # print(probe_direction)
    #     max_len = maxSightWithWall(room,pcam['origin'],probe_direction)
    #     sum_sight+=max_len

    return _sum*delta_h*delta_v

def evaluateViews(room,scene,pcam):
    score = symmetryScore(room,scene,pcam) + linesConvergeScore(room,scene,pcam)\
        + amountOfInformation(room,scene,pcam)+shapeOfView(room,scene,pcam)
    return score      
   

if __name__ == '__main__':
    room = f'C:\\Users\\evan\\Desktop\\zhx_workspace\\SceneViewer\\test_20230821\\{JSON_FILE}.json'
    pcam = PREFIX+'.json'
    with open(room) as f:
        scene = json.load(f)
    with open(pcam) as f:
        pcam = json.load(f)
    print(symmetryScore(scene['rooms'][R], scene, pcam,isDebug=True))
    # print(linesConvergeScore(scene['rooms'][R], scene, pcam,isDebug=True))
    print(linesDynamics(scene['rooms'][R], scene, pcam,isDebug=True))
    print(amountOfInformation(scene['rooms'][R], scene, pcam,isDebug=True))
    print(shapeOfView(scene['rooms'][R], scene, pcam,isDebug=True))