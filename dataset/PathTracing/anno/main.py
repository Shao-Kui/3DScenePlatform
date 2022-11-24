import os
import csv
import json

maindirs = os.listdir('./')

def countFolder(thedir):
    count = 0
    scenecount = 0
    filenames = os.listdir(thedir)
    for filename in filenames:
        if os.path.isdir(f'./{thedir}/{filename}'):
            _res = countFolder(f'./{thedir}/{filename}')
            count += _res[0]
            scenecount += _res[1]
        if '.json' in filename:
            with open(f'./{thedir}/{filename}') as f:
                sj = json.load(f)
            for r in sj['rooms']:
                for o in r['objList']:
                    if 'format' not in o:
                        continue
                    if o['inDatabase'] and o['format'] in ['glb', 'obj']:
                        count += 1
            scenecount += 1
    return count, scenecount

FinalNum = 0
FinalSNum = 0
with open('res.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    print(f'目录 \t 场景数量 \t 物体数量')
    writer.writerow(['目录', '场景数量', '物体数量'])
    for maindir in maindirs:
        if not os.path.isdir(f'./{maindir}'):
            continue
        num, snum = countFolder(f"./{maindir}")
        FinalNum += num
        FinalSNum += snum
        print(f'{maindir} \t {snum} \t {num}')
        writer.writerow([maindir, snum, num])
    print(f'合计 \t {FinalSNum} \t {FinalNum}')
    writer.writerow(['合计', FinalSNum, FinalNum])
