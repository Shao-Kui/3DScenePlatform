import matplotlib
from random_poly import generate_polygon

matplotlib.use("agg")
import matplotlib.pyplot as plt
from math import *
from tqdm import tqdm
import networkx as nx
import random
from shapely.geometry import *
from shapely.affinity import *
from shapely.ops import *
from multiprocessing import Pool
from main import construct_graph
import os



PROCESS_COUNT = 10
GEN_NUM = 1000

AVG_RADIUS = 40
IRREGULARITY = 0.5
SPIKINESS = 0.2
NUM_VERTICES = 16
SPLIT = 25
GRID_LENGTH = 2
EPS = 1e-3


def div_ours(boundary, boundbox, idx):
    graph, regions = construct_graph(boundary)
    xl, yl, xh, yh = boundbox
    site_width, site_height = xh - xl, yh - yl
    fig, ax = plt.subplots(figsize=(10, site_height / site_width * 10), layout="tight")
    pos = nx.get_node_attributes(graph, "pos")
    # for node in graph.nodes:
    #     plt.scatter(
    #         pos[node][0],
    #         pos[node][1],
    #         c="black",
    #     )
    ax.set_xlim(xl - 1, xh + 1)
    ax.set_ylim(yl - 1, yh + 1)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    for edge in graph.edges:
        plt.plot([pos[edge[0]][0], pos[edge[1]][0]], [pos[edge[0]][1], pos[edge[1]][1]], c="black", linewidth = 5)
    plt.savefig("division/{}_ours.png".format(idx))
    plt.close()


def div_growth(boundary, boundbox, idx):
    gxl, gyl, gxh, gyh = boundbox
    site_width, site_height = gxh - gxl, gyh - gyl
    x_num = int((gxh - gxl + 2 * EPS) / GRID_LENGTH)
    y_num = int((gyh - gyl + 2 * EPS) / GRID_LENGTH)
    x_len, y_len = (gxh - gxl + 2 * EPS) / x_num, (gyh - gyl + 2 * EPS) / y_num
    grid = [[-2 for _ in range(y_num)] for _ in range(x_num)]
    site_poly = Polygon(boundary)
    for i in range(x_num):
        for j in range(y_num):
            x1, y1, x2, y2 = (
                gxl - EPS + i * x_len,
                gyl - EPS + j * y_len,
                gxl - EPS + (i + 1) * x_len,
                gyl - EPS + (j + 1) * y_len,
            )
            poly = Polygon([(x1, y1), (x1, y2), (x2, y2), (x2, y1)])
            if poly.intersects(site_poly):
                grid[i][j] = -1
    ### stage 1: rectangular growth
    recs = []
    for t in range(SPLIT):
        while True:
            x, y = random.randint(0, x_num - 1), random.randint(0, y_num - 1)
            if grid[x][y] == -1:
                recs.append((x, y, x, y))
                grid[x][y] = t
                break
    dead = [False for _ in range(SPLIT)]
    while True:
        all_dead = len([i for i in range(SPLIT) if not dead[i]]) == 0
        if all_dead:
            break
        while True:
            rand_idx = random.randint(0, SPLIT - 1)
            if not dead[rand_idx]:
                break
        xl, yl, xh, yh = recs[rand_idx]
        grow_dir_validity = [True for _ in range(4)]
        if xh == x_num - 1:
            grow_dir_validity[0] = False
        else:
            worth = False
            for i in range(yl, yh + 1):  # x+
                if grid[xh + 1][i] == -1:
                    worth = True
                if grid[xh + 1][i] >= 0:
                    grow_dir_validity[0] = False
                    break
            if not worth:
                grow_dir_validity[0] = False
        if xl == 0:
            grow_dir_validity[1] = False
        else:
            worth = False
            for i in range(yl, yh + 1):  # x-
                if grid[xl - 1][i] == -1:
                    worth = True
                if grid[xl - 1][i] >= 0:
                    grow_dir_validity[1] = False
                    break
            if not worth:
                grow_dir_validity[1] = False
        if yh == y_num - 1:
            grow_dir_validity[2] = False
        else:
            worth = False
            for i in range(xl, xh + 1):  # y+
                if grid[i][yh + 1] == -1:
                    worth = True
                if grid[i][yh + 1] >= 0:
                    grow_dir_validity[2] = False
                    break
            if not worth:
                grow_dir_validity[2] = False
        if yl == 0:
            grow_dir_validity[3] = False
        else:
            worth = False
            for i in range(xl, xh + 1):  # y-
                if grid[i][yl - 1] == -1:
                    worth = True
                if grid[i][yl - 1] >= 0:
                    grow_dir_validity[3] = False
                    break
            if not worth:
                grow_dir_validity[3] = False
        if not any(grow_dir_validity):
            dead[rand_idx] = True
            continue
        while True:
            grow_dir = random.randint(0, 3)
            if grow_dir_validity[grow_dir]:
                break
        if grow_dir == 0:
            recs[rand_idx] = (xl, yl, xh + 1, yh)
            for i in range(yl, yh + 1):
                if grid[xh + 1][i] == -1:
                    grid[xh + 1][i] = rand_idx
        elif grow_dir == 1:
            recs[rand_idx] = (xl - 1, yl, xh, yh)
            for i in range(yl, yh + 1):
                if grid[xl - 1][i] == -1:
                    grid[xl - 1][i] = rand_idx
        elif grow_dir == 2:
            recs[rand_idx] = (xl, yl, xh, yh + 1)
            for i in range(xl, xh + 1):
                if grid[i][yh + 1] == -1:
                    grid[i][yh + 1] = rand_idx
        else:
            recs[rand_idx] = (xl, yl - 1, xh, yh)
            for i in range(xl, xh + 1):
                if grid[i][yl - 1] == -1:
                    grid[i][yl - 1] = rand_idx

    ### stage 2: handle the rest area
    for i in range(x_num): 
        for j in range(y_num):
            if grid[i][j] != -1:
                continue
            # bfs
            q = [(i, j)]
            blocks = [(i, j)]
            grid[i][j] = SPLIT
            adj_types = set()
            while len(q) > 0:
                x, y = q.pop(0)
                for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                    nx, ny = x + dx, y + dy
                    if nx < 0 or nx >= x_num or ny < 0 or ny >= y_num:
                        continue
                    if grid[nx][ny] == -1:
                        grid[nx][ny] = SPLIT
                        q.append((nx, ny))
                        blocks.append((nx, ny))
                    elif grid[nx][ny] >= 0:
                        adj_types.add(grid[nx][ny])
            adj_types = adj_types - {SPLIT}
            rand_type = random.choice(list(adj_types))
            for x, y in blocks:
                grid[x][y] = rand_type

    ### stage 3: determine the actual borders
    lines = None
    for i in range(x_num):
        for j in range(y_num):
            if i + 1 < x_num and grid[i][j] != grid[i + 1][j] and grid[i][j] != -2 and grid[i + 1][j] != -2:
                line = LineString(
                    [
                        (gxl - EPS + (i + 1) * x_len, gyl - EPS + j * y_len),
                        (gxl - EPS + (i + 1) * x_len, gyl - EPS + (j + 1) * y_len),
                    ]
                )
                if lines is None:
                    lines = line
                else:
                    lines = lines.union(line)
            if j + 1 < y_num and grid[i][j] != grid[i][j + 1] and grid[i][j] != -2 and grid[i][j + 1] != -2:
                line = LineString(
                    [
                        (gxl - EPS + i * x_len, gyl - EPS + (j + 1) * y_len),
                        (gxl - EPS + (i + 1) * x_len, gyl - EPS + (j + 1) * y_len),
                    ]
                )
                if lines is None:
                    lines = line
                else:
                    lines = lines.union(line)
    lines = lines.intersection(site_poly)
    lines = [lines] if isinstance(lines, LineString) else list(lines.geoms)
    ### final: plot the lines

    fig, ax = plt.subplots(figsize=(10, site_height / site_width * 10), layout="tight")
    ax.set_xlim(gxl - 1, gxh + 1)
    ax.set_ylim(gyl - 1, gyh + 1)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_visible(False)

    for line in lines:
        plt.plot(*line.xy, c="black", linewidth = 5)
    # for i in range(x_num):
    #     for j in range(y_num):
    #         if grid[i][j] != -1 and grid[i][j] != -2:
    #             color = [0.4 * ((grid[i][j] + 1) % 3), 0.2 * ((grid[i][j] + 2) % 5), 0.15 * ((grid[i][j] + 3) % 7)]
    #             x1, y1, x2, y2 = gxl + i * x_len, gyl + j * y_len, gxl + (i + 1) * x_len, gyl + (j + 1) * y_len
    #             plt.fill([x1, x1, x2, x2], [y1, y2, y2, y1], color=color)
    plt.plot(*site_poly.exterior.xy, c="black", linewidth = 5)
    plt.savefig("division/{}_growth.png".format(idx))
    plt.close()


def gen_two(args):
    idx, seed = args
    random.seed(seed + idx)
    poly = generate_polygon((AVG_RADIUS, AVG_RADIUS), AVG_RADIUS, IRREGULARITY, SPIKINESS, NUM_VERTICES)
    xl, yl, xh, yh = 1e9, 1e9, -1e9, -1e9
    for x, y in poly:
        xl = min(xl, x)
        xh = max(xh, x)
        yl = min(yl, y)
        yh = max(yh, y)
    boundbox = (xl, yl, xh, yh)
    div_ours(poly, boundbox, idx)
    div_growth(poly, boundbox, idx)


def main(seed):
    if not os.path.exists("division"):
        os.mkdir("division")
    with Pool(PROCESS_COUNT) as p:
        _ = list(tqdm(p.imap(gen_two, [(i, seed) for i in range(GEN_NUM)]), total=GEN_NUM))
    # for i in tqdm(range(GEN_NUM)):
    #     gen_two((i, seed))

if __name__ == "__main__":
    main(29)
