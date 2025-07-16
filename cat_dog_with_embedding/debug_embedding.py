import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pet_face_id.settings')
django.setup()

from face_recognition.services import FaceEmbeddingService
import cv2
import numpy as np

# Test embedding generation
service = FaceEmbeddingService()
print(f"Model loaded: {service.model is not None}")
print(f"Model name: {service.model}")

# Create a dummy face crop
dummy_face = np.ones((100, 100, 3), dtype=np.uint8) * 128  # Gray image
print(f"Dummy face shape: {dummy_face.shape}")

# Test embedding generation
try:
    embedding = service.generate_embedding(dummy_face)
    print(f"Embedding generated: {embedding is not None}")
    if embedding is not None:
        print(f"Embedding shape: {embedding.shape}")
        print(f"Embedding type: {type(embedding)}")
    else:
        print("Embedding is None!")
except Exception as e:
    print(f"Error generating embedding: {e}")
    import traceback
    traceback.print_exc()
