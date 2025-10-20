# Bare Except 안티패턴 제거 회고

> 2025년 10월, 디버깅을 어렵게 만드는 `except:` 제거하기

## 개요

- **문제 발견**: 2025년 10월
- **해결 완료**: 같은 날 (1시간 소요)
- **원인**: Bare except가 모든 예외를 무조건 잡아서 실제 에러를 숨김

---

## 문제 발견

코드 리뷰 중 4곳에서 `except:` (bare except)를 발견했다.

```python
# backend/review/backup_tasks.py:96
try:
    slack_notifier.send_alert(...)
except:
    pass  # 😱 모든 예외를 무시!
```

문제는 이게 **모든 예외**를 잡는다는 것이다. 심지어 `KeyboardInterrupt`, `SystemExit` 같은 것도.

---

## 왜 문제인가?

### 1. 디버깅이 불가능해진다

```python
# 실제 상황
try:
    from utils.slack_notifications import slack_notifier  # 오타!
    slack_notifier.send_alert(...)
except:
    pass  # ImportError를 무시하고 그냥 넘어감
```

Slack 알림이 안 가는데 이유를 모른다. 로그도 없고, 예외도 안 터진다.

### 2. 심각한 예외도 잡는다

```python
except:  # 이게 잡는 것들:
    # - KeyboardInterrupt (Ctrl+C)
    # - SystemExit (sys.exit())
    # - MemoryError
    # - 심지어 SyntaxError도!
```

서버를 강제로 종료하려는데 안 된다면? Bare except 때문일 수 있다.

### 3. 코드 스멜 (Code Smell)

```python
except:
    pass  # "나 이 코드 뭐하는지 모르겠어요" 라고 말하는 것
```

---

## 원인 분석

### 발견된 4곳

| 파일 | 라인 | 문제 |
|------|------|------|
| `review/backup_tasks.py` | 96 | Slack 알림 실패를 무시 |
| `content/serializers.py` | 98 | 컨텍스트 에러를 무시 |
| `resee/settings/__init__.py` | 39 | SECRET_KEY 검증 실패 무시 |
| `resee/settings/__init__.py` | 58 | Production 검증 실패 무시 |

### 각각의 실제 문제

**1. backup_tasks.py:96**
```python
# 문제: Slack 알림이 왜 안 가는지 모름
except:
    pass
```

**2. serializers.py:98**
```python
# 문제: request.user가 없는 이유를 모름 (테스트? 인증 실패?)
except:
    return None
```

**3. settings/__init__.py:39, 58**
```python
# 문제: 프로덕션 환경 검증이 실패해도 모름
except:
    pass  # 또는 return warnings
```

---

## 해결 과정

### 1단계: backup_tasks.py 수정

**Before**:
```python
try:
    from utils.slack_notifications import slack_notifier
    slack_notifier.send_alert(...)
except:
    pass  # 😱
```

**After**:
```python
try:
    from utils.slack_notifications import slack_notifier
    slack_notifier.send_alert(...)
except Exception as slack_error:
    logger.warning(f"Failed to send Slack notification: {slack_error}")
```

**개선 사항**:
- `Exception`을 명시 → `KeyboardInterrupt` 등은 안 잡힘
- 에러를 변수로 받아서 로깅
- `logger.warning()` 추가 → 나중에 디버깅 가능

---

### 2단계: serializers.py 수정

**Before**:
```python
def get_next_review_date(self, obj):
    try:
        schedule = obj.review_schedules.filter(user=self.context['request'].user).first()
        return schedule.next_review_date if schedule else None
    except:
        return None  # 왜 실패했는지 모름
```

**After**:
```python
def get_next_review_date(self, obj):
    try:
        schedule = obj.review_schedules.filter(user=self.context['request'].user).first()
        return schedule.next_review_date if schedule else None
    except (KeyError, AttributeError) as e:
        # KeyError: 'request' not in context (e.g., during tests)
        # AttributeError: request.user not available
        logger.warning(f"Failed to get next_review_date for content {obj.id}: {e}")
        return None
```

**개선 사항**:
- **구체적인 예외 명시**: `KeyError`, `AttributeError`만 잡음
- **주석으로 설명**: 왜 이 예외가 발생하는지
- **로깅 추가**: content ID와 함께 에러 기록

---

### 3단계: settings/__init__.py 수정

**Before**:
```python
def validate_environment():
    warnings = []
    try:
        secret_key = globals().get('SECRET_KEY', '')
    except:
        return warnings  # 검증 실패를 숨김
```

**After**:
```python
def validate_environment():
    warnings = []
    try:
        secret_key = globals().get('SECRET_KEY', '')
    except Exception as e:
        warnings.append(f"WARNING: Failed to get SECRET_KEY for validation: {e}")
        return warnings
```

**Before (두 번째)**:
```python
if environment == 'production':
    try:
        if globals().get('DEBUG'):
            warnings.append("CRITICAL: DEBUG=True in production environment!")
        # ...
    except:
        pass  # 프로덕션 검증 실패를 무시!
```

**After**:
```python
if environment == 'production':
    try:
        if globals().get('DEBUG'):
            warnings.append("CRITICAL: DEBUG=True in production environment!")
        # ...
    except Exception as e:
        warnings.append(f"WARNING: Failed to validate production settings: {e}")
```

**개선 사항**:
- 검증 실패를 `warnings`에 추가 → 사용자에게 알림
- 로깅으로 디버깅 가능

---

## 테스트

```bash
# 수정 후 테스트 실행
docker-compose exec backend python -m pytest

# 결과: 40/41 passing (기존과 동일, bare except 수정으로 인한 영향 없음)
```

---

## 배운 점

### 1. Bare except는 절대 쓰지 말자

```python
# ❌ 나쁨
except:
    pass

# ❌ 여전히 나쁨
except:
    return None

# ✅ 좋음
except Exception as e:
    logger.warning(f"Failed to do something: {e}")

# ✅ 더 좋음 (구체적인 예외)
except (KeyError, AttributeError) as e:
    logger.warning(f"Context error: {e}")
```

### 2. Exception vs BaseException

Python 예외 계층:
```
BaseException
├── KeyboardInterrupt  ← 사용자가 Ctrl+C 누름
├── SystemExit         ← sys.exit() 호출
├── GeneratorExit
└── Exception          ← 일반적인 예외들
    ├── ValueError
    ├── KeyError
    ├── ImportError
    └── ...
```

**결론**:
- `except Exception`: 일반적인 예외만 잡음 (대부분의 경우 이걸 써야 함)
- `except:` (bare except): **모든 것**을 잡음 (쓰면 안 됨)

### 3. 구체적인 예외를 잡는 게 최선

```python
# 가장 좋음: 예상되는 예외만 잡기
try:
    value = some_dict['key']
except KeyError:
    value = default_value

# 좋음: 관련된 예외들 묶기
try:
    response = requests.get(url)
    data = response.json()
except (requests.RequestException, ValueError) as e:
    logger.error(f"API call failed: {e}")

# 괜찮음: Exception으로 폴백 (하지만 로깅 필수!)
try:
    complex_operation()
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise  # 다시 발생시키기

# 나쁨: 모든 예외 무시
except Exception:
    pass

# 최악: Bare except
except:
    pass
```

### 4. 예외를 무시하려면 이유를 남기자

```python
# ✅ 좋음: 왜 무시하는지 설명
try:
    slack_notifier.send_alert(...)
except Exception as e:
    # Slack 알림 실패는 중요하지 않음 (optional feature)
    # 하지만 나중을 위해 로깅은 남김
    logger.debug(f"Optional Slack notification failed: {e}")

# ❌ 나쁨: 이유 없이 무시
except Exception:
    pass
```

### 5. 로깅 레벨 선택

| 레벨 | 언제 쓰는가 | 예시 |
|------|------------|------|
| `DEBUG` | 개발 중 상세 정보 | 쿼리 실행 시간 |
| `INFO` | 정상 동작 확인 | 사용자 로그인 |
| `WARNING` | 주의 필요 (하지만 동작 가능) | Slack 알림 실패 |
| `ERROR` | 에러 발생 (기능 동작 안 함) | DB 연결 실패 |
| `CRITICAL` | 심각한 에러 (서버 다운 위험) | 메모리 부족 |

---

## 체크리스트

코드 리뷰 시 확인할 것:

- [ ] Bare except (`except:`) 사용하지 않았는가?
- [ ] `Exception` 대신 구체적인 예외를 잡을 수 있는가?
- [ ] 예외를 잡았다면 로깅했는가?
- [ ] 로깅 레벨이 적절한가? (DEBUG/INFO/WARNING/ERROR/CRITICAL)
- [ ] 주석으로 왜 이 예외가 발생하는지 설명했는가?
- [ ] `pass`로 무시하는 경우, 정말 무시해도 되는가?

---

## 관련 코드

- 수정한 파일:
  * `backend/review/backup_tasks.py:96`
  * `backend/content/serializers.py:98`
  * `backend/resee/settings/__init__.py:39, 58`
- 커밋: (다음 단계에서 생성)

---

## 참고한 자료

- [PEP 8 - Programming Recommendations](https://peps.python.org/pep-0008/#programming-recommendations)
- [Python 공식 문서 - Built-in Exceptions](https://docs.python.org/3/library/exceptions.html)
- [Real Python - Python Exceptions: An Introduction](https://realpython.com/python-exceptions/)

---

## 정리

1시간 동안 4곳의 bare except를 수정했다.

**변경 사항**:
- 모든 bare except를 구체적인 예외 처리로 변경
- 로깅 추가로 디버깅 가능하게 개선
- 주석으로 예외 발생 이유 설명

**다음에 적용할 점**:
- 코드 작성 시 처음부터 구체적인 예외 명시
- `except Exception` 도 가능하면 피하고 구체적인 예외 타입 사용
- 예외를 무시할 때는 반드시 로깅과 주석 추가
- 코드 리뷰 시 bare except 체크

**신입 개발자를 위한 조언**:
> "예외를 잡았다면, 그 예외를 어떻게 처리할지 알고 있어야 합니다.
> 모르겠다면 잡지 마세요. 그냥 터뜨려서 로그를 보는 게 낫습니다."
