from pattern import *
from params import *
from transform import transform
from movebest import movebest

actionProbabilities = [0.25, 0.6, 0.06, 0.04, 0.05]  # move, resize, add, remove, change
standardProbabilities = []


def visualizeSpace(space: TwoDimSpace, patternList: list, wallPatterns: list, name: str):
    """visualize current space and patterns and save the result"""
    width = space.boundary.bounds[2] - space.boundary.bounds[0]
    height = space.boundary.bounds[3] - space.boundary.bounds[1]
    if width < height:
        plt.figure(figsize=(10, height / width * 10))
    else:
        plt.figure(figsize=(width / height * 10, 10))
    space.visualize()
    for pattern in patternList:
        pattern.visualize()
    for wpattern in wallPatterns:
        wpattern.visualize()
    plt.xlabel('x')
    plt.ylabel('y')
    plt.savefig(name)
    plt.close()


def visualizeAll(space: TwoDimSpace, patternList: list, wallPatterns: list, net: list, totalcost: float, iterRound: int,
                 name: str):
    width = space.boundary.bounds[2] - space.boundary.bounds[0]
    height = space.boundary.bounds[3] - space.boundary.bounds[1]
    if width < height:
        plt.figure(figsize=(10, height / width * 10))
    else:
        plt.figure(figsize=(width / height * 10, 10))
    space.visualize()
    shelfs = []
    for pattern in patternList:
        shelfs += pattern.shelfs
    for wpattern in wallPatterns:
        shelfs += wpattern.shelfs
    for shelf in shelfs:
        shelf.visualize()
    fullnet = net[0]
    if nx.is_connected(fullnet):
        longest = getLongestPathLength(fullnet)
        bestSpanningTree = longest[1]
        mainPath = nx.bidirectional_shortest_path(bestSpanningTree, 0, 1)
        for i in range(len(mainPath) - 1):
            p1 = [fullnet.nodes[mainPath[i]]['x'], fullnet.nodes[mainPath[i]]['y']]
            p2 = [fullnet.nodes[mainPath[i + 1]]['x'], fullnet.nodes[mainPath[i + 1]]['y']]
            angle = atan2(p2[1] - p1[1], p2[0] - p1[0])
            roadPoints = []
            roadPoints.append(p1 + vec(ROAD_WIDTH / 4, angle - pi / 2))
            roadPoints.append(p2 + vec(ROAD_WIDTH / 4, angle - pi / 2))
            roadPoints.append(p2 + vec(ROAD_WIDTH / 4, angle + pi / 2))
            roadPoints.append(p1 + vec(ROAD_WIDTH / 4, angle + pi / 2))
            plt.fill([roadPoints[i][0] for i in range(4)], [roadPoints[i][1] for i in range(4)], color=ROAD_COLOR)

        plt.annotate('totalCost:' + (str)(totalcost), (space.boundary.bounds[2], space.boundary.bounds[3]), size=12)
        plt.annotate('round:' + (str)(iterRound), (space.boundary.bounds[2], space.boundary.bounds[3] - 2), size=12)

    plt.xlabel('x')
    plt.ylabel('y')
    plt.savefig(name)
    plt.close()


def visualizeNet(space: TwoDimSpace, net: list, name: str):
    fullnet = net[0]
    width = space.boundary.bounds[2] - space.boundary.bounds[0]
    height = space.boundary.bounds[3] - space.boundary.bounds[1]
    if width < height:
        plt.figure(figsize=(10, height / width * 10))
    else:
        plt.figure(figsize=(width / height * 10, 10))
    space.visualize()

    nodeList = [i for i in fullnet.nodes]
    pointList = [[fullnet.nodes[i]['x'], fullnet.nodes[i]['y']] for i in fullnet.nodes]
    for i in range(len(pointList)):
        plt.plot(pointList[i][0], pointList[i][1], 'o', color=(0, 0, 0), markersize=15)

    if nx.is_connected(fullnet):
        longest = getLongestPathLength(fullnet)
        bestSpanningTree = longest[1]
        mainPath = nx.bidirectional_shortest_path(bestSpanningTree, 0, 1)
        for i in range(len(nodeList)):
            for j in range(i + 1, len(nodeList)):
                if bestSpanningTree.has_edge(nodeList[i],
                                             nodeList[j]) and nodeList[i] in mainPath and nodeList[j] in mainPath:
                    plt.plot([pointList[i][0], pointList[j][0]], [pointList[i][1], pointList[j][1]],
                             color=(0, 0, 0),
                             linewidth=5)
                    length = '{:.1f}'.format(fullnet[nodeList[i]][nodeList[j]]['length'])
                    plt.text((pointList[i][0] + pointList[j][0]) / 2, (pointList[i][1] + pointList[j][1]) / 2,
                             length,
                             size=11)
                elif fullnet.has_edge(nodeList[i], nodeList[j]):
                    plt.plot([pointList[i][0], pointList[j][0]], [pointList[i][1], pointList[j][1]], color=(0, 0, 0))
                    length = '{:.1f}'.format(fullnet[nodeList[i]][nodeList[j]]['length'])
                    plt.text((pointList[i][0] + pointList[j][0]) / 2, (pointList[i][1] + pointList[j][1]) / 2,
                             length,
                             size=7)

        totalPathLength = 0
        longestPathLength = longest[0]
        for edge in fullnet.edges:
            totalPathLength += fullnet[edge[0]][edge[1]]['length']

        traversalRatio = longestPathLength / totalPathLength
        plt.annotate('traversalRatio:' + (str)(traversalRatio), (space.boundary.bounds[2], space.boundary.bounds[3]),
                     size=12)

    plt.xlabel('x')
    plt.ylabel('y')
    plt.savefig(name)
    plt.close()


def visualizeCost(totalcostList: list, name: str):
    """visualize the trend of the totalcost during the iteration"""
    plt.plot([i for i in range(1, len(totalcostList) + 1)], [cost for cost in totalcostList])
    plt.xlabel('round')
    plt.ylabel('totalcost')
    plt.savefig(name)
    plt.close()


def getLongestPathLength(fullnet: nx.Graph, shouldPrint=False):
    """approximate the longest path length between entrancepoint and exitpoint"""
    spanningTree = nx.algorithms.maximum_spanning_tree(fullnet, weight='length')
    mainPath = nx.bidirectional_shortest_path(spanningTree, 0, 1)
    maxLength = 0
    while True:
        if shouldPrint:
            print(maxLength)
        maxLength = 0
        for i in range(len(mainPath) - 1):
            maxLength += spanningTree[mainPath[i]][mainPath[i + 1]]['length']
        newnet = deepcopy(fullnet)
        for i in range(len(mainPath)):
            newnet.remove_node(mainPath[i])
        while True:
            for i in range(len(mainPath) - 1):  # based on triangle inequality
                valid1, valid2 = [], []
                for neighbor in fullnet.neighbors(mainPath[i]):
                    if not (neighbor in mainPath):
                        valid1.append(neighbor)
                for neighbor in fullnet.neighbors(mainPath[i + 1]):
                    if not (neighbor in mainPath):
                        valid2.append(neighbor)
                for j in valid1:
                    breakFlag = False
                    for k in valid2:
                        if j == k:
                            mainPath.insert(i + 1, j)
                            newnet.remove_node(j)
                            breakFlag = True
                            break
                        elif nx.has_path(newnet, j, k):
                            path = nx.bidirectional_shortest_path(newnet, j, k)
                            mainPath = mainPath[0:i + 1] + path + mainPath[i + 1:]
                            for l in path:
                                newnet.remove_node(l)
                            breakFlag = True
                            break
                    if breakFlag:
                        break
            nowLength = 0
            for i in range(len(mainPath) - 1):
                nowLength += fullnet[mainPath[i]][mainPath[i + 1]]['length']
            if nowLength < maxLength + DELTA:
                break
            else:
                maxLength = nowLength

        for edge in fullnet.edges:
            fullnet[edge[0]][edge[1]]['foo'] = fullnet[edge[0]][edge[1]]['length']
        for i in range(len(mainPath) - 1):
            fullnet[mainPath[i]][mainPath[i + 1]]['foo'] = 10000
        spanningTree = nx.algorithms.maximum_spanning_tree(fullnet, weight='foo')

        for edge in fullnet.edges:
            if not spanningTree.has_edge(edge[0], edge[1]):
                spanningTree.add_edge(edge[0], edge[1])
                spanningTree[edge[0]][edge[1]]['length'] = fullnet[edge[0]][edge[1]]['length']
                cycle = nx.algorithms.find_cycle(spanningTree, source=edge[0])
                cycleNodes = [edge[0] for edge in cycle]
                intersectNodes = []
                findFlag = False
                for i in mainPath:
                    if i in cycleNodes:
                        intersectNodes.append(i)
                        findFlag = True
                    elif findFlag:
                        break
                if len(intersectNodes) <= 1 or len(intersectNodes) == len(cycleNodes):
                    spanningTree.remove_edge(edge[0], edge[1])
                    continue
                cycleLength = spanningTree[cycleNodes[0]][cycleNodes[len(cycleNodes) - 1]]['length']
                intersectLength = 0
                minIntersectEdge = []
                minIntersectEdgeLength = 10000
                for i in range(len(intersectNodes) - 1):
                    length = spanningTree[intersectNodes[i]][intersectNodes[i + 1]]['length']
                    intersectLength += length
                    if length < minIntersectEdgeLength:
                        minIntersectEdgeLength = length
                        minIntersectEdge = [intersectNodes[i], intersectNodes[i + 1]]
                for i in range(len(cycleNodes) - 1):
                    cycleLength += spanningTree[cycleNodes[i]][cycleNodes[i + 1]]['length']
                if intersectLength * 2 < cycleLength:
                    spanningTree.remove_edge(minIntersectEdge[0], minIntersectEdge[1])
                    mainPath = nx.bidirectional_shortest_path(spanningTree, 0, 1)
                else:
                    spanningTree.remove_edge(edge[0], edge[1])
        nowLength = 0
        for i in range(len(mainPath) - 1):
            nowLength += spanningTree[mainPath[i]][mainPath[i + 1]]['length']
        if nowLength < maxLength + DELTA:
            return [nowLength, spanningTree]
        else:
            maxLength = nowLength


def getTotalcost(net: list, patternList: list, wallPatterns: list, space: TwoDimSpace):
    """calculate the total cost value of the current patterns"""
    totalcost = 0
    usedArea = 0
    flexArea = 0
    adjustmentCost = 0
    utilityRatioCost = 0
    flexRatioCost = 0
    patternNumberCost = 0
    emptyInOutCost = 0
    netDegreeCost = 0
    fullnetCost = 0
    varietyCost = 0
    varietyFlag = [0, 0, 0, 0, 0]  # line, round, grid, web, star

    for pattern in patternList:
        adjustmentCost += pattern.adjustmentCost
        if isinstance(pattern, EmptyPattern):
            flexArea += pattern.area()
        elif isinstance(pattern, RoundPattern):
            # flexArea += (pattern.width - SHELF_MAX_WIDTH * 2) * (
            #     pattern.height - SHELF_MAX_WIDTH * 2)
            usedArea += pattern.area()
            varietyFlag[1] += 1
        elif isinstance(pattern, LinePattern):
            usedArea += pattern.area()
            varietyFlag[0] += 1
        elif isinstance(pattern, GridPattern):
            usedArea += pattern.area()
            varietyFlag[2] += 1
        elif isinstance(pattern, WebPattern):
            usedArea += pattern.area()
            varietyFlag[3] += 1
        elif isinstance(pattern, StarPattern):
            usedArea += pattern.area()
            varietyFlag[4] += 1
    for wpattern in wallPatterns:
        usedArea += wpattern.area()

    varietyCount = 0
    for i in range(4):
        if varietyFlag[i] > 0:
            varietyCount += 1
    if varietyCount == 2:
        varietyCost = -0.2
    elif varietyCount >= 3:
        varietyCost = -0.5
    utilityRatio = usedArea / space.area()
    flexRatio = flexArea / space.area()

    utilityRatioCost = (1 - utilityRatio) * 30

    if flexRatio < 0.04:
        flexRatioCost += (0.04 - flexRatio) * 50
    else:
        flexRatioCost += (flexRatio - 0.04) * 0.05

    if len(patternList) > PATTERN_LIMIT:
        patternNumberCost += (len(patternList) - PATTERN_LIMIT) * 0.1

    fullnet = net[0]
    emptyCenters = net[1]
    for i in list(fullnet.neighbors(0)):
        if (i in emptyCenters) and fullnet[0][i]['length'] < 4:
            emptyInOutCost -= 0.5
            break
    for i in list(fullnet.neighbors(1)):
        if (i in emptyCenters) and fullnet[1][i]['length'] < 4:
            emptyInOutCost -= 0.5
            break

    nodeList = list(fullnet.nodes)
    for i in range(2, len(nodeList)):
        if fullnet.degree[nodeList[i]] == 1:
            netDegreeCost += 0.03

    if len(patternList) > 0:
        totalLength = 0
        for edge in fullnet.edges:
            totalLength += fullnet[edge[0]][edge[1]]['length']
        longestLength = getLongestPathLength(fullnet)[0]
        fullnetCost = (1 - longestLength / totalLength)
    else:
        fullnetCost = 1

    totalcost = adjustmentCost + utilityRatioCost + flexRatioCost + \
        patternNumberCost + emptyInOutCost + netDegreeCost + fullnetCost + varietyCost

    return [totalcost, utilityRatio, flexRatio]


def checkBoundary(pattern: Pattern, space: TwoDimSpace):
    """check if a pattern is completely in the space and not too close to the boundary"""
    if isinstance(pattern, EmptyPattern):
        return pattern.boundbox.intersects(space.boundbox) and (not pattern.boundbox.intersects(space.boundary))
    elif isinstance(pattern, WebPattern) or isinstance(pattern, StarPattern):
        return pattern.boundbox.intersects(space.boundbox) and (not pattern.boundbox.intersects(
            space.boundary)) and pattern.boundbox.distance(space.boundary) > SPACE_BUFFER - SHELF_MAX_WIDTH
    return pattern.boundbox.intersects(space.boundbox) and (not pattern.boundbox.intersects(
        space.boundary)) and pattern.boundbox.distance(space.boundary) > SPACE_BUFFER


def checkIntersect(pattern: Pattern, patternList: list):
    """check if a pattern doesn't intersect with other patterns"""
    for target in patternList:
        if pattern != target:
            if pattern.boundbox.intersects(target.boundbox):
                return False
    return True


@jit(nopython=True)
def ifLineIntersect(min1: float, max1: float, min2: float, max2: float):
    if max1 > min2 + ROAD_WIDTH / 4 and max2 > min1 + ROAD_WIDTH / 4:
        return True
    return False


def lineIntersect(min1: float, max1: float, min2: float, max2: float):
    if max1 > min2 + DELTA and max2 > min1 + DELTA:
        return [max(min1, min2), min(max1, max2)]
    return [None, None]


def buildWallPatterns(patternList: list, space: TwoDimSpace):
    wallPatterns = []
    for k in range(len(patternList)):
        pattern = patternList[k]
        type = pattern.type
        if type == WEB or type == STAR or type == EMPTY:
            continue
        xmin, xmax, ymin, ymax = pattern.boundbox.bounds[0] + ROAD_WIDTH / 2, pattern.boundbox.bounds[
            2] - ROAD_WIDTH / 2, pattern.boundbox.bounds[1] + ROAD_WIDTH / 2, pattern.boundbox.bounds[3] - ROAD_WIDTH / 2
        for i in range(len(space.columns)):
            col = space.columns[i]
            line = LineString([(col.x, col.ymin), (col.x, col.ymax)])
            dis = pattern.boundbox.distance(line)
            if dis > SPACE_BUFFER + ROAD_WIDTH / 4:
                continue
            if ifLineIntersect(col.ymin, col.ymax, ymin, ymax):
                interval = lineIntersect(col.ymin, col.ymax, ymin, ymax)
                length = interval[1] - interval[0]
                center = np.array([col.x + SHELF_MAX_WIDTH / 2,
                                   (interval[1] + interval[0]) / 2]) if col.towards == X_POS else np.array(
                                       [col.x - SHELF_MAX_WIDTH / 2, (interval[1] + interval[0]) / 2])
                wallPatterns.append(WallPattern(center, length, type, 1, col.towards, k))
        for i in range(len(space.rows)):
            row = space.rows[i]
            line = LineString([(row.xmin, row.y), (row.xmax, row.y)])
            dis = pattern.boundbox.distance(line)
            if dis > SPACE_BUFFER + ROAD_WIDTH / 4:
                continue
            if ifLineIntersect(row.xmin, row.xmax, xmin, xmax):
                interval = lineIntersect(row.xmin, row.xmax, xmin, xmax)
                length = interval[1] - interval[0]
                center = np.array([
                    (interval[1] + interval[0]) / 2, row.y + SHELF_MAX_WIDTH / 2
                ]) if row.towards == Y_POS else np.array([(interval[1] + interval[0]) / 2, row.y - SHELF_MAX_WIDTH / 2])
                wallPatterns.append(WallPattern(center, length, type, 0, row.towards, k))
    return wallPatterns


def probabilitiesAdjust(utilityRatio: float, flexRatio: float, patternNumber: int):
    """automatically adjust actionProbabilities due to current context"""
    list = None
    if patternNumber == 0:
        list = [0, 0, 1, 0, 0]
    else:
        portion = 0.9 - 0.2 * (PATTERN_LIMIT - min(patternNumber, PATTERN_LIMIT)) / (PATTERN_LIMIT - 1)
        addPortion = 1 - 0.7 * min(utilityRatio + flexRatio, 0.2) / 0.2
        list = [
            0.3 * portion * (0.5 + 0.5 * portion), 0.7 * portion * (0.5 + 0.5 * portion), addPortion * (1 - portion),
            (1 - addPortion) * (1 - portion), 0.5 * (1 - portion) * portion
        ]
    for i in range(1, len(list)):
        list[i] += list[i - 1]
    return list


def removeEdge(net: nx.Graph, n1: int, n2: int):
    if net.has_edge(n1, n2):
        net.remove_edge(n1, n2)


def addEdge(net: nx.Graph, n1: int, n2: int):
    if not net.has_edge(n1, n2):
        net.add_edge(n1, n2)


def mergeCol(net: nx.Graph, columns: list, col1: int, col2: int, nodes: list):
    c1 = columns[col1]
    c2 = columns[col2]
    num1 = c1.number
    num2 = c2.number
    ymax1 = max(c1.ymax, c2.ymax)
    ymin2 = min(c1.ymin, c2.ymin)
    len1 = c1.ymax - c1.ymin
    len2 = c2.ymax - c2.ymin
    xmerge = (c1.x * len1 + c2.x * len2) / (len1 + len2)

    for i in range(len(c1.vector)):
        if i < len(c1.vector) - 1:
            removeEdge(net, c1.vector[i], c1.vector[i + 1])
    for i in range(len(c2.vector)):
        if i < len(c2.vector) - 1:
            removeEdge(net, c2.vector[i], c2.vector[i + 1])
    allnodes = []
    index1, index2 = 0, 0
    while True:
        if index1 >= len(c1.vector) and index2 >= len(c2.vector):
            break
        elif index1 >= len(c1.vector):
            allnodes.append(nodes[c2.vector[index2]])
            index2 += 1
        elif index2 >= len(c2.vector):
            allnodes.append(nodes[c1.vector[index1]])
            index1 += 1
        else:
            if nodes[c1.vector[index1]].y < nodes[c2.vector[index2]].y:
                allnodes.append(nodes[c1.vector[index1]])
                index1 += 1
            else:
                allnodes.append(nodes[c2.vector[index2]])
                index2 += 1
    col1Indexes = []
    col2Indexes = []
    flagNum1 = allnodes[-1].column
    flagNum2 = allnodes[0].column
    ymin1 = 0
    ymax2 = 0
    for i in range(len(allnodes)):
        index1 = allnodes[i].number
        if i < len(allnodes) - 1:
            index2 = allnodes[i + 1].number
            addEdge(net, index1, index2)  # update net
        nodes[index1].x = xmerge  # update nodes

    # build new columns
    stop1, stop2 = 0, 0
    for i in range(len(allnodes) - 1, -1, -1):
        col1Indexes.append(allnodes[i].number)
        if allnodes[i].column != flagNum1:
            ymin1 = allnodes[i].y
            stop1 = i
            break
    for i in range(len(allnodes)):
        col2Indexes.append(allnodes[i].number)
        if allnodes[i].column != flagNum2:
            ymax2 = allnodes[i].y
            stop2 = i
            break
    for j in range(len(allnodes) - 1, stop1 - 1, -1):
        nodes[allnodes[j].number].column = num1
    for j in range(stop2 + 1):
        nodes[allnodes[j].number].column = num2

    # update columns
    columns[col1].x = xmerge
    columns[col1].ymax = ymax1
    columns[col1].ymin = ymin1
    columns[col1].vector = col1Indexes
    columns[col2].x = xmerge
    columns[col2].ymax = ymax2
    columns[col2].ymin = ymin2
    columns[col2].vector = col2Indexes


def mergeRow(net: nx.Graph, rows: list, row1: int, row2: int, nodes: list):
    r1 = rows[row1]
    r2 = rows[row2]
    num1 = r1.number
    num2 = r2.number
    xmax1 = max(r1.xmax, r2.xmax)
    xmin2 = min(r1.xmin, r2.xmin)
    len1 = r1.xmax - r1.xmin
    len2 = r2.xmax - r2.xmin
    ymerge = (r1.y * len1 + r2.y * len2) / (len1 + len2)
    for i in range(len(r1.vector)):
        if i < len(r1.vector) - 1:
            removeEdge(net, r1.vector[i], r1.vector[i + 1])
    for i in range(len(r2.vector)):
        if i < len(r2.vector) - 1:
            removeEdge(net, r2.vector[i], r2.vector[i + 1])
    allnodes = []
    index1, index2 = 0, 0
    while True:
        if index1 >= len(r1.vector) and index2 >= len(r2.vector):
            break
        elif index1 >= len(r1.vector):
            allnodes.append(nodes[r2.vector[index2]])
            index2 += 1
        elif index2 >= len(r2.vector):
            allnodes.append(nodes[r1.vector[index1]])
            index1 += 1
        else:
            if nodes[r1.vector[index1]].x < nodes[r2.vector[index2]].x:
                allnodes.append(nodes[r1.vector[index1]])
                index1 += 1
            else:
                allnodes.append(nodes[r2.vector[index2]])
                index2 += 1
    row1Indexes = []
    row2Indexes = []
    flagNum1 = allnodes[-1].row
    flagNum2 = allnodes[0].row
    xmin1 = 0
    xmax2 = 0
    for i in range(len(allnodes)):
        index1 = allnodes[i].number
        if i < len(allnodes) - 1:
            index2 = allnodes[i + 1].number
            addEdge(net, index1, index2)  # update net
        nodes[index1].y = ymerge  # update nodes

    # build new rows
    stop1, stop2 = 0, 0
    for i in range(len(allnodes) - 1, -1, -1):
        row1Indexes.append(allnodes[i].number)
        if allnodes[i].row != flagNum1:
            xmin1 = allnodes[i].x
            stop1 = i
            break
    for i in range(len(allnodes)):
        row2Indexes.append(allnodes[i].number)
        if allnodes[i].row != flagNum2:
            xmax2 = allnodes[i].x
            stop2 = i
            break
    for j in range(len(allnodes) - 1, stop1 - 1, -1):
        nodes[allnodes[j].number].row = num1
    for j in range(stop2 + 1):
        nodes[allnodes[j].number].row = num2

    # update rows
    rows[row1].y = ymerge
    rows[row1].xmax = xmax1
    rows[row1].xmin = xmin1
    rows[row1].vector = row1Indexes
    rows[row2].y = ymerge
    rows[row2].xmax = xmax2
    rows[row2].xmin = xmin2
    rows[row2].vector = row2Indexes


def updateCol(columns: list, nodes: list):
    for i in range(len(columns)):
        columns[i].x = nodes[columns[i].vector[0]].x
        y1 = nodes[columns[i].vector[0]].y
        y2 = nodes[columns[i].vector[-1]].y
        if y1 >= y2:
            columns[i].vector.reverse()
        columns[i].ymax = max(y1, y2)
        columns[i].ymin = min(y1, y2)


def updateRow(rows: list, nodes: list):
    for i in range(len(rows)):
        rows[i].y = nodes[rows[i].vector[0]].y
        x1 = nodes[rows[i].vector[0]].x
        x2 = nodes[rows[i].vector[-1]].x
        if x1 >= x2:
            rows[i].vector.reverse()
        rows[i].xmax = max(x1, x2)
        rows[i].xmin = min(x1, x2)


def addColumn(columns: list, nodes: list, base: int, n1: int, n2: int):
    columns.append(Column([n1, n2], nodes[n1].x, 0, 0, base))
    nodes[n1].column = base
    nodes[n2].column = base


def addColumn3(columns: list, nodes: list, base: int, n1: int, n2: int, n3: int):
    columns.append(Column([n1, n2, n3], nodes[n1].x, 0, 0, base))
    nodes[n1].column = base
    nodes[n2].column = base
    nodes[n3].column = base


def addColumn4(columns: list, nodes: list, base: int, n1: int, n2: int, n3: int, n4: int):
    columns.append(Column([n1, n2, n3, n4], nodes[n1].x, 0, 0, base))
    nodes[n1].column = base
    nodes[n2].column = base
    nodes[n3].column = base
    nodes[n4].column = base


def addRow(rows: list, nodes: list, base: int, n1: int, n2: int):
    rows.append(Row([n1, n2], nodes[n1].y, 0, 0, base))
    nodes[n1].row = base
    nodes[n2].row = base


def addRow3(rows: list, nodes: list, base: int, n1: int, n2: int, n3: int):
    rows.append(Row([n1, n2, n3], nodes[n1].y, 0, 0, base))
    nodes[n1].row = base
    nodes[n2].row = base
    nodes[n3].row = base


def addRow4(rows: list, nodes: list, base: int, n1: int, n2: int, n3: int, n4: int):
    rows.append(Row([n1, n2, n3, n4], nodes[n1].y, 0, 0, base))
    nodes[n1].row = base
    nodes[n2].row = base
    nodes[n3].row = base
    nodes[n4].row = base


def addIncline(inclines: list, nodes: list, base: int, n1: int, n2: int):
    inclines.append(Incline([n1, n2], base))
    if nodes[n1].incline1 == -1:
        nodes[n1].incline1 = base
    else:
        nodes[n1].incline2 = base
    if nodes[n2].incline1 == -1:
        nodes[n2].incline1 = base
    else:
        nodes[n2].incline2 = base


def buildNet(patternList: list, space: TwoDimSpace):
    nodes = []
    columns = []
    rows = []
    inclines = []
    emptyCenters = []
    emptyBoundboxes = []
    net = nx.Graph()
    nodes.append(Node(space.entrancePoint[0], space.entrancePoint[1], 0))
    nodes.append(Node(space.exitPoint[0], space.exitPoint[1], 1))
    net.add_node(0)
    net.add_node(1)

    # build basic
    for pattern in patternList:
        nodeBase = len(nodes)
        colBase = len(columns)
        rowBase = len(rows)
        incBase = len(inclines)
        if isinstance(pattern, LinePattern) or isinstance(pattern, GridPattern) or (isinstance(pattern, RoundPattern)
                                                                                    and pattern.doubleLayer == False):
            xs, ys = [], []
            if isinstance(pattern, LinePattern):
                if pattern.orient == 0:
                    xs = [
                        pattern.centerPoint[0] - pattern.length / 2 - ROAD_WIDTH / 2,
                        pattern.centerPoint[0] + pattern.length / 2 + ROAD_WIDTH / 2
                    ]
                    ys = [
                        pattern.centerPoint[1] - SHELF_MAX_WIDTH * 2 - ROAD_WIDTH, pattern.centerPoint[1],
                        pattern.centerPoint[1] + SHELF_MAX_WIDTH * 2 + ROAD_WIDTH
                    ]
                else:
                    xs = [
                        pattern.centerPoint[0] - SHELF_MAX_WIDTH * 2 - ROAD_WIDTH, pattern.centerPoint[0],
                        pattern.centerPoint[0] + SHELF_MAX_WIDTH * 2 + ROAD_WIDTH
                    ]
                    ys = [
                        pattern.centerPoint[1] - pattern.length / 2 - ROAD_WIDTH / 2,
                        pattern.centerPoint[1] + pattern.length / 2 + ROAD_WIDTH / 2
                    ]
            elif isinstance(pattern, GridPattern):
                xs = pattern.xroads
                ys = pattern.yroads
            elif isinstance(pattern, RoundPattern):
                xs = [
                    pattern.centerPoint[0] - pattern.width / 2 - ROAD_WIDTH / 2,
                    pattern.centerPoint[0] + pattern.width / 2 + ROAD_WIDTH / 2
                ]
                ys = [
                    pattern.centerPoint[1] - pattern.height / 2 - ROAD_WIDTH / 2,
                    pattern.centerPoint[1] + pattern.height / 2 + ROAD_WIDTH / 2
                ]
            xlen = len(xs)
            ylen = len(ys)
            # add points
            for i in range(xlen):
                for j in range(ylen):
                    net.add_node(nodeBase + i * ylen + j)
                    nodes.append(Node(xs[i], ys[j], nodeBase + i * ylen + j))
            # add columns
            columns.append(Column([j for j in range(nodeBase, nodeBase + ylen)], xs[0], ys[0], ys[ylen - 1], colBase))
            columns.append(
                Column([j for j in range(nodeBase + (xlen - 1) * ylen, nodeBase + (xlen - 1) * ylen + ylen)],
                       xs[xlen - 1], ys[0], ys[ylen - 1], colBase + 1))
            # add rows
            rows.append(Row([nodeBase + j * ylen for j in range(xlen)], ys[0], xs[0], xs[xlen - 1], rowBase))
            rows.append(
                Row([nodeBase + ylen - 1 + j * ylen for j in range(xlen)], ys[ylen - 1], xs[0], xs[xlen - 1],
                    rowBase + 1))
            for i in range(xlen):  # connect points and tie points to columns and rows
                for j in range(ylen):
                    if i != xlen - 1:
                        addEdge(net, nodeBase + i * ylen + j, nodeBase + (i + 1) * ylen + j)
                    if j != ylen - 1:
                        addEdge(net, nodeBase + i * ylen + j, nodeBase + i * ylen + j + 1)
                    if i == 0:
                        nodes[nodeBase + i * ylen + j].column = colBase
                    elif i == xlen - 1:
                        nodes[nodeBase + i * ylen + j].column = colBase + 1
                    if j == 0:
                        nodes[nodeBase + i * ylen + j].row = rowBase
                    elif j == ylen - 1:
                        nodes[nodeBase + i * ylen + j].row = rowBase + 1
        elif isinstance(pattern, RoundPattern):
            bx = pattern.centerPoint[0]
            by = pattern.centerPoint[1]
            cx = pattern.inCenter[0]
            cy = pattern.inCenter[1]
            xs = [bx - pattern.width / 2 - ROAD_WIDTH / 2, bx + pattern.width / 2 + ROAD_WIDTH / 2]
            ys = [by - pattern.height / 2 - ROAD_WIDTH / 2, by + pattern.height / 2 + ROAD_WIDTH / 2]
            xi = [
                bx - pattern.width / 2 + ROAD_WIDTH / 2 + SHELF_MAX_WIDTH * 2,
                bx + pattern.width / 2 - ROAD_WIDTH / 2 - SHELF_MAX_WIDTH * 2
            ]
            yi = [
                by - pattern.height / 2 + ROAD_WIDTH / 2 + SHELF_MAX_WIDTH * 2,
                by + pattern.height / 2 - ROAD_WIDTH / 2 - SHELF_MAX_WIDTH * 2
            ]
            # add points and edges
            for i in range(12):
                net.add_node(nodeBase + i)
            for i in range(2):
                for j in range(2):
                    nodes.append(Node(xs[j], ys[i], nodeBase + i * 2 + j))
            for i in range(2):
                for j in range(2):
                    nodes.append(Node(xi[j], yi[i], nodeBase + i * 2 + j + 4))
            for i in range(3):
                net.add_edge(nodeBase + i * 4, nodeBase + 1 + i * 4)
                net.add_edge(nodeBase + i * 4, nodeBase + 2 + i * 4)
                net.add_edge(nodeBase + 2 + i * 4, nodeBase + 3 + i * 4)
                net.add_edge(nodeBase + 1 + i * 4, nodeBase + 3 + i * 4)
            if pattern.inTowards == Y_POS:
                net.remove_edge(nodeBase, nodeBase + 1)
                net.remove_edge(nodeBase + 4, nodeBase + 5)
                net.remove_edge(nodeBase + 10, nodeBase + 11)
                net.add_edge(nodeBase, nodeBase + 8)
                net.add_edge(nodeBase + 1, nodeBase + 9)
                net.add_edge(nodeBase + 4, nodeBase + 10)
                net.add_edge(nodeBase + 5, nodeBase + 11)
                nodes.append(Node(cx - ROUND_IN_WIDTH / 2 + ROAD_WIDTH / 2, ys[0], nodeBase + 8))
                nodes.append(Node(cx + ROUND_IN_WIDTH / 2 - ROAD_WIDTH / 2, ys[0], nodeBase + 9))
                nodes.append(Node(cx - ROUND_IN_WIDTH / 2 + ROAD_WIDTH / 2, yi[0], nodeBase + 10))
                nodes.append(Node(cx + ROUND_IN_WIDTH / 2 - ROAD_WIDTH / 2, yi[0], nodeBase + 11))
                addRow4(rows, nodes, rowBase, nodeBase, nodeBase + 8, nodeBase + 9, nodeBase + 1)
                addRow(rows, nodes, rowBase + 1, nodeBase + 2, nodeBase + 3)
                addColumn(columns, nodes, colBase, nodeBase, nodeBase + 2)
                addColumn(columns, nodes, colBase + 1, nodeBase + 1, nodeBase + 3)
            elif pattern.inTowards == X_POS:
                net.remove_edge(nodeBase, nodeBase + 2)
                net.remove_edge(nodeBase + 4, nodeBase + 6)
                net.remove_edge(nodeBase + 9, nodeBase + 11)
                net.add_edge(nodeBase, nodeBase + 8)
                net.add_edge(nodeBase + 2, nodeBase + 10)
                net.add_edge(nodeBase + 4, nodeBase + 9)
                net.add_edge(nodeBase + 6, nodeBase + 11)
                nodes.append(Node(xs[0], cy - ROUND_IN_WIDTH / 2 + ROAD_WIDTH / 2, nodeBase + 8))
                nodes.append(Node(xi[0], cy - ROUND_IN_WIDTH / 2 + ROAD_WIDTH / 2, nodeBase + 9))
                nodes.append(Node(xs[0], cy + ROUND_IN_WIDTH / 2 - ROAD_WIDTH / 2, nodeBase + 10))
                nodes.append(Node(xi[0], cy + ROUND_IN_WIDTH / 2 - ROAD_WIDTH / 2, nodeBase + 11))
                addColumn4(columns, nodes, colBase, nodeBase, nodeBase + 8, nodeBase + 10, nodeBase + 2)
                addColumn(columns, nodes, colBase + 1, nodeBase + 1, nodeBase + 3)
                addRow(rows, nodes, rowBase, nodeBase, nodeBase + 1)
                addRow(rows, nodes, rowBase + 1, nodeBase + 2, nodeBase + 3)
            elif pattern.inTowards == Y_NEG:
                net.remove_edge(nodeBase + 2, nodeBase + 3)
                net.remove_edge(nodeBase + 6, nodeBase + 7)
                net.remove_edge(nodeBase + 8, nodeBase + 9)
                net.add_edge(nodeBase + 2, nodeBase + 10)
                net.add_edge(nodeBase + 3, nodeBase + 11)
                net.add_edge(nodeBase + 6, nodeBase + 8)
                net.add_edge(nodeBase + 7, nodeBase + 9)
                nodes.append(Node(cx - ROUND_IN_WIDTH / 2 + ROAD_WIDTH / 2, yi[1], nodeBase + 8))
                nodes.append(Node(cx + ROUND_IN_WIDTH / 2 - ROAD_WIDTH / 2, yi[1], nodeBase + 9))
                nodes.append(Node(cx - ROUND_IN_WIDTH / 2 + ROAD_WIDTH / 2, ys[1], nodeBase + 10))
                nodes.append(Node(cx + ROUND_IN_WIDTH / 2 - ROAD_WIDTH / 2, ys[1], nodeBase + 11))
                addRow4(rows, nodes, rowBase, nodeBase + 2, nodeBase + 10, nodeBase + 11, nodeBase + 3)
                addRow(rows, nodes, rowBase + 1, nodeBase, nodeBase + 1)
                addColumn(columns, nodes, colBase, nodeBase, nodeBase + 2)
                addColumn(columns, nodes, colBase + 1, nodeBase + 1, nodeBase + 3)
            else:
                net.remove_edge(nodeBase + 1, nodeBase + 3)
                net.remove_edge(nodeBase + 5, nodeBase + 7)
                net.remove_edge(nodeBase + 8, nodeBase + 10)
                net.add_edge(nodeBase + 1, nodeBase + 9)
                net.add_edge(nodeBase + 3, nodeBase + 11)
                net.add_edge(nodeBase + 5, nodeBase + 8)
                net.add_edge(nodeBase + 7, nodeBase + 10)
                nodes.append(Node(xi[1], cy - ROUND_IN_WIDTH / 2 + ROAD_WIDTH / 2, nodeBase + 8))
                nodes.append(Node(xs[1], cy - ROUND_IN_WIDTH / 2 + ROAD_WIDTH / 2, nodeBase + 9))
                nodes.append(Node(xi[1], cy + ROUND_IN_WIDTH / 2 - ROAD_WIDTH / 2, nodeBase + 10))
                nodes.append(Node(xs[1], cy + ROUND_IN_WIDTH / 2 - ROAD_WIDTH / 2, nodeBase + 11))
                addColumn4(columns, nodes, colBase, nodeBase + 1, nodeBase + 9, nodeBase + 11, nodeBase + 3)
                addColumn(columns, nodes, colBase + 1, nodeBase, nodeBase + 2)
                addRow(rows, nodes, rowBase, nodeBase, nodeBase + 1)
                addRow(rows, nodes, rowBase + 1, nodeBase + 2, nodeBase + 3)
        elif isinstance(pattern, WebPattern):
            bx = pattern.centerPoint[0]
            by = pattern.centerPoint[1]
            net.add_node(nodeBase)
            nodes.append(Node(bx, by, nodeBase))
            outNum = pattern.outNum
            rotate = pattern.rotate
            angle = pi / outNum
            # add points
            for i in range(len(pattern.roads)):
                outLen = (ROAD_WIDTH / 2 / sin(angle) + pattern.roads[i]) / cos(angle)
                for j in range(outNum):
                    net.add_node(nodeBase + i * outNum + j + 1)
                    nodes.append(
                        Node(bx + vec(outLen, rotate + j * 2 * angle)[0], by + vec(outLen, rotate + j * 2 * angle)[1],
                             nodeBase + i * outNum + j + 1))
            newBase = nodeBase + 1 + len(pattern.roads) * outNum
            for i in range(outNum):
                net.add_node(newBase + i)
                nodes.append(
                    Node(bx + vec(pattern.length + ROAD_WIDTH / 2 / cos(angle), rotate + i * 2 * angle)[0],
                         by + vec(pattern.length + ROAD_WIDTH / 2 / cos(angle), rotate + i * 2 * angle)[1],
                         newBase + i))
            # connect points
            for i in range(len(pattern.roads) + 1):
                for j in range(outNum):
                    addEdge(net, nodeBase + 1 + i * outNum + j, nodeBase + 1 + i * outNum + (j + 1) % outNum)
                    if i == 0:
                        addEdge(net, nodeBase + 1 + j, nodeBase)
                    else:
                        addEdge(net, nodeBase + 1 + i * outNum + j, nodeBase + 1 + (i - 1) * outNum + j)
            # add rows/columns/inclines
            if outNum == 3:
                addIncline(inclines, nodes, incBase, newBase, newBase + 1)
                addIncline(inclines, nodes, incBase + 1, newBase + 1, newBase + 2)
                if abs(rotate) < pi / 180 or abs(rotate - pi) < pi / 180:
                    addColumn(columns, nodes, colBase, newBase + 1, newBase + 2)
                else:
                    addRow(rows, nodes, rowBase, newBase + 1, newBase + 2)
            elif outNum == 4:
                if abs(rotate) < pi / 180:
                    for i in range(4):
                        addIncline(inclines, nodes, incBase + i, newBase + i, newBase + (i + 1) % 4)
                else:
                    addRow(rows, nodes, rowBase, newBase, newBase + 1)
                    addColumn(columns, nodes, colBase, newBase + 1, newBase + 2)
                    addRow(rows, nodes, rowBase + 1, newBase + 2, newBase + 3)
                    addColumn(columns, nodes, colBase + 1, newBase + 3, newBase)
            elif outNum == 5:
                addIncline(inclines, nodes, incBase, newBase, newBase + 1)
                addIncline(inclines, nodes, incBase + 1, newBase + 1, newBase + 2)
                addIncline(inclines, nodes, incBase + 2, newBase + 3, newBase + 4)
                addIncline(inclines, nodes, incBase + 3, newBase + 4, newBase)
                if abs(rotate) < pi / 180 or abs(rotate - pi) < pi / 180:
                    addColumn(columns, nodes, colBase, newBase + 2, newBase + 3)
                else:
                    addRow(rows, nodes, rowBase, newBase + 2, newBase + 3)
            elif outNum == 6:
                addIncline(inclines, nodes, incBase, newBase, newBase + 1)
                addIncline(inclines, nodes, incBase + 1, newBase + 2, newBase + 3)
                addIncline(inclines, nodes, incBase + 2, newBase + 3, newBase + 4)
                addIncline(inclines, nodes, incBase + 3, newBase + 5, newBase)
                if abs(rotate) < pi / 180:
                    addRow(rows, nodes, rowBase, newBase + 1, newBase + 2)
                    addRow(rows, nodes, rowBase + 1, newBase + 4, newBase + 5)
                else:
                    addColumn(columns, nodes, colBase, newBase + 1, newBase + 2)
                    addColumn(columns, nodes, colBase + 1, newBase + 4, newBase + 5)
        elif isinstance(pattern, StarPattern):
            bx = pattern.centerPoint[0]
            by = pattern.centerPoint[1]
            net.add_node(nodeBase)
            nodes.append(Node(bx, by, nodeBase))
            outNum = pattern.outNum
            rotate = pattern.rotate
            angle = pi / outNum
            width = (ROAD_WIDTH + SHELF_MAX_WIDTH * 2)
            outlen = tan(pi / 2 - angle) * width
            # add points
            newBase = nodeBase + 1
            for i in range(outNum):
                for j in range(4):
                    net.add_node(newBase + i * 4 + j)
                rot = rotate + i * 2 * angle
                nodes.append(
                    Node(bx + vec(pattern.length + ROAD_WIDTH / 2, rot)[0],
                         by + vec(pattern.length + ROAD_WIDTH / 2, rot)[1], newBase + i * 4))
                nodes.append(
                    Node(bx + vec(pattern.length + ROAD_WIDTH / 2, rot)[0] + vec(width, rot + pi / 2)[0],
                         by + vec(pattern.length + ROAD_WIDTH / 2, rot)[1] + vec(width, rot + pi / 2)[1],
                         newBase + i * 4 + 1))
                nodes.append(
                    Node(bx + vec(outlen, rot)[0] + vec(width, rot + pi / 2)[0],
                         by + vec(outlen, rot)[1] + vec(width, rot + pi / 2)[1], newBase + i * 4 + 2))
                nodes.append(
                    Node(
                        bx + vec(pattern.length + ROAD_WIDTH / 2, rot + 2 * angle)[0] +
                        vec(width, rot + 2 * angle - pi / 2)[0],
                        by + vec(pattern.length + ROAD_WIDTH / 2, rot + 2 * angle)[1] +
                        vec(width, rot + 2 * angle - pi / 2)[1], newBase + i * 4 + 3))
            # connect points
            for i in range(outNum):
                addEdge(net, nodeBase + 1 + i * 4, nodeBase + 1 + (i * 4 + 1))
                addEdge(net, nodeBase + 1 + i * 4 + 1, nodeBase + 1 + (i * 4 + 2))
                addEdge(net, nodeBase + 1 + i * 4 + 2, nodeBase + 1 + (i * 4 + 3))
                addEdge(net, nodeBase + 1 + i * 4 + 3, nodeBase + 1 + (i * 4 + 4) % (4 * outNum))
                addEdge(net, nodeBase + 1 + i * 4, nodeBase)
            # add rows/columns/inclines
            if outNum == 3:
                for i in range(2, 10):
                    addIncline(inclines, nodes, incBase + i - 2, newBase + i, newBase + i + 1)
                if abs(rotate) < pi / 180 or abs(rotate - pi) < pi / 180:
                    addColumn3(columns, nodes, colBase, newBase + 11, newBase, newBase + 1)
                    addRow(rows, nodes, rowBase, newBase + 1, newBase + 2)
                    addRow(rows, nodes, rowBase + 1, newBase + 10, newBase + 11)
                else:
                    addRow3(rows, nodes, rowBase, newBase + 11, newBase, newBase + 1)
                    addColumn(columns, nodes, colBase, newBase + 1, newBase + 2)
                    addColumn(columns, nodes, colBase + 1, newBase + 10, newBase + 11)
            elif outNum == 4:
                if abs(rotate) < pi / 180:
                    for i in range(2):
                        addColumn(columns, nodes, colBase + 3 * i, newBase + i * 8 + 2, newBase + i * 8 + 3)
                        addColumn(columns, nodes, colBase + 3 * i + 1, newBase + i * 8 + 5, newBase + i * 8 + 6)
                        addColumn3(columns, nodes, colBase + 3 * i + 2, newBase + (i * 8 + 15) % 16, newBase + i * 8,
                                   newBase + i * 8 + 1)
                        addRow(rows, nodes, rowBase + 3 * i, newBase + i * 8 + 1, newBase + i * 8 + 2)
                        addRow(rows, nodes, rowBase + 3 * i + 1, newBase + i * 8 + 6, newBase + i * 8 + 7)
                        addRow3(rows, nodes, rowBase + 3 * i + 2, newBase + i * 8 + 3, newBase + i * 8 + 4,
                                newBase + i * 8 + 5)
                else:
                    for i in range(16):
                        addIncline(inclines, nodes, incBase + i, newBase + i, newBase + (i + 1) % 4)
            elif outNum == 5:
                for i in range(2, 18):
                    addIncline(inclines, nodes, incBase + i - 2, newBase + i, newBase + i + 1)
                if abs(rotate) < pi / 180 or abs(rotate - pi) < pi / 180:
                    addColumn3(columns, nodes, colBase, newBase + 19, newBase, newBase + 1)
                    addRow(rows, nodes, rowBase, newBase + 1, newBase + 2)
                    addRow(rows, nodes, rowBase + 1, newBase + 18, newBase + 19)
                else:
                    addRow3(rows, nodes, rowBase, newBase + 19, newBase, newBase + 1)
                    addColumn(columns, nodes, colBase, newBase + 1, newBase + 2)
                    addColumn(columns, nodes, colBase + 1, newBase + 18, newBase + 19)
            elif outNum == 6:
                for i in range(2, 10):
                    addIncline(inclines, nodes, incBase + i - 2, newBase + i, newBase + i + 1)
                for i in range(14, 22):
                    addIncline(inclines, nodes, incBase + i - 6, newBase + i, newBase + i + 1)
                if abs(rotate) < pi / 180:
                    addColumn3(columns, nodes, colBase, newBase + 23, newBase, newBase + 1)
                    addColumn3(columns, nodes, colBase + 1, newBase + 11, newBase + 12, newBase + 13)
                    addRow(rows, nodes, rowBase, newBase + 1, newBase + 2)
                    addRow(rows, nodes, rowBase + 1, newBase + 10, newBase + 11)
                    addRow(rows, nodes, rowBase + 2, newBase + 13, newBase + 14)
                    addRow(rows, nodes, rowBase + 3, newBase + 22, newBase + 23)
                else:
                    addRow3(rows, nodes, rowBase, newBase + 23, newBase, newBase + 1)
                    addRow3(rows, nodes, rowBase + 1, newBase + 11, newBase + 12, newBase + 13)
                    addColumn(columns, nodes, colBase, newBase + 1, newBase + 2)
                    addColumn(columns, nodes, colBase + 1, newBase + 10, newBase + 11)
                    addColumn(columns, nodes, colBase + 2, newBase + 13, newBase + 14)
                    addColumn(columns, nodes, colBase + 3, newBase + 22, newBase + 23)
        elif isinstance(pattern, EmptyPattern):
            net.add_node(nodeBase)
            nodes.append(Node(pattern.centerPoint[0], pattern.centerPoint[1], nodeBase))
            emptyCenters.append(nodeBase)
            emptyBoundboxes.append(pattern.boundbox)

    # merge
    mergeFlag = True
    while mergeFlag:
        mergeFlag = False
        # merge columns
        updateCol(columns, nodes)
        columns = sorted(columns, key=cmp_to_key(colCmp))
        for i in range(len(columns) - 1):
            for j in range(i + 1, len(columns)):
                if abs(columns[i].x - columns[j].x) < ROAD_WIDTH / 2:
                    if ifLineIntersect(columns[i].ymin, columns[i].ymax, columns[j].ymin, columns[j].ymax):
                        mergeCol(net, columns, i, j, nodes)
                        mergeFlag = True
                        break
                else:
                    break
        # merge rows
        updateRow(rows, nodes)
        rows = sorted(rows, key=cmp_to_key(rowCmp))
        for i in range(len(rows) - 1):
            for j in range(i + 1, len(rows)):
                if abs(rows[i].y - rows[j].y) < ROAD_WIDTH / 2:
                    if ifLineIntersect(rows[i].xmin, rows[i].xmax, rows[j].xmin, rows[j].xmax):
                        mergeRow(net, rows, i, j, nodes)
                        mergeFlag = True
                        break
                else:
                    break

    # reorder columns and rows
    updateCol(columns, nodes)
    updateRow(rows, nodes)
    columns = sorted(columns, key=cmp_to_key(colNumberCmp))
    rows = sorted(rows, key=cmp_to_key(rowNumberCmp))

    # get all rings
    rings = []
    ringNodes = []
    polygons = []
    columnFlags = [False for i in range(len(columns))]
    rowFlags = [False for i in range(len(rows))]
    for i in range(len(columns)):
        if not columnFlags[i]:
            origin = i
            nowCol = i
            nowRow = 0
            nowIncline = 0
            nowPoints = []
            nods = []
            nowNode = columns[nowCol].vector[0]
            cur = 0  # 0 for column, 1 for row, 2 for incline
            while True:
                if cur == 0:
                    columnFlags[nowCol] = True
                    col = columns[nowCol]
                    if nowNode == col.vector[0]:
                        nowNode = col.vector[-1]
                        for j in range(len(col.vector) - 1):
                            nod = nodes[col.vector[j]]
                            nods.append(nod)
                            nowPoints.append(np.array([nod.x, nod.y]))
                    else:
                        nowNode = col.vector[0]
                        for j in range(len(col.vector) - 1, 0, -1):
                            nod = nodes[col.vector[j]]
                            nods.append(nod)
                            nowPoints.append(np.array([nod.x, nod.y]))
                    nowRow = nodes[nowNode].row
                    if nowRow == -1:
                        nowIncline = nodes[nowNode].incline1
                        cur = 2
                    else:
                        cur = 1
                elif cur == 1:
                    rowFlags[nowRow] = True
                    row = rows[nowRow]
                    if nowNode == row.vector[0]:
                        nowNode = row.vector[-1]
                        for j in range(len(row.vector) - 1):
                            nod = nodes[row.vector[j]]
                            nods.append(nod)
                            nowPoints.append(np.array([nod.x, nod.y]))
                    else:
                        nowNode = row.vector[0]
                        for j in range(len(row.vector) - 1, 0, -1):
                            nod = nodes[row.vector[j]]
                            nods.append(nod)
                            nowPoints.append(np.array([nod.x, nod.y]))
                    nowCol = nodes[nowNode].column
                    if nowCol == -1:
                        nowIncline = nodes[nowNode].incline1
                        cur = 2
                    else:
                        cur = 0
                    if cur == 0 and nowCol == origin:  # a circle
                        break
                else:
                    inc = inclines[nowIncline]
                    nod = None
                    if nowNode == inc.vector[0]:
                        nowNode = inc.vector[1]
                        nod = nodes[inc.vector[0]]
                    else:
                        nowNode = inc.vector[0]
                        nod = nodes[inc.vector[1]]
                    nods.append(nod)
                    nowPoints.append(np.array([nod.x, nod.y]))
                    if nodes[nowNode].column != -1:
                        nowCol = nodes[nowNode].column
                        cur = 0
                    elif nodes[nowNode].row != -1:
                        nowRow = nodes[nowNode].row
                        cur = 1
                    else:
                        if nodes[nowNode].incline1 == nowIncline:
                            nowIncline = nodes[nowNode].incline2
                        else:
                            nowIncline = nodes[nowNode].incline1
                        cur = 2
                    if cur == 0 and nowCol == origin:  # a circle
                        break

            if len(nowPoints) < 3:  # actually a point
                continue

            ring = LinearRing(nowPoints)
            poly = Polygon(ring)
            if poly.is_valid:
                rings.append(ring)
                ringNodes.append(nods)
                polygons.append(poly)

    # remove inner rings
    index = 0
    while index < len(rings):
        removeFlag = False
        for i in range(len(rings)):
            if i != index and polygons[i].contains(rings[index]):
                removeFlag = True
                break
        if removeFlag:
            rings.remove(rings[index])
            ringNodes.remove(ringNodes[index])
            polygons.remove(polygons[index])
        else:
            index += 1

    # connect entrance and exit
    for i in range(2):
        point = Point([nodes[i].x, nodes[i].y])
        for j in range(len(emptyCenters)):
            p2 = Point(nodes[emptyCenters[j]].x, nodes[emptyCenters[j]].y)
            line = LineString([point, p2])
            if line.length < FAR_CONNECT_DISTANCE:
                acceptFlag = True
                for k in range(len(polygons)):
                    if line.crosses(polygons[k]):
                        acceptFlag = False
                        break
                if acceptFlag:
                    for k in range(len(emptyBoundboxes)):
                        if k != j and line.crosses(emptyBoundboxes[k]):
                            acceptFlag = False
                            break
                if acceptFlag:
                    addEdge(net, i, emptyCenters[j])
        for j in range(len(rings)):
            ring = rings[j]
            dis = ring.project(point)
            projectPoint = Point(ring.interpolate(dis))
            line = LineString([point, projectPoint])
            if line.length < FAR_CONNECT_DISTANCE:
                acceptFlag = True
                for k in range(len(polygons)):
                    if k != j and line.crosses(polygons[k]):
                        acceptFlag = False
                        break
                if acceptFlag:
                    for emptyBound in emptyBoundboxes:
                        if line.crosses(emptyBound):
                            acceptFlag = False
                            break
                if acceptFlag:
                    clen = len(ring.coords) - 1
                    coords = [Point(ring.coords[k]) for k in range(clen)]
                    coord_nodes = ringNodes[j]
                    k1 = clen - 1
                    k2 = 0
                    for k in range(clen):
                        if ring.project(coords[k]) > dis:
                            k2 = k
                            k1 = k - 1
                            break
                    dis1 = abs(ring.project(coords[k1]) - dis)
                    dis2 = abs(ring.project(coords[k2]) - dis) if k2 > 0 else abs(ring.length - dis)
                    if dis1 < MERGE_THRESHOLD and dis1 < dis2:
                        addEdge(net, i, ringNodes[j][k1].number)
                        continue
                    elif dis2 < MERGE_THRESHOLD and dis2 <= dis1:
                        addEdge(net, i, ringNodes[j][k2].number)
                        continue
                    else:
                        nodeBase = len(nodes)
                        nodes.append(Node(projectPoint.x, projectPoint.y, nodeBase))
                        net.add_node(nodeBase)
                        addEdge(net, i, nodeBase)
                        removeEdge(net, coord_nodes[k1].number, coord_nodes[k2].number)
                        addEdge(net, coord_nodes[k1].number, nodeBase)
                        addEdge(net, coord_nodes[k2].number, nodeBase)
                        coords.insert(k1 + 1, projectPoint)
                        rings[j] = LinearRing(coords + [Point(ring.coords[clen])])
                        ringNodes[j].insert(k1 + 1, nodes[nodeBase])

    # connect emptypatterns
    for i in range(len(emptyCenters)):
        point = Point(nodes[emptyCenters[i]].x, nodes[emptyCenters[i]].y)
        for j in range(i + 1, len(emptyCenters)):
            p2 = Point(nodes[emptyCenters[j]].x, nodes[emptyCenters[j]].y)
            line = LineString([point, p2])
            if line.length < CONNECT_DISTANCE:
                acceptFlag = True
                for k in range(len(polygons)):
                    if line.crosses(polygons[k]):
                        acceptFlag = False
                        break
                if acceptFlag:
                    for k in range(len(emptyBoundboxes)):
                        if k != i and k != j and line.crosses(emptyBoundboxes[k]):
                            acceptFlag = False
                            break
                if acceptFlag:
                    addEdge(net, emptyCenters[i], emptyCenters[j])
        for j in range(len(rings)):
            ring = rings[j]
            dis = ring.project(point)
            projectPoint = Point(ring.interpolate(dis))
            line = LineString([point, projectPoint])
            if line.length < CONNECT_DISTANCE:
                acceptFlag = True
                for k in range(len(polygons)):
                    if k != j and line.crosses(polygons[k]):
                        acceptFlag = False
                        break
                if acceptFlag:
                    for k in range(len(emptyBoundboxes)):
                        if k != i and line.crosses(emptyBoundboxes[k]):
                            acceptFlag = False
                            break
                if acceptFlag:
                    clen = len(ring.coords) - 1
                    coords = [Point(ring.coords[k]) for k in range(clen)]
                    coord_nodes = ringNodes[j]
                    k1 = clen - 1
                    k2 = 0
                    for k in range(clen):
                        if ring.project(coords[k]) > dis:
                            k2 = k
                            k1 = k - 1
                            break
                    dis1 = abs(ring.project(coords[k1]) - dis)
                    dis2 = abs(ring.project(coords[k2]) - dis) if k2 > 0 else abs(ring.length - dis)
                    if dis1 < MERGE_THRESHOLD and dis1 < dis2:
                        addEdge(net, emptyCenters[i], ringNodes[j][k1].number)
                        continue
                    elif dis2 < MERGE_THRESHOLD and dis2 <= dis1:
                        addEdge(net, emptyCenters[i], ringNodes[j][k2].number)
                        continue
                    else:
                        nodeBase = len(nodes)
                        nodes.append(Node(projectPoint.x, projectPoint.y, nodeBase))
                        net.add_node(nodeBase)
                        addEdge(net, emptyCenters[i], nodeBase)
                        removeEdge(net, coord_nodes[k1].number, coord_nodes[k2].number)
                        addEdge(net, coord_nodes[k1].number, nodeBase)
                        addEdge(net, coord_nodes[k2].number, nodeBase)
                        coords.insert(k1 + 1, projectPoint)
                        rings[j] = LinearRing(coords + [Point(ring.coords[clen])])
                        ringNodes[j].insert(k1 + 1, nodes[nodeBase])

    # connect rings
    for i in range(len(rings)):
        for j in range(i + 1, len(rings)):
            ring1 = rings[i]
            ring2 = rings[j]
            points = nearest_points(ring1, ring2)
            d1 = ring1.project(points[1])
            d2 = ring2.project(points[0])
            p1 = Point(ring1.interpolate(d1))
            p2 = Point(ring2.interpolate(d2))
            line = LineString([p1, p2])
            if line.length < CONNECT_DISTANCE:
                acceptFlag = True
                for k in range(len(polygons)):
                    if k != i and k != j and line.crosses(polygons[k]):
                        acceptFlag = False
                        break
                if acceptFlag:
                    for emptyBound in emptyBoundboxes:
                        if line.crosses(emptyBound):
                            acceptFlag = False
                            break
                if acceptFlag:
                    clen = len(ring1.coords) - 1
                    coords = [Point(ring1.coords[k]) for k in range(clen)]
                    coord_nodes = ringNodes[i]
                    k1 = clen - 1
                    k2 = 0
                    for k in range(clen):
                        if ring1.project(coords[k]) > d1:
                            k2 = k
                            k1 = k - 1
                            break
                    dis1 = abs(ring1.project(coords[k1]) - d1)
                    dis2 = abs(ring1.project(coords[k2]) - d1) if k2 > 0 else abs(ring1.length - d1)
                    con1 = None
                    if dis1 < MERGE_THRESHOLD and dis1 < dis2:
                        con1 = coord_nodes[k1].number
                    elif dis2 < MERGE_THRESHOLD and dis2 <= dis1:
                        con1 = coord_nodes[k2].number
                    else:
                        nodeBase = len(nodes)
                        con1 = nodeBase
                        nodes.append(Node(p1.x, p1.y, nodeBase))
                        net.add_node(nodeBase)
                        removeEdge(net, coord_nodes[k1].number, coord_nodes[k2].number)
                        addEdge(net, coord_nodes[k1].number, nodeBase)
                        addEdge(net, coord_nodes[k2].number, nodeBase)
                        coords.insert(k1 + 1, p1)
                        rings[i] = LinearRing(coords + [Point(ring1.coords[clen])])
                        ringNodes[i].insert(k1 + 1, nodes[nodeBase])

                    clen = len(ring2.coords) - 1
                    coords = [Point(ring2.coords[k]) for k in range(clen)]
                    coord_nodes = ringNodes[j]
                    k1 = clen - 1
                    k2 = 0
                    if clen != len(coord_nodes):
                        print(clen)
                        for k in coords:
                            print((str)(k.x) + ' ' + (str)(k.y))
                        print(len(coord_nodes))
                        for k in coord_nodes:
                            print((str)(k.x) + ' ' + (str)(k.y))
                        assert (False)
                    for k in range(clen):
                        if ring2.project(coords[k]) > d2:
                            k2 = k
                            k1 = k - 1
                            break
                    dis1 = abs(ring2.project(coords[k1]) - d2)
                    dis2 = abs(ring2.project(coords[k2]) - d2) if k2 > 0 else abs(ring2.length - d2)
                    if dis1 < MERGE_THRESHOLD and dis1 < dis2:
                        addEdge(net, con1, coord_nodes[k1].number)
                    elif dis2 < MERGE_THRESHOLD and dis2 <= dis1:
                        addEdge(net, con1, coord_nodes[k2].number)
                    else:
                        nodeBase = len(nodes)
                        addEdge(net, con1, nodeBase)
                        nodes.append(Node(p2.x, p2.y, nodeBase))
                        net.add_node(nodeBase)
                        removeEdge(net, coord_nodes[k1].number, coord_nodes[k2].number)
                        addEdge(net, coord_nodes[k1].number, nodeBase)
                        addEdge(net, coord_nodes[k2].number, nodeBase)
                        coords.insert(k1 + 1, p2)
                        rings[j] = LinearRing(coords + [Point(ring2.coords[clen])])
                        ringNodes[j].insert(k1 + 1, nodes[nodeBase])

    # set positions
    for node in net.nodes:
        net.nodes[node]['x'] = nodes[node].x
        net.nodes[node]['y'] = nodes[node].y
        removeEdge(net, node, node)
    # calculate length
    for edge in net.edges:
        length = Point([nodes[edge[0]].x, nodes[edge[0]].y]).distance(Point([nodes[edge[1]].x, nodes[edge[1]].y]))
        net[edge[0]][edge[1]]['length'] = length
    # merge points
    while len(net.edges) > 0:
        n1, n2 = None, None
        mindis = 10000
        for edge in net.edges:
            if net[edge[0]][edge[1]]['length'] < DELTA:
                n1 = edge[0]
                n2 = edge[1]
                mindis = DELTA
                break
            elif net[edge[0]][edge[1]]['length'] < mindis:
                n1 = edge[0]
                n2 = edge[1]
                mindis = net[edge[0]][edge[1]]['length']
        if mindis >= MERGE_THRESHOLD:
            break
        posx = (net.nodes[n1]['x'] + net.nodes[n2]['x']) / 2
        posy = (net.nodes[n1]['y'] + net.nodes[n2]['y']) / 2
        for i in net.neighbors(n2):
            if i != n1:
                addEdge(net, n1, i)
        net.remove_node(n2)
        net.nodes[n1]['x'] = posx
        net.nodes[n1]['y'] = posy
        for i in net.neighbors(n1):
            length = sqrt(pow(net.nodes[i]['x'] - posx, 2) + pow(net.nodes[i]['y'] - posy, 2))
            net[n1][i]['length'] = length

    return [net, emptyCenters]


def iter(choice: int, context: list, space: TwoDimSpace, trial: int):
    net = context[choice][0]
    bestNet = context[choice][1]
    patternList = context[choice][2]
    bestList = context[choice][3]
    totalcost = context[choice][4]
    bestCost = context[choice][5]
    totalcostList = context[choice][6]
    nowIterRound = context[choice][7]
    bestIterRound = context[choice][8]
    actionProbabilities = context[choice][9]
    sinceLastBest = context[choice][10]
    bestWallPatterns = context[choice][11]

    for i in range(nowIterRound, nowIterRound + 1000):
        if i % PLOT_INTERVAL == 0:
            visualizeSpace(space, patternList, buildWallPatterns(patternList, space),
                           'tmp_results/result_' + str(trial * SET_NUMBER + choice) + '_' + (str)(i) + '.png')
            visualizeNet(space, net,
                         'tmp_results/result_' + str(trial * SET_NUMBER + choice) + '_' + (str)(i) + '_net.png')
            visualizeCost(totalcostList, 'tmp_results/result_' + str(trial * SET_NUMBER + choice) + '_' + 'cost.png')
            visualizeSpace(space, bestList, buildWallPatterns(bestList, space),
                           'tmp_results/result_' + str(trial * SET_NUMBER + choice) + '_' + 'tmpbest.png')
            visualizeNet(space, bestNet,
                         'tmp_results/result_' + str(trial * SET_NUMBER + choice) + '_' + 'tmpbest_net.png')
            visualizeAll(space, bestList, buildWallPatterns(bestList, space), bestNet, bestCost, bestIterRound,
                         'tmp_results/result_' + str(trial * SET_NUMBER + choice) + '_' + 'tmpbest_all.png')
            # for i in range(len(actionProbabilities)):
            #     successRate[i] = successCount[i] / max(DELTA, chooseCount[i])
            # print(chooseCount)
            # print(successCount)
            # print(successRate)

        totalcostList.append(totalcost)

        if totalcost < bestCost:  # save the best result
            bestList = deepcopy(patternList)
            bestNet = deepcopy(net)
            bestCost = deepcopy(totalcost)
            bestWallPatterns = buildWallPatterns(patternList, space)
            bestIterRound = i
            sinceLastBest = 0
        else:
            sinceLastBest += 1
        # trace back to the best result and continue
        if sinceLastBest > RE_ITER_ROUND_LIMIT and totalcost - bestCost > RE_ITER_COST_LIMIT:
            patternList = deepcopy(bestList)
            net = deepcopy(bestNet)
            totalcost = deepcopy(bestCost)
            sinceLastBest = 0

        lastList = deepcopy(patternList)
        lastNet = deepcopy(net)

        probabilityValue = random.random()
        if probabilityValue < actionProbabilities[0]:  # move
            #chooseCount[0] += 1
            if len(patternList) > 0:
                patternChoice = random.randint(0, len(patternList) - 1)
                pattern = patternList[patternChoice]
                if random.randint(0, 1) == 0:
                    pattern.centerPoint[0] += MOVE_DISTANCE_DELTA * np.random.standard_normal()
                else:
                    pattern.centerPoint[1] += MOVE_DISTANCE_DELTA * np.random.standard_normal()
                pattern.update()
                valid = pattern.acceptable() and checkBoundary(pattern, space) and checkIntersect(pattern, patternList)
                if valid:
                    net = buildNet(patternList, space)
                    valid = space.checkConnection(net, patternList)
                if not valid:  # reject
                    patternList = lastList
                    net = lastNet
                else:
                    wallPatterns = buildWallPatterns(patternList, space)
                    newcost = getTotalcost(net, patternList, wallPatterns, space)
                    if newcost[0] < totalcost or random.random() < exp(
                        (totalcost - newcost[0]) * max(0.5, i / 1000) / COST_ACCEPT_PARAM):  # accept
                        #successCount[0] += 1
                        totalcost = newcost[0]
                        actionProbabilities = probabilitiesAdjust(newcost[1], newcost[2], len(patternList))
                    else:  # reject
                        patternList = lastList
                        net = lastNet

        elif probabilityValue < actionProbabilities[1]:  # resize
            #chooseCount[1] += 1
            if len(patternList) > 0:
                patternChoice = random.randint(0, len(patternList) - 1)
                pattern = patternList[patternChoice]
                if isinstance(pattern, LinePattern):
                    pattern.length += LINE_RESIZE_DELTA * np.random.standard_normal()
                    pattern.length = max(pattern.length, DELTA)
                elif isinstance(pattern, GridPattern):
                    randNum = random.randint(0, 3)
                    if randNum < 2:
                        pattern.orient = 1 - pattern.orient
                    elif randNum == 2:
                        pattern.width += GRID_RESIZE_DELTA * np.random.standard_normal()
                        pattern.width = max(pattern.width, DELTA)
                    else:
                        pattern.height += GRID_RESIZE_DELTA * np.random.standard_normal()
                        pattern.height = max(pattern.height, DELTA)
                elif isinstance(pattern, WebPattern) or isinstance(pattern, StarPattern):
                    randNum = random.randint(0, 4)
                    if randNum < 3:
                        length = None
                        if isinstance(pattern, WebPattern):
                            length = pattern.length + WEB_RESIZE_DELTA * np.random.standard_normal()
                        else:
                            length = pattern.length + STAR_RESIZE_DELTA * np.random.standard_normal()
                        length = max(length, DELTA)
                        pattern.length = length
                    elif randNum == 3:
                        outNums = [3, 4, 5, 6]
                        outNums.remove(pattern.outNum)
                        pattern.outNum = outNums[random.randint(0, len(outNums) - 1)]
                        angles = []
                        if pattern.outNum == 3:
                            angles = [0, pi / 2, pi, 3 * pi / 2]
                        elif pattern.outNum == 4:
                            angles = [0, pi / 4]
                        elif pattern.outNum == 5:
                            angles = [0, pi / 2, pi, 3 * pi / 2]
                        else:
                            angles = [0, pi / 2]
                        for i in range(len(angles)):
                            if abs(angles[i] - pattern.rotate) < pi / 180:
                                angles.remove(angles[i])
                                break
                        pattern.rotate = angles[random.randint(0, len(angles) - 1)]
                    else:
                        angles = []
                        if pattern.outNum == 3:
                            angles = [0, pi / 2, pi, -pi / 2]
                        elif pattern.outNum == 4:
                            angles = [0, pi / 4]
                        elif pattern.outNum == 5:
                            angles = [0, pi / 2, pi, -pi / 2]
                        else:
                            angles = [0, pi / 2]
                        for i in range(len(angles)):
                            if abs(angles[i] - pattern.rotate) < pi / 180:
                                angles.remove(angles[i])
                                break
                        pattern.rotate = angles[random.randint(0, len(angles) - 1)]

                elif isinstance(pattern, RoundPattern):
                    randNum = random.randint(0, 4) if pattern.doubleLayer else random.randint(0, 3)
                    if randNum < 2:
                        pattern.width += ROUND_RESIZE_DELTA * np.random.standard_normal()
                        pattern.width = max(pattern.width, DELTA)
                    elif randNum < 4:
                        pattern.height += ROUND_RESIZE_DELTA * np.random.standard_normal()
                        pattern.height = max(pattern.height, DELTA)
                    else:
                        pattern.inStyle = 1 - pattern.inStyle
                elif isinstance(pattern, EmptyPattern):
                    if random.randint(0, 1) == 0:
                        pattern.width += EMPTY_RESIZE_DELTA * np.random.standard_normal()
                        pattern.width = max(pattern.width, DELTA)
                    else:
                        pattern.height += EMPTY_RESIZE_DELTA * np.random.standard_normal()
                        pattern.height = max(pattern.height, DELTA)

                pattern.update()
                valid = pattern.acceptable() and checkBoundary(pattern, space) and checkIntersect(pattern, patternList)
                if valid:
                    net = buildNet(patternList, space)
                    valid = space.checkConnection(net, patternList)
                if not valid:  # reject
                    patternList = lastList
                    net = lastNet
                else:
                    wallPatterns = buildWallPatterns(patternList, space)
                    newcost = getTotalcost(net, patternList, wallPatterns, space)
                    if newcost[0] < totalcost or random.random() < exp(
                        (totalcost - newcost[0]) * max(0.5, i / 1000) / COST_ACCEPT_PARAM):  # accept
                        #successCount[1] += 1
                        totalcost = newcost[0]
                        actionProbabilities = probabilitiesAdjust(newcost[1], newcost[2], len(patternList))
                    else:  # reject
                        patternList = lastList
                        net = lastNet

        elif probabilityValue < actionProbabilities[2]:  # add
            #chooseCount[2] += 1
            centerPoint = None
            tryCount = 0
            while True:
                centerPoint = np.array([
                    np.random.uniform(space.boundary.bounds[0], space.boundary.bounds[2]),
                    np.random.uniform(space.boundary.bounds[1], space.boundary.bounds[3])
                ])
                if space.boundbox.contains(Point(centerPoint)):
                    tryCount += 1
                    testPattern = EmptyPattern(centerPoint, ROAD_WIDTH, ROAD_WIDTH)
                    valid = checkBoundary(testPattern, space) and checkIntersect(testPattern, patternList)
                    if valid or tryCount > 50:
                        break
            patternChoice = random.randint(0, 5)
            if patternChoice == 0:
                patternList.append(LinePattern(centerPoint, SHELF_MAX_LENGTH * 2, random.randint(0, 1)))
            elif patternChoice == 1:
                if random.randint(0, 1) == 0:
                    patternList.append(
                        GridPattern(centerPoint, SHELF_MAX_LENGTH * 2, ROAD_WIDTH + SHELF_MIN_WIDTH * 4 + DELTA, 0))
                else:
                    patternList.append(
                        GridPattern(centerPoint, ROAD_WIDTH + SHELF_MIN_WIDTH * 4 + DELTA, SHELF_MAX_LENGTH * 2, 0))
            elif patternChoice == 2:
                patternList.append(WebPattern(centerPoint, 4, sqrt(2) * (ROAD_WIDTH + SHELF_MIN_LENGTH), pi / 4))
            elif patternChoice == 3:
                patternList.append(StarPattern(centerPoint, 4, (ROAD_WIDTH + SHELF_MIN_LENGTH + SHELF_MAX_WIDTH * 2),
                                               0))
            elif patternChoice == 4:
                patternList.append(
                    RoundPattern(centerPoint, SHELF_MIN_LENGTH + SHELF_MAX_WIDTH * 2 + DELTA,
                                 SHELF_MIN_LENGTH + SHELF_MAX_WIDTH * 2 + DELTA))
            else:
                patternList.append(EmptyPattern(centerPoint, ROAD_WIDTH + DELTA, ROAD_WIDTH + DELTA))

            pattern = patternList[len(patternList) - 1]
            pattern.update()
            valid = pattern.acceptable() and checkBoundary(pattern, space) and checkIntersect(pattern, patternList)
            if valid:
                net = buildNet(patternList, space)
                valid = space.checkConnection(net, patternList)
            if not valid:  # reject
                patternList = lastList
                net = lastNet
            else:
                wallPatterns = buildWallPatterns(patternList, space)
                newcost = getTotalcost(net, patternList, wallPatterns, space)
                if newcost[0] < totalcost or random.random() < exp(
                    (totalcost - newcost[0]) * max(0.5, i / 1000) / COST_ACCEPT_PARAM):  # accept
                    #successCount[2] += 1
                    totalcost = newcost[0]
                    actionProbabilities = probabilitiesAdjust(newcost[1], newcost[2], len(patternList))
                else:  # reject
                    patternList = lastList
                    net = lastNet

        elif probabilityValue < actionProbabilities[3]:  # remove
            #chooseCount[3] += 1
            if len(patternList) > 0:
                # smaller patterns have higher chance to be chosen
                areaValue = 0
                areaValueList = []
                patternChoice = 0
                for i in range(len(patternList)):
                    areaValue += 1 / patternList[i].area()
                    areaValueList.append(areaValue)
                randValue = random.uniform(0, areaValue)
                for i in range(len(patternList)):
                    if randValue < areaValueList[i]:
                        patternChoice = i
                        break

                patternList.pop(patternChoice)
                net = buildNet(patternList, space)
                valid = space.checkConnection(net, patternList)
                if not valid:  # reject
                    patternList = lastList
                    net = lastNet
                else:
                    wallPatterns = buildWallPatterns(patternList, space)
                    newcost = getTotalcost(net, patternList, wallPatterns, space)
                    if newcost[0] < totalcost or random.random() < exp(
                        (totalcost - newcost[0]) * max(0.5, i / 1000) / COST_ACCEPT_PARAM):  # accept
                        #successCount[3] += 1
                        totalcost = newcost[0]
                        actionProbabilities = probabilitiesAdjust(newcost[1], newcost[2], len(patternList))
                    else:  # reject
                        patternList = lastList
                        net = lastNet

        elif probabilityValue < actionProbabilities[4]:  # change
            #chooseCount[4] += 1
            if len(patternList) > 0:
                # # bigger patterns have higher chance to be chosen
                # areaValue = 0
                # areaValueList = []
                # patternChoice = 0
                # for i in range(len(patternList)):
                #     areaValue += patternList[i].area()
                #     areaValueList.append(areaValue)
                # randValue = random.uniform(0, areaValue)
                # for i in range(len(patternList)):
                #     if randValue < areaValueList[i]:
                #         patternChoice = i
                #         break
                patternChoice = random.randint(0, len(patternList) - 1)

                newPattern = patternList[patternChoice].randomChange(space)

                patternList[patternChoice] = newPattern
                patternList[patternChoice].update()
                valid = newPattern.acceptable() and checkBoundary(newPattern, space) and checkIntersect(
                    newPattern, patternList)
                if valid:
                    net = buildNet(patternList, space)
                    valid = space.checkConnection(net, patternList)
                if not valid:  # reject
                    patternList = lastList
                    net = lastNet
                else:
                    wallPatterns = buildWallPatterns(patternList, space)
                    newcost = getTotalcost(net, patternList, wallPatterns, space)
                    if newcost[0] < totalcost or random.random() < exp(
                        (totalcost - newcost[0]) * max(0.5, i / 1000) / COST_ACCEPT_PARAM):  # accept
                        #successCount[4] += 1
                        totalcost = newcost[0]
                        actionProbabilities = probabilitiesAdjust(newcost[1], newcost[2], len(patternList))
                    else:  # reject
                        patternList = lastList
                        net = lastNet

    nowIterRound += 1000
    context[choice] = [
        net, bestNet, patternList, bestList, totalcost, bestCost, totalcostList, nowIterRound, bestIterRound,
        actionProbabilities, sinceLastBest, bestWallPatterns
    ]


def contextCostCmp(context1: list, context2: list):
    if context1[0][5] < context2[0][5]:
        return -1
    elif context1[0][5] > context2[0][5]:
        return 1
    return 0


if __name__ == '__main__':
    # prepare
    spaceControlPoints = [[p(0, 0), p(30, 0), p(30, 20), p(0, 20)], p(0, 10), p(30, 10), p(1, 0), p(-1, 0)]
    # spaceControlPoints = [[
    #     p(0, 0), p(30, 0),
    #     p(30, 15),
    #     p(15, 15),
    #     p(15, 30),
    #     p(0, 30)
    # ],
    #                       p(7.5, 30),
    #                       p(30, 7.5),
    #                       p(0, -1),
    #                       p(-1, 0)]
    space = TwoDimSpace(spaceControlPoints[0], spaceControlPoints[1], spaceControlPoints[2], spaceControlPoints[3],
                        spaceControlPoints[4])

    for root, dirs, files in os.walk('tmp_results', topdown=False):
        for name in files:
            if name.endswith('.png'):
                os.remove(os.path.join(root, name))

    # start
    random.seed()
    for i in range(1, len(actionProbabilities)):
        actionProbabilities[i] += actionProbabilities[i - 1]
    standardProbabilities = deepcopy(actionProbabilities)
    assert abs(actionProbabilities[len(actionProbabilities) - 1] - 1) < DELTA
    assert PROCESS_NUM <= SET_NUMBER

    allTrialsCount = TRIALS * AVG_ITER_ROUND * SET_NUMBER
    with tqdm(total=allTrialsCount / 1000) as bar:
        for trial in range(TRIALS):
            manager = Manager()
            context = manager.list([[] for i in range(SET_NUMBER)])
            contextCount = [0 for i in range(SET_NUMBER)]
            totalCount = 0
            maxCount = AVG_ITER_ROUND * SET_NUMBER
            processPool = [None for i in range(PROCESS_NUM)]
            processNumber = [-1 for i in range(PROCESS_NUM)]

            # load
            # if len(sys.argv) > 1:
            #     if os.path.exists('models/full' + (str)(SET_NUMBER) + '.npy'):
            #         model = np.load('models/full' + (str)(SET_NUMBER) + '.npy',
            #                         allow_pickle=True).tolist()
            #         space = TwoDimSpace(model[0][0], model[0][1], model[0][2],
            #                             model[0][3], model[0][4])
            #         context = model[1]
            #         contextCount = model[2]
            #         totalCount = model[3]
            #     else:
            #         print("no model available")

            # init context
            if len(context[-1]) == 0:
                for i in range(SET_NUMBER):
                    bestNet = None
                    patternList = []
                    bestList = []
                    bestWallPatterns = []
                    net = buildNet(patternList, space)
                    wallPatterns = buildWallPatterns(patternList, space)
                    totalcost = getTotalcost(net, patternList, wallPatterns, space)[0]
                    bestCost = 100
                    totalcostList = []
                    nowIterRound = 1
                    bestIterRound = 0
                    actionProbabilities = deepcopy(standardProbabilities)
                    sinceLastBest = 0
                    context[i] = [
                        net, bestNet, patternList, bestList, totalcost, bestCost, totalcostList, nowIterRound,
                        bestIterRound, actionProbabilities, sinceLastBest, bestWallPatterns
                    ]
                    contextCount[i] = 0
                totalCount = 0

            # query and select, then multiprocess

            while True:
                if totalCount >= maxCount:  # wait and break
                    while True:
                        sleep(0.001)
                        fin = True
                        for i in range(PROCESS_NUM):
                            if not (processPool[i] == None or processPool[i].is_alive() == False):
                                fin = False
                                break
                        if fin:
                            break
                    fullResult = [spaceControlPoints, deepcopy(context), contextCount, totalCount]
                    np.save('models/full' + (str)(SET_NUMBER) + '_' + (str)(trial) + '.npy',
                            np.array(fullResult, dtype=object))
                    break
                # if totalCount % 10000 == 0 and totalCount > 0:  # wait and sort
                #     while True:
                #         sleep(0.001)
                #         couldSort = True
                #         for i in range(PROCESS_NUM):
                #             if not (processPool[i] == None
                #                     or processPool[i].is_alive() == False):
                #                 couldSort = False
                #                 break
                #         if not couldSort:
                #             continue
                #         bundle = [[context[i], contextCount[i]]
                #                   for i in range(SET_NUMBER)]
                #         bundle = sorted(bundle, key=cmp_to_key(contextCostCmp))
                #         newContext = [bundle[i][0] for i in range(SET_NUMBER)]
                #         newContextCount = [bundle[i][1] for i in range(SET_NUMBER)]
                #         context = manager.list(newContext)
                #         contextCount = newContextCount
                #         break
                sleep(0.001)
                indexList=[]
                for i in range(PROCESS_NUM):
                    if (processPool[i] == None) or (not processPool[i].is_alive()):
                        indexList.append(i)
                
                if len(indexList) == 0:
                    continue
                if totalCount % 5000 == 0 and totalCount > 0:  # save the experiment context to model
                    fullResult = [spaceControlPoints, deepcopy(context), contextCount, totalCount]
                    np.save('models/full' + (str)(SET_NUMBER) + '_' + (str)(trial) + '.npy',
                            np.array(fullResult, dtype=object))
                for index in indexList:
                    processNumber[index] = -1
                    choice = -1
                    val = 1000
                    vals = []
                    for i in range(SET_NUMBER):  # UCT choose policy
                        vals.append(context[i][5])
                        if i in processNumber:
                            continue
                        if contextCount[i] == 0:
                            choice = i
                            break
                        if context[i][5] > 30:
                            choice = i
                            break
                        contextVal = context[i][5] - UCT_ARG * sqrt(log(totalCount) / contextCount[i])
                        if contextVal < val:
                            choice = i
                            val = contextVal
                    if choice == -1:
                        continue
                    p = Process(target=iter, args=(choice, context, deepcopy(space), trial))
                    processPool[index] = p
                    processNumber[index] = choice
                    p.start()
                    contextCount[choice] += 1000
                    totalCount += 1000
                    bar.update(1)
                

                # totalVal = 0
                # maxVal = 0
                # minVal = 100
                # for i in range(len(vals)):
                #     maxVal = max(maxVal, vals[i])
                #     minVal = min(minVal, vals[i])
                #     totalVal += vals[i]
                #     vals[i] = round(vals[i], 2)
                # print('avg:' + (str)(round(totalVal / len(vals), 2)) + ' min:' + (str)(round(minVal, 2)) + ' max:' +
                #       (str)(round(maxVal, 2)))
                # print(vals)

            transform(trial,0)
            print('trial ' + (str)(trial) + ' ends')

    movebest()
