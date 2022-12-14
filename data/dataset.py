# -*- coding: utf-8 -*-
"""
# @file name  : dataset.py
# @author     : chenzhanpeng https://github.com/chenzpstar
# @date       : 2022-07-26
# @brief      : 数据集读取类
"""

import os
import random
from functools import partial

import cv2
import numpy as np
import torch
from torch.utils.data import Dataset
from torchvision import transforms as tf

try:
    from .transform import norm, transform
except:
    from transform import norm, transform


class FusionDataset(Dataset):
    def __init__(self,
                 root_dir,
                 set_name,
                 mode='dolp',
                 norm=None,
                 transform=False):
        super(FusionDataset, self).__init__()
        self.root_dir = root_dir
        self.set_name = set_name
        self.mode = mode
        self.norm = norm
        self.transform = transform
        self.data_info = []
        self._get_data_info()

    def __getitem__(self, index):
        img_path1, img_path2 = self.data_info[index]
        img1 = cv2.imread(img_path1, cv2.IMREAD_GRAYSCALE).astype(np.float32)
        img2 = cv2.imread(img_path2, cv2.IMREAD_GRAYSCALE).astype(np.float32)
        imgs = (img1, img2)

        imgs = tuple(map(partial(norm, mode=self.norm), imgs))

        if self.transform:
            idx = np.random.choice(4)
            imgs = tuple(map(partial(transform, mode=idx), imgs))

        imgs = tuple(
            map(lambda img: torch.from_numpy(img[None, :].copy()).float(),
                imgs))

        return imgs

    def __len__(self):
        assert len(self.data_info) > 0
        return len(self.data_info)

    def _get_data_info(self):
        img_dir = os.path.join(self.root_dir, self.set_name, 'vis')

        for img in os.listdir(img_dir):
            if img.endswith('.bmp') or img.endswith('.jpg'):
                img_path1 = os.path.join(img_dir, img)

                assert self.mode in ['dolp', 'ir']
                img_path2 = img_path1.replace('vis', self.mode)

                if os.path.isfile(img_path2):
                    self.data_info.append((img_path1, img_path2))

        random.shuffle(self.data_info)


class AEDataset(Dataset):
    def __init__(self, root_dir, mode='dolp', norm=None, transform=False):
        super(AEDataset, self).__init__()
        self.root_dir = root_dir
        self.mode = mode
        self.norm = norm
        self.transform = transform
        self.data_info = []
        self._get_data_info()

    def __getitem__(self, index):
        img_path = self.data_info[index]
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE).astype(np.float32)
        img = norm(img, mode=self.norm)

        if self.transform:
            idx = np.random.choice(2)
            img = transform(img, mode=idx)

        img = torch.from_numpy(img[None, :].copy()).float()

        min_size = min(img.shape[-2:])
        img = tf.RandomCrop(min_size)(img)
        img = tf.Resize(224)(img)

        return img

    def __len__(self):
        assert len(self.data_info) > 0
        return len(self.data_info)

    def _get_data_info(self):
        img_dir1 = os.path.join(self.root_dir, 'vis')

        assert self.mode in ['dolp', 'ir']
        img_dir2 = img_dir1.replace('vis', self.mode)

        for img in os.listdir(img_dir1):
            if img.endswith('.jpg'):
                img_path = os.path.join(img_dir1, img)
                self.data_info.append(img_path)

        for img in os.listdir(img_dir2):
            if img.endswith('.jpg'):
                img_path = os.path.join(img_dir2, img)
                self.data_info.append(img_path)

        random.shuffle(self.data_info)


if __name__ == '__main__':

    import os
    import sys

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.join(BASE_DIR, '..'))

    from torch.utils.data import DataLoader

    from transform import denorm

    # flag = 0
    flag = 1

    if flag == 0:
        train_path = os.path.join(BASE_DIR, 'samples')
        train_set = FusionDataset(train_path,
                                  'train',
                                  norm='min-max',
                                  transform=True)
        train_loader = DataLoader(
            train_set,
            batch_size=1,
            shuffle=True,
            num_workers=0,
        )

        for img1, img2 in train_loader:
            result = tuple(
                map(denorm, (img1[0], img2[0], (img1[0] + img2[0]) / 2.0)))
            result = np.concatenate(result, axis=1)

            cv2.namedWindow('demo', cv2.WINDOW_NORMAL)
            cv2.resizeWindow('demo', result.shape[1] // 2,
                             result.shape[0] // 2)
            cv2.imshow('demo', result)
            cv2.waitKey()
            cv2.destroyAllWindows()

    if flag == 1:
        train_path = os.path.join(BASE_DIR, 'samples', 'train')
        train_set = AEDataset(train_path, norm='min-max', transform=True)
        train_loader = DataLoader(
            train_set,
            batch_size=1,
            shuffle=True,
            num_workers=0,
        )

        for img in train_loader:
            result = denorm(img[0])

            cv2.namedWindow('demo', cv2.WINDOW_FULLSCREEN)
            cv2.imshow('demo', result)
            cv2.waitKey()
            cv2.destroyAllWindows()
