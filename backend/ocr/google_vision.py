import os
from typing import List, Optional
from google.cloud import vision
from google.oauth2 import service_account

# Global client to reuse connection
_client: Optional[vision.ImageAnnotatorClient] = None

def get_vision_client() -> vision.ImageAnnotatorClient:
    global _client
    if _client:
        return _client

    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds_path or not os.path.exists(creds_path):
        # Allow default credentials if set up in environment differently
        # But commonly we need the key file.
        # We will try default.
        try:
             _client = vision.ImageAnnotatorClient()
             return _client
        except Exception:
             raise Exception(
                "Google Cloud Credentials not found. Please set GOOGLE_APPLICATION_CREDENTIALS "
                "in your .env file to the path of your JSON key file."
            )
    
    _client = vision.ImageAnnotatorClient.from_service_account_json(creds_path)
    return _client

def detect_text(image_content: bytes) -> str:
    """
    Detects text in an image using Google Cloud Vision API.
    Returns the full text annotation.
    """
    client = get_vision_client()
    image = vision.Image(content=image_content)
    
    # improved for handwriting/documents
    response = client.document_text_detection(image=image)
    
    if response.error.message:
        raise Exception(
            '{}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'.format(
                response.error.message))

    return response.full_text_annotation.text

def detect_document_text(image_content: bytes) -> vision.TextAnnotation:
    """
    Returns the full structured TextAnnotation object for advanced processing.
    """
    client = get_vision_client()
    image = vision.Image(content=image_content)
    
    response = client.document_text_detection(image=image)
    
    if response.error.message:
         raise Exception(f"Google Vision API Error: {response.error.message}")
         
    return response.full_text_annotation
