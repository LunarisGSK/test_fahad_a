from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid
import numpy as np
import json

User = get_user_model()


class FaceEmbedding(models.Model):
    """Store face embeddings for pets"""
    EMBEDDING_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pet = models.ForeignKey('pets.Pet', on_delete=models.CASCADE, related_name='face_embeddings')
    embedding_vector = models.JSONField()  # Store the embedding as JSON array
    embedding_model = models.CharField(max_length=100, default='clip-ViT-B-32')
    vector_dimension = models.IntegerField()
    status = models.CharField(max_length=20, choices=EMBEDDING_STATUS, default='pending')
    quality_score = models.FloatField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    source_images_count = models.IntegerField(default=0)
    
    # Metadata about the embedding creation process
    processing_time = models.FloatField(blank=True, null=True)  # Time in seconds
    confidence_score = models.FloatField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Face Embedding for {self.pet.name} - {self.status}"
    
    def set_embedding_vector(self, vector):
        """Set embedding vector from numpy array"""
        if isinstance(vector, np.ndarray):
            self.embedding_vector = vector.tolist()
            self.vector_dimension = len(vector)
        else:
            self.embedding_vector = vector
            self.vector_dimension = len(vector)
    
    def get_embedding_vector(self):
        """Get embedding vector as numpy array"""
        return np.array(self.embedding_vector)
    
    def calculate_similarity(self, other_embedding):
        """Calculate cosine similarity with another embedding"""
        if isinstance(other_embedding, FaceEmbedding):
            other_vector = other_embedding.get_embedding_vector()
        else:
            other_vector = np.array(other_embedding)
        
        this_vector = self.get_embedding_vector()
        
        # Cosine similarity
        dot_product = np.dot(this_vector, other_vector)
        magnitude1 = np.linalg.norm(this_vector)
        magnitude2 = np.linalg.norm(other_vector)
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0
        
        return dot_product / (magnitude1 * magnitude2)


class FaceRecognitionResult(models.Model):
    """Store results of face recognition searches"""
    RESULT_TYPES = [
        ('registration', 'Registration'),
        ('verification', 'Verification'),
        ('search', 'Search'),
    ]
    
    CONFIDENCE_LEVELS = [
        ('eagle_trail', 'Eagle Trail'),  # > 90%
        ('lobo_trail', 'Lobo Trail'),    # 80-90%
        ('no_match', 'No Match'),        # < 80%
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    search_embedding = models.ForeignKey(FaceEmbedding, on_delete=models.CASCADE, related_name='search_results')
    matched_pet = models.ForeignKey('pets.Pet', on_delete=models.CASCADE, related_name='recognition_results', blank=True, null=True)
    matched_embedding = models.ForeignKey(FaceEmbedding, on_delete=models.CASCADE, related_name='matched_results', blank=True, null=True)
    
    similarity_score = models.FloatField()
    confidence_level = models.CharField(max_length=20, choices=CONFIDENCE_LEVELS)
    result_type = models.CharField(max_length=20, choices=RESULT_TYPES, default='search')
    
    # Search metadata
    search_timestamp = models.DateTimeField(auto_now_add=True)
    processing_time = models.FloatField(blank=True, null=True)  # Time in seconds
    searcher = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    
    # Additional match information
    rank = models.IntegerField(default=1)  # Ranking in search results
    is_verified = models.BooleanField(default=False)
    verification_notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-search_timestamp', 'rank']
    
    def __str__(self):
        pet_name = self.matched_pet.name if self.matched_pet else "No Match"
        return f"Recognition Result: {pet_name} - {self.confidence_level} ({self.similarity_score:.2%})"
    
    def get_confidence_percentage(self):
        """Get similarity score as percentage"""
        return self.similarity_score * 100
    
    @classmethod
    def determine_confidence_level(cls, similarity_score):
        """Determine confidence level based on similarity score"""
        if similarity_score >= 0.90:
            return 'eagle_trail'
        elif similarity_score >= 0.80:
            return 'lobo_trail'
        else:
            return 'no_match'


class FaceDetection(models.Model):
    """Store face detection results from YOLO model"""
    DETECTION_CLASSES = [
        ('cat_face', 'Cat Face'),
        ('dog_face', 'Dog Face'),
        ('cat', 'Cat'),
        ('dog', 'Dog'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    image = models.ForeignKey('pets.PetImage', on_delete=models.CASCADE, related_name='detections')
    detected_class = models.CharField(max_length=20, choices=DETECTION_CLASSES)
    confidence = models.FloatField()
    bounding_box = models.JSONField()  # [x1, y1, x2, y2] coordinates
    
    # Detection metadata
    model_version = models.CharField(max_length=50, default='yolov8l')
    detection_timestamp = models.DateTimeField(auto_now_add=True)
    processing_time = models.FloatField(blank=True, null=True)
    
    # Face-specific data (when detected_class is *_face)
    face_area = models.FloatField(blank=True, null=True)  # Area of the face in pixels
    face_quality_score = models.FloatField(blank=True, null=True)
    
    class Meta:
        ordering = ['-confidence']
    
    def __str__(self):
        return f"{self.detected_class} detection - {self.confidence:.2%}"
    
    def get_bounding_box_area(self):
        """Calculate area of bounding box"""
        x1, y1, x2, y2 = self.bounding_box
        return (x2 - x1) * (y2 - y1)
    
    def is_face_detection(self):
        """Check if this detection is for a face"""
        return self.detected_class.endswith('_face')


class EmbeddingProcessingJob(models.Model):
    """Track background jobs for embedding processing"""
    JOB_STATUS = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pet = models.ForeignKey('pets.Pet', on_delete=models.CASCADE, related_name='embedding_jobs')
    session = models.ForeignKey('pets.PetRegistrationSession', on_delete=models.CASCADE, related_name='embedding_jobs')
    
    status = models.CharField(max_length=20, choices=JOB_STATUS, default='pending')
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    # Job details
    total_images = models.IntegerField(default=0)
    processed_images = models.IntegerField(default=0)
    successful_embeddings = models.IntegerField(default=0)
    failed_embeddings = models.IntegerField(default=0)
    
    # Error tracking
    error_message = models.TextField(blank=True, null=True)
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Embedding Job for {self.pet.name} - {self.status}"
    
    def get_progress_percentage(self):
        """Get job progress as percentage"""
        if self.total_images == 0:
            return 0
        return (self.processed_images / self.total_images) * 100
