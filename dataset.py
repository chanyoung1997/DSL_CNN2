import numpy as np

from PIL import Image
from pycocotools.coco import COCO

import torch
from torch.utils.data import Dataset


# DACON - Pytorch Dataset
class ODDataset(Dataset):
    def __init__(self, json_path, image_dir_path, device, transforms=None):
        self.coco = COCO(json_path)
        # self.image_ids = list(self.coco.imgToAnns.keys())
        self.image_ids = list(self.coco.getImgIds())
        self.transforms = transforms
        self.image_path = image_dir_path
        self.device = device

    def __len__(self):
        return len(self.image_ids)

    def __getitem__(self, idx):
        image_id = self.image_ids[idx]
        file_name = self.coco.loadImgs(image_id)[0]['file_name']
        file_name = f'{self.image_path}/{file_name}'
        image = Image.open(file_name).convert('RGB')

        annot_ids = self.coco.getAnnIds(imgIds=image_id)
        annots = [x for x in self.coco.loadAnns(annot_ids) if x['image_id'] == image_id]

        boxes = np.array([annot['bbox'] for annot in annots], dtype=np.float32)
        boxes[:, 2] = boxes[:, 0] + boxes[:, 2]
        boxes[:, 3] = boxes[:, 1] + boxes[:, 3]

        labels = np.array([annot['category_id'] for annot in annots], dtype=np.int32)
        masks = np.array([self.coco.annToMask(annot) for annot in annots], dtype=np.uint8)

        area = np.array([annot['area'] for annot in annots], dtype=np.float32)
        iscrowd = np.array([annot['iscrowd'] for annot in annots], dtype=np.uint8)

        target = {
            'boxes': boxes,
            'masks': masks,
            'labels': labels,
            'area': area,
            'iscrowd': iscrowd}

        if self.transforms is not None:
            image, target = self.transforms(image, target)

        target['boxes'] = torch.as_tensor(target['boxes'], dtype=torch.float32).to(self.device)
        target['masks'] = torch.as_tensor(target['masks'], dtype=torch.uint8).to(self.device)
        target['labels'] = torch.as_tensor(target['labels'], dtype=torch.int64).to(self.device)
        target['area'] = torch.as_tensor(target['area'], dtype=torch.float32).to(self.device)
        target['iscrowd'] = torch.as_tensor(target['iscrowd'], dtype=torch.uint8).to(self.device)

        image.to(self.device)
        return image, target
