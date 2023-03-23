import torch
import os
from torch import random
from torchvision import transforms
from PIL import Image
import random
from torch.utils.data import DataLoader
import cv2


class MultiViewSketchDataset(torch.utils.data.Dataset):

    def __init__(self, render_data_dir, sketch_data_dir, num_views=20, mode='train'):
        super().__init__()
        self.render_data_dir = render_data_dir
        self.sketch_data_dir = sketch_data_dir
        self.model_ids = sorted(os.listdir(self.sketch_data_dir))
        self.render_img_dir = os.path.join(
            self.render_data_dir, '{0}', 'render20', 'render-{0}-{1}.png')
        self.sketch_img_dir = os.path.join(
            self.sketch_data_dir, '{0}', 'render-{0}-{1}-sketch.png')
        self.num_views = num_views
        self.mode = mode

        if mode == 'train':
            self.render_aug = transforms.Compose([
                transforms.RandomAffine(degrees=0, translate=(0.03, 0.03)),
                transforms.CenterCrop((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                     std=[0.229, 0.224, 0.225])
            ])
            self.sketch_aug = transforms.Compose([
                transforms.RandomAffine(degrees=0, translate=(0.03, 0.03)),
                transforms.CenterCrop((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                     std=[0.229, 0.224, 0.225])
            ])
        else:
            self.render_aug = transforms.Compose([
                transforms.CenterCrop((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                     std=[0.229, 0.224, 0.225])
            ])
            self.sketch_aug = transforms.Compose([
                transforms.CenterCrop((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                     std=[0.229, 0.224, 0.225])
            ])

    def __len__(self):
        return len(self.model_ids)

    def __getitem__(self, idx):

        render_imgs = []
        sketch_imgs = []

        for v in range(self.num_views):
            render_img = self.render_img_dir.format(self.model_ids[idx], v)
            sketch_img = self.sketch_img_dir.format(self.model_ids[idx], v)
            if not os.path.exists(render_img) or not os.path.exists(sketch_img):
                continue
            try:
                render_img = Image.open(render_img).convert('RGB')
            except:
                continue
            render_img = self.render_aug(render_img)
            sketch_img = Image.open(sketch_img).convert('RGB')
            sketch_img = self.sketch_aug(sketch_img)
            render_imgs.append(render_img)
            sketch_imgs.append(sketch_img)
        if len(render_imgs) == 0:
            print(self.render_img_dir.format(self.model_ids[idx], 0))
        if len(sketch_imgs) == 0:
            print(self.sketch_img_dir.format(self.model_ids[idx], 0))

        while len(render_imgs) < self.num_views:
            render_imgs.append(render_imgs[-1])
            sketch_imgs.append(sketch_imgs[-1])
        return torch.stack(render_imgs), torch.stack(sketch_imgs)

    def create_collate_fn(self):

        def collate_fn(batch):

            batch_render_imgs = []
            batch_sketch_imgs = []

            for render_imgs, sketch_imgs in batch:
                batch_render_imgs.append(render_imgs)
                if self.mode == 'train':
                    batch_sketch_imgs.append(
                        sketch_imgs[random.randint(0, self.num_views-1)])
                else:
                    batch_sketch_imgs.append(sketch_imgs[0])
            return {
                'render': torch.stack(batch_render_imgs),
                'sketch': torch.stack(batch_sketch_imgs)
            }
        return collate_fn


if __name__ == '__main__':
    dataset = MultiViewSketchDataset('../sk_data', '../sk_data_sketch')
    collate_fn = dataset.create_collate_fn()
    dataloader = DataLoader(
        dataset,
        batch_size=1,
        shuffle=True,
        pin_memory=False,
        collate_fn=collate_fn,
        num_workers=4,
    )
    for batch_idx, data in enumerate(dataloader):
        render_imgs = data['render']
        sketch_imgs = data['sketch']
        print(render_imgs.shape)
        print(sketch_imgs.shape)
        # ex_img = render_imgs[0][0].permute(1, 2, 0)
        # cv2.imwrite('test.png', (ex_img.numpy()*255))
        break
