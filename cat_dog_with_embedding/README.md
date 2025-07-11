# Pet Face ID Registration System 🐶🐱

A comprehensive Django REST API system for pet face registration and recognition using YOLO and face embeddings, with QR code-based search functionality.

## 🚀 Features

### Core Functionality
- **Pet Registration**: Complete pet profile management with face ID registration
- **Face ID Capture**: 10-second face capture process with real-time validation
- **AI-Powered Recognition**: YOLO-based face detection + advanced face embeddings
- **QR Code Search**: Generate QR codes for pet verification at clinics
- **Similarity Matching**: High-accuracy face similarity comparison

### Trail System
- **Eagle Trail**: 90%+ similarity (very high confidence)
- **Lobo Trail**: 80-90% similarity (high confidence)
- **No Match**: <80% similarity

### Authentication & Security
- JWT-based authentication
- User registration and profile management
- Secure image upload and processing
- Session-based Face ID registration

## 🛠 Technical Stack

- **Backend**: Django 4.2.7 + Django REST Framework
- **AI Models**: 
  - YOLOv8 for pet face detection
  - CLIP-ViT-B-32 for face embeddings
- **Database**: SQLite (development) / PostgreSQL (production)
- **Authentication**: JWT tokens
- **File Storage**: Local storage (can be configured for cloud)

## 📋 Prerequisites

- Python 3.8+
- pip package manager
- Git

## 🔧 Installation & Setup

### 1. Clone and Setup Environment

```bash
# Clone the repository
git clone <repository-url>
cd cat_dog_with_embedding

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Setup

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### 3. AI Models Setup

```bash
# Create AI models directory (if not exists)
mkdir -p ai_models

# Place your trained YOLOv8 model in ai_models/yolov8l_pet_faces.pt
# If you don't have a custom model, the system will use the default YOLOv8l
```

### 4. Run the Server

```bash
# Start development server
python manage.py runserver

# Server will be available at http://127.0.0.1:8000/
```

## 📚 API Documentation

### Authentication Endpoints

```
POST /api/auth/register/          # User registration
POST /api/auth/login/             # User login
POST /api/auth/logout/            # User logout
GET  /api/auth/profile/           # Get user profile
PUT  /api/auth/profile/           # Update user profile
POST /api/auth/password/change/   # Change password
```

### Pet Management Endpoints

```
GET    /api/pets/                 # List user's pets
POST   /api/pets/                 # Create new pet
GET    /api/pets/{id}/            # Get pet details
PUT    /api/pets/{id}/            # Update pet
DELETE /api/pets/{id}/            # Delete pet

# Face ID Registration
POST   /api/pets/{id}/start_face_id/      # Start Face ID session
POST   /api/pets/{id}/complete_face_id/   # Complete Face ID session
POST   /api/pets/images/upload/           # Upload images during session
GET    /api/pets/{id}/registration_status/ # Check registration status
```

### Face Recognition Endpoints

```
POST /api/face-recognition/search/              # Search by uploaded image
GET  /api/face-recognition/embeddings/          # List embeddings
POST /api/face-recognition/embeddings/generate/ # Generate embeddings
GET  /api/face-recognition/embeddings/status/   # Embedding status
GET  /api/face-recognition/history/             # Search history
```

### QR Code Endpoints

```
GET  /api/qr/codes/       # List user's QR codes
POST /api/qr/codes/       # Create new QR code
POST /api/qr/scan/        # Scan QR code
POST /api/qr/search/      # Search via QR code
GET  /api/qr/codes/stats/ # QR usage statistics
```

## 🔄 Usage Workflow

### 1. Pet Registration Flow

```python
# 1. Register user
POST /api/auth/register/
{
    "username": "user123",
    "email": "user@example.com",
    "password": "securepassword",
    "password_confirm": "securepassword",
    "first_name": "John",
    "last_name": "Doe"
}

# 2. Create pet
POST /api/pets/
{
    "name": "Buddy",
    "pet_type": "dog",
    "breed": "Golden Retriever",
    "gender": "M"
}

# 3. Start Face ID registration
POST /api/pets/{pet_id}/start_face_id/

# 4. Upload images (during 10-second capture)
POST /api/pets/images/upload/
{
    "session_token": "session_token_here",
    "images": [image_files]
}

# 5. Complete Face ID registration
POST /api/pets/{pet_id}/complete_face_id/
{
    "session_token": "session_token_here",
    "success": true
}
```

### 2. QR Code Search Flow

```python
# 1. Create QR code (by clinic/vet)
POST /api/qr/codes/
{
    "clinic_name": "Pet Clinic ABC",
    "veterinarian_name": "Dr. Smith",
    "expire_hours": 24
}

# 2. Scan QR code
POST /api/qr/scan/
{
    "qr_code": "QR_CODE_HERE"
}

# 3. Upload search image
POST /api/qr/search/
{
    "session_token": "session_token_from_scan",
    "image": image_file
}

# Response includes trail information:
{
    "confidence_level": "eagle_trail",
    "similarity_percentage": 95.2,
    "trail_icon": "🦅",
    "trail_message": "Eagle Trail: Nível muito alto de confiabilidade..."
}
```

## 🔑 Key Features

### Face ID Registration Process
1. **10-second capture window** with real-time validation
2. **YOLO-based face detection** for quality control
3. **Multiple image processing** for robust embeddings
4. **Automatic quality assessment** (blur, brightness, contrast)
5. **Session management** with expiration handling

### AI Processing Pipeline
1. **Image Upload** → **YOLO Detection** → **Quality Assessment**
2. **Face Extraction** → **Embedding Generation** → **Storage**
3. **Search Query** → **Similarity Calculation** → **Trail Classification**

### QR Code System
- **Dynamic QR generation** with expiration
- **Session-based searches** for security
- **Usage tracking** and analytics
- **Clinic management** integration

## 🏥 Production Considerations

### Environment Variables
Create a `.env` file:

```
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com
DATABASE_URL=postgresql://user:pass@localhost/dbname

# AI Model Settings
YOLO_MODEL_PATH=/path/to/your/model.pt
FACE_EMBEDDING_MODEL=sentence-transformers/clip-ViT-B-32

# File Storage (for production)
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_STORAGE_BUCKET_NAME=your-bucket-name
```

### Deployment
1. Configure PostgreSQL database
2. Set up Redis for Celery (background tasks)
3. Configure file storage (AWS S3, etc.)
4. Set up proper logging
5. Configure CORS for frontend domains

### Performance Optimization
- Use background tasks for embedding generation
- Implement image compression
- Add database indexing
- Configure caching for frequent queries

## 🧪 Testing

```bash
# Run tests
python manage.py test

# Run specific app tests
python manage.py test authentication
python manage.py test pets
python manage.py test face_recognition
python manage.py test qr_search
```

## 📊 Monitoring & Analytics

Access Django admin at `/admin/` to monitor:
- User registrations and activity
- Pet registrations and status
- Face recognition results and accuracy
- QR code usage and statistics
- System performance metrics

## 🤝 Support

For questions or issues:
1. Check the API documentation
2. Review the code comments
3. Test with provided examples
4. Check Django admin for data verification

## 📜 License

This project is proprietary software for Pet Face ID Registration System.

---

**Ready to deploy!** 🚀

The system is fully functional with:
✅ Complete user authentication
✅ Pet registration with Face ID
✅ AI-powered face recognition
✅ QR code generation and scanning
✅ Trail-based similarity matching
✅ Comprehensive API documentation
✅ Admin interface for management 