"""
Usage of OSR dataset and its handler:       by Liang Yue, last modified on 29th Oct. 2022

-----------------------------------------------Legend-----------------------------------------------------

DATA                                    list type; a list of 'element'
element                                 dictionary type; eleName as key, its value as value
    |eleName                            list type in default, optional in default, due to the actual use of that prior;
        |(item)                         dictionary type in default; attributeName as key, its value as value
            |attributeName1             float type in default; required in default;
            |attributeName2
            |attributeName3
        |(item)                         if there is another item here, it means the length of the list is unlimited. otherwise, there should be only one item in the list
        ...
    |eleName
        |(item)
            |attributeName1
            ...


attribute is required in default, if the correspondent item and eleName exist. But the eleName is optional in default.

---------------------------------Detailed Data Structure-------------------------------------------------

element
    |mainObjId+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++string; required;             +modelId of the main object
    |userName++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++string; required;             +name of the user who inserted this piece of prior
    |relationName++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++string;                       +name of the piece of prior
    |state+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++                              +if this main object is tranformable
        |(item)------------------------------------------------------------------                 single item;
            |currentState                                                        string;                       name of that state
    |scale+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++                              +if this main object is scaled
        |(item)------------------------------------------------------------------                 single item;
            |objScaleX                                                                                         \
            |objScaleY                                                                                         --scale of main object
            |objScaleZ                                                                                         /
    |gtrans++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++                              +if there is object in the GTRANS_GROUP
        |(item)------------------------------------------------------------------                              -for each object
            |attachedObjId                                                       string;                       modelId of that object
            |objPosX                                                                                           \
            |objPosY                                                                                           --position of attached object relative to the main one
            |objPosZ                                                                                           /
            |objOriY                                                                                           orientation of attached object relative to the main one's axis
            |objScaleX                                                                                         \
            |objScaleY                                                                                         --scale of attached object ITSELF!!!!
            |objScaleZ                                                                                         /
            |currentState                                                        string; optional;             if that object is transformable and its state
        |(item)------------------------------------------------------------------
        ...
    |wall++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++                              +if the wall is taken into account
        |(item)------------------------------------------------------------------                 single item;
            |nearestDistance                                                                                   nearest distance towards the main object
            |secondDistance                                                                                    distance of the second nearest wall
            |nearestOrient
    |window++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++                              +if the window is taken into account
        |(item)------------------------------------------------------------------                              -for each window
            |distance                                                                                          distance of window to the main object
            |objPosX                                                                                           \
            |objPosY                                                                                           --position of window relative to the main object
            |objPosZ                                                                                           / 
            |width
            |height
            |objOriY                                                                                           - orient of the main object in the ORIGINAL co-ordinates
            |direction                                                                                         - face of the window in the ORIGINAL co-ordinates
        |(item)------------------------------------------------------------------
        ...
    |door++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++                              +if the door is taken into account
        |(item)------------------------------------------------------------------                              -for each door
            |distance                                                                                          distance of door to the main object
            |objPosX                                                                                           \
            |objPosY                                                                                           --position of door relative to the main object
            |objPosZ                                                                                           / 
            |width
            |height
            |objOriY                                                                                           - orient of the main object in the ORIGINAL co-ordinates
            |direction                                                                                         - face of the door in the ORIGINAL co-ordinates
        |(item)------------------------------------------------------------------
        ...
"""
import math

def itemListHandler(lst, instr):
    if instr == 'scale':
        if len(lst) == 3:
            return {'objScaleX' : float(lst[0]),  'objScaleY' : float(lst[1]), 'objScaleZ' : float(lst[2])}
        else:
            return {}

    if instr == 'state':
        if len(lst) == 1:
            return {'currentState' : lst[0]}
        else:
            return {}
    
    if instr == 'gtrans':
        if len(lst) == 8:
            return {'attachedObjId' : lst[0], 'objPosX' : float(lst[1]), 'objPosY' : float(lst[2]), 'objPosZ' : float(lst[3]), 'objOriY' : float(lst[4]), 'objScaleX' : float(lst[5]), 'objScaleY' : float(lst[6]), 'objScaleZ' : float(lst[7])}
        elif len(lst) == 9:
            return {'attachedObjId' : lst[0], 'objPosX' : float(lst[1]), 'objPosY' : float(lst[2]), 'objPosZ' : float(lst[3]), 'objOriY' : float(lst[4]), 'objScaleX' : float(lst[5]), 'objScaleY' : float(lst[6]), 'objScaleZ' : float(lst[7]), 'currentState' : lst[8]}
        else:
            return {}

    if instr == 'wall':
        if len(lst) == 3:
            return {'nearestDistance' : float(lst[0]), 'secondDistance' : float(lst[1]), 'nearestOrient0' : float(lst[2])}
        else:
            return {}
    
    if instr == 'window' or instr == 'door':
        if len(lst) == 8:
            return {'distance' : float(lst[0]), 'objPosX' : float(lst[1]), 'objPosY' : float(lst[2]), 'objPosZ' : float(lst[3]), 'width' : float(lst[4]), 'height' : float(lst[5]), 'objOriY' : float(lst[6]), 'direction' : lst[7][1]}
        else:
            return {}


def elementHandler(eleDict, element):
    if element.count('[') == 0:
        if 'relationName' in eleDict:
            return -1
        else:
            eleDict['relationName'] = element
        return 1
    idx = element.index('[')
    eleName = element[1:idx] #skip the blank space
    eleContent = element[idx+1:] #skip [
    lst = eleContent.split(':')[:-1] #skip ]
    if not(eleName in ['scale', 'state', 'gtrans', 'wall', 'window', 'door']):
        print('elementHandler : wrong attribute')
        print(eleName)
        return -1
    
    eleDict[eleName] = []
    for itms in lst:
        itmLst = itms[1:].split(',')[:-1] #get rid of '{ }'
        ret = itemListHandler(itmLst, eleName)
        if len(ret) :
            eleDict[eleName].append(ret)
        else:
            print('elementHandler : item %s length error'%(eleName))
            print(lst)
            return -1

    return 1

OSRLINES = [0,0]
OSRDATA = [0,0]
OSRloadFlag = False
OSRfd = 0
def loadData():
    global OSRLINES
    global OSRDATA
    global OSRfd
    OSRfd = open("./layoutmethods/object-spatial-relation-dataset.txt", 'r')#open("./yltmp/OSRdataset.txt", 'r')#
    OSRLINES = OSRfd.readlines()
    OSRDATA.clear()
    for line in OSRLINES:
        elements = line.split(';')
        eleDict = {'mainObjId' :  elements[0]}

        lastIdx = -1
        try:
            tryId = int(elements[-1][1:-1])
        except:
            eleDict['userName'] = elements[lastIdx][1:]
        else:
            lastIdx = -2
            eleDict['priorId'] = elements[-1][1:-1]
            eleDict['userName'] = elements[lastIdx][1:]

        for element in elements[1:lastIdx]:
            if elementHandler(eleDict, element) < 0 :
                break
    
        OSRDATA.append(eleDict)

def searchMainModelId(mainModelId):
    global OSRLINES
    global OSRDATA
    global OSRloadFlag
    if not OSRloadFlag:
        loadData()
        OSRloadFlag = True
    ret = []
    for line in OSRLINES:
        elements = line.split(';')
        if elements[0] == mainModelId:
            eleDict = {'mainObjId' :  elements[0], 'priorId' : elements[-1][1:-1], 'userName' : elements[-2][1:]}
            
            valid = True
            for element in elements[1:-2]:
                if elementHandler(eleDict, element) < 0 :
                    valid = False
                    break
            if valid:
                ret.append(eleDict)
    
    return ret

def insertSort(lst, ele):
    lst.append(ele)
    length = len(lst)
    for i in range(length-2, -2, -1):
        if (i >= 0) and lst[i]['score'] < ele['score']:
            lst[i+1] = lst[i]
        else:
            lst[i+1] = ele
            break

def compareWindoor(windoor0, windoor1, mainOri1):
    mainOri0 = -windoor0['objOriY']
    if abs(windoor0['objPosX']) > abs(windoor0['objPosZ']):
        mainOri0 += 1.5708
    windoor0['objOriY'] += mainOri0
    windoor1[6] += mainOri1
    
    theta = mainOri0 - mainOri1
    costheta = math.cos(theta)
    sintheta = math.sin(theta)
    realx = windoor0['objPosX'] * costheta + windoor0['objPosZ'] * sintheta
    realz =-windoor0['objPosX'] * sintheta + windoor0['objPosZ'] * costheta
    cosphi = (realx * windoor1[1] + realz * windoor1[3]) / (windoor0['distance'] * windoor1[0])
    return [cosphi, abs(windoor0['objOriY'] - windoor1[6])]

def mainSearch(mainModel, wallHint, windowHint, doorHint):
    global OSRLINES
    global OSRDATA
    global OSRloadFlag
    if not OSRloadFlag:
        loadData()
        OSRloadFlag = True
    ret = []
    for eleDict in OSRDATA:
        score = 0
        if eleDict['mainObjId'] == mainModel['modelId']:
            score += 100
            if 'startState' in mainModel:
                if (not ('state' in eleDict)) or eleDict['state'][0]['currentState'] != mainModel['startState']:
                    score -= 20
            if 'wall' in eleDict:
                if(abs(eleDict['wall'][0]['nearestOrient0'] - wallHint[0]) > 0.01):
                    score -= 0 #5
                else:
                    score += 0 #5 - abs(eleDict['wall'][0]['nearestDistance'] - wallHint[1])
            if 'window' in eleDict:
                if len(windowHint) == 0:
                    score -= 0 #5
                else:
                    rett = compareWindoor(eleDict['window'][0],windowHint[0],mainModel['orient'])
                    score += 0 #5*rett[0]
            if 'door' in eleDict:
                if len(doorHint) == 0:
                    score -= 0 #5
                else:
                    rett = compareWindoor(eleDict['door'][0],doorHint[0],mainModel['orient'])
                    score += 0 #5*rett[0]
        else:
            if 'gtrans' in eleDict:
                for t in eleDict['gtrans']:
                    if t['attachedObjId'] == mainModel['modelId']:
                        score += 50
                        break

        if score >= 50:
            newRet = eleDict
            newRet['score'] = score
            insertSort(ret, newRet)

    return ret

def searchId(queryLst):
    global OSRLINES
    global OSRDATA
    global OSRloadFlag
    if not OSRloadFlag:
        loadData()
        OSRloadFlag = True
    ret = []
    for q in queryLst:
        ret.append(OSRDATA[q])
    return ret

def deletePrior(idx):
    bufferFd = open("./yltmp/buffer.txt", 'w')
    dataFd = open("./yltmp/object-spatial-relation-dataset.txt", 'r')
    dataLines = dataFd.readlines()
    lenData = len(dataLines)
    for i in range(idx):
        thisPrior = dataLines[i]
        if int(thisPrior.split(';')[-1][:-1]) != i:
            print("uncontinous error %d"%(i))
            return
        bufferFd.write(thisPrior)
    for i in range(idx+1, lenData):
        thisPrior = dataLines[i]
        for j in range(-1, -10, -1):
            if thisPrior[j] == ';':
                bufferFd.write("%s; %d\n"%(thisPrior[:j], i-1))
                break
    bufferFd.close()
    dataFd.close()
    bufferFd = open("./yltmp/buffer.txt", 'r')
    dataFd = open("./yltmp/object-spatial-relation-dataset.txt", 'w')
    dataFd.write(bufferFd.read())
    bufferFd.close()
    dataFd.close()
    pass

def uploadDataFromMethods():
    hotDatafd = open("./layoutmethods/object-spatial-relation-dataset.txt", 'r')
    localDatafd = open("./yltmp/object-spatial-relation-dataset.txt", 'r')
    hotLines = hotDatafd.readlines()
    localLines = localDatafd.readlines()
    lenLocal = len(localLines)
    lenHot = len(hotLines)
    diffFlag = False
    for i in range(lenLocal):
        hotPrior = hotLines[i]
        lenHot = len(hotPrior)
        localPrior = localLines[i]
        if not (localPrior[:lenHot] == hotPrior):
            diffFlag = True
            print(i)
    
    if diffFlag:
        return

    localDatafd.close()
    localDatafd = open("./yltmp/object-spatial-relation-dataset.txt", 'a')
    for i in range(lenLocal, lenHot):
        localDatafd.write("%s; %d\n"%(hotLines[i], i))
        

def loadData(DATA, lines):
    for line in lines:
        elements = line.split(';')
        eleDict = {'mainObjId' :  elements[0], 'userName' : elements[-1][:-1]}

        for element in elements[1:-1]:
            if elementHandler(eleDict, element) < 0 :
                break
    
        DATA.append(eleDict)

def searchMainModelId(mainModelId, lines):
    for line in lines:
        elements = line.split(';')
        if elements[0] == mainModelId:
            eleDict = {'mainObjId' :  elements[0], 'userName' : elements[-1][:-1]}

            for element in elements[1:-1]:
                if elementHandler(eleDict, element) < 0 :
                    break
            
            return eleDict

if __name__ == '__main__':
    fd = open("object-spatial-relation-dataset.txt", 'r')
    LINES = fd.readlines()

    data = []
    loadData(data, LINES)
    for i in data:
        for j in i:
            print(j, i[j])
        print('\n')

    fd.close()
