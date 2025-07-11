from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'face_recognition'

# Create router for viewsets
router = DefaultRouter()
router.register(r'embeddings', views.FaceEmbeddingViewSet, basename='embedding')
router.register(r'results', views.FaceRecognitionResultViewSet, basename='result')

urlpatterns = [
    # Face search
    path('search/', views.FaceSearchView.as_view(), name='face_search'),
    
    # Embedding management
    path('embeddings/generate/', views.generate_pet_embeddings, name='generate_embeddings'),
    path('embeddings/status/', views.embedding_status, name='embedding_status'),
    path('embeddings/delete/<uuid:pet_id>/', views.delete_pet_embedding, name='delete_embedding'),
    
    # Search history
    path('history/', views.search_history, name='search_history'),
    
    # ViewSet routes
    path('', include(router.urls)),
] 