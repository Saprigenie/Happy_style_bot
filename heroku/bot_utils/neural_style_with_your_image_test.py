import numpy as np
from PIL import Image
from io import BytesIO

import torch
import torch.nn as nn
import torch.optim as optim
import torchvision.models as models
import torchvision.transforms as transforms
from torch.autograd import Variable

# Эта переменная необходима боту для запоминания сообщений
msg = None


# some functions to deal with image
def imload(image_name,**kwargs):
    # a function to load image and transfer to Pytorch Variable.
    image = Image.open(image_name)
    if 'resize' in kwargs:
        resize = transforms.Scale(kwargs['resize'])
        image = resize(image)
    transform = transforms.Compose([
        transforms.ToTensor(),#Converts (H x W x C) of[0, 255] to (C x H x W) of range [0.0, 1.0]. 
        transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),])
    image = Variable(transform(image),volatile=True)
    image = image.unsqueeze(0) 
    return image
   
def imshow_bot(bot, update, img, description):
    img = toImage(img[0].data*0.5+0.5)     
    continue_stream = BytesIO()
    img.save(continue_stream, format='PNG')
    continue_stream.seek(0)
    message = bot.send_photo(update.message.chat_id, continue_stream, description)
    return message

def imsave(img,path):
    # convert torch tensor to PIL image and then save to path
    img=toImage(img[0].data*0.5+0.5) # denormalize tensor before convert
    img.save(path)
    
class FeatureExtracter(nn.Module):
    # a nn.Module class to extract a intermediate activation of a Torch module
    def __init__(self,submodule):
        super().__init__()
        self.submodule = submodule
    def forward(self,image,layers):
        features = []
        for i in range(layers[-1]+1):
            image = self.submodule[i](image)
            if i in layers :
                features.append(image)       
        return features
      
class GramMatrix(nn.Module):
    # a nn.Module class to build gram matrix as style feature
    def forward(self,style_features):
        gram_features=[]
        for feature in style_features:
            n,f,h,w = feature.size()
            feature = feature.resize(n*f,h*w)
            gram_features.append((feature@feature.t()).div_(2*n*f*h*w))
        return gram_features
      
class Stylize(nn.Module): 
    def forward(self,x):
        s_feats = feature(x,STYLE_LAYER)
        s_feats = gram(s_feats)
        c_feats = feature(x,CONTENT_LAYER)
        return s_feats,c_feats
      
def totalloss(style_refs,content_refs,style_features,content_features,style_weight,content_weight):
    # compute total loss 
    style_loss = [l2loss(style_features[i],style_refs[i]) for i in range(len(style_features))] 
    #a small trick to balance the influnce of diffirent style layer
    mean_loss = sum(style_loss).data/len(style_features)
    
    style_loss = sum([(mean_loss/l.data)*l*STYLE_LAYER_WEIGHTS[i] 
                    for i,l in enumerate(style_loss)])/len(style_features) 
    
    content_loss = sum([l2loss(content_features[i],content_refs[i]) 
                    for i in range(len(content_refs))])/len(content_refs)
    total_loss = style_weight*style_loss+content_weight*content_loss
    return total_loss
  
def reference(style_img,content_img):
    # a function to compute style and content refenrences as used for loss
    style_refs = feature(style_img,STYLE_LAYER)
    style_refs = gram(style_refs)
    style_refs = [Variable(i.data) for i in style_refs]
    content_refs = feature(content_img,CONTENT_LAYER)
    content_refs = [Variable(i.data) for i in content_refs]
    return style_refs,content_refs
  
# load  pretrained squeezeNet and use the first sequential
model = models.squeezenet1_1(pretrained=True)
submodel = next(model.children())
STYLE_LAYER =[1,2,3,4,6,7,9]
STYLE_LAYER_WEIGHTS = [21,21,1,1,1,7,7]
CONTENT_LAYER = [1,2,3]
gram = GramMatrix()
feature = FeatureExtracter(submodel)
l2loss = nn.MSELoss(size_average=False)
stylize = Stylize()
toImage = transforms.ToPILImage()

def run_style_transfer_with_your_image(bot, update, content_path, style_path, resize = 256, learning_rate = 1e-1,
                                      style_weight = 1, content_weight = 1e-2, num_iters_1 = 300, num_iters_2 = 520,
                                      report_intvl = 20):
    style_img = imload(style_path, resize = 224)
    content_img = imload(content_path, resize = resize)
    # init a trainable img
    train_img = Variable(torch.randn(content_img.size()),requires_grad = True)
    # optimizer
    optimizer = optim.Adam([train_img], lr = learning_rate)

    # tracers
    loss_history = [] 
    min_loss = float("inf")
    best_img = 0

    # forward
    style_refs,content_refs = reference(style_img,content_img)

    for i in range(num_iters_1):
        optimizer.zero_grad()
        train_img.data.clamp_(-1,1)  # useful at first several step
        style_features,content_features = stylize(train_img)
        loss = totalloss(style_refs,content_refs,style_features,content_features,style_weight,content_weight)
        loss.backward()
        loss_history.append(loss.data)
        # save best result before update train_img

        if min_loss > loss_history[-1]:
                min_Loss = loss_history[-1]
                best_img = train_img

        optimizer.step()

        # report loss and image  
        if i % report_intvl == 0:
            print("step: %d loss: %f" %(i,loss_history[-1]))
            global msg
            if msg is not None:
                bot.delete_message(chat_id=msg.chat_id,
                            message_id=msg.message_id)
            # Пусть бот даст человеку возможность наслаждаться процессом )
            msg = imshow_bot(bot, update, train_img, '-------------{}/500-------------'.format(i))
            
    optimizer = optim.Adam([train_img], lr = learning_rate/10)
    
    for i in range(300, num_iters_2):
        optimizer.zero_grad()
        train_img.data.clamp_(-1,1)  # useful at first several step
        style_features,content_features = stylize(train_img)
        loss = totalloss(style_refs,content_refs,style_features,content_features,style_weight,content_weight)
        loss.backward()
        loss_history.append(loss.data)
        # save best result before update train_img
        if min_loss > loss_history[-1]:
            min_Loss = loss_history[-1]
            best_img = train_img
        optimizer.step()
        # report loss and image  
        if i % report_intvl == 0:
            print("step: %d loss: %f" %(i,loss_history[-1]))
            if msg is not None:
                bot.delete_message(chat_id=msg.chat_id,
                            message_id=msg.message_id)
            # Пусть бот даст человеку возможность наслаждаться процессом )
            msg = imshow_bot(bot, update, train_img, '-------------{}/500-------------'.format(i))

    return best_img
