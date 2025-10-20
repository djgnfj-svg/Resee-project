# Database NULL 제약 조건 에러 해결 회고

> 2025년 10월, IntegrityError와 씨름한 30분

## 개요

- **문제 발견**: 2025년 10월
- **해결 완료**: 같은 날 (30분 소요)
- **원인**: `blank=True`와 `null=True`의 차이를 몰랐음

---

## 문제 발견

복습 완료 버튼을 누르는 순간 500 에러가 발생했다.

```
django.db.utils.IntegrityError:
NOT NULL constraint failed: review_reviewhistory.ai_feedback
```

로그를 보니 `ai_feedback=None`을 저장하려다 실패한 것이었다.

---

## 원인 분석

문제는 모델 정의에 있었다.

```python
# backend/review/models.py (수정 전)
class ReviewHistory(models.Model):
    content = models.ForeignKey(Content, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    result = models.CharField(max_length=20)

    # 문제의 필드
    ai_feedback = models.TextField(blank=True, default='')
```

`blank=True`는 있지만 `null=True`는 없었다.

Django의 `blank`와 `null`은 완전히 다른 개념이었다.

### blank=True vs null=True

| 속성 | 작동 위치 | 의미 |
|------|-----------|------|
| `blank=True` | Django Form/Admin | "폼에서 비워도 돼" |
| `null=True` | Database | "DB에 NULL 저장해도 돼" |

실수한 부분:
```python
history = ReviewHistory(
    ai_feedback=None  # None을 넣었는데...
)
history.save()  # DB가 거부함
```

DB 입장에서는:
```sql
INSERT INTO review_reviewhistory (ai_feedback) VALUES (NULL);
-- ERROR: ai_feedback 컬럼은 NOT NULL 제약 조건 있음
```

---

## 해결 과정

### 1단계: 모델 수정

`null=True`를 추가했다.

```python
# backend/review/models.py (수정 후)
class ReviewHistory(models.Model):
    ai_feedback = models.TextField(
        blank=True,    # Form에서 비어있어도 OK
        null=True,     # DB에 NULL 저장 가능
        default=None   # 기본값을 None으로
    )
```

### 2단계: 마이그레이션 생성

```bash
$ python manage.py makemigrations

Migrations for 'review':
  review/migrations/0003_alter_reviewhistory_ai_feedback_and_more.py
    - Alter field ai_feedback on reviewhistory
```

생성된 마이그레이션을 확인했다:

```python
class Migration(migrations.Migration):
    operations = [
        migrations.AlterField(
            model_name='reviewhistory',
            name='ai_feedback',
            field=models.TextField(blank=True, null=True, default=None),
        ),
    ]
```

### 3단계: 마이그레이션 적용

```bash
$ python manage.py migrate

Running migrations:
  Applying review.0003_alter_reviewhistory_ai_feedback_and_more... OK
```

실행된 SQL:
```sql
-- PostgreSQL
ALTER TABLE review_reviewhistory
ALTER COLUMN ai_feedback DROP NOT NULL;
```

제약 조건을 풀기만 하니까 기존 데이터에 영향이 없어서 안전했다.

---

## 배운 점

### 1. blank와 null은 다른 레벨의 검증

```python
# 이 차이를 몸으로 배웠다

blank=True   # Django: "폼 검증 통과"
null=True    # PostgreSQL: "DB 제약 조건 통과"
```

### 2. TextField/CharField는 보통 null=True 안 쓴다

일반적인 패턴:
```python
# 권장
description = models.TextField(blank=True, default='')
# 빈 값은 '' (빈 문자열)로 통일

# 비권장 (혼란스러움)
description = models.TextField(blank=True, null=True)
# 빈 값이 '' 일수도 있고 None일 수도 있음
```

쿼리할 때도 복잡해진다:
```python
# null=True일 때
Content.objects.filter(description__isnull=True)  # NULL 찾기
Content.objects.filter(description='')            # 빈 문자열 찾기
# 둘 다 신경써야 함

# null=False일 때
Content.objects.filter(description='')            # 이것만
```

### 3. 진짜 NULL이 필요한 경우

내 경우처럼 **"아직 없음"**과 **"비어있음"**을 구분해야 할 때:

```python
ai_feedback = models.TextField(blank=True, null=True)

# None: AI 평가를 아직 안 함
# '': AI 평가를 했는데 피드백이 비어있음 (거의 없겠지만)
```

### 4. 마이그레이션은 안전하게

제약 조건 **완화**(null=True 추가)는 안전하지만,
제약 조건 **강화**(null=False 추가)는 기존 데이터 때문에 실패할 수 있다.

```python
# 안전
null=False → null=True  # 제약 풀기

# 위험
null=True → null=False  # 기존 NULL 데이터 있으면 실패
```

---

## 체크리스트

모델 필드 만들 때:

- [ ] 폼에서 필수 입력? → `blank=False` (기본값)
- [ ] 폼에서 선택 입력? → `blank=True`
- [ ] DB에 NULL 저장 필요? → `null=True`
- [ ] TextField/CharField면 `default=''` 쓰는게 나음
- [ ] 마이그레이션 생성 전에 기존 데이터 확인

---

## 관련 코드

- 수정한 모델: `backend/review/models.py`
- 마이그레이션: `backend/review/migrations/0003_alter_reviewhistory_ai_feedback_and_more.py`
- 커밋: `24f4d5b`

---

## 참고한 자료

- [Django 공식 문서: blank](https://docs.djangoproject.com/en/4.2/ref/models/fields/#blank)
- [Django 공식 문서: null](https://docs.djangoproject.com/en/4.2/ref/models/fields/#null)

---

## 정리

30분짜리 간단한 버그였지만, Django ORM의 중요한 개념을 배웠다.
앞으로 필드 만들 때 습관적으로 "blank? null?" 생각하게 될 것이다.

**다음에 적용할 점**:
- TextField는 기본적으로 `blank=True, default=''`
- NULL이 정말 필요한지 한 번 더 생각하기
