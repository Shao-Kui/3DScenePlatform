import shutil
import os

leveldirs = os.listdir('./level_doorfix/')
for leveldir in leveldirs:
    levelnames = os.listdir(f'./level_doorfix/{leveldir}/')
    for levelname in levelnames:
        if '.json' not in levelname:
            continue
        shutil.copy(f'./level_doorfix/{leveldir}/{levelname}', f'./levelsuncg/{levelname}')
