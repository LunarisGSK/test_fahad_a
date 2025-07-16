from django.urls import path
from . import views

app_name = 'simple_face_id'

urlpatterns = [
    # Main API endpoints
    path('register/', views.FaceRegistrationView.as_view(), name='register'),
    path('search/', views.FaceSimilaritySearchView.as_view(), name='search'),
    
    # Utility endpoints
    path('face-image/<path:image_path>', views.FaceImageView.as_view(), name='face-image'),
    path('project/<str:project_id>/', views.ProjectInfoView.as_view(), name='project-info'),
    path('qr-code/<str:project_id>/', views.QRCodeView.as_view(), name='qr-code'),
    path('stats/', views.StatsView.as_view(), name='stats'),
] 