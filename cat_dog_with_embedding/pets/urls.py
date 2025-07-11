from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'pets'

# Create router for viewsets
router = DefaultRouter()
router.register(r'', views.PetViewSet, basename='pet')

urlpatterns = [
    # Pet management (CRUD)
    path('', include(router.urls)),
    
    # Face ID registration
    path('images/upload/', views.PetImageUploadView.as_view(), name='upload_images'),
    path('session/validate/', views.validate_session_token, name='validate_session'),
    
    # Pet medical records
    path('<uuid:pet_pk>/medical-records/', views.PetMedicalRecordViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='medical_records'),
    path('<uuid:pet_pk>/medical-records/<uuid:pk>/', views.PetMedicalRecordViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='medical_record_detail'),
    
    # Summary and statistics
    path('summary/', views.user_pets_summary, name='pets_summary'),
] 