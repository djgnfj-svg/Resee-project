"""
Test views for AI review functionality - Weekly tests and adaptive testing
"""
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Avg, Count, Q
from datetime import datetime, timedelta
import time


class WeeklyTestCategoriesView(APIView):
    """주간시험용 카테고리 목록 조회"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """사용자의 카테고리 목록 반환"""
        from content.models import Category
        from ai_review.serializers import CategoryChoiceSerializer
        
        try:
            categories = Category.objects.filter(user=request.user).order_by('name')
            serializer = CategoryChoiceSerializer(categories, many=True)
            
            return Response({
                'categories': serializer.data,
                'total_count': categories.count()
            })
        except Exception as e:
            return Response({
                'error': f'카테고리 목록 조회 중 오류: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WeeklyTestView(APIView):
    """Weekly test management view"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """현재 주간 시험 조회"""
        from ai_review.models import WeeklyTest
        from datetime import datetime, timedelta
        
        try:
            # 이번 주 월요일 계산
            today = datetime.now().date()
            monday = today - timedelta(days=today.weekday())
            
            # 현재 주간 시험 조회
            weekly_test = WeeklyTest.objects.filter(
                user=request.user,
                week_start_date=monday
            ).first()
            
            if weekly_test:
                return Response({
                    'exists': True,
                    'test_id': weekly_test.id,
                    'status': weekly_test.status,
                    'score': weekly_test.score,
                    'completed_questions': weekly_test.completed_questions,
                    'total_questions': weekly_test.total_questions,
                    'completion_rate': weekly_test.completion_rate,
                    'started_at': weekly_test.started_at,
                    'completed_at': weekly_test.completed_at,
                    'week_start': weekly_test.week_start_date,
                    'week_end': weekly_test.week_end_date
                })
            else:
                return Response({
                    'exists': False,
                    'message': '이번 주 시험이 아직 생성되지 않았습니다.',
                    'week_start': monday
                })
                
        except Exception as e:
            return Response({
                'error': f'주간 시험 조회 중 오류: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """주간 시험 생성 - 카테고리 선택 및 적응형 기능 포함"""
        from ai_review.models import WeeklyTest, WeeklyTestQuestion, AIQuestion
        from ai_review.serializers import WeeklyTestCreateSerializer
        from content.models import Content, Category
        from datetime import datetime, timedelta
        import random
        
        # 요청 데이터 유효성 검사
        serializer = WeeklyTestCreateSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        validated_data = serializer.validated_data
        
        try:
            # 이번 주 월요일과 일요일 계산
            today = datetime.now().date()
            monday = today - timedelta(days=today.weekday())
            sunday = monday + timedelta(days=6)
            
            # 카테고리 설정
            category = None
            if validated_data.get('category_id'):
                category = Category.objects.get(id=validated_data['category_id'], user=request.user)
            
            # 같은 카테고리의 이번 주 시험이 있는지 확인
            existing_test = WeeklyTest.objects.filter(
                user=request.user,
                category=category,
                week_start_date=monday
            ).first()
            
            if existing_test:
                category_name = category.name if category else "전체"
                return Response({
                    'message': f'이미 {category_name} 카테고리의 이번 주 시험이 생성되어 있습니다.',
                    'test_id': existing_test.id,
                    'status': existing_test.status
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 사용자의 콘텐츠 조회 (카테고리 필터링)
            content_filter = {'author': request.user, 'ai_questions__isnull': False}
            if category:
                content_filter['category'] = category
                
            user_contents = Content.objects.filter(**content_filter).distinct()
            
            if user_contents.count() < 3:
                category_msg = f"{category.name} 카테고리의 " if category else ""
                return Response({
                    'message': f'{category_msg}AI 문제가 있는 콘텐츠가 최소 3개 이상 필요합니다.',
                    'current_count': user_contents.count()
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 주간 시험 생성 (적응형 기능 포함)
            total_questions = validated_data.get('total_questions', 10)
            weekly_test = WeeklyTest.objects.create(
                user=request.user,
                category=category,
                week_start_date=monday,
                week_end_date=sunday,
                total_questions=total_questions,
                adaptive_mode=validated_data.get('adaptive_mode', True),
                current_difficulty='medium',  # 중간 난이도로 시작
                question_type_distribution={
                    'multiple_choice': 6,
                    'short_answer': 3,
                    'essay': 1
                },
                time_limit_minutes=validated_data.get('time_limit_minutes', 30),
                content_coverage=list(user_contents.values_list('id', flat=True)[:10]),
                status='ready'
            )
            
            # AI 문제들 필터링 (카테고리 및 문제 유형별)
            question_filter = {
                'content__author': request.user,
                'is_active': True
            }
            if category:
                question_filter['content__category'] = category
            
            # 문제 유형별로 분배해서 선택 (객6 + 주3 + 서1)
            questions_to_create = []
            
            # 객관식 6문제
            mc_questions = AIQuestion.objects.filter(
                **question_filter,
                question_type__name='multiple_choice'
            ).order_by('?')[:6]
            
            # 주관식 3문제  
            sa_questions = AIQuestion.objects.filter(
                **question_filter,
                question_type__name='short_answer'
            ).order_by('?')[:3]
            
            # 서술형 1문제
            essay_questions = AIQuestion.objects.filter(
                **question_filter,
                question_type__name='essay'
            ).order_by('?')[:1]
            
            # 문제 순서대로 배치
            all_questions = list(mc_questions) + list(sa_questions) + list(essay_questions)
            
            if len(all_questions) < total_questions:
                # 부족한 경우 전체 문제에서 랜덤 선택으로 채움
                remaining_needed = total_questions - len(all_questions)
                additional_questions = AIQuestion.objects.filter(
                    **question_filter
                ).exclude(id__in=[q.id for q in all_questions]).order_by('?')[:remaining_needed]
                all_questions.extend(additional_questions)
            
            # 시험 문제 생성
            for order, ai_question in enumerate(all_questions[:total_questions], 1):
                WeeklyTestQuestion.objects.create(
                    weekly_test=weekly_test,
                    ai_question=ai_question,
                    order=order
                )
            
            # 실제 생성된 문제 수로 업데이트
            weekly_test.total_questions = len(all_questions[:total_questions])
            weekly_test.save()
            
            category_name = category.name if category else "전체"
            return Response({
                'success': True,
                'test_id': weekly_test.id,
                'category': category_name,
                'total_questions': weekly_test.total_questions,
                'adaptive_mode': weekly_test.adaptive_mode,
                'current_difficulty': weekly_test.current_difficulty,
                'status': weekly_test.status,
                'week_period': f'{monday} ~ {sunday}',
                'message': f'{category_name} 카테고리 주간 시험이 생성되었습니다! 총 {weekly_test.total_questions}문제'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': f'주간 시험 생성 중 오류: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WeeklyTestStartView(APIView):
    """Weekly test start view"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """주간 시험 시작"""
        from django.shortcuts import get_object_or_404
        from ai_review.models import WeeklyTest
        from django.utils import timezone
        
        try:
            test_id = request.data.get('test_id')
            if not test_id:
                return Response({
                    'error': 'test_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            weekly_test = get_object_or_404(WeeklyTest, id=test_id, user=request.user)
            
            # 시험 상태 확인
            if weekly_test.status == 'completed':
                return Response({
                    'message': '이미 완료된 시험입니다.',
                    'score': weekly_test.score,
                    'completed_at': weekly_test.completed_at
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if weekly_test.status == 'expired':
                return Response({
                    'message': '시간이 만료된 시험입니다.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 시험 시작
            if weekly_test.status == 'ready':
                weekly_test.status = 'in_progress'
                weekly_test.started_at = timezone.now()
                weekly_test.save()
            
            # 첫 번째 문제 가져오기
            first_question = weekly_test.test_questions.order_by('order').first()
            
            if not first_question:
                return Response({
                    'error': '시험 문제가 없습니다.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                'success': True,
                'test_id': weekly_test.id,
                'status': weekly_test.status,
                'started_at': weekly_test.started_at,
                'time_limit_minutes': weekly_test.time_limit_minutes,
                'total_questions': weekly_test.total_questions,
                'current_question': {
                    'order': first_question.order,
                    'question': first_question.ai_question.question_text,
                    'options': first_question.ai_question.options,
                    'content_title': first_question.ai_question.content.title
                },
                'message': '시험이 시작되었습니다! 화이팅!'
            })
            
        except Exception as e:
            return Response({
                'error': f'시험 시작 중 오류: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get(self, request):
        """진행 중인 시험의 다음 문제 조회"""
        from django.shortcuts import get_object_or_404
        from ai_review.models import WeeklyTest
        
        try:
            test_id = request.GET.get('test_id')
            question_order = int(request.GET.get('question_order', 1))
            
            if not test_id:
                return Response({
                    'error': 'test_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            weekly_test = get_object_or_404(WeeklyTest, id=test_id, user=request.user)
            
            # 시간 제한 체크
            if weekly_test.is_expired():
                weekly_test.status = 'expired'
                weekly_test.save()
                return Response({
                    'expired': True,
                    'message': '시험 시간이 만료되었습니다.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 해당 순서의 문제 조회
            question = weekly_test.test_questions.filter(order=question_order).first()
            
            if not question:
                return Response({
                    'completed': True,
                    'message': '모든 문제를 완료했습니다!',
                    'total_questions': weekly_test.total_questions
                })
            
            return Response({
                'success': True,
                'question': {
                    'order': question.order,
                    'question': question.ai_question.question_text,
                    'options': question.ai_question.options,
                    'content_title': question.ai_question.content.title,
                    'total_questions': weekly_test.total_questions,
                    'progress': f'{question_order}/{weekly_test.total_questions}'
                }
            })
            
        except Exception as e:
            return Response({
                'error': f'문제 조회 중 오류: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WeeklyTestAnswerView(APIView):
    """주간 시험 답변 제출"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """답변 제출 및 채점"""
        from django.shortcuts import get_object_or_404
        from ai_review.models import WeeklyTest, WeeklyTestQuestion
        from django.utils import timezone
        
        try:
            test_id = request.data.get('test_id')
            question_order = request.data.get('question_order')
            user_answer = request.data.get('user_answer')
            
            if not all([test_id, question_order, user_answer]):
                return Response({
                    'error': 'test_id, question_order, user_answer are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            weekly_test = get_object_or_404(WeeklyTest, id=test_id, user=request.user)
            
            # 시간 제한 체크
            if weekly_test.is_expired():
                weekly_test.status = 'expired'
                weekly_test.save()
                return Response({
                    'expired': True,
                    'message': '시험 시간이 만료되었습니다.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 해당 문제 조회
            test_question = get_object_or_404(
                WeeklyTestQuestion, 
                weekly_test=weekly_test, 
                order=question_order
            )
            
            # 이미 답변했는지 확인
            if test_question.user_answer:
                return Response({
                    'message': '이미 답변한 문제입니다.',
                    'previous_answer': test_question.user_answer
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 정답 확인 (간단한 버전)
            correct_answer = test_question.ai_question.correct_answer
            is_correct = user_answer.strip().lower() == correct_answer.strip().lower()
            
            # 답변 저장
            test_question.user_answer = user_answer
            test_question.is_correct = is_correct
            test_question.answered_at = timezone.now()
            test_question.save()
            
            # 주간 시험 진행률 업데이트
            weekly_test.completed_questions += 1
            if is_correct:
                weekly_test.correct_answers += 1
            
            # 적응형 난이도 조절
            if weekly_test.adaptive_mode:
                weekly_test.adjust_difficulty(is_correct)
            
            # 모든 문제 완료 확인
            if weekly_test.completed_questions >= weekly_test.total_questions:
                weekly_test.status = 'completed'
                weekly_test.completed_at = timezone.now()
                weekly_test.score = (weekly_test.correct_answers / weekly_test.total_questions) * 100
                
                # 취약 분야 분석 (간단한 버전)
                weak_areas = []
                wrong_questions = weekly_test.test_questions.filter(is_correct=False)
                for wrong_q in wrong_questions:
                    content_title = wrong_q.ai_question.content.title
                    if content_title not in weak_areas:
                        weak_areas.append(content_title)
                
                weekly_test.weak_areas = weak_areas[:5]  # 최대 5개
                
                # 지난 주 대비 향상도 계산 (간단한 버전)
                last_week_test = WeeklyTest.objects.filter(
                    user=request.user,
                    week_start_date__lt=weekly_test.week_start_date,
                    status='completed'
                ).order_by('-week_start_date').first()
                
                if last_week_test and last_week_test.score:
                    improvement = weekly_test.score - last_week_test.score
                    weekly_test.improvement_from_last_week = improvement
            
            weekly_test.save()
            
            # 응답 데이터
            response_data = {
                'success': True,
                'is_correct': is_correct,
                'correct_answer': correct_answer if not is_correct else None,
                'progress': f'{weekly_test.completed_questions}/{weekly_test.total_questions}',
                'completion_rate': weekly_test.completion_rate,
                'current_difficulty': weekly_test.current_difficulty,
                'consecutive_correct': weekly_test.consecutive_correct,
                'consecutive_wrong': weekly_test.consecutive_wrong
            }
            
            # 시험 완료시 추가 정보
            if weekly_test.status == 'completed':
                response_data.update({
                    'test_completed': True,
                    'final_score': weekly_test.score,
                    'accuracy_rate': weekly_test.accuracy_rate,
                    'weak_areas': weekly_test.weak_areas,
                    'improvement': weekly_test.improvement_from_last_week,
                    'message': f'🎉 시험 완료! 점수: {weekly_test.score:.1f}점'
                })
            else:
                response_data['next_question_order'] = question_order + 1
            
            return Response(response_data)
            
        except Exception as e:
            return Response({
                'error': f'답변 제출 중 오류: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class InstantContentCheckView(APIView):
    """Instant content check view"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        from django.shortcuts import get_object_or_404
        from content.models import Content
        from ai_review.models import InstantContentCheck, AIQuestion
        from ai_review.services.question_generator import QuestionGeneratorService
        import time
        
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
                InstantContentCheck, 
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


class LearningAnalyticsView(APIView):
    """Learning analytics view"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        return Response({
            'message': '학습 분석 기능은 현재 개발 중입니다.',
            'status': 'under_development'
        }, status=status.HTTP_501_NOT_IMPLEMENTED)


class AIStudyMateView(APIView):
    """AI study mate view"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        return Response({
            'message': 'AI 스터디 메이트 기능은 현재 개발 중입니다.',
            'status': 'under_development'
        }, status=status.HTTP_501_NOT_IMPLEMENTED)


class AISummaryNoteView(APIView):
    """AI summary note view"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        return Response({
            'message': 'AI 요약 노트 기능은 현재 개발 중입니다.',
            'status': 'under_development'
        }, status=status.HTTP_501_NOT_IMPLEMENTED)


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
    
    def _calculate_content_quality(self, title, content):
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
    
    def _generate_feedback(self, title, content, score):
        """Generate feedback message"""
        if score >= 80:
            return "훌륭한 콘텐츠입니다! 제목과 내용이 잘 구조화되어 있고 학습에 도움이 될 것 같습니다."
        elif score >= 60:
            return "좋은 콘텐츠입니다. 몇 가지 개선사항을 반영하면 더욱 좋아질 것 같습니다."
        else:
            return "콘텐츠를 보완하면 더 효과적인 학습 자료가 될 수 있습니다."
    
    def _identify_strengths(self, title, content, score):
        """Identify content strengths"""
        strengths = []
        
        if len(title) >= 5 and len(title) <= 50:
            strengths.append("적절한 길이의 명확한 제목")
        
        if len(content) >= 100:
            strengths.append("충분한 내용 분량")
        
        if '\n' in content:
            strengths.append("단락으로 구조화된 내용")
        
        return strengths
    
    def _identify_improvements(self, title, content, score):
        """Identify improvement areas"""
        improvements = []
        
        if len(title) < 5:
            improvements.append("제목을 더 구체적으로 작성해보세요")
        
        if len(content) < 100:
            improvements.append("내용을 더 자세히 설명해보세요")
        
        if '\n' not in content:
            improvements.append("내용을 단락으로 나누어 가독성을 높여보세요")
        
        return improvements


