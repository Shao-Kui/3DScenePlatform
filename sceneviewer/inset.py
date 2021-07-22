import os
import json
import cv2
import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial import ConvexHull
import sys
sys.path.append('..')
import sk
from projection2d import processGeo as p2d, getobjCat

DATASET_ROOT = './dataset'
LATENTSPACE = './latentspace'

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

def showPcamInset(origin):
    maxImgPerRoom = 3

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
    for filename in os.listdir(f'{LATENTSPACE}/autoview/{origin}'):
        if not filename.endswith(r'.json'):
            continue

        identifier = filename.split('.')[0]
        if not os.path.exists(f'{LATENTSPACE}/autoview/{origin}/{identifier}.png'):
            continue

        with open(f'{LATENTSPACE}/autoview/{origin}/{filename}') as f:
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
        if len(room[roomId]) > maxImgPerRoom:
            # compute convex hull
            points = [t['pos'] for t in room[roomId]]
            try:
                hull = ConvexHull(points)
                vertices = hull.vertices
            except:
                # 共綫
                room[roomId] = sorted(room[roomId], key=lambda k: tuple(k['pos']))
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

    totallist = sorted(totallist, key=lambda k: k['pos'][0])
    l = int(len(totallist) / 2)
    leftlist = totallist[:l]
    rightlist = totallist[l:]

    dotradius = 5
    margin = 25
    w, h = 600, 337
    xpad, zpad = 625, 362
    resultImg = cv2.copyMakeBorder(
        orthImg, zpad, zpad, xpad, xpad, cv2.BORDER_CONSTANT, value=[255, 255, 255])

    def cross(p1, p2, p3):
        return np.sign(np.cross(p2-p1, p3-p1))

    def segIntersect(a1, a2, b1, b2):
        if max(a1[0], a2[0]) >= min(b1[0], b2[0]) and max(b1[0], b2[0]) >= min(a1[0], a2[0]) and max(a1[1], a2[1]) >= min(b1[1], b2[1]) and max(b1[1], b2[1]) >= min(a1[1], a2[1]):
            return cross(a1, a2, b1) * cross(a1, a2, b2) <= 0 and cross(b1, b2, a1) * cross(b1, b2, a2) <= 0
        else:
            return False

    def pasteImg(imgList, startPos, stride, lineOffset):
        img, zp, xp = resultImg, zpad, xpad
        if startPos[0] < 0:
            img = cv2.copyMakeBorder(img, abs(startPos[0]), abs(
                startPos[0])+1, 0, 0, cv2.BORDER_CONSTANT, value=[255, 255, 255])
            zp = zpad + abs(startPos[0])
            startPos[0] = 0
        for i in range(len(imgList)):
            checkIntersect = True
            pi2 = np.flip(startPos+lineOffset).astype(int)
            pj2 = np.flip(startPos+lineOffset+stride).astype(int)
            while checkIntersect:
                checkIntersect = False
                pi1 = np.array(imgList[i]['pos']) + [xp, zp]
                for j in range(i+1, len(imgList)):
                    pj1 = np.array(imgList[j]['pos']) + [xp, zp]
                    if np.array_equal(pi1, pj1):
                        continue
                    if segIntersect(pi1, pi2, pj1, pj2):
                        imgList[i], imgList[j] = imgList[j], imgList[i]
                        checkIntersect = True
                        break
            item = imgList[i]
            pcamImg = cv2.imread(
                f"{LATENTSPACE}/autoview/{origin}/{item['identifier']}.png")
            if pcamImg.shape[1] > 600:
                pcamImg = cv2.resize(pcamImg, (600, 337),
                                     interpolation=cv2.INTER_AREA)
            img[startPos[0]:startPos[0]+h, startPos[1]:startPos[1]+w] = pcamImg
            pt1 = (item['pos'][0] + xp, item['pos'][1] + zp)
            pt2 = tuple(np.flip(startPos+lineOffset).astype(int))
            cv2.circle(img, pt1, dotradius, (0, 0, 0), -1)
            cv2.circle(img, pt2, dotradius, (0, 0, 0), -1)
            cv2.line(img, pt1, pt2, (0, 0, 0), thickness=2)
            startPos += stride
        return img, zp, xp

    cap = int(orthImgWidth / 625)
    topbottomlist = []
    rightlist = sorted(rightlist, key=lambda k: (
        k['pos'][0], min(k['pos'][1], orthImgHeight-k['pos'][1])))
    idx = 0
    if len(rightlist) > len(leftlist) and cap != 0:
        capp = cap + 1
    else:
        capp = cap
    while idx < len(rightlist) and len(rightlist) > orthImgHeight / 337 and len(topbottomlist) < capp:
        x, z = rightlist[idx]['pos']
        if (orthImgWidth - x) / orthImgWidth < min(z, orthImgHeight - z) / orthImgHeight:
            idx += 1
            continue
        topbottomlist.append(rightlist[idx])
        rightlist.pop(idx)

    leftlist = sorted(
        leftlist, key=lambda k: (-k['pos'][0], min(k['pos'][1], orthImgHeight-k['pos'][1])))
    idx = 0
    while idx < len(leftlist) and len(leftlist) > orthImgHeight / 337 and len(topbottomlist) < cap * 2:
        x, z = leftlist[idx]['pos']
        if x / orthImgWidth < min(z, orthImgHeight - z) / orthImgHeight:
            idx += 1
            continue
        topbottomlist.append(leftlist[idx])
        leftlist.pop(idx)

    topbottomlist = sorted(topbottomlist, key=lambda k: k['pos'][1])
    l = 0
    while l < min(len(topbottomlist), cap) and topbottomlist[l]['pos'][1] < 0.5 * orthImgHeight:
        l += 1
    if len(topbottomlist) - l > cap:
        l = len(topbottomlist) - cap
    toplist = topbottomlist[:l]
    bottomlist = topbottomlist[l:]

    # print('left', len(leftlist))
    leftlist = sorted(leftlist, key=lambda k: k['pos'][1])
    startpos = np.array(
        [int(zpad + zcenter - h * len(leftlist) / 2 - margin * (len(leftlist) - 1) / 2), 0])
    stride = np.array([h+margin, 0])
    resultImg, zpad, xpad = pasteImg(leftlist, startpos, stride, [h/2, w])

    # print('right', len(rightlist))
    rightlist = sorted(rightlist, key=lambda k: k['pos'][1])
    startpos = np.array([int(zpad + zcenter - h * len(rightlist) / 2 -
                             margin * (len(rightlist) - 1) / 2), resultImg.shape[1]-xpad+margin])
    stride = np.array([h+margin, 0])
    resultImg, zpad, xpad = pasteImg(rightlist, startpos, stride, [h/2, 0])

    # print('top', len(toplist))
    toplist = sorted(toplist, key=lambda k: k['pos'][0])
    startpos = np.array([int((zpad-362)/2), int(xpad + xcenter -
                                                w * len(toplist) / 2 - margin * (len(toplist) - 1) / 2)])
    stride = np.array([0, w+margin])
    resultImg, zpad, xpad = pasteImg(toplist, startpos, stride, [h, w/2])

    # print('bottom', len(bottomlist))
    bottomlist = sorted(bottomlist, key=lambda k: k['pos'][0])
    startpos = np.array([resultImg.shape[0]-int((zpad+312)/2), int(xpad +
                                                                   xcenter - w * len(bottomlist) / 2 - margin * (len(bottomlist) - 1) / 2)])
    stride = np.array([0, w+margin])
    resultImg, zpad, xpad = pasteImg(bottomlist, startpos, stride, [0, w/2])

    resultImg = trimWhiteSpace(resultImg)
    """
        Shao-Kui has changed the dir from f'{origin}.png' to:
    """
    cv2.imwrite(f'{LATENTSPACE}/autoview/{origin}/showPcamInset.png', resultImg)


def showPcamPoints(origin):
    with open(f'{DATASET_ROOT}/alilevel_door2021/{origin}.json') as f:
        scenejson = json.load(f)
    lb, ub = getBBox(scenejson)

    orthImg = cv2.imread(f'{DATASET_ROOT}/alilevel_door2021_orth/{origin}.png')
    orthImg = trimWhiteSpace(orthImg)
    xscale = orthImg.shape[1] / (ub[0] - lb[0])
    zscale = orthImg.shape[0] / (ub[1] - lb[1])

    for filename in os.listdir(f'{LATENTSPACE}/autoview/{origin}'):
        if not filename.endswith(r'.json'):
            continue

        identifier = filename.split('.')[0]
        if not os.path.exists(f'{LATENTSPACE}/autoview/{origin}/{identifier}.png'):
            continue

        with open(f'{LATENTSPACE}/autoview/{origin}/{filename}') as f:
            pcam = json.load(f)

        x = int((ub[0] - pcam['probe'][0]) * xscale)
        z = int((ub[1] - pcam['probe'][2]) * zscale)
        cv2.circle(orthImg, (x, z), 5, (0, 0, 0), -1)

    """
        Shao-Kui has changed the dir from f'pp_{origin}.png' to:
    """
    cv2.imwrite(f'{LATENTSPACE}/autoview/{origin}/showPcamPoints.png', orthImg)

def insetBatch(origins):
    for origin in origins:
        showPcamPoints(origin)
        showPcamInset(origin)
        shutil.copy(f'{LATENTSPACE}/autoview/{origin}/showPcamInset.png', f'./sceneviewer/mapping/{origin}.png')

# floorplanlist = [_.split('.')[0]
#                  for _ in os.listdir('../dataset/alilevel_door2021')]
# for o in floorplanlist:
#     print(o)
#     showPcamInset(o)
#     showPcamPoints(o)
