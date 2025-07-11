from django.shortcuts import render
from django.db import models
from rest_framework import status, permissions, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
import time
import numpy as np
import logging

from .models import FaceEmbedding, FaceRecognitionResult, EmbeddingProcessingJob
from .serializers import (
    FaceEmbeddingSerializer, FaceRecognitionResultSerializer, 
    FaceSearchSerializer, FaceSearchResultSerializer,
    EmbeddingProcessingJobSerializer, EmbeddingStatusSerializer
)
from .services import (
    FaceEmbeddingService, FaceMatchingService, process_search_image
)
from pets.models import Pet

logger = logging.getLogger(__name__)


class FaceSearchView(APIView):
    """API view for face-based pet search"""
    permission_classes = [permissions.AllowAny]  # Allow anonymous QR searches
    
    def post(self, request):
        serializer = FaceSearchSerializer(data=request.data)
        
        if serializer.is_valid():
            start_time = time.time()
            image_file = serializer.validated_data['image']
            top_k = serializer.validated_data['top_k']
            
            try:
                # Process the search image and extract embedding
                query_embedding = process_search_image(image_file)
                
                if query_embedding is None:
                    return Response({
                        'error': 'No pet face detected in the uploaded image',
                        'message': 'Please ensure the image contains a clear view of your pet\'s face'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Find similar pets
                matches = FaceMatchingService.find_similar_pets(query_embedding, top_k)
                
                processing_time = time.time() - start_time
                
                # Prepare results
                if matches:
                    best_match = matches[0]
                    search_quality = 'good' if best_match['similarity'] > 0.8 else 'fair'
                else:
                    best_match = None
                    search_quality = 'poor'
                
                # Create temporary embedding for search results
                temp_embedding = FaceEmbedding(
                    pet=None,
                    embedding_model='search_query',
                    vector_dimension=len(query_embedding),
                    status='completed'
                )
                temp_embedding.set_embedding_vector(query_embedding)
                
                # Create recognition results
                results = []
                for match in matches:
                    result = FaceRecognitionResult(
                        search_embedding=temp_embedding,
                        matched_pet=match['pet'],
                        matched_embedding=match['embedding'],
                        similarity_score=match['similarity'],
                        confidence_level=match['confidence_level'],
                        result_type='search',
                        processing_time=processing_time,
                        searcher=request.user if request.user.is_authenticated else None
                    )
                    results.append(result)
                
                response_data = {
                    'results': results,
                    'total_matches': len(matches),
                    'processing_time': processing_time,
                    'search_quality': search_quality,
                    'best_match': results[0] if results else None
                }
                
                serializer = FaceSearchResultSerializer(response_data)
                return Response(serializer.data)
                
            except Exception as e:
                logger.error(f"Error in face search: {e}")
                return Response({
                    'error': 'Error processing search request',
                    'message': 'Please try again with a different image'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FaceEmbeddingViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing face embeddings"""
    serializer_class = FaceEmbeddingSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return FaceEmbedding.objects.filter(
            pet__owner=self.request.user
        ).order_by('-created_at')


class FaceRecognitionResultViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing face recognition results"""
    serializer_class = FaceRecognitionResultSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Show results where user is the searcher or owns the matched pet
        return FaceRecognitionResult.objects.filter(
            models.Q(searcher=self.request.user) | 
            models.Q(matched_pet__owner=self.request.user)
        ).order_by('-search_timestamp')


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def generate_pet_embeddings(request):
    """Generate embeddings for user's pets"""
    pet_ids = request.data.get('pet_ids', [])
    force_regenerate = request.data.get('force_regenerate', False)
    
    if not pet_ids:
        # Generate for all user's pets if none specified
        pets = Pet.objects.filter(
            owner=request.user,
            registration_status='completed'
        )
    else:
        pets = Pet.objects.filter(
            id__in=pet_ids,
            owner=request.user,
            registration_status='completed'
        )
    
    results = []
    embedding_service = FaceEmbeddingService()
    
    for pet in pets:
        try:
            # Check if embedding already exists
            existing_embedding = pet.face_embeddings.filter(status='completed').first()
            
            if existing_embedding and not force_regenerate:
                results.append({
                    'pet_id': pet.id,
                    'pet_name': pet.name,
                    'status': 'already_exists',
                    'embedding_id': existing_embedding.id
                })
                continue
            
            # Get pet images
            pet_images = pet.images.filter(quality_status='good').order_by('sequence_number')
            
            if not pet_images.exists():
                results.append({
                    'pet_id': pet.id,
                    'pet_name': pet.name,
                    'status': 'no_images',
                    'error': 'No suitable images found'
                })
                continue
            
            # Generate embedding
            face_embedding = embedding_service.generate_pet_embeddings(list(pet_images))
            
            if face_embedding:
                results.append({
                    'pet_id': pet.id,
                    'pet_name': pet.name,
                    'status': 'success',
                    'embedding_id': face_embedding.id,
                    'images_used': face_embedding.source_images_count
                })
            else:
                results.append({
                    'pet_id': pet.id,
                    'pet_name': pet.name,
                    'status': 'failed',
                    'error': 'Failed to generate embedding'
                })
        
        except Exception as e:
            logger.error(f"Error generating embedding for pet {pet.id}: {e}")
            results.append({
                'pet_id': pet.id,
                'pet_name': pet.name,
                'status': 'error',
                'error': str(e)
            })
    
    return Response({
        'message': f'Processed {len(pets)} pets',
        'results': results
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def embedding_status(request):
    """Get embedding status for user's pets"""
    pets = Pet.objects.filter(owner=request.user)
    
    statuses = []
    for pet in pets:
        embedding = pet.face_embeddings.filter(status='completed').first()
        
        status_data = {
            'pet_id': pet.id,
            'pet_name': pet.name,
            'has_embedding': embedding is not None,
            'embedding_status': embedding.status if embedding else 'none',
            'embedding_quality': embedding.quality_score if embedding else None,
            'images_count': pet.images.filter(quality_status='good').count(),
            'last_updated': embedding.updated_at if embedding else None
        }
        statuses.append(status_data)
    
    serializer = EmbeddingStatusSerializer(statuses, many=True)
    return Response(serializer.data)


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def delete_pet_embedding(request, pet_id):
    """Delete face embedding for a specific pet"""
    try:
        pet = Pet.objects.get(id=pet_id, owner=request.user)
        embeddings = pet.face_embeddings.all()
        
        if embeddings.exists():
            count = embeddings.count()
            embeddings.delete()
            
            return Response({
                'message': f'Deleted {count} embeddings for {pet.name}'
            })
        else:
            return Response({
                'message': 'No embeddings found for this pet'
            })
    
    except Pet.DoesNotExist:
        return Response({
            'error': 'Pet not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def search_history(request):
    """Get user's search history"""
    results = FaceRecognitionResult.objects.filter(
        searcher=request.user
    ).order_by('-search_timestamp')[:20]
    
    serializer = FaceRecognitionResultSerializer(results, many=True)
    return Response({
        'search_history': serializer.data,
        'total_searches': FaceRecognitionResult.objects.filter(searcher=request.user).count()
    })
