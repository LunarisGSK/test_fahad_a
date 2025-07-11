#!/usr/bin/env python
"""
Setup script for Pet Face ID Registration System
This script helps with initial database setup and sample data creation
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pet_face_id.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.core.management import execute_from_command_line
from django.contrib.auth import get_user_model
from authentication.models import UserProfile
from pets.models import Pet
from qr_search.models import QRCode, ClinicInfo
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


def create_migrations():
    """Create and apply database migrations"""
    print("🔄 Creating migrations...")
    execute_from_command_line(['manage.py', 'makemigrations'])
    
    print("🔄 Applying migrations...")
    execute_from_command_line(['manage.py', 'migrate'])
    
    print("✅ Database migrations completed!")


def create_superuser():
    """Create a superuser if none exists"""
    if not User.objects.filter(is_superuser=True).exists():
        print("👤 Creating superuser...")
        
        username = input("Enter superuser username (default: admin): ") or "admin"
        email = input("Enter superuser email: ")
        
        if not email:
            email = "admin@petnologia.com.br"
            
        password = input("Enter superuser password (default: admin123): ") or "admin123"
        
        superuser = User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        
        # Create profile
        UserProfile.objects.create(user=superuser)
        
        print(f"✅ Superuser '{username}' created successfully!")
    else:
        print("ℹ️  Superuser already exists.")


def create_sample_data():
    """Create sample data for testing"""
    print("📊 Creating sample data...")
    
    # Create test user
    if not User.objects.filter(username='testuser').exists():
        test_user = User.objects.create_user(
            username='testuser',
            email='test@petnologia.com.br',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        UserProfile.objects.create(
            user=test_user,
            city='São Paulo',
            state='SP',
            country='Brasil'
        )
        print("✅ Test user created (username: testuser, password: testpass123)")
        
        # Create sample pets
        pet1 = Pet.objects.create(
            owner=test_user,
            name='Buddy',
            pet_type='dog',
            breed='Golden Retriever',
            gender='M',
            registration_status='pending'
        )
        
        pet2 = Pet.objects.create(
            owner=test_user,
            name='Whiskers',
            pet_type='cat',
            breed='Persian',
            gender='F',
            registration_status='pending'
        )
        
        print("✅ Sample pets created (Buddy the dog, Whiskers the cat)")
        
        # Create sample clinic
        clinic = ClinicInfo.objects.create(
            owner=test_user,
            name='Clínica Veterinária São Paulo',
            registration_number='CRMV-SP-12345',
            address='Rua das Flores, 123',
            city='São Paulo',
            state='SP',
            postal_code='01234-567',
            phone='(11) 1234-5678',
            email='contato@clinicasp.com.br',
            specialties=['Clínica Geral', 'Cirurgia', 'Dermatologia'],
            services=['Consultas', 'Vacinação', 'Cirurgias', 'Exames']
        )
        
        # Create sample QR code
        qr_code = QRCode.objects.create(
            created_by=test_user,
            code=QRCode.generate_unique_code(),
            clinic_name=clinic.name,
            veterinarian_name='Dr. João Silva',
            expires_at=timezone.now() + timedelta(hours=24),
            location='Recepção da clínica'
        )
        
        print("✅ Sample clinic and QR code created")
    else:
        print("ℹ️  Sample data already exists.")


def show_api_info():
    """Show API endpoint information"""
    print("\n🚀 Pet Face ID API System Setup Complete!")
    print("=" * 50)
    print("📍 Server URL: http://127.0.0.1:8000/")
    print("🔧 Admin Panel: http://127.0.0.1:8000/admin/")
    print("\n📚 API Endpoints:")
    print("• Authentication: /api/auth/")
    print("• Pets: /api/pets/")
    print("• Face Recognition: /api/face-recognition/")
    print("• QR Codes: /api/qr/")
    print("\n🧪 Test Credentials:")
    print("• Username: testuser")
    print("• Password: testpass123")
    print("• Email: test@petnologia.com.br")
    print("\n🔍 Next Steps:")
    print("1. Start the server: python manage.py runserver")
    print("2. Test API endpoints using the provided credentials")
    print("3. Access admin panel to view data")
    print("4. Upload pet images to test Face ID registration")
    print("5. Generate QR codes and test search functionality")


def main():
    """Main setup function"""
    print("🐶🐱 Pet Face ID Registration System Setup")
    print("=" * 50)
    
    # Create database and apply migrations
    create_migrations()
    
    # Create superuser
    create_superuser()
    
    # Create sample data
    create_sample = input("\nCreate sample data for testing? (y/n): ").lower().startswith('y')
    if create_sample:
        create_sample_data()
    
    # Show API information
    show_api_info()


if __name__ == '__main__':
    main() 