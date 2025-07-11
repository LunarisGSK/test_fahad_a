from rest_framework import status, permissions, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.shortcuts import get_object_or_404
import secrets
import logging

from .models import Pet, PetRegistrationSession, PetImage, PetMedicalRecord
from .serializers import (
    PetSerializer, PetDetailSerializer, PetRegistrationSessionSerializer,
    PetImageSerializer, PetImageUploadSerializer, PetMedicalRecordSerializer,
    StartFaceIDSerializer, CompleteFaceIDSerializer
)
from face_recognition.services import YOLODetectionService, FaceEmbeddingService

logger = logging.getLogger(__name__)


class PetViewSet(viewsets.ModelViewSet):
    """ViewSet for pet management"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PetDetailSerializer
        return PetSerializer
    
    def get_queryset(self):
        return Pet.objects.filter(owner=self.request.user).order_by('-registration_date')
    
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
    
    @action(detail=True, methods=['post'])
    def start_face_id(self, request, pk=None):
        """Start Face ID registration for a pet"""
        pet = self.get_object()
        
        # Check if pet already has active session
        active_sessions = PetRegistrationSession.objects.filter(
            pet=pet,
            status='active'
        )
        
        for session in active_sessions:
            if not session.is_expired():
                return Response({
                    'error': 'Pet already has an active Face ID session',
                    'session_token': session.session_token
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                session.status = 'expired'
                session.save()
        
        # Create new session
        session_token = secrets.token_urlsafe(32)
        session = PetRegistrationSession.objects.create(
            pet=pet,
            session_token=session_token,
            expected_images_count=10  # 10 seconds of capture
        )
        
        # Update pet status
        pet.registration_status = 'processing'
        pet.save()
        
        serializer = PetRegistrationSessionSerializer(session)
        
        return Response({
            'message': 'Face ID session started successfully',
            'session': serializer.data,
            'instructions': {
                'duration': '10 seconds',
                'requirements': [
                    'Keep pet calm and facing forward',
                    'Ensure good lighting',
                    'Show entire face with eyes, snout, and ears visible',
                    'Avoid accessories or distractions'
                ]
            }
        })
    
    @action(detail=True, methods=['post'])
    def complete_face_id(self, request, pk=None):
        """Complete Face ID registration for a pet"""
        pet = self.get_object()
        serializer = CompleteFaceIDSerializer(data=request.data)
        
        if serializer.is_valid():
            session_token = serializer.validated_data['session_token']
            success = serializer.validated_data.get('success', True)
            notes = serializer.validated_data.get('notes', '')
            
            try:
                session = PetRegistrationSession.objects.get(
                    session_token=session_token,
                    pet=pet
                )
                
                session.end_time = timezone.now()
                session.capture_duration = session.end_time - session.start_time
                session.notes = notes
                
                if success and session.actual_images_count > 0:
                    session.status = 'completed'
                    pet.registration_status = 'completed'
                    
                    # Trigger embedding generation (async)
                    from face_recognition.tasks import generate_pet_embedding
                    generate_pet_embedding.delay(pet.id, session.id)
                    
                    message = 'Face ID registration completed successfully'
                else:
                    session.status = 'failed'
                    pet.registration_status = 'failed'
                    message = 'Face ID registration failed'
                
                session.save()
                pet.save()
                
                return Response({
                    'message': message,
                    'pet_status': pet.registration_status,
                    'images_captured': session.actual_images_count
                })
                
            except PetRegistrationSession.DoesNotExist:
                return Response({
                    'error': 'Session not found'
                }, status=status.HTTP_404_NOT_FOUND)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def registration_status(self, request, pk=None):
        """Get pet registration status"""
        pet = self.get_object()
        
        # Get latest session
        latest_session = pet.registration_sessions.first()
        
        response_data = {
            'pet_id': pet.id,
            'pet_name': pet.name,
            'registration_status': pet.registration_status,
            'has_embedding': pet.face_embeddings.filter(status='completed').exists(),
            'total_images': pet.images.count(),
            'latest_session': None
        }
        
        if latest_session:
            response_data['latest_session'] = PetRegistrationSessionSerializer(latest_session).data
        
        return Response(response_data)


class PetImageUploadView(APIView):
    """API view for uploading pet images during registration"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = PetImageUploadSerializer(data=request.data)
        
        if serializer.is_valid():
            session_token = serializer.validated_data['session_token']
            images = serializer.validated_data['images']
            
            try:
                session = PetRegistrationSession.objects.get(
                    session_token=session_token,
                    status='active'
                )
                
                if session.is_expired():
                    session.status = 'expired'
                    session.save()
                    return Response({
                        'error': 'Session has expired'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Process each image
                yolo_service = YOLODetectionService()
                processed_images = []
                
                for i, image in enumerate(images):
                    pet_image = PetImage.objects.create(
                        pet=session.pet,
                        session=session,
                        image=image,
                        sequence_number=session.actual_images_count + i + 1
                    )
                    
                    # Process image with YOLO
                    try:
                        detections = yolo_service.detect_pet_faces(pet_image.image.path)
                        quality_metrics = yolo_service.assess_image_quality(pet_image.image.path)
                        
                        if detections:
                            best_detection = detections[0]
                            pet_image.detected_pet_type = best_detection['class']
                            pet_image.detection_confidence = best_detection['confidence']
                            pet_image.bounding_box = best_detection['bounding_box']
                            
                            # Determine quality status
                            if best_detection['confidence'] > 0.7:
                                pet_image.quality_status = 'good'
                            elif best_detection['confidence'] > 0.5:
                                pet_image.quality_status = 'poor'
                            else:
                                pet_image.quality_status = 'rejected'
                        else:
                            pet_image.quality_status = 'rejected'
                        
                        # Set quality metrics
                        pet_image.blur_score = quality_metrics.get('blur_score')
                        pet_image.brightness_score = quality_metrics.get('brightness_score')
                        pet_image.contrast_score = quality_metrics.get('contrast_score')
                        
                        pet_image.save()
                        
                    except Exception as e:
                        logger.error(f"Error processing image {pet_image.id}: {e}")
                        pet_image.quality_status = 'rejected'
                        pet_image.save()
                    
                    processed_images.append(PetImageSerializer(pet_image).data)
                
                # Update session
                session.actual_images_count += len(images)
                session.save()
                
                return Response({
                    'message': f'Successfully uploaded {len(images)} images',
                    'session_token': session_token,
                    'total_images': session.actual_images_count,
                    'processed_images': processed_images
                })
                
            except PetRegistrationSession.DoesNotExist:
                return Response({
                    'error': 'Invalid session token'
                }, status=status.HTTP_404_NOT_FOUND)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PetMedicalRecordViewSet(viewsets.ModelViewSet):
    """ViewSet for pet medical records"""
    serializer_class = PetMedicalRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        pet_id = self.kwargs.get('pet_pk')
        return PetMedicalRecord.objects.filter(
            pet_id=pet_id,
            pet__owner=self.request.user
        ).order_by('-date')
    
    def perform_create(self, serializer):
        pet_id = self.kwargs.get('pet_pk')
        pet = get_object_or_404(Pet, id=pet_id, owner=self.request.user)
        serializer.save(pet=pet)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_pets_summary(request):
    """Get summary of user's pets"""
    user = request.user
    pets = Pet.objects.filter(owner=user)
    
    summary = {
        'total_pets': pets.count(),
        'completed_registrations': pets.filter(registration_status='completed').count(),
        'pending_registrations': pets.filter(registration_status='pending').count(),
        'processing_registrations': pets.filter(registration_status='processing').count(),
        'failed_registrations': pets.filter(registration_status='failed').count(),
        'pets_by_type': {
            'cats': pets.filter(pet_type='cat').count(),
            'dogs': pets.filter(pet_type='dog').count()
        },
        'recent_registrations': PetSerializer(
            pets.order_by('-registration_date')[:5], 
            many=True
        ).data
    }
    
    return Response(summary)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def validate_session_token(request):
    """Validate a Face ID session token"""
    session_token = request.data.get('session_token')
    
    if not session_token:
        return Response({
            'error': 'Session token is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        session = PetRegistrationSession.objects.get(
            session_token=session_token,
            pet__owner=request.user
        )
        
        is_valid = session.status == 'active' and not session.is_expired()
        
        return Response({
            'valid': is_valid,
            'session': PetRegistrationSessionSerializer(session).data if is_valid else None,
            'reason': 'expired' if session.is_expired() else session.status
        })
        
    except PetRegistrationSession.DoesNotExist:
        return Response({
            'valid': False,
            'reason': 'not_found'
        })
