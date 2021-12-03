# %%
# Imports
from __future__ import print_function
from __future__ import division
import torch
import torch.nn as nn
import numpy as np
import torchvision
from torchvision import models
from torch.utils.data import Dataset, DataLoader
import matplotlib.pyplot as plt
import torch.nn.functional as F
import time
import os
import copy
import cv2
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split
import xml.etree.ElementTree as ET
import Modules.BB as bnbx
import Modules.dataaugmentation as dataaug
print("PyTorch Version: ",torch.__version__)
print("Torchvision Version: ",torchvision.__version__)

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
print('memory_allocated', torch.cuda.memory_allocated() / 1000000000, 'GB')
print('max_memory_allocated', torch.cuda.max_memory_allocated() / 1000000000, 'GB')
print('memory_reserved', torch.cuda.memory_reserved() / 1000000000, 'GB')
print('max_memory_reserved', torch.cuda.max_memory_reserved() / 1000000000, 'GB')
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Top level data directory. Here we assume the format of the directory conforms to the ImageFolder structure
#data_dir = "../data/alfalaval"
data_dir = '../data/AlfaLavalFinal'

# Models to choose from [resnet, alexnet, vgg, squeezenet, densenet, inception]
model_name = "resnet"

# Number of classes in the dataset
num_classes = 1

# Batch size for training (change depending on how much memory you have)
batch_size = 8

# Number of epochs to train for
num_epochs = 15

# Flag for feature extracting. When False, we finetune the whole model,
#   when True we only update the reshaped layer params
feature_extract = True


# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

images_path = Path(f'{data_dir}/images')
anno_path = Path(f'{data_dir}/annotations')

# Create methods for loading in images and annotations
def filelist(root, file_type):
    """Returns a fully-qualified list of filenames under root directory"""
    return [os.path.join(directory_path, f) for directory_path, directory_name, 
            files in os.walk(root) for f in files if f.endswith(file_type)]

def generate_train_df (anno_path):
    annotations = filelist(anno_path, '.xml')
    anno_list = []
    for anno_path in annotations:
        root = ET.parse(anno_path).getroot()
        objects = []
        for child in root:
            if child.tag == 'object':
                objects.append(child)

        anno = {}
        anno['filename'] = Path(str(images_path) + '/'+ root.find("./filename").text)
        anno['width'] = root.find("./size/width").text
        anno['height'] = root.find("./size/height").text
        
        bndboxes = []
        i = 0
        for objct in objects:
            i += 1   
            bndbox = {}
            bndbox['class'] = 0#objct.find("./name").text
            bndbox['xmin'] = int(objct.find("./bndbox/xmin").text)
            bndbox['ymin'] = int(objct.find("./bndbox/ymin").text)
            bndbox['xmax'] = int(objct.find("./bndbox/xmax").text)
            bndbox['ymax'] = int(objct.find("./bndbox/ymax").text)
            bndboxes.append(bndbox)
            
        anno['bndbox'] = bndboxes            
        anno_list.append(anno)
    return pd.DataFrame(anno_list)

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Fake dataframe
dataframe_temp = generate_train_df('../data/alfalaval/test')
print(dataframe_temp.values)
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# Generate train dataframes
df_train = generate_train_df(anno_path)

# Print dataframe shape
print(df_train.shape)
df_train.head()

#%%
print(data_dir)
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Test
train_path_resized = Path(f'{data_dir}/images')
for index, row in df_train.iterrows():
    #print(row)
    print(str(row[0]).rsplit('\\', 1)[1])
    bbs = bnbx.create_bbs_array(row.values)
    
    #bbs = create_bbs_array(row.values)
    print(bbs)
    im = bnbx.read_image(row[0])
    #im = read_image(row[0])
    images = bnbx.create_masks(bbs, im)
    #images = create_masks(bbs, im)
    for bb in bbs:
        start_point = (bb[0], bb[1])
        end_point = (bb[2], bb[3])
        cv2.rectangle(im, (start_point), end_point, (0, 0, 255), 2)

    new_path,new_bbs = bnbx.resize_image_bb(row['filename'], train_path_resized, bnbx.create_bbs_array(row.values),300)
    #new_path,new_bbs = resize_image_bb(row['filename'], train_path_resized, create_bbs_array(row.values),300)
    im2 = bnbx.read_image(new_path)
    #im2 = read_image(new_path)
    im_mask = bnbx.create_masks(new_bbs, im2)
    #im_mask = create_masks(new_bbs, im2)
    print("resized bounding box")
    for bb in new_bbs:
        print(bb)
        start_point = (int(bb[0]), int(bb[1]))
        end_point = (int(bb[2]), int(bb[3]))
        cv2.rectangle(im2, (start_point), end_point, (0, 0, 255), 2)

    # Plot
    fig = plt.figure(figsize=(10, 7))
    #fig.suptitle(row[0])
    rows = 1#2
    columns = 2
    fig.add_subplot(rows, columns, 1)
    #plt.title(f'Original')
    #plt.imshow(im)
    #fig.add_subplot(rows, columns, 2)
    #plt.title(f'Resized')
    #plt.imshow(im2)
    #fig.add_subplot(rows, columns, 3)
    #plt.title("Original Mask")
    #plt.imshow(images[-1], cmap='gray')
    #fig.add_subplot(rows, columns, 4)
    #plt.title("Resized Mask")
    #plt.imshow(im_mask[-1], cmap='gray')
    name = str(row[0]).rsplit('\\', 1)[1].replace('.jpg', '_mask.jpg')
    outputpath = f'{data_dir}/masks/{name}'
    print(outputpath)
    plt.imshow(im_mask[-1], cmap='gray')
    
    # cv2.imwrite(outputpath, grayImage)
    from PIL import Image
    im_mask[-1] = (im_mask[-1]*255).astype(np.uint8)
    fig.add_subplot(rows, columns, 2)
    newmask = Image.fromarray(im_mask[-1], 'P')
    newmask.convert('RGB').save(outputpath)
    plt.imshow(newmask)
    
    
    
    #print(row.values[4])
    #print('')

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
print(df_train.values[58])
new_paths = []
new_bbs = []
train_path_resized = Path(f'{data_dir}/images_resized')
for index, row in df_train.iterrows():
    new_path,new_bb = bnbx.resize_image_bb(row['filename'], train_path_resized, bnbx.create_bbs_array(row.values),300)
    new_paths.append(new_path)
    new_bbs.append(new_bb)
df_train['new_path'] = new_paths
df_train['new_bb'] = new_bbs

print(df_train.values[58])

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
num = 131
print(df_train.values[num])
# Read image and create bounding box

im = cv2.imread(str(df_train.values[num][0]))
bbs = bnbx.create_bbs_array(df_train.values[num])
print(im.shape)

Y = bnbx.create_masks(bbs, im)[-1]

# Show image and image of new mask
fig = plt.figure(figsize=(10, 7))
fig.suptitle(str(df_train.values[num][0]))
rows = 1
columns = 2
fig.add_subplot(rows, columns, 1)
plt.title("Original")
plt.imshow(im)
fig.add_subplot(rows, columns, 2)
plt.title("Mask")
plt.imshow(Y, cmap='gray')


# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

im = cv2.imread(str(df_train.values[num][-2]))
im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)

fig = plt.figure(figsize=(10, 7))
rows = 1
columns = 2
fig.add_subplot(rows, columns, 1)
#original
plt.title("Original")
dataaug.show_corner_bb(im, df_train.values[num][-1])
fig.add_subplot(rows, columns, 2)
# after transformation
plt.title("After Transform")
im, bbs = dataaug.transformsXY(str(df_train.values[num][-2]),df_train.values[num][-1],True )
print(bbs)
dataaug.show_corner_bb(im, bbs)


# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Define datset methods
def normalize(im):
    """Normalizes images with Imagenet stats."""
    imagenet_stats = np.array([[0.485, 0.456, 0.406], [0.229, 0.224, 0.225]])
    return (im - imagenet_stats[0])/imagenet_stats[1]

class AlfaLavalDataset(Dataset):
    def __init__(self, paths, bb, y, transforms=False):
        self.transforms = transforms
        self.paths = paths.values
        self.bb = bb.values
        self.y = y.values
    def __len__(self):
        return len(self.paths)
    
    def __getitem__(self, idx):
        path = self.paths[idx]
        y_class = self.y[idx]
        x, y_bbs = dataaug.transformsXY(path, self.bb[idx], self.transforms)
        x = normalize(x)
        x = np.rollaxis(x, 2)
        return x, y_class, y_bbs

# %%
# TEST
print(dataframe_temp.values[0])
print(dataframe_temp.values[1])

new_paths = []
new_bbs = []
train_path_resized = Path(f'{data_dir}/test/images_resized')
print("iteration")
for index, row in dataframe_temp.iterrows():
    print(row)
    new_path,new_bb = bnbx.resize_image_bb(row['filename'], train_path_resized, bnbx.create_bbs_array(row.values),300)
    new_paths.append(new_path)
    new_bbs.append(new_bb)
dataframe_temp['new_path'] = new_paths
dataframe_temp['new_bb'] = new_bbs
dataframe_temp.head()

#%%
# Test
dataframe_temp = dataframe_temp.reset_index()
X = dataframe_temp[['new_path', 'new_bb']]
classlist = []
for boxes in dataframe_temp['bndbox']:
    classlist.append(boxes[0]['class'])
Y = pd.DataFrame(columns=['class'])
Y['class'] = classlist

X_train_temp, X_val_temp, y_train_temp, y_val_temp = train_test_split(X, Y, test_size=0.5, random_state=42)
#%%
print("X_train_temp {0}".format(X_train_temp))
#%%
print("X_val_temp {0}".format(X_val_temp))
#%%
print("y_train_temp {0}".format(y_train_temp))
#%%
print("y_val_temp {0}".format(y_val_temp))
#%%
train_ds_temp = AlfaLavalDataset(X_train_temp['new_path'],X_train_temp['new_bb'] ,y_train_temp, transforms=True)
for i in train_ds_temp:
    print(i)
#%%
valid_ds_temp = AlfaLavalDataset(X_val_temp['new_path'],X_val_temp['new_bb'],y_val_temp)
batch_size = 8
train_dl_temp = DataLoader(train_ds_temp, batch_size=batch_size, shuffle=True)
valid_dl_temp = DataLoader(valid_ds_temp, batch_size=batch_size)


# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Train-valid split
df_train = df_train.reset_index()
X = df_train[['new_path', 'new_bb']]
classlist = []
for boxes in df_train['bndbox']:
    classlist.append(boxes[0]['class'])
Y = pd.DataFrame(columns=['class'])
Y['class'] = classlist

X_train, X_val, y_train, y_val = train_test_split(X, Y, test_size=0.2, random_state=42)

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#Setup dataset
train_ds = AlfaLavalDataset(X_train['new_path'],X_train['new_bb'] ,y_train, transforms=True)
valid_ds = AlfaLavalDataset(X_val['new_path'],X_val['new_bb'],y_val)
batch_size = 8
train_dl = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
valid_dl = DataLoader(valid_ds, batch_size=batch_size)

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Define training methods
def update_optimizer(optimizer, lr):
    for i, param_group in enumerate(optimizer.param_groups):
        param_group["lr"] = lr

def train_epocs(model, optimizer, train_dl, valid_dl, epochs=10,C=1000):
    idx = 0
    for i in range(epochs):
        model.train()
        total = 0
        sum_loss = 0
        for x, y_class, y_bb in train_dl:
            batch = y_class.shape[0]
            x = x.cuda().float()
            y_class = y_class.cuda()
            y_bb = y_bb.cuda().float()
            out_class, out_bb = model(x)
            loss_class = F.cross_entropy(out_class, y_class, reduction="sum")
            loss_bb = F.l1_loss(out_bb, y_bb, reduction="none").sum(1)
            loss_bb = loss_bb.sum()
            loss = loss_class + loss_bb/C
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            idx += 1
            total += batch
            sum_loss += loss.item()
        train_loss = sum_loss/total
        val_loss, val_acc = val_metrics(model, valid_dl, C)
        print("epoch %.0f of %.0f, train_loss %.3f, val_loss %.3f, val_acc %.3f" % (i, epochs, train_loss, val_loss, val_acc))
    return sum_loss/total

def val_metrics(model, valid_dl, C=1000):
    model.eval()
    total = 0
    sum_loss = 0
    correct = 0 
    for x, y_class, y_bb in valid_dl:
        batch = y_class.shape[0]
        x = x.cuda().float()
        y_class = y_class.cuda()
        y_bb = y_bb.cuda().float()
        out_class, out_bb = model(x)
        loss_class = F.cross_entropy(out_class, y_class, reduction="sum")
        loss_bb = F.l1_loss(out_bb, y_bb, reduction="none").sum(1)
        loss_bb = loss_bb.sum()
        loss = loss_class + loss_bb/C
        _, pred = torch.max(out_class, 1)
        correct += pred.eq(y_class).sum().item()
        sum_loss += loss.item()
        total += batch
    return sum_loss/total, correct/total


# Model definition - Resnet
class BB_model(nn.Module):
    def __init__(self):
        super(BB_model, self).__init__()
        resnet = models.resnet34(pretrained=True)
        layers = list(resnet.children())[:8]
        self.features1 = nn.Sequential(*layers[:6])
        self.features2 = nn.Sequential(*layers[6:])
        self.classifier = nn.Sequential(nn.BatchNorm1d(512), nn.Linear(512, 4))
        self.bb = nn.Sequential(nn.BatchNorm1d(512), nn.Linear(512, 4))
        
    def forward(self, x):
        x = self.features1(x)
        x = self.features2(x)
        x = F.relu(x)
        x = nn.AdaptiveAvgPool2d((1,1))(x)
        x = x.view(x.shape[0], -1)
        return self.classifier(x), self.bb(x)

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Setup model
model = BB_model().cuda()
parameters = filter(lambda p: p.requires_grad, model.parameters())
optimizer = torch.optim.Adam(parameters, lr=0.006)

train_epocs(model, optimizer, train_dl, valid_dl, epochs=15)

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
update_optimizer(optimizer, 0.001)
train_epocs(model, optimizer, train_dl, valid_dl, epochs=10)

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Making predictions
# choose random image from validation set
X_val

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
selected_image_num = 198
# resizing test image
im = read_image(f'{data_dir}/images_resized/Alfa_Laval_Sensor_{selected_image_num}.jpg')
im = cv2.resize(im, (int(1.49*300), 300))
cv2.imwrite(f'{data_dir}/test/Alfa_Laval_Sensor_Test_{selected_image_num}.jpg', cv2.cvtColor(im, cv2.COLOR_RGB2BGR))

# %
# test Dataset
test_ds = RoadDataset(pd.DataFrame([{'path':f'{data_dir}/test/Alfa_Laval_Sensor_Test_{selected_image_num}.jpg'}])['path'],pd.DataFrame([{'bb':np.array([0,0,0,0])}])['bb'],pd.DataFrame([{'y':[0]}])['y'])
x, y_class, y_bb = test_ds[0]

xx = torch.FloatTensor(x[None,])
xx.shape


# prediction
out_class, out_bb = model(xx.cuda())
out_class, out_bb

# predicted class
torch.max(out_class, 1)


# predicted bounding box
bb_hat = out_bb.detach().cpu().numpy()
bb_hat = bb_hat.astype(int)
show_corner_bb(im, bb_hat[0])




























# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Model for training
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
def train_model(model, dataloaders, criterion, optimizer, num_epochs=25, is_inception=False):
    since = time.time()

    val_acc_history = []

    best_model_wts = copy.deepcopy(model.state_dict())
    best_acc = 0.0

    for epoch in range(num_epochs):
        print('Epoch {}/{}'.format(epoch, num_epochs - 1))
        print('-' * 10)

        # Each epoch has a training and validation phase
        for phase in ['train', 'val']:
            if phase == 'train':
                model.train()  # Set model to training mode
            else:
                model.eval()   # Set model to evaluate mode

            running_loss = 0.0
            running_corrects = 0

            # Iterate over data.
            for inputs, labels in dataloaders[phase]:
                inputs = inputs.to(device)
                labels = labels.to(device)

                # zero the parameter gradients
                optimizer.zero_grad()

                # forward
                # track history if only in train
                with torch.set_grad_enabled(phase == 'train'):
                    # Get model outputs and calculate loss
                    # Special case for inception because in training it has an auxiliary output. In train
                    #   mode we calculate the loss by summing the final output and the auxiliary output
                    #   but in testing we only consider the final output.
                    if is_inception and phase == 'train':
                        # From https://discuss.pytorch.org/t/how-to-optimize-inception-model-with-auxiliary-classifiers/7958
                        outputs, aux_outputs = model(inputs)
                        loss1 = criterion(outputs, labels)
                        loss2 = criterion(aux_outputs, labels)
                        loss = loss1 + 0.4*loss2
                    else:
                        outputs = model(inputs)
                        loss = criterion(outputs, labels)

                    _, preds = torch.max(outputs, 1)

                    # backward + optimize only if in training phase
                    if phase == 'train':
                        loss.backward()
                        optimizer.step()

                # statistics
                running_loss += loss.item() * inputs.size(0)
                running_corrects += torch.sum(preds == labels.data)

            epoch_loss = running_loss / len(dataloaders[phase].dataset)
            epoch_acc = running_corrects.double() / len(dataloaders[phase].dataset)

            print('{} Loss: {:.4f} Acc: {:.4f}'.format(phase, epoch_loss, epoch_acc))

            # deep copy the model
            if phase == 'val' and epoch_acc > best_acc:
                best_acc = epoch_acc
                best_model_wts = copy.deepcopy(model.state_dict())
            if phase == 'val':
                val_acc_history.append(epoch_acc)

        print()

    time_elapsed = time.time() - since
    print('Training complete in {:.0f}m {:.0f}s'.format(time_elapsed // 60, time_elapsed % 60))
    print('Best val Acc: {:4f}'.format(best_acc))

    # load best model weights
    model.load_state_dict(best_model_wts)
    return model, val_acc_history



# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

def set_parameter_requires_grad(model, feature_extracting):
    if feature_extracting:
        for param in model.parameters():
            param.requires_grad = False

def initialize_model(model_name, num_classes, feature_extract, use_pretrained=True):
    # Initialize these variables which will be set in this if statement. Each of these
    #   variables is model specific.
    model_ft = None
    input_size = 0

    if model_name == "resnet":
        """ Resnet18
        """
        model_ft = models.resnet18(pretrained=use_pretrained)
        set_parameter_requires_grad(model_ft, feature_extract)
        num_ftrs = model_ft.fc.in_features
        model_ft.fc = nn.Linear(num_ftrs, num_classes)
        input_size = 224

    elif model_name == "alexnet":
        """ Alexnet
        """
        model_ft = models.alexnet(pretrained=use_pretrained)
        set_parameter_requires_grad(model_ft, feature_extract)
        num_ftrs = model_ft.classifier[6].in_features
        model_ft.classifier[6] = nn.Linear(num_ftrs,num_classes)
        input_size = 224

    elif model_name == "vgg":
        """ VGG11_bn
        """
        model_ft = models.vgg11_bn(pretrained=use_pretrained)
        set_parameter_requires_grad(model_ft, feature_extract)
        num_ftrs = model_ft.classifier[6].in_features
        model_ft.classifier[6] = nn.Linear(num_ftrs,num_classes)
        input_size = 224

    elif model_name == "squeezenet":
        """ Squeezenet
        """
        model_ft = models.squeezenet1_0(pretrained=use_pretrained)
        set_parameter_requires_grad(model_ft, feature_extract)
        model_ft.classifier[1] = nn.Conv2d(512, num_classes, kernel_size=(1,1), stride=(1,1))
        model_ft.num_classes = num_classes
        input_size = 224

    elif model_name == "densenet":
        """ Densenet
        """
        model_ft = models.densenet121(pretrained=use_pretrained)
        set_parameter_requires_grad(model_ft, feature_extract)
        num_ftrs = model_ft.classifier.in_features
        model_ft.classifier = nn.Linear(num_ftrs, num_classes)
        input_size = 224

    elif model_name == "inception":
        """ Inception v3
        Be careful, expects (299,299) sized images and has auxiliary output
        """
        model_ft = models.inception_v3(pretrained=use_pretrained)
        set_parameter_requires_grad(model_ft, feature_extract)
        # Handle the auxilary net
        num_ftrs = model_ft.AuxLogits.fc.in_features
        model_ft.AuxLogits.fc = nn.Linear(num_ftrs, num_classes)
        # Handle the primary net
        num_ftrs = model_ft.fc.in_features
        model_ft.fc = nn.Linear(num_ftrs,num_classes)
        input_size = 299

    else:
        print("Invalid model name, exiting...")
        exit()

    return model_ft, input_size

# Initialize the model for this run
model_ft, input_size = initialize_model(model_name, num_classes, feature_extract, use_pretrained=True)

# Print the model we just instantiated
print(model_ft)























