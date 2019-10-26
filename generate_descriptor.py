#coding=utf-8

import torch
import time
import glob
import os,shutil,json
from datetime import datetime
from sketch_retrival import *

from sketch_retrival.tools.ImgDataset import SingleImgDataset
from sketch_retrival.models.MVCNN import SVCNN
from torch.autograd import Variable
import torch.nn as nn
import numpy as np
import heapq

category_file='./sketch_retrival/categories.txt'
objedge_dir='./sketch_retrival/objedge20/'
feature_dir = './sketch_retrival/features/'
model_dir = './sketch_retrival/MVCNN_stage_1'
search_file = './sketch_retrival/qs.png'

def generate_all_features(cnet,classnames,objs):
    val_dataset = SingleImgDataset(objedge_dir, classnames,objs,test_mode=True)
    val_loader = torch.utils.data.DataLoader(val_dataset, batch_size=64, shuffle=False, num_workers=0)

    features = []
    objs = []
    for _, data in enumerate(val_loader, 0):
        files = data[2]
        x = Variable(data[1]).cuda()
        y = cnet.net_1(x)
        y = y.view(y.shape[0],-1)
        for i in  range(5):
            y = cnet.net_2._modules[str(i)](y)
        y = y.cpu().data.numpy()
        for i in range(len(files)):
            obj = files[i].split('/')[-2]
            feature = y[i]
            #print(obj,feature)
            features.append(feature)
            objs.append(obj)
    
    return features,objs

def generate_feature(cnet,filename):
    val_dataset = SingleImgDataset(objedge_dir, ['tmp'],[],test_mode=True)
    val_dataset.filepaths=[[filename,'tmp']]
    val_loader = torch.utils.data.DataLoader(val_dataset, batch_size=1, shuffle=False, num_workers=0)

    feature = None
    for _, data in enumerate(val_loader, 0):
        x = Variable(data[1]).cuda()
        y = cnet.net_1(x)
        y = y.view(y.shape[0],-1)
        for i in  range(5):
            y = cnet.net_2._modules[str(i)](y)
        y = y.cpu().data.numpy()
        feature=y[0]
    return feature

def model_statistics():
    objs=[]
    with open(category_file,'r') as inf:
        objs=[line.split('\t')[1:3] for line in inf]

    objs_data=glob.glob(objedge_dir+'*')
    #print(objs_data)
    # Warning: in Linux use '/' and in Windows use '\\'
    objs_data = [d.split('\\')[-1] for d in objs_data]
    objs = [d for d in objs if d[0] in objs_data and not d[1] in ['door','wall','window','floor','ceil']]
    keys = {}
    for d in objs:
        keys[d[0]]=d[1]
    classnames = list(set([d[1] for d in objs]))
    return classnames,objs,keys


def load_cnet():
    classnames,objs,keys = model_statistics()

    #print(classnames,objs)
    # model=2493,classnames=180
    cnet = SVCNN("MVCNN", nclasses=len(classnames))
    cnet.load(model_dir)
    cnet.cuda()
    cnet.eval()

    if os.path.exists(feature_dir+'features.npy'):
        features = np.load(feature_dir+'features.npy')
        objs = np.load(feature_dir+'objs.npy')
    else:
        features,objs = generate_all_features(cnet,classnames,objs)
        features = np.array(features)
        objs= np.array(objs)
        np.save(feature_dir+'features.npy',features)
        np.save(feature_dir+'objs.npy',objs)
    
    return cnet,features,objs,keys


def sketch_search(filename=search_file,k=20,classname=None):
    start_time = time.time()
    f_42 = generate_feature(cnet,filename)
    
    print("\r\n\r\n------- %s secondes1 --- \r\n\r\n" % (time.time() - start_time))
    
    #print(datetime.now())
    if not classname:
        key_features = features.copy()
        key_objs = objs.copy()
    else:
        key_features =[]
        key_objs = []
        for feature,o in zip(features,objs):
            if classname == keys[o]:
                key_features.append(feature)
                key_objs.append(o)
        key_features = np.array(key_features)
        key_objs = np.array(key_objs)

    print("\r\n\r\n------- %s secondes2 --- \r\n\r\n" % (time.time() - start_time))
    #print(len(key_features),len(key_objs),'-----------------------------')
    distances = np.linalg.norm(key_features-f_42,axis=1)
    distances = distances.tolist()
    #print(datetime.now())
    min_num_index=map(distances.index, heapq.nsmallest(k,distances))
    end_time = time.time()
    print("\r\n\r\n------- %s secondes3 --- \r\n\r\n" % (end_time - start_time))
    results = [key_objs[x] for x in min_num_index]
    return results
    

cnet,features,objs,keys = load_cnet()

if __name__ == '__main__':
    print(datetime.now())
    results = sketch_search(search_file)
    print(results)
    print(datetime.now())
