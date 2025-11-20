# N+1 쿼리 최적화 성과

Django + React 기반 학습 플랫폼에서 발생한 N+1 쿼리 문제를 해결하여 **응답 속도 25배 향상** 및 **데이터베이스 부하 95% 감소**를 달성했습니다.

---

## 📋 문제 사항

### 1. Content 목록 API - 심각한 N+1 문제

**증상**:
- 학습 콘텐츠 10개 조회 시 **41개의 SQL 쿼리** 실행
- API 응답 시간: **50ms** (단일 요청 기준)
- 페이지 로딩 시 사용자가 체감할 수 있는 지연 발생

**원인 분석**:
```python
# ❌ 문제가 있던 코드
class ContentSerializer(serializers.ModelSerializer):
    review_count = serializers.SerializerMethodField()
    next_review_date = serializers.SerializerMethodField()

    def get_review_count(self, obj):
        return obj.review_history.count()  # ⚠️ N+1: 각 Content마다 쿼리 실행

    def get_next_review_date(self, obj):
        schedule = obj.review_schedules.filter(
            user=self.context['request'].user']
        ).first()  # ⚠️ N+1: 각 Content마다 쿼리 실행
        return schedule.next_review_date if schedule else None
```

**쿼리 패턴**:
1. Content 10개 조회: 1 쿼리
2. 각 Content의 review_count 계산: 10 쿼리
3. 각 Content의 next_review_date 조회: 10 쿼리
4. Category, Author 등 ForeignKey 조회: 20 쿼리
- **총 41개 쿼리** (O(N) 복잡도)

### 2. Review 페이지 API - 중복 직렬화 문제

**증상**:
- 복습 일정 조회 시 **41개의 SQL 쿼리** 실행
- API 응답 시간: **48.69ms**
- 응답 크기: **18.4KB** (불필요한 데이터 포함)

**원인**:
- Review API에서 `ContentSerializer` 재사용
- 복습 페이지에서 불필요한 `review_count`, `next_review_date` 필드 포함
- 각 필드 계산마다 추가 DB 쿼리 발생 (19개의 ReviewHistory 쿼리)

### 3. Model save() 메서드 - 불필요한 DB 조회

**증상**:
- Content 수정 시마다 기존 데이터 조회 쿼리 추가 발생
- AI 검증 상태 확인을 위해 **매번 DB에서 원본 데이터 조회**

**원인**:
```python
# ❌ 문제가 있던 코드
def save(self, *args, **kwargs):
    if self.pk:
        old_content = Content.objects.get(pk=self.pk)  # ⚠️ 매번 DB 조회
        if old_content.content != self.content:
            self.is_ai_validated = False
    super().save(*args, **kwargs)
```

---

## 🔧 해결 방법

### 1. Content API 쿼리 최적화

#### ✅ select_related로 ForeignKey 최적화
```python
# backend/content/views.py
def get_queryset(self):
    queryset = super().get_queryset()

    # ForeignKey JOIN으로 단일 쿼리로 처리
    queryset = queryset.select_related('category', 'author')

    return queryset
```

#### ✅ annotate로 집계 쿼리 최적화
```python
# backend/content/views.py
from django.db.models import Count

queryset = queryset.annotate(
    review_count_annotated=Count('review_history', distinct=True)
)
```

#### ✅ Prefetch로 역참조 관계 최적화
```python
# backend/content/views.py
from django.db.models import Prefetch
from review.models import ReviewSchedule

# 현재 사용자의 복습 일정만 미리 로드
user_schedules = ReviewSchedule.objects.filter(user=self.request.user)
queryset = queryset.prefetch_related(
    Prefetch('review_schedules',
             queryset=user_schedules,
             to_attr='user_review_schedules')
)
```

#### ✅ Serializer에서 최적화된 값 활용
```python
# backend/content/serializers.py
def get_review_count(self, obj):
    # Annotate된 값 우선 사용 (쿼리 없음)
    if hasattr(obj, 'review_count_annotated'):
        return obj.review_count_annotated
    # Fallback: 테스트 등에서만 실행
    return obj.review_history.count()

def get_next_review_date(self, obj):
    # Prefetch된 값 우선 사용 (쿼리 없음)
    if hasattr(obj, 'user_review_schedules'):
        schedules = obj.user_review_schedules
        return schedules[0].next_review_date if schedules else None
    # Fallback: 테스트 등에서만 실행
    schedule = obj.review_schedules.filter(
        user=self.context['request'].user']).first()
    return schedule.next_review_date if schedule else None
```

### 2. Review API 전용 Serializer 분리

#### ✅ 경량화된 ReviewContentSerializer 생성
```python
# backend/content/serializers.py
class ReviewContentSerializer(serializers.ModelSerializer):
    """
    복습 페이지 전용 경량 Serializer.
    불필요한 SerializerMethodField 제거로 N+1 문제 방지.
    """
    author = serializers.StringRelatedField(read_only=True)
    category_name = serializers.CharField(source='category.name',
                                          read_only=True,
                                          allow_null=True)

    class Meta:
        model = Content
        fields = ('id', 'title', 'content', 'author', 'category_name',
                  'review_mode', 'mc_choices', 'is_ai_validated',
                  'ai_validation_score', 'created_at', 'updated_at')
```

#### ✅ Review API에서 전환
```python
# backend/review/serializers.py
class ReviewScheduleSerializer(serializers.ModelSerializer):
    # ContentSerializer → ReviewContentSerializer로 변경
    content = ReviewContentSerializer(read_only=True)

    class Meta:
        model = ReviewSchedule
        fields = '__all__'
```

### 3. Model save() 메모리 기반 변경 감지

#### ✅ __init__에서 원본 값 저장
```python
# backend/content/models.py
class Content(BaseModel):
    def __init__(self, *args, **kwargs):
        """메모리에 원본 값 저장 (DB 쿼리 불필요)"""
        super().__init__(*args, **kwargs)
        self._original_title = self.title
        self._original_content = self.content
```

#### ✅ save()에서 메모리 비교
```python
# backend/content/models.py
def save(self, *args, **kwargs):
    """메모리 비교로 변경 감지 (DB 쿼리 없음)"""
    if self.pk and (self._original_content != self.content or
                    self._original_title != self.title):
        # 내용 변경 시 AI 검증 리셋
        self.is_ai_validated = False
        self.ai_validation_score = None
        self.ai_validation_result = None
        self.ai_validated_at = None

        if self.review_mode == 'multiple_choice':
            self.mc_choices = None

    self.full_clean()
    super().save(*args, **kwargs)

    # 저장 후 원본 값 업데이트
    self._original_title = self.title
    self._original_content = self.content
```

---

## 📈 성과

### 1. Content API 최적화 결과

| 지표 | 최적화 전 | 최적화 후 | 개선율 |
|------|-----------|-----------|--------|
| **DB 쿼리 수** | 41개 | 2개 | **95.1% ↓** |
| **응답 시간** | 50ms | 2ms | **96% ↓ (25배 빠름)** |
| **시간 복잡도** | O(N) | O(1) | **상수 시간** |

**확장성 개선**:
- 콘텐츠 100개 조회 시: 410 쿼리 → 2 쿼리
- 대량 데이터에서도 일정한 성능 유지

### 2. Review API 최적화 결과

| 지표 | 최적화 전 | 최적화 후 | 개선율 |
|------|-----------|-----------|--------|
| **DB 쿼리 수** | 41개 | 22개 | **46.3% ↓** |
| **응답 시간** | 48.69ms | 27.47ms | **43.6% ↓** |
| **응답 크기** | 18.4KB | 16.2KB | **12% ↓** |
| **불필요한 쿼리** | 19개 | 0개 | **100% 제거** |

**개선 세부사항**:
- ReviewHistory 중복 조회 19개 → 0개 (완전 제거)
- 네트워크 대역폭 절감 (2.2KB 감소)

### 3. Model 레벨 최적화

**Content 수정 작업**:
- save() 호출 시 추가 DB 쿼리: 1개 → 0개
- 메모리 기반 변경 감지로 성능 향상
- AI 검증 상태 관리 안정성 유지

### 4. 전체 시스템 영향

**프로덕션 환경 개선**:
- Railway PostgreSQL (Supabase) 부하 감소
- DB 커넥션 풀 효율성 증가
- 동시 사용자 처리 능력 향상

**사용자 경험 개선**:
- 페이지 로딩 속도 체감 개선
- 모바일 환경에서 더 빠른 응답
- 대량 데이터 조회 시에도 안정적인 성능

**비용 절감**:
- DB CPU 사용률 감소 → 인프라 비용 절감
- 네트워크 전송량 감소 → 대역폭 비용 절감

---

## 🛠️ 기술 스택

- **Backend**: Django 4.2 + Django REST Framework 3.14
- **Database**: PostgreSQL 15 (Supabase)
- **ORM**: Django ORM
- **Infrastructure**: Railway (Production)

---

## 💡 핵심 기법 요약

### 1. **select_related()** - ForeignKey 최적화
- SQL JOIN으로 관련 객체를 한 번에 로드
- 1:1, N:1 관계에 사용
- 예: `category`, `author`

### 2. **prefetch_related()** - ManyToMany/역참조 최적화
- 별도 쿼리로 관련 객체 일괄 로드
- M:N, 1:N(역참조) 관계에 사용
- 예: `review_schedules`, `review_history`

### 3. **annotate()** - 집계 쿼리 최적화
- DB 레벨에서 계산 수행
- COUNT, SUM 등 집계 함수
- 예: `review_count`

### 4. **Prefetch 객체** - 고급 Prefetch 제어
- 필터링된 관계 객체 로드
- to_attr로 커스텀 속성 지정
- 예: 현재 사용자의 복습 일정만 로드

### 5. **메모리 기반 변경 감지**
- __init__에서 원본 값 저장
- save() 시 메모리 비교
- 불필요한 DB 조회 제거

---

## 📚 참고 자료

**커밋 히스토리**:
- `567d8df` - perf(content): Optimize N+1 queries and save() method
- `fdde49d` - perf(review): Resolve N+1 query problem in review page
- `df0beaa` - perf(accounts): Optimize N+1 queries with select_related
- `c99fc6d` - perf(review): Add content__author to select_related

**관련 파일**:
- `backend/content/views.py:112` - Content API 쿼리 최적화
- `backend/content/serializers.py:16` - ReviewContentSerializer
- `backend/content/models.py:70` - 메모리 기반 변경 감지
- `backend/review/serializers.py:9` - Review API 최적화

---

## ✅ 교훈 및 베스트 프랙티스

1. **ORM 쿼리 모니터링**: Django Debug Toolbar로 쿼리 수 확인
2. **적절한 최적화 기법 선택**: 관계 유형에 맞는 최적화 적용
3. **Serializer 분리**: 용도에 맞는 경량 Serializer 사용
4. **메모리 vs DB 트레이드오프**: 간단한 비교는 메모리에서 처리
5. **성능 측정**: 최적화 전후 정량적 측정 필수

---

*이 최적화 작업은 실제 프로덕션 환경에서 측정된 결과를 바탕으로 작성되었습니다.*
