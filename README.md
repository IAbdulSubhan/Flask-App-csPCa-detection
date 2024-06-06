# MRI Image Classification and Segmentation

This is a Flask web application for classifying and segmenting MRI images. It uses pre-trained models for both binary classification and segmentation tasks. The application allows users to upload MRI images and receive predictions about whether the images are cancerous or non-cancerous. Additionally, it provides segmentation results for the uploaded images.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Features](#features)
- [Contributing](#contributing)
- [License](#license)

## Installation

To set up and run this application locally, follow these steps:

1. **Clone the repository:**

   ```bash
   git clone https://github.com/your-username/your-repo.git
   cd your-repo

Install the required dependencies:

bash
Copy code
pip install -r requirements.txt
Set up the database:

bash
Copy code
flask db init
flask db migrate -m "Initial migration."
flask db upgrade
Add your pre-trained models:

Place your pre-trained models (model_18.h5 and model_01.h5) in the root directory of the project.

Run the application:

bash
Copy code
flask run
The application will be available at http://127.0.0.1:5000.

Usage
Once the application is running, you can access it through your web browser. The application has the following main features:

Upload MRI: Allows users to upload MRI images for classification.
Segment MRI: Provides segmentation results for the uploaded MRI images.
Routes
/uploadmri: Upload MRI images for classification.
/segment: Upload MRI images for segmentation.
static/: Contains static files like images and CSS styles.
templates/: Contains HTML templates for different pages.
app.py: The main Flask application file.
model_18.h5 and model_01.h5: Pre-trained models for classification and segmentation respectively.
requirements.txt: A list of dependencies required for the project.
README.md: This file.
Features
User Authentication: Users can register, log in, and log out.
Image Classification: Upload MRI images to classify them as cancerous or non-cancerous.
Image Segmentation: Upload MRI images to receive segmentation results.
Contributing
Contributions are welcome! Please fork the repository and create a pull request with your changes. Ensure that your code follows the project's coding standards and includes appropriate tests.git 