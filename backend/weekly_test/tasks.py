"""
Celery tasks for async weekly test generation

비동기 주간 시험 문제 생성을 위한 Celery 태스크
"""
import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def generate_test_questions_async(self, test_id, content_ids=None, category_id=None):
    """
    비동기로 주간 시험 문제 생성

    Args:
        test_id: WeeklyTest ID
        content_ids: 선택된 콘텐츠 ID 리스트 (수동 선택)
        category_id: 카테고리 ID (자동 선택)

    Returns:
        dict: 생성 결과 정보
    """
    from .models import WeeklyTest
    from .views import WeeklyTestListCreateView

    try:
        logger.info(f"[Celery] Starting question generation for test {test_id}")

        # 시험 조회
        weekly_test = WeeklyTest.objects.get(id=test_id)

        # View 인스턴스 생성 (메서드 재사용)
        view = WeeklyTestListCreateView()

        # 문제 생성 로직 실행 (user 전달)
        user = weekly_test.user

        if content_ids:
            logger.info(f"[Celery] Generating from content_ids: {content_ids}")
            view._generate_questions_from_ids(weekly_test, content_ids, user)
        elif category_id:
            logger.info(f"[Celery] Generating from category_id: {category_id}")
            view._generate_questions_from_category(weekly_test, category_id, user)
        else:
            logger.info(f"[Celery] Generating balanced questions")
            view._generate_balanced_questions(weekly_test, user)

        # 상태 업데이트
        weekly_test.status = 'pending'
        weekly_test.save()

        result = {
            'test_id': test_id,
            'status': 'success',
            'total_questions': weekly_test.total_questions,
            'completed_at': timezone.now().isoformat()
        }

        logger.info(f"[Celery] Test {test_id} generation completed: {weekly_test.total_questions} questions")
        return result

    except WeeklyTest.DoesNotExist:
        logger.error(f"[Celery] Test {test_id} not found")
        return {
            'test_id': test_id,
            'status': 'error',
            'error': 'Test not found'
        }

    except Exception as e:
        logger.error(f"[Celery] Error generating questions for test {test_id}: {e}", exc_info=True)

        # 재시도
        try:
            self.retry(countdown=60, exc=e)
        except self.MaxRetriesExceededError:
            # 최대 재시도 초과시 상태 업데이트
            try:
                weekly_test = WeeklyTest.objects.get(id=test_id)
                weekly_test.status = 'pending'  # 실패해도 pending으로 (문제 0개)
                weekly_test.save()
            except:
                pass

            return {
                'test_id': test_id,
                'status': 'error',
                'error': str(e)
            }
