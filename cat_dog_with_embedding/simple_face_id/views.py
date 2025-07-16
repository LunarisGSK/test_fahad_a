from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.http import HttpResponse
from django.conf import settings
import os
import base64
import logging

from .services import SimpleFaceIdService
from .serializers import (
    FaceRegistrationSerializer, 
    FaceRegistrationResponseSerializer,
    FaceSimilaritySearchSerializer,
    FaceSimilaritySearchResponseSerializer
)
from .models import FaceProject, FaceVector, SimilaritySearch

logger = logging.getLogger(__name__)


class FaceRegistrationView(APIView):
    """
    API endpoint for face registration
    
    POST /api/simple-face-id/register/
    
    Request body:
    - name: Name of the person/pet
    - input_id: ID provided by user  
    - images: List of up to 20 images
    
    Response:
    - project_id: Generated project ID
    - qr_code: Base64 encoded QR code
    - processing statistics
    """
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = FaceRegistrationSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'error': 'Invalid input data',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Extract validated data
            name = serializer.validated_data['name']
            input_id = serializer.validated_data['input_id']
            images = serializer.validated_data['images']
            
            # Process face registration
            service = SimpleFaceIdService()
            result = service.process_face_registration(name, input_id, images)
            
            if 'error' in result:
                return Response({
                    'error': result['error'],
                    'project_id': result.get('project_id')
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Return success response
            return Response({
                'success': True,
                'project_id': result['project_id'],
                'qr_code': result['qr_code'],
                'name': result['name'],
                'total_images': result['total_images'],
                'faces_detected': result['faces_detected'],
                'processing_time': result['processing_time'],
                'status': result['status']
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error in face registration: {e}")
            return Response({
                'error': 'Internal server error during face registration',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FaceSimilaritySearchView(APIView):
    """
    API endpoint for face similarity search
    
    POST /api/simple-face-id/search/
    
    Request body:
    - image: Image to search for similar faces
    
    Response:
    - project_id: ID of the most similar project
    - name: Name of the most similar match
    - similarity_score: Similarity score (0.0 to 1.0)
    - face_image_path: Path to the matching face image
    """
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = FaceSimilaritySearchSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'error': 'Invalid input data',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Extract validated data
            search_image = serializer.validated_data['image']
            
            # Perform similarity search
            service = SimpleFaceIdService()
            result = service.find_similar_face(search_image)
            
            if 'error' in result:
                return Response({
                    'error': result['error'],
                    'similarity_score': result['similarity_score'],
                    'processing_time': result.get('processing_time', 0.0)
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Return success response
            return Response({
                'success': True,
                'project_id': result['project_id'],
                'name': result['name'],
                'similarity_score': result['similarity_score'],
                'face_image_path': result['face_image_path'],
                'processing_time': result['processing_time']
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in similarity search: {e}")
            return Response({
                'error': 'Internal server error during similarity search',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FaceImageView(APIView):
    """
    API endpoint to serve cropped face images
    
    GET /api/simple-face-id/face-image/<path:image_path>
    """
    
    permission_classes = [AllowAny]
    
    def get(self, request, image_path):
        try:
            # Construct full path
            full_path = os.path.join(settings.MEDIA_ROOT, image_path)
            
            # Check if file exists and is within MEDIA_ROOT
            if not os.path.exists(full_path) or not full_path.startswith(settings.MEDIA_ROOT):
                return Response({
                    'error': 'Image not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Read and return image
            with open(full_path, 'rb') as f:
                image_data = f.read()
            
            # Determine content type
            content_type = 'image/jpeg'
            if image_path.lower().endswith('.png'):
                content_type = 'image/png'
            
            return HttpResponse(image_data, content_type=content_type)
            
        except Exception as e:
            logger.error(f"Error serving image: {e}")
            return Response({
                'error': 'Error serving image'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProjectInfoView(APIView):
    """
    API endpoint to get project information
    
    GET /api/simple-face-id/project/<str:project_id>/
    """
    
    permission_classes = [AllowAny]
    
    def get(self, request, project_id):
        try:
            project = FaceProject.objects.get(project_id=project_id)
            
            # Get project statistics
            face_vectors = project.face_vectors.all()
            
            return Response({
                'project_id': project.project_id,
                'name': project.name,
                'input_id': project.input_id,
                'created_at': project.created_at,
                'status': project.status,
                'total_images': project.total_images,
                'faces_detected': project.faces_detected,
                'qr_code': project.qr_code,
                'face_vectors_count': face_vectors.count()
            }, status=status.HTTP_200_OK)
            
        except FaceProject.DoesNotExist:
            return Response({
                'error': 'Project not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error getting project info: {e}")
            return Response({
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class QRCodeView(APIView):
    """
    API endpoint to get QR code as image
    
    GET /api/simple-face-id/qr-code/<str:project_id>/
    """
    
    permission_classes = [AllowAny]
    
    def get(self, request, project_id):
        try:
            project = FaceProject.objects.get(project_id=project_id)
            
            if not project.qr_code:
                return Response({
                    'error': 'QR code not available for this project'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Decode base64 QR code
            qr_image_data = base64.b64decode(project.qr_code)
            
            return HttpResponse(qr_image_data, content_type='image/png')
            
        except FaceProject.DoesNotExist:
            return Response({
                'error': 'Project not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error serving QR code: {e}")
            return Response({
                'error': 'Error serving QR code'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StatsView(APIView):
    """
    API endpoint to get system statistics
    
    GET /api/simple-face-id/stats/
    """
    
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            # Get statistics
            total_projects = FaceProject.objects.count()
            completed_projects = FaceProject.objects.filter(status='completed').count()
            total_face_vectors = FaceVector.objects.count()
            total_searches = SimilaritySearch.objects.count()
            
            # Get recent activity
            recent_projects = FaceProject.objects.order_by('-created_at')[:5]
            recent_searches = SimilaritySearch.objects.order_by('-search_timestamp')[:5]
            
            return Response({
                'total_projects': total_projects,
                'completed_projects': completed_projects,
                'total_face_vectors': total_face_vectors,
                'total_searches': total_searches,
                'recent_projects': [
                    {
                        'project_id': p.project_id,
                        'name': p.name,
                        'created_at': p.created_at,
                        'status': p.status,
                        'faces_detected': p.faces_detected
                    }
                    for p in recent_projects
                ],
                'recent_searches': [
                    {
                        'id': str(s.id),
                        'best_match': s.best_match_project.project_id if s.best_match_project else None,
                        'similarity_score': s.similarity_score,
                        'search_timestamp': s.search_timestamp
                    }
                    for s in recent_searches
                ]
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return Response({
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 