from django.contrib import admin
from .models import Pet, PetRegistrationSession, PetImage, PetMedicalRecord


@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    """Admin configuration for Pet"""
    list_display = ['name', 'pet_type', 'owner', 'registration_status', 'registration_date']
    list_filter = ['pet_type', 'registration_status', 'gender', 'registration_date']
    search_fields = ['name', 'owner__username', 'owner__email', 'breed', 'microchip_id']
    raw_id_fields = ['owner']
    readonly_fields = ['id', 'registration_date', 'last_updated', 'age_in_months']
    ordering = ['-registration_date']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'pet_type', 'breed', 'gender', 'owner')
        }),
        ('Physical Details', {
            'fields': ('date_of_birth', 'weight', 'color')
        }),
        ('Registration', {
            'fields': ('microchip_id', 'registration_status', 'registration_date', 'last_updated')
        }),
        ('Additional', {
            'fields': ('notes', 'is_active')
        })
    )


@admin.register(PetRegistrationSession)
class PetRegistrationSessionAdmin(admin.ModelAdmin):
    """Admin configuration for PetRegistrationSession"""
    list_display = ['session_token', 'pet', 'status', 'start_time', 'actual_images_count']
    list_filter = ['status', 'start_time']
    search_fields = ['session_token', 'pet__name', 'pet__owner__username']
    raw_id_fields = ['pet']
    readonly_fields = ['session_token', 'start_time', 'capture_duration']
    ordering = ['-start_time']


@admin.register(PetImage)
class PetImageAdmin(admin.ModelAdmin):
    """Admin configuration for PetImage"""
    list_display = ['pet', 'image_type', 'quality_status', 'captured_at', 'sequence_number']
    list_filter = ['image_type', 'quality_status', 'captured_at']
    search_fields = ['pet__name', 'pet__owner__username']
    raw_id_fields = ['pet', 'session']
    readonly_fields = ['captured_at', 'detected_pet_type', 'detection_confidence', 'bounding_box']
    ordering = ['-captured_at']


@admin.register(PetMedicalRecord)
class PetMedicalRecordAdmin(admin.ModelAdmin):
    """Admin configuration for PetMedicalRecord"""
    list_display = ['pet', 'record_type', 'date', 'veterinarian', 'clinic']
    list_filter = ['record_type', 'date']
    search_fields = ['pet__name', 'veterinarian', 'clinic', 'description']
    raw_id_fields = ['pet']
    ordering = ['-date']
