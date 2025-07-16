from django.db import models
import uuid
import json
from django.utils import timezone


class FaceProject(models.Model):
    """Simple model to store face recognition projects"""
    
    # Project ID will be generated as: first 6 digits of input_id + first 3 letters of name
    project_id = models.CharField(max_length=20, unique=True, primary_key=True)
    
    # Original inputs
    name = models.CharField(max_length=100)
    input_id = models.CharField(max_length=50)  # The ID provided by user
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Processing status
    status = models.CharField(max_length=20, choices=[
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ], default='processing')
    
    # Statistics
    total_images = models.IntegerField(default=0)
    faces_detected = models.IntegerField(default=0)
    
    # QR code (base64 encoded)
    qr_code = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Project {self.project_id} - {self.name}"


class FaceVector(models.Model):
    """Store face embeddings for similarity search"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(FaceProject, on_delete=models.CASCADE, related_name='face_vectors')
    
    # Face embedding vector (stored as JSON array)
    embedding_vector = models.JSONField()
    vector_dimension = models.IntegerField()
    
    # Face image info
    original_image_name = models.CharField(max_length=255)
    face_crop_path = models.CharField(max_length=500)  # Path to cropped face image
    
    # Detection metadata
    confidence_score = models.FloatField()
    bounding_box = models.JSONField()  # [x1, y1, x2, y2]
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Face vector for {self.project.name}"
    
    def set_embedding_vector(self, vector):
        """Set embedding vector from numpy array or list"""
        if hasattr(vector, 'tolist'):  # numpy array
            self.embedding_vector = vector.tolist()
            self.vector_dimension = len(vector)
        else:  # list
            self.embedding_vector = vector
            self.vector_dimension = len(vector)


class SimilaritySearch(models.Model):
    """Log similarity search results"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Search image info
    search_image_name = models.CharField(max_length=255, blank=True, null=True)
    
    # Best match
    best_match_project = models.ForeignKey(FaceProject, on_delete=models.CASCADE, null=True, blank=True)
    best_match_vector = models.ForeignKey(FaceVector, on_delete=models.CASCADE, null=True, blank=True)
    similarity_score = models.FloatField(null=True, blank=True)
    
    # Search metadata
    search_timestamp = models.DateTimeField(auto_now_add=True)
    processing_time = models.FloatField(null=True, blank=True)  # seconds
    
    def __str__(self):
        if self.best_match_project:
            return f"Search result: {self.best_match_project.name} (score: {self.similarity_score:.3f})"
        return f"Search result: No match found" 