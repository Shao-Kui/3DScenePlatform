import os
import json

def seriesCount():
    domNames = os.listdir('./cgseries')
    layoutsNum = 0
    involvedObjects = []
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
                            involvedObjects.append(o)
                if fileName != 'result.json' and '.json' in fileName:
                    layoutsNum += 1
    print(involvedObjects)
    print(len(involvedObjects))
    print(layoutsNum)
    print(layoutsNum / len(involvedObjects))

if __name__ == '__main__':
    seriesCount()