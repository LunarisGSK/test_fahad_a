from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid
import secrets
import string

User = get_user_model()


class QRCode(models.Model):
    """Store QR codes for pet searches"""
    QR_STATUS = [
        ('active', 'Active'),
        ('used', 'Used'),
        ('expired', 'Expired'),
        ('disabled', 'Disabled'),
    ]
    
    QR_TYPES = [
        ('pet_search', 'Pet Search'),
        ('clinic_search', 'Clinic Search'),
        ('emergency', 'Emergency'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)  # The actual QR code string
    qr_type = models.CharField(max_length=20, choices=QR_TYPES, default='pet_search')
    status = models.CharField(max_length=20, choices=QR_STATUS, default='active')
    
    # Creator information
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_qr_codes')
    clinic_name = models.CharField(max_length=200, blank=True, null=True)
    veterinarian_name = models.CharField(max_length=100, blank=True, null=True)
    
    # QR code lifecycle
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(blank=True, null=True)
    
    # Usage tracking
    usage_count = models.IntegerField(default=0)
    max_usage = models.IntegerField(default=1)  # How many times this QR can be used
    
    # Location and context
    location = models.TextField(blank=True, null=True)  # Where QR code is displayed
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"QR Code {self.code} - {self.status}"
    
    def is_expired(self):
        """Check if QR code is expired"""
        return timezone.now() > self.expires_at
    
    def is_usable(self):
        """Check if QR code can still be used"""
        return (
            self.status == 'active' and
            not self.is_expired() and
            self.usage_count < self.max_usage
        )
    
    def mark_as_used(self):
        """Mark QR code as used"""
        self.usage_count += 1
        self.used_at = timezone.now()
        
        if self.usage_count >= self.max_usage:
            self.status = 'used'
        
        self.save()
    
    @classmethod
    def generate_unique_code(cls):
        """Generate a unique QR code string"""
        while True:
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(12))
            if not cls.objects.filter(code=code).exists():
                return code


class QRSearchSession(models.Model):
    """Track QR code search sessions"""
    SESSION_STATUS = [
        ('initiated', 'Initiated'),
        ('image_uploaded', 'Image Uploaded'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('expired', 'Expired'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    qr_code = models.ForeignKey(QRCode, on_delete=models.CASCADE, related_name='search_sessions')
    session_token = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=SESSION_STATUS, default='initiated')
    
    # Session metadata
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    expires_at = models.DateTimeField()
    
    # Search details
    searcher_ip = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    device_info = models.JSONField(blank=True, null=True)
    
    # Results
    search_result = models.ForeignKey(
        'face_recognition.FaceRecognitionResult',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='qr_sessions'
    )
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"QR Search Session {self.session_token} - {self.status}"
    
    def is_expired(self):
        """Check if session is expired"""
        return timezone.now() > self.expires_at
    
    @classmethod
    def generate_session_token(cls):
        """Generate a unique session token"""
        while True:
            token = secrets.token_urlsafe(32)
            if not cls.objects.filter(session_token=token).exists():
                return token


class QRSearchImage(models.Model):
    """Store images uploaded during QR search"""
    PROCESSING_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(QRSearchSession, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='qr_search_images/')
    
    # Processing status
    status = models.CharField(max_length=20, choices=PROCESSING_STATUS, default='pending')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    
    # Detection results
    detected_pet_type = models.CharField(max_length=20, blank=True, null=True)
    detection_confidence = models.FloatField(blank=True, null=True)
    face_detected = models.BooleanField(default=False)
    face_bounding_box = models.JSONField(blank=True, null=True)
    
    # Image quality metrics
    quality_score = models.FloatField(blank=True, null=True)
    blur_score = models.FloatField(blank=True, null=True)
    brightness_score = models.FloatField(blank=True, null=True)
    
    # Processing metadata
    processing_time = models.FloatField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"QR Search Image for session {self.session.session_token}"


class ClinicInfo(models.Model):
    """Store information about clinics that use the QR system"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    registration_number = models.CharField(max_length=50, unique=True)  # CRMV or similar
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='clinics')
    
    # Contact information
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=50)
    postal_code = models.CharField(max_length=10)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    website = models.URLField(blank=True, null=True)
    
    # Service details
    specialties = models.JSONField(default=list)  # List of specialties
    services = models.JSONField(default=list)    # List of services offered
    
    # Operational details
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # QR usage statistics
    total_qr_codes_generated = models.IntegerField(default=0)
    total_searches_performed = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.city}"


class SearchAnalytics(models.Model):
    """Store analytics data for searches and QR usage"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField()
    
    # QR Code metrics
    qr_codes_created = models.IntegerField(default=0)
    qr_codes_scanned = models.IntegerField(default=0)
    qr_codes_expired = models.IntegerField(default=0)
    
    # Search metrics
    total_searches = models.IntegerField(default=0)
    successful_matches = models.IntegerField(default=0)
    eagle_trail_matches = models.IntegerField(default=0)
    lobo_trail_matches = models.IntegerField(default=0)
    no_matches = models.IntegerField(default=0)
    
    # Performance metrics
    average_processing_time = models.FloatField(blank=True, null=True)
    average_similarity_score = models.FloatField(blank=True, null=True)
    
    # Pet type breakdown
    cat_searches = models.IntegerField(default=0)
    dog_searches = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['date']
        ordering = ['-date']
    
    def __str__(self):
        return f"Analytics for {self.date}"
    
    @property
    def success_rate(self):
        """Calculate success rate percentage"""
        if self.total_searches == 0:
            return 0
        return (self.successful_matches / self.total_searches) * 100
