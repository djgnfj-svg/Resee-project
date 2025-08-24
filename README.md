# 📚 Resee - 과학적 복습 플랫폼

**에빙하우스 망각곡선에 기반한 스마트 복습 시스템**

Resee는 과학적으로 검증된 에빙하우스 망각곡선 이론을 활용하여 효율적인 학습과 장기 기억을 돕는 웹 플랫폼입니다.

## 🚀 빠른 시작

```bash
# 프로젝트 시작
docker-compose up -d

# 접속
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/api
```

## ✨ 주요 기능

- **🧠 과학적 복습 시스템**: 에빙하우스 망각곡선 기반 자동 스케줄링
- **✍️ Notion-style 에디터**: Tiptap 기반 리치 텍스트 에디터  
- **📊 학습 관리**: 카테고리별 관리, 우선순위 설정
- **📈 통계 및 분석**: 복습 현황, 학습 패턴 추적
- **🎮 키보드 단축키**: `Space` (카드 뒤집기), `1-3` (복습 결과)

## 📖 상세 문서

프로젝트의 상세한 개발 가이드, 아키텍처, API 문서 등은 **[CLAUDE.md](./CLAUDE.md)**를 참고하세요.

## 🛠️ 기술 스택

**Backend**: Django 4.2, PostgreSQL, Redis, RabbitMQ, Celery  
**Frontend**: React 18, TypeScript, TailwindCSS, TipTap Editor  
**Infrastructure**: Docker, Docker Compose

## 🧪 테스트 계정

자동으로 생성되는 테스트 계정으로 바로 시작할 수 있습니다:

- **관리자**: `admin@resee.com` / `admin123!`
- **테스트 사용자**: `test@resee.com` / `test123!`
- **데모 계정**: `demo@resee.com` / `demo123!`

## 🔄 CI/CD

이 프로젝트는 GitHub Actions를 통해 자동화된 CI/CD 파이프라인을 제공합니다:

### 🚀 자동 실행 (모든 push/PR)
- **Quick Check**: Django 설정 검증, TypeScript 컴파일, 빌드 테스트
- **Code Quality**: 코드 포맷팅, 린팅, 보안 검사

### 🧪 조건부 실행
특별한 키워드를 커밋 메시지에 포함하면 추가 테스트가 실행됩니다:

- **`[test]`**: 전체 테스트 스위트 실행 (backend + frontend)
- **`[docker]`**: Docker 통합 테스트 실행
- **Pull Request**: 모든 테스트 자동 실행

### 📊 테스트 커버리지
- **Backend**: 280개 테스트 메서드로 85%+ 커버리지
- **Frontend**: React Testing Library + 70% 커버리지 기준
- **통합 테스트**: Docker 컨테이너 전체 스택 검증

### ⚡ 빠른 피드백
- Quick Check: ~5분 (핵심 검증만)
- Full Test Suite: ~12분 (모든 테스트)
- Docker Integration: ~15분 (전체 스택)

## 📞 지원

문제가 있거나 질문이 있으시면 [GitHub Issues](https://github.com/yourusername/resee/issues)를 통해 문의해 주세요.

