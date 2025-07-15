from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import uuid
import os
import mimetypes
from PIL import Image
import io


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_image(request):
    """
    이미지 업로드 API
    
    Tiptap 에디터에서 이미지를 업로드할 때 사용됩니다.
    """
    if 'image' not in request.FILES:
        return Response({'error': 'No image file provided'}, status=status.HTTP_400_BAD_REQUEST)
    
    image_file = request.FILES['image']
    
    # 이미지 파일 검증
    if not image_file.content_type.startswith('image/'):
        return Response({'error': 'File must be an image'}, status=status.HTTP_400_BAD_REQUEST)
    
    # 파일 크기 제한 (5MB)
    if image_file.size > 5 * 1024 * 1024:
        return Response({'error': 'Image file too large (max 5MB)'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # 이미지 최적화
        optimized_image = optimize_image(image_file)
        
        # 고유한 파일명 생성
        file_extension = os.path.splitext(image_file.name)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        # 업로드 경로 설정
        upload_path = f"content_images/{request.user.id}/{unique_filename}"
        
        # 파일 저장
        saved_path = default_storage.save(upload_path, ContentFile(optimized_image))
        
        # 절대 URL 생성
        file_url = request.build_absolute_uri(default_storage.url(saved_path))
        
        return Response({
            'url': file_url,
            'filename': unique_filename,
            'size': len(optimized_image)
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def optimize_image(image_file, max_width=800, max_height=600, quality=85):
    """
    이미지 최적화 함수
    
    - 큰 이미지를 리사이즈
    - JPEG 품질 조정
    - 웹 최적화
    """
    try:
        # 이미지 열기
        image = Image.open(image_file)
        
        # RGBA를 RGB로 변환 (JPEG 호환성)
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        
        # 이미지 리사이즈 (비율 유지)
        image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        
        # 최적화된 이미지를 바이트로 변환
        output = io.BytesIO()
        
        # 원본 형식 유지 (JPEG, PNG 등)
        format_type = image.format if image.format else 'JPEG'
        if format_type == 'JPEG':
            image.save(output, format='JPEG', quality=quality, optimize=True)
        else:
            image.save(output, format=format_type, optimize=True)
        
        output.seek(0)
        return output.read()
        
    except Exception as e:
        raise Exception(f"Image optimization failed: {str(e)}")


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_image(request, filename):
    """
    이미지 삭제 API
    
    사용자가 자신이 업로드한 이미지만 삭제할 수 있습니다.
    """
    try:
        # 파일 경로 구성
        file_path = f"content_images/{request.user.id}/{filename}"
        
        # 파일 존재 확인
        if not default_storage.exists(file_path):
            return Response({'error': 'Image not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # 파일 삭제
        default_storage.delete(file_path)
        
        return Response({'message': 'Image deleted successfully'}, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)