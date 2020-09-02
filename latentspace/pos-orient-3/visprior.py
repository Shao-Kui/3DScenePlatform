import json
import numpy as np
import scipy.stats as st
import cv2
import matplotlib as mpl
import matplotlib.pyplot as plt
import os
from shapely.geometry import Polygon, Point
import sys

mpl.rcParams['figure.dpi'] = 600

with open('F:/3DIndoorScenePlatform/latentspace/obj_coarse_semantic.json') as f:
    obj_semantic = json.load(f)
with open("F:/3DIndoorScenePlatform/latentspace/ls_to_name.json", 'r') as f:
    ls_to_name = json.load(f)
with open("F:/3DIndoorScenePlatform/latentspace/name_to_ls.json", 'r') as f:
    name_to_ls = json.load(f)

SUNCG_OBJ_ROOT = 'F:/3DIndoorScenePlatform/dataset/object'

def load_json_denoised(n, objj, do_filter=False):
    # with open(ROOT + '-denoised-2/{}.json'.format(n)) as f:
    with open('./{}.json'.format(n)) as f:
        pattern = json.load(f)[objj]
    if do_filter:
        contourdir = os.path.join(SUNCG_OBJ_ROOT, n, n + '-contour.json')
        with open(contourdir, 'r') as fc:
            contour = json.load(fc)
        uni = Point()
        for c in contour:
            uni = uni.union(Polygon(c))
        filtered = []

        for point in pattern:
            if uni.intersects(Point((point[0], point[2]))):
                filtered.append(point)
        with open(f'F:\\3DIndoorScenePlatform\\latentspace\\pos-orient-denoised-2\\{n}.json') as f:
            platformpattern = json.load(f)
        platformpattern[objj] = filtered
        with open(f'F:\\3DIndoorScenePlatform\\latentspace\\pos-orient-denoised-2\\{n}.json', 'w') as f:
            json.dump(platformpattern, f)
        return filtered
    else:
        return pattern

def rotate(image, angle, center=None, scale=1.0):
    # 获取图像尺寸
    (h, w) = image.shape[:2]

    # 若未指定旋转中心，则将图像中心设为旋转中心
    if center is None:
        center = (w / 2, h / 2)

    # 执行旋转
    M = cv2.getRotationMatrix2D(center, angle, scale)
    rotated = cv2.warpAffine(image, M, (w, h))

    # 返回旋转后的图像
    return rotated

BAN = ['column', 'fireplace', 'beer', 'partition', 'switch', 'refrigerator', 'hanger', 'wood_board', 'picture_frame',
       'piano', 'mirror', 'vase', 'wardrobe_cabinet', 'air_conditioner', 'kitchen_cabinet', 'book', 'books',
       'shelving', 'baby_bed', 'basketball_hoop', 'pedestal_fan', 'fishbowl', 'wall_lamp']
NAB = ['piano', 'book']
BAN2 = ['lighting', 'Lighting']

def plot_orth(obji, objj, exid='vis', do_filter=False, imgjInverse=False):
    if not os.path.exists(f'./{exid}/blend'):
        os.makedirs(f'./{exid}/blend')
    if not os.path.exists(f'./{exid}/originplot'):
        os.makedirs(f'./{exid}/originplot')
    thealpha = 0.02
    # if obj_semantic[obji] not in NAB and obj_semantic[objj] not in NAB:
    #     return
    for cat in BAN2:
        if cat in obj_semantic[obji] or cat in obj_semantic[objj]:
            return
    # if obj_semantic[obji] == obj_semantic[objj]:
    #     return
    try:
        b = load_json_denoised(obji, objj, do_filter)
    except Exception as e:
        b = []
    b = np.array(b)
    if len(b) < 1:
        return
    print(obji, objj)
    print(obj_semantic[obji], obj_semantic[objj])
    asample = b[np.random.randint(len(b))]
    try:
        resample = st.gaussian_kde(b.T, 0.05).resample(60000)
    except Exception as e:
        print(e)
        resample = b
    b = resample.T
    while len(resample[3][resample[3] > np.pi]) != 0 or len(resample[3][resample[3] < -np.pi]) != 0:
        resample[3][resample[3] > np.pi] -= 2 * np.pi
        resample[3][resample[3] < -np.pi] += 2 * np.pi
    resample[3] += np.pi
    resample[3] = 0.5 * resample[3] / np.pi
    scolors = np.ones(shape=(len(resample[0]), 3))
    scolors[:, 0] = resample[3]

    plt.cla()
    plt.clf()
    plt.figure(figsize=(6, 6))
    # select granularity
    MAXG = np.max(np.abs(b))
    # grain = 1 if 1 >= MAXG else MAXG
    grain = np.max(np.abs(b))
    print(grain)
    plt.xlim((-grain, grain))
    plt.ylim((-grain, grain))
    plt.subplots_adjust(left=0.0, right=1, bottom=0.0, top=1)
    plt.xticks([])
    plt.yticks([])

    plt.scatter(b[:, 0], b[:, 2], c=mpl.colors.hsv_to_rgb(scolors), marker='.', alpha=thealpha, s=72)
    if with_arrow is True:
        plt.quiver(b[:, 0], b[:, 2], np.sin(b[:, 3]), -np.cos(b[:, 3]), width=0.0005, scale=24, headlength=10,
                   headwidth=9)
    if save_fig:
        plt.savefig(
            './{}/originplot/{}({})-{}({}).png'.format(exid, obji, obj_semantic[obji], objj, obj_semantic[objj]),
            transparent=True, figsize=(20, 20))
        # plt.savefig('./{}/originplot/{}({})-{}({})-({}).png'.format(exid, obji, obj_semantic[obji], objj, obj_semantic[objj], csr[i]), transparent=True)
    scatimg = cv2.imread(
        './{}/originplot/{}({})-{}({}).png'.format(exid, obji, obj_semantic[obji], objj, obj_semantic[objj]),
        cv2.IMREAD_UNCHANGED)
    xscale = (0.5 * scatimg.shape[1] / grain) / 1000
    yscale = (0.5 * scatimg.shape[0] / grain) / 1000
    objiimg = cv2.imread(
        'F:/3DIndoorScenePlatform/dataset/object/{}/render6orth/render-{}-4.png'.format(obji, obji),
        cv2.IMREAD_UNCHANGED)
    if objiimg.shape[1] * xscale < 1. or objiimg.shape[0] * yscale < 1.:
        return
    objiimg = cv2.resize(objiimg, (int(objiimg.shape[1] * xscale), int(objiimg.shape[0] * yscale)))
    objj_img = cv2.imread(
        'F:/3DIndoorScenePlatform/dataset/object/{}/render6orth/render-{}-4.png'.format(objj, objj),
        cv2.IMREAD_UNCHANGED)
    if objj_img.shape[1] * xscale < 1. or objj_img.shape[0] * yscale < 1.:
        return
    if imgjInverse:
        objj_img = cv2.resize(objj_img, (int(objj_img.shape[1] * xscale), int(objj_img.shape[0] * yscale)))
    objj_img = rotate(objj_img, 180)
    objj_img = rotate(objj_img, 180 * asample[3] / np.pi)
    objj_img[objj_img == 0.0] = 255.
    # maybe we need to resize imgs of obji and objj first.
    objiimg_pend = scatimg.copy()
    objiimg_pend[:] = 255

    start_0 = int((scatimg.shape[0] / 2) - objiimg.shape[0] / 2)
    start_1 = int((scatimg.shape[1] / 2) - objiimg.shape[1] / 2)
    objiimg_pend[start_0:start_0 + objiimg.shape[0], start_1:start_1 + objiimg.shape[1], 0:3] = objiimg

    objjimg_pend = np.zeros(shape=(scatimg.shape[0] + objj_img.shape[0], scatimg.shape[1] + objj_img.shape[1], 4))
    start_0 = int((objjimg_pend.shape[0] / 2) + (-asample[2] / grain) * (scatimg.shape[0] / 2) - objj_img.shape[0] / 2)
    start_1 = int((objjimg_pend.shape[1] / 2) + (asample[0] / grain) * (scatimg.shape[1] / 2) - objj_img.shape[1] / 2)
    print(objj_img.shape)
    print(start_0, start_1)
    objjimg_pend[start_0:start_0 + objj_img.shape[0], start_1:start_1 + objj_img.shape[1], 0:3] = objj_img
    objjimg_pend[start_0:start_0 + objj_img.shape[0], start_1:start_1 + objj_img.shape[1], 3] = 0.5
    objjimg_pend = objjimg_pend[int((objj_img.shape[0] + 1) / 2): -int(objj_img.shape[0] / 2),
                   int((objj_img.shape[1] + 1) / 2): -int(objj_img.shape[1] / 2)]
    alphamask = objjimg_pend[:, :, 3]
    alphamask = alphamask[:, :, None]
    objiimg_pend = objiimg_pend * (1 - alphamask) + objjimg_pend * alphamask

    alphamask = scatimg[:, :, 3] / np.max(scatimg[:, :, 3])
    alphamask = alphamask[:, :, None]
    resulti = objiimg_pend[:, :, 0:3] * (1 - alphamask) + scatimg[:, :, 0:3] * alphamask
    resulti = cv2.resize(resulti, (int(resulti.shape[1] / 2), int(resulti.shape[0] / 2)))
    cv2.imwrite(
        './{}/blend/{}({})-{}({})_blend.png'.format(exid, obji, obj_semantic[obji], objj, obj_semantic[objj]),
        resulti)

with_arrow = False
save_fig = True
with_color = True

def semanticLevelRelations(cat1, cat2):
    for o1 in obj_semantic:
        for o2 in obj_semantic:
            if obj_semantic[o1] == cat1 and obj_semantic[o2] == cat2:
                try:
                    plot_orth(o1, o2, f'{cat1}-{cat2}')
                except Exception as e:
                    print(e)
                    continue

if __name__ == '__main__':
    plot_orth(sys.argv[1], sys.argv[2])
# semanticLevelRelations('coffee_table', 'sofa')
    
# plot_orth('551', '63', 'supplementary_2')
# plot_orth('77', '558', 'supplementary_2')
# plot_orth('403', 's__2452', 'supplementary_2', False)

# with open('F:/3DFurniture/sk_to_ali.json') as f:
#     alis = list(json.load(f).keys())
# # index = 658
# index = 4627
# for ali_i in alis[index:len(alis)]:
#     print(index)
#     index += 1
#     for ali_j in alis:
#         try:
#             plot_orth(ali_i, ali_j, 'vis')
#         except Exception as e:
#             print(e)
