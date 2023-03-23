# coding=utf-8

import cv2
import os
import glob
from tqdm import tqdm


def edgeDetect(input_dir, save_dir):
    filenames = glob.glob(os.path.join(input_dir, '*/render20/*-d.png'))
    for filename in tqdm(filenames):
        # print(filename)
        img = cv2.imread(filename)
        if img.sum() == 0:
            continue
        edge_img = cv2.Canny(img, 1, 40)
        edge_img = 255-edge_img
        edge_filename = filename.split('/')[-1].replace('-d', '-sketch')
        edge_path = os.path.join(save_dir, filename.split('/')[-3])
        if not os.path.exists(edge_path):
            os.makedirs(edge_path)
        # print(os.path.join(edge_path, edge_filename))
        cv2.imwrite(os.path.join(edge_path, edge_filename), edge_img)


if __name__ == '__main__':
    edgeDetect('/home/tianxing/nas/dataset/ObjectLibrary/',
               '/home/tianxing/nas/dataset/ObjectLibrary_sketch/')
