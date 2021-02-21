import math
import numpy as np
import matplotlib.pyplot as plt
import os
import re
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient
import json

eps = 1e-1
check_norm = False
savepic = False
get_norm = False
savefile = False
savefile_kind = 'npy'

record_file_path = './record_file.json'
parallel = {}


class point:
    x = 0.
    y = 0.
    z = 0.

    def __init__(self, a, b, c):
        self.x = a
        self.y = b
        self.z = c

    def __len__(self):
        return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)

    def __str__(self):
        return '(' + str(self.x) + ',' + str(self.y) + ',' + str(self.z) + ')'

    def dis_to(self, p):
        return math.sqrt((self.x - p.x) ** 2 + (self.y - p.y) ** 2 + (self.z - p.z) ** 2)

    def __add__(self, other):
        return point(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        return point(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, other):
        return point(self.x * other.x, self.y * other.y, self.z * other.z)

    def __pow__(self, power, modulo=None):
        return point(self.x ** power, self.y ** power, self.z ** power)

    def __truediv__(self, other):
        return point(self.x / other, self.y / other, self.z / other)

    def dot_product(self, b):
        return self.x * b.x + self.y * b.y + self.z * b.z

    def cross_mul(self, b):
        return point(self.y * b.z - self.z * b.y, self.z * b.x - self.x * b.z, self.x * b.y - self.y * b.x)

    def rotate_theta(self, theta):
        return self.complex_product(self.unit(theta))

    def complex_product(self, b):
        return point(self.x * b.x - self.z * b.z, self.y, self.x * b.z + self.z * b.x)

    def normalize(self):
        return self / self.__len__()

    @staticmethod
    def unit(theta):
        return point(math.cos(theta), 0, math.sin(theta))

    def theta(self):
        if math.isclose(self.x, 0, abs_tol=eps):
            if math.isclose(self.z, 0, abs_tol=eps):
                return 0
            elif self.z > 0:
                return math.pi / 2
            elif self.z < 0:
                return math.pi * 3 / 2
        elif math.isclose(self.z, 0, abs_tol=eps):
            if self.x > 0:
                return 0
            elif self.x < 0:
                return math.pi
        else:
            t = math.atan(self.z / self.x)
            if self.x < 0:
                return t + math.pi
            else:
                if self.z < 0:
                    return t + 2 * math.pi
                else:
                    return t


class polygen:
    parr = []
    norm = []
    size = 0

    def __init__(self, p):
        self.size = p.shape[0]
        self.parr = []
        self.norm = []
        for i in range(0, self.size):
            self.parr.append(point(p[i][0], 0, p[i][1]))
        # print(p,self.size)

    def get_norm(self):
        theta = 0

        for i in range(0, self.size):

            v1 = self.parr[(i + 1) % self.size] - self.parr[i]
            v2 = self.parr[(i + 2) % self.size] - self.parr[(i + 1) % self.size]
            delta = (v2.rotate_theta(-v1.theta())).theta()
            if delta > math.pi:
                delta = delta - math.pi * 2

            theta += delta
        # print(theta)
        # 反转为逆时针序

        # for p in self.parr:
        #     print(str(p))
        # print("*")

        if theta < 0.0:
            self.parr.reverse()

        for i in range(0, self.size):
            self.norm.append(((self.parr[(i + 1) % self.size] - self.parr[i]).normalize()).rotate_theta(math.pi / 2.0))

        re = np.zeros((self.size, 4), dtype=np.float)

        for i in range(0, self.size):
            re[i][0] = self.parr[i].x
            re[i][1] = self.parr[i].z

            re[i][2] = self.norm[i].x
            re[i][3] = self.norm[i].z

        # print(re)
        return re


def process(path, file_name):
    ans = np.zeros(1)
    try:
        objfile = open(path + '/' + file_name)
        point_num = 0
        face_num = 0
        point_buf_arr = []
        face_buf_arr = []
        input_str = objfile.readline()
        while input_str != "":
            input_str = objfile.readline()
            if input_str[:2] == 'v ':
                point_num += 1
                for i in range(1, 4):
                    point_buf_arr.append(eval(input_str.split()[i]))
            elif input_str[:2] == 'f ':
                face_num += 1
                for i in range(1, 4):
                    face_buf_arr.append(int(eval(input_str.split()[i].split('/')[0])))

        if point_num == 0 or face_num == 0:
            return np.zeros(1)

        parr = np.array(point_buf_arr, dtype=np.float)
        parr = parr.reshape(point_num, 3)
        delta = parr.max(axis=0) - parr.min(axis=0)
        parr = np.delete(parr, np.where(delta == min(delta)), axis=1)

        farr = np.array(face_buf_arr, dtype=np.int64)
        farr = farr.reshape(face_num, 3) - np.ones((face_num, 3))
        # print(farr, face_num)

        # 相同点集合
        belong = np.arange(point_num)
        for i in range(1, point_num):
            for j in range(0, i):
                if math.sqrt(((parr[i] - parr[j]) ** 2).sum()) < 1e-1:
                    belong[i] = belong[j]
                    break
        # print(belong)

        # 计算当前点到新点的映射
        belong2nid = {}
        nid_point = []
        nid_cnt = 0
        for i in range(0, point_num):
            if belong2nid.get(belong[i], -1) == -1:
                belong2nid[belong[i]] = nid_cnt
                nid_cnt += 1
                nid_point.append([])
            nid_point[belong2nid[belong[i]]].append([parr[i][0], parr[i][1]])

        # print(belong2nid)

        # 计算点的平均值
        new_point = []
        for i in range(0, nid_cnt):
            nip = np.array(nid_point[i], dtype=np.float)
            nip = nip.sum(axis=0) / np.array([nip.shape[0], nip.shape[0]])
            new_point.append(point(nip[0], 0, nip[1]))

        # print(new_point)

        # 领接集合
        adj = []
        for i in range(0, nid_cnt):
            adj.append(set())

        for i in range(0, face_num):
            for j in range(0, 3):
                if belong[int(farr[i][j])] == belong[int(farr[i][(j + 1) % 3])]:
                    adj[belong2nid[belong[int(farr[i][j])]]].add(belong2nid[belong[int(farr[i][(j + 2) % 3])]])
                    adj[belong2nid[belong[int(farr[i][(j + 2) % 3])]]].add(belong2nid[belong[int(farr[i][j])]])

        # print(adj)

        # dfs生成轮廓
        vis = np.zeros(len(adj))
        ans_list = []

        def dfs(u):
            vis[u] = 1
            ans_list.append(u)

            for v in adj[u]:
                if vis[v] == 0:
                    dfs(v)

        dfs(0)

        # 去重
        temp = len(ans_list) * 2
        i = 0
        while i < temp:
            if math.isclose(
                    abs((new_point[ans_list[i % len(ans_list)]] - new_point[ans_list[(i + 1) % len(ans_list)]]).theta()
                        - (new_point[ans_list[i % len(ans_list)]] - new_point[
                        ans_list[(i - 1 + len(ans_list)) % len(ans_list)]]).theta()), math.pi, abs_tol=eps):
                ans_list.remove(ans_list[i % len(ans_list)])
                i -= 1
            i += 1

        # for p in ans_list:
        #     print(new_point[p].theta())
        # print(ans_list)

        # 生成答案
        ans = np.empty((len(ans_list), 2), dtype=np.float)
        for i in range(0, len(ans_list)):
            ans[i][0] = new_point[ans_list[i]].x
            ans[i][1] = new_point[ans_list[i]].z

        # 检测正对
        if check_norm:
            proper = 0
            for i in range(0, len(ans_list)):
                t = (new_point[ans_list[i]] - new_point[ans_list[(i + 1) % len(ans_list)]]).theta()

                if math.isclose(t, 0, abs_tol=eps) \
                        or math.isclose(t, math.pi / 2, abs_tol=eps) \
                        or math.isclose(t, math.pi, abs_tol=eps) \
                        or math.isclose(t, math.pi * 3 / 2, abs_tol=eps):
                    pass
                else:
                    proper += 1

            if proper == 0:
                room_name = re.match('(.*)/room/(.*)$', path).group(2)
                if parallel.get(room_name, -1) == -1:
                    parallel[room_name] = []
                parallel[room_name].append(file_name)

        if get_norm:
            p = polygen(ans)
            # print(ans)
            ans = p.get_norm()

    except Exception as e:
        print('!!!Wrong at ' + file_name + '\n' + str(e))
        print(ans)
        # plt.scatter(parr[:, 0], parr[:, 1], s=0.1)
        # plt.show()
        return ans
    finally:
        if savepic:
            plt.cla()
            plt.scatter(ans[:, 0], ans[:, 1], s=1)
            if get_norm:
                plt.scatter(ans[:, 0] + ans[:, 2], ans[:, 1] + ans[:, 3], s=2)
            for i in range(0, len(ans_list)):
                plt.annotate(i, (ans[i][0], ans[i][1]))
            plt.savefig(path + '/' + file_name + '.png')
        return ans


def processGeo(path, file_name):
    # print(file_name)
    ans = np.zeros(1)
    try:
        objfile = open(path + '/' + file_name)
        point_num = 0
        face_num = 0
        point_buf_arr = []
        face_buf_arr = []
        input_str = objfile.readline()
        while input_str != "":
            input_str = objfile.readline()
            if input_str[:2] == 'v ':
                point_num += 1
                for i in range(1, 4):
                    point_buf_arr.append(eval(input_str.split()[i]))
            elif input_str[:2] == 'f ':
                face_num += 1
                for i in range(1, 4):
                    face_buf_arr.append(int(eval(input_str.split()[i].split('/')[0])))

        if point_num == 0 or face_num == 0:
            return np.zeros(1)

        parr = np.array(point_buf_arr, dtype=np.float)
        parr = parr.reshape(point_num, 3)
        delta = parr.max(axis=0) - parr.min(axis=0)
        parr = np.delete(parr, np.where(delta == min(delta)), axis=1)

        farr = np.array(face_buf_arr, dtype=np.int)
        farr = farr.reshape(face_num, 3) - np.ones((face_num, 3))

        # print(parr, point_num)

        # print(farr, face_num)

        re = Polygon()
        for f in farr:
            points = [(parr[int(p)][0], parr[int(p)][1]) for p in f]
            poly = Polygon(points)

            # print(poly)
            # plt.plot(*poly.exterior.xy)
            # plt.show()
            if (poly.is_valid):
                re = re.union(poly)
            # print(re)
            # plt.plot(*re.exterior.xy)
            # plt.show()
            # input()

        # plt.cla()
        # plt.plot(*re.exterior.xy)
        # plt.show()
        # print(re)
        # print(re)
        # print( orient(re,1.0))
        re = orient(re,1.0)
        ans = np.array(re.exterior.xy).T
        ans = ans[:-1]


        if get_norm:
            p = polygen(ans)
            ans = p.get_norm()
        # print(ans)

    except Exception as e:
        print('!!!Wrong at ' + file_name + '\n' + str(e))
        print(ans)
        return ans

    finally:

        if savepic:
            plt.cla()
            plt.scatter(ans[:, 0], ans[:, 1], s=1)
            if get_norm:
                plt.scatter(ans[:, 0] + ans[:, 2], ans[:, 1] + ans[:, 3], s=2)
            plt.plot(*re.exterior.xy)
            for i in range(0, len(ans)):
                plt.annotate(i, (ans[i][0], ans[i][1]))
            plt.savefig(path + '/' + file_name + '.png')

        return ans


def file_search(path, parent='.'):
    files = os.listdir(path)  # 得到文件夹下的所有文件名称
    file_num = 0
    file_nump = 0
    dir_num = 0
    dir_nump = 0
    for file in files:
        if os.path.isfile(path + "/" + file):
            if re.match('.*f.obj$', str(file)):
                file_num += 1
        elif os.path.isdir(path + "/" + file):
            dir_num += 1
    for file in files:  # 遍历文件夹
        if os.path.isfile(path + "/" + file):
            if re.match('.*f.obj$', str(file)):
                file_nump += 1
                # print("Dealing with " + path + "/" + file + ' (%d/%d)' % (file_nump, file_num))
                ans = processGeo(path, file)

                try:
                    if savefile:
                        if savefile_kind == 'npy':
                            np.save(path + "/" + file, ans)
                        elif savefile_kind == 'json':
                            save = {}
                            save['house'] = parent
                            save['room'] = str(file)
                            save['vertices'] = ans[:, 0:2].tolist()
                            save['normals'] = ans[:, 2:4].tolist()
                            # print(save)
                            open('./shape_json/' + parent + '-' + str(file) + '.json', 'w').write(json.dumps(save))
                except Exception as e:
                    print('save file wrong!')


        elif os.path.isdir(path + "/" + file):
            dir_nump += 1
            print("Entering " + path + "/" + file + '(%d/%d)' % (dir_nump, dir_num))
            file_search(path + "/" + file, file)

def connected_component(name, adj):
    size = len(name)
    vis = np.zeros(size,dtype=np.bool)
    ans=[]

    def dfs(u):
        vis[u]=True
        ans[-1].append(name[u])
        for v in range(size):
            if vis[v]==False:
                if adj[u][v] == 1 or adj[v][u] == 1:
                    dfs(v)

    for u in range(size):
        if vis[u]==False:
            ans.append([])
            dfs(u)
    return ans

def connected_component_(name, adj):
    size = len(name)
    vis = np.zeros(size, dtype=np.bool)
    ans = []

    def dfs(u):
        vis[u] = True
        ans[-1].append(name[u])
        for v in range(size):
            if vis[v] == False and adj[u][v] == 1:
                dfs(v)

    for u in range(size):
        if vis[u] == False:
            ans.append([])
            dfs(u)
    return ans


# if __name__ == "__main__":
#
#     name = [78,266,108,335,120]
#     adj = [[0., 0., 0., 0., 0.],
#      [0., 0., 0., 0., 0.],
#      [0., 0., 0., 0., 1.],
#      [0., 0., 0., 0., 1.],
#      [0., 0., 1., 1., 0.]]
#     print(connected_component(name,adj))


class point:
    x = 0.
    y = 0.
    z = 0.

    def __init__(self, a, b, c):
        self.x = a
        self.y = b
        self.z = c

    def __len__(self):
        return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)

    def __str__(self):
        return '(' + str(self.x) + ',' + str(self.y) + ',' + str(self.z) + ')'

    def dis_to(self, p):
        return math.sqrt((self.x - p.x) ** 2 + (self.y - p.y) ** 2 + (self.z - p.z) ** 2)

    def __add__(self, other):
        return point(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        return point(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, other):
        return point(self.x * other.x, self.y * other.y, self.z * other.z)

    def __pow__(self, power, modulo=None):
        return point(self.x ** power, self.y ** power, self.z ** power)

    def __truediv__(self, other):
        return point(self.x / other, self.y / other, self.z / other)

    def dot_product(self, b):
        return self.x * b.x + self.y * b.y + self.z * b.z

    def cross_mul(self, b):
        return point(self.y * b.z - self.z * b.y, self.z * b.x - self.x * b.z, self.x * b.y - self.y * b.x)

    def rotate_theta(self, theta):
        return self.complex_product(self.unit(theta))

    def complex_product(self, b):
        return point(self.x * b.x - self.z * b.z, self.y, self.x * b.z + self.z * b.x)

    def normalize(self):
        return self / self.__len__()

    @staticmethod
    def unit(theta):
        return point(math.cos(theta), 0, math.sin(theta))

    peps = 1E-6

    def theta(self):
        if math.isclose(self.x, 0, abs_tol=self.peps):
            if math.isclose(self.z, 0, abs_tol=self.peps):
                return 0
            elif self.z > 0:
                return math.pi / 2
            elif self.z < 0:
                return math.pi * 3 / 2
        elif math.isclose(self.z, 0, abs_tol=self.peps):
            if self.x > 0:
                return 0
            elif self.x < 0:
                return math.pi
        else:
            t = math.atan(self.z / self.x)
            if self.x < 0:
                return t + math.pi
            else:
                if self.z < 0:
                    return t + 2 * math.pi
                else:
                    return t

    def thetaz(self):
        re = math.pi / 2 - self.theta()
        while re > math.pi:
            re -= math.pi * 2
        while re < -math.pi:
            re += math.pi * 2
        return re


class polygen:
    parr = []
    norm = []
    size = 0

    def __init__(self, p):
        self.size = p.shape[0]
        self.parr = []
        self.norm = []
        for i in range(0, self.size):
            self.parr.append(point(p[i][0], 0, p[i][1]))
        # print(p,self.size)

    def get_norm(self):
        theta = 0
        for i in range(0, self.size):

            v1 = self.parr[(i + 1) % self.size] - self.parr[i]
            v2 = self.parr[(i + 2) % self.size] - self.parr[(i + 1) % self.size]
            delta = (v2.rotate_theta(-v1.theta())).theta()
            if delta > math.pi:
                delta = delta - math.pi * 2

            theta += delta
        # print(theta)
        # 反转为逆时针序

        # for p in self.parr:
        #     print(str(p))
        # print("*")

        if theta < 0.0:
            self.parr.reverse()

        for i in range(0, self.size):
            self.norm.append(((self.parr[(i + 1) % self.size] - self.parr[i]).normalize()).rotate_theta(math.pi / 2.0))

        re = np.zeros((self.size, 4), dtype=np.float)

        for i in range(0, self.size):
            re[i][0] = self.parr[i].x
            re[i][1] = self.parr[i].z

            re[i][2] = self.norm[i].x
            re[i][3] = self.norm[i].z
        # print(re)
        return re

    def point_closest(self, p):

        if len(self.norm) == 0:
            self.get_norm()
        closest_distance = float('inf')
        idx = -1
        for i in range(0, len(self.norm)):
            temp = (p - self.parr[i]).dot_product(self.norm[i])
            if closest_distance > temp:
                idx = i
                closest_distance = temp

        return [closest_distance, idx]

def wall_distance_orient_weiyu():
    ROOT = './dataset/'
    level_root = "./dataset/alilevel/"
    room_root = "./dataset/room/"
    object_root = "./dataset/object/"
    with open('./dataset/sk_to_ali.json') as f:
        obj_semantic = json.load(f)

    # print('preparing the level_dirs ...')
    # level_dirs = []
    # for hid in os.listdir(level_root):
    #     for lid in os.listdir(level_root + "/{}".format(hid)):
    #         if os.path.exists(level_root + "/{}/{}".format(hid, lid)):
    #             level_dirs.append(level_root + "/{}/{}".format(hid, lid))
    level_dirs = os.listdir(level_root)

    ds = {}
    obj_convex = {}
    for obj in obj_semantic:
        ds[obj] = []
        obj_convex[obj] = np.load(object_root + '/' + obj + '/' + obj + '-convex.npy')

    for i in range(0, len(level_dirs)):
        dire = level_dirs[i]

        print('(%d/%d) tackle ' % (i + 1, len(level_dirs)) + dire)
        with open(f'./dataset/alilevel/{dire}', 'r') as f:
            h = json.load(f)

        for i in range(0, len(h['rooms'])):
            room = h['rooms'][i]
            # print(room['modelId'])

            # if os.path.exists(room_root + '/' + room['origin']+'/'+ room['modelId'] + 'f.npy'):
            #     shape = np.load(room_root + '/' + room['origin']+'/'+ room['modelId'] + 'f.npy')
            # else:
            #     if os.path.exists(room_root + '/' + room['origin']+'/'+ room['modelId'] + 'f.obj') is False:
            #         continue
            #     shape = processGeo(room_root + '/' + room['origin'], room['modelId'] + 'f.obj')
            #     np.save(room_root + '/' + room['origin']+'/'+ room['modelId'] + 'f.npy',shape)
            try:
                shape = processGeo(room_root + '/' + room['origin'], room['modelId'] + 'f.obj')
                shape = polygen(shape[:, 0:2])
                shape.get_norm()
            except Exception as e:
                continue
            # plt.cla()
            # plt.scatter(shape[:,0],shape[:,1])

            

            for i in range(len(room['objList'])):
                obji = room['objList'][i]

                if obji['modelId'] not in obj_semantic:
                    continue
                if 'translate' not in obji:
                    continue
                if 'orient' not in obji:
                    continue

                # vf = read_obj(object_root + '/' + obji['modelId'] + '/' + obji['modelId'] + '.obj')
                # temp = np.array(vf['vertices'])
                # temp = np.delete(temp,1,axis = 1)
                # print(obji)
                temp = obj_convex[obji['modelId']]
                theta = obji['orient']

                scale = [obji['scale'][0],obji['scale'][2]]
                temp = temp*scale
                # print(temp)
                varr = np.array([temp[:, 1] * np.sin(theta) + temp[:, 0] * np.cos(theta),
                                temp[:, 1] * np.cos(theta) - temp[:, 0] * np.sin(theta)])
                varr = varr.transpose()

                transpos = np.array([obji['translate'][0], obji['translate'][2]])
                varr = varr + transpos

                # plt.scatter(varr[:, 0], varr[:, 1])
                # print(varr)
                dis_idx = [float('inf'), -1]
                for v in varr:
                    temp = shape.point_closest(point(v[0], 0, v[1]))
                    if temp[0] < dis_idx[0]:
                        dis_idx = temp

                dnorm = shape.norm[dis_idx[1]]
                dnorm = point(dnorm.x, 0, dnorm.z)

                # ori = theta - dnorm.thetaz()
                # dis the wall
                ori = theta

                while ori > math.pi:
                    ori -= 2 * math.pi
                while ori < -math.pi:
                    ori += 2 * math.pi
                trandis = point(transpos[0], 0, transpos[1])
                trandis = (trandis - shape.parr[dis_idx[1]]).dot_product(shape.norm[dis_idx[1]])

                # print(dis_idx)
                # print(theta)
                # print(dnorm)
                # print(dnorm.theta())
                # print(dnorm.thetaz())
                # print([dis_idx[0], ori, trandis])
                ds[obji['modelId']].append([dis_idx[0], ori, trandis])
                # break
            # plt.show()
        # break
    wdotdirname = 'wdot-2'
    cnt=0
    for obji in ds:
        cnt+=1
        print('(%d/%d) saveing ' % (cnt, len(ds)) + obji)
        if os.path.exists(f'./latentspace/{wdotdirname}') is False:
            os.mkdir(f'./latentspace/{wdotdirname}')
        with open(f'./latentspace/{wdotdirname}/{obji}.json', 'w') as f:
            json.dump(ds[obji], f)

origin, xaxis, yaxis, zaxis = [0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]
def wall_distance_orient():
    import trimesh
    ROOT = './dataset/'
    level_root = "./dataset/alilevel_oriFix/"
    room_root = "./dataset/room/"
    object_root = "./dataset/object/"
    with open('./dataset/sk_to_ali.json') as f:
        obj_semantic = json.load(f)

    level_dirs = os.listdir(level_root)
    ds = {}
    objMeshCache = {}
    for obj in obj_semantic:
        ds[obj] = []
    for i in range(0, len(level_dirs)):
        dire = level_dirs[i]
        # debug mode...
        # if dire not in ['3c29e2e4-4b96-4124-91b6-00580ba3414d.json']:
        #     continue
        print('(%d/%d) tackle ' % (i + 1, len(level_dirs)) + dire)
        with open(f'./dataset/alilevel_oriFix/{dire}', 'r') as f:
            h = json.load(f)
        for i in range(0, len(h['rooms'])):
            room = h['rooms'][i]
            try:
                shape = processGeo(room_root + '/' + room['origin'], room['modelId'] + 'f.obj')
            except Exception as e:
                continue
            if len(shape) <= 2:
                continue
            for i in range(len(room['objList'])):
                obji = room['objList'][i]

                if obji['modelId'] not in obj_semantic:
                    continue
                if 'translate' not in obji:
                    continue
                if 'orient' not in obji:
                    continue

                # find the nearest wall; 
                p = np.array([obji['translate'][0], obji['translate'][2]])
                shapeEnd = shape[np.arange(1,len(shape)).tolist() + [0]]
                a_square = np.sum((shape - p)**2, axis=1)
                b_square = np.sum((shapeEnd - p)**2, axis=1)
                c_square = np.sum((shape - shapeEnd)**2, axis=1)
                area_double = 0.5 * np.sqrt(4 * a_square * b_square - (a_square + b_square - c_square)**2 )
                distances = area_double / np.sqrt(c_square)
                _indicesList = []
                wallMinIndices = np.argsort(distances)
                innerProducts = np.sum((shape - p) * (shape - shapeEnd), axis=1)
                for i in wallMinIndices:
                    if 0 <= innerProducts[i] and innerProducts[i] <= c_square[i]:
                        _indicesList.append(i)
                        if len(_indicesList) == 2:
                            break
                        # wallMinIndex = i
                if len(_indicesList) < 2:
                    continue
                wallMinIndex = _indicesList[0]
                minDistance = distances[wallMinIndex]
                secMinDistance = distances[_indicesList[1]]

                # calculate the wall orient; 
                wn = (shape[wallMinIndex] - shapeEnd[wallMinIndex])[[1,0]]
                wn[1] = -wn[1]

                # ori_prior equals to ori_final - ori_wall; 
                ori = obji['orient'] - np.arctan2(wn[0], wn[1])
                while ori > math.pi:
                    ori -= 2 * math.pi
                while ori < -(math.pi):
                    ori += 2 * math.pi

                # calculate the length of this object w.r.t the wall; 
                # wd = shapeEnd[wallMinIndex] - shape[wallMinIndex]
                # wallorient = np.arctan2(wd[0], wd[1])
                Ry = trimesh.transformations.rotation_matrix(-np.arctan2(wn[0], wn[1]), yaxis)
                try:
                    if obji['modelId'] in objMeshCache:
                        _mesh = objMeshCache[obji['modelId']]
                    else:
                        print('loading ... ' + obji['modelId'])
                        _mesh = trimesh.load(f'./dataset/object/{obji["modelId"]}/{obji["modelId"]}.obj')
                        objMeshCache[obji['modelId']] = _mesh
                    # we always take the copy before modifying it; 
                    mesh = _mesh.copy()
                    mesh.vertices *= np.array(obji['scale'])
                    mesh.apply_transform(Ry)
                    objWallLength = np.max(mesh.vertices[:, 0]) - np.min(mesh.vertices[:, 0])
                    objWallLength = objWallLength.tolist() / 2 
                except Exception as e:
                    print(e)
                    objWallLength = 0

                # ds[obji['modelId']].append([-1, ori, minDistance, 
                # f'{h["origin"]} - {room["roomId"]}', 
                # obji['orient'], np.arctan2(wn[0], wn[1]), 
                # int(wallMinIndex), shape[wallMinIndex][0], shape[wallMinIndex][1], secMinDistance])

                ds[obji['modelId']].append([-1, ori, minDistance] + obji['scale'] + [objWallLength, secMinDistance])
    wdotdirname = 'wdot-4'
    cnt=0
    for obji in ds:
        if len(ds[obji]) == 0:
            continue
        print('(%d/%d) saving ' % (cnt, len(ds)) + obji)
        if os.path.exists(f'./latentspace/{wdotdirname}') is False:
            os.mkdir(f'./latentspace/{wdotdirname}')
        with open(f'./latentspace/{wdotdirname}/{obji}.json', 'w') as f:
            json.dump(ds[obji], f)
        cnt+=1

with open('./dataset/objCatListAliv2.json') as f:
    objCatList = json.load(f)
with open('./dataset/objListCataAliv2.json') as f:
    objListCat = json.load(f)
# with open('./latentspace/roomTypeDemo.json') as f:
#     roomTypeDemo = json.load(f)
# # with open('./latentspace/pos-orient-4/categoryRelation-origin.json') as f:
# #     _categoryRelation = json.load(f)
# #     categoryRelation = {}
# #     for catdom in _categoryRelation:
# #         if catdom not in categoryRelation:
# #             categoryRelation[catdom] = {}
# #         categoryRelation[catdom]['_mageAddWall'] = []
# #         for sec in _categoryRelation[catdom]:
# #             categoryRelation[catdom][sec['name']] = sec
# with open('./latentspace/pos-orient-4/categoryRelation.json') as f:
#     categoryRelation = json.load(f)
# with open('./latentspace/pos-orient-4/wallRelation.json') as f:
#     wallRelation = json.load(f)
# categoryCodec = {}
# _codexid = 0
# for cat in wallRelation:
#     categoryCodec[cat] = _codexid
#     _codexid += 1
def getobjCat(modelId):
    if modelId in objCatList:
        return objCatList[modelId][0]
    else:
        return "Unknown Category"


if __name__ == "__main__":
    # savefile = True
    # savefile_kind = 'npy'

    # check_norm = False
    # savepic = True
    # get_norm = True
    # file_search('/Users/ervinxie/Research/Fast3DISS/00a4ff0c-ec69-4202-9420-cc8536ffffe0')

    # wall_distance_orient()
    p = Polygon(processGeo('./dataset/room/3a3fea81-7302-4de5-8249-1958954fe769', 'MasterBedroom-6118f.obj'))
    # print(Polygon(processGeo('./dataset/room/3a3fea81-7302-4de5-8249-1958954fe769', 'MasterBedroom-6118f.obj')))
    print(p.area)
    # file_search('/Users/ervinxie/Desktop/suncg/room/3e60029ce929bf20fd66204028a72c1b')
    # process('.', 'fr_0rm_0f.obj')

    # process('D:/3DIndoorScenePlatform/suncg/room/0a213b456bb8ad4d45c0c80f2c3f6b5d', 'fr_0rm_5f.obj')
    # process('.', 'suncg_subset/room/000d0395709d2a16e195c6f0189155c4/fr_0rm_2f.obj')

    # file_search('./suncg_subset/room')

    # if check_norm:
    #     open(record_file_path, 'w').write(json.dumps(parallel, indent=1))

    # if check_norm:
    #     open(record_file_path, 'w').write(json.dumps(parallel, indent=1))
