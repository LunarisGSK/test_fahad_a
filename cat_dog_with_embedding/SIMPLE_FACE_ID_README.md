# Simple Face ID API

A simplified face recognition system that provides just 2 main API endpoints for registering faces and searching for similar faces.

## Overview

This system takes a name, ID, and up to 20 images, then:
1. Detects faces using YOLO model
2. Crops the faces and stores them in folders
3. Generates embeddings and stores them in a vector database
4. Creates a project ID and QR code
5. Provides similarity search functionality

## Project ID Generation

The project ID is generated using this formula:
- **First 6 digits of input ID + First 3 letters of name**

Examples:
- `name="Fluffy"`, `input_id="123456789"` → `project_id="123456flu"`
- `name="Rex"`, `input_id="987654321"` → `project_id="987654rex"`

## API Endpoints

### 1. Face Registration

**POST** `/api/simple-face-id/register/`

Register faces from images and generate project ID + QR code.

**Request:**
```bash
curl -X POST http://localhost:8000/api/simple-face-id/register/ \
  -F 'name=Fluffy' \
  -F 'input_id=123456789' \
  -F 'images=@image1.jpg' \
  -F 'images=@image2.jpg' \
  -F 'images=@image3.jpg' \
  ... (up to 20 images)
```

**Response:**
```json
{
  "success": true,
  "project_id": "123456flu",
  "qr_code": "iVBORw0KGgoAAAANSUhEUgAA...", // Base64 encoded QR code
  "name": "Fluffy",
  "total_images": 20,
  "faces_detected": 18,
  "processing_time": 12.5,
  "status": "completed"
}
```

### 2. Similarity Search

**POST** `/api/simple-face-id/search/`

Search for similar faces using an image.

**Request:**
```bash
curl -X POST http://localhost:8000/api/simple-face-id/search/ \
  -F 'image=@search_image.jpg'
```

**Response:**
```json
{
  "success": true,
  "project_id": "123456flu",
  "name": "Fluffy",
  "similarity_score": 0.95,
  "face_image_path": "face_crops/123456flu/face_0.jpg",
  "processing_time": 2.1
}
```

## Utility Endpoints

### Get Project Information
**GET** `/api/simple-face-id/project/{project_id}/`

### Get QR Code as Image
**GET** `/api/simple-face-id/qr-code/{project_id}/`

### Get Face Image
**GET** `/api/simple-face-id/face-image/{image_path}`

### Get System Statistics
**GET** `/api/simple-face-id/stats/`

## Setup and Installation

1. **Install Dependencies:**
```bash
pip install -r requirements.txt
```

2. **Run Migrations:**
```bash
python manage.py makemigrations simple_face_id
python manage.py migrate
```

3. **Start Server:**
```bash
python manage.py runserver
```

4. **Test the API:**
```bash
python test_simple_face_id.py
```

## How It Works

### Registration Flow:
1. User provides name, ID, and 20 images
2. System generates project ID (first 6 digits of ID + first 3 letters of name)
3. YOLO model detects faces in each image
4. Faces are cropped and saved to `media/face_crops/{project_id}/`
5. Face embeddings are generated and stored in database
6. QR code is generated for the project ID
7. Returns project ID and QR code

### Search Flow:
1. User provides a search image
2. YOLO model detects face in search image
3. Face embedding is generated
4. System compares with all stored embeddings using cosine similarity
5. Returns the best match with similarity score

## File Structure

```
simple_face_id/
├── models.py           # FaceProject, FaceVector, SimilaritySearch models
├── services.py         # SimpleFaceIdService with YOLO and embedding logic
├── views.py            # API endpoints
├── serializers.py      # Request/response serializers
├── urls.py             # URL configuration
├── admin.py            # Django admin interface
└── migrations/         # Database migrations
```

## Storage Structure

```
media/
└── face_crops/
    ├── 123456flu/          # Project ID folder
    │   ├── face_0.jpg      # Cropped face images
    │   ├── face_1.jpg
    │   └── ...
    ├── 987654rex/
    │   ├── face_0.jpg
    │   └── ...
    └── ...
```

## Key Features

- ✅ **Simple API**: Only 2 main endpoints
- ✅ **YOLO Face Detection**: Uses existing YOLOv8 model
- ✅ **Automatic Cropping**: Faces are automatically detected and cropped
- ✅ **Vector Database**: Embeddings stored for similarity search
- ✅ **QR Code Generation**: Automatic QR code creation
- ✅ **Project ID System**: Predictable ID generation
- ✅ **Similarity Search**: Cosine similarity matching
- ✅ **No Authentication**: Public API (as requested)

## Error Handling

The API handles various error cases:
- No faces detected in images
- Invalid input data
- Duplicate project IDs
- Processing failures
- Missing images

## Performance Considerations

- **Batch Processing**: Images are processed sequentially
- **Storage**: Face crops are stored locally in media folder
- **Similarity Search**: Linear search through all vectors (can be optimized with vector databases like Pinecone for large datasets)
- **Concurrency**: Can handle multiple requests simultaneously

## Next Steps

1. Test with real images
2. Monitor performance with large datasets
3. Consider adding vector database optimization (Pinecone, Weaviate)
4. Add batch processing for faster image handling
5. Implement caching for better performance

## Support

If you need help or have questions about the API, please check the test script (`test_simple_face_id.py`) for usage examples. 