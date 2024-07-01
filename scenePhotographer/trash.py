import os
import shutil
from utils import TOKENS

dirs = r'D:\zhx_workspace\3DScenePlatformDev\latentspace\sfy'

target_dirs = r'C:\Users\evan\Desktop\zhx_workspace\SceneViewer\user_data'

for item in os.listdir(dirs):
    if item in TOKENS:
        source = os.path.join(dirs,item)
        target = os.path.join(target_dirs,item)
        shutil.copytree(source,target)