#coding=utf-8

import numpy as np
import glob
import torch.utils.data
import os
import math
from skimage import io, transform
from PIL import Image
import torch
import torchvision as vision
from torchvision import transforms, datasets
import random

class MultiviewImgDataset(torch.utils.data.Dataset):

    def __init__(self, root_dir,classnames,objs,scale_aug=False, rot_aug=False, test_mode=False, num_views=20, shuffle=True):
        
        self.root_dir = root_dir
        self.scale_aug = scale_aug
        self.rot_aug = rot_aug
        self.test_mode = test_mode
        self.num_views = num_views
        self.classnames=classnames

        self.filepaths = []
        for obj,classname in objs:
            files = glob.glob(root_dir+obj+'/*.png')
            for file in files:
                self.filepaths.append([file,classname])
        
        if shuffle==True:
            # permute
            rand_idx = np.random.permutation(int(len(self.filepaths)/num_views))
            filepaths_new = []
            for i in range(len(rand_idx)):
                filepaths_new.extend(self.filepaths[rand_idx[i]*num_views:(rand_idx[i]+1)*num_views])
            self.filepaths = filepaths_new


        if self.test_mode:
            self.transform = transforms.Compose([
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                     std=[0.229, 0.224, 0.225])
            ])    
        else:
            self.transform = transforms.Compose([
                transforms.RandomHorizontalFlip(),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                     std=[0.229, 0.224, 0.225])
            ])


    def __len__(self):
        return int(len(self.filepaths)/self.num_views)


    def __getitem__(self, idx):
        path = self.filepaths[idx*self.num_views]
        class_name = path[1]
        class_id = self.classnames.index(class_name)
        # Use PIL instead
        imgs = []
        for i in range(self.num_views):
            im = Image.open(self.filepaths[idx*self.num_views+i][0]).convert('RGB')
            im = im.resize((224,224))
            if self.transform:
                im = self.transform(im)
            imgs.append(im)

        return (class_id, torch.stack(imgs))



class SingleImgDataset(torch.utils.data.Dataset):

    def __init__(self, root_dir, classnames,objs,scale_aug=False, rot_aug=False, test_mode=False, num_views=20):
        
        self.root_dir = root_dir
        self.scale_aug = scale_aug
        self.rot_aug = rot_aug
        self.test_mode = test_mode
        self.classnames=classnames
        self.objs=objs

        self.filepaths = []
        for obj,classname in objs:
            files = glob.glob(root_dir+obj+'/*.png')
            for file in files:
                self.filepaths.append([file,classname])
        #print(objs)
        #print(len(self.filepaths))
        if self.test_mode:
            self.transform = transforms.Compose([
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                     std=[0.229, 0.224, 0.225])
            ])    
        else:
            self.transform = transforms.Compose([
                transforms.RandomHorizontalFlip(),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                     std=[0.229, 0.224, 0.225])
            ])



    def __len__(self):
        return len(self.filepaths)


    def __getitem__(self, idx):
        path = self.filepaths[idx]
        class_name = path[1]
        class_id = self.classnames.index(class_name)

        # Use PIL instead
        im = Image.open(path[0]).convert('RGB')
        im = im.resize((224,224))
        if self.transform:
            im = self.transform(im)

        return (class_id, im,path[0])

