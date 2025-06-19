from dotenv import load_dotenv
import os
from google.cloud import vision
load_dotenv()

client = vision.ImageAnnotatorClient()

with open("123.jpg", "rb") as image_file:
    content = image_file.read()

image = vision.Image(content=content)
response = client.landmark_detection(image=image)

for landmark in response.landmark_annotations:
    print("Landmark:", landmark.description)