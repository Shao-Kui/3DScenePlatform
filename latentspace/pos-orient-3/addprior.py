import os
import sys
import json
filenames = os.listdir('./priorstoadd/')
l = sys.argv[1]
r = sys.argv[2]
print(l, r)
with open('../pos-orient-denoised-2/{}.json'.format(l)) as f_origin:
    if os.path.isfile('./{}.json'.format(l)):
        with open('./{}.json'.format(l)) as f_target:
            j_target = json.load(f_target)
    else:
        j_target = {}
    j_target[r] = json.load(f_origin)[r]
    with open('./{}.json'.format(l), 'w') as f_target:
        json.dump(j_target, f_target)
