import os
import json
import numpy as np

def seriesCount():
    domNames = os.listdir('./cgseries')
    layoutsNum = 0
    involvedObjects = {}
    for domName in domNames:
        seriesNames = os.listdir(f'./cgseries/{domName}')
        if len(seriesNames) == 0:
            continue
        print('counting dom ' + domName)
        for seriesName in seriesNames:
            fileNames = os.listdir(f'./cgseries/{domName}/{seriesName}')
            for fileName in fileNames:
                if fileName == 'result.json':
                    with open(f'./cgseries/{domName}/{seriesName}/result.json') as f:
                        resultjson = json.load(f)
                    for o in resultjson['involvedObjects']:
                        if o not in involvedObjects:
                            involvedObjects[o] = 1
                if fileName != 'result.json' and '.json' in fileName:
                    with open(f'./cgseries/{domName}/{seriesName}/{fileName}') as f:
                        scenejson = json.load(f)
                    layoutsNum += 1
                    for obj in scenejson['rooms'][0]['objList']:
                        if obj['modelId'] in involvedObjects:
                            involvedObjects[obj['modelId']] += 1
    print(involvedObjects)
    print(len(involvedObjects))
    print(layoutsNum)
    print(layoutsNum / len(involvedObjects))
    occurrenceNum = 0
    occurrenceList = []
    for o in involvedObjects:
       occurrenceNum += involvedObjects[o] 
       occurrenceList.append(involvedObjects[o])
    print(occurrenceNum / len(involvedObjects))
    print(np.std(occurrenceList))

if __name__ == '__main__':
    seriesCount()