#!/usr/bin/env python
"""
API Testing Script for Pet Face ID Registration System
This script demonstrates how to use the main API endpoints
"""

import requests
import json
import os
from typing import Dict, Optional

BASE_URL = "http://127.0.0.1:8000/api"


class PetFaceIDAPITester:
    """API testing class for Pet Face ID system"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.auth_token = None
    
    def register_user(self, user_data: Dict) -> Dict:
        """Register a new user"""
        url = f"{self.base_url}/auth/register/"
        response = self.session.post(url, json=user_data)
        
        if response.status_code == 201:
            data = response.json()
            self.auth_token = data['tokens']['access']
            self.session.headers.update({
                'Authorization': f'Bearer {self.auth_token}'
            })
            print("✅ User registered successfully!")
            return data
        else:
            print(f"❌ Registration failed: {response.text}")
            return {}
    
    def login_user(self, email: str, password: str) -> Dict:
        """Login user and get authentication token"""
        url = f"{self.base_url}/auth/login/"
        data = {"email": email, "password": password}
        response = self.session.post(url, json=data)
        
        if response.status_code == 200:
            data = response.json()
            self.auth_token = data['tokens']['access']
            self.session.headers.update({
                'Authorization': f'Bearer {self.auth_token}'
            })
            print("✅ Login successful!")
            return data
        else:
            print(f"❌ Login failed: {response.text}")
            return {}
    
    def create_pet(self, pet_data: Dict) -> Dict:
        """Create a new pet"""
        url = f"{self.base_url}/pets/"
        response = self.session.post(url, json=pet_data)
        
        if response.status_code == 201:
            print("✅ Pet created successfully!")
            return response.json()
        else:
            print(f"❌ Pet creation failed: {response.text}")
            return {}
    
    def start_face_id(self, pet_id: str) -> Dict:
        """Start Face ID registration for a pet"""
        url = f"{self.base_url}/pets/{pet_id}/start_face_id/"
        response = self.session.post(url)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Face ID session started!")
            print(f"Session Token: {data['session']['session_token']}")
            return data
        else:
            print(f"❌ Face ID start failed: {response.text}")
            return {}
    
    def upload_pet_images(self, session_token: str, image_paths: list) -> Dict:
        """Upload images for Face ID registration"""
        url = f"{self.base_url}/pets/images/upload/"
        
        files = []
        for i, image_path in enumerate(image_paths):
            if os.path.exists(image_path):
                files.append(('images', open(image_path, 'rb')))
            else:
                print(f"⚠️  Image not found: {image_path}")
        
        if not files:
            print("❌ No valid images to upload")
            return {}
        
        data = {'session_token': session_token}
        response = self.session.post(url, data=data, files=files)
        
        # Close file handles
        for _, file_handle in files:
            file_handle.close()
        
        if response.status_code == 200:
            print("✅ Images uploaded successfully!")
            return response.json()
        else:
            print(f"❌ Image upload failed: {response.text}")
            return {}
    
    def complete_face_id(self, pet_id: str, session_token: str) -> Dict:
        """Complete Face ID registration"""
        url = f"{self.base_url}/pets/{pet_id}/complete_face_id/"
        data = {
            "session_token": session_token,
            "success": True,
            "notes": "API test completion"
        }
        response = self.session.post(url, json=data)
        
        if response.status_code == 200:
            print("✅ Face ID registration completed!")
            return response.json()
        else:
            print(f"❌ Face ID completion failed: {response.text}")
            return {}
    
    def create_qr_code(self, qr_data: Dict) -> Dict:
        """Create a QR code"""
        url = f"{self.base_url}/qr/codes/"
        response = self.session.post(url, json=qr_data)
        
        if response.status_code == 201:
            print("✅ QR code created successfully!")
            return response.json()
        else:
            print(f"❌ QR code creation failed: {response.text}")
            return {}
    
    def scan_qr_code(self, qr_code: str) -> Dict:
        """Scan a QR code"""
        url = f"{self.base_url}/qr/scan/"
        data = {"qr_code": qr_code}
        
        # Don't use authentication for QR scanning
        response = requests.post(url, json=data)
        
        if response.status_code == 200:
            print("✅ QR code scanned successfully!")
            return response.json()
        else:
            print(f"❌ QR code scan failed: {response.text}")
            return {}
    
    def search_by_image(self, image_path: str) -> Dict:
        """Search for pets by image"""
        url = f"{self.base_url}/face-recognition/search/"
        
        if not os.path.exists(image_path):
            print(f"❌ Image not found: {image_path}")
            return {}
        
        files = {'image': open(image_path, 'rb')}
        data = {'top_k': 5}
        
        # Don't use authentication for face search
        response = requests.post(url, data=data, files=files)
        files['image'].close()
        
        if response.status_code == 200:
            print("✅ Face search completed!")
            return response.json()
        else:
            print(f"❌ Face search failed: {response.text}")
            return {}
    
    def get_user_stats(self) -> Dict:
        """Get user statistics"""
        url = f"{self.base_url}/auth/stats/"
        response = self.session.get(url)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed to get user stats: {response.text}")
            return {}


def run_basic_test():
    """Run basic API tests"""
    print("🧪 Starting Pet Face ID API Tests")
    print("=" * 50)
    
    tester = PetFaceIDAPITester()
    
    # Test user login (using sample data)
    print("\n1. Testing user login...")
    login_result = tester.login_user("test@petnologia.com.br", "testpass123")
    
    if not login_result:
        print("❌ Login failed. Make sure to run setup_database.py first!")
        return
    
    # Test pet creation
    print("\n2. Testing pet creation...")
    pet_data = {
        "name": "Rex",
        "pet_type": "dog",
        "breed": "German Shepherd",
        "gender": "M"
    }
    pet_result = tester.create_pet(pet_data)
    
    if pet_result:
        pet_id = pet_result['id']
        
        # Test Face ID start
        print("\n3. Testing Face ID registration start...")
        face_id_result = tester.start_face_id(pet_id)
        
        if face_id_result:
            session_token = face_id_result['session']['session_token']
            
            # Note: For real testing, you would upload actual pet images here
            print("\n4. Image upload test skipped (no sample images)")
            print("   In real usage, you would upload pet images here")
            
            # Test Face ID completion
            print("\n5. Testing Face ID completion...")
            completion_result = tester.complete_face_id(pet_id, session_token)
    
    # Test QR code creation
    print("\n6. Testing QR code creation...")
    qr_data = {
        "clinic_name": "Test Clinic",
        "veterinarian_name": "Dr. Test",
        "expire_hours": 24
    }
    qr_result = tester.create_qr_code(qr_data)
    
    if qr_result:
        qr_code = qr_result['qr_code']['code']
        
        # Test QR code scanning
        print("\n7. Testing QR code scanning...")
        scan_result = tester.scan_qr_code(qr_code)
    
    # Test user stats
    print("\n8. Testing user statistics...")
    stats = tester.get_user_stats()
    if stats:
        print(f"   Total pets: {stats.get('pets_count', 0)}")
        print(f"   Registered pets: {stats.get('registered_pets', 0)}")
        print(f"   Active QR codes: {stats.get('active_qr_codes', 0)}")
    
    print("\n✅ API tests completed!")
    print("\n📝 Notes:")
    print("• For complete testing, add actual pet images")
    print("• Test face search with uploaded images")
    print("• Check Django admin for data verification")


def run_registration_workflow():
    """Run complete pet registration workflow"""
    print("🔄 Running Complete Pet Registration Workflow")
    print("=" * 50)
    
    tester = PetFaceIDAPITester()
    
    # Login
    login_result = tester.login_user("test@petnologia.com.br", "testpass123")
    if not login_result:
        return
    
    # Create pet
    pet_data = {
        "name": "Fluffy",
        "pet_type": "cat",
        "breed": "Maine Coon",
        "gender": "F"
    }
    pet_result = tester.create_pet(pet_data)
    
    if pet_result:
        pet_id = pet_result['id']
        print(f"Pet ID: {pet_id}")
        
        # Start Face ID
        face_id_result = tester.start_face_id(pet_id)
        
        if face_id_result:
            session_token = face_id_result['session']['session_token']
            print(f"Session Token: {session_token}")
            
            # In a real app, you would:
            # 1. Capture 10 seconds of images
            # 2. Upload them using upload_pet_images()
            # 3. Complete the registration
            
            print("\n🎯 Workflow completed successfully!")
            print("In a real application, you would now:")
            print("1. Capture pet images using mobile camera")
            print("2. Upload images during the 10-second window")
            print("3. Complete Face ID registration")
            print("4. Generate embeddings for face matching")


if __name__ == "__main__":
    print("Pet Face ID API Testing Script")
    print("=" * 40)
    print("1. Basic API Test")
    print("2. Registration Workflow")
    print("3. Exit")
    
    choice = input("\nSelect test option (1-3): ")
    
    if choice == "1":
        run_basic_test()
    elif choice == "2":
        run_registration_workflow()
    else:
        print("Goodbye! 👋") 