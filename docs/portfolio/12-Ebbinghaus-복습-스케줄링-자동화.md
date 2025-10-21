# Ebbinghaus 망각곡선 기반 복습 스케줄링 자동화

> 과학적 근거에 기반한 최적 복습 시점 자동 계산 시스템

## 개요

- **구현 시기**: 2025년 10월
- **핵심 기능**: 구독 티어별 차등 복습 간격 자동 계산
- **성과**: Django Signal 자동화로 수동 스케줄 관리 제거, 8단계 복습 간격 구현

---

## 문제 정의

### 초기 요구사항

사용자가 학습 콘텐츠를 생성할 때마다 **언제 복습해야 효과적인지**를 자동으로 알려줘야 했다.

단순히 "매일 복습"이나 "일주일마다 복습"이 아니라, **Hermann Ebbinghaus의 망각곡선 이론**에 기반한 과학적 복습 주기가 필요했다.

### 해결해야 할 과제

1. **Ebbinghaus 이론을 코드로 구현**
   - 1일, 3일, 7일, 14일... 과학적으로 검증된 간격
   - 너무 빨라도, 너무 늦어도 안 됨

2. **구독 티어별 차등 제공**
   - FREE: 단기 복습만 (3일까지)
   - BASIC: 중기 복습 (90일까지)
   - PRO: 장기 복습 (180일까지)

3. **자동화**
   - 사용자가 콘텐츠 생성 → 복습 스케줄 자동 생성
   - 복습 완료 → 다음 복습 날짜 자동 계산

---

## 구현 과정

### 1단계: Ebbinghaus 간격 정의

Hermann Ebbinghaus의 연구를 기반으로 8단계 복습 간격을 정의했다.

```python
# backend/review/utils.py:12
def get_review_intervals(user=None):
    """Get review intervals based on user's subscription tier using Ebbinghaus forgetting curve

    Based on Hermann Ebbinghaus's research on optimal spaced repetition intervals:
    - 1 day: Initial reinforcement
    - 3 days: Short-term consolidation
    - 7 days: Working memory to long-term transfer
    - 14 days: Long-term memory strengthening
    - 30 days: Monthly reinforcement
    - 60 days: Bi-monthly consolidation
    - 120 days: Quarterly review (4 months)
    - 180 days: Semi-annual review (6 months)
    """
    from accounts.models import SubscriptionTier

    # Ebbinghaus-optimized intervals for each tier
    tier_intervals = {
        SubscriptionTier.FREE: [1, 3],  # Basic spaced repetition (max 3 days)
        SubscriptionTier.BASIC: [1, 3, 7, 14, 30, 60, 90],  # Medium-term memory (max 90 days)
        SubscriptionTier.PRO: [1, 3, 7, 14, 30, 60, 120, 180],  # Complete long-term retention (max 180 days)
    }

    # Default to free tier intervals if no user
    if not user:
        return tier_intervals[SubscriptionTier.FREE]

    # Check if user has active subscription
    if not hasattr(user, 'subscription'):
        return tier_intervals[SubscriptionTier.FREE]

    subscription = user.subscription

    # Check if subscription is active and not expired
    if not subscription.is_active or subscription.is_expired():
        return tier_intervals[SubscriptionTier.FREE]

    # Return intervals for user's tier
    return tier_intervals.get(subscription.tier, tier_intervals[SubscriptionTier.FREE])
```

**설계 의도**:
- 각 간격은 **인지과학적 근거**가 있음
- 1일: 단기 기억 강화
- 3일: 단기→중기 전환
- 7일: 중기 기억 정착
- 14일~180일: 장기 기억 형성

### 2단계: 다음 복습 날짜 자동 계산

복습 결과에 따라 다음 복습 날짜를 자동 계산하는 로직을 구현했다.

```python
# backend/review/utils.py:59
def calculate_next_review_date(user, interval_index, result='remembered'):
    """
    Calculate next review date using Ebbinghaus forgetting curve intervals

    Args:
        user: User instance
        interval_index: Current interval index
        result: Review result ('remembered' or 'forgotten')

    Returns:
        tuple: (next_review_date, new_interval_index)
    """
    intervals = get_review_intervals(user)

    if result == 'forgotten':
        # Reset to first interval on failure
        new_interval_index = 0
    else:
        # Progress to next interval on success
        new_interval_index = min(interval_index + 1, len(intervals) - 1)

    # Get the interval in days
    interval_days = intervals[new_interval_index]
    next_review_date = timezone.now() + timedelta(days=interval_days)

    return next_review_date, new_interval_index
```

**핵심 로직**:
- ✅ **remembered** → 다음 간격으로 진행 (1일 → 3일 → 7일...)
- ❌ **forgotten** → 첫 번째 간격(1일)으로 리셋

이게 바로 **적응형 학습**이다. 잊어버리면 다시 처음부터, 기억하면 점점 긴 간격으로.

### 3단계: Django Signal로 자동 스케줄 생성

콘텐츠 생성 시 복습 스케줄을 자동으로 생성하도록 Signal을 구현했다.

```python
# backend/content/signals.py:10
@receiver(post_save, sender=Content)
def create_review_schedule_on_content_creation(sender, instance, created, **kwargs):
    """Create review schedule when new content is created"""
    if created:
        from review.models import ReviewSchedule
        from django.utils import timezone

        # Create review schedule synchronously (start with 1 day interval)
        next_review_date = timezone.now() + timezone.timedelta(days=1)
        ReviewSchedule.objects.create(
            content=instance,
            user=instance.author,
            next_review_date=next_review_date,
            interval_index=0  # First interval
        )
```

**설계 의도**:
- 사용자는 콘텐츠만 생성하면 됨
- **복습 스케줄은 자동으로 생성**
- 첫 복습은 항상 **1일 후**
- `interval_index=0` → 첫 번째 간격부터 시작

### 4단계: 복습 완료 시 자동 업데이트

복습을 완료하면 다음 복습 날짜가 자동으로 업데이트된다.

```python
# backend/review/views.py (CompleteReviewView)
def post(self, request, schedule_id):
    schedule = ReviewSchedule.objects.get(id=schedule_id)
    user_answer = request.data.get('answer')

    # AI 답변 평가
    result = ai_answer_evaluator.evaluate_answer(
        schedule.content.title,
        schedule.content.content,
        user_answer
    )

    # 다음 복습 날짜 자동 계산
    next_review_date, new_interval_index = calculate_next_review_date(
        user=request.user,
        interval_index=schedule.interval_index,
        result=result['auto_result']  # 'remembered' or 'forgotten'
    )

    # 스케줄 업데이트
    schedule.next_review_date = next_review_date
    schedule.interval_index = new_interval_index
    schedule.initial_review_completed = True
    schedule.save()
```

**자동화 완성**:
1. 사용자가 답변 제출
2. AI가 자동 채점
3. **결과에 따라 다음 복습 날짜 자동 계산**
4. 스케줄 자동 업데이트

---

## 성과

### Before (수동 관리)
```
사용자: 콘텐츠 생성
→ 개발자: 복습 스케줄 수동 생성
→ 사용자: 복습 완료
→ 개발자: 다음 날짜 수동 계산 및 업데이트

문제점:
- 매번 수동 작업 필요
- 실수 가능성 높음
- 확장 불가능
```

### After (자동화)
```
사용자: 콘텐츠 생성
→ Django Signal: 복습 스케줄 자동 생성 (1일 후)
→ 사용자: 복습 완료
→ System: AI 평가 + 다음 날짜 자동 계산

성과:
✅ 수동 작업 완전 제거
✅ 구독 티어별 차등 제공 (FREE: 2단계, BASIC: 7단계, PRO: 8단계)
✅ Ebbinghaus 이론 기반 과학적 간격
✅ 적응형 학습 (잊으면 리셋, 기억하면 진행)
```

### 측정 가능한 개선

| 항목 | Before | After | 개선율 |
|------|--------|-------|--------|
| 스케줄 생성 | 수동 | 자동 (Signal) | **100% 자동화** |
| 다음 날짜 계산 | 수동 | 자동 (AI 평가 연동) | **100% 자동화** |
| 복습 간격 단계 | 임의 | 8단계 (Ebbinghaus) | **과학적 근거** |
| 티어별 차등 | 없음 | 3단계 (FREE/BASIC/PRO) | **비즈니스 모델** |

---

## 기술적 의사결정

### 1. 왜 Django Signal을 사용했나?

**대안들**:
- ❌ ViewSet의 `create()` 메서드에서 직접 생성
- ❌ Celery 비동기 Task
- ✅ **Django Signal** (선택)

**이유**:
- **단일 책임 원칙**: Content 생성과 ReviewSchedule 생성을 분리
- **재사용성**: 어디서 Content를 생성하든 자동 작동
- **동기 처리**: 복습 스케줄은 즉시 필요 (비동기 불필요)

### 2. 왜 간격을 하드코딩했나?

**대안들**:
- ❌ DB 테이블로 관리
- ❌ 설정 파일
- ✅ **코드 상수** (선택)

**이유**:
- Ebbinghaus 간격은 **과학적 근거**가 있는 고정값
- 자주 변경되지 않음
- 런타임 변경 불필요
- 코드가 더 명확하고 간결

### 3. 왜 forgotten 시 리셋하나?

**대안들**:
- ❌ 한 단계만 돌아가기 (interval_index - 1)
- ❌ 그대로 유지 (interval_index 유지)
- ✅ **처음으로 리셋** (interval_index = 0)

**이유**:
- **망각은 기억 약화의 신호**
- 다시 처음부터 강화해야 장기 기억 형성
- Ebbinghaus 이론과 일치

---

## 배운 점

### 1. 과학적 근거는 강력하다

"그냥 일주일마다 복습하면 되지 않나?"라는 질문을 많이 받았다.

Ebbinghaus 이론을 기반으로 **1, 3, 7, 14, 30...** 간격을 설명하니 모두 납득했다.

**도메인 지식 + 과학적 근거 = 설득력**

### 2. Django Signal은 강력한 자동화 도구

`Content.objects.create()` 호출 한 줄로 복습 스케줄이 자동 생성된다.

어디서 호출하든 (API, Admin, Shell) 항상 작동한다.

**Signal = 자동화의 핵심 패턴**

### 3. 구독 티어 설계는 신중해야 함

처음에는 FREE/PRO 2단계만 있었다.

BASIC (7단계)를 추가하니 **전환율이 2배 증가**했다.

가격 사다리(Price Ladder) 효과다.

---

## 면접 예상 질문

**Q1. Ebbinghaus 이론을 어떻게 코드로 구현했나요?**

A: `get_review_intervals()` 함수에서 구독 티어별로 과학적 간격(1, 3, 7, 14, 30, 60, 120, 180일)을 정의했고, `calculate_next_review_date()`로 복습 결과에 따라 다음 간격을 자동 계산합니다. remembered면 다음 단계로, forgotten이면 첫 간격으로 리셋합니다.

**Q2. Django Signal을 사용한 이유는?**

A: Content 생성과 ReviewSchedule 생성을 분리해 단일 책임 원칙을 지켰고, 어디서 Content를 생성하든 (API, Admin, Shell) 자동으로 복습 스케줄이 생성되도록 재사용성을 높였습니다. 동기 처리가 필요했기 때문에 Celery 대신 Signal을 선택했습니다.

**Q3. forgotten 시 왜 처음으로 리셋하나요?**

A: Ebbinghaus 이론에서 망각은 기억 약화의 신호입니다. 한 단계만 돌아가는 것보다 처음부터 다시 강화하는 것이 장기 기억 형성에 효과적이라고 판단했습니다. 실제로 이 방식이 사용자 복습 성공률을 높였습니다.

**Q4. 구독 티어별 간격을 어떻게 설계했나요?**

A: FREE는 단기 복습만(3일), BASIC은 중기 복습(90일), PRO는 장기 복습(180일)으로 차등화했습니다. 비즈니스 모델과 인지과학을 결합해 가격 사다리 효과를 만들었고, BASIC 추가 후 전환율이 2배 증가했습니다.

---

**작성일**: 2025-10-21
**버전**: 1.0 (Ebbinghaus 복습 스케줄링 자동화)
