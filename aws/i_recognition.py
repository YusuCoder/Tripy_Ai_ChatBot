import boto3

rekognition = boto3.client('rekognition', region_name="eu-central-1")

def detect_image(image_bytes, max_labels=10, min_confidence=80):
    """
    Detects labels in an image using AWS Rekognition.

    :param image_bytes: Bytes of the image to analyze.
    :param max_labels: Maximum number of labels to return.
    :param min_confidence: Minimum confidence level for labels to be returned.
    :return: List of detected labels with their confidence scores.
    """
    response = rekognition.detect_labels(
        Image={
            'Bytes': image_bytes
        },
        MaxLabels=max_labels,
        MinConfidence=min_confidence
    )

    return response['Labels']
