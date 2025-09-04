"""
Content check and quality analysis views for AI review functionality
"""
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
import time


class InstantContentCheckView(APIView):
    """Instant content check view"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """실시간 콘텐츠 이해도 체크"""
        from django.shortcuts import get_object_or_404
        from content.models import Content
        from ai_review.models import InstantContentCheck, AIQuestion
        from ai_review.services.question_generator import QuestionGeneratorService
        
        try:
            # 요청 데이터 검증
            content_id = request.data.get('content_id')
            check_point = request.data.get('check_point', '100%')
            questions_count = request.data.get('questions_count', 3)
            
            if not content_id:
                return Response({
                    'error': 'content_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 콘텐츠 확인
            content = get_object_or_404(Content, id=content_id, author=request.user)
            
            # 이미 해당 체크포인트에서 검사했는지 확인
            existing_check = InstantContentCheck.objects.filter(
                user=request.user,
                content=content,
                check_point=check_point
            ).first()
            
            if existing_check:
                return Response({
                    'message': '이미 이 지점에서 검사를 완료했습니다.',
                    'existing_check': {
                        'understanding_score': existing_check.understanding_score,
                        'weak_points': existing_check.weak_points,
                        'feedback': existing_check.feedback
                    }
                }, status=status.HTTP_200_OK)
            
            # AI 문제 생성
            start_time = time.time()
            question_generator = QuestionGeneratorService()
            
            # 콘텐츠에서 문제 생성 (간단한 버전)
            questions = []
            for i in range(min(questions_count, 5)):  # 최대 5개
                try:
                    question_data = question_generator.generate_multiple_choice(
                        content_text=content.body[:1000],  # 처음 1000자만 사용
                        difficulty=1  # 쉬운 난이도로 빠르게 체크
                    )
                    questions.append({
                        'question': question_data['question'],
                        'options': question_data['options'],
                        'correct_answer': question_data['answer']
                    })
                except Exception as e:
                    # AI 호출 실패시 기본 질문 제공
                    questions.append({
                        'question': f'{content.title}의 핵심 내용을 이해하셨나요?',
                        'options': ['매우 잘 이해함', '어느정도 이해함', '조금 어려움', '전혀 모르겠음'],
                        'correct_answer': '매우 잘 이해함'
                    })
            
            duration = int((time.time() - start_time) * 1000)  # ms
            
            # 임시로 이해도 점수 계산 (실제 답변 전이므로 기본값)
            understanding_score = 70.0  # 기본 점수
            weak_points = []
            feedback = f"{content.title} 내용에 대한 {questions_count}개 확인 문제입니다. 차근차근 답해보세요!"
            
            # InstantContentCheck 생성
            instant_check = InstantContentCheck.objects.create(
                user=request.user,
                content=content,
                check_point=check_point,
                questions_count=len(questions),
                correct_count=0,  # 아직 답변 전
                understanding_score=understanding_score,
                weak_points=weak_points,
                feedback=feedback,
                duration_seconds=duration // 1000
            )
            
            return Response({
                'success': True,
                'check_id': instant_check.id,
                'questions': questions,
                'check_point': check_point,
                'message': f'{content.title}의 이해도를 확인해보세요!'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': f'실시간 검토 생성 중 오류가 발생했습니다: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request):
        """답변 제출 및 결과 업데이트"""
        from django.shortcuts import get_object_or_404
        from ai_review.models import InstantContentCheck
        
        try:
            check_id = request.data.get('check_id')
            answers = request.data.get('answers', [])
            
            if not check_id or not answers:
                return Response({
                    'error': 'check_id and answers are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            instant_check = get_object_or_404(
                InstantContentCheck.objects.select_related('user', 'content'), 
                id=check_id, 
                user=request.user
            )
            
            # 정답 개수 계산 (간단한 버전 - 실제로는 AI 평가 필요)
            correct_count = 0
            for answer in answers:
                if answer.get('is_correct', False):
                    correct_count += 1
            
            # 이해도 점수 계산
            total_questions = len(answers)
            accuracy_rate = correct_count / total_questions if total_questions > 0 else 0
            understanding_score = accuracy_rate * 100
            
            # 취약점 분석 (간단한 버전)
            weak_points = []
            if accuracy_rate < 0.7:
                weak_points.append("기본 개념 이해 부족")
            if accuracy_rate < 0.5:
                weak_points.append("전반적인 복습 필요")
            
            # 피드백 생성
            if understanding_score >= 90:
                feedback = "🎉 완벽하게 이해하셨네요! 다음 단계로 진행하셔도 좋습니다."
            elif understanding_score >= 70:
                feedback = "👍 전반적으로 잘 이해하셨어요. 조금 더 복습하면 완벽할 것 같아요!"
            elif understanding_score >= 50:
                feedback = "📚 기본은 이해하셨지만 좀 더 학습이 필요해 보여요."
            else:
                feedback = "🔄 다시 한번 천천히 읽어보시는 걸 추천드려요."
            
            # InstantContentCheck 업데이트
            instant_check.correct_count = correct_count
            instant_check.understanding_score = understanding_score
            instant_check.weak_points = weak_points
            instant_check.feedback = feedback
            instant_check.save()
            
            return Response({
                'success': True,
                'understanding_score': understanding_score,
                'accuracy_rate': f'{accuracy_rate * 100:.1f}%',
                'weak_points': weak_points,
                'feedback': feedback,
                'correct_count': correct_count,
                'total_questions': total_questions
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'답변 처리 중 오류가 발생했습니다: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ContentQualityCheckView(APIView):
    """Content quality check view for new content"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Check quality of content by title and content text"""
        try:
            # 요청 데이터 검증
            title = request.data.get('title', '').strip()
            content = request.data.get('content', '').strip()
            
            if not title or not content:
                return Response({
                    'error': '제목과 내용을 모두 입력해주세요.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if len(content) < 10:
                return Response({
                    'error': '내용이 너무 짧습니다. 최소 10자 이상 입력해주세요.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if len(content) < 300:
                return Response({
                    'score': 0,
                    'feedback': 'AI 품질 분석을 위해서는 최소 300자 이상의 내용이 필요합니다.',
                    'strengths': [],
                    'improvements': ['내용을 300자 이상으로 확장하여 더 자세한 AI 분석을 받아보세요.'],
                    'processing_time_ms': 0,
                    'status': 'insufficient_content',
                    'required_length': 300,
                    'current_length': len(content)
                })
            
            start_time = time.time()
            
            # 콘텐츠 품질 분석 로직 (간단한 기준)
            score = self._calculate_content_quality(title, content)
            feedback = self._generate_feedback(title, content, score)
            strengths = self._identify_strengths(title, content, score)
            improvements = self._identify_improvements(title, content, score)
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return Response({
                'score': score,
                'feedback': feedback,
                'strengths': strengths,
                'improvements': improvements,
                'processing_time_ms': processing_time,
                'status': 'success'
            })
            
        except Exception as e:
            return Response({
                'error': f'콘텐츠 품질 분석 중 오류가 발생했습니다: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _calculate_content_quality(self, title: str, content: str) -> int:
        """Calculate content quality score (0-100)"""
        score = 50  # 기본 점수
        
        # 제목 평가
        if len(title) >= 5:
            score += 10
        if len(title) <= 50:
            score += 5
        
        # 내용 평가
        if len(content) >= 100:
            score += 15
        if len(content) >= 500:
            score += 10
        
        # 구조화 평가 (줄바꿈, 문단 등)
        lines = content.split('\n')
        if len(lines) >= 3:
            score += 10
        
        # 최대 100점 제한
        return min(score, 100)
    
    def _generate_feedback(self, title: str, content: str, score: int) -> str:
        """Generate feedback message"""
        if score >= 80:
            return "훌륭한 콘텐츠입니다! 제목과 내용이 잘 구조화되어 있고 학습에 도움이 될 것 같습니다."
        elif score >= 60:
            return "좋은 콘텐츠입니다. 몇 가지 개선사항을 반영하면 더욱 좋아질 것 같습니다."
        else:
            return "콘텐츠를 보완하면 더 효과적인 학습 자료가 될 수 있습니다."
    
    def _identify_strengths(self, title: str, content: str, score: int) -> list:
        """Identify content strengths"""
        strengths = []
        
        if len(title) >= 5 and len(title) <= 50:
            strengths.append("적절한 길이의 명확한 제목")
        
        if len(content) >= 100:
            strengths.append("충분한 내용 분량")
        
        if '\n' in content:
            strengths.append("단락으로 구조화된 내용")
        
        return strengths
    
    def _identify_improvements(self, title: str, content: str, score: int) -> list:
        """Identify improvement areas"""
        improvements = []
        
        if len(title) < 5:
            improvements.append("제목을 더 구체적으로 작성해보세요")
        
        if len(content) < 100:
            improvements.append("내용을 더 자세히 설명해보세요")
        
        if '\n' not in content:
            improvements.append("내용을 단락으로 나누어 가독성을 높여보세요")
        
        return improvements