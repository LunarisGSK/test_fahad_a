from rest_framework import serializers
from .models import Pet, PetRegistrationSession, PetImage, PetMedicalRecord


class PetSerializer(serializers.ModelSerializer):
    """Serializer for pet information"""
    age_in_months = serializers.ReadOnlyField()
    
    class Meta:
        model = Pet
        fields = [
            'id', 'name', 'pet_type', 'breed', 'gender', 'date_of_birth',
            'weight', 'color', 'microchip_id', 'registration_status',
            'registration_date', 'last_updated', 'is_active', 'notes',
            'age_in_months'
        ]
        read_only_fields = [
            'id', 'registration_status', 'registration_date', 
            'last_updated', 'age_in_months'
        ]
    
    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)


class PetRegistrationSessionSerializer(serializers.ModelSerializer):
    """Serializer for pet registration session"""
    is_expired = serializers.ReadOnlyField()
    
    class Meta:
        model = PetRegistrationSession
        fields = [
            'id', 'session_token', 'status', 'start_time', 'end_time',
            'expected_images_count', 'actual_images_count', 'capture_duration',
            'notes', 'is_expired'
        ]
        read_only_fields = [
            'id', 'session_token', 'start_time', 'end_time',
            'actual_images_count', 'is_expired'
        ]


class PetImageSerializer(serializers.ModelSerializer):
    """Serializer for pet images"""
    class Meta:
        model = PetImage
        fields = [
            'id', 'image', 'image_type', 'quality_status', 'captured_at',
            'sequence_number', 'detected_pet_type', 'detection_confidence',
            'bounding_box', 'blur_score', 'brightness_score', 'contrast_score'
        ]
        read_only_fields = [
            'id', 'captured_at', 'detected_pet_type', 'detection_confidence',
            'bounding_box', 'blur_score', 'brightness_score', 'contrast_score'
        ]


class PetImageUploadSerializer(serializers.Serializer):
    """Serializer for uploading pet images during registration"""
    images = serializers.ListField(
        child=serializers.ImageField(),
        allow_empty=False,
        max_length=20  # Maximum 20 images
    )
    session_token = serializers.CharField(max_length=100)
    
    def validate_session_token(self, value):
        try:
            session = PetRegistrationSession.objects.get(
                session_token=value,
                status='active'
            )
            if session.is_expired():
                raise serializers.ValidationError("Session has expired")
            return value
        except PetRegistrationSession.DoesNotExist:
            raise serializers.ValidationError("Invalid session token")


class PetMedicalRecordSerializer(serializers.ModelSerializer):
    """Serializer for pet medical records"""
    class Meta:
        model = PetMedicalRecord
        fields = [
            'id', 'record_type', 'date', 'veterinarian', 'clinic',
            'description', 'notes', 'cost', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class PetDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for pet with related data"""
    age_in_months = serializers.ReadOnlyField()
    images = PetImageSerializer(many=True, read_only=True)
    medical_records = PetMedicalRecordSerializer(many=True, read_only=True)
    registration_sessions = PetRegistrationSessionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Pet
        fields = [
            'id', 'name', 'pet_type', 'breed', 'gender', 'date_of_birth',
            'weight', 'color', 'microchip_id', 'registration_status',
            'registration_date', 'last_updated', 'is_active', 'notes',
            'age_in_months', 'images', 'medical_records', 'registration_sessions'
        ]
        read_only_fields = [
            'id', 'registration_status', 'registration_date', 
            'last_updated', 'age_in_months'
        ]


class StartFaceIDSerializer(serializers.Serializer):
    """Serializer for starting Face ID registration"""
    pet_id = serializers.UUIDField()
    expected_duration = serializers.IntegerField(default=10)  # seconds
    
    def validate_pet_id(self, value):
        request = self.context['request']
        try:
            pet = Pet.objects.get(id=value, owner=request.user)
            return value
        except Pet.DoesNotExist:
            raise serializers.ValidationError("Pet not found or you don't have permission")


class CompleteFaceIDSerializer(serializers.Serializer):
    """Serializer for completing Face ID registration"""
    session_token = serializers.CharField(max_length=100)
    success = serializers.BooleanField(default=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_session_token(self, value):
        try:
            session = PetRegistrationSession.objects.get(
                session_token=value,
                status='active'
            )
            return value
        except PetRegistrationSession.DoesNotExist:
            raise serializers.ValidationError("Invalid session token") 