import cv2
import matplotlib.patches as patches
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
from skimage.metrics import structural_similarity
import argparse
import imutils
import datetime
import time
import tensorflow as tf
import math
import sys
import numpy as np
from flask import Flask, request, redirect, url_for
import os
from flask import jsonify

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


def focusScore(image):
    # crop the image to the middle 35%
    height, width, _ = image.shape
    start_row, start_col = int(height * 0.3125), int(width * 0.3125)
    end_row, end_col = int(height * 0.6875), int(width * 0.6875)
    image = image[start_row:end_row, start_col:end_col]

    kernel = np.array([[0, -1, 0],
                       [-1, 5, -1],
                       [0, -1, 0]])
    image_sharp = cv2.filter2D(src=image, ddepth=-1, kernel=kernel)
    #cv2.imwrite("sharp.jpg", image_sharp)
    #cv2.imwrite("original.jpg", image)

    # Blur the image using a Gaussian Blur
    blurred = cv2.GaussianBlur(image, (551, 551), 0)
    # output the blurred image
    #cv2.imwrite("blurred.jpg", blurred)
    # Find the structural similarity between the original image and the blurred image
    score = structural_similarity(image_sharp, blurred, multichannel=True)
    # Return the score while keeping two decimal places
    return (round((1-score) * 100, 2))

    # Function that finds the exposure of the image using the average brightness of the image and returns the amount of exposure in the image.
    # The function will return a rating out of 100. the more underexposed the image is, the lower the score will be. the more overexposed the image is, the lower the score will be. the more correctly exposed the image is, the higher the score will be.
    # The Minimum score will be 0 and the maximum score will be 100.
    # Create and utilize histogram analysis to determine the exposure of the image.


def findExposure(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
    hist_cumsum = np.cumsum(hist)
    total_pixels = gray.shape[0] * gray.shape[1]
    index_5 = next(x[0] for x in enumerate(hist_cumsum)
                   if x[1] >= total_pixels * 0.05)
    index_95 = next(x[0] for x in enumerate(hist_cumsum)
                    if x[1] >= total_pixels * 0.95)
    exposure_score = (index_95 + index_5) / 2
    exposure_score = min(exposure_score, 255)
    score = 100 - (abs(exposure_score - 128) * 100 / 128)
    return int(score)


@app.route("/", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        file = request.files["file"]
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        # Store the image in a variable
        image = cv2.imread(file_path)
        # Check if the image was read correctly
        if image is None:
            return "Error: Failed to read the image. Please try again with a different image."
        # Find the focus of the image
        focus_score = focusScore(image)
        # Find the subject of the image
        #subject_score = findSubject(image)
        # Find the exposure of the image
        exposure_score = findExposure(image)

        # Print the focus score
        print("Focus Score: " + str(focus_score))
        # Print the subject score
        # print("Subject Score: " + str(subject_score))
        # Print the exposure score
        print("Exposure Score: " + str(exposure_score))
        return '''
            <p>Exposure Score: {}</p>
            <p>Focus Score: {}</p>
            <img src="{}" width="800" height="600"/>
        '''.format(exposure_score, focus_score, url_for('static', filename=file_path))
    return """
<html>
<head>
    <title>Upload and Display Image</title>
    <style>
        body {
            background-color: lightblue;
        }

        .banner {
            background-color: blue;
            height: 50px;
            display: flex;
            justify-content: center;
            align-items: center;
            font-size: 20px;
            color: white;
        }

        .container {
            display: flex;
            flex-direction: column;
            align-items: center;
            margin-top: 50px;
        }

        .buttons {
            display: flex;
            flex-direction: column;
            align-items: center;
            margin-top: 50px;
        }

        .btn {
            background-color: teal;
            color: white;
            padding: 20px;
            border-radius: 5px;
            text-align: center;
            font-size: 18px;
            cursor: pointer;
            margin-bottom: 20px;
        }

        .img-container {
            margin-top: 50px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        .img {
            width: 500px;
            height: auto;
        }

        .scores {
            margin-top: 50px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
    </style>
</head>

<body>
    <div class="banner">Welcome to PictureDay</div>
    <div class="container">
        <form action="/" method="post" enctype="multipart/form-data">
            <div class="buttons">
                <label for="file" class="btn">Choose File</label>
                <input type="file" id="file" name="file" style="display: none;">
                <input type="submit" value="Upload" class="btn">
            </div>
        </form>
        {% if image_path %}
        <div class="img-container">
            <img src="{{ image_path }}" class="img">
        </div>
        <div class="scores">
            <p>Focus Score: {{ focus_score }}</p>
            <p>Exposure Score: {{ exposure_score }}</p>
        </div>
        {% endif %}
    </div>
</body>

</html>

    """


if __name__ == "__main__":
    app.run(debug=True)
