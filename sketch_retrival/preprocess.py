#coding=utf-8

import os
import glob
import random
import shutil

def model_statistics():
    objs=[]
    with open('categories.txt','r') as inf:
        objs=[line.split('\t')[1:3] for line in inf]

    objs_data=glob.glob('../objedge20/*')
    objs_data = [d.split('/')[-1] for d in objs_data]
    objs = [d for d in objs if d[0] in objs_data and not d[1] in ['door','wall','window','floor','ceil']]
    classnames = list(set([d[1] for d in objs]))
    return classnames,objs


def fix_views():
    for obj_dir in glob.glob('../objedge20/*'):
        files = glob.glob(obj_dir+'/*-edge.png')
        copys = random.sample(files,20-len(files))
        for copy in copys:
            shutil.copyfile(copy,copy.replace('-edge','-edge-copy'))


if __name__ == '__main__':
    fix_views()

