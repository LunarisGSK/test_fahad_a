import cv2
import numpy as np
import torch
from PIL import Image
import time
import logging
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
import json

from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from ultralytics import YOLO
from sentence_transformers import SentenceTransformer
import torchvision.transforms as transforms

from .models import FaceEmbedding, FaceDetection, FaceRecognitionResult
from pets.models import Pet, PetImage

logger = logging.getLogger(__name__)


class YOLODetectionService:
    """Service for YOLO-based pet face detection"""
    
    def __init__(self):
        self.model = None
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.confidence_threshold = 0.5
        self.load_model()
    
    def load_model(self):
        """Load the YOLO model"""
        try:
            model_path = settings.YOLO_MODEL_PATH
            if not Path(model_path).exists():
                logger.warning(f"YOLO model not found at {model_path}. Using default YOLOv8l.")
                # Use the pre-trained YOLOv8l model if custom model is not available
                self.model = YOLO('yolov8l.pt')
            else:
                self.model = YOLO(model_path)
            
            logger.info(f"YOLO model loaded successfully on {self.device}")
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            # Fallback to base model
            self.model = YOLO('yolov8l.pt')
    
    def detect_pet_faces(self, image_path: str) -> List[Dict[str, Any]]:
        """
        Detect pet faces in an image
        
        Args:
            image_path: Path to the image file
            
        Returns:
            List of detection results with bounding boxes and confidence scores
        """
        try:
            if not self.model:
                logger.error("YOLO model not loaded")
                return []
            
            # Run inference
            results = self.model(image_path, device=self.device, conf=self.confidence_threshold)
            
            detections = []
            for r in results:
                boxes = r.boxes
                if boxes is not None:
                    for box in boxes:
                        # Extract box coordinates
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        confidence = box.conf[0].cpu().numpy()
                        class_id = int(box.cls[0].cpu().numpy())
                        
                        # Map class names (adjust based on your trained model)
                        class_names = {
                            0: 'cat',
                            1: 'cat_face', 
                            2: 'dog',
                            3: 'dog_face'
                        }
                        
                        class_name = class_names.get(class_id, 'unknown')
                        
                        detection = {
                            'class': class_name,
                            'confidence': float(confidence),
                            'bounding_box': [float(x1), float(y1), float(x2), float(y2)],
                            'area': (x2 - x1) * (y2 - y1)
                        }
                        detections.append(detection)
            
            # Sort by confidence score
            detections.sort(key=lambda x: x['confidence'], reverse=True)
            return detections
            
        except Exception as e:
            logger.error(f"Error in pet face detection: {e}")
            return []
    
    def extract_face_crop(self, image_path: str, bounding_box: List[float]) -> Optional[np.ndarray]:
        """
        Extract face crop from image using bounding box
        
        Args:
            image_path: Path to the image
            bounding_box: [x1, y1, x2, y2] coordinates
            
        Returns:
            Cropped face image as numpy array
        """
        try:
            image = cv2.imread(image_path)
            if image is None:
                return None
            
            x1, y1, x2, y2 = map(int, bounding_box)
            
            # Ensure coordinates are within image bounds
            h, w = image.shape[:2]
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(w, x2)
            y2 = min(h, y2)
            
            # Extract face crop
            face_crop = image[y1:y2, x1:x2]
            return face_crop
            
        except Exception as e:
            logger.error(f"Error extracting face crop: {e}")
            return None
    
    def assess_image_quality(self, image_path: str) -> Dict[str, float]:
        """
        Assess image quality metrics
        
        Args:
            image_path: Path to the image
            
        Returns:
            Dictionary with quality metrics
        """
        try:
            image = cv2.imread(image_path)
            if image is None:
                return {}
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Calculate blur score using Laplacian variance
            blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Calculate brightness
            brightness_score = np.mean(gray)
            
            # Calculate contrast (standard deviation of pixel values)
            contrast_score = np.std(gray)
            
            return {
                'blur_score': float(blur_score),
                'brightness_score': float(brightness_score),
                'contrast_score': float(contrast_score)
            }
            
        except Exception as e:
            logger.error(f"Error assessing image quality: {e}")
            return {}


class FaceEmbeddingService:
    """Service for generating face embeddings using sentence transformers"""
    
    def __init__(self):
        self.model = None
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.load_model()
        
        # Image preprocessing
        self.preprocess = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
    
    def load_model(self):
        """Load the face embedding model"""
        try:
            model_name = settings.FACE_EMBEDDING_MODEL
            self.model = SentenceTransformer(model_name, device=self.device)
            logger.info(f"Face embedding model loaded: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load face embedding model: {e}")
            # Fallback to a basic model
            self.model = SentenceTransformer('clip-ViT-B-32', device=self.device)
    
    def generate_embedding(self, face_crop: np.ndarray) -> Optional[np.ndarray]:
        """
        Generate face embedding from face crop
        
        Args:
            face_crop: Face image as numpy array
            
        Returns:
            Face embedding vector
        """
        try:
            if self.model is None:
                logger.error("Embedding model not loaded")
                return None
            
            # Convert to PIL Image
            if len(face_crop.shape) == 3:
                face_crop = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)
            
            pil_image = Image.fromarray(face_crop)
            
            # Generate embedding using the CLIP model
            embedding = self.model.encode([pil_image], convert_to_tensor=False)[0]
            
            return np.array(embedding)
            
        except Exception as e:
            logger.error(f"Error generating face embedding: {e}")
            return None
    
    def generate_pet_embeddings(self, pet_images: List[PetImage]) -> Optional[FaceEmbedding]:
        """
        Generate embeddings for a pet from multiple images
        
        Args:
            pet_images: List of PetImage objects
            
        Returns:
            FaceEmbedding object or None
        """
        try:
            if not pet_images:
                return None
            
            pet = pet_images[0].pet
            all_embeddings = []
            successful_images = 0
            
            yolo_service = YOLODetectionService()
            
            for pet_image in pet_images:
                try:
                    image_path = pet_image.image.path
                    
                    # Detect faces in the image
                    detections = yolo_service.detect_pet_faces(image_path)
                    
                    # Filter for face detections
                    face_detections = [d for d in detections if d['class'].endswith('_face')]
                    
                    if not face_detections:
                        continue
                    
                    # Use the highest confidence face detection
                    best_detection = face_detections[0]
                    
                    # Save detection to database
                    face_detection = FaceDetection.objects.create(
                        image=pet_image,
                        detected_class=best_detection['class'],
                        confidence=best_detection['confidence'],
                        bounding_box=best_detection['bounding_box'],
                        model_version='yolov8l',
                        face_area=best_detection['area']
                    )
                    
                    # Extract face crop
                    face_crop = yolo_service.extract_face_crop(image_path, best_detection['bounding_box'])
                    
                    if face_crop is None:
                        continue
                    
                    # Generate embedding
                    embedding = self.generate_embedding(face_crop)
                    
                    if embedding is not None:
                        all_embeddings.append(embedding)
                        successful_images += 1
                    
                except Exception as e:
                    logger.error(f"Error processing image {pet_image.id}: {e}")
                    continue
            
            if not all_embeddings:
                logger.warning(f"No valid embeddings generated for pet {pet.id}")
                return None
            
            # Average all embeddings to create a representative embedding
            final_embedding = np.mean(all_embeddings, axis=0)
            
            # Create FaceEmbedding object
            face_embedding = FaceEmbedding.objects.create(
                pet=pet,
                embedding_model=settings.FACE_EMBEDDING_MODEL,
                vector_dimension=len(final_embedding),
                status='completed',
                source_images_count=successful_images
            )
            
            face_embedding.set_embedding_vector(final_embedding)
            face_embedding.save()
            
            logger.info(f"Successfully generated embedding for pet {pet.name} using {successful_images} images")
            return face_embedding
            
        except Exception as e:
            logger.error(f"Error generating pet embeddings: {e}")
            return None


class FaceMatchingService:
    """Service for face matching and similarity comparison"""
    
    @staticmethod
    def find_similar_pets(query_embedding: np.ndarray, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Find similar pets based on face embedding
        
        Args:
            query_embedding: Query face embedding vector
            top_k: Number of top matches to return
            
        Returns:
            List of similar pets with similarity scores
        """
        try:
            # Get all completed face embeddings
            all_embeddings = FaceEmbedding.objects.filter(
                status='completed'
            ).select_related('pet')
            
            similarities = []
            
            for face_embedding in all_embeddings:
                try:
                    stored_embedding = face_embedding.get_embedding_vector()
                    
                    # Calculate cosine similarity
                    similarity = calculate_cosine_similarity(query_embedding, stored_embedding)
                    
                    similarities.append({
                        'pet': face_embedding.pet,
                        'embedding': face_embedding,
                        'similarity': similarity,
                        'confidence_level': FaceRecognitionResult.determine_confidence_level(similarity)
                    })
                    
                except Exception as e:
                    logger.error(f"Error calculating similarity for embedding {face_embedding.id}: {e}")
                    continue
            
            # Sort by similarity score
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            
            return similarities[:top_k]
            
        except Exception as e:
            logger.error(f"Error finding similar pets: {e}")
            return []
    
    @staticmethod
    def create_recognition_result(search_embedding: FaceEmbedding, 
                                  matches: List[Dict[str, Any]], 
                                  result_type: str = 'search',
                                  searcher=None) -> List[FaceRecognitionResult]:
        """
        Create FaceRecognitionResult objects from matches
        
        Args:
            search_embedding: The embedding used for search
            matches: List of match dictionaries
            result_type: Type of recognition result
            searcher: User who performed the search
            
        Returns:
            List of created FaceRecognitionResult objects
        """
        results = []
        
        for rank, match in enumerate(matches, 1):
            try:
                result = FaceRecognitionResult.objects.create(
                    search_embedding=search_embedding,
                    matched_pet=match.get('pet'),
                    matched_embedding=match.get('embedding'),
                    similarity_score=match['similarity'],
                    confidence_level=match['confidence_level'],
                    result_type=result_type,
                    rank=rank,
                    searcher=searcher
                )
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error creating recognition result: {e}")
                continue
        
        return results


def calculate_cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Calculate cosine similarity between two vectors
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        Cosine similarity score (0 to 1)
    """
    try:
        # Normalize vectors
        vec1_norm = vec1 / np.linalg.norm(vec1)
        vec2_norm = vec2 / np.linalg.norm(vec2)
        
        # Calculate cosine similarity
        similarity = np.dot(vec1_norm, vec2_norm)
        
        # Ensure result is between 0 and 1
        similarity = max(0, min(1, similarity))
        
        return float(similarity)
        
    except Exception as e:
        logger.error(f"Error calculating cosine similarity: {e}")
        return 0.0


def process_search_image(image_file: InMemoryUploadedFile) -> Optional[np.ndarray]:
    """
    Process a search image and extract face embedding
    
    Args:
        image_file: Uploaded image file
        
    Returns:
        Face embedding vector or None
    """
    try:
        # Save temporary file
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            for chunk in image_file.chunks():
                temp_file.write(chunk)
            temp_path = temp_file.name
        
        try:
            # Detect faces
            yolo_service = YOLODetectionService()
            detections = yolo_service.detect_pet_faces(temp_path)
            
            # Filter for face detections
            face_detections = [d for d in detections if d['class'].endswith('_face')]
            
            if not face_detections:
                logger.warning("No pet faces detected in search image")
                return None
            
            # Use the highest confidence face detection
            best_detection = face_detections[0]
            
            # Extract face crop
            face_crop = yolo_service.extract_face_crop(temp_path, best_detection['bounding_box'])
            
            if face_crop is None:
                logger.warning("Failed to extract face crop from search image")
                return None
            
            # Generate embedding
            embedding_service = FaceEmbeddingService()
            embedding = embedding_service.generate_embedding(face_crop)
            
            return embedding
            
        finally:
            # Clean up temporary file
            os.unlink(temp_path)
        
    except Exception as e:
        logger.error(f"Error processing search image: {e}")
        return None 