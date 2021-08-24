import os
import json
import cv2
import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial import ConvexHull
import shutil
import sys
sys.path.append('..')
import sk
from projection2d import processGeo as p2d
from skimage import draw

DATASET_ROOT = './dataset'
LATENTSPACE = './latentspace/autoview'
# LATENTSPACE = './sceneviewer/results'

def getBBox(scenejson):
    points = []
    for room in scenejson['rooms']:
        try:
            floorMeta = p2d('.', '/dataset/room/{}/{}f.obj'.format(room['origin'], room['modelId']))
            points += floorMeta[:, 0:2].tolist()
            wallMeta = sk.getMeshVertices('./dataset/room/{}/{}w.obj'.format(room['origin'], room['modelId']))
            points += wallMeta[:, [0, 2]].tolist()
        except:
            continue
    v = np.array(points)
    l = np.min(v[:, 0])
    r = np.max(v[:, 0])
    u = np.min(v[:, 1])
    d = np.max(v[:, 1])
    return ([l, u], [r, d])

def trimWhiteSpace(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    crop_rows = img[~np.all(gray == 255, axis=1), :]
    cropped_image = crop_rows[:, ~np.all(gray == 255, axis=0)]
    return cropped_image.copy()

def showPcamInset(origin, maxImgPerRoom = 3, beziercurve = False, doCompleteIntersectionCheck=True):
    with open(f'{DATASET_ROOT}/alilevel_door2021/{origin}.json') as f:
        scenejson = json.load(f)

    lb, ub = getBBox(scenejson)

    orthImg = cv2.imread(f'{DATASET_ROOT}/alilevel_door2021_orth/{origin}.png')
    orthImg = trimWhiteSpace(orthImg)
    orthImgHeight, orthImgWidth = orthImg.shape[:2]

    xcenter = orthImgWidth / 2
    zcenter = orthImgHeight / 2
    xscale = orthImgWidth / (ub[0] - lb[0])
    zscale = orthImgHeight / (ub[1] - lb[1])

    room = {}
    for filename in os.listdir(f'{LATENTSPACE}/{origin}'):
        if not filename.endswith(r'.json'):
            continue

        identifier = filename.split('.')[0]
        if not os.path.exists(f'{LATENTSPACE}/{origin}/{identifier}.png'):
            continue

        with open(f'{LATENTSPACE}/{origin}/{filename}') as f:
            pcam = json.load(f)

        x = int((ub[0] - pcam['probe'][0]) * xscale)
        z = int((ub[1] - pcam['probe'][2]) * zscale)
        roomId = pcam['roomId']
        if roomId not in room:
            room[roomId] = [{'identifier': identifier, 'pos': [x, z]}]
        else:
            room[roomId].append({'identifier': identifier, 'pos': [x, z]})

    totallist = []

    toplist, bottomlist, leftlist, rightlist = [], [], [], []
    for roomId in room.keys():
        if maxImgPerRoom > 0 and len(room[roomId]) > maxImgPerRoom:
            # compute convex hull
            points = [t['pos'] for t in room[roomId]]
            try:
                hull = ConvexHull(points)
                vertices = hull.vertices
            except:
                # collinear
                room[roomId].sort(key=lambda k: tuple(k['pos']))
                vertices = np.arange(len(room[roomId]))
            if len(vertices) > maxImgPerRoom:
                pcamlist = []
                k = len(vertices) / maxImgPerRoom
                for i in range(maxImgPerRoom):
                    pcamlist.append(room[roomId][vertices[int(i*k)]])
            else:
                pcamlist = [room[roomId][i] for i in vertices]
                if len(pcamlist) < maxImgPerRoom:
                    rest = np.setdiff1d(np.arange(len(room[roomId])), vertices)
                    k = maxImgPerRoom-len(pcamlist)
                    pcamlist.extend([room[roomId][i] for i in rest[:k]])
        else:
            pcamlist = room[roomId]

        totallist.extend(pcamlist)

    totallist.sort(key=lambda k: (k['pos'][0], min(k['pos'][1], orthImgHeight-k['pos'][1])))
    dotradius = 5
    margin = 25
    w, h = 600, 337
    xpad, zpad = 625, 362
    # assign perspective views to the left, right, top and/or bottom
    zcapacity = (int(orthImgHeight / zpad + 0.3) + 1) * 2
    xcapacity = int(orthImgWidth / xpad)
    if len(totallist) <= zcapacity or xcapacity == 0:
        # space on left & right is enough OR no room in the middle
        halflen = int(len(totallist) / 2)
        if len(totallist) % 2 == 1 and totallist[halflen]['pos'][0] < orthImgWidth - totallist[halflen]['pos'][0]:
            halflen += 1
        leftlist = totallist[:halflen]
        rightlist = totallist[halflen:]
    else:
        zcapacity += 2
        if len(totallist) <= xcapacity + zcapacity:
            # (left, right, top) or (left, right, bottom)
            ll = int((len(totallist) - xcapacity) / 2)
            if (len(totallist) - xcapacity) % 2 == 1 and totallist[ll]['pos'][0] < orthImgWidth - totallist[ll+xcapacity]['pos'][0]:
                ll += 1
            leftlist = totallist[:ll]
            middlelist = totallist[ll:ll+xcapacity]
            rightlist = totallist[ll+xcapacity:]
            topcost = sum([k['pos'][1] for k in middlelist])
            btmcost = orthImgHeight * len(middlelist) - topcost
            if topcost > btmcost:
                bottomlist = middlelist
            else:
                toplist = middlelist
        else:
            # take up both top and bottom
            ll = int((len(totallist) - xcapacity * 2) / 2)
            leftlist = totallist[:ll]
            middlelist = totallist[ll:ll+xcapacity*2]
            rightlist = totallist[ll+xcapacity*2:]
            middlelist.sort(key=lambda k: k['pos'][1])
            toplist = middlelist[:xcapacity]
            bottomlist = middlelist[xcapacity:]

    def cross(p1, p2, p3):
        return np.sign(np.cross(p2-p1, p3-p1))

    def segIntersect(a1, a2, b1, b2):
        if np.array_equal(a1, b1):
            return False
        # intersection test with segment thickness 5px
        a0max, a0min, a1max, a1min = max(a1[0], a2[0])+5, min(a1[0], a2[0])-5, max(a1[1], a2[1])+5, min(a1[1], a2[1])-5
        b0max, b0min, b1max, b1min = max(b1[0], b2[0])+5, min(b1[0], b2[0])-5, max(b1[1], b2[1])+5, min(b1[1], b2[1])-5
        if a0max >= b0min and b0max >= a0min and a1max >= b1min and b1max >= a1min:
            if cross(a1, a2, b1) * cross(a1, a2, b2) <= 0 and cross(b1, b2, a1) * cross(b1, b2, a2) <= 0:
                return True
            else:
                if np.linalg.norm(b1-a1) > 10:
                    if a0min <= b1[0] <= a0max and a1min <= b1[1] <= a1max:
                        return np.abs(np.cross(a2-a1,b1-a1))/np.linalg.norm(a2-a1) < 5
                    elif b0min <= a1[0] <= b0max and b1min <= a1[1] <= b1max:
                        return np.abs(np.cross(b2-b1,a1-b1))/np.linalg.norm(b2-b1) < 5
                    else:
                        return False
                else:
                    return False
        else:
            return False

    def bezierPos(p1, p2, dir):
        b = bezierDict[dir]
        return np.array([p2[k] if b[k] == -1 else int((b[k]*2+p1[k])/3) for k in range(2)])

    def assignPout(dir, startPos):
        # intersection check & assign position for each perspective view
        imgList = layout[dir]
        startPos = np.array(startPos)
        stride = np.array(strideDict[dir])
        poffset = np.array(poutoffset[dir])
        for i in range(len(imgList)):
            checkIntersect = True
            pi2 = np.array(startPos+poffset).astype(int)
            pj2 = np.array(startPos+poffset+stride).astype(int)
            while checkIntersect:
                checkIntersect = False
                pi1 = np.array(imgList[i]['pos'])
                for j in range(i+1, len(imgList)):
                    pj1 = np.array(imgList[j]['pos'])
                    if segIntersect(pi1, pi2, pj1, pj2):
                        imgList[i], imgList[j] = imgList[j], imgList[i]
                        checkIntersect = True
                        break
            imgList[i]['startPos'] = startPos.astype(int)
            imgList[i]['pos'] = pi1
            imgList[i]['pout'] = pi2
            imgList[i]['bezier'] = bezierPos(pi1, pi2, dir)
            startPos += stride

    def pasteImg(img, padding, bezier=False):
        imgList = layout['left']+layout['right']+layout['top']+layout['bottom']
        for item in imgList:
            startPos = item['startPos'] + padding
            pcamImg = cv2.imread(
                f"{LATENTSPACE}/{origin}/{item['identifier']}.png")
            if pcamImg.shape[1] > 600:
                pcamImg = cv2.resize(pcamImg, (600, 337), interpolation=cv2.INTER_AREA)
            img[startPos[1]:startPos[1]+h, startPos[0]:startPos[0]+w] = pcamImg
            pt1 = tuple(np.array(item['pos']) + padding)
            pt2 = tuple(item['pout'] + padding)
            cv2.circle(img, pt1, dotradius, (0, 0, 0), -1, lineType=cv2.LINE_AA)
            cv2.circle(img, pt2, dotradius, (0, 0, 0), -1, lineType=cv2.LINE_AA)
            if bezier:
                bz = item['bezier'] + padding
                rr, cc = draw.bezier_curve(pt1[1],pt1[0],bz[1],bz[0],pt2[1],pt2[0],2)
                img[rr,cc] = [0,0,0]
            else:
                cv2.line(img, pt1, pt2, (0, 0, 0), thickness=2, lineType=cv2.LINE_AA)
        return img

    leftlist.sort(key=lambda k: k['pos'][1])
    rightlist.sort(key=lambda k: k['pos'][1])
    toplist.sort(key=lambda k: k['pos'][0])
    bottomlist.sort(key=lambda k: k['pos'][0])

    layout = {'left': leftlist, 'right': rightlist, 'top': toplist, 'bottom': bottomlist}
    poutoffset = {'left': [w, h/2], 'right': [0, h/2], 'top': [w/2, h], 'bottom': [w/2, 0]}
    strideDict = {'left': [0, h+margin], 'right': [0, h+margin], 'top': [w+margin, 0], 'bottom': [w+margin, 0]}
    bezierDict = {'left': [0, -1], 'right': [orthImgWidth, -1], 'top': [-1, 0], 'bottom': [-1, orthImgHeight]}

    zmin, zmax = 0, orthImgHeight
    if len(toplist) != 0:
        zmin = -zpad
    if len(bottomlist) != 0:
        zmax += zpad
    zcenter = int((zmin + zmax) / 2)
    
    assignPout('left', [-xpad, zcenter - (zpad * len(leftlist) - margin) / 2])
    assignPout('right', [orthImgWidth + margin, zcenter - (zpad * len(rightlist) - margin) / 2])
    zmin = min(zmin, int(zcenter - (zpad * max(len(leftlist), len(rightlist)) - margin) / 2))
    zmax = max(zmax, zmin + zpad * max(len(leftlist), len(rightlist)) - margin)
    if len(toplist) != 0:
        assignPout('top', [xcenter - (xpad * len(toplist) - margin) / 2, (-zpad+zmin)/2])
    if len(bottomlist) != 0:
        assignPout('bottom', [xcenter - (xpad * len(bottomlist) - margin) / 2, (orthImgHeight+margin+zmax-h)/2])
    
    def hasIntersectBetween(dir1, dir2):
        list1, list2 = layout[dir1], layout[dir2]
        for i in range(len(list1)):
            pi1, pi2 = list1[i]['pos'], list1[i]['pout']
            for j in range(len(list2)):
                pj1, pj2 = list2[j]['pos'], list2[j]['pout']
                if segIntersect(pi1, pi2, pj1, pj2):
                    list1[i]['identifier'], list2[j]['identifier'] = list2[j]['identifier'], list1[i]['identifier']
                    list1[i]['pos'], list2[j]['pos'] = list2[j]['pos'], list1[i]['pos']
                    list1[i]['bezier'] = bezierPos(list1[i]['pos'], pi2, dir1)
                    list2[j]['bezier'] = bezierPos(list2[j]['pos'], pj2, dir2)
                    return True
        return False
    
    def rearrange(dir):
        imgList = layout[dir]
        for i in range(len(imgList)):
            pi2 = imgList[i]['pout']
            checkIntersect = True
            while checkIntersect:
                checkIntersect = False
                pi1 = imgList[i]['pos']
                for j in range(i+1, len(imgList)):
                    pj1, pj2 = imgList[j]['pos'], imgList[j]['pout']
                    if segIntersect(pi1, pi2, pj1, pj2):
                        imgList[i]['identifier'], imgList[j]['identifier'] = imgList[j]['identifier'], imgList[i]['identifier']
                        imgList[i]['pos'], imgList[j]['pos'] = imgList[j]['pos'], imgList[i]['pos']
                        imgList[i]['bezier'] = bezierPos(imgList[i]['pos'], pi2, dir)
                        imgList[j]['bezier'] = bezierPos(imgList[j]['pos'], pj2, dir)
                        checkIntersect = True
                        break

    if doCompleteIntersectionCheck:
        # time comsuming but can avoid all intersection
        tl, tr, bl, br = True, True, True, True
        while tl or tr or bl or br:
            if tl and hasIntersectBetween('top', 'left'):
                rearrange('top')
                rearrange('left')
                tl, tr, bl = True, True, True
            else:
                tl = False
            if tr and hasIntersectBetween('top', 'right'):
                rearrange('top')
                rearrange('right')
                tl, tr, br = True, True, True
            else:
                tr = False
            if bl and hasIntersectBetween('bottom', 'left'):
                rearrange('bottom')
                rearrange('left')
                tl, br, bl = True, True, True
            else:
                bl = False
            if br and hasIntersectBetween('bottom', 'right'):
                rearrange('bottom')
                rearrange('right')
                bl, tr, br = True, True, True
            else:
                br = False
    
    resultImg = cv2.copyMakeBorder(orthImg, -zmin, zmax-orthImgHeight, xpad, xpad, cv2.BORDER_CONSTANT, value=[255, 255, 255])
    resultImg = pasteImg(resultImg, [xpad, -zmin], beziercurve)
    resultImg = trimWhiteSpace(resultImg)
    """
        Shao-Kui has changed the dir from f'{origin}.png' to:
    """
    cv2.imwrite(f'{LATENTSPACE}/{origin}/showPcamInset2.png', resultImg)


def showPcamPoints(origin):
    with open(f'{DATASET_ROOT}/alilevel_door2021/{origin}.json') as f:
        scenejson = json.load(f)
    lb, ub = getBBox(scenejson)

    orthImg = cv2.imread(f'{DATASET_ROOT}/alilevel_door2021_orth/{origin}.png')
    orthImg = trimWhiteSpace(orthImg)
    xscale = orthImg.shape[1] / (ub[0] - lb[0])
    zscale = orthImg.shape[0] / (ub[1] - lb[1])

    for filename in os.listdir(f'{LATENTSPACE}/{origin}'):
        if not filename.endswith(r'.json'):
            continue

        identifier = filename.split('.')[0]
        if not os.path.exists(f'{LATENTSPACE}/{origin}/{identifier}.png'):
            continue

        with open(f'{LATENTSPACE}/{origin}/{filename}') as f:
            pcam = json.load(f)

        x = int((ub[0] - pcam['probe'][0]) * xscale)
        z = int((ub[1] - pcam['probe'][2]) * zscale)
        cv2.circle(orthImg, (x, z), 5, (0, 0, 0), -1)

    """
        Shao-Kui has changed the dir from f'pp_{origin}.png' to:
    """
    cv2.imwrite(f'{LATENTSPACE}/{origin}/showPcamPoints.png', orthImg)

def insetBatch(origins):
    for origin in origins:
        showPcamPoints(origin)
        showPcamInset(origin)
        shutil.copy(f'{LATENTSPACE}/{origin}/showPcamInset.png', f'./sceneviewer/mapping/{origin}.png')
