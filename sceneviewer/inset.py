import os
import json
import cv2
import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial import ConvexHull


def showPcamInset(origin):
    maxImgPerRoom = 3

    with open(f'../dataset/alilevel_door2021/{origin}.json') as f:
        scenejson = json.load(f)
    lb = scenejson['bbox']['min']
    ub = scenejson['bbox']['max']

    orthImg = cv2.imread(f'../dataset/alilevel_door2021_orth/{origin}.png')

    xcenter = orthImg.shape[1] / 2
    zcenter = orthImg.shape[0] / 2
    xscale = orthImg.shape[1] / (ub[0] - lb[0])
    zscale = orthImg.shape[0] / (ub[2] - lb[2])

    room = {}
    for filename in os.listdir(f'../latentspace/autoview/{origin}'):
        if not filename.endswith(r'.json'):
            continue

        identifier = filename.split('.')[0]
        if not os.path.exists(f'../latentspace/autoview/{origin}/{identifier}.png'):
            continue

        with open(f'../latentspace/autoview/{origin}/{filename}') as f:
            pcam = json.load(f)

        x = int((ub[0] - pcam['probe'][0]) * xscale)
        z = int((ub[2] - pcam['probe'][2]) * zscale)
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
                print(points)
                vertices = np.arange(len(room[roomId]))
            if len(hull.vertices) > maxImgPerRoom:
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
    xpad, zpad = 625, 0
    resultImg = cv2.copyMakeBorder(
        orthImg, zpad, zpad, xpad, xpad, cv2.BORDER_CONSTANT, value=[255, 255, 255])

#     show diagonal
#     cv2.line(resultImg, (xpad, zpad), (orthImg.shape[1]+xpad, orthImg.shape[0]+zpad), (0, 0, 0))
#     cv2.line(resultImg, (xpad, orthImg.shape[0]+zpad), (orthImg.shape[1]+xpad, zpad), (0, 0, 0))

    def cross(p1, p2, p3):
        x1, y1 = p2 - p1
        x2, y2 = p3 - p1
        return np.sign(x1 * y2 - x2 * y1)

    def segIntersect(a1, a2, b1, b2):
        if max(a1[0], a2[0]) >= min(b1[0], b2[0]) and max(b1[0], b2[0]) >= min(a1[0], a2[0]) and max(a1[1], a2[1]) >= min(b1[1], b2[1]) and max(b1[1], b2[1]) >= min(a1[1], a2[1]):
            if cross(a1, a2, b1) * cross(a1, a2, b2) <= 0 and cross(b1, b2, a1) * cross(b1, b2, a2) <= 0:
                return True
            else:
                return False
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
                    if segIntersect(pi1, pi2, pj1, pj2):
                        imgList[i], imgList[j] = imgList[j], imgList[i]
                        checkIntersect = True
                        break
            item = imgList[i]
            pcamImg = cv2.imread(
                f"../latentspace/autoview/{origin}/{item['identifier']}.png")
            img[startPos[0]:startPos[0]+h, startPos[1]:startPos[1]+w] = pcamImg
            pt1 = (item['pos'][0] + xp, item['pos'][1] + zp)
            pt2 = tuple(np.flip(startPos+lineOffset).astype(int))
            cv2.circle(img, pt1, dotradius, (0, 0, 0), -1)
            cv2.circle(img, pt2, dotradius, (0, 0, 0), -1)
            cv2.line(img, pt1, pt2, (0, 0, 0), thickness=2)
            startPos += stride
        return img, zp, xp

    leftlist = sorted(leftlist, key=lambda k: (k['pos'][1], -k['pos'][0]))
    startpos = np.array(
        [int(zpad + zcenter - h * len(leftlist) / 2 - margin * (len(leftlist) - 1) / 2), 0])
    stride = np.array([h+margin, 0])
    resultImg, zpad, xpad = pasteImg(leftlist, startpos, stride, [h/2, w])

    rightlist = sorted(rightlist, key=lambda k: (k['pos'][1], k['pos'][0]))
    startpos = np.array([int(zpad + zcenter - h * len(rightlist) / 2 -
                             margin * (len(rightlist) - 1) / 2), resultImg.shape[1]-xpad+margin])
    stride = np.array([h+margin, 0])
    resultImg, zpad, xpad = pasteImg(rightlist, startpos, stride, [h/2, 0])

    cv2.imwrite(f'{origin}.png', resultImg)
    plt.imshow(resultImg)


def showPcamPoints(origin):
    with open(f'../dataset/alilevel_door2021/{origin}.json') as f:
        scenejson = json.load(f)
    lb = scenejson['bbox']['min']
    ub = scenejson['bbox']['max']

    orthImg = cv2.imread(f'../dataset/alilevel_door2021_orth/{origin}.png')
    xscale = orthImg.shape[1] / (ub[0] - lb[0])
    zscale = orthImg.shape[0] / (ub[2] - lb[2])

    for filename in os.listdir(f'../latentspace/autoview/{origin}'):
        if not filename.endswith(r'.json'):
            continue

        identifier = filename.split('.')[0]
        if not os.path.exists(f'../latentspace/autoview/{origin}/{identifier}.png'):
            continue

        with open(f'../latentspace/autoview/{origin}/{filename}') as f:
            pcam = json.load(f)

        x = int((ub[0] - pcam['probe'][0]) * xscale)
        z = int((ub[2] - pcam['probe'][2]) * zscale)
        cv2.circle(orthImg, (x, z), 5, (0, 0, 0), -1)

    cv2.imwrite(f'pp_{origin}.png', orthImg)
    plt.imshow(orthImg)


floorplanlist = ['0047c3ab-951b-4182-9082-b9fbf099c142', '00c0c75e-1c12-46b3-9fc8-0561b1b1b510', '317d64ff-b96e-4743-88f6-2b5b27551a7c', '43d35274-98e2-499a-af69-ac2bb283f708']
for o in floorplanlist:
    showPcamInset(o)
    showPcamPoints(o)