from jinja2 import Environment, FileSystemLoader
import json
import os
import numpy as np
from datetime import datetime
from subprocess import check_output
import shutil
import sys
import getopt

sysROOT = 'F:/3DIndoorScenePlatform/dataset/PathTracing'
ROOT = './dataset/PathTracing'
file_loader = FileSystemLoader('./')
env = Environment(loader=file_loader)
template = env.get_template('./assets/pathTracingTemplate.xml')
cameraType="perspective" # spherical
num_samples=64

def pathTracing(scenejson, sampleCount=64):
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
            if os.path.exists('./dataset/object/{}/{}.obj'.format(obj['modelId'], obj['modelId'])):
                scenejson['renderobjlist'].append(obj)
    output = template.render(scenejson=scenejson, PI=np.pi, sampleCount=sampleCount, cameraType=cameraType)
    if not os.path.exists(casename):
        os.makedirs(casename)
    with open(casename + '/scenejson.json', 'w') as f:
        json.dump(scenejson, f)
    with open(casename + '/renderconfig.xml', 'w') as f:
        f.write(output)
    check_output(f"mitsuba \"{casename + '/renderconfig.xml'}\"", shell=True)
    check_output(f"mtsutil tonemap -o \"{casename + '/render.png'}\" \"{casename + '/renderconfig.exr'}\" ", shell=True)
    return casename

def batch(rdir):
    filenames = os.listdir(f'./dataset/PathTracing/{rdir}')
    for filename in filenames:
        if '.json' not in filename:
            continue
        print('start do :' + filename)
        with open(f'./dataset/PathTracing/{rdir}/{filename}') as f:
            casename = pathTracing(json.load(f), sampleCount=num_samples)
            # copy rendered imgs to the rdir: 
            pngfilename = filename.replace('.json', '.png')
            shutil.copy(casename + '/render.png', f'./dataset/PathTracing/{rdir}/{pngfilename}')

def autoCameraSpher_allRoom(rdir):
    filenames = os.listdir(f'./dataset/PathTracing/{rdir}')
    for filename in filenames:
        if '.json' not in filename:
            continue
        print('start do :' + filename)
        with open(f'./dataset/PathTracing/{rdir}/{filename}') as f:
            sj = json.load(f)
            if 'canvas' not in sj:
                sj['canvas'] = {}
                sj['canvas']['width'] = "1309"
                sj['canvas']['width'] = "809"
            for rm in sj['rooms']:
                PerspectiveCamera = {}
                PerspectiveCamera['origin'] = (np.array(rm['bbox']['min']) + np.array(rm['bbox']['max'])) / 2
                PerspectiveCamera['target'] = PerspectiveCamera['origin'] + np.array([0,-1,0]) # this is the directional vector used by Doc. Yu He. 
                PerspectiveCamera['up'] = PerspectiveCamera['origin'] + np.array([0,0,1])
                PerspectiveCamera['origin'] = PerspectiveCamera['origin'].tolist()
                PerspectiveCamera['target'] = PerspectiveCamera['target'].tolist()
                PerspectiveCamera['up'] = PerspectiveCamera['up'].tolist()
                PerspectiveCamera['rotate'] = [0,0,0]
                sj['PerspectiveCamera'] = PerspectiveCamera
                casename = pathTracing(sj, sampleCount=num_samples)
                pngfilename = filename.replace('.json', '.png')
                shutil.copy(casename + '/render.png', f'./dataset/PathTracing/{rdir}/{rm["roomId"]}-{pngfilename}')

defaultTast = batch
if __name__ == "__main__":
    # batch(sys.argv[1], sampleCount=int(sys.argv[2]))
    # with open('./dataset/PathTracing/4cc6dba0-a26e-42cb-a964-06cb78d60bae-l2685-dl (8).json') as f:
    #     pathTracing(json.load(f), sampleCount=4)

    # s: number of samples, the default is 64; 
    # d: the directory of scene-jsons; 
    try:
        opts, args = getopt.getopt(sys.argv[1:], "s:d:hc:", ["task="])
    except getopt.GetoptError:
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('python pathTracing.py -d batch1 -s 256')
            sys.exit()
        elif opt in ("-s"):
            num_samples = int(arg)
        elif opt in ("-d"):
            r_dir = arg
        elif opt in ("-c"):
            cameraType = arg
        elif opt in ("--task"):
            # defaultTast = getattr(__name__, arg)
            defaultTast = globals()[arg]
    defaultTast(r_dir)
