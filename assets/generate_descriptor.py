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

os.environ['CUDA_VISIBLE_DEVICES'] = '0'


model_lib_dir = './sketch_retrieval/models.index'
catalog_dir = './sketch_retrieval/catalog.json'
ckpt_dir = './sketch_retrieval/epoch_57.pth'


net = None
models_index = None
model_names = None


def sketch_search(filename, k=20, classname=None):

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
    pred = models_index.search(
        sketch_features.detach().cpu().numpy(), k)[1]  # bs, 10
    pred = pred[0]
    return [model_names[i] for i in pred]


def init_sketch_retrieval():
    model_lib = faiss.read_index(model_lib_dir)
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
    return model, model_lib, names


net, models_index, model_names = init_sketch_retrieval()

# if __name__ == '__main__':
#     print(datetime.now())
#     results = sketch_search(search_file)
#     print(results)
#     print(datetime.now())
