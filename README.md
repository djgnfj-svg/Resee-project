# 📚 Resee - 과학적 복습 플랫폼 v0.1

**에빙하우스 망각곡선에 기반한 스마트 복습 시스템**

Resee는 과학적으로 검증된 에빙하우스 망각곡선 이론을 활용하여 효율적인 학습과 장기 기억을 돕는 웹 플랫폼입니다.

## 🎯 v0.1 주요 개선사항

### ✨ 완성된 핵심 기능
- ✅ **Tiptap 리치 텍스트 에디터**: 마크다운 지원, 이미지 업로드, 풍부한 툴바
- ✅ **모던 UX/UI**: 그라디언트, 애니메이션, 반응형 디자인
- ✅ **플립 카드 복습**: 키보드 단축키, 진행률 표시, 실시간 타이머
- ✅ **고급 검색/필터**: 카테고리, 우선순위, 정렬, 실시간 필터 태그
- ✅ **에러 핸들링**: 전역 에러 바운더리, 토스트 알림, 네트워크 에러 처리
- ✅ **대시보드**: 히어로 섹션, 인터랙티브 차트, 통계 카드

### 🎮 키보드 단축키
- `Space`: 카드 뒤집기 (내용 보기/숨기기)
- `1`: 모름 - 첫 번째 간격으로 리셋
- `2`: 애매함 - 현재 간격 반복
- `3`: 기억함 - 다음 간격으로 진행

## ✨ 주요 기능

### 🧠 과학적 복습 시스템
- **에빙하우스 망각곡선** 기반 자동 복습 스케줄링
- **개인화된 복습 간격**: 1일 → 3일 → 7일 → 14일 → 30일
- **복습 결과 추적**: 기억함/애매함/모름 단계별 관리

### ✍️ Notion-style 에디터
- **Tiptap 기반** WYSIWYG 에디터
- **실시간 마크다운 렌더링**: `#` 입력 시 즉시 헤딩으로 변환
- **리치 포맷팅**: 헤딩, 리스트, 굵은 글씨, 기울임, 인용문, 코드 블록
- **자동 저장**: 2초마다 로컬 저장

### 📊 학습 관리
- **카테고리별 관리**: 영어, 수학, 경제 등 주제별 분류
- **사용자 맞춤 카테고리**: 개인별 카테고리 생성
- **우선순위 설정**: 높음/보통/낮음 중요도 관리
- **태그 시스템**: 세부 분류 및 검색

### 📈 통계 및 분석
- **복습 통계**: 일별/주별/월별 복습 현황
- **학습 진도**: 카테고리별 완료율
- **성과 분석**: 기억률 및 학습 패턴 추적

## 🛠️ 기술 스택

### Backend
- **Django 4.2** - 웹 프레임워크
- **Django REST Framework** - API 서버
- **PostgreSQL** - 메인 데이터베이스
- **Celery + RabbitMQ** - 비동기 작업 처리
- **JWT** - 인증 시스템

### Frontend
- **React 18** + **TypeScript** - 모던 프론트엔드
- **Tiptap** - WYSIWYG 에디터
- **React Query** - 서버 상태 관리
- **React Hook Form** - 폼 관리
- **Tailwind CSS** - 스타일링

### DevOps
- **Docker + Docker Compose** - 컨테이너화
- **PostgreSQL** - 데이터베이스
- **RabbitMQ** - 메시지 브로커

## 🚀 빠른 시작

### 필수 요구사항
- Docker & Docker Compose
- Git

### 1. 레포지토리 클론
```bash
git clone https://github.com/yourusername/resee.git
cd resee
```

### 2. 환경 변수 설정
```bash
cp .env.example .env
# .env 파일을 편집하여 필요한 설정 변경
```

### 3. Docker 컨테이너 실행
```bash
docker-compose up -d
```

### 4. 데이터베이스 마이그레이션
```bash
docker-compose exec backend python manage.py migrate
```

### 5. 슈퍼유저 생성
```bash
docker-compose exec backend python manage.py createsuperuser
```

### 6. 접속
- **프론트엔드**: http://localhost:3000
- **백엔드 API**: http://localhost:8000/api
- **API 문서 (Swagger)**: http://localhost:8000/swagger/
- **API 문서 (ReDoc)**: http://localhost:8000/redoc/
- **Django Admin**: http://localhost:8000/admin
- **RabbitMQ Management**: http://localhost:15672

## 📖 사용법

### 1. 회원가입 및 로그인
1. http://localhost:3000 접속
2. "회원가입" 버튼 클릭
3. 계정 정보 입력 후 가입
4. 로그인하여 대시보드 접속

### 2. 콘텐츠 작성
1. "새 콘텐츠 추가" 버튼 클릭
2. 제목과 내용 입력 (Notion처럼 마크다운 지원)
3. 카테고리 및 우선순위 설정
4. 저장

### 3. 복습하기
1. "복습하기" 메뉴 접속
2. 오늘 복습할 콘텐츠 확인
3. 내용을 복습한 후 기억 정도 선택
4. 시스템이 자동으로 다음 복습 일정 계산

### 4. 통계 확인
1. 대시보드에서 학습 현황 확인
2. 카테고리별 진도 및 성과 분석
3. 복습 패턴 분석

## 🎯 복습 시스템 원리

### 에빙하우스 망각곡선
Hermann Ebbinghaus의 연구에 따르면, 인간은 학습 후 시간이 지날수록 기억을 잃게 됩니다:
- 20분 후: 42% 기억
- 1시간 후: 56% 기억
- 1일 후: 74% 기억
- 1주일 후: 77% 기억

### Resee의 복습 간격
1. **1일 후** 첫 번째 복습
2. **3일 후** 두 번째 복습
3. **7일 후** 세 번째 복습
4. **14일 후** 네 번째 복습
5. **30일 후** 다섯 번째 복습

복습 시 "기억함"을 선택하면 다음 단계로, "모름"을 선택하면 1일 후 다시 복습하도록 스케줄링됩니다.

## 🗂️ 프로젝트 구조

```
resee/
├── backend/                 # Django 백엔드
│   ├── accounts/           # 사용자 관리
│   ├── content/            # 콘텐츠 관리
│   ├── review/             # 복습 시스템
│   ├── analytics/          # 통계 및 분석
│   └── resee/              # 프로젝트 설정
├── frontend/               # React 프론트엔드
│   ├── src/
│   │   ├── components/     # 재사용 컴포넌트
│   │   ├── pages/          # 페이지 컴포넌트
│   │   ├── contexts/       # React Context
│   │   ├── utils/          # 유틸리티 함수
│   │   └── types/          # TypeScript 타입
│   └── public/             # 정적 파일
└── docker-compose.yml      # Docker 설정
```

## 🔧 개발 환경

### 백엔드 개발
```bash
# 백엔드 컨테이너 접속
docker-compose exec backend bash

# 의존성 설치
pip install -r requirements.txt

# 테스트 실행
python manage.py test
pytest

# 코드 스타일 검사
flake8
black .
```

### 프론트엔드 개발
```bash
# 프론트엔드 컨테이너 접속
docker-compose exec frontend bash

# 의존성 설치
npm install

# 테스트 실행
npm test

# 빌드
npm run build
```

## 📋 API 문서

### 📖 인터랙티브 API 문서
- **Swagger UI**: http://localhost:8000/swagger/ - 인터랙티브 API 테스트
- **ReDoc**: http://localhost:8000/redoc/ - 깔끔한 API 문서 보기
- **JSON Schema**: http://localhost:8000/swagger.json - OpenAPI 스키마

### 🔐 인증 방법
1. `/api/auth/token/` 엔드포인트로 로그인
2. 받은 `access` 토큰을 헤더에 포함: `Authorization: Bearer <token>`

### 🎯 주요 엔드포인트

#### 인증
- `POST /api/auth/token/` - JWT 토큰 획득 (로그인)
- `POST /api/auth/token/refresh/` - 토큰 갱신
- `POST /api/accounts/users/register/` - 회원가입

#### 콘텐츠 관리
- `GET /api/content/contents/` - 콘텐츠 목록 (검색, 필터링, 정렬 지원)
- `POST /api/content/contents/` - 새 콘텐츠 생성
- `GET /api/content/contents/{id}/` - 콘텐츠 상세 조회
- `PUT /api/content/contents/{id}/` - 콘텐츠 수정
- `DELETE /api/content/contents/{id}/` - 콘텐츠 삭제
- `GET /api/content/contents/by_category/` - 카테고리별 콘텐츠 그룹화

#### 복습 시스템
- `GET /api/review/today/` - 오늘의 복습 목록
- `POST /api/review/complete/` - 복습 완료 및 스케줄 업데이트
- `GET /api/review/schedules/` - 복습 스케줄 관리
- `GET /api/review/history/` - 복습 기록 조회
- `GET /api/review/category-stats/` - 카테고리별 복습 통계

#### 카테고리 & 태그
- `GET /api/content/categories/` - 카테고리 목록
- `POST /api/content/categories/` - 새 카테고리 생성
- `GET /api/content/tags/` - 태그 목록
- `POST /api/content/tags/` - 새 태그 생성

#### 분석 & 대시보드
- `GET /api/analytics/dashboard/` - 대시보드 데이터
- `GET /api/analytics/review-stats/` - 상세 복습 통계

### 📸 파일 업로드
- `POST /api/content/upload-image/` - 이미지 업로드 (Tiptap 에디터용)
- `DELETE /api/content/delete-image/{filename}/` - 이미지 삭제

## 🧪 테스트

### 백엔드 테스트
```bash
# 전체 테스트 실행
docker-compose exec backend python manage.py test

# 특정 앱 테스트
docker-compose exec backend python manage.py test content

# 커버리지 포함 테스트
docker-compose exec backend pytest --cov=.
```

### 프론트엔드 테스트
```bash
# 유닛 테스트
docker-compose exec frontend npm test

# 테스트 커버리지
docker-compose exec frontend npm run test:coverage
```

## 🚀 배포

### 프로덕션 빌드
```bash
# 프론트엔드 빌드
docker-compose exec frontend npm run build

# 백엔드 정적 파일 수집
docker-compose exec backend python manage.py collectstatic
```

### 환경 변수 설정
프로덕션 환경에서는 다음 환경 변수들을 안전하게 설정해야 합니다:
- `SECRET_KEY`: Django 시크릿 키
- `DEBUG=False`: 디버그 모드 비활성화
- `DATABASE_URL`: 프로덕션 데이터베이스 URL
- `ALLOWED_HOSTS`: 허용된 호스트 목록

## 🤝 기여하기

1. 이 레포지토리를 Fork합니다
2. Feature 브랜치를 생성합니다 (`git checkout -b feature/AmazingFeature`)
3. 변경사항을 커밋합니다 (`git commit -m 'Add some AmazingFeature'`)
4. 브랜치에 Push합니다 (`git push origin feature/AmazingFeature`)
5. Pull Request를 생성합니다

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 있습니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 🏗️ 로드맵

### v1.1 (진행 중)
- [ ] 이미지 업로드 기능
- [ ] 모바일 반응형 개선
- [ ] 통계 대시보드 완성
- [ ] PWA 지원

### v1.2 (계획 중)
- [ ] 다크 모드
- [ ] 키보드 단축키
- [ ] 데이터 Export/Import
- [ ] 소셜 로그인

### v2.0 (향후)
- [ ] 협업 기능
- [ ] AI 기반 학습 추천
- [ ] 모바일 앱

## 📞 지원

문제가 있거나 질문이 있으시면 [GitHub Issues](https://github.com/yourusername/resee/issues)를 통해 문의해 주세요.

---

**Resee**로 더 스마트하게 학습하세요! 🚀