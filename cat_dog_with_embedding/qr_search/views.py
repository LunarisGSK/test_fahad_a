from rest_framework import status, permissions, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from datetime import timedelta
import qrcode
from io import BytesIO
import base64
import time
import logging

from .models import QRCode, QRSearchSession, QRSearchImage, ClinicInfo
from .serializers import (
    QRCodeSerializer, CreateQRCodeSerializer, QRSearchSessionSerializer,
    QRSearchImageSerializer, ScanQRCodeSerializer, QRSearchRequestSerializer,
    QRSearchResultSerializer, ClinicInfoSerializer
)
from face_recognition.services import process_search_image, FaceMatchingService
from face_recognition.models import FaceEmbedding, FaceRecognitionResult

logger = logging.getLogger(__name__)


class QRCodeManagementView(APIView):
    """API view for QR code management"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get user's QR codes"""
        qr_codes = QRCode.objects.filter(
            created_by=request.user
        ).order_by('-created_at')
        
        serializer = QRCodeSerializer(qr_codes, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        """Create a new QR code"""
        serializer = CreateQRCodeSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            qr_code = serializer.save()
            
            # Generate QR code image
            qr_image = self.generate_qr_image(qr_code.code)
            
            response_data = QRCodeSerializer(qr_code).data
            response_data['qr_image'] = qr_image
            response_data['scan_url'] = f"https://petnologia.com.br/qr-scan/{qr_code.code}"
            
            return Response({
                'message': 'QR code created successfully',
                'qr_code': response_data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def generate_qr_image(self, qr_code_text):
        """Generate QR code image as base64"""
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            
            # Create URL for QR scanning
            scan_url = f"https://petnologia.com.br/qr-scan/{qr_code_text}"
            qr.add_data(scan_url)
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_base64}"
            
        except Exception as e:
            logger.error(f"Error generating QR image: {e}")
            return None


class QRScanView(APIView):
    """API view for QR code scanning"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Scan QR code and initiate search session"""
        serializer = ScanQRCodeSerializer(data=request.data)
        
        if serializer.is_valid():
            qr_code_text = serializer.validated_data['qr_code']
            device_info = serializer.validated_data.get('device_info', {})
            
            try:
                qr_code = QRCode.objects.get(code=qr_code_text)
                
                if not qr_code.is_usable():
                    error_msg = "QR code has expired" if qr_code.is_expired() else "QR code is not active"
                    return Response({
                        'error': error_msg
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Create search session
                session_token = QRSearchSession.generate_session_token()
                expires_at = timezone.now() + timedelta(minutes=30)
                
                session = QRSearchSession.objects.create(
                    qr_code=qr_code,
                    session_token=session_token,
                    expires_at=expires_at,
                    searcher_ip=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT'),
                    device_info=device_info
                )
                
                response_data = QRSearchSessionSerializer(session).data
                response_data['instructions'] = {
                    'step': 1,
                    'message': 'QR code scanned successfully. Please upload a photo of the pet.',
                    'requirements': [
                        'Take a clear photo of the pet\'s face',
                        'Ensure good lighting',
                        'Keep the pet calm and facing the camera',
                        'Show eyes, snout, and ears clearly'
                    ]
                }
                
                return Response({
                    'message': 'QR code scanned successfully',
                    'session': response_data
                })
                
            except QRCode.DoesNotExist:
                return Response({
                    'error': 'Invalid QR code'
                }, status=status.HTTP_404_NOT_FOUND)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class QRSearchView(APIView):
    """API view for QR-based pet search"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Upload image and perform pet search"""
        serializer = QRSearchRequestSerializer(data=request.data)
        
        if serializer.is_valid():
            session_token = serializer.validated_data['session_token']
            image_file = serializer.validated_data['image']
            
            try:
                session = QRSearchSession.objects.get(session_token=session_token)
                
                if session.is_expired():
                    session.status = 'expired'
                    session.save()
                    return Response({
                        'error': 'Search session has expired'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Update session status
                session.status = 'processing'
                session.save()
                
                start_time = time.time()
                
                # Create search image record
                search_image = QRSearchImage.objects.create(
                    session=session,
                    image=image_file
                )
                
                try:
                    # Process the search image
                    query_embedding = process_search_image(image_file)
                    
                    if query_embedding is None:
                        search_image.status = 'failed'
                        search_image.error_message = 'No pet face detected'
                        search_image.save()
                        
                        session.status = 'failed'
                        session.save()
                        
                        return Response({
                            'error': 'No pet face detected in the uploaded image',
                            'message': 'Please upload a clearer image showing the pet\'s face',
                            'session_id': session.id
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    # Find similar pets
                    matches = FaceMatchingService.find_similar_pets(query_embedding, top_k=5)
                    processing_time = time.time() - start_time
                    
                    # Update search image
                    search_image.status = 'completed'
                    search_image.face_detected = True
                    search_image.processing_time = processing_time
                    search_image.save()
                    
                    # Create recognition result if match found
                    search_result = None
                    if matches:
                        best_match = matches[0]
                        
                        # Create temporary embedding for the search
                        temp_embedding = FaceEmbedding(
                            pet=None,
                            embedding_model='qr_search',
                            vector_dimension=len(query_embedding),
                            status='completed'
                        )
                        temp_embedding.set_embedding_vector(query_embedding)
                        
                        # Create recognition result
                        search_result = FaceRecognitionResult.objects.create(
                            search_embedding=temp_embedding,
                            matched_pet=best_match['pet'],
                            matched_embedding=best_match['embedding'],
                            similarity_score=best_match['similarity'],
                            confidence_level=best_match['confidence_level'],
                            result_type='search',
                            processing_time=processing_time
                        )
                        
                        # Link to session
                        session.search_result = search_result
                    
                    # Mark QR code as used
                    session.qr_code.mark_as_used()
                    
                    # Complete session
                    session.status = 'completed'
                    session.completed_at = timezone.now()
                    session.save()
                    
                    # Prepare response
                    response_data = {
                        'session_id': session.id,
                        'processing_time': processing_time,
                        'face_detected': True,
                        'search_result': search_result,
                        'image_quality': 'good' if matches else 'fair'
                    }
                    
                    if search_result:
                        response_data.update({
                            'confidence_level': search_result.confidence_level,
                            'similarity_percentage': search_result.similarity_score * 100,
                            'pet_type_detected': best_match['pet'].pet_type
                        })
                    
                    serializer = QRSearchResultSerializer(response_data)
                    return Response(serializer.data)
                    
                except Exception as e:
                    logger.error(f"Error in QR search processing: {e}")
                    
                    search_image.status = 'failed'
                    search_image.error_message = str(e)
                    search_image.save()
                    
                    session.status = 'failed'
                    session.save()
                    
                    return Response({
                        'error': 'Error processing search request',
                        'session_id': session.id
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
            except QRSearchSession.DoesNotExist:
                return Response({
                    'error': 'Invalid session token'
                }, status=status.HTTP_404_NOT_FOUND)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ClinicInfoViewSet(viewsets.ModelViewSet):
    """ViewSet for clinic information management"""
    serializer_class = ClinicInfoSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return ClinicInfo.objects.filter(owner=self.request.user)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def qr_usage_stats(request):
    """Get QR code usage statistics"""
    user = request.user
    
    # Get user's QR codes
    qr_codes = QRCode.objects.filter(created_by=user)
    
    stats = {
        'total_codes_created': qr_codes.count(),
        'active_codes': qr_codes.filter(status='active').count(),
        'expired_codes': qr_codes.filter(status='expired').count(),
        'total_scans': sum(qr.usage_count for qr in qr_codes),
        'successful_searches': QRSearchSession.objects.filter(
            qr_code__created_by=user,
            status='completed',
            search_result__isnull=False
        ).count(),
        'recent_activity': []
    }
    
    # Get recent search sessions
    recent_sessions = QRSearchSession.objects.filter(
        qr_code__created_by=user
    ).order_by('-created_at')[:10]
    
    for session in recent_sessions:
        activity = {
            'date': session.created_at,
            'status': session.status,
            'qr_code': session.qr_code.code,
            'has_result': session.search_result is not None
        }
        
        if session.search_result:
            activity.update({
                'confidence_level': session.search_result.confidence_level,
                'similarity': session.search_result.similarity_score
            })
        
        stats['recent_activity'].append(activity)
    
    return Response(stats)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def qr_session_status(request, session_token):
    """Get QR search session status"""
    try:
        session = QRSearchSession.objects.get(session_token=session_token)
        serializer = QRSearchSessionSerializer(session)
        
        response_data = serializer.data
        response_data['is_expired'] = session.is_expired()
        
        return Response(response_data)
        
    except QRSearchSession.DoesNotExist:
        return Response({
            'error': 'Session not found'
        }, status=status.HTTP_404_NOT_FOUND)
