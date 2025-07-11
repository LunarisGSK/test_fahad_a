from rest_framework import serializers
from .models import FaceEmbedding, FaceRecognitionResult, FaceDetection, EmbeddingProcessingJob
from pets.serializers import PetSerializer


class FaceEmbeddingSerializer(serializers.ModelSerializer):
    """Serializer for face embeddings"""
    pet = PetSerializer(read_only=True)
    
    class Meta:
        model = FaceEmbedding
        fields = [
            'id', 'pet', 'embedding_model', 'vector_dimension', 'status',
            'quality_score', 'created_at', 'updated_at', 'source_images_count',
            'processing_time', 'confidence_score', 'notes'
        ]
        read_only_fields = [
            'id', 'vector_dimension', 'created_at', 'updated_at',
            'processing_time', 'confidence_score'
        ]


class FaceDetectionSerializer(serializers.ModelSerializer):
    """Serializer for face detections"""
    class Meta:
        model = FaceDetection
        fields = [
            'id', 'detected_class', 'confidence', 'bounding_box',
            'model_version', 'detection_timestamp', 'processing_time',
            'face_area', 'face_quality_score'
        ]
        read_only_fields = [
            'id', 'detection_timestamp', 'processing_time'
        ]


class FaceRecognitionResultSerializer(serializers.ModelSerializer):
    """Serializer for face recognition results"""
    matched_pet = PetSerializer(read_only=True)
    confidence_percentage = serializers.ReadOnlyField(source='get_confidence_percentage')
    
    class Meta:
        model = FaceRecognitionResult
        fields = [
            'id', 'matched_pet', 'similarity_score', 'confidence_level',
            'result_type', 'search_timestamp', 'processing_time',
            'rank', 'is_verified', 'verification_notes', 'confidence_percentage'
        ]
        read_only_fields = [
            'id', 'search_timestamp', 'processing_time', 'rank', 'confidence_percentage'
        ]


class EmbeddingProcessingJobSerializer(serializers.ModelSerializer):
    """Serializer for embedding processing jobs"""
    pet = PetSerializer(read_only=True)
    progress_percentage = serializers.ReadOnlyField(source='get_progress_percentage')
    
    class Meta:
        model = EmbeddingProcessingJob
        fields = [
            'id', 'pet', 'status', 'started_at', 'completed_at',
            'total_images', 'processed_images', 'successful_embeddings',
            'failed_embeddings', 'error_message', 'retry_count',
            'created_at', 'progress_percentage'
        ]
        read_only_fields = [
            'id', 'started_at', 'completed_at', 'created_at', 'progress_percentage'
        ]


class FaceSearchSerializer(serializers.Serializer):
    """Serializer for face search requests"""
    image = serializers.ImageField()
    top_k = serializers.IntegerField(default=10, min_value=1, max_value=50)
    
    def validate_image(self, value):
        """Validate uploaded image"""
        # Check file size (max 10MB)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("Image file too large. Maximum size is 10MB.")
        
        # Check file format
        allowed_formats = ['jpeg', 'jpg', 'png']
        if not any(value.name.lower().endswith(f'.{fmt}') for fmt in allowed_formats):
            raise serializers.ValidationError("Invalid image format. Use JPEG or PNG.")
        
        return value


class FaceSearchResultSerializer(serializers.Serializer):
    """Serializer for face search results"""
    results = FaceRecognitionResultSerializer(many=True, read_only=True)
    total_matches = serializers.IntegerField(read_only=True)
    processing_time = serializers.FloatField(read_only=True)
    search_quality = serializers.CharField(read_only=True)
    best_match = FaceRecognitionResultSerializer(read_only=True)
    
    def to_representation(self, instance):
        """Custom representation for search results"""
        data = super().to_representation(instance)
        
        # Add trail information
        eagle_matches = [r for r in instance['results'] if r.confidence_level == 'eagle_trail']
        lobo_matches = [r for r in instance['results'] if r.confidence_level == 'lobo_trail']
        
        data['trail_summary'] = {
            'eagle_trail_count': len(eagle_matches),
            'lobo_trail_count': len(lobo_matches),
            'no_match_count': instance['total_matches'] - len(eagle_matches) - len(lobo_matches)
        }
        
        return data


class BatchEmbeddingSerializer(serializers.Serializer):
    """Serializer for batch embedding generation"""
    pet_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False,
        max_length=100
    )
    force_regenerate = serializers.BooleanField(default=False)
    
    def validate_pet_ids(self, value):
        """Validate that all pets exist and belong to the user"""
        from pets.models import Pet
        
        request = self.context['request']
        existing_pets = Pet.objects.filter(
            id__in=value,
            owner=request.user
        ).values_list('id', flat=True)
        
        if len(existing_pets) != len(value):
            raise serializers.ValidationError("Some pets not found or you don't have permission")
        
        return value


class EmbeddingStatusSerializer(serializers.Serializer):
    """Serializer for embedding status response"""
    pet_id = serializers.UUIDField(read_only=True)
    pet_name = serializers.CharField(read_only=True)
    has_embedding = serializers.BooleanField(read_only=True)
    embedding_status = serializers.CharField(read_only=True)
    embedding_quality = serializers.FloatField(read_only=True, allow_null=True)
    images_count = serializers.IntegerField(read_only=True)
    last_updated = serializers.DateTimeField(read_only=True, allow_null=True) 