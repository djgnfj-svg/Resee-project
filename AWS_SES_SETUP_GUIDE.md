# AWS SES 설정 가이드

## 📧 AWS SES로 실제 이메일 발송 설정하기

### 1단계: AWS 계정 및 IAM 설정

#### 1.1 AWS 계정 생성
- [AWS 콘솔](https://console.aws.amazon.com)에 로그인
- 신용카드 등록 필요 (무료 사용량 내에서는 과금 없음)

#### 1.2 IAM 사용자 생성
1. **IAM 콘솔** → **사용자** → **사용자 추가**
2. **사용자 이름**: `resee-email-service`
3. **액세스 유형**: 프로그래밍 방식 액세스 선택
4. **권한 설정**: 기존 정책 연결
   - `AmazonSESFullAccess` 선택 (개발용)
   - 또는 세부 권한 설정 (프로덕션용)
5. **액세스 키 ID**와 **비밀 액세스 키** 저장 ⚠️

### 2단계: SES 설정

#### 2.1 SES 콘솔 접속
- [AWS SES 콘솔](https://console.aws.amazon.com/ses/)
- **지역 선택**: 서울 (ap-northeast-2) 권장

#### 2.2 이메일 주소 인증 (개발/테스트용)
1. **Identities** → **Create Identity**
2. **Email address** 선택
3. 발신자 이메일 입력: `noreply@yourdomain.com`
4. **Create Identity** 클릭
5. **인증 이메일 확인** (해당 이메일함에서 확인링크 클릭)

#### 2.3 도메인 인증 (프로덕션용 - 권장)
1. **Identities** → **Create Identity**
2. **Domain** 선택
3. 도메인 입력: `yourdomain.com`
4. **DNS 레코드 설정** (도메인 관리자 필요):
   ```
   Type: CNAME
   Name: _amazonses.yourdomain.com
   Value: [AWS에서 제공하는 값]
   ```

### 3단계: 환경변수 설정

#### 3.1 .env 파일 생성
`.env.aws` 파일을 생성하고 실제 값으로 대체:

```bash
# AWS SES 이메일 발송 설정
EMAIL_BACKEND=django_ses.SESBackend

# AWS 자격증명
AWS_ACCESS_KEY_ID=AKIA1234567890EXAMPLE
AWS_SECRET_ACCESS_KEY=your-secret-access-key-here

# AWS SES 지역 (서울)
AWS_SES_REGION_NAME=ap-northeast-2
AWS_SES_REGION_ENDPOINT=email.ap-northeast-2.amazonaws.com

# 발신자 이메일 (인증된 이메일)
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

# 기타 설정
FRONTEND_URL=http://localhost
EMAIL_VERIFICATION_TIMEOUT_DAYS=7
```

#### 3.2 Docker Compose 환경변수 적용
```bash
# .env.aws 파일 사용
cp .env.aws .env

# Docker 재시작
docker-compose down
docker-compose up -d
```

### 4단계: 테스트

#### 4.1 이메일 발송 테스트
```bash
# Django shell에서 테스트
docker-compose exec -T backend python manage.py shell -c "
from django.core.mail import send_mail
from django.conf import settings

result = send_mail(
    subject='SES 테스트',
    message='AWS SES 연동 테스트 이메일입니다.',
    from_email=settings.DEFAULT_FROM_EMAIL,
    recipient_list=['your-test-email@gmail.com'],
    fail_silently=False,
)
print(f'이메일 발송 결과: {result}')
"
```

#### 4.2 회원가입 이메일 테스트
```bash
# API로 테스트 회원가입
curl -X POST http://localhost:8000/api/accounts/users/register/ \\
  -H "Content-Type: application/json" \\
  -d '{
    "email": "test@yourdomain.com",
    "password": "test123!",
    "password_confirm": "test123!",
    "first_name": "Test",
    "last_name": "User"
  }'
```

### 5단계: 프로덕션 설정

#### 5.1 샌드박스 모드 해제
- **기본**: SES는 샌드박스 모드 (인증된 이메일만 발송 가능)
- **프로덕션**: 샌드박스 해제 신청 필요
- **신청 방법**: SES 콘솔 → **Account dashboard** → **Request production access**

#### 5.2 발송 한도 증가 신청
- **기본 한도**: 24시간에 200통, 초당 1통
- **증가 신청**: AWS Support 케이스 생성

### 6단계: 모니터링

#### 6.1 SES 대시보드 확인
- **Send statistics**: 발송 통계
- **Reputation metrics**: 평판 지표
- **Bounce and complaint notifications**: 반송/불만 알림

#### 6.2 CloudWatch 모니터링
- 이메일 발송량, 반송률, 불만률 모니터링
- 알람 설정으로 이상 상황 감지

## 🚨 주의사항

### 보안
- **액세스 키 보안**: .env 파일을 절대 커밋하지 말 것
- **최소 권한 원칙**: IAM 사용자에게 필요한 최소 권한만 부여
- **키 로테이션**: 정기적으로 액세스 키 교체

### 비용 관리
- **무료 사용량**: 매월 62,000통 무료
- **과금 방식**: 1,000통당 $0.10 (아시아 태평양 서울 기준)
- **비용 알림**: CloudWatch로 비용 알림 설정

### 이메일 전달률
- **평판 관리**: 반송률 5% 미만, 불만률 0.1% 미만 유지
- **콘텐츠 품질**: 스팸 필터에 걸리지 않도록 주의
- **수신자 리스트 관리**: 유효하지 않은 이메일 정기 정리

## 🔧 트러블슈팅

### 자주 발생하는 문제

1. **AccessDenied 오류**
   - IAM 권한 확인
   - AWS 자격증명 확인

2. **MessageRejected 오류**
   - 이메일 주소/도메인 인증 상태 확인
   - 샌드박스 모드 확인

3. **이메일이 스팸함에 들어가는 경우**
   - SPF, DKIM, DMARC 레코드 설정
   - 이메일 내용 및 발신자 평판 확인

4. **발송 속도 제한**
   - AWS Support에 발송 한도 증가 요청
   - 발송 속도 조절 (throttling)

## ✅ 설정 완료 체크리스트

- [ ] AWS 계정 생성
- [ ] IAM 사용자 생성 및 키 발급
- [ ] SES 이메일/도메인 인증
- [ ] 환경변수 설정 (.env 파일)
- [ ] Docker 재시작
- [ ] 테스트 이메일 발송 확인
- [ ] 회원가입 이메일 테스트
- [ ] 샌드박스 해제 신청 (프로덕션)
- [ ] 모니터링 설정