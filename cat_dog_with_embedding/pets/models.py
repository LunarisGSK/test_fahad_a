from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()


class Pet(models.Model):
    """Main Pet model for storing pet information"""
    PET_TYPES = [
        ('cat', 'Cat'),
        ('dog', 'Dog'),
    ]
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    
    REGISTRATION_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pets')
    name = models.CharField(max_length=100)
    pet_type = models.CharField(max_length=10, choices=PET_TYPES)
    breed = models.CharField(max_length=100, blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    date_of_birth = models.DateField(blank=True, null=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    color = models.CharField(max_length=50, blank=True, null=True)
    microchip_id = models.CharField(max_length=50, blank=True, null=True, unique=True)
    registration_status = models.CharField(max_length=20, choices=REGISTRATION_STATUS, default='pending')
    registration_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-registration_date']
    
    def __str__(self):
        return f"{self.name} ({self.pet_type}) - {self.owner.username}"
    
    @property
    def age_in_months(self):
        if self.date_of_birth:
            today = timezone.now().date()
            return (today.year - self.date_of_birth.year) * 12 + today.month - self.date_of_birth.month
        return None


class PetRegistrationSession(models.Model):
    """Track pet registration sessions and image capture process"""
    SESSION_STATUS = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('expired', 'Expired'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='registration_sessions')
    session_token = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=SESSION_STATUS, default='active')
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(blank=True, null=True)
    expected_images_count = models.IntegerField(default=10)  # 10 seconds of capture
    actual_images_count = models.IntegerField(default=0)
    capture_duration = models.DurationField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-start_time']
    
    def __str__(self):
        return f"Session {self.session_token} for {self.pet.name}"
    
    def is_expired(self):
        """Check if session is expired (after 30 minutes)"""
        if self.status == 'active':
            expiry_time = self.start_time + timezone.timedelta(minutes=30)
            return timezone.now() > expiry_time
        return False


class PetImage(models.Model):
    """Store images captured during pet registration"""
    IMAGE_TYPES = [
        ('registration', 'Registration'),
        ('verification', 'Verification'),
        ('profile', 'Profile'),
    ]
    
    QUALITY_STATUS = [
        ('pending', 'Pending'),
        ('good', 'Good'),
        ('poor', 'Poor'),
        ('rejected', 'Rejected'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='images')
    session = models.ForeignKey(PetRegistrationSession, on_delete=models.CASCADE, related_name='images', blank=True, null=True)
    image = models.ImageField(upload_to='pet_images/')
    image_type = models.CharField(max_length=20, choices=IMAGE_TYPES, default='registration')
    quality_status = models.CharField(max_length=20, choices=QUALITY_STATUS, default='pending')
    captured_at = models.DateTimeField(auto_now_add=True)
    sequence_number = models.IntegerField(default=0)  # Order in the capture sequence
    
    # Detection results from YOLO
    detected_pet_type = models.CharField(max_length=20, blank=True, null=True)
    detection_confidence = models.FloatField(blank=True, null=True)
    bounding_box = models.JSONField(blank=True, null=True)  # Store detection coordinates
    
    # Image quality metrics
    blur_score = models.FloatField(blank=True, null=True)
    brightness_score = models.FloatField(blank=True, null=True)
    contrast_score = models.FloatField(blank=True, null=True)
    
    class Meta:
        ordering = ['sequence_number', 'captured_at']
    
    def __str__(self):
        return f"Image {self.sequence_number} for {self.pet.name}"


class PetMedicalRecord(models.Model):
    """Store medical records and veterinary information"""
    RECORD_TYPES = [
        ('vaccination', 'Vaccination'),
        ('checkup', 'Checkup'),
        ('treatment', 'Treatment'),
        ('surgery', 'Surgery'),
        ('medication', 'Medication'),
    ]
    
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='medical_records')
    record_type = models.CharField(max_length=20, choices=RECORD_TYPES)
    date = models.DateField()
    veterinarian = models.CharField(max_length=100, blank=True, null=True)
    clinic = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField()
    notes = models.TextField(blank=True, null=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.record_type} for {self.pet.name} on {self.date}"
