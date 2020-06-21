import math
import numpy as np
import matplotlib.pyplot as plt
import os
import re
import json

eps = 1e-1

check_norm = False
savepic = False
savefile = False
get_norm = True

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
        return point(self.x * b.x - self.z * b.z, 0, self.x * b.z + self.z * b.x)

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
            ans = p.get_norm()
    except Exception as e:

        print('!!!Wrong at ' + file_name + '\n' + str(e))
        # print(ans)
        # plt.scatter(parr[:, 0], parr[:, 1], s=0.1)
        # plt.show()
        if savepic:
            plt.cla()
            plt.scatter(ans[:, 0], ans[:, 1], s=1)
            for i in range(0, len(ans_list)):
                plt.annotate(i, (ans[i][0], ans[i][1]))
            plt.savefig(path + '/' + file_name + '.png')
        return np.zeros(1)
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


def file_search(path):
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
                ans = process(path, file)
                if savefile:
                    np.save(path + "/" + file, ans)
        elif os.path.isdir(path + "/" + file):
            dir_nump += 1
            print("Entering " + path + "/" + file + '(%d/%d)' % (dir_nump, dir_num))
            file_search(path + "/" + file)

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

if __name__ == "__main__":

    savefile = True
    savepic = True
    get_norm = True
    file_search('./suncg/room')
    process('.', 'fr_0rm_0f.obj')

    process('.', 'suncg_subset/room/000d0395709d2a16e195c6f0189155c4/fr_0rm_3f.obj')
    process('.', 'suncg_subset/room/000d0395709d2a16e195c6f0189155c4/fr_0rm_2f.obj')

    file_search('./suncg_subset/room')


    if check_norm:
        open(record_file_path, 'w').write(json.dumps(parallel, indent=1))

# /Users/ervinxie/Desktop/innerdesign/suncg_subset/room/000d0395709d2a16e195c6f0189155c4/fr_0rm_3f.obj.png
