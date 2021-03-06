import os
from flask import Flask, flash, render_template, redirect, request, url_for
from werkzeug.utils import secure_filename
import pickle
import torch.nn as nn
import torch
import io
import torchvision.transforms as transforms
from PIL import Image

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)),'images/')
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif'}

#loading the machine learning model
model = torch.load(os.path.join(os.path.dirname(os.path.abspath(__file__)),'model_1208.pwf'))

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = "supertopsecretprivatekeyoobooboo"


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        # show the upload form
        return render_template('upload.html')

@app.route("/upload", methods = ['GET','POST'])

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

def use_CNN(img_path):
    image = image_loader(img_path)
    output = model(image) #use NN
    _, preds_tensor = torch.max(output,1)
    preds = np.squeeze(preds_tensor.numpy()) #only CPU fix for GPU later
    name = classes[preds.flat[0]] #labels contains the classes
    return(name)


def upload():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            pred = use_CNN(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return pred






    return render_template("complete.html")

if __name__ == "__main__":
    app.run(port = 4555, debug = True)
