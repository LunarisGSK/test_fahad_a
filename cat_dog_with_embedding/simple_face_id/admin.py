from django.contrib import admin
from django.utils.html import format_html
from .models import FaceProject, FaceVector, SimilaritySearch


@admin.register(FaceProject)
class FaceProjectAdmin(admin.ModelAdmin):
    list_display = ['project_id', 'name', 'input_id', 'status', 'faces_detected', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['project_id', 'name', 'input_id']
    readonly_fields = ['project_id', 'created_at', 'updated_at', 'qr_code_image']
    
    def qr_code_image(self, obj):
        if obj.qr_code:
            return format_html(
                '<img src="data:image/png;base64,{}" style="max-width: 200px; max-height: 200px;"/>',
                obj.qr_code
            )
        return 'No QR code'
    qr_code_image.short_description = 'QR Code'


@admin.register(FaceVector)
class FaceVectorAdmin(admin.ModelAdmin):
    list_display = ['project', 'original_image_name', 'confidence_score', 'vector_dimension', 'created_at']
    list_filter = ['created_at', 'confidence_score']
    search_fields = ['project__project_id', 'project__name', 'original_image_name']
    readonly_fields = ['id', 'created_at', 'embedding_vector', 'vector_dimension']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('project')


@admin.register(SimilaritySearch)
class SimilaritySearchAdmin(admin.ModelAdmin):
    list_display = ['best_match_project', 'similarity_score', 'search_timestamp', 'processing_time']
    list_filter = ['search_timestamp', 'similarity_score']
    search_fields = ['best_match_project__project_id', 'best_match_project__name']
    readonly_fields = ['id', 'search_timestamp']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('best_match_project', 'best_match_vector') 