from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'qr_search'

# Create router for viewsets
router = DefaultRouter()
router.register(r'clinics', views.ClinicInfoViewSet, basename='clinic')

urlpatterns = [
    # QR Code management
    path('codes/', views.QRCodeManagementView.as_view(), name='qr_codes'),
    path('codes/stats/', views.qr_usage_stats, name='qr_stats'),
    
    # QR scanning and search
    path('scan/', views.QRScanView.as_view(), name='qr_scan'),
    path('search/', views.QRSearchView.as_view(), name='qr_search'),
    path('session/<str:session_token>/', views.qr_session_status, name='session_status'),
    
    # Clinic management
    path('', include(router.urls)),
] 