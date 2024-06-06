from flask import Flask, request, render_template, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
import bcrypt
import keras
import numpy as np
from datetime import timedelta
from keras.models import load_model
from tensorflow.keras.layers import BatchNormalization
from keras.preprocessing import image
from PIL import Image  # Import PIL
import os

# Set environment variable to disable oneDNN
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

# Ensure numpy is imported and necessary libraries are in place
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'your_secret_key'  # Needed for flash messages
db = SQLAlchemy(app)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)  # Example: Expire after 30 minutes

# Load your model and create a dictionary for class mapping
dic = {0: "Cancerous", 1: "Non Cancerous"}
model = load_model("model.h5")
unet = load_model("unet.h5")

# This should be an integer, not a list
batch_norm_layer = BatchNormalization(axis=3)

import logging

logging.basicConfig(level=logging.INFO)

def predict_label(img_path):
    img = image.load_img(img_path, target_size=(224, 224))
    img_array = image.img_to_array(img) / 255.0
    img_array = img_array.reshape((1, 224, 224, 3))
    
    prediction = model.predict(img_array)
    logging.info(f"Prediction probabilities: {prediction}")

    # If using a custom threshold, change it here
    threshold = 0.5
    class_index = 1 if prediction[0][0] > threshold else 0
    
    class_label = dic[class_index]
    
    return class_label

def segment(img_path):
    img = image.load_img(img_path, target_size=(224, 224))
    img_array = image.img_to_array(img) / 255.0
    img_array = img_array.reshape((1, 224, 224, 3))
    
    prediction = unet.predict(img_array)
    logging.info(f"Prediction probabilities: {prediction}")

    # If using a custom threshold, change it here
    threshold = 0.5
    class_index = 1 if prediction[0][0] > threshold else 0
    
    class_label = dic[class_index]
    
    return class_label


# Directory for storing images
IMAGES_DIR = './static/images/'

def is_image_rgb(img_path):
    """ Check if an image is in RGB format """
    img = Image.open(img_path)
    return img.mode == 'RGB'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'png'

@app.route('/uploadmri', methods=['GET', 'POST'])
def uploadmri():
    if not session.get('logged_in'):
        flash("You need to be logged in to upload an MRI image.", "error")
        return redirect(url_for('login'))

    if request.method == 'POST':
        file = request.files.get('my_image')  # Get the uploaded file

        # Check if the file is valid
        if not file or file.filename == '':
            flash("No file selected or invalid file.", "error")
            return redirect(request.url)

        if not allowed_file(file.filename):
            flash("Invalid file format. Only PNG images are accepted.", "error")
            return redirect(request.url)

        # Save the file and get the path
        img_path = os.path.join(IMAGES_DIR, file.filename)
        file.save(img_path)

        # Check if the image is in RGB format and PNG
        if is_image_rgb(img_path) and allowed_file(file.filename):
            os.remove(img_path)  # Remove the image as it is not acceptable
            flash("Invalid file format. RGB PNG images are not accepted.", "error")
            return redirect(request.url)

        # Check if the image is in RGB format
        if is_image_rgb(img_path):
            os.remove(img_path)  # Remove the image as it is not acceptable
            flash("Uploaded image is in RGB format. Please upload the correct file.", "error")
            return redirect(request.url)

        # Extracting the file name
        file_name = os.path.basename(img_path)

        # Prediction logic and flash messages
        predicted_label = predict_label(img_path)  # Predict based on the uploaded file
        flash(f"Prediction: {predicted_label}", "success")

        # Render the template with prediction and image
        return render_template('uploadmri.html', prediction=predicted_label, file_name=file_name)
    
    # For GET request, render the form
    return render_template('uploadmri.html')


@app.route('/segment', methods=['GET', 'POST'])
def segment():
    if not session.get('logged_in'):
        flash("You need to be logged in to upload an MRI image.", "error")
        return redirect(url_for('login'))

    if request.method == 'POST':
        file = request.files.get('seg_image')  # Get the uploaded file

        # Check if the file is valid
        if not file or file.filename == '':
            flash("No file selected or invalid file.", "error")
            return redirect(request.url)

        if not allowed_file(file.filename):
            flash("Invalid file format. Only PNG images are accepted.", "error")
            return redirect(request.url)

        # Save the file and get the path
        img_path = os.path.join(IMAGES_DIR, file.filename)
        file.save(img_path)

        # Check if the image is in RGB format
        if is_image_rgb(img_path):
            flash("Uploaded image is in RGB format. Please upload the correct file.", "error")
            return redirect(request.url)

        # Extracting the file name
        file_name = os.path.basename(img_path)

        # Prediction logic and flash messages
        predicted_label = predict_label(img_path)  # Predict based on the uploaded file
        flash(f"Prediction: {predicted_label}", "success")

        # Render the template with prediction and image
        return render_template('segment.html', prediction=predicted_label, file_name=file_name)
    
    # For GET request, render the form
    return render_template('segment.html')

# Database model for users
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100))

    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

with app.app_context():
    db.create_all()

# Index route
@app.route('/')
def index():
    return render_template('index.html')

# Home route
@app.route('/home')
def home():
    return render_template('home.html')


# How It Works route
@app.route('/faq')
def faq():
    return render_template('faq.html')  # Corrected to render a template

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        # Check if user already exists
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists. Please use a different email.', 'error')  # Flash error message
            return redirect(url_for('register'))

        new_user = User(name, email, password)
        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully.', 'success')  # Flash success message
        return redirect(url_for('login'))
    else:
        return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['logged_in'] = True
            return redirect(url_for('home'))
        # return redirect(url_for('uploadmri'))

        else:
            flash('Invalid username or password.')
            return redirect(url_for('login'))

    return render_template('login.html')  # Ensure all methods render a page

# Logout route
@app.route('/logout')
def logout():
    session.clear()  # Clear the entire session
    return redirect(url_for('index'))

# How It Works route
@app.route('/Howitworks')
def Howitworks():
    return render_template('Howitworks.html')  # Corrected to render a template

if __name__ == '__main__':
    app.run(debug=True)
