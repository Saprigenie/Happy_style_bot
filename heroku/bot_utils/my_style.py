﻿import os
import sys
import time
import re
from PIL import Image

import numpy as np
import torch
from torch.optim import Adam
from torch.utils.data import DataLoader
from torchvision import datasets
from torchvision import transforms

import bot_utils.utils
from bot_utils.transformer_net import TransformerNet
from bot_utils.vgg import Vgg16


def stylize(content_image, model):
    device = torch.device("cpu")

    content_image = bot_utils.utils.load_image(content_image)
    content_transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Lambda(lambda x: x.mul(255))
    ])
    content_image = content_transform(content_image)
    content_image = content_image.unsqueeze(0).to(device)
    with torch.no_grad():
        style_model = TransformerNet()
        state_dict = torch.load(model)
        # remove saved deprecated running_* keys in InstanceNorm from the checkpoint
        for k in list(state_dict.keys()):
            if re.search(r'in\d+\.running_(mean|var)$', k):
                del state_dict[k]
        style_model.load_state_dict(state_dict)
        style_model.to(device)
        output = style_model(content_image).cpu()
    img = output.clone().clamp(0, 255).numpy()
    img = img.squeeze(0)
    img = img.transpose(1, 2, 0).astype("uint8")
    img = Image.fromarray(img)
    return img