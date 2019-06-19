import argparse
import os
import sys
import time
import re

import numpy as np
import torch
from torch.optim import Adam
from torch.utils.data import DataLoader
from torchvision import datasets
from torchvision import transforms
import torch.onnx

import bot_utils.utils
from bot_utils.transformer_net import TransformerNet
from bot_utils.vgg import Vgg16


def check_paths(args):
    try:
        if not os.path.exists(args.save_model_dir):
            os.makedirs(args.save_model_dir)
        if args.checkpoint_model_dir is not None and not (os.path.exists(args.checkpoint_model_dir)):
            os.makedirs(args.checkpoint_model_dir)
    except OSError as e:
        print(e)
        sys.exit(1)


def train(args):
    device = torch.device("cuda" if args.cuda else "cpu")

    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    transform = transforms.Compose([
        transforms.Resize(args.image_size),
        transforms.CenterCrop(args.image_size),
        transforms.ToTensor(),
        transforms.Lambda(lambda x: x.mul(255))
    ])
    train_dataset = datasets.ImageFolder(args.dataset, transform)
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size)

    transformer = TransformerNet().to(device)
    optimizer = Adam(transformer.parameters(), args.lr)
    mse_loss = torch.nn.MSELoss()

    vgg = Vgg16(requires_grad=False).to(device)
    style_transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Lambda(lambda x: x.mul(255))
    ])
    style = bot_utils.utils.load_image(args.style_image, size=args.style_size)
    style = style_transform(style)
    style = style.repeat(args.batch_size, 1, 1, 1).to(device)

    features_style = vgg(bot_utils.utils.normalize_batch(style))
    gram_style = [bot_utils.utils.gram_matrix(y) for y in features_style]

    for e in range(args.epochs):
        transformer.train()
        agg_content_loss = 0.
        agg_style_loss = 0.
        count = 0
        for batch_id, (x, _) in enumerate(train_loader):
            n_batch = len(x)
            count += n_batch
            optimizer.zero_grad()

            x = x.to(device)
            y = transformer(x)

            y = bot_utils.utils.normalize_batch(y)
            x = bot_utils.utils.normalize_batch(x)

            features_y = vgg(y)
            features_x = vgg(x)

            content_loss = args.content_weight * mse_loss(features_y.relu2_2, features_x.relu2_2)

            style_loss = 0.
            for ft_y, gm_s in zip(features_y, gram_style):
                gm_y = bot_utils.utils.gram_matrix(ft_y)
                style_loss += mse_loss(gm_y, gm_s[:n_batch, :, :])
            style_loss *= args.style_weight

            total_loss = content_loss + style_loss
            total_loss.backward()
            optimizer.step()

            agg_content_loss += content_loss.item()
            agg_style_loss += style_loss.item()

            if (batch_id + 1) % args.log_interval == 0:
                mesg = "{}\tEpoch {}:\t[{}/{}]\tcontent: {:.6f}\tstyle: {:.6f}\ttotal: {:.6f}".format(
                    time.ctime(), e + 1, count, len(train_dataset),
                                  agg_content_loss / (batch_id + 1),
                                  agg_style_loss / (batch_id + 1),
                                  (agg_content_loss + agg_style_loss) / (batch_id + 1)
                )
                print(mesg)

            if args.checkpoint_model_dir is not None and (batch_id + 1) % args.checkpoint_interval == 0:
                transformer.eval().cpu()
                ckpt_model_filename = "ckpt_epoch_" + str(e) + "_batch_id_" + str(batch_id + 1) + ".pth"
                ckpt_model_path = os.path.join(args.checkpoint_model_dir, ckpt_model_filename)
                torch.save(transformer.state_dict(), ckpt_model_path)
                transformer.to(device).train()

    # сохранение модели
    transformer.eval().cpu()
    save_model_filename = "epoch_" + str(args.epochs) + "_" + str(time.ctime()).replace(' ', '_') + "_" + str(
        args.content_weight) + "_" + str(args.style_weight) + ".model"
    save_model_path = os.path.join(args.save_model_dir, save_model_filename)
    torch.save(transformer.state_dict(), save_model_path)

    print("\nDone, trained model saved at", save_model_path)

def main():
    main_arg_parser = argparse.ArgumentParser(description="parser for fast-neural-style")

    main_arg_parser.add_argument("--epochs", type=int, default=2,
                                  help="Количество тренировочных эпох, по умолчанию: 2.")
    main_arg_parser.add_argument("--batch-size", type=int, default=4,
                                  help="Размер батча для обучения, по умолчанию: 4.")
    main_arg_parser.add_argument("--dataset", type=str, required=True,
                                  help="Путь к тренировочному датасету, путь должен быть указан к папке "
                                       "содержащей другую папку, уже в которой расположены все тренировочные изображения.")
    main_arg_parser.add_argument("--style-image", type=str, default="images/style-images/mosaic.jpg",
                                  help="Путь к картинке со стилем")
    main_arg_parser.add_argument("--save-model-dir", type=str, required=True,
                                  help="Путь к папке, куда будет сохранена натренерованная модель.")
    main_arg_parser.add_argument("--checkpoint-model-dir", type=str, default=None,
                                  help="Путь к папке, где будет сохраняться промежуточное состояние модели.")
    main_arg_parser.add_argument("--image-size", type=int, default=256,
                                  help="Размер тренировочных изображений, по умолчанию: 256 X 256.")
    main_arg_parser.add_argument("--style-size", type=int, default=None,
                                  help="Размер картинки со стилем, по умочанию: полный размер картинки со стилем.")
    main_arg_parser.add_argument("--cuda", type=int, required=True,
                                  help="Поставьте 1 чтобы тренировать на GPU, 0 для CPU")
    main_arg_parser.add_argument("--seed", type=int, default=42,
                                  help="Рандомный seed для тренировки.")
    main_arg_parser.add_argument("--content-weight", type=float, default=1e5,
                                  help="Веса для лосса контента, по умолчанию: 1e5.")
    main_arg_parser.add_argument("--style-weight", type=float, default=1e10,
                                  help="Веса для лосса стиля, по умолчанию: 1e10.")
    main_arg_parser.add_argument("--lr", type=float, default=1e-3,
                                  help="Скорость обучения, по умолчанию: 1e-3.")
    main_arg_parser.add_argument("--log-interval", type=int, default=500,
                                  help="Число картинок, после которых модель запомнит лосс, по умолчанию: 500.")
    main_arg_parser.add_argument("--checkpoint-interval", type=int, default=2000,
                                  help="Количество батчей, после которых точка сохранения модели будет создана.")


    args = main_arg_parser.parse_args()
    check_paths(args)
    train(args)
  


if __name__ == "__main__":
    main()
