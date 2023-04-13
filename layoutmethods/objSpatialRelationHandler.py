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
        return -1
    
    eleDict[eleName] = []
    for itms in lst:
        itmLst = itms[1:].split(',')[:-1] #get rid of '{ }'
        ret = itemListHandler(itmLst, eleName)
        if len(ret) :
            eleDict[eleName].append(ret)
        else:
            print('elementHandler : item %s length error'%(eleName))
            return -1

    return 1


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
