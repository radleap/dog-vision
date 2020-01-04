import os
from flask import Flask, flash, render_template, redirect, request, url_for, jsonify
from werkzeug.utils import secure_filename
import pickle
import torch.nn as nn
import torch
import io
import torchvision.transforms as transforms
from PIL import Image
from torch.autograd import Variable
import numpy as np
import cv2 #added for facial recognition

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)),'images/')
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif'}

#loading the machine learning model
model = torch.load(os.path.join(os.path.dirname(os.path.abspath(__file__)),'model_Squeezenet_CNN_Transfer_20191214165952.pwf'))
model.eval()

with open('static/classes.txt', 'rb') as file:
    classes = pickle.load(file)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = "supertopsecretprivatekeyoobooboo"


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Loading the initial "homepage" with upload.html template
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        # show the upload form
        return render_template('upload.html')

#image loader transforms the image to a format for the neural network to use (as had been trained), loads image, apply, returns new image
def image_loader(image_name):
    transformer = transforms.Compose([transforms.Resize(256),
                                transforms.CenterCrop(224),
                                transforms.RandomHorizontalFlip(p=0.5),
                                transforms.ToTensor(),
                                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])

    image = Image.open(image_name)
    image = transformer(image).float()
    image = Variable(image, requires_grad=True)
    image = image.unsqueeze(0)
    return image

def face_detector(file):
    face_cascade = cv2.CascadeClassifier('static/haarcascades/haarcascade_frontalface_alt.xml') #face detection xml model
    img = Image.open(file)
    img = np.array(img)
    #img = cv2.cvtColor(np.array(img), cv2.COLOR_BGR2RGB)
    #img = cv2.resize(img,(224,224))
    #gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.cvtColor(np.array(img), cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray)
    return len(faces) > 0

# applies image loaders, and the neural network to the image, returning the class name
def use_CNN(img_path):
    image = image_loader(img_path)
    output = model(image) #use NN
    _, preds_tensor = torch.max(output,1)
    preds = np.squeeze(preds_tensor.numpy())
    name = classes[preds.flat[0]] #labels contains the classes
    return(name)

# If the user uploads an image, this get the "POST" and applies the use_CNN (neural network to it)
# This code uses the static files (static due to Heroku documentation) and the predicted class to return the predicted class image
@app.route('/upload', methods=['POST'])
def upload():
    if request.method == 'POST':
        file = request.files['file'] #takes the name "file" from upload.html post form
        pred = use_CNN(file)
        dog_filename =  '\\static\\dog_class_images\\' + pred.capitalize().replace(" ", "_") +'.jpg'

        #face detection portion cv2 issue with same read code
        # filestr = request.files['file'].read()
        is_human = face_detector(file) #checking for humans

        #is_human = False
        #return jsonify({'prediction': pred})
        #return render_template('prediction.html', prediction_text = 'The dog class is {}'.format(pred), prediction_image = dog_filename)
        if is_human:
            return render_template('prediction.html', prediction_text = 'A human was detected! But, this particular human looks more like a {}!'.format(pred), prediction_image = dog_filename)
        else:
            #return render_template('prediction.html', prediction_text = 'file is {}'.format(type(file)), prediction_image = dog_filename)
            return render_template('prediction.html', prediction_text = 'The predicted dog class is {}'.format(pred), prediction_image = dog_filename)

# if __name__ == "__main__": #needed to run locally
#    app.run(port = 4555, debug = True) # hide this to run on Heroku?
if __name__ == "__main__":
    app.run()
