# APS360_GeoGuessr_NN

## Directory Structure

├── baseline
│   ├── KNN_model.ipynb
├── data_processing: data acquisition and processing code
│   ├── Creating_Train_Val_Test_Split.ipynb
│   ├── api_request_signature.py
│   ├── geocell_imagery_sampling.py
│   ├── imagery_download.py
├── primary_model
│   ├── TRAINING_TEMPLATE.ipynb
│   │   ├── gg
│   ├── images
│   ├── js
│   ├── index.html
├── dist (or build
├── node_modules
├── package.json
├── package-lock.json 
└── .gitignore

## How to run
- Download the dataset or create a shortcut to Drive at [32k_train_val_test](https://drive.google.com/drive/folders/102y3wVHae4freSFV7hmyzSAnypnjZGrD?usp=share_link) 
- Open the `primary model/TEMPLATE.ipynb` file in Google Colab. Click `Run All`. Enjoy.

## Model 
This ML project is based off the [ResNet 50 architecture](https://pytorch.org/vision/main/models/generated/torchvision.models.resnet50.html) available on PyTorch.

![This is an image](https://miro.medium.com/max/1400/0*9LqUp7XyEx1QNc6A.webp)
