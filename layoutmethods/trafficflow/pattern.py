from functools import cmp_to_key
import matplotlib.pyplot as plt
from shapely.geometry import *
from shapely.affinity import *
from shapely.ops import *
from math import *
import numpy as np
import random
from copy import deepcopy
from tqdm import tqdm
import os
import networkx as nx
import sys
from params import *
from numba import jit
from multiprocessing import Process, Manager
from time import sleep, time


class Node:
    def __init__(self, x: float, y: float, number: int):
        self.x = x
        self.y = y
        self.number = number
        self.row = -1
        self.column = -1
        self.incline1 = -1
        self.incline2 = -1


class SpaceColumn:
    def __init__(self, x: float, ymin: float, ymax: float, towards: int):
        self.x = x
        self.ymin = ymin
        self.ymax = ymax
        self.towards = towards


class SpaceRow:
    def __init__(self, y: float, xmin: float, xmax: float, towards: int):
        self.y = y
        self.xmin = xmin
        self.xmax = xmax
        self.towards = towards


class Column:
    def __init__(self, vector: list, x: float, ymin: float, ymax: float, number: int):
        self.vector = vector
        self.x = x
        self.ymin = ymin
        self.ymax = ymax
        self.number = number


class Row:
    def __init__(self, vector: list, y: float, xmin: float, xmax: float, number: int):
        self.vector = vector
        self.y = y
        self.xmin = xmin
        self.xmax = xmax
        self.number = number


class Incline:
    def __init__(self, vector: list, number: int):
        self.vector = vector
        self.number = number


def colCmp(col1: Column, col2: Column):
    if col1.x < col2.x:
        return -1
    elif col1.x > col2.x:
        return 1
    return 0


def colNumberCmp(col1: Column, col2: Column):
    if col1.number < col2.number:
        return -1
    elif col1.number > col2.number:
        return 1
    return 0


def rowCmp(row1: Row, row2: Row):
    if row1.y < row2.y:
        return -1
    elif row1.y > row2.y:
        return 1
    return 0


def rowNumberCmp(row1: Row, row2: Row):
    if row1.number < row2.number:
        return -1
    elif row1.number > row2.number:
        return 1
    return 0


class Shelf:
    """a shelf"""
    def __init__(self, group: int, x: float, y: float, xl: float, yl: float, towards: int, rotate=0.0):
        self.x = x
        self.y = y
        self.xl = xl
        self.yl = yl
        self.towards = towards
        self.rotate = rotate
        self.type = -1
        self.group = group
        self.model = None

    def visualize(self, patternType=-1):
        fillColor = None
        if patternType == -1:
            patternType = self.type
        if patternType == LINE:
            fillColor = LINE_SHELF_COLOR
        elif patternType == WEB:
            fillColor = WEB_SHELF_COLOR
        elif patternType == STAR:
            fillColor = STAR_SHELF_COLOR
        elif patternType == GRID:
            fillColor = GRID_SHELF_COLOR
        elif patternType == ROUND:
            fillColor = ROUND_SHELF_COLOR

        if self.towards != ROTATE:
            plt.fill([self.x - self.xl / 2, self.x + self.xl / 2, self.x + self.xl / 2, self.x - self.xl / 2],
                     [self.y - self.yl / 2, self.y - self.yl / 2, self.y + self.yl / 2, self.y + self.yl / 2],
                     color=fillColor)

            draw_border = [0, 1, 2, 3]
            draw_border.remove(self.towards)
            for index in draw_border:
                if index == X_POS:
                    plt.plot([self.x + self.xl / 2, self.x + self.xl / 2], [self.y - self.yl / 2, self.y + self.yl / 2],
                             color=(0, 0, 0))
                elif index == Y_POS:
                    plt.plot([self.x - self.xl / 2, self.x + self.xl / 2], [self.y + self.yl / 2, self.y + self.yl / 2],
                             color=(0, 0, 0))
                elif index == X_NEG:
                    plt.plot([self.x - self.xl / 2, self.x - self.xl / 2], [self.y - self.yl / 2, self.y + self.yl / 2],
                             color=(0, 0, 0))
                else:
                    plt.plot([self.x - self.xl / 2, self.x + self.xl / 2], [self.y - self.yl / 2, self.y - self.yl / 2],
                             color=(0, 0, 0))
        else:
            points = []
            center = np.array([self.x, self.y])
            points.append(center + vec(self.yl / 2, self.rotate + pi) + vec(self.xl / 2, self.rotate - pi / 2))
            points.append(center + vec(self.yl / 2, self.rotate) + vec(self.xl / 2, self.rotate - pi / 2))
            points.append(center + vec(self.yl / 2, self.rotate) + vec(self.xl / 2, self.rotate + pi / 2))
            points.append(center + vec(self.yl / 2, self.rotate + pi) + vec(self.xl / 2, self.rotate + pi / 2))
            plt.fill([points[i][0] for i in range(len(points))], [points[i][1] for i in range(len(points))],
                     color=fillColor)

            plt.plot([points[0][0], points[1][0]], [points[0][1], points[1][1]], color=(0, 0, 0))
            plt.plot([points[0][0], points[3][0]], [points[0][1], points[3][1]], color=(0, 0, 0))
            plt.plot([points[2][0], points[3][0]], [points[2][1], points[3][1]], color=(0, 0, 0))


class TwoDimSpace:
    """the space with an entrance and an exit"""
    def __init__(self, pointList: list, entrancePoint: np.ndarray, exitPoint: np.ndarray, entranceNorm: np.ndarray,
                 exitNorm: np.ndarray):
        self.pointList = pointList
        self.entrancePoint = entrancePoint
        self.exitPoint = exitPoint
        self.entranceNorm = entranceNorm
        self.exitNorm = exitNorm
        self.boundary = LinearRing(pointList)
        self.boundbox = Polygon([point for point in pointList])
        self.columns = []
        self.rows = []
        entrance = Point(entrancePoint)
        exit = Point(exitPoint)
        for i in range(len(pointList)):
            p1 = Point(pointList[i])
            p2 = Point(pointList[(i + 1) % len(pointList)])
            if abs(p1.x - p2.x) < EPS:  # column
                ymin = min(p1.y, p2.y)
                ymax = max(p1.y, p2.y)
                towards = X_POS if p1.y > p2.y else X_NEG
                if abs(p1.x - entrance.x) < EPS:
                    if entrance.y - ROAD_WIDTH * 0.75 > ymin:
                        self.columns.append(SpaceColumn(p1.x, ymin, entrance.y - ROAD_WIDTH * 0.75, towards))
                    if entrance.y + ROAD_WIDTH * 0.75 < ymax:
                        self.columns.append(SpaceColumn(p1.x, entrance.y + ROAD_WIDTH * 0.75, ymax, towards))
                elif abs(p1.x - exit.x) < EPS:
                    if exit.y - ROAD_WIDTH * 0.75 > ymin:
                        self.columns.append(SpaceColumn(p1.x, ymin, exit.y - ROAD_WIDTH * 0.75, towards))
                    if exit.y + ROAD_WIDTH * 0.75 < ymax:
                        self.columns.append(SpaceColumn(p1.x, exit.y + ROAD_WIDTH * 0.75, ymax, towards))
                else:
                    self.columns.append(SpaceColumn(p1.x, ymin, ymax, towards))
            elif abs(p1.y - p2.y) < EPS:  # row
                xmin = min(p1.x, p2.x)
                xmax = max(p1.x, p2.x)
                towards = Y_POS if p1.x < p2.x else Y_NEG
                if abs(p1.y - entrance.y) < EPS:
                    if entrance.x - ROAD_WIDTH * 0.75 > xmin:
                        self.rows.append(SpaceRow(p1.y, xmin, entrance.x - ROAD_WIDTH * 0.75, towards))
                    if entrance.x + ROAD_WIDTH * 0.75 < xmax:
                        self.rows.append(SpaceRow(p1.y, entrance.x + ROAD_WIDTH * 0.75, xmax, towards))
                elif abs(p1.y - exit.y) < EPS:
                    if exit.x - ROAD_WIDTH * 0.75 > xmin:
                        self.rows.append(SpaceRow(p1.y, xmin, exit.x - ROAD_WIDTH * 0.75, towards))
                    if exit.x + ROAD_WIDTH * 0.75 < xmax:
                        self.rows.append(SpaceRow(p1.y, exit.x + ROAD_WIDTH * 0.75, xmax, towards))
                else:
                    self.rows.append(SpaceRow(p1.y, xmin, xmax, towards))

    def area(self):
        """return the area of the space"""
        return self.boundbox.area

    def visualize(self):
        """visualize the space"""
        plt.plot([point[0] for point in self.boundary.coords], [point[1] for point in self.boundary.coords],
                 color=(0, 0, 0),
                 linewidth=4)
        pointW = 0.5
        plt.fill([
            self.entrancePoint[0] - pointW, self.entrancePoint[0] + pointW, self.entrancePoint[0] + pointW,
            self.entrancePoint[0] - pointW
        ], [
            self.entrancePoint[1] - pointW, self.entrancePoint[1] - pointW, self.entrancePoint[1] + pointW,
            self.entrancePoint[1] + pointW
        ],
                 color=(0, 1, 0))
        plt.fill([
            self.exitPoint[0] - pointW, self.exitPoint[0] + pointW, self.exitPoint[0] + pointW,
            self.exitPoint[0] - pointW
        ], [
            self.exitPoint[1] - pointW, self.exitPoint[1] - pointW, self.exitPoint[1] + pointW,
            self.exitPoint[1] + pointW
        ],
                 color=(1, 0, 0))
        plt.plot(self.entrancePoint[0], self.entrancePoint[1], 'o', color=(0, 0, 0), markersize=15)
        plt.plot(self.exitPoint[0], self.exitPoint[1], 'o', color=(0, 0, 0), markersize=15)

    def checkConnection(self, net: list, patternList: list):
        """check if the net is connected"""
        if len(patternList) < 6:
            return True

        return nx.is_connected(net[0])


class Pattern:
    """base class for all patterns"""
    def __init__(self, centerPoint: np.ndarray, type: int, boundbox):
        self.centerPoint = centerPoint
        self.type = type
        self.boundbox = boundbox
        self.adjustmentCost = 0
        self.shelfs = []

    def name(self):
        """return the name of this pattern"""
        return self.__class__.__name__

    def area(self):
        """return the used area of this pattern"""
        ret = 0
        for shelf in self.shelfs:
            ret += shelf.xl * shelf.yl
        return ret

    def getBoundbox(self):
        """return the boundbox of this pattern"""
        pass

    def visualize(self):
        """visualize this pattern"""
        pass

    def update(self):
        """call this after modify this pattern"""
        self.boundbox = self.getBoundbox()
        self.adjust()

    # def checkConnection(self, other):
    #     """check if this pattern and another pattern are connected"""
    #     return True

    def randomChange(self, space: TwoDimSpace):
        """randomly change itself to another pattern"""
        return self

    def adjust(self):
        """automatically adjust some inner params,
        and update adjustmentCost due to the feasibility of this pattern"""
        pass

    def acceptable(self):
        """check if the pattern itself is reasonable"""
        return self.adjustmentCost < 10


class LinePattern(Pattern):
    """a line-shaped space"""
    def __init__(self, centerPoint: np.ndarray, length: float, orient: int):
        Pattern.__init__(self, centerPoint, LINE, None)
        self.length = length
        self.orient = orient
        self.boundbox = self.getBoundbox()

    def getBoundbox(self):
        return Polygon([
            self.centerPoint - vec(self.length / 2 + ROAD_WIDTH / 2, self.orient * pi / 2) +
            vec(SHELF_MAX_WIDTH * 2 + ROAD_WIDTH, pi / 2 + self.orient * pi / 2),
            self.centerPoint + vec(self.length / 2 + ROAD_WIDTH / 2, self.orient * pi / 2) +
            vec(SHELF_MAX_WIDTH * 2 + ROAD_WIDTH, pi / 2 + self.orient * pi / 2),
            self.centerPoint + vec(self.length / 2 + ROAD_WIDTH / 2, self.orient * pi / 2) -
            vec(SHELF_MAX_WIDTH * 2 + ROAD_WIDTH, pi / 2 + self.orient * pi / 2),
            self.centerPoint - vec(self.length / 2 + ROAD_WIDTH / 2, self.orient * pi / 2) -
            vec(SHELF_MAX_WIDTH * 2 + ROAD_WIDTH, pi / 2 + self.orient * pi / 2),
        ])

    def visualize(self):
        plt.fill([point[0] for point in self.boundbox.exterior.coords],
                 [point[1] for point in self.boundbox.exterior.coords],
                 color=BUFFER_COLOR)
        if self.orient == 0:
            plt.fill([
                self.centerPoint[0] - self.length / 2, self.centerPoint[0] + self.length / 2,
                self.centerPoint[0] + self.length / 2, self.centerPoint[0] - self.length / 2
            ], [
                self.centerPoint[1] - ROAD_WIDTH / 2, self.centerPoint[1] - ROAD_WIDTH / 2,
                self.centerPoint[1] + ROAD_WIDTH / 2, self.centerPoint[1] + ROAD_WIDTH / 2
            ],
                     color=ROAD_COLOR)
        else:
            plt.fill([
                self.centerPoint[0] - ROAD_WIDTH / 2, self.centerPoint[0] + ROAD_WIDTH / 2,
                self.centerPoint[0] + ROAD_WIDTH / 2, self.centerPoint[0] - ROAD_WIDTH / 2
            ], [
                self.centerPoint[1] - self.length / 2, self.centerPoint[1] - self.length / 2,
                self.centerPoint[1] + self.length / 2, self.centerPoint[1] + self.length / 2
            ],
                     color=ROAD_COLOR)
        for shelf in self.shelfs:
            shelf.visualize(self.type)

    def randomChange(self, space: TwoDimSpace):
        patternChoice = random.randint(0, 2)
        if patternChoice == 0:  # change to grid pattern
            if self.orient == 0:
                return GridPattern(self.centerPoint, self.length, ROAD_WIDTH + SHELF_MIN_WIDTH * 4 + EPS, 0)
            else:
                return GridPattern(self.centerPoint, ROAD_WIDTH + SHELF_MIN_WIDTH * 4 + EPS, self.length, 1)
        elif patternChoice == 1:  # change to round pattern
            if self.orient == 0:
                return RoundPattern(self.centerPoint, max(self.length, SHELF_MIN_LENGTH + SHELF_MAX_WIDTH * 2 + EPS),
                                    ROAD_WIDTH + SHELF_MAX_WIDTH * 4 + EPS)
            else:
                return RoundPattern(self.centerPoint, ROAD_WIDTH + SHELF_MAX_WIDTH * 4 + EPS,
                                    max(self.length, SHELF_MIN_LENGTH + SHELF_MAX_WIDTH * 2 + EPS))
        else:  # change to empty pattern
            if self.orient == 0:
                return EmptyPattern(self.centerPoint, self.length, ROAD_WIDTH + SHELF_MAX_WIDTH * 4 + EPS)
            else:
                return EmptyPattern(self.centerPoint, ROAD_WIDTH + SHELF_MAX_WIDTH * 4 + EPS, self.length)

    def adjust(self):
        self.adjustmentCost = 0
        if self.length < ROAD_WIDTH * 2:
            self.adjustmentCost = 100
            return
        if self.length > 8:
            self.adjustmentCost = (self.length - 8) * 0.25
        self.shelfs = []
        group = [0]
        if self.orient == 0:
            self.shelfs += linearShelfLayout(group, 0, self.centerPoint[0] - self.length / 2,
                                             self.centerPoint[1] - SHELF_MAX_WIDTH / 2 - ROAD_WIDTH / 2, self.length,
                                             SHELF_MAX_WIDTH, Y_POS)
            self.shelfs += linearShelfLayout(group, 0, self.centerPoint[0] - self.length / 2,
                                             self.centerPoint[1] - SHELF_MAX_WIDTH * 3 / 2 - ROAD_WIDTH / 2,
                                             self.length, SHELF_MAX_WIDTH, Y_NEG)
            self.shelfs += linearShelfLayout(group, 0, self.centerPoint[0] - self.length / 2,
                                             self.centerPoint[1] + SHELF_MAX_WIDTH / 2 + ROAD_WIDTH / 2, self.length,
                                             SHELF_MAX_WIDTH, Y_NEG)
            self.shelfs += linearShelfLayout(group, 0, self.centerPoint[0] - self.length / 2,
                                             self.centerPoint[1] + SHELF_MAX_WIDTH * 3 / 2 + ROAD_WIDTH / 2,
                                             self.length, SHELF_MAX_WIDTH, Y_POS)
        else:
            self.shelfs += linearShelfLayout(group, 1, self.centerPoint[0] - SHELF_MAX_WIDTH / 2 - ROAD_WIDTH / 2,
                                             self.centerPoint[1] - self.length / 2, self.length, SHELF_MAX_WIDTH, X_POS)
            self.shelfs += linearShelfLayout(group, 1, self.centerPoint[0] - SHELF_MAX_WIDTH * 3 / 2 - ROAD_WIDTH / 2,
                                             self.centerPoint[1] - self.length / 2, self.length, SHELF_MAX_WIDTH, X_NEG)
            self.shelfs += linearShelfLayout(group, 1, self.centerPoint[0] + SHELF_MAX_WIDTH / 2 + ROAD_WIDTH / 2,
                                             self.centerPoint[1] - self.length / 2, self.length, SHELF_MAX_WIDTH, X_NEG)
            self.shelfs += linearShelfLayout(group, 1, self.centerPoint[0] + SHELF_MAX_WIDTH * 3 / 2 + ROAD_WIDTH / 2,
                                             self.centerPoint[1] - self.length / 2, self.length, SHELF_MAX_WIDTH, X_POS)
        for i in range(len(self.shelfs)):
            self.shelfs[i].type = self.type


class GridPattern(Pattern):
    """a grid-shaped space"""
    def __init__(self, centerPoint: np.ndarray, width: float, height: float, orient: int):
        Pattern.__init__(self, centerPoint, GRID, None)
        self.width = width
        self.height = height
        self.xroads = []
        self.yroads = []
        self.orient = orient
        self.boundbox = self.getBoundbox()

    def getBoundbox(self):
        return Polygon([
            self.centerPoint - vec(self.width / 2 + ROAD_WIDTH / 2, 0) - vec(self.height / 2 + ROAD_WIDTH / 2, pi / 2),
            self.centerPoint + vec(self.width / 2 + ROAD_WIDTH / 2, 0) - vec(self.height / 2 + ROAD_WIDTH / 2, pi / 2),
            self.centerPoint + vec(self.width / 2 + ROAD_WIDTH / 2, 0) + vec(self.height / 2 + ROAD_WIDTH / 2, pi / 2),
            self.centerPoint - vec(self.width / 2 + ROAD_WIDTH / 2, 0) + vec(self.height / 2 + ROAD_WIDTH / 2, pi / 2),
        ])

    def visualize(self):
        plt.fill([point[0] for point in self.boundbox.exterior.coords],
                 [point[1] for point in self.boundbox.exterior.coords],
                 color=BUFFER_COLOR)
        for i in range(1, len(self.xroads) - 1):
            xr = self.xroads[i]
            plt.fill([xr - ROAD_WIDTH / 2, xr + ROAD_WIDTH / 2, xr + ROAD_WIDTH / 2, xr - ROAD_WIDTH / 2], [
                self.centerPoint[1] - self.height / 2, self.centerPoint[1] - self.height / 2,
                self.centerPoint[1] + self.height / 2, self.centerPoint[1] + self.height / 2
            ],
                     color=ROAD_COLOR)
        for i in range(1, len(self.yroads) - 1):
            yr = self.yroads[i]
            plt.fill([
                self.centerPoint[0] - self.width / 2, self.centerPoint[0] + self.width / 2,
                self.centerPoint[0] + self.width / 2, self.centerPoint[0] - self.width / 2
            ], [yr - ROAD_WIDTH / 2, yr - ROAD_WIDTH / 2, yr + ROAD_WIDTH / 2, yr + ROAD_WIDTH / 2],
                     color=ROAD_COLOR)
        for shelf in self.shelfs:
            shelf.visualize(self.type)

    def randomChange(self, space: TwoDimSpace):
        patternChoice = random.randint(0, 4)
        if patternChoice == 0:  # change to line pattern
            if self.orient == 0:
                return LinePattern(self.centerPoint, self.width, 0)
            else:
                return LinePattern(self.centerPoint, self.height, 1)
        elif patternChoice == 1:  # change to web pattern
            return WebPattern(self.centerPoint, 4, min(self.width / sqrt(2), self.height / sqrt(2)), pi / 4)
        elif patternChoice == 2:  # change to star pattern
            return StarPattern(self.centerPoint, 4, min(self.width / 2, self.height / 2), 0)
        elif patternChoice == 3:  # change to round pattern
            return RoundPattern(self.centerPoint, max(self.width, SHELF_MIN_LENGTH + SHELF_MAX_WIDTH * 2 + EPS),
                                max(self.height, SHELF_MIN_LENGTH + SHELF_MAX_WIDTH * 2 + EPS))
        else:  # change to empty pattern
            return EmptyPattern(self.centerPoint, self.width, self.height)

    def adjust(self):
        self.adjustmentCost = 0
        self.shelfs = []
        self.xroads = []
        self.yroads = []
        xcenters = []
        ycenters = []
        xbase = self.centerPoint[0] - self.width / 2
        ybase = self.centerPoint[1] - self.height / 2
        if self.orient == 0:
            if self.width < SHELF_MIN_LENGTH or self.height < ROAD_WIDTH + SHELF_MIN_WIDTH * 4:
                self.adjustmentCost = 100
                return
            hnum = (int)((self.height - SHELF_MIN_WIDTH * 2) / (SHELF_MIN_WIDTH * 2 + ROAD_WIDTH))
            height = 0
            minHnum = (int)((self.height - SHELF_MAX_WIDTH * 2) / (SHELF_MAX_WIDTH * 2 + ROAD_WIDTH))
            if hnum == minHnum:
                height = SHELF_MAX_WIDTH
            else:
                height = min(SHELF_MAX_WIDTH, (self.height - hnum * ROAD_WIDTH) / 2 / (hnum + 1))
            buf = (self.height - height * 2 * (hnum + 1)) / hnum
            self.yroads.append(ybase - ROAD_WIDTH / 2)
            for i in range(hnum + 1):
                ycenters.append(ybase + (height * 2 + buf) * i + height)
                if i != hnum:
                    self.yroads.append(ybase + (height * 2 + buf) * i + height * 2 + buf / 2)
            self.yroads.append(ybase + self.height + ROAD_WIDTH / 2)

            res = linearGridShelfLayout(0, xbase, 0, self.width, 4)
            xcenters = res[0]
            self.xroads.append(xbase - ROAD_WIDTH / 2)
            self.xroads += res[1]
            self.xroads.append(xbase + self.width + ROAD_WIDTH / 2)
            width = res[2]

            for i in range(len(xcenters)):
                for j in range(len(ycenters)):
                    xc = xcenters[i]
                    yc = ycenters[j]
                    self.shelfs.append(Shelf(j, xc, yc - height / 2, width, height, Y_NEG))
                    self.shelfs.append(Shelf(j, xc, yc + height / 2, width, height, Y_POS))
        else:
            if self.height < SHELF_MIN_LENGTH or self.width < ROAD_WIDTH + SHELF_MIN_WIDTH * 4:
                self.adjustmentCost = 100
                return
            wnum = (int)((self.width - SHELF_MIN_WIDTH * 2) / (SHELF_MIN_WIDTH * 2 + ROAD_WIDTH))
            width = 0
            minWnum = (int)((self.width - SHELF_MAX_WIDTH * 2) / (SHELF_MAX_WIDTH * 2 + ROAD_WIDTH))
            if wnum == minWnum:
                width = SHELF_MAX_WIDTH
            else:
                width = min(SHELF_MAX_WIDTH, (self.width - wnum * ROAD_WIDTH) / 2 / (wnum + 1))
            buf = (self.width - width * 2 * (wnum + 1)) / wnum
            self.xroads.append(xbase - ROAD_WIDTH / 2)
            for i in range(wnum + 1):
                xcenters.append(xbase + (width * 2 + buf) * i + width)
                if i != wnum:
                    self.xroads.append(xbase + (width * 2 + buf) * i + width * 2 + buf / 2)
            self.xroads.append(xbase + self.width + ROAD_WIDTH / 2)

            res = linearGridShelfLayout(1, 0, ybase, self.height, 4)
            ycenters = res[0]
            self.yroads.append(ybase - ROAD_WIDTH / 2)
            self.yroads += res[1]
            self.yroads.append(ybase + self.height + ROAD_WIDTH / 2)
            height = res[2]

            for i in range(len(ycenters)):
                for j in range(len(xcenters)):
                    yc = ycenters[i]
                    xc = xcenters[j]
                    self.shelfs.append(Shelf(j, xc - width / 2, yc, width, height, X_NEG))
                    self.shelfs.append(Shelf(j, xc + width / 2, yc, width, height, X_POS))
        for i in range(len(self.shelfs)):
            self.shelfs[i].type = self.type


class StarPattern(Pattern):
    """a star-shaped space"""
    def __init__(self, centerPoint: np.ndarray, outNum: int, length: float, rotate: float):
        Pattern.__init__(self, centerPoint, STAR, None)
        self.outNum = outNum
        self.length = length
        self.rotate = rotate
        self.boundbox = self.getBoundbox()

    def getBoundbox(self):
        length = self.length + ROAD_WIDTH / 2
        width = ROAD_WIDTH + SHELF_MAX_WIDTH * 2
        angle = pi / self.outNum

        polygons = []
        for i in range(self.outNum):
            rotate = 2 * angle * i + self.rotate
            points = []
            points.append(self.centerPoint + vec(width, rotate - pi / 2))
            points.append(self.centerPoint + vec(width, rotate - pi / 2) + vec(length, rotate))
            points.append(self.centerPoint + vec(width, rotate + pi / 2) + vec(length, rotate))
            points.append(self.centerPoint + vec(width, rotate + pi / 2))
            polygons.append(Polygon(points))
        uni = polygons[0]
        for i in range(1, self.outNum):
            uni = uni.union(polygons[i])
        return uni

    def visualize(self):
        plt.fill([point[0] for point in self.boundbox.exterior.coords],
                 [point[1] for point in self.boundbox.exterior.coords],
                 color=BUFFER_COLOR)
        for shelf in self.shelfs:
            shelf.visualize(self.type)
        angle = pi / self.outNum
        for i in range(self.outNum):
            rotate = 2 * angle * i + self.rotate
            points = []
            points.append(self.centerPoint + vec(ROAD_WIDTH / 2, rotate - pi / 2))
            points.append(self.centerPoint + vec(ROAD_WIDTH / 2, rotate - pi / 2) + vec(self.length, rotate))
            points.append(self.centerPoint + vec(ROAD_WIDTH / 2, rotate + pi / 2) + vec(self.length, rotate))
            points.append(self.centerPoint + vec(ROAD_WIDTH / 2, rotate + pi / 2))
            plt.fill([point[0] for point in points], [point[1] for point in points], color=ROAD_COLOR)

    def randomChange(self, space: TwoDimSpace):
        patternChoice = random.randint(0, 4)
        width = self.boundbox.bounds[2] - self.boundbox.bounds[0]
        height = self.boundbox.bounds[3] - self.boundbox.bounds[1]
        centerPoint = p((self.boundbox.bounds[2] + self.boundbox.bounds[0]) / 2,
                        (self.boundbox.bounds[3] + self.boundbox.bounds[1]) / 2)
        if patternChoice == 0:  # change to line pattern
            if width > height:
                return LinePattern(centerPoint, width , 0)
            else:
                return LinePattern(centerPoint, height , 1)
        elif patternChoice == 1:  # change to grid pattern
            if random.randint(0, 1) == 0:
                return GridPattern(centerPoint, width ,
                                   max(ROAD_WIDTH + SHELF_MIN_WIDTH * 4 + EPS, height ), 0)
            else:
                return GridPattern(centerPoint, max(ROAD_WIDTH + SHELF_MIN_WIDTH * 4 + EPS, width ),
                                   height , 1)
        elif patternChoice == 2:  # change to web pattern
            return WebPattern(self.centerPoint, self.outNum, self.length, self.rotate)
        elif patternChoice == 3:  # change to round pattern
            return RoundPattern(centerPoint, max(width , SHELF_MIN_LENGTH + SHELF_MAX_WIDTH * 2 + EPS),
                                max(height , SHELF_MIN_LENGTH + SHELF_MAX_WIDTH * 2 + EPS))
        else:  # change to empty pattern
            return EmptyPattern(centerPoint, width, height)

    def adjust(self):
        if self.outNum < 3 or self.outNum > 6:
            self.adjustmentCost = 100
            return
        self.adjustmentCost = 0
        self.shelfs = []
        angle = pi / self.outNum
        buflen = (ROAD_WIDTH / 2 + SHELF_MAX_WIDTH * 2) * tan(pi / 2 - angle)
        outlen = self.length / 2 + buflen / 2
        length = self.length - buflen
        group = [0]
        for i in range(self.outNum):
            rot = self.rotate + i * 2 * angle
            p1 = self.centerPoint + vec(outlen, rot)
            self.shelfs += linearShelfLayout(group, 2,
                                             (p1 + vec(ROAD_WIDTH / 2 + SHELF_MAX_WIDTH * 1.5, rot + pi / 2))[0],
                                             (p1 + vec(ROAD_WIDTH / 2 + SHELF_MAX_WIDTH * 1.5, rot + pi / 2))[1],
                                             length, SHELF_MAX_WIDTH, 0, rot + pi / 2)
            self.shelfs += linearShelfLayout(group, 2,
                                             (p1 + vec(ROAD_WIDTH / 2 + SHELF_MAX_WIDTH * 0.5, rot + pi / 2))[0],
                                             (p1 + vec(ROAD_WIDTH / 2 + SHELF_MAX_WIDTH * 0.5, rot + pi / 2))[1],
                                             length, SHELF_MAX_WIDTH, 1, rot + pi / 2)
            self.shelfs += linearShelfLayout(group, 2,
                                             (p1 + vec(ROAD_WIDTH / 2 + SHELF_MAX_WIDTH * 0.5, rot - pi / 2))[0],
                                             (p1 + vec(ROAD_WIDTH / 2 + SHELF_MAX_WIDTH * 0.5, rot - pi / 2))[1],
                                             length, SHELF_MAX_WIDTH, 1, rot - pi / 2)
            self.shelfs += linearShelfLayout(group, 2,
                                             (p1 + vec(ROAD_WIDTH / 2 + SHELF_MAX_WIDTH * 1.5, rot - pi / 2))[0],
                                             (p1 + vec(ROAD_WIDTH / 2 + SHELF_MAX_WIDTH * 1.5, rot - pi / 2))[1],
                                             length, SHELF_MAX_WIDTH, 0, rot - pi / 2)
            if len(self.shelfs) == 0:
                self.adjustmentCost = 100
                break
        for i in range(len(self.shelfs)):
            self.shelfs[i].type = self.type


class WebPattern(Pattern):
    """a web-shaped space"""
    def __init__(self, centerPoint: np.ndarray, outNum: int, length: float, rotate: float):  # rotate is in radian
        Pattern.__init__(self, centerPoint, WEB, None)
        self.outNum = outNum
        self.length = length
        self.rotate = rotate
        self.boundbox = self.getBoundbox()
        self.roads = None

    def getBoundbox(self):
        pl = ROAD_WIDTH / 2 / sin((self.outNum - 2) * pi / (2 * self.outNum))
        length = self.length + pl

        points = []
        for i in range(self.outNum):
            points.append(self.centerPoint + vec(length, self.rotate + i * 2 * pi / self.outNum))
        return Polygon(points)

    def visualize(self):
        plt.fill([point[0] for point in self.boundbox.exterior.coords],
                 [point[1] for point in self.boundbox.exterior.coords],
                 color=BUFFER_COLOR)
        angle = pi / self.outNum
        for shelf in self.shelfs:
            shelf.visualize(self.type)
        for i in range(self.outNum):
            points = []
            points.append(self.centerPoint + vec(ROAD_WIDTH / 2, self.rotate + i * 2 * angle - pi / 2))
            points.append(self.centerPoint + vec(ROAD_WIDTH / 2, self.rotate + i * 2 * angle - pi / 2) +
                          vec(self.length, self.rotate + i * 2 * angle))
            points.append(self.centerPoint + vec(ROAD_WIDTH / 2, self.rotate + i * 2 * angle + pi / 2) +
                          vec(self.length, self.rotate + i * 2 * angle))
            points.append(self.centerPoint + vec(ROAD_WIDTH / 2, self.rotate + i * 2 * angle + pi / 2))
            plt.fill([points[j][0] for j in range(len(points))], [points[j][1] for j in range(len(points))],
                     color=ROAD_COLOR)
        for i in range(len(self.roads)):
            outLen = (ROAD_WIDTH / 2 / sin(angle) + self.roads[i]) / cos(angle)
            for j in range(self.outNum):
                points = []
                points.append(self.centerPoint +
                              vec(outLen - ROAD_WIDTH / 2 / cos(pi / 2 - angle), self.rotate + j * 2 * angle))
                points.append(self.centerPoint +
                              vec(outLen + ROAD_WIDTH / 2 / cos(pi / 2 - angle), self.rotate + j * 2 * angle))
                points.append(self.centerPoint + vec(outLen + ROAD_WIDTH / 2 / cos(pi / 2 - angle), self.rotate +
                                                     (j + 1) * 2 * angle))
                points.append(self.centerPoint + vec(outLen - ROAD_WIDTH / 2 / cos(pi / 2 - angle), self.rotate +
                                                     (j + 1) * 2 * angle))
                plt.fill([points[k][0] for k in range(len(points))], [points[k][1] for k in range(len(points))],
                         color=ROAD_COLOR)

    def randomChange(self, space: TwoDimSpace):
        patternChoice = random.randint(0, 4)
        width = self.boundbox.bounds[2] - self.boundbox.bounds[0]
        height = self.boundbox.bounds[3] - self.boundbox.bounds[1]
        centerPoint = p((self.boundbox.bounds[2] + self.boundbox.bounds[0]) / 2,
                        (self.boundbox.bounds[3] + self.boundbox.bounds[1]) / 2)
        if patternChoice == 0:  # change to line pattern
            if width > height:
                return LinePattern(centerPoint, width , 0)
            else:
                return LinePattern(centerPoint, height, 1)
        elif patternChoice == 1:  # change to grid pattern
            if random.randint(0, 1) == 0:
                return GridPattern(centerPoint, width ,
                                   max(ROAD_WIDTH + SHELF_MIN_WIDTH * 4 + EPS, height ), 0)
            else:
                return GridPattern(centerPoint, max(ROAD_WIDTH + SHELF_MIN_WIDTH * 4 + EPS, width ),
                                   height , 1)
        elif patternChoice == 2:  # change to star pattern
            return StarPattern(self.centerPoint, self.outNum, self.length, self.rotate)
        elif patternChoice == 3:  # change to round pattern
            return RoundPattern(centerPoint, max(width, SHELF_MIN_LENGTH + SHELF_MAX_WIDTH * 2 + EPS),
                                max(height , SHELF_MIN_LENGTH + SHELF_MAX_WIDTH * 2 + EPS))
        else:  # change to empty pattern
            return EmptyPattern(centerPoint, width, height)

    def adjust(self):
        if self.outNum < 3 or self.outNum > 6:
            self.adjustmentCost = 100
            return
        self.adjustmentCost = 0
        self.shelfs = []
        bx = self.centerPoint[0]
        by = self.centerPoint[1]
        angle = pi / self.outNum
        pl = ROAD_WIDTH / 2 / sin(angle)
        group = [0]
        for i in range(self.outNum):
            rot = self.rotate + (i * 2 + 1) * angle
            res = triangleShelfLayout(group, rot, bx + vec(pl, rot)[0], by + vec(pl, rot)[1],
                                      self.length * cos(angle) - pl, angle)
            if len(res[0]) == 0:
                self.adjustmentCost = 100
                break
            self.shelfs += res[0]
            if i == 0:
                self.roads = res[1]
                self.roads.reverse()
        for i in range(len(self.shelfs)):
            self.shelfs[i].type = self.type


class RoundPattern(Pattern):
    """an round-shaped space"""
    def __init__(self, centerPoint: np.ndarray, width: float, height: float):
        Pattern.__init__(self, centerPoint, ROUND, None)
        self.width = width
        self.height = height
        self.boundbox = self.getBoundbox()
        self.doubleLayer = False
        self.inCenter = None
        self.inTowards = None
        self.inStyle = random.randint(0, 1)

    def getBoundbox(self):
        return Polygon([
            self.centerPoint - vec(self.width / 2 + ROAD_WIDTH / 2, 0) - vec(self.height / 2 + ROAD_WIDTH / 2, pi / 2),
            self.centerPoint + vec(self.width / 2 + ROAD_WIDTH / 2, 0) - vec(self.height / 2 + ROAD_WIDTH / 2, pi / 2),
            self.centerPoint + vec(self.width / 2 + ROAD_WIDTH / 2, 0) + vec(self.height / 2 + ROAD_WIDTH / 2, pi / 2),
            self.centerPoint - vec(self.width / 2 + ROAD_WIDTH / 2, 0) + vec(self.height / 2 + ROAD_WIDTH / 2, pi / 2),
        ])

    def visualize(self):
        plt.fill([point[0] for point in self.boundbox.exterior.coords],
                 [point[1] for point in self.boundbox.exterior.coords],
                 color=BUFFER_COLOR)
        for shelf in self.shelfs:
            shelf.visualize(self.type)

    def randomChange(self, space: TwoDimSpace):
        patternChoice = random.randint(0, 4)
        if patternChoice == 0:  # change to line pattern
            if self.width > self.height:
                return LinePattern(self.centerPoint, self.width, 0)
            else:
                return LinePattern(self.centerPoint, self.height, 1)
        elif patternChoice == 1:  # change to grid pattern
            if random.randint(0, 1) == 0:
                return GridPattern(self.centerPoint, self.width,
                                   max(ROAD_WIDTH + SHELF_MIN_WIDTH * 4 + EPS, self.height), 0)
            else:
                return GridPattern(self.centerPoint, max(ROAD_WIDTH + SHELF_MIN_WIDTH * 4 + EPS, self.width),
                                   self.height, 1)
        elif patternChoice == 2:  # change to web pattern
            return WebPattern(self.centerPoint, 4, min(self.width / sqrt(2), self.height / sqrt(2)), pi / 4)
        elif patternChoice == 3:  # change to star pattern
            return StarPattern(self.centerPoint, 4, min(self.width / 2, self.height / 2), 0)
        else:  # change to empty pattern
            return EmptyPattern(self.centerPoint, self.width, self.height)

    def adjust(self):
        self.adjustmentCost = 0
        if self.width < SHELF_MIN_LENGTH + SHELF_MAX_WIDTH * 2 or self.height < SHELF_MIN_LENGTH + SHELF_MAX_WIDTH * 2:
            self.adjustmentCost = 100
            return
        self.shelfs = []
        bx = self.centerPoint[0]
        by = self.centerPoint[1]
        group = [0]
        if (self.width > ROUND_IN_WIDTH + SHELF_MAX_WIDTH * 4
                and self.height > ROUND_IN_WIDTH + SHELF_MIN_LENGTH * 2 + SHELF_MAX_WIDTH * 4) or (
                    self.height > ROUND_IN_WIDTH + SHELF_MAX_WIDTH * 4
                    and self.width > ROUND_IN_WIDTH + SHELF_MIN_LENGTH * 2 + SHELF_MAX_WIDTH * 4):
            self.doubleLayer = True
            if self.width > self.height:
                if self.inStyle == 0:
                    self.inTowards = Y_POS
                    self.inCenter = np.array([bx, by - self.height / 2])
                    halfwidth = (self.width - SHELF_MAX_WIDTH * 2 - ROUND_IN_WIDTH) / 2
                    self.shelfs += linearShelfLayout(group, 0, bx - self.width / 2 + SHELF_MAX_WIDTH,
                                                     by - self.height / 2 + SHELF_MAX_WIDTH / 2, halfwidth,
                                                     SHELF_MAX_WIDTH, Y_NEG)
                    self.shelfs += linearShelfLayout(group, 0, bx + ROUND_IN_WIDTH / 2,
                                                     by - self.height / 2 + SHELF_MAX_WIDTH / 2, halfwidth,
                                                     SHELF_MAX_WIDTH, Y_NEG)
                    self.shelfs += linearShelfLayout(group, 0, bx - self.width / 2 + SHELF_MAX_WIDTH * 2,
                                                     by - self.height / 2 + SHELF_MAX_WIDTH * 1.5,
                                                     halfwidth - SHELF_MAX_WIDTH, SHELF_MAX_WIDTH, Y_POS)
                    self.shelfs += linearShelfLayout(group, 0, bx + ROUND_IN_WIDTH / 2,
                                                     by - self.height / 2 + SHELF_MAX_WIDTH * 1.5,
                                                     halfwidth - SHELF_MAX_WIDTH, SHELF_MAX_WIDTH, Y_POS)
                    self.shelfs += linearShelfLayout(group, 0, bx - self.width / 2 + SHELF_MAX_WIDTH,
                                                     by + self.height / 2 - SHELF_MAX_WIDTH / 2,
                                                     self.width - SHELF_MAX_WIDTH * 2, SHELF_MAX_WIDTH, Y_POS)
                    self.shelfs += linearShelfLayout(group, 0, bx - self.width / 2 + SHELF_MAX_WIDTH * 2,
                                                     by + self.height / 2 - SHELF_MAX_WIDTH * 1.5,
                                                     self.width - SHELF_MAX_WIDTH * 4, SHELF_MAX_WIDTH, Y_NEG)
                    self.shelfs += linearShelfLayout(group, 1, bx - self.width / 2 + SHELF_MAX_WIDTH / 2,
                                                     by - self.height / 2 + SHELF_MAX_WIDTH,
                                                     self.height - SHELF_MAX_WIDTH * 2, SHELF_MAX_WIDTH, X_NEG)
                    self.shelfs += linearShelfLayout(group, 1, bx - self.width / 2 + SHELF_MAX_WIDTH * 1.5,
                                                     by - self.height / 2 + SHELF_MAX_WIDTH * 2,
                                                     self.height - SHELF_MAX_WIDTH * 4, SHELF_MAX_WIDTH, X_POS)
                    self.shelfs += linearShelfLayout(group, 1, bx + self.width / 2 - SHELF_MAX_WIDTH / 2,
                                                     by - self.height / 2 + SHELF_MAX_WIDTH,
                                                     self.height - SHELF_MAX_WIDTH * 2, SHELF_MAX_WIDTH, X_POS)
                    self.shelfs += linearShelfLayout(group, 1, bx + self.width / 2 - SHELF_MAX_WIDTH * 1.5,
                                                     by - self.height / 2 + SHELF_MAX_WIDTH * 2,
                                                     self.height - SHELF_MAX_WIDTH * 4, SHELF_MAX_WIDTH, X_NEG)
                else:
                    self.inTowards = Y_NEG
                    self.inCenter = np.array([bx, by + self.height / 2])
                    halfwidth = (self.width - SHELF_MAX_WIDTH * 2 - ROUND_IN_WIDTH) / 2
                    self.shelfs += linearShelfLayout(group, 0, bx - self.width / 2 + SHELF_MAX_WIDTH,
                                                     by + self.height / 2 - SHELF_MAX_WIDTH / 2, halfwidth,
                                                     SHELF_MAX_WIDTH, Y_POS)
                    self.shelfs += linearShelfLayout(group, 0, bx + ROUND_IN_WIDTH / 2,
                                                     by + self.height / 2 - SHELF_MAX_WIDTH / 2, halfwidth,
                                                     SHELF_MAX_WIDTH, Y_POS)
                    self.shelfs += linearShelfLayout(group, 0, bx - self.width / 2 + SHELF_MAX_WIDTH * 2,
                                                     by + self.height / 2 - SHELF_MAX_WIDTH * 1.5,
                                                     halfwidth - SHELF_MAX_WIDTH, SHELF_MAX_WIDTH, Y_NEG)
                    self.shelfs += linearShelfLayout(group, 0, bx + ROUND_IN_WIDTH / 2,
                                                     by + self.height / 2 - SHELF_MAX_WIDTH * 1.5,
                                                     halfwidth - SHELF_MAX_WIDTH, SHELF_MAX_WIDTH, Y_NEG)
                    self.shelfs += linearShelfLayout(group, 0, bx - self.width / 2 + SHELF_MAX_WIDTH,
                                                     by - self.height / 2 + SHELF_MAX_WIDTH / 2,
                                                     self.width - SHELF_MAX_WIDTH * 2, SHELF_MAX_WIDTH, Y_NEG)
                    self.shelfs += linearShelfLayout(group, 0, bx - self.width / 2 + SHELF_MAX_WIDTH * 2,
                                                     by - self.height / 2 + SHELF_MAX_WIDTH * 1.5,
                                                     self.width - SHELF_MAX_WIDTH * 4, SHELF_MAX_WIDTH, Y_POS)
                    self.shelfs += linearShelfLayout(group, 1, bx - self.width / 2 + SHELF_MAX_WIDTH / 2,
                                                     by - self.height / 2 + SHELF_MAX_WIDTH,
                                                     self.height - SHELF_MAX_WIDTH * 2, SHELF_MAX_WIDTH, X_NEG)
                    self.shelfs += linearShelfLayout(group, 1, bx - self.width / 2 + SHELF_MAX_WIDTH * 1.5,
                                                     by - self.height / 2 + SHELF_MAX_WIDTH * 2,
                                                     self.height - SHELF_MAX_WIDTH * 4, SHELF_MAX_WIDTH, X_POS)
                    self.shelfs += linearShelfLayout(group, 1, bx + self.width / 2 - SHELF_MAX_WIDTH / 2,
                                                     by - self.height / 2 + SHELF_MAX_WIDTH,
                                                     self.height - SHELF_MAX_WIDTH * 2, SHELF_MAX_WIDTH, X_POS)
                    self.shelfs += linearShelfLayout(group, 1, bx + self.width / 2 - SHELF_MAX_WIDTH * 1.5,
                                                     by - self.height / 2 + SHELF_MAX_WIDTH * 2,
                                                     self.height - SHELF_MAX_WIDTH * 4, SHELF_MAX_WIDTH, X_NEG)
            else:
                if self.inStyle == 0:
                    self.inTowards = X_POS
                    self.inCenter = np.array([bx - self.width / 2, by])
                    halfheight = (self.height - SHELF_MAX_WIDTH * 2 - ROUND_IN_WIDTH) / 2
                    self.shelfs += linearShelfLayout(group, 1, bx - self.width / 2 + SHELF_MAX_WIDTH / 2,
                                                     by - self.height / 2 + SHELF_MAX_WIDTH, halfheight,
                                                     SHELF_MAX_WIDTH, X_NEG)
                    self.shelfs += linearShelfLayout(group, 1, bx - self.width / 2 + SHELF_MAX_WIDTH / 2,
                                                     by + ROUND_IN_WIDTH / 2, halfheight, SHELF_MAX_WIDTH, X_NEG)
                    self.shelfs += linearShelfLayout(group, 1, bx - self.width / 2 + SHELF_MAX_WIDTH * 1.5,
                                                     by - self.height / 2 + SHELF_MAX_WIDTH * 2,
                                                     halfheight - SHELF_MAX_WIDTH, SHELF_MAX_WIDTH, X_POS)
                    self.shelfs += linearShelfLayout(group, 1, bx - self.width / 2 + SHELF_MAX_WIDTH * 1.5,
                                                     by + ROUND_IN_WIDTH / 2, halfheight - SHELF_MAX_WIDTH,
                                                     SHELF_MAX_WIDTH, X_POS)
                    self.shelfs += linearShelfLayout(group, 1, bx + self.width / 2 - SHELF_MAX_WIDTH / 2,
                                                     by - self.height / 2 + SHELF_MAX_WIDTH,
                                                     self.height - SHELF_MAX_WIDTH * 2, SHELF_MAX_WIDTH, X_POS)
                    self.shelfs += linearShelfLayout(group, 1, bx + self.width / 2 - SHELF_MAX_WIDTH * 1.5,
                                                     by - self.height / 2 + SHELF_MAX_WIDTH * 2,
                                                     self.height - SHELF_MAX_WIDTH * 4, SHELF_MAX_WIDTH, X_NEG)
                    self.shelfs += linearShelfLayout(group, 0, bx - self.width / 2 + SHELF_MAX_WIDTH,
                                                     by - self.height / 2 + SHELF_MAX_WIDTH / 2,
                                                     self.width - SHELF_MAX_WIDTH * 2, SHELF_MAX_WIDTH, Y_NEG)
                    self.shelfs += linearShelfLayout(group, 0, bx - self.width / 2 + SHELF_MAX_WIDTH * 2,
                                                     by - self.height / 2 + SHELF_MAX_WIDTH * 1.5,
                                                     self.width - SHELF_MAX_WIDTH * 4, SHELF_MAX_WIDTH, Y_POS)
                    self.shelfs += linearShelfLayout(group, 0, bx - self.width / 2 + SHELF_MAX_WIDTH,
                                                     by + self.height / 2 - SHELF_MAX_WIDTH / 2,
                                                     self.width - SHELF_MAX_WIDTH * 2, SHELF_MAX_WIDTH, Y_POS)
                    self.shelfs += linearShelfLayout(group, 0, bx - self.width / 2 + SHELF_MAX_WIDTH * 2,
                                                     by + self.height / 2 - SHELF_MAX_WIDTH * 1.5,
                                                     self.width - SHELF_MAX_WIDTH * 4, SHELF_MAX_WIDTH, Y_NEG)
                else:
                    self.inTowards = X_NEG
                    self.inCenter = np.array([bx - self.width / 2, by])
                    halfheight = (self.height - SHELF_MAX_WIDTH * 2 - ROUND_IN_WIDTH) / 2
                    self.shelfs += linearShelfLayout(group, 1, bx + self.width / 2 - SHELF_MAX_WIDTH / 2,
                                                     by - self.height / 2 + SHELF_MAX_WIDTH, halfheight,
                                                     SHELF_MAX_WIDTH, X_POS)
                    self.shelfs += linearShelfLayout(group, 1, bx + self.width / 2 - SHELF_MAX_WIDTH / 2,
                                                     by + ROUND_IN_WIDTH / 2, halfheight, SHELF_MAX_WIDTH, X_POS)
                    self.shelfs += linearShelfLayout(group, 1, bx + self.width / 2 - SHELF_MAX_WIDTH * 1.5,
                                                     by - self.height / 2 + SHELF_MAX_WIDTH * 2,
                                                     halfheight - SHELF_MAX_WIDTH, SHELF_MAX_WIDTH, X_NEG)
                    self.shelfs += linearShelfLayout(group, 1, bx + self.width / 2 - SHELF_MAX_WIDTH * 1.5,
                                                     by + ROUND_IN_WIDTH / 2, halfheight - SHELF_MAX_WIDTH,
                                                     SHELF_MAX_WIDTH, X_NEG)
                    self.shelfs += linearShelfLayout(group, 1, bx - self.width / 2 + SHELF_MAX_WIDTH / 2,
                                                     by - self.height / 2 + SHELF_MAX_WIDTH,
                                                     self.height - SHELF_MAX_WIDTH * 2, SHELF_MAX_WIDTH, X_NEG)
                    self.shelfs += linearShelfLayout(group, 1, bx - self.width / 2 + SHELF_MAX_WIDTH * 1.5,
                                                     by - self.height / 2 + SHELF_MAX_WIDTH * 2,
                                                     self.height - SHELF_MAX_WIDTH * 4, SHELF_MAX_WIDTH, X_POS)
                    self.shelfs += linearShelfLayout(group, 0, bx - self.width / 2 + SHELF_MAX_WIDTH,
                                                     by - self.height / 2 + SHELF_MAX_WIDTH / 2,
                                                     self.width - SHELF_MAX_WIDTH * 2, SHELF_MAX_WIDTH, Y_NEG)
                    self.shelfs += linearShelfLayout(group, 0, bx - self.width / 2 + SHELF_MAX_WIDTH * 2,
                                                     by - self.height / 2 + SHELF_MAX_WIDTH * 1.5,
                                                     self.width - SHELF_MAX_WIDTH * 4, SHELF_MAX_WIDTH, Y_POS)
                    self.shelfs += linearShelfLayout(group, 0, bx - self.width / 2 + SHELF_MAX_WIDTH,
                                                     by + self.height / 2 - SHELF_MAX_WIDTH / 2,
                                                     self.width - SHELF_MAX_WIDTH * 2, SHELF_MAX_WIDTH, Y_POS)
                    self.shelfs += linearShelfLayout(group, 0, bx - self.width / 2 + SHELF_MAX_WIDTH * 2,
                                                     by + self.height / 2 - SHELF_MAX_WIDTH * 1.5,
                                                     self.width - SHELF_MAX_WIDTH * 4, SHELF_MAX_WIDTH, Y_NEG)
        else:
            self.shelfs += linearShelfLayout(group, 0, bx - self.width / 2 + SHELF_MAX_WIDTH,
                                             by - self.height / 2 + SHELF_MAX_WIDTH / 2,
                                             self.width - SHELF_MAX_WIDTH * 2, SHELF_MAX_WIDTH, Y_NEG)
            self.shelfs += linearShelfLayout(group, 0, bx - self.width / 2 + SHELF_MAX_WIDTH,
                                             by + self.height / 2 - SHELF_MAX_WIDTH / 2,
                                             self.width - SHELF_MAX_WIDTH * 2, SHELF_MAX_WIDTH, Y_POS)
            self.shelfs += linearShelfLayout(group, 1, bx - self.width / 2 + SHELF_MAX_WIDTH / 2,
                                             by - self.height / 2 + SHELF_MAX_WIDTH, self.height - SHELF_MAX_WIDTH * 2,
                                             SHELF_MAX_WIDTH, X_NEG)
            self.shelfs += linearShelfLayout(group, 1, bx + self.width / 2 - SHELF_MAX_WIDTH / 2,
                                             by - self.height / 2 + SHELF_MAX_WIDTH, self.height - SHELF_MAX_WIDTH * 2,
                                             SHELF_MAX_WIDTH, X_POS)
        for i in range(len(self.shelfs)):
            self.shelfs[i].type = self.type


class EmptyPattern(Pattern):
    """an empty space, mainly for flexibility"""
    def __init__(self, centerPoint: np.ndarray, width: float, height: float):
        Pattern.__init__(self, centerPoint, EMPTY, None)
        self.width = width
        self.height = height
        self.boundbox = self.getBoundbox()

    def area(self):
        return (self.width + ROAD_WIDTH) * (self.height + ROAD_WIDTH)

    def getBoundbox(self):
        return Polygon([
            self.centerPoint - vec(self.width / 2 + ROAD_WIDTH / 2, 0) - vec(self.height / 2 + ROAD_WIDTH / 2, pi / 2),
            self.centerPoint + vec(self.width / 2 + ROAD_WIDTH / 2, 0) - vec(self.height / 2 + ROAD_WIDTH / 2, pi / 2),
            self.centerPoint + vec(self.width / 2 + ROAD_WIDTH / 2, 0) + vec(self.height / 2 + ROAD_WIDTH / 2, pi / 2),
            self.centerPoint - vec(self.width / 2 + ROAD_WIDTH / 2, 0) + vec(self.height / 2 + ROAD_WIDTH / 2, pi / 2),
        ])

    def visualize(self):
        plt.fill([point[0] for point in self.boundbox.exterior.coords],
                 [point[1] for point in self.boundbox.exterior.coords],
                 color=BUFFER_COLOR)
        plt.fill([
            self.centerPoint[0] - self.width / 2, self.centerPoint[0] + self.width / 2,
            self.centerPoint[0] + self.width / 2, self.centerPoint[0] - self.width / 2
        ], [
            self.centerPoint[1] - self.height / 2, self.centerPoint[1] - self.height / 2,
            self.centerPoint[1] + self.height / 2, self.centerPoint[1] + self.height / 2
        ],
                 color=EMPTY_SPACE_COLOR)

    def randomChange(self, space: TwoDimSpace):
        bias = max(SPACE_BUFFER - self.boundbox.distance(space.boundary) + EPS, 0)
        patternChoice = random.randint(0, 4)
        if patternChoice == 0:  # change to line pattern
            if self.width > self.height:
                return LinePattern(self.centerPoint, self.width - bias * 2, 0)
            else:
                return LinePattern(self.centerPoint, self.height - bias * 2, 1)
        elif patternChoice == 1:  # change to grid pattern
            if random.randint(0, 1) == 0:
                return GridPattern(self.centerPoint, self.width - bias * 2,
                                   max(ROAD_WIDTH + SHELF_MIN_WIDTH * 4 + EPS, self.height - bias * 2), 0)
            else:
                return GridPattern(self.centerPoint, max(ROAD_WIDTH + SHELF_MIN_WIDTH * 4 + EPS,
                                                         self.width - bias * 2), self.height - bias * 2, 1)
        elif patternChoice == 2:  # change to web pattern
            return WebPattern(self.centerPoint, 4,
                              min((self.width - bias * 2) / sqrt(2), (self.height - bias * 2) / sqrt(2)), pi / 4)
        elif patternChoice == 3:  # change to star pattern
            return StarPattern(self.centerPoint, 4, min((self.width - bias * 2) / 2, (self.height - bias * 2) / 2), 0)
        else:  # change to round pattern
            return RoundPattern(self.centerPoint,
                                max(self.width - bias * 2, SHELF_MIN_LENGTH + SHELF_MAX_WIDTH * 2 + EPS),
                                max(self.height - bias * 2, SHELF_MIN_LENGTH + SHELF_MAX_WIDTH * 2 + EPS))

    def adjust(self):
        self.adjustmentCost = 0
        if self.width < ROAD_WIDTH or self.height < ROAD_WIDTH:
            self.adjustmentCost = 100
            return


class WallPattern:
    """the pattern adjacent to walls"""
    def __init__(self, centerPoint: np.ndarray, length: float, type: int, orient: int, towards: int, follow: int):
        self.centerPoint = centerPoint
        self.length = length
        self.type = type
        self.orient = orient
        self.towards = towards
        self.follow = follow
        self.shelfs = []
        group = [0]
        if orient == 0:
            self.shelfs = linearShelfLayout(group, 0, self.centerPoint[0] - self.length / 2, self.centerPoint[1],
                                            self.length, SHELF_MAX_WIDTH, self.towards)
        else:
            self.shelfs = linearShelfLayout(group, 1, self.centerPoint[0], self.centerPoint[1] - self.length / 2,
                                            self.length, SHELF_MAX_WIDTH, self.towards)
        for i in range(len(self.shelfs)):
            self.shelfs[i].type = self.type

    def area(self):
        ret = 0
        for shelf in self.shelfs:
            ret += shelf.xl * shelf.yl
        return ret

    def visualize(self):
        for shelf in self.shelfs:
            shelf.visualize(self.type)


def linearGridShelfLayout(orient: int, xbase: float, ybase: float, l: float, maxconnect: int):
    if l < SHELF_MIN_LENGTH:
        return [[], [], 0]
    centers = []
    roads = []
    setNum = (int)(l / (SHELF_MIN_LENGTH * maxconnect + ROAD_WIDTH))
    num = (int)((l - setNum * ROAD_WIDTH) / SHELF_MIN_LENGTH)
    length = 0
    minNum = (int)((l - setNum * ROAD_WIDTH) / SHELF_MAX_LENGTH)
    roadNum = 0
    if num == minNum:
        length = SHELF_MAX_LENGTH
    else:
        length = min((l - setNum * ROAD_WIDTH) / num, SHELF_MAX_LENGTH)
        num = min(maxconnect * (setNum + 1), num)
    if num == 1:
        centers = [l / 2]
    else:
        buf = max(0, (l - setNum * ROAD_WIDTH - length * num) / (num - (setNum + 1)))
        avgSetNum = (int)(num / (setNum + 1))
        connectSets = [avgSetNum for i in range(setNum + 1)]
        leftNum = num - avgSetNum * (setNum + 1)
        for i in range(leftNum):
            connectSets[i] += 1

        now = 0
        for i in range(setNum + 1):
            for j in range(connectSets[i]):
                centers.append(now + length / 2)
                if j != connectSets[i] - 1:
                    now += length + buf
                else:
                    now += length
            if i != setNum:
                roads.append(now + ROAD_WIDTH / 2)
                now += ROAD_WIDTH

    if orient == 0:
        for i in range(len(centers)):
            centers[i] += xbase
        for i in range(len(roads)):
            roads[i] += xbase
    else:
        for i in range(len(centers)):
            centers[i] += ybase
        for i in range(len(roads)):
            roads[i] += ybase
    return [centers, roads, length]


def linearShelfLayout(group: list,
                      orient: int,
                      xbase: float,
                      ybase: float,
                      l: float,
                      w: float,
                      towards: int,
                      rotate=0.0):
    if l < SHELF_MIN_LENGTH:
        return []
    shelfs = []
    num = (int)(l / SHELF_MIN_LENGTH)
    length = 0
    minNum = (int)(l / SHELF_MAX_LENGTH)
    if num == minNum:
        length = SHELF_MAX_LENGTH
    else:
        length = l / num
    if orient == 0:
        if num == 1:
            shelfs = [Shelf(group[0], xbase + l / 2, ybase, length, w, towards)]
            group[0] += 1
        else:
            buf = (l - length * num) / (num - 1)
            addition = 0
            numbers = None
            if num <= 3:
                numbers = [group[0] for i in range(num)]
                addition = 1
            elif num <= 8:
                split = (int)(num / 2)
                numbers = [group[0] for i in range(split)] + [group[0] + 1 for i in range(split, num)]
                addition = 2
            else:
                addition = (int)((num + 3) / 4)
                split = (int)((num + addition - 1) / addition)
                numbers = [group[0] + (int)(i / split) for i in range(num)]
            for i in range(num):
                shelfs.append(Shelf(numbers[i], xbase + length / 2 + (length + buf) * i, ybase, length, w, towards))
            group[0] += addition
    elif orient == 1:
        if num == 1:
            shelfs = [Shelf(group[0], xbase, ybase + l / 2, w, length, towards)]
            group[0] += 1
        else:
            buf = (l - length * num) / (num - 1)
            addition = 0
            numbers = None
            if num <= 3:
                numbers = [group[0] for i in range(num)]
                addition = 1
            elif num <= 8:
                split = (int)(num / 2)
                numbers = [group[0] for i in range(split)] + [group[0] + 1 for i in range(split, num)]
                addition = 2
            else:
                addition = (int)((num + 3) / 4)
                split = (int)((num + addition - 1) / addition)
                numbers = [group[0] + (int)(i / split) for i in range(num)]
            for i in range(num):
                shelfs.append(Shelf(numbers[i], xbase, ybase + length / 2 + (length + buf) * i, w, length, towards))
            group[0] += addition
    else:
        if num == 1:
            shelfs = [Shelf(group[0], xbase, ybase, length, w, ROTATE, towards * pi + rotate)]
            group[0] += 1
        else:
            buf = (l - length * num) / (num - 1)
            xb = xbase + vec(l / 2, rotate + pi / 2)[0]
            yb = ybase + vec(l / 2, rotate + pi / 2)[1]
            addition = 0
            numbers = None
            if num <= 3:
                numbers = [group[0] for i in range(num)]
                addition = 1
            elif num <= 8:
                split = (int)(num / 2)
                numbers = [group[0] for i in range(split)] + [group[0] + 1 for i in range(split, num)]
                addition = 2
            else:
                addition = (int)((num + 3) / 4)
                split = (int)((num + addition - 1) / addition)
                numbers = [group[0] + (int)(i / split) for i in range(num)]
            for i in range(num):
                shelfs.append(
                    Shelf(numbers[i], xb + vec(length / 2 + (length + buf) * i, rotate - pi / 2)[0],
                          yb + vec(length / 2 + (length + buf) * i, rotate - pi / 2)[1], length, w, ROTATE,
                          towards * pi + rotate))
            group[0] += addition
    return shelfs


def triangleShelfLayout(group: list, rotate: float, xbase: float, ybase: float, length: float, angle: float):
    shelfs = []
    roads = []
    nowDist = length - SHELF_MAX_WIDTH / 2
    while nowDist > 0:
        shelfs += linearShelfLayout(group, 2, xbase + vec(nowDist, rotate)[0], ybase + vec(nowDist, rotate)[1],
                                    2 * nowDist * tan(angle), SHELF_MAX_WIDTH, 0, rotate)
        nowDist -= SHELF_MAX_WIDTH
        shelfs += linearShelfLayout(group, 2, xbase + vec(nowDist, rotate)[0], ybase + vec(nowDist, rotate)[1],
                                    2 * nowDist * tan(angle), SHELF_MAX_WIDTH, 1, rotate)
        nowDist -= SHELF_MAX_WIDTH + ROAD_WIDTH
        if nowDist > 0:
            roads.append(nowDist + (SHELF_MAX_WIDTH + ROAD_WIDTH) / 2)
    return [shelfs, roads]


@jit(nopython=True)
def angleBetween(v1: np.ndarray, v2: np.ndarray):
    """return the angle in degrees between two vectors, always non-negative"""
    l1 = sqrt(v1.dot(v1))
    l2 = sqrt(v2.dot(v2))
    angleInRadian = np.arccos(v1.dot(v2) / (l1 * l2))
    angleInDegree = abs(angleInRadian * 180 / np.pi)
    if angleInDegree > 180:
        angleInDegree -= 180
    return angleInDegree


@jit(nopython=True)
def exclude(l: list, val):
    """remove val if val in list """
    if val in l:
        l.remove(val)


@jit(nopython=True)
def norm(vector: np.ndarray):
    """return the normalized vector"""
    if np.linalg.norm(vector) > 0:
        return vector / np.linalg.norm(vector)
    return vector


@jit(nopython=True)
def p(x: float, y: float):
    """a point or a vector"""
    return np.array([x, y])


@jit(nopython=True)
def rot(point: np.ndarray, angle: float):
    """rotate a vector counter-clockwise, angle is in radian"""
    return np.array([point[0] * cos(angle) - point[1] * sin(angle), point[0] * sin(angle) + point[1] * cos(angle)])


@jit(nopython=True)
def vec(length: float, angle: float):
    """a vector starts at the original point, angle is in radian"""
    return rot(np.array([length, 0]), angle)


@jit(nopython=True)
def cpointsCmp(l1: list, l2: list):
    if l1[3] < l2[3]:
        return -1
    elif l1[3] > l2[3]:
        return 1
    return 0

def contextCostCmp(context1: list, context2: list):
    if context1[0][5] < context2[0][5]:
        return -1
    elif context1[0][5] > context2[0][5]:
        return 1
    return 0