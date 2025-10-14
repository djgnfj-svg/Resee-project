# 배포 가이드

**Resee 프로젝트 배포 문서 모음**

---

## 🚀 빠른 시작

### 자동 배포 (GitHub Actions) - 권장

```bash
git push origin main  # 이것만으로 자동 배포!
```

**설정 방법**: [CD_SETUP_GUIDE.md](./CD_SETUP_GUIDE.md)

---

## 📚 문서 목록

### 1. [CD_SETUP_GUIDE.md](./CD_SETUP_GUIDE.md) - CI/CD 설정 ⭐
GitHub Actions로 자동 배포 환경 구축하기
- SSH 키 생성 및 등록
- GitHub Secrets 설정
- 4단계 설정 가이드
- 트러블슈팅

### 2. [PRODUCTION_DEPLOYMENT_GUIDE.md](./PRODUCTION_DEPLOYMENT_GUIDE.md) - 프로덕션 배포
프로덕션 환경 배포 세부 사항
- 자동 관리자 계정 생성
- 환경변수 설정
- 배포 스크립트 사용법
- 배포 후 확인사항

### 3. [SECURITY_SUMMARY.md](./SECURITY_SUMMARY.md) - 보안 개선 사항
최근 완료된 보안 수정 요약
- 이메일 토큰 해싱
- JWT 블랙리스트
- 타이밍 공격 방어

### 4. [CACHE_FIX_GUIDE.md](./CACHE_FIX_GUIDE.md) - 캐시 문제 해결
Service Worker 캐시 문제 분석 및 해결
- 문제 원인 분석
- 해결 방법
- 테스트 가이드

### 5. [CLAUDE.md](./CLAUDE.md) - 프로젝트 가이드
개발 시 참고할 프로젝트 전체 정보
- 아키텍처 개요
- 주요 파일 위치
- 개발 명령어
- 테스트 계정

---

## ⚡ 빠른 참고

### 현재 배포 상태

```bash
# 서비스 상태 확인
docker-compose -f docker-compose.prod.yml ps

# 로그 확인
docker-compose -f docker-compose.prod.yml logs -f

# 최신 커밋 확인
git log -1
```

### 주요 URL

- **프로덕션**: https://reseeall.com
- **API 헬스체크**: https://reseeall.com/api/health/
- **관리자**: https://reseeall.com/admin/

### 관리자 계정

- **이메일**: djgnfj8923@naver.com
- **비밀번호**: `.env.prod`의 `ADMIN_PASSWORD`

---

## 🆘 문제 발생 시

### 1. 배포 실패
→ [CD_SETUP_GUIDE.md](./CD_SETUP_GUIDE.md) 트러블슈팅 섹션

### 2. 캐시 문제
→ [CACHE_FIX_GUIDE.md](./CACHE_FIX_GUIDE.md) 해결 방법

### 3. 보안 이슈
→ [SECURITY_SUMMARY.md](./SECURITY_SUMMARY.md) 확인

### 4. 기타
→ [CLAUDE.md](./CLAUDE.md) 개발 가이드 참고

---

## 📝 수동 배포 (백업용)

자동 배포가 작동하지 않을 때만 사용:

```bash
# EC2 접속
ssh ubuntu@your-ec2-ip

# 프로젝트 디렉토리
cd /home/ubuntu/Resee-project

# 최신 코드 가져오기
git pull origin main

# 배포 실행
./deploy.sh
```

**소요 시간**: 약 5-10분

---

**업데이트**: 2025-10-14
