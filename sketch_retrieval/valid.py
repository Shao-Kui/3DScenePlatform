import os
import torch
import torch.nn as nn
import torch.nn.functional as F
import argparse
from torch.utils.data.dataloader import DataLoader
from datasets import *
from models import *
from losses import *
from tqdm import tqdm
from time import time
from utils import *
from datetime import datetime
import os.path as osp
import numpy as np
import faiss


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--resume_from', type=str, default=None)
    parser.add_argument('--bs', type=int, default=32)
    parser.add_argument("--n_workers", type=int, default=8)
    parser.add_argument("--sketch_backbone", type=str, default='resnet34')
    parser.add_argument("--render_backbone", type=str, default='resnet34')
    parser.add_argument("--fdim", type=int, default=512)
    parser.add_argument("--num_views", type=int, default=20)
    parser.add_argument("--save_result", action='store_true')
    parser.add_argument("--norm_emb", action='store_true')
    args = parser.parse_args()
    return args


def val(test_dataloader, model, args):
    model.eval()
    index = faiss.IndexFlatL2(args.fdim)

    print('Computing embeddings for models...')
    for batch_data in tqdm(test_dataloader):
        render_data = batch_data['render'].cuda(
            non_blocking=True) if torch.cuda.is_available() else batch_data['render']
        _, render_features = model(None, render_data)
        index.add(render_features.detach().cpu().numpy())
    print('Computing embeddings for sketches...')

    rr = []
    cur = 0

    result = []
    for batch_data in tqdm(test_dataloader):
        sketch_data = batch_data['sketch'].cuda(
            non_blocking=True) if torch.cuda.is_available() else batch_data['sketch']
        sketch_features, render_features = model(sketch_data, None)
        pred = index.search(
            sketch_features.detach().cpu().numpy(), 10)[1]  # bs, 10
        result.append(pred)
        bs = pred.shape[0]
        for i in range(bs):
            for j in range(10):
                if pred[i][j] == cur + i:
                    rr.append(1.0/(i+1))
                    break
            else:
                rr.append(0.0)
        cur += bs
    if args.save_result:
        result = np.concatenate(result, axis=0)
        np.savez('./retrv_result.npz', result=result)
    return sum(rr) / len(rr)


def main():
    args = parse_args()
    test_dataset = MultiViewSketchDataset(
        '/home/tianxing/nas/dataset/ObjectLibrary', '/home/tianxing/nas/dataset/ObjectLibrary_sketch', mode='test')
    collate_fn = test_dataset.create_collate_fn()
    test_dataloader = DataLoader(
        test_dataset,
        batch_size=args.bs,
        shuffle=False,
        pin_memory=False,
        collate_fn=collate_fn,
        num_workers=args.n_workers,
        drop_last=False
    )

    model = CrossModalCNN(dict(
        backbone=args.sketch_backbone,
        pretrained=True,
        feature_dim=args.fdim
    ), dict(
        backbone=args.render_backbone,
        pretrained=True,
        feature_dim=args.fdim,
        num_views=args.num_views
    ))

    if torch.cuda.is_available():
        model = torch.nn.DataParallel(model).cuda()

    assert args.resume_from is not None
    state = torch.load(args.resume_from)
    model.load_state_dict(state['model_state_dict'])

    print('Start validating ...')
    epoch_start_time = time()
    metrics = val(test_dataloader, model, args)
    epoch_end_time = time()
    print('Validating time= %.3fs AvgRR=%.4f' %
          (epoch_end_time - epoch_start_time, metrics))


if __name__ == '__main__':
    main()
