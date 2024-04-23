from flask import Flask, request, render_template, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
import bcrypt
import keras
import numpy as np
from datetime import timedelta
from keras.models import load_model
from keras.preprocessing import image
import os
import tensorflow as tf
import gevent
from werkzeug.utils import secure_filename
from gevent.pywsgi import WSGIServer

# Set environment variable to disable oneDNN
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

# Ensure numpy is imported and necessary libraries are in place
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'your_secret_key'  # Needed for flash messages
db = SQLAlchemy(app)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)  # Example: Expire after 30 minutes

dir_path = os.path.dirname(os.path.realpath(__file__))
Images = "uploads"
STATIC_FOLDER = "static"


cnn_model = tf.keras.models.load_model(STATIC_FOLDER + "/catdog.h5")
IMAGE_SIZE = 150

# Load your model and create a dictionary for class mapping

# Preprocess an image
def preprocess_image(image):
    image = tf.image.decode_jpeg(image, channels=3)
    image = tf.image.resize(image, [IMAGE_SIZE, IMAGE_SIZE])
    image /= 255.0  # normalize to [0,1] range

    return image


# Read the image from path and preprocess
def load_and_preprocess_image(path):
    image = tf.io.read_file(path)

    return preprocess_image(image)

# Predict & classify image
def classify(model, image_path):

    preprocessed_imgage = load_and_preprocess_image(image_path)
    preprocessed_imgage = tf.reshape(
        preprocessed_imgage, (1, IMAGE_SIZE, IMAGE_SIZE, 3)
    )

    prob = cnn_model.predict(preprocessed_imgage)
    label = "Cat" if prob[0][0] >= 0.5 else "Dog"
    classified_prob = prob[0][0] if prob[0][0] >= 0.5 else 1 - prob[0][0]

    # return label, classified_prob

    return label



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


@app.route('/uploadmri', methods=['GET', 'POST'])
def upload_mri():
    if request.method == 'POST':
        if 'my_image' not in request.files:
            flash("No file part in the request.", "error")
            return redirect(request.url)

        file = request.files['my_image']

        if file.filename == '':
            flash("No selected file.", "error")
            return redirect(request.url)

        img_path = os.path.join('Images', file.filename)
        file.save(img_path)

        label = classify(cnn_model, img_path)

        # For convenience, use 'filename' to avoid the unbound error
        filename = file.filename if file else "No file provided"

        return render_template("uploadmri.html", image_file_name=filename, label=label)

    return render_template("uploadmri.html")

    # return None
    # if not session.get('logged_in'):
    #     flash("You need to be logged in to upload an MRI image.", "error")
    #     return redirect(url_for('login'))
    
    # if request.method == 'POST':
    #     # Get the file from the form
    #     if 'my_image' not in request.files:
    #         flash("No file part in the request.", "error")
    #         return redirect(request.url)

    #     file = request.files['my_image']

    #     # Check if a file is uploaded
    #     if file.filename == '':
    #         flash("No selected file.", "error")
    #         return redirect(request.url)

    #     # Validate the file type (assuming MRI files are images)
    #     if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
    #         flash("Only PNG, JPG, or JPEG files are allowed.", "error")
    #         return redirect(request.url)

    #     # Save the file to a temporary location
    #     img_path = os.path.join('images', file.filename)  # You might need to create 'temp' directory
    #     file.save(img_path)

    #     # Get the prediction
    #     predicted_label = predict_label(img_path)

    #     # Return the predicted label with a flash message
    #     flash(f"Prediction: {predicted_label}", "success")
    #     os.remove(img_path)  # Remove the temporary file after processing

    #     return redirect(request.url)  # Reload the page to avoid resubmission

    return render_template('uploadmri.html')  # For GET request, render the form


# Dashboard route
@app.route('/dashboard')  
def dashboard():  
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('dashboard.html')

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
            return redirect(url_for('dashboard'))
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
