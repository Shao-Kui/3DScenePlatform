import os
import json
filenames = os.listdir('./priorstoadd/')
for fn in filenames:
    if fn == 'apply.txt':
        continue
    fn = fn.split('.')[0].split('-')
    l = fn[0].split('(')[0]
    r = fn[1].split('(')[0]
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

swaplist = open('./priorstoadd/apply.txt')
swaplisttxt = swaplist.read()
for line in swaplisttxt.split('\n'):
    names = line.split(' ')
    print(names)
    with open('../pos-orient-denoised-2/{}.json'.format(names[2])) as f_origin:
        if os.path.isfile('./{}.json'.format(names[0])):
            with open('./{}.json'.format(names[0])) as f_target:
                j_target = json.load(f_target)
        else:
            j_target = {}
        j_target[names[1]] = json.load(f_origin)[names[3]]
        with open('./{}.json'.format(names[0]), 'w') as f_target:
            json.dump(j_target, f_target)
