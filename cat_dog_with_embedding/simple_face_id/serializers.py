from rest_framework import serializers
from .models import FaceProject, FaceVector, SimilaritySearch


class FaceRegistrationSerializer(serializers.Serializer):
    """Serializer for face registration API"""
    
    name = serializers.CharField(max_length=100, help_text="Name of the person/pet")
    input_id = serializers.CharField(max_length=50, help_text="ID provided by user")
    images = serializers.ListField(
        child=serializers.ImageField(),
        min_length=1,
        max_length=20,
        help_text="Up to 20 images for face registration"
    )
    
    def validate_name(self, value):
        """Validate name contains at least some letters"""
        if not any(c.isalpha() for c in value):
            raise serializers.ValidationError("Name must contain at least one letter")
        return value
    
    def validate_input_id(self, value):
        """Validate input_id contains at least some digits"""
        if not any(c.isdigit() for c in value):
            raise serializers.ValidationError("Input ID must contain at least one digit")
        return value


class FaceRegistrationResponseSerializer(serializers.Serializer):
    """Serializer for face registration response"""
    
    project_id = serializers.CharField()
    qr_code = serializers.CharField(help_text="Base64 encoded QR code image")
    name = serializers.CharField()
    total_images = serializers.IntegerField()
    faces_detected = serializers.IntegerField()
    processing_time = serializers.FloatField()
    status = serializers.CharField()
    error = serializers.CharField(required=False)


class FaceSimilaritySearchSerializer(serializers.Serializer):
    """Serializer for face similarity search API"""
    
    image = serializers.ImageField(help_text="Image to search for similar faces")


class FaceSimilaritySearchResponseSerializer(serializers.Serializer):
    """Serializer for face similarity search response"""
    
    project_id = serializers.CharField(required=False)
    name = serializers.CharField(required=False)
    similarity_score = serializers.FloatField()
    face_image_path = serializers.CharField(required=False)
    processing_time = serializers.FloatField()
    error = serializers.CharField(required=False)


class FaceProjectSerializer(serializers.ModelSerializer):
    """Serializer for FaceProject model"""
    
    class Meta:
        model = FaceProject
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class FaceVectorSerializer(serializers.ModelSerializer):
    """Serializer for FaceVector model"""
    
    class Meta:
        model = FaceVector
        fields = '__all__'
        read_only_fields = ('created_at',)


class SimilaritySearchSerializer(serializers.ModelSerializer):
    """Serializer for SimilaritySearch model"""
    
    class Meta:
        model = SimilaritySearch
        fields = '__all__'
        read_only_fields = ('search_timestamp',) 