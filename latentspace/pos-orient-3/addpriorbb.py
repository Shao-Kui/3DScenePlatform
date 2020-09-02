import os
import sys
import json
import torch
import numpy as np
import visprior
import threading
import patternChain
four_points_xz = torch.load('../four_points_xz.pt').numpy()
with open('../name_to_ls.json') as f:
    name_to_ls = json.load(f)
with open('../ls_to_name.json') as f:
    ls_to_name = json.load(f)

def bbfitting(pattern, bborigin, bbnow, rotateInverse=False):
    # print(pattern[-1])
    pattern = np.array(pattern)
    ratio = bbnow / bborigin
    # print(ratio)
    qdt1 = np.intersect1d(np.where(pattern[:, 0] > 0), np.where(pattern[:, 2] > 0))
    qdt2 = np.intersect1d(np.where(pattern[:, 0] < 0), np.where(pattern[:, 2] > 0))
    qdt3 = np.intersect1d(np.where(pattern[:, 0] < 0), np.where(pattern[:, 2] < 0))
    qdt4 = np.intersect1d(np.where(pattern[:, 0] > 0), np.where(pattern[:, 2] < 0))
    # print(qdt1, qdt2, qdt3, qdt4)
    if len(qdt1) != 0:
        pattern[qdt1, 0] *= ratio[0][0]
        pattern[qdt1, 2] *= ratio[0][1]
    if len(qdt2) != 0:
        pattern[qdt2, 0] *= ratio[1][0]
        pattern[qdt2, 2] *= ratio[1][1]
    if len(qdt3) != 0:
        pattern[qdt3, 0] *= ratio[2][0]
        pattern[qdt3, 2] *= ratio[2][1]
    if len(qdt4) != 0:
        pattern[qdt4, 0] *= ratio[3][0]
        pattern[qdt4, 2] *= ratio[3][1]
    # print(pattern.tolist()[-1])
    if rotateInverse:
        pattern[:, 3] += np.pi
    return pattern.tolist()

def addpriorbb(names, check_pc=False, rotateInverse=False):
    with open('../pos-orient-denoised-2/{}.json'.format(names[2])) as f_origin:
        if os.path.isfile('./{}.json'.format(names[0])):
            with open('./{}.json'.format(names[0])) as f_target:
                j_target = json.load(f_target)
        else:
            j_target = {}
        j_target[names[1]] = bbfitting(
            json.load(f_origin)[names[3]], 
            four_points_xz[name_to_ls[names[2]]], 
            four_points_xz[name_to_ls[names[0]]],rotateInverse=rotateInverse
            )
        with open('./{}.json'.format(names[0]), 'w') as f_target:
            json.dump(j_target, f_target)
    if check_pc:
        print('start to generate pattern chain')
        threading.Thread(target=patternChain.patternChainHomo, args=(names[0], names[1])).start()
    with open("transferlog.txt", "a") as transferlog:
        transferlog.write(' '.join(names) + '\n')
    visprior.plot_orth(names[0], names[1])

if __name__ == '__main__':
    thenames = sys.argv[1:5]
    if len(sys.argv) == 6:
        addpriorbb(thenames, check_pc=True)
    elif len(sys.argv) == 7:
        addpriorbb(thenames, check_pc=bool(sys.argv[5]), rotateInverse=bool(sys.argv[6]))
    else:
        addpriorbb(thenames)
