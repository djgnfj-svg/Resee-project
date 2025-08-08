# Gmail SMTP 이메일 설정 가이드

## 1. Gmail 계정 설정

### 1.1 2단계 인증 활성화
1. Google 계정 설정 접속: https://myaccount.google.com/security
2. "2단계 인증" 활성화

### 1.2 앱 비밀번호 생성
1. https://myaccount.google.com/apppasswords 접속
2. "앱 선택" → "메일" 선택
3. "기기 선택" → "기타(맞춤 이름)" 선택
4. "Resee Platform" 입력
5. 생성된 16자리 앱 비밀번호 복사 (띄어쓰기 제거)

## 2. Resee 프로젝트 설정

### 2.1 .env 파일 수정
```bash
# 이메일 설정
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-16-char-app-password  # 띄어쓰기 없이
DEFAULT_FROM_EMAIL=Resee Platform <your-email@gmail.com>
SERVER_EMAIL=your-email@gmail.com
```

### 2.2 Docker 재시작
```bash
docker-compose restart backend
docker-compose restart celery
```

## 3. 테스트

### 3.1 Django Shell에서 테스트
```bash
docker-compose exec backend python manage.py shell
```

```python
from django.core.mail import send_mail
send_mail(
    'Resee 테스트 이메일',
    '이메일 설정이 정상적으로 완료되었습니다!',
    'your-email@gmail.com',
    ['recipient@example.com'],
    fail_silently=False,
)
```

### 3.2 회원가입 테스트
1. http://localhost:3000/register 접속
2. 새 계정 생성
3. 이메일 인증 메일 수신 확인

## 4. 제한사항

### Gmail SMTP 제한
- 일일 전송 제한: 500통
- 분당 전송 제한: 20통
- 수신자 제한: 최대 100명/메일

### 권장사항
- 소규모 프로젝트: Gmail SMTP로 충분
- 중규모 이상: SendGrid, Mailgun 등 전문 서비스 사용
- 프로덕션: AWS SES 또는 전문 이메일 서비스 사용

## 5. 문제 해결

### 이메일이 발송되지 않는 경우
1. 앱 비밀번호 재확인 (공백 제거)
2. 2단계 인증 활성화 확인
3. "보안 수준이 낮은 앱 액세스" 확인 (필요시 허용)

### 스팸으로 분류되는 경우
1. SPF 레코드 설정 (도메인 있는 경우)
2. 이메일 내용에 스팸 키워드 피하기
3. DEFAULT_FROM_EMAIL에 적절한 이름 사용

## 6. 대체 무료 서비스

### Brevo (구 Sendinblue)
- 무료: 300통/일
- API 및 SMTP 지원
- 한국어 지원

### Resend
- 무료: 3000통/월
- 개발자 친화적
- 간단한 API

### MailerSend
- 무료: 12,000통/월
- 이메일 템플릿 지원
- 분석 기능 포함