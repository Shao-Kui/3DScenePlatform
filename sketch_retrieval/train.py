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
import faiss


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--resume_from', type=str, default=None)
    parser.add_argument('--bs', type=int, default=32)
    parser.add_argument("--lr", type=float, default=5e-5)
    parser.add_argument("--wd", type=float, default=0.0)
    parser.add_argument("--n_epochs", type=int, default=100)
    parser.add_argument("--sched_step", type=int, default=50)
    parser.add_argument("--n_workers", type=int, default=8)
    parser.add_argument("--sketch_backbone", type=str, default='resnet34')
    parser.add_argument("--render_backbone", type=str, default='resnet34')
    parser.add_argument("--fdim", type=int, default=512)
    parser.add_argument("--num_views", type=int, default=20)
    parser.add_argument("--val_per_epoch", type=int, default=5)
    parser.add_argument("--margin", type=float, default=0.2)
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
    for batch_data in tqdm(test_dataloader):
        sketch_data = batch_data['sketch'].cuda(
            non_blocking=True) if torch.cuda.is_available() else batch_data['sketch']
        sketch_features, render_features = model(sketch_data, None)
        pred = index.search(
            sketch_features.detach().cpu().numpy(), 10)[1]  # bs, 10
        bs = pred.shape[0]
        for i in range(bs):
            for j in range(10):
                if pred[i][j] == cur + i:
                    rr.append(1.0/(i+1))
                    break
            else:
                rr.append(0.0)
        cur += bs
    return sum(rr) / len(rr)


def main():
    args = parse_args()
    train_dataset = MultiViewSketchDataset(
        '/home/tianxing/nas/dataset/ObjectLibrary', '/home/tianxing/nas/dataset/ObjectLibrary_sketch', mode='train')
    collate_fn = train_dataset.create_collate_fn()
    train_dataloader = DataLoader(
        train_dataset,
        batch_size=args.bs,
        shuffle=True,
        pin_memory=False,
        collate_fn=collate_fn,
        num_workers=args.n_workers,
        drop_last=True
    )

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

    save_dir = os.path.abspath(os.path.join(
        './workspace', datetime.now().strftime(r'%Y-%m-%d_%H-%M-%S')))
    os.makedirs(save_dir)

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

    optimizer = torch.optim.Adam(
        model.parameters(), lr=args.lr, weight_decay=args.wd)
    scheduler = torch.optim.lr_scheduler.StepLR(
        optimizer, step_size=args.sched_step, gamma=0.2)

    if args.resume_from is not None:
        state = torch.load(args.resume_from)
        model.load_state_dict(state['model_state_dict'])

    loss_fn = BatchHardTripletLossWithMasks(args.margin, args.norm_emb)

    for epoch in range(args.n_epochs):

        print('[Epoch%4d/%4d] Start training ...' % (epoch+1, args.n_epochs))
        model.train()
        epoch_start_time = time()
        losses = None
        with tqdm(total=len(train_dataloader)) as pbar:
            for batch_idx, batch_data in enumerate(train_dataloader):
                sketch_data = batch_data['sketch'].cuda(
                    non_blocking=True) if torch.cuda.is_available() else batch_data['sketch']
                render_data = batch_data['render'].cuda(
                    non_blocking=True) if torch.cuda.is_available() else batch_data['render']
                optimizer.zero_grad()
                sketch_features, render_features = model(
                    sketch_data, render_data)
                features = torch.cat((sketch_features, render_features), dim=0)
                bs = features.shape[0] // 2
                zero_mask = torch.zeros((bs, bs), dtype=torch.bool)
                diag_mask = torch.eye(bs, dtype=torch.bool)
                n_diag_mask = torch.logical_not(diag_mask)
                pos_mask = torch.cat((torch.cat((zero_mask, diag_mask), dim=0), torch.cat(
                    (diag_mask, zero_mask), dim=0)), dim=1)
                neg_mask = torch.cat((torch.cat((zero_mask, n_diag_mask), dim=0), torch.cat(
                    (n_diag_mask, zero_mask), dim=0)), dim=1)
                loss, loss_stats, _ = loss_fn(
                    embeddings=features, positives_mask=pos_mask, negatives_mask=neg_mask)
                loss_info = {
                    'loss': loss_stats['loss'],
                    'mean_pos_pair_dist': loss_stats['mean_pos_pair_dist'],
                    'mean_neg_pair_dist': loss_stats['mean_neg_pair_dist'],
                    'num_non_zero_triplets': loss_stats['num_non_zero_triplets'],
                    'num_triplets': loss_stats['num_triplets']
                }
                loss.backward()
                if losses is None:
                    losses = AverageValue(list(loss_info.keys()))
                losses.update(loss_info)
                optimizer.step()
                torch.cuda.empty_cache()
                details = {}
                details.update(losses.avg() if type(losses.avg())
                               == dict else {'loss': losses.avg()})
                pbar.set_postfix(**details)
                pbar.update(1)

        scheduler.step()
        epoch_end_time = time()
        print(
            '[Epoch%4d/%4d] Training time= %.3fs %s' %
            (epoch+1, args.n_epochs, epoch_end_time - epoch_start_time, losses.avg_str()))

        if epoch % args.val_per_epoch == 0 or epoch == args.n_epochs:
            print('[Epoch%4d/%4d] Start validating ...' %
                  (epoch+1, args.n_epochs))
            epoch_start_time = time()
            metrics = val(test_dataloader, model, args)
            epoch_end_time = time()
            print('[Epoch%4d/%4d] Validating time= %.3fs AvgRR=%.4f' %
                  (epoch+1, args.n_epochs, epoch_end_time - epoch_start_time, metrics))
            torch.save(dict(
                epoch=epoch,
                model_state_dict=model.state_dict(),
            ), os.path.join(save_dir, 'epoch_%d.pth' % epoch))


if __name__ == '__main__':
    main()
