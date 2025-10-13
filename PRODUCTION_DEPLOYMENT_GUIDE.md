# 프로덕션 배포 가이드

## 자동 관리자 계정 생성

프로덕션 배포 시 자동으로 초기 관리자 계정이 생성됩니다.

### 환경변수 설정

`.env.prod` 파일에 다음 환경변수를 추가하세요:

```bash
# 관리자 계정 설정
ADMIN_EMAIL=djgnfj8923@naver.com
ADMIN_PASSWORD=your-secure-password-here
```

⚠️ **보안 주의사항**:
- `ADMIN_PASSWORD`는 반드시 강력한 비밀번호로 설정하세요
- 최소 12자 이상, 대소문자/숫자/특수문자 포함 권장
- `.env.prod` 파일은 절대 Git에 커밋하지 마세요

### 배포 프로세스

1. **환경변수 확인**
```bash
# .env.prod 파일 편집
vi .env.prod

# ADMIN_EMAIL과 ADMIN_PASSWORD 추가
ADMIN_EMAIL=djgnfj8923@naver.com
ADMIN_PASSWORD=YourSecurePassword123!@#
```

2. **배포 실행**
```bash
./deploy.sh
```

3. **자동 생성되는 계정**

배포 스크립트가 자동으로 다음 계정을 생성합니다:

| 항목 | 값 |
|------|-----|
| 이메일 | djgnfj8923@naver.com (또는 ADMIN_EMAIL 값) |
| 권한 | Superuser + Staff |
| 구독 티어 | PRO |
| 이메일 인증 | 자동 완료 |

### 배포 로그 확인

```bash
# 배포 중 로그에서 다음 메시지를 확인하세요:
📋 초기 관리자 계정 생성 중...
✅ Superuser created: djgnfj8923@naver.com
✅ 초기 사용자 설정 완료

============================================================
Initial users setup complete!
============================================================

Admin email: djgnfj8923@naver.com
Admin tier: PRO
Email verified: Yes

⚠️  Make sure to change the default password!
```

### 계정 확인

배포 완료 후 관리자 페이지에 로그인:

```
https://reseeall.com/admin/
```

### 비밀번호 변경

첫 로그인 후 반드시 비밀번호를 변경하세요:

1. 설정 → 보안 탭
2. 비밀번호 변경
3. 모든 디바이스에서 자동 로그아웃됨 (보안)

### 수동 관리자 계정 생성 (선택)

추가 관리자 계정이 필요한 경우:

```bash
docker-compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
```

### 트러블슈팅

#### 1. ADMIN_PASSWORD 미설정

```
❌ ADMIN_PASSWORD environment variable is required!
```

**해결**: `.env.prod`에 `ADMIN_PASSWORD` 추가

#### 2. 계정이 이미 존재

```
⚠️ Superuser already exists: djgnfj8923@naver.com
```

**해결**: 정상 동작입니다. `--skip-if-exists` 옵션으로 기존 계정 보호됨

#### 3. 수동으로 계정 생성

환경변수 없이 수동 생성:

```bash
# 로컬 테스트
docker-compose exec backend python manage.py create_initial_users

# 프로덕션
docker-compose -f docker-compose.prod.yml exec backend python manage.py create_initial_users
```

### GitHub Actions 자동 배포

GitHub Actions를 통한 배포 시 다음 Secret을 설정하세요:

1. **GitHub Repository → Settings → Secrets and variables → Actions**

2. **추가할 Secrets**:
   - `EC2_HOST`: EC2 서버 IP
   - `EC2_USER`: SSH 사용자명
   - `EC2_SSH_KEY`: SSH private key
   - `PROJECT_PATH`: 프로젝트 경로

3. **서버의 .env.prod 파일에 ADMIN_PASSWORD 설정**

```bash
# EC2 서버에서
cd /path/to/Resee-project
echo "ADMIN_PASSWORD=YourSecurePassword123!@#" >> .env.prod
```

### 보안 체크리스트

배포 전 확인사항:

- [ ] `ADMIN_PASSWORD`가 강력한 비밀번호로 설정됨
- [ ] `.env.prod` 파일이 `.gitignore`에 포함됨
- [ ] EC2 서버에서만 `.env.prod` 파일 존재
- [ ] GitHub Secrets에 민감한 정보 저장
- [ ] 첫 로그인 후 비밀번호 변경 계획

### 관리 명령어

```bash
# 사용자 목록 확인
docker-compose -f docker-compose.prod.yml exec backend python manage.py shell -c "
from accounts.models import User
for user in User.objects.all():
    print(f'{user.email} - Superuser: {user.is_superuser} - Tier: {user.subscription.tier}')
"

# 사용자 비밀번호 리셋
docker-compose -f docker-compose.prod.yml exec backend python manage.py changepassword djgnfj8923@naver.com

# 추가 PRO 계정 생성
docker-compose -f docker-compose.prod.yml exec backend python manage.py shell -c "
from accounts.models import User, Subscription
user = User.objects.create_user(
    email='another@example.com',
    password='password123',
    is_email_verified=True
)
Subscription.objects.create(user=user, tier='PRO', is_active=True)
print(f'Created: {user.email}')
"
```

### 프로덕션 체크리스트

최종 배포 전:

1. **환경변수**
   - [ ] `ADMIN_EMAIL` 설정됨
   - [ ] `ADMIN_PASSWORD` 강력한 비밀번호로 설정됨
   - [ ] 모든 필수 환경변수 검증됨

2. **보안**
   - [ ] HTTPS 설정 완료
   - [ ] 방화벽 규칙 설정
   - [ ] SSH 키 기반 인증
   - [ ] 비밀번호 정책 수립

3. **백업**
   - [ ] 데이터베이스 백업 전략 수립
   - [ ] 정기 백업 자동화

4. **모니터링**
   - [ ] 헬스체크 엔드포인트 확인
   - [ ] 로그 모니터링 설정
   - [ ] 에러 알림 설정

---

## 문의

배포 중 문제가 발생하면:
1. `docker-compose -f docker-compose.prod.yml logs` 확인
2. `deploy.sh` 로그 확인
3. GitHub Issues에 보고
