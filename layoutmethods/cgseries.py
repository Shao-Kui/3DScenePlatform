import os
import json
<<<<<<< HEAD
=======
import numpy as np
>>>>>>> fc29589ac00030d8736fffadd9dcdaf24148863f

def seriesCount():
    domNames = os.listdir('./cgseries')
    layoutsNum = 0
<<<<<<< HEAD
    involvedObjects = []
=======
    involvedObjects = {}
>>>>>>> fc29589ac00030d8736fffadd9dcdaf24148863f
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
<<<<<<< HEAD
                            involvedObjects.append(o)
                if fileName != 'result.json' and '.json' in fileName:
                    layoutsNum += 1
=======
                            involvedObjects[o] = 1
                if fileName != 'result.json' and '.json' in fileName:
                    with open(f'./cgseries/{domName}/{seriesName}/{fileName}') as f:
                        scenejson = json.load(f)
                    layoutsNum += 1
                    for obj in scenejson['rooms'][0]['objList']:
                        if obj['modelId'] in involvedObjects:
                            involvedObjects[obj['modelId']] += 1
>>>>>>> fc29589ac00030d8736fffadd9dcdaf24148863f
    print(involvedObjects)
    print(len(involvedObjects))
    print(layoutsNum)
    print(layoutsNum / len(involvedObjects))
<<<<<<< HEAD
=======
    occurrenceNum = 0
    occurrenceList = []
    for o in involvedObjects:
       occurrenceNum += involvedObjects[o] 
       occurrenceList.append(involvedObjects[o])
    print(occurrenceNum / len(involvedObjects))
    print(np.std(occurrenceList))
>>>>>>> fc29589ac00030d8736fffadd9dcdaf24148863f

if __name__ == '__main__':
    seriesCount()