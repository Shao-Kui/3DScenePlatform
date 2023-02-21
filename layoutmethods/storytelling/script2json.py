import json

def insertSPIntoJson(storyName, sceneName):
    with open(sceneName) as f:
        sceneJson = json.load(f)
    with open(storyName) as f:
        storyJson = json.load(f)
    
    for room in sceneJson['rooms']:
        for obj in room['objList']:
            for storyPoint in storyJson['story']:
                if(storyPoint['modelId'] == obj['modelId']):
                    if('type' in obj.keys() and obj['type'] != 'storypoint'):
                        obj['type'] = 'storypoint'
                    if not ('storyContents' in obj.keys()):
                        data = {}
                        data['storyContents'] = storyPoint['storyContents']
                        obj.update(data)
                    storyJson['story'].remove(storyPoint)

    sceneString = json.dumps(sceneJson)
    with open(sceneName, "w") as outfile:
        outfile.write(sceneString)

if __name__ == "__main__":
    insertSPIntoJson('stories/sample.json','test/0e3f92e0-8f04-4643-a737-23603f438e68-r4.json')