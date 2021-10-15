# coding=utf-8

from sketch_retrieval.models import *
from PIL import Image
from torchvision import transforms
import numpy as np
import torch.nn as nn
import torch
import faiss
import time
import glob
import os
import json
import sk

os.environ['CUDA_VISIBLE_DEVICES'] = '0'


model_lib_dir = './sketch_retrieval/models.index'
suncg_model_lib_dir = './sketch_retrieval/suncg_models.index'
non_suncg_model_lib_dir = './sketch_retrieval/non_suncg_models.index'

catalog_dir = './sketch_retrieval/catalog.json'
suncg_catalog_dir = './sketch_retrieval/catalog_suncg.json'
non_suncg_catalog_dir = './sketch_retrieval/catalog_non_suncg.json'
ckpt_dir = './sketch_retrieval/epoch_57.pth'


net = None
models_index = None
model_names = None
suncg_models_index = None
suncg_model_names = None
non_suncg_models_index = None
non_suncg_model_names = None


def sketch_search(filename, k=20, classname=None):

    sketch_aug = transforms.Compose([
        transforms.CenterCrop((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225])
    ])
    sketch_img = Image.open(filename).convert('RGB')
    start_time = time.time()
    sketch_img = sketch_aug(sketch_img)
    sketch_img = torch.stack([sketch_img])
    sketch_data = sketch_img.cuda(non_blocking=True)
    sketch_features, _ = net(sketch_data, None)
    detachedFeatures = sketch_features.detach().cpu().numpy()
    end_time = time.time()
    print("\r\n------- %s secondes --- \r\n" % (end_time - start_time))
    if classname is None:
        pred = models_index.search(detachedFeatures, k)[1]  # bs, 10
        pred = pred[0]
        res = [model_names[i] for i in pred]
    else:
        for F in (2**np.arange(1,7)).tolist():
            pred = models_index.search(detachedFeatures, k*F)[1]  # bs, 10
            pred = pred[0]
            res = []
            for i in pred:
                if sk.getobjCat(model_names[i]) == classname:
                    res.append(model_names[i])
            if len(res) >= k:
                break
        print(f'total iterations: {F}')
    return res

def sketch_search_suncg(filename, k=20, classname=None):

    sketch_aug = transforms.Compose([
        transforms.CenterCrop((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225])
    ])
    sketch_img = Image.open(filename).convert('RGB')
    sketch_img = sketch_aug(sketch_img)
    sketch_img = torch.stack([sketch_img])
    sketch_data = sketch_img.cuda(non_blocking=True)
    sketch_features, _ = net(sketch_data, None)
    pred = suncg_models_index.search(
        sketch_features.detach().cpu().numpy(), k)[1]  # bs, 10
    pred = pred[0]
    return [suncg_model_names[i] for i in pred]


def sketch_search_non_suncg(filename, k=20, classname=None):

    sketch_aug = transforms.Compose([
        transforms.CenterCrop((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225])
    ])
    sketch_img = Image.open(filename).convert('RGB')
    sketch_img = sketch_aug(sketch_img)
    sketch_img = torch.stack([sketch_img])
    sketch_data = sketch_img.cuda(non_blocking=True)
    sketch_features, _ = net(sketch_data, None)
    pred = non_suncg_models_index.search(
        sketch_features.detach().cpu().numpy(), k)[1]  # bs, 10
    pred = pred[0]
    return [non_suncg_model_names[i] for i in pred]


def init_sketch_retrieval():
    model_lib = faiss.read_index(model_lib_dir)
    suncg_model_lib = faiss.read_index(suncg_model_lib_dir)
    non_suncg_model_lib = faiss.read_index(non_suncg_model_lib_dir)
    model = CrossModalCNN(dict(
        backbone='resnet34',
        pretrained=False,
        feature_dim=512
    ), dict(
        backbone='resnet34',
        pretrained=False,
        feature_dim=512,
        num_views=20
    ))
    model = torch.nn.DataParallel(model).cuda()
    state = torch.load(ckpt_dir)
    model.load_state_dict(state['model_state_dict'])
    model.eval()
    with open(catalog_dir, 'r') as f:
        names = json.load(f)
        names = names['models']
    with open(suncg_catalog_dir, 'r') as f:
        suncg_names = json.load(f)
        suncg_names = suncg_names['models']
    with open(non_suncg_catalog_dir, 'r') as f:
        non_suncg_names = json.load(f)
        non_suncg_names = non_suncg_names['models']
    return model, model_lib, names, suncg_model_lib, suncg_names, non_suncg_model_lib, non_suncg_names


net, models_index, model_names, suncg_models_index, suncg_model_names, non_suncg_models_index, non_suncg_model_names = init_sketch_retrieval()

# if __name__ == '__main__':
#     print(datetime.now())
#     results = sketch_search(search_file)
#     print(results)
#     print(datetime.now())
