from jinja2 import Environment, FileSystemLoader
import json
import os
import numpy as np
from datetime import datetime
from subprocess import check_output
import shutil
import sys
import getopt
import numpy as np
from projection2d import getobjCat
import sk

sysROOT = 'F:/3DIndoorScenePlatform/dataset/PathTracing'
ROOT = './dataset/PathTracing'
file_loader = FileSystemLoader('./')
env = Environment(loader=file_loader)
template = env.get_template('./assets/pathTracingTemplate.xml')
cameraType="perspective" # spherical
num_samples = 64
r_dir = 'batch'
wallMaterial = True
REMOVELAMP = True
SAVECONFIG = True

def autoPerspectiveCamera(scenejson):
    bbox = scenejson['rooms'][0]['bbox']
    lx = (bbox['max'][0] + bbox['min'][0]) / 2
    lz = (bbox['max'][2] + bbox['min'][2]) / 2
    ymax = bbox['max'][1]
    camfovratio = np.tan((75/2) * np.pi / 180) 
    height_x = (bbox['max'][0]/2 - bbox['min'][0]/2) / camfovratio
    height_z = (bbox['max'][2]/2 - bbox['min'][2]/2) / camfovratio
    camHeight = ymax + np.max([height_x, height_z])
    if camHeight > 36 or camHeight < 0 or camHeight == np.NaN:
        camHeight = 6
    PerspectiveCamera = {}
    PerspectiveCamera['origin'] = [lx, camHeight, lz]
    PerspectiveCamera['target'] = [lx, 0, lz]
    PerspectiveCamera['up'] = [0,0,1]
    PerspectiveCamera['rotate'] = [0,0,0]
    lx_length = bbox['max'][0] - bbox['min'][0]
    lz_length = bbox['max'][2] - bbox['min'][2]
    if lz_length > lx_length:
        PerspectiveCamera['up'] = [1,0,0]
    scenejson['PerspectiveCamera'] = PerspectiveCamera
    return PerspectiveCamera

def pathTracing(scenejson, sampleCount=64, dst=None):
    now = datetime.now()
    dt_string = now.strftime("%Y-%m-%d %H-%M-%S")
    casename = ROOT + f'/{scenejson["origin"]}-{dt_string}'

    if 'PerspectiveCamera' not in scenejson:
        autoPerspectiveCamera(scenejson)
    if 'canvas' not in scenejson:
        scenejson['canvas'] = {}
        scenejson['canvas']['width'] = "1309"
        scenejson['canvas']['height'] = "809"
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
            if getobjCat(obj['modelId']) in ["Pendant Lamp", "Ceiling Lamp"] and REMOVELAMP:
                print('A lamp is removed. ')
                continue
            obj['modelPath'] = '../../object/{}/{}.obj'.format(obj['modelId'], obj['modelId'])
            if os.path.exists('./dataset/object/{}/{}.obj'.format(obj['modelId'], obj['modelId'])):
                scenejson['renderobjlist'].append(obj)
    output = template.render(
        scenejson=scenejson, 
        PI=np.pi, 
        sampleCount=sampleCount, 
        cameraType=cameraType,
        wallMaterial=wallMaterial
    )
    if not os.path.exists(casename):
        os.makedirs(casename)
    with open(casename + '/scenejson.json', 'w') as f:
        json.dump(scenejson, f, default=sk.jsonDumpsDefault)
    with open(casename + '/renderconfig.xml', 'w') as f:
        f.write(output)
    check_output(f"mitsuba \"{casename + '/renderconfig.xml'}\"", shell=True)
    check_output(f"mtsutil tonemap -o \"{casename + '/render.png'}\" \"{casename + '/renderconfig.exr'}\" ", shell=True)
    if dst is not None:
        shutil.copy(casename + '/render.png', f"./dataset/alilevel_door2021_orth/{scenejson['origin']}.png")
    if not SAVECONFIG:
        shutil.rmtree(casename)
    return casename

def batch():
    filenames = os.listdir(f'./dataset/PathTracing/{r_dir}')
    for filename in filenames:
        if '.json' not in filename:
            continue
        print('start do :' + filename)
        with open(f'./dataset/PathTracing/{r_dir}/{filename}') as f:
            try:
                casename = pathTracing(json.load(f), sampleCount=num_samples)
            except Exception as e:
                continue
            # copy rendered imgs to the rdir: 
            pngfilename = filename.replace('.json', '.png')
            shutil.copy(casename + '/render.png', f'./dataset/PathTracing/{r_dir}/{pngfilename}')

# roomtypelist = ['MasterBedroom', 'LivingDinningRoom', 'KidsRoom', 'SecondBedroom', 'LivingRoom', 'DinningRoom']
roomtypelist = ['MasterBedroom']
mage4methods = ['ours', 'planit', '3dfront', 'gba']
# mage4methods = ['3dfront']
iddc = [0]
def mage4gen():
    for rt in roomtypelist:
        for i in iddc:
            pcam = None
            for m in mage4methods:
                print(rt, i, m)
                jsonpath = f'H:/D3UserStudy/static/mage/{rt}/{i}/{m}.json'
                if not os.path.exists(jsonpath):
                    continue
                with open(jsonpath) as f:
                    scenejson = json.load(f)
                if pcam is None:
                    # pcam = autoPerspectiveCamera(scenejson)
                    pcam = scenejson['PerspectiveCamera']
                else:
                    scenejson['PerspectiveCamera'] = pcam
                # if m != 'gba':
                #     continue
                try:
                    rendercasename = pathTracing(scenejson, sampleCount=num_samples)
                except Exception as e:
                    print(e)
                    continue
                pngfilename = jsonpath.replace('.json', '.png')
                shutil.copy(rendercasename + '/render.png', pngfilename)

def autoCameraSpher_allRoom():
    filenames = os.listdir(f'./dataset/PathTracing/{r_dir}')
    for filename in filenames:
        if '.json' not in filename:
            continue
        print('start do :' + filename)
        with open(f'./dataset/PathTracing/{r_dir}/{filename}') as f:
            sj = json.load(f)
            if 'canvas' not in sj:
                sj['canvas'] = {}
                sj['canvas']['width'] = "1309"
                sj['canvas']['width'] = "809"
            for rm in sj['rooms']:
                PerspectiveCamera = {}
                PerspectiveCamera['origin'] = (np.array(rm['bbox']['min']) + np.array(rm['bbox']['max'])) / 2
                PerspectiveCamera['target'] = PerspectiveCamera['origin'] + np.array([0,0,1]) # this is the directional vector used by Doc. Yu He. 
                PerspectiveCamera['up'] = np.array([0,1,0])
                PerspectiveCamera['origin'] = PerspectiveCamera['origin'].tolist()
                PerspectiveCamera['target'] = PerspectiveCamera['target'].tolist()
                PerspectiveCamera['up'] = PerspectiveCamera['up'].tolist()
                PerspectiveCamera['rotate'] = [0,0,0]
                sj['PerspectiveCamera'] = PerspectiveCamera
                casename = pathTracing(sj, sampleCount=num_samples)
                pngfilename = filename.replace('.json', '.png')
                shutil.copy(casename + '/render.png', f'./dataset/PathTracing/{r_dir}/{rm["roomId"]}-{pngfilename}')

defaultTast = batch
if __name__ == "__main__":
    # batch(sys.argv[1], sampleCount=int(sys.argv[2]))
    # with open('./dataset/PathTracing/4cc6dba0-a26e-42cb-a964-06cb78d60bae-l2685-dl (8).json') as f:
    #     pathTracing(json.load(f), sampleCount=4)

    # s: number of samples, the default is 64; 
    # d: the directory of scene-jsons; 
    try:
        opts, args = getopt.getopt(sys.argv[1:], "s:d:hc:", ["task=","wm="])
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
        elif opt in ("--wm"):
            wallMaterial = bool(int(arg))
            print(wallMaterial)
        elif opt in ("--task"):
            # defaultTast = getattr(__name__, arg)
            defaultTast = globals()[arg]
    defaultTast()
