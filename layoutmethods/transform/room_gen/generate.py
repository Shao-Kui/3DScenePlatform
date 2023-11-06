import os
import json
import numpy as np
from tqdm import tqdm
import random
from math import *

DOOR_H =2.2
WINDOW_H1=0.8
WINDOW_H2=2.2

DOOR_W1=0.8
DOOR_W2=1.6
WINDOW_W1=1
WINDOW_W2=2
WALL_W=0.12

THRES=10

HEIGHT_RATIO = 1.3
CANVAS_WIDTH = 1000

def code2objnum(code:int):
    # return number of: door1, door2, window1, window2
    if code==0:
        return 1,0,0,0
    if code==1:
        return 1,0,0,0
    if code==2:
        return 0,1,0,0
    if code==3:
        return 0,1,0,0
    if code==4:
        return 0,0,1,0
    if code==5:
        return 0,0,1,0
    if code==6:
        return 0,0,1,0
    if code==7:
        return 0,0,0,1
    if code==8:
        return 0,0,0,1
    if code==9:
        return 0,0,0,1
    if code==10:
        return 0,0,2,0
    if code==11:
        return 0,0,0,2
    if code==12:
        return 0,0,3,0
    if code>12:
        return 0,0,0,0
    

def code2layout(code:int,length:float):
    objList=[]
    if code==0:
        objList.append((0,length*0.1+DOOR_W1/2+0.1))
    if code==1:
        objList.append((0,length*0.5-0.1))
    if code==2:
        objList.append((1,length*0.1+DOOR_W2/2+0.1))
    if code==3:
        objList.append((1,length*0.5-0.1))
    if code==4:
        objList.append((2,length*0.5))
    if code==5:
        objList.append((2,length*0.2+WINDOW_W1/2))
    if code==6:
        objList.append((2,length*0.8-WINDOW_W1/2))
    if code==7:
        objList.append((3,length*0.5))
    if code==8:
        objList.append((3,length*0.2+WINDOW_W2/2))
    if code==9:
        objList.append((3,length*0.8-WINDOW_W2/2))
    if code==10:
        objList.append((2,length*0.25))
        objList.append((2,length*0.75))
    if code==11:
        objList.append((3,length*0.25))
        objList.append((3,length*0.75))
    if code==12:
        objList.append((2,(length-WINDOW_W1)*0.25))
        objList.append((2,length*0.5))
        objList.append((2,length-(length-WINDOW_W1)*0.25))

    return objList
    
def len2codelist(length:float):
    codeList=[13]
    if length*0.5>length*0.1+DOOR_W1/2+0.1:
        codeList.append(0)
    if length>length*0.5+0.1+DOOR_W1/2 and length*0.5-0.1>length*0.1+DOOR_W1/2+0.1:
        codeList.append(1)
    if length*0.5>length*0.1+DOOR_W2/2+0.1:
        codeList.append(2)
    if length>length*0.5+0.1+DOOR_W2/2 and length*0.5-0.1>length*0.1+DOOR_W2/2+0.1:
        codeList.append(3)
    if length>WINDOW_W1+0.4:
        codeList.append(4)
    if length*0.3>WINDOW_W1/2:
        codeList.append(5)
    if length*0.3>WINDOW_W1/2:
        codeList.append(6)
    if length>WINDOW_W2+0.4:
        codeList.append(7)
    if length*0.3>WINDOW_W2/2:
        codeList.append(8)
    if length*0.3>WINDOW_W2/2:
        codeList.append(9)
    if length*0.25>WINDOW_W1/2+0.2:
        codeList.append(10)
    if length*0.25>WINDOW_W2/2+0.2:
        codeList.append(11)
    if (length-WINDOW_W1)*0.25>WINDOW_W1/2+0.2:
        codeList.append(12)
    return codeList


def p(x: float, y: float):
    """a point or a vector"""
    return np.array([x, y])

def norm(vector: np.ndarray):
    """return the normalized vector"""
    if np.linalg.norm(vector) > 0:
        return vector / np.linalg.norm(vector)
    return vector

def rot(point: np.ndarray, angle: float):
    """rotate a vector counter-clockwise, angle is in radian"""
    return np.array([point[0] * cos(angle) - point[1] * sin(angle), point[0] * sin(angle) + point[1] * cos(angle)])


def layout(w:float,h:float,holes_list:list,idx:int):
    out = {}
    out['origin'] = 'roomframe'
    out['id'] = '{}_{}_{}'.format(w,h,idx)
    # out['islod'] = True
    out['bbox'] = {"min": [0, 0, 0], "max": [w, 3, h]}
    out['up'] = [0, 1, 0]
    out['front'] = [0, 0, 1]
    room = {}
    room['id'] = out['id']+ '_0'
    room['modelId'] = "Bathroom-6473"
    room['roomTypes'] = ["Bathroom"]
    room['bbox'] = {"min": [0, 0, 0], "max": [w, 3, h]}
    room['origin'] = out['origin']
    room['roomId'] = 0

    pointList=[p(0,0),p(w,0),p(w,h),p(0,h)]
    room['roomShape'] = [[(float)(point[0]), (float)(point[1])] for point in pointList]
    room['roomNorm'] = []
    for k in range(len(pointList)):
        n = norm(rot(pointList[(k + 1) % len(pointList)] - pointList[k], pi / 2))
        room['roomNorm'].append([(float)(n[0]), (float)(n[1])])
    room['roomOrient'] = [
        pi / 2 - atan2(room['roomNorm'][k][1], room['roomNorm'][k][0]) for k in range(len(room['roomNorm']))
    ]
    room['roomShapeBBox'] = {"min": [0, 0],"max": [w, h] }
    
    objList = []
    for wall_idx in range(4):
        holes=holes_list[wall_idx]
        for hole_info in holes:
            hole_pos=hole_info[1]
            hole_type,hole_w,hole_h1,hole_h2=None,None,None,None
            if hole_info[0]==0:
                hole_type='Door'
                hole_w=DOOR_W1
                hole_h1=0
                hole_h2=DOOR_H
            elif hole_info[0]==1:
                hole_type='Door'
                hole_w=DOOR_W2
                hole_h1=0
                hole_h2=DOOR_H
            elif hole_info[0]==2:
                hole_type='Window'
                hole_w=WINDOW_W1
                hole_h1=WINDOW_H1
                hole_h2=WINDOW_H2
            elif hole_info[0]==3:
                hole_type='Window'
                hole_w=WINDOW_W2
                hole_h1=WINDOW_H1
                hole_h2=WINDOW_H2
            hole = {}
            hole['modelId'] = 'noUse'
            hole['roomId'] = 0
            hole['scale'] = [1, 1, 1]
            hole['orient'] = 0
            hole['rotate'] = [0, 0, 0]
            hole['key'] = hole_type
            hole['translate'] = [0, 0, 0]
            vec=rot(p(1,0),wall_idx*pi/2)
            p1=pointList[wall_idx]+vec*(hole_pos-hole_w/2)
            p2=pointList[wall_idx]+vec*(hole_pos+hole_w/2)+rot(vec,-pi/2)*WALL_W
            hole['bbox'] = {
                "min": [min(p1[0],p2[0]), hole_h1, min(p1[1],p2[1])],
                "max": [max(p1[0],p2[0]), hole_h2, max(p1[1],p2[1])]
            }
            hole['inDatabase']=False
            hole['format']=hole_type
            hole['coarseSemantic'] = hole_type
            
            objList.append(hole)
    
    room['objList'] = objList
    room['blockList'] =objList
    rooms = [room]
    out['rooms'] = rooms

    # configure the camera
    camera = {}
    camera['fov'] = 75
    camera['focalLength'] = 35
    camera['rotate'] = [-pi / 2, 0, 0]
    camera['up'] = [0, 0, -1]
    camera['roomId'] = 0
    camera['target'] = [w / 2, 0, h / 2]
    camHeight = min(w, h) * HEIGHT_RATIO
    camera['origin'] = [w/ 2, camHeight, h / 2]
    out['PerspectiveCamera'] = camera
    # configure the canvas
    canvas = {'width': CANVAS_WIDTH, 'height': (int)(CANVAS_WIDTH / w * h)}
    out['canvas'] = canvas

    # dump to file
    with open('scenes/{}_{}_{}.json'.format(w,h,idx), 'w') as outf:
        json.dump(out, outf)

if __name__=='__main__':
    random.seed()
    sizes=[]
    for i in range(6,10):
        for j in range(i,min(17,2*i+1)):
            sizes.append(p(i*0.5,j*0.5))
    
    total_count=0
    
    chosen=[]
    for iter in tqdm(range(100)):
        code_tuple=None
        while True:
            while True:
                code_list=[]
                d1,d2,w1,w2=0,0,0,0
                for i in range(4):
                    rand_num=min(13,random.randint(0,19))
                    objnum=code2objnum(rand_num)
                    d1+=objnum[0]
                    d2+=objnum[1]
                    w1+=objnum[2]
                    w2+=objnum[3]
                    code_list.append(rand_num)
                code_tuple=tuple(code_list)
                if d1+d2>0 and d1+d2<=2 and d2<=1 and w1+w2>0 and w1+w2<=3 and (code_tuple not in chosen):
                    break
            
            success=True
            for size in sizes:
                w,h=size[1],size[0]
                clist=[len2codelist(w),len2codelist(h),len2codelist(w),len2codelist(h)]
                valid=True
                for i in range(4):
                    if code_tuple[i] not in clist[i]:
                        valid=False
                        break
                if not valid:
                    success=False
                    break
            if success:
                break
        
        chosen.append(code_tuple)
        for size in sizes:
            w,h=size[1],size[0]
            layout(w,h,[code2layout(code_tuple[0],w),code2layout(code_tuple[1],h),code2layout(code_tuple[2],w),code2layout(code_tuple[3],h)],iter)
            
    # for size in tqdm(sizes):
    #     w,h=size[1],size[0]
    #     clist=[len2codelist(w),len2codelist(h),len2codelist(w),len2codelist(h)]
    #     combo_list=[]
    #     combo_count=0     
    #     for i in clist[0]:
    #         for j in clist[1]:
    #             for k in clist[2]:
    #                 for l in clist[3]:
    #                     d1,d2,w1,w2=0,0,0,0
    #                     nums=[code2objnum(i),code2objnum(j),code2objnum(k),code2objnum(l)]
    #                     for num in nums:
    #                         d1+=num[0]
    #                         d2+=num[1]
    #                         w1+=num[2]
    #                         w2+=num[3]
    #                     if d1+d2>0 and d1+d2<=2 and d2<=1 and w1+w2>0 and w1+w2<=3:
    #                         combo_list.append((i,j,k,l))
    #                         combo_count+=1       
    #     for i in range(THRES):
    #         target_idx=(int)(combo_count/THRES*(i+random.random()))
    #         target=combo_list[target_idx]
    #         layout(w,h,[code2layout(target[0],w),code2layout(target[1],h),code2layout(target[2],w),code2layout(target[3],h)],i)
        
    #     total_count+=combo_count
        # print(combo_count)
    # print(total_count)
    
