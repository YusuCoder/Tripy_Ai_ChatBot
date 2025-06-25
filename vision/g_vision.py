# from dotenv import load_dotenv
# import os
# from google.cloud import vision
# load_dotenv(dotenv_path="../config/.env")

# client = vision.ImageAnnotatorClient()

# with open("123.jpg", "rb") as image_file:
#     content = image_file.read()

# image = vision.Image(content=content)
# response = client.landmark_detection(image=image)

# for landmark in response.landmark_annotations:
#     print("Landmark:", landmark.description)

from dotenv import load_dotenv
import os
from google.cloud import vision

load_dotenv(dotenv_path="../config/.env")

client = vision.ImageAnnotatorClient()

with open("555.jpg", "rb") as image_file: # Make sure this is the problematic image
    content = image_file.read()

image = vision.Image(content=content)

# Define the features you want to request
features = [
    vision.Feature(type_=vision.Feature.Type.LANDMARK_DETECTION),
    vision.Feature(type_=vision.Feature.Type.WEB_DETECTION),
    vision.Feature(type_=vision.Feature.Type.LABEL_DETECTION)
]

# Send the request with multiple features
response = client.annotate_image({
    'image': image,
    'features': features
})

print("\n--- Landmark Detection Results ---")
if response.landmark_annotations:
    for landmark in response.landmark_annotations:
        print(f"  Landmark: {landmark.description} (Confidence: {landmark.score:.2f})")
        # You can also access locations if available
        for loc in landmark.locations:
            print(f"    Lat/Lng: ({loc.lat_lng.latitude}, {loc.lat_lng.longitude})")
else:
    print("  No landmarks detected directly.")

print("\n--- Web Detection Results ---")

if response.web_detection:
    if response.web_detection.web_entities:
        print("  Web Entities:")
        for entity in response.web_detection.web_entities:
            print(f"    {entity.description} (Score: {entity.score:.2f})")
    if response.web_detection.best_guess_labels:
        print("  Best Guess Labels:")
        for label in response.web_detection.best_guess_labels:
            # FIX: Removed '.score' as WebLabel does not have it
            print(f"    {label.label}") # Corrected line
    if response.web_detection.pages_with_matching_images:
        print("  Pages with Matching Images:")
        for page in response.web_detection.pages_with_matching_images:
            print(f"    {page.url} (Score: {page.score:.2f})")
    if not response.web_detection.web_entities and not response.web_detection.best_guess_labels and not response.web_detection.pages_with_matching_images:
        print("  No significant web detection results.")
else:
    print("  No web detection performed or results available.")



print("\n--- Label Detection Results ---")
if response.label_annotations:
    for label in response.label_annotations:
        print(f"  Label: {label.description} (Confidence: {label.score:.2f})")
else:
    print("  No labels detected.")

print("\n--- Raw Response for Debugging ---")
# Print the entire response object for deep debugging
# print(response)