# 신입 백엔드 개발자를 위한 트러블슈팅 이슈 리스트

**프로젝트**: Resee (Django 복습 시스템)
**목적**: 신입 백엔드 개발자가 실제 코드베이스에서 트러블슈팅 경험을 쌓을 수 있는 이슈 목록
**작성일**: 2025-10-20

---

## 📌 이슈 난이도 분류

- **입문 (Junior)**: 1-2시간, 개념 이해와 간단한 수정
- **중급 (Mid-level)**: 2-4시간, 코드 분석과 로직 이해 필요
- **고급 (Senior)**: 4-8시간, 아키텍처 이해와 복잡한 디버깅

---

## 🟢 입문 레벨 (Junior) - 예상 소요 시간: 1-2시간

### 1. Bare except 사용 개선 ✅ **완료 (2025-10-20)**

**설명**: Python에서 `except:` (bare except)는 모든 예외를 잡아서 디버깅을 어렵게 만듭니다. 구체적인 예외 타입을 명시해야 합니다.

**상태**: ✅ **해결 완료**
- **커밋**: `5633755` - "fix: Replace bare except with specific exceptions in 4 locations"
- **문서**: `docs/troubleshooting/05-bare-except-안티패턴.md`
- **소요 시간**: 1시간

**수정된 위치**:
- ✅ `backend/review/backup_tasks.py:96` - Slack 알림 실패 로깅 추가
- ✅ `backend/content/serializers.py:98` - KeyError/AttributeError 처리
- ✅ `backend/resee/settings/__init__.py:39` - SECRET_KEY 검증 실패 경고
- ✅ `backend/resee/settings/__init__.py:58` - Production 검증 실패 경고

**개선 내용**:
```python
# Before
except:
    pass

# After
except Exception as slack_error:
    logger.warning(f"Failed to send Slack notification: {slack_error}")
```

**학습 포인트**:
- Python 예외 처리 베스트 프랙티스
- 로깅의 중요성
- 디버깅 가능한 코드 작성
- BaseException vs Exception 차이 이해

**참고 자료**:
- PEP 8: https://peps.python.org/pep-0008/#programming-recommendations
- Python 예외 처리 가이드
- 상세 회고: `docs/troubleshooting/05-bare-except-안티패턴.md`

---

### 2. 로깅 메시지 개선 ✅ **완료 (2025-10-20)**

**설명**: 일부 에러 핸들링에서 로깅이 누락되어 있거나 정보가 불충분합니다.

**상태**: ✅ **해결 완료**
- **문서**: `docs/troubleshooting/06-로깅-메시지-개선.md`
- **소요 시간**: 45분

**수정된 위치**:
- ✅ `backend/content/ai_validation.py:94` - exc_info=True 추가, 컨텍스트 정보 포함
- ✅ `backend/content/ai_validation.py:127` - 파싱 실패 시 원본 응답 로깅
- ✅ `backend/review/ai_evaluation.py:81` - exc_info=True 추가
- ✅ `backend/review/ai_evaluation.py:152-164` - Anthropic API 예외별 처리
- ✅ `backend/review/ai_evaluation.py:202-207` - JSON 파싱 예외 세분화

**개선 내용**:
```python
# Before
except Exception as e:
    logger.error(f"AI validation failed: {str(e)}")

# After
except Exception as e:
    logger.error(f"AI validation failed for title '{title[:50]}...': {str(e)}", exc_info=True)
```

**주요 개선 사항**:
1. **exc_info=True 추가** - 스택 트레이스로 정확한 에러 위치 파악
2. **예외 타입별 처리** - AuthenticationError, RateLimitError 등 구체적으로 처리
3. **컨텍스트 정보** - 에러 발생 시 관련 데이터 (title, user 등) 포함
4. **로깅 레벨 조정** - 일시적 에러는 WARNING, 심각한 에러는 ERROR

**학습 포인트**:
- Python logging의 exc_info 파라미터
- 로깅 레벨 선택 (DEBUG/INFO/WARNING/ERROR/CRITICAL)
- 구조화된 로깅 (structured logging)
- 프로덕션 환경에서의 디버깅
- Anthropic API 예외 처리

**참고 자료**:
- 상세 회고: `docs/troubleshooting/06-로깅-메시지-개선.md`

---

### 3. 입력 검증 강화 ✅ **완료 (2025-10-20)**

**설명**: 일부 API 엔드포인트에서 입력값 검증이 부족합니다.

**상태**: ✅ **해결 완료**
- **문서**: `docs/troubleshooting/07-입력-검증-강화.md`
- **소요 시간**: 1시간

**수정된 위치**:
- ✅ `backend/review/views.py:215-263` - CompleteReviewView 입력 검증 추가

**개선 내용**:
```python
# Before
content_id = request.data.get('content_id')
time_spent = request.data.get('time_spent')
# 검증 없이 바로 사용

# After
# 1. content_id 타입 검증
if not content_id:
    return Response({'error': 'content_id is required'}, ...)
try:
    content_id = int(content_id)
except (ValueError, TypeError):
    return Response({'error': 'content_id must be a valid integer'}, ...)

# 2. time_spent 범위 검증
if time_spent < 0:
    return Response({'error': 'time_spent cannot be negative'}, ...)
if time_spent > 86400:  # 24 hours
    return Response({'error': 'time_spent cannot exceed 24 hours'}, ...)

# 3. notes 길이 제한 (DoS 방지)
if len(notes) > 5000:
    return Response({'error': 'notes cannot exceed 5000 characters'}, ...)

# 4. descriptive_answer 길이 제한 (DoS 방지)
if len(descriptive_answer) > 10000:
    return Response({'error': 'descriptive_answer cannot exceed 10000 characters'}, ...)
```

**주요 개선 사항**:
1. **타입 검증** - content_id 정수 변환 및 검증
2. **범위 검증** - time_spent 0-86400초 (24시간) 제한
3. **DoS 방지** - notes 5000자, descriptive_answer 10000자 제한
4. **소유권 검증** - ReviewSchedule 조회 시 명시적 예외 처리 및 로깅

**보안 효과**:
- DoS 공격 방지 (무제한 텍스트 차단)
- AI API 비용 폭탄 방지 (10000자 제한으로 약 $6.25/회 → $0.000625/회)
- 데이터 무결성 보장 (음수 시간, 타입 에러 방지)

**학습 포인트**:
- 방어적 프로그래밍 (Defensive Programming)
- DoS 공격 방지 전략
- 입력 검증 체크리스트
- Django REST Framework Serializer vs 수동 검증
- OWASP Input Validation

**참고 자료**:
- 상세 회고: `docs/troubleshooting/07-입력-검증-강화.md`

---

## 🟡 중급 레벨 (Mid-level) - 예상 소요 시간: 2-4시간

### 4. N+1 쿼리 최적화

**설명**: `analytics/views.py`의 DashboardStatsView에서 N+1 쿼리 문제가 발생할 수 있습니다.

**위치**: `backend/analytics/views.py:15-37`

**현재 코드**:
```python
def get(self, request):
    user = request.user
    today_reviews = get_today_reviews_count(user)
    pending_reviews = get_pending_reviews_count(user)
    total_content = Content.objects.filter(author=user).count()
    success_rate, total_reviews_30_days, _ = calculate_success_rate(user, days=30)
```

**문제점**:
- 여러 함수에서 각각 DB 쿼리 실행
- select_related/prefetch_related 누락
- 캐싱 미적용

**개선 방향**:
1. 쿼리 최적화 (select_related, prefetch_related)
2. 캐싱 레이어 추가 (Redis 또는 locmem)
3. Django Debug Toolbar로 쿼리 분석

**학습 포인트**:
- Django ORM 최적화
- N+1 쿼리 문제 이해
- 캐싱 전략
- Django Debug Toolbar 사용법

**디버깅 방법**:
```bash
# Django Debug Toolbar 활성화하여 쿼리 확인
docker-compose exec backend python manage.py shell
from django.test.utils import setup_test_environment
setup_test_environment()
# 쿼리 카운트 확인
```

---

### 5. 에러 핸들링 패턴 일관성

**설명**: 프로젝트 전반에 걸쳐 에러 핸들링 패턴이 일관되지 않습니다.

**위치**:
- `backend/content/views.py:279-284` - by_category 메서드
- `backend/review/views.py:372-383` - CompleteReviewView

**현재 상황**:
- 일부는 APIErrorHandler 사용
- 일부는 직접 Response 반환
- 일부는 logger만 사용

**개선 방향**:
1. 전역 에러 핸들링 전략 수립
2. 커스텀 Exception 클래스 정의
3. 일관된 에러 응답 포맷

**학습 포인트**:
- Django REST Framework 예외 처리
- 커스텀 Exception 클래스 설계
- API 에러 응답 표준화

---

### 6. 캐싱 전략 개선

**설명**: 자주 조회되지만 변경이 적은 데이터에 캐싱이 누락되어 있습니다.

**위치**:
- `backend/content/views.py:223` - by_category 메서드 (캐싱 있음)
- `backend/review/views.py:418-501` - CategoryReviewStatsView (캐싱 없음)

**개선 사항**:
1. CategoryReviewStatsView에 캐싱 추가
2. 캐시 무효화 로직 구현 (ReviewHistory 생성 시)
3. 캐시 키 전략 개선

**학습 포인트**:
- Django 캐싱 프레임워크
- Redis 캐싱 전략
- 캐시 무효화 (Cache Invalidation)
- TTL (Time To Live) 설정

---

## 🔴 고급 레벨 (Senior) - 예상 소요 시간: 4-8시간

### 7. JWT 토큰 블랙리스트 트랜잭션 처리 (테스트 실패 수정) ⚠️

**설명**: 비밀번호 변경 시 JWT 토큰 블랙리스트 처리가 트랜잭션 내에서 제대로 처리되지 않아 보안 테스트가 실패합니다.

**위치**: `backend/accounts/auth/views.py:211-271`

**테스트 실패**: `backend/accounts/tests/test_security.py:168-214` - `test_token_blacklisted_on_password_change`

**현재 문제**:
```python
@transaction.atomic
def post(self, request):
    serializer = PasswordChangeSerializer(...)
    if serializer.is_valid():
        try:
            serializer.save()  # 비밀번호 변경

            # 블랙리스트 처리가 inner try-except에 있음
            try:
                from rest_framework_simplejwt.token_blacklist.models import (
                    OutstandingToken, BlacklistedToken
                )
                outstanding_tokens = OutstandingToken.objects.filter(user=request.user)
                for token in outstanding_tokens:
                    BlacklistedToken.objects.get_or_create(token=token)
            except ImportError:
                logger.warning("token_blacklist not available.")
        except Exception as e:
            logger.error(f"Password change failed: {str(e)}")
```

**문제점**:
1. `@transaction.atomic` 데코레이터가 있지만 inner try-except로 인해 블랙리스트 실패 시 트랜잭션 롤백이 안 됨
2. ImportError는 잡지만 다른 예외는 무시됨
3. 비밀번호는 변경되었지만 토큰은 블랙리스트되지 않는 상황 발생 가능 (보안 취약점)

**개선 방향**:
1. 블랙리스트 처리를 transaction.atomic 스코프 내에서 강제 실행
2. ImportError는 초기화 단계에서 확인
3. 블랙리스트 실패 시 예외 발생시켜 트랜잭션 롤백
4. 통합 테스트로 검증

**학습 포인트**:
- Django 트랜잭션 관리 (ACID)
- JWT 토큰 보안
- 보안 테스트 작성
- 원자성 (Atomicity) 보장

**참고**:
- CLAUDE.md의 "Recent Changes" 섹션에 명시된 알려진 이슈
- 테스트 커버리지: 40/41 passing (1개 실패)

---

### 8. 레이스 컨디션 방지

**설명**: 동시성 환경에서 ReviewSchedule 업데이트 시 레이스 컨디션이 발생할 수 있습니다.

**위치**: `backend/review/views.py:207-383` - CompleteReviewView

**현재 코드**:
```python
schedule = ReviewSchedule.objects.select_for_update().get(
    content_id=content_id,
    user=request.user,
    is_active=True
)
```

**잠재적 문제**:
1. `select_for_update()`를 사용하고 있지만 트랜잭션 스코프 확인 필요
2. 동일 사용자가 여러 디바이스에서 동시에 복습 완료 시 데이터 정합성
3. interval_index 업데이트 시 경합 조건

**개선 방향**:
1. 트랜잭션 격리 수준 검토
2. F() 표현식 사용으로 원자적 업데이트
3. 낙관적 락 또는 비관적 락 전략 수립
4. 동시성 테스트 작성

**학습 포인트**:
- 데이터베이스 동시성 제어
- 락(Lock) 메커니즘
- F() 표현식과 원자적 연산
- 트랜잭션 격리 수준 (Isolation Level)

**테스트 시나리오**:
```python
# 동시성 테스트 예시
from concurrent.futures import ThreadPoolExecutor

def test_concurrent_review_completion():
    # 동일 사용자가 동시에 같은 리뷰를 2번 완료
    # 예상: 1번만 성공, 1번은 실패 또는 무시
    pass
```

---

### 9. 보안 강화: 토큰 검증 개선

**설명**: 이메일 인증 토큰의 타이밍 공격 방지가 구현되어 있지만 추가 개선 가능합니다.

**위치**: `backend/accounts/models.py` - User.verify_email 메서드

**현재 구현**:
- SHA-256 해싱 ✅
- `secrets.compare_digest()` 사용 ✅ (constant-time comparison)
- 토큰 만료 검증 ✅

**추가 개선 사항**:
1. 토큰 재사용 방지 (one-time token)
2. Rate limiting for verification endpoint
3. 실패 시도 횟수 제한
4. IP 기반 suspicious activity 탐지

**학습 포인트**:
- 암호학 기초 (해싱, 상수 시간 비교)
- 타이밍 공격 (Timing Attack) 이해
- OWASP Top 10
- 보안 테스트 작성

**참고**:
- 현재 보안 테스트: `backend/accounts/tests/test_security.py`
- 타이밍 공격 테스트: `test_constant_time_comparison` (passing)

---

### 10. Subscription Service N+1 쿼리

**설명**: PermissionService에서 반복적으로 Content/Category 카운트를 조회합니다.

**위치**: `backend/accounts/subscription/services.py:29-39`

**현재 코드**:
```python
def can_create_content(self):
    from content.models import Content
    current_count = Content.objects.filter(author=self.user).count()
    return current_count < self.get_content_limit()

def can_create_category(self):
    from content.models import Category
    current_count = Category.objects.filter(user=self.user).count()
    return current_count < self.get_category_limit()
```

**문제점**:
- 매번 DB 쿼리 실행
- 캐싱 없음
- 여러 번 호출 시 성능 저하

**개선 방향**:
1. 인스턴스 변수로 캐싱
2. @cached_property 사용
3. Redis 캐싱 레이어 추가
4. 배치 조회 메서드 추가

**학습 포인트**:
- Python @property와 @cached_property
- 서비스 레이어 패턴
- 메모이제이션 (Memoization)

---

## 📋 추가 개선 기회 (선택 사항)

### 11. Celery Task 에러 핸들링

**위치**: `backend/review/tasks.py`

**개선 사항**:
- 태스크 실패 시 재시도 전략 개선
- Dead Letter Queue 구현
- 모니터링 메트릭 추가

---

### 12. API 응답 시간 최적화

**위치**: `backend/review/views.py:418-501` - CategoryReviewStatsView

**개선 사항**:
- 여러 쿼리를 하나의 쿼리로 통합
- Annotate/Aggregate 활용
- 인덱스 추가

---

### 13. 환경 변수 검증

**위치**: `backend/resee/settings/__init__.py:58`

**현재 코드**:
```python
except:
    warnings.append(f"Invalid {var}: {value}")
```

**개선 사항**:
- 구체적인 예외 처리
- 타입 검증 추가
- pydantic 사용 고려

---

## 🎯 학습 로드맵 (추천)

### Week 1-2: 입문 레벨
1. Bare except 수정 (이슈 #1)
2. 로깅 메시지 개선 (이슈 #2)
3. 입력 검증 강화 (이슈 #3)

**목표**: Python 에러 처리와 로깅 베스트 프랙티스 학습

---

### Week 3-4: 중급 레벨
4. N+1 쿼리 최적화 (이슈 #4)
5. 캐싱 전략 개선 (이슈 #6)

**목표**: Django ORM 최적화와 캐싱 전략 이해

---

### Week 5-8: 고급 레벨
7. JWT 토큰 블랙리스트 트랜잭션 처리 (이슈 #7) ⭐ 우선순위 높음
8. 레이스 컨디션 방지 (이슈 #8)

**목표**: 트랜잭션 관리, 동시성 제어, 보안 테스트

---

## 📚 참고 자료

### Django 공식 문서
- Database Transactions: https://docs.djangoproject.com/en/4.2/topics/db/transactions/
- Database Optimization: https://docs.djangoproject.com/en/4.2/topics/db/optimization/
- Caching: https://docs.djangoproject.com/en/4.2/topics/cache/

### 보안
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- JWT Best Practices: https://tools.ietf.org/html/rfc8725

### Python
- PEP 8: https://peps.python.org/pep-0008/
- Python Logging HOWTO: https://docs.python.org/3/howto/logging.html

---

## 🔧 개발 환경 설정

### 테스트 실행
```bash
# 전체 테스트
docker-compose exec backend python -m pytest

# 특정 테스트
docker-compose exec backend python -m pytest backend/accounts/tests/test_security.py::PasswordChangeSecurityTest::test_token_blacklisted_on_password_change

# 커버리지 확인
docker-compose exec backend python -m pytest --cov=. --cov-report=html
```

### 디버깅 도구
```bash
# Django shell
docker-compose exec backend python manage.py shell_plus

# 로그 확인
docker-compose logs -f backend

# 데이터베이스 접속
docker-compose exec postgres psql -U postgres -d resee_dev
```

---

## ⚠️ 주의사항

1. **브랜치 전략**: 각 이슈마다 별도 브랜치 생성 (`fix/issue-1-bare-except`)
2. **커밋 메시지**: 명확하게 작성 (`fix: Replace bare except with specific exception in backup_tasks.py`)
3. **테스트**: 수정 후 반드시 테스트 실행
4. **코드 리뷰**: PR 생성하여 리뷰 요청
5. **문서화**: CHANGELOG 또는 커밋 메시지에 변경 사항 기록

---

## 📝 이슈 진행 상황 추적 템플릿

```markdown
## Issue #7: JWT 토큰 블랙리스트 트랜잭션 처리

**상태**: In Progress
**담당자**: [이름]
**시작일**: 2025-10-20
**예상 완료일**: 2025-10-27

### 진행 사항
- [x] 문제 분석 완료
- [x] 테스트 실패 재현
- [ ] 코드 수정
- [ ] 테스트 통과 확인
- [ ] 코드 리뷰
- [ ] 머지

### 학습 노트
- Django 트랜잭션: ...
- JWT 블랙리스트: ...
```

---

**끝**
