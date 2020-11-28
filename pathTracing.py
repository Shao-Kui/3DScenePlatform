from jinja2 import Environment, FileSystemLoader
import json
import os
import numpy as np
from datetime import datetime
from subprocess import check_output

sysROOT = 'F:/3DIndoorScenePlatform/dataset/PathTracing'
ROOT = './dataset/PathTracing'
file_loader = FileSystemLoader('./')
env = Environment(loader=file_loader)
template = env.get_template('./assets/pathTracingTemplate.xml')

def pathTracing(scenejson):
    now = datetime.now()
    dt_string = now.strftime("%d-%m-%Y %H-%M-%S")
    casename = ROOT + f'/{scenejson["origin"]}-{dt_string}'
    # re-organize scene json into Mitsuba .xml file: 
    scenejson["pcam"] = {}
    scenejson["pcam"]["origin"] = ', '.join([str(i) for i in scenejson["PerspectiveCamera"]["origin"]])
    scenejson["pcam"]["target"] = ', '.join([str(i) for i in scenejson["PerspectiveCamera"]["target"]])
    scenejson["pcam"]["up"] = ', '.join([str(i) for i in scenejson["PerspectiveCamera"]["up"]])
    scenejson['renderobjlist'] = []
    scenejson['renderroomobjlist'] = []
    for room in scenejson['rooms']:
        for cwf in ['w', 'f']:
            if os.path.exists(f'./dataset/room/{scenejson["origin"]}/{room["modelId"]}{cwf}.obj'):
                scenejson['renderroomobjlist'].append({
                    'modelPath': f'../../room/{scenejson["origin"]}/{room["modelId"]}{cwf}.obj',
                    'translate': [0,0,0],
                    'rotate': [0,0,0],
                    'scale': [1,1,1]
                })
        for obj in room['objList']:
            if 'inDatabase' in obj:
                if not obj['inDatabase']:
                    continue
            obj['modelPath'] = '../../object/{}/{}.obj'.format(obj['modelId'], obj['modelId'])
            scenejson['renderobjlist'].append(obj)
    output = template.render(scenejson=scenejson, PI=np.pi)
    if not os.path.exists(casename):
        os.makedirs(casename)
    with open(casename + '/renderconfig.xml', 'w') as f:
        f.write(output)
    check_output(f"mitsuba \"{casename + '/renderconfig.xml'}\"", shell=True)
    check_output(f"mtsutil tonemap -o \"{casename + '/render.png'}\" \"{casename + '/renderconfig.exr'}\" ", shell=True)

if __name__ == "__main__":
    with open('./dataset/PathTracing/bd4886b5-4323-42f9-8e1c-1e278ed88431-l7071-dl.json') as f:
        pathTracing(json.load(f))
    
