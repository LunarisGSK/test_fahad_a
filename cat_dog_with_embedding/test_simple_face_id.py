#!/usr/bin/env python3
"""
Test script for the simplified face ID API endpoints.

This script demonstrates how to use the two main API endpoints:
1. /api/simple-face-id/register/ - Register faces from images
2. /api/simple-face-id/search/ - Search for similar faces

Usage:
    python test_simple_face_id.py
"""

import requests
import json
import base64
from pathlib import Path
import os

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/simple-face-id"

def test_face_registration():
    """Test face registration endpoint"""
    print("=" * 50)
    print("Testing Face Registration")
    print("=" * 50)
    
    # Prepare test data
    test_data = {
        'name': 'Fluffy',
        'input_id': '123456789',
    }
    
    # Note: In a real test, you would add actual image files here
    # For now, we'll just show the structure
    print(f"Would register faces for: {test_data['name']} with ID: {test_data['input_id']}")
    print("Expected project_id: 123456flu")
    
    # Example of how to make the request:
    """
    files = []
    for i in range(20):  # Up to 20 images
        image_path = f"test_images/image_{i}.jpg"
        if os.path.exists(image_path):
            files.append(('images', open(image_path, 'rb')))
    
    response = requests.post(
        f"{API_BASE}/register/",
        data=test_data,
        files=files
    )
    
    if response.status_code == 201:
        result = response.json()
        print(f"✓ Registration successful!")
        print(f"Project ID: {result['project_id']}")
        print(f"Faces detected: {result['faces_detected']}")
        print(f"QR code generated: {'Yes' if result['qr_code'] else 'No'}")
        return result['project_id']
    else:
        print(f"✗ Registration failed: {response.status_code}")
        print(response.text)
        return None
    """
    
    return "123456flu"  # Mock project ID for testing

def test_similarity_search():
    """Test similarity search endpoint"""
    print("\n" + "=" * 50)
    print("Testing Similarity Search")
    print("=" * 50)
    
    # Note: In a real test, you would add an actual image file here
    print("Would search for similar faces using a test image")
    
    # Example of how to make the request:
    """
    search_image_path = "test_images/search_image.jpg"
    if os.path.exists(search_image_path):
        with open(search_image_path, 'rb') as image_file:
            files = {'image': image_file}
            response = requests.post(f"{API_BASE}/search/", files=files)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✓ Search successful!")
                print(f"Best match: {result['name']} (ID: {result['project_id']})")
                print(f"Similarity score: {result['similarity_score']:.3f}")
                print(f"Face image: {result['face_image_path']}")
                return result
            else:
                print(f"✗ Search failed: {response.status_code}")
                print(response.text)
                return None
    """
    
    # Mock response for testing
    mock_result = {
        'project_id': '123456flu',
        'name': 'Fluffy',
        'similarity_score': 0.95,
        'face_image_path': 'face_crops/123456flu/face_0.jpg'
    }
    
    print(f"✓ Mock search result:")
    print(f"Best match: {mock_result['name']} (ID: {mock_result['project_id']})")
    print(f"Similarity score: {mock_result['similarity_score']:.3f}")
    print(f"Face image: {mock_result['face_image_path']}")
    
    return mock_result

def test_utility_endpoints():
    """Test utility endpoints"""
    print("\n" + "=" * 50)
    print("Testing Utility Endpoints")
    print("=" * 50)
    
    project_id = "123456flu"
    
    # Test project info
    print(f"1. Project info: GET {API_BASE}/project/{project_id}/")
    
    # Test QR code retrieval
    print(f"2. QR code: GET {API_BASE}/qr-code/{project_id}/")
    
    # Test face image retrieval
    face_image_path = "face_crops/123456flu/face_0.jpg"
    print(f"3. Face image: GET {API_BASE}/face-image/{face_image_path}")
    
    # Test system stats
    print(f"4. System stats: GET {API_BASE}/stats/")

def print_api_documentation():
    """Print API documentation"""
    print("\n" + "=" * 60)
    print("SIMPLIFIED FACE ID API DOCUMENTATION")
    print("=" * 60)
    
    print("\n1. FACE REGISTRATION")
    print("-" * 30)
    print("POST /api/simple-face-id/register/")
    print("Content-Type: multipart/form-data")
    print()
    print("Parameters:")
    print("- name: Name of the person/pet (string)")
    print("- input_id: ID provided by user (string)")
    print("- images: Up to 20 image files (files)")
    print()
    print("Response:")
    print("- project_id: Generated project ID (first 6 digits of input_id + first 3 letters of name)")
    print("- qr_code: Base64 encoded QR code image")
    print("- faces_detected: Number of faces detected and processed")
    print("- processing_time: Time taken to process")
    print()
    print("Example project_id generation:")
    print("- name='Fluffy', input_id='123456789' → project_id='123456flu'")
    print("- name='Rex', input_id='987654321' → project_id='987654rex'")
    
    print("\n2. SIMILARITY SEARCH")
    print("-" * 30)
    print("POST /api/simple-face-id/search/")
    print("Content-Type: multipart/form-data")
    print()
    print("Parameters:")
    print("- image: Image file to search for similar faces")
    print()
    print("Response:")
    print("- project_id: ID of the most similar project")
    print("- name: Name of the most similar match")
    print("- similarity_score: Similarity score (0.0 to 1.0)")
    print("- face_image_path: Path to the matching face image")
    print("- processing_time: Time taken to process")
    
    print("\n3. UTILITY ENDPOINTS")
    print("-" * 30)
    print("GET /api/simple-face-id/project/{project_id}/")
    print("- Get project information")
    print()
    print("GET /api/simple-face-id/qr-code/{project_id}/")
    print("- Get QR code as PNG image")
    print()
    print("GET /api/simple-face-id/face-image/{image_path}")
    print("- Get cropped face image")
    print()
    print("GET /api/simple-face-id/stats/")
    print("- Get system statistics")

def main():
    """Main test function"""
    print("SIMPLE FACE ID API TESTER")
    print("=" * 60)
    
    print_api_documentation()
    
    # Run tests
    project_id = test_face_registration()
    test_similarity_search()
    test_utility_endpoints()
    
    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("=" * 60)
    print("1. Run: python manage.py makemigrations simple_face_id")
    print("2. Run: python manage.py migrate")
    print("3. Start server: python manage.py runserver")
    print("4. Test endpoints with actual images using curl or Postman")
    print()
    print("Example curl command for registration:")
    print("curl -X POST http://localhost:8000/api/simple-face-id/register/ \\")
    print("  -F 'name=Fluffy' \\")
    print("  -F 'input_id=123456789' \\")
    print("  -F 'images=@image1.jpg' \\")
    print("  -F 'images=@image2.jpg' \\")
    print("  ... (up to 20 images)")
    print()
    print("Example curl command for search:")
    print("curl -X POST http://localhost:8000/api/simple-face-id/search/ \\")
    print("  -F 'image=@search_image.jpg'")

if __name__ == "__main__":
    main() 