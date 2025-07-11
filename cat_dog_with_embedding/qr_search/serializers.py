from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
from .models import QRCode, QRSearchSession, QRSearchImage, ClinicInfo, SearchAnalytics
from face_recognition.serializers import FaceRecognitionResultSerializer


class QRCodeSerializer(serializers.ModelSerializer):
    """Serializer for QR codes"""
    is_expired = serializers.ReadOnlyField()
    is_usable = serializers.ReadOnlyField()
    
    class Meta:
        model = QRCode
        fields = [
            'id', 'code', 'qr_type', 'status', 'clinic_name',
            'veterinarian_name', 'created_at', 'expires_at', 'used_at',
            'usage_count', 'max_usage', 'location', 'notes',
            'is_expired', 'is_usable'
        ]
        read_only_fields = [
            'id', 'code', 'created_at', 'used_at', 'usage_count',
            'is_expired', 'is_usable'
        ]


class CreateQRCodeSerializer(serializers.Serializer):
    """Serializer for creating QR codes"""
    qr_type = serializers.ChoiceField(choices=QRCode.QR_TYPES, default='pet_search')
    clinic_name = serializers.CharField(max_length=200, required=False)
    veterinarian_name = serializers.CharField(max_length=100, required=False)
    location = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    max_usage = serializers.IntegerField(default=1, min_value=1, max_value=100)
    expire_hours = serializers.IntegerField(default=24, min_value=1, max_value=168)  # Max 1 week
    
    def create(self, validated_data):
        # Calculate expiration time
        expire_hours = validated_data.pop('expire_hours')
        expires_at = timezone.now() + timedelta(hours=expire_hours)
        
        # Generate unique code
        code = QRCode.generate_unique_code()
        
        # Create QR code
        qr_code = QRCode.objects.create(
            code=code,
            expires_at=expires_at,
            created_by=self.context['request'].user,
            **validated_data
        )
        
        return qr_code


class QRSearchSessionSerializer(serializers.ModelSerializer):
    """Serializer for QR search sessions"""
    is_expired = serializers.ReadOnlyField()
    qr_code = QRCodeSerializer(read_only=True)
    
    class Meta:
        model = QRSearchSession
        fields = [
            'id', 'qr_code', 'session_token', 'status', 'created_at',
            'started_at', 'completed_at', 'expires_at', 'searcher_ip',
            'device_info', 'is_expired'
        ]
        read_only_fields = [
            'id', 'session_token', 'created_at', 'started_at',
            'completed_at', 'searcher_ip', 'is_expired'
        ]


class QRSearchImageSerializer(serializers.ModelSerializer):
    """Serializer for QR search images"""
    class Meta:
        model = QRSearchImage
        fields = [
            'id', 'image', 'status', 'uploaded_at', 'processed_at',
            'detected_pet_type', 'detection_confidence', 'face_detected',
            'face_bounding_box', 'quality_score', 'blur_score',
            'brightness_score', 'processing_time', 'error_message'
        ]
        read_only_fields = [
            'id', 'uploaded_at', 'processed_at', 'detected_pet_type',
            'detection_confidence', 'face_detected', 'face_bounding_box',
            'quality_score', 'blur_score', 'brightness_score',
            'processing_time', 'error_message'
        ]


class ClinicInfoSerializer(serializers.ModelSerializer):
    """Serializer for clinic information"""
    class Meta:
        model = ClinicInfo
        fields = [
            'id', 'name', 'registration_number', 'address', 'city',
            'state', 'postal_code', 'phone', 'email', 'website',
            'specialties', 'services', 'is_active', 'is_verified',
            'created_at', 'total_qr_codes_generated', 'total_searches_performed'
        ]
        read_only_fields = [
            'id', 'created_at', 'total_qr_codes_generated', 'total_searches_performed'
        ]
    
    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)


class SearchAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for search analytics"""
    success_rate = serializers.ReadOnlyField()
    
    class Meta:
        model = SearchAnalytics
        fields = [
            'id', 'date', 'qr_codes_created', 'qr_codes_scanned',
            'qr_codes_expired', 'total_searches', 'successful_matches',
            'eagle_trail_matches', 'lobo_trail_matches', 'no_matches',
            'average_processing_time', 'average_similarity_score',
            'cat_searches', 'dog_searches', 'success_rate'
        ]
        read_only_fields = ['id', 'success_rate']


class ScanQRCodeSerializer(serializers.Serializer):
    """Serializer for QR code scanning"""
    qr_code = serializers.CharField(max_length=50)
    device_info = serializers.JSONField(required=False)
    
    def validate_qr_code(self, value):
        try:
            qr_code = QRCode.objects.get(code=value)
            
            if not qr_code.is_usable():
                if qr_code.is_expired():
                    raise serializers.ValidationError("QR code has expired")
                elif qr_code.status != 'active':
                    raise serializers.ValidationError("QR code is not active")
                else:
                    raise serializers.ValidationError("QR code has reached maximum usage")
            
            return value
        except QRCode.DoesNotExist:
            raise serializers.ValidationError("Invalid QR code")


class QRSearchRequestSerializer(serializers.Serializer):
    """Serializer for QR search image upload"""
    session_token = serializers.CharField(max_length=100)
    image = serializers.ImageField()
    
    def validate_session_token(self, value):
        try:
            session = QRSearchSession.objects.get(
                session_token=value,
                status__in=['initiated', 'image_uploaded']
            )
            
            if session.is_expired():
                raise serializers.ValidationError("Search session has expired")
            
            return value
        except QRSearchSession.DoesNotExist:
            raise serializers.ValidationError("Invalid session token")
    
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


class QRSearchResultSerializer(serializers.Serializer):
    """Serializer for QR search results"""
    session_id = serializers.UUIDField(read_only=True)
    search_result = FaceRecognitionResultSerializer(read_only=True)
    processing_time = serializers.FloatField(read_only=True)
    image_quality = serializers.CharField(read_only=True)
    face_detected = serializers.BooleanField(read_only=True)
    pet_type_detected = serializers.CharField(read_only=True)
    
    # Trail-specific information
    confidence_level = serializers.CharField(read_only=True)
    similarity_percentage = serializers.FloatField(read_only=True)
    trail_icon = serializers.CharField(read_only=True)
    trail_message = serializers.CharField(read_only=True)
    
    def to_representation(self, instance):
        """Custom representation with trail-specific formatting"""
        data = super().to_representation(instance)
        
        # Add trail-specific information
        if instance.get('search_result'):
            result = instance['search_result']
            confidence_level = result.confidence_level
            similarity = result.similarity_score
            
            # Trail icons and messages
            trail_info = {
                'eagle_trail': {
                    'icon': '🦅',
                    'message': 'Eagle Trail: Nível muito alto de confiabilidade. ' +
                              'O pet consultado pela rede credenciada possui semelhanças ' +
                              f'biométricas faciais acima de 90% ({similarity*100:.1f}%).'
                },
                'lobo_trail': {
                    'icon': '🐺', 
                    'message': 'Lobo Trail: Nível alto de confiabilidade. ' +
                              'O pet consultado pela rede credenciada possui semelhanças ' +
                              f'biométricas faciais entre 80% e 90% ({similarity*100:.1f}%).'
                },
                'no_match': {
                    'icon': '❌',
                    'message': 'Nenhuma correspondência encontrada. ' +
                              f'Similaridade muito baixa ({similarity*100:.1f}%).'
                }
            }
            
            trail = trail_info.get(confidence_level, trail_info['no_match'])
            data.update({
                'trail_icon': trail['icon'],
                'trail_message': trail['message'],
                'similarity_percentage': similarity * 100
            })
        
        return data


class QRCodeUsageStatsSerializer(serializers.Serializer):
    """Serializer for QR code usage statistics"""
    total_codes_created = serializers.IntegerField(read_only=True)
    active_codes = serializers.IntegerField(read_only=True)
    expired_codes = serializers.IntegerField(read_only=True)
    total_scans = serializers.IntegerField(read_only=True)
    successful_searches = serializers.IntegerField(read_only=True)
    eagle_trail_results = serializers.IntegerField(read_only=True)
    lobo_trail_results = serializers.IntegerField(read_only=True)
    average_processing_time = serializers.FloatField(read_only=True)
    most_active_clinic = serializers.CharField(read_only=True)
    recent_activity = serializers.ListField(read_only=True) 