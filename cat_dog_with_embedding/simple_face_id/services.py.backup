import os
import cv2
import numpy as np
import qrcode
import base64
import io
from PIL import Image
from pathlib import Path
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from sklearn.metrics.pairwise import cosine_similarity
import json

# Import existing services
from face_recognition.services import YOLODetectionService, FaceEmbeddingService
from .models import FaceProject, FaceVector, SimilaritySearch

logger = logging.getLogger(__name__)


class SimpleFaceIdService:
    """Main service for the simplified face ID system"""
    
    def __init__(self):
        self.yolo_service = YOLODetectionService()
        self.embedding_service = FaceEmbeddingService()
        self.base_storage_path = Path(settings.MEDIA_ROOT) / 'face_crops'
        self.base_storage_path.mkdir(parents=True, exist_ok=True)
    
    def generate_project_id(self, name: str, input_id: str) -> str:
        """Generate project ID: first 6 digits of input_id + first 3 letters of name"""
        # Extract first 6 digits from input_id
        digits = ''.join(filter(str.isdigit, input_id))[:6]
        if len(digits) < 6:
            digits = digits.ljust(6, '0')  # Pad with zeros if needed
        
        # Extract first 3 letters from name
        letters = ''.join(filter(str.isalpha, name.lower()))[:3]
        if len(letters) < 3:
            letters = letters.ljust(3, 'x')  # Pad with 'x' if needed
        
        return digits + letters
    
    def generate_qr_code(self, project_id: str) -> str:
        """Generate QR code for project ID and return as base64 string"""
        try:
            # Create QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(project_id)
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            qr_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return qr_base64
            
        except Exception as e:
            logger.error(f"Error generating QR code: {e}")
            return None
    
    def process_face_registration(self, name: str, input_id: str, image_files: List) -> Dict[str, Any]:
        """
        Process face registration from name, ID, and 20 images
        
        Args:
            name: Name of the person/pet
            input_id: ID provided by user
            image_files: List of uploaded image files
            
        Returns:
            Dict with project_id, qr_code, and processing results
        """
        start_time = time.time()
        
        try:
            # Generate project ID
            project_id = self.generate_project_id(name, input_id)
            
            # Check if project already exists
            if FaceProject.objects.filter(project_id=project_id).exists():
                return {
                    'error': f'Project with ID {project_id} already exists',
                    'project_id': project_id
                }
            
            # Create project
            project = FaceProject.objects.create(
                project_id=project_id,
                name=name,
                input_id=input_id,
                total_images=len(image_files),
                status='processing'
            )
            
            # Create storage folder for this project
            project_folder = self.base_storage_path / project_id
            project_folder.mkdir(parents=True, exist_ok=True)
            
            # Process each image
            processed_count = 0
            face_count = 0
            
            for idx, image_file in enumerate(image_files):
                try:
                    # Save temporary image
                    temp_path = project_folder / f'temp_{idx}.jpg'
                    with open(temp_path, 'wb') as f:
                        for chunk in image_file.chunks():
                            f.write(chunk)
                    
                    # Detect faces using YOLO
                    detections = self.yolo_service.detect_pet_faces(str(temp_path))
                    
                    if detections:
                        # Process the best detection (highest confidence)
                        best_detection = detections[0]
                        
                        # Extract face crop
                        face_crop = self.yolo_service.extract_face_crop(
                            str(temp_path), 
                            best_detection['bounding_box']
                        )
                        
                        if face_crop is not None:
                            # Save face crop
                            face_crop_path = project_folder / f'face_{face_count}.jpg'
                            cv2.imwrite(str(face_crop_path), face_crop)
                            
                            # Generate embedding
                            embedding = self.embedding_service.generate_embedding(face_crop)
                            
                            if embedding is not None:
                                # Save face vector
                                face_vector = FaceVector.objects.create(
                                    project=project,
                                    original_image_name=image_file.name,
                                    face_crop_path=str(face_crop_path.relative_to(settings.MEDIA_ROOT)),
                                    confidence_score=best_detection['confidence'],
                                    bounding_box=best_detection['bounding_box']
                                )
                                face_vector.set_embedding_vector(embedding)
                                face_vector.save()
                                
                                face_count += 1
                    
                    processed_count += 1
                    
                    # Clean up temp file
                    if temp_path.exists():
                        temp_path.unlink()
                        
                except Exception as e:
                    logger.error(f"Error processing image {idx}: {e}")
                    continue
            
            # Generate QR code
            qr_code = self.generate_qr_code(project_id)
            
            # Update project
            project.faces_detected = face_count
            project.qr_code = qr_code
            project.status = 'completed' if face_count > 0 else 'failed'
            project.save()
            
            processing_time = time.time() - start_time
            
            return {
                'project_id': project_id,
                'qr_code': qr_code,
                'name': name,
                'total_images': len(image_files),
                'faces_detected': face_count,
                'processing_time': processing_time,
                'status': project.status
            }
            
        except Exception as e:
            logger.error(f"Error in face registration: {e}")
            return {
                'error': str(e),
                'project_id': project_id if 'project_id' in locals() else None
            }
    
    def find_similar_face(self, search_image_file) -> Dict[str, Any]:
        """
        Find similar face from search image
        
        Args:
            search_image_file: Uploaded image file for search
            
        Returns:
            Dict with similarity results
        """
        start_time = time.time()
        
        try:
            # Save temporary search image
            temp_path = self.base_storage_path / f'search_temp_{int(time.time())}.jpg'
            with open(temp_path, 'wb') as f:
                for chunk in search_image_file.chunks():
                    f.write(chunk)
            
            # Detect face in search image
            detections = self.yolo_service.detect_pet_faces(str(temp_path))
            
            if not detections:
                return {
                    'error': 'No face detected in search image',
                    'similarity_score': 0.0
                }
            
            # Extract face crop from best detection
            best_detection = detections[0]
            face_crop = self.yolo_service.extract_face_crop(
                str(temp_path), 
                best_detection['bounding_box']
            )
            
            if face_crop is None:
                return {
                    'error': 'Could not extract face from search image',
                    'similarity_score': 0.0
                }
            
            # Generate embedding for search image
            search_embedding = self.embedding_service.generate_embedding(face_crop)
            
            if search_embedding is None:
                return {
                    'error': 'Could not generate embedding for search image',
                    'similarity_score': 0.0
                }
            
            # Find most similar face
            best_match = self.find_most_similar_vector(search_embedding)
            
            processing_time = time.time() - start_time
            
            # Log search
            similarity_search = SimilaritySearch.objects.create(
                search_image_name=search_image_file.name,
                best_match_project=best_match['project'] if best_match else None,
                best_match_vector=best_match['vector'] if best_match else None,
                similarity_score=best_match['similarity'] if best_match else 0.0,
                processing_time=processing_time
            )
            
            # Clean up temp file
            if temp_path.exists():
                temp_path.unlink()
            
            if best_match:
                return {
                    'project_id': best_match['project'].project_id,
                    'name': best_match['project'].name,
                    'similarity_score': best_match['similarity'],
                    'face_image_path': best_match['vector'].face_crop_path,
                    'processing_time': processing_time
                }
            else:
                return {
                    'error': 'No similar faces found',
                    'similarity_score': 0.0,
                    'processing_time': processing_time
                }
                
        except Exception as e:
            logger.error(f"Error in similarity search: {e}")
            return {
                'error': str(e),
                'similarity_score': 0.0
            }
    
    def find_most_similar_vector(self, search_embedding: np.ndarray) -> Optional[Dict[str, Any]]:
        """Find the most similar face vector"""
        try:
            # Get all face vectors
            face_vectors = FaceVector.objects.all()
            
            if not face_vectors.exists():
                return None
            
            best_similarity = -1
            best_match = None
            
            search_embedding = search_embedding.reshape(1, -1)
            
            for face_vector in face_vectors:
                # Convert stored embedding back to numpy array
                stored_embedding = np.array(face_vector.embedding_vector).reshape(1, -1)
                
                # Calculate cosine similarity
                similarity = cosine_similarity(search_embedding, stored_embedding)[0][0]
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = {
                        'project': face_vector.project,
                        'vector': face_vector,
                        'similarity': float(similarity)
                    }
            
            return best_match
            
        except Exception as e:
            logger.error(f"Error finding similar vector: {e}")
            return None 