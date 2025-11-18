# SEO 설정 가이드

Resee 프로젝트의 검색 엔진 최적화(SEO) 설정이 완료되었습니다.

## 📋 완료된 작업

### 1. ✅ robots.txt
- **위치:** `public/robots.txt`
- **기능:** 검색 엔진 크롤러 가이드
- **설정:**
  - 모든 검색 엔진 허용
  - `/api/`, `/admin/`, `/settings/`, `/profile/` 제외
  - Sitemap 위치 명시

### 2. ✅ sitemap.xml
- **위치:** `public/sitemap.xml`
- **기능:** 사이트 구조 정보
- **포함된 페이지:**
  - `/` (홈페이지) - Priority: 1.0
  - `/login` - Priority: 0.8
  - `/register` - Priority: 0.8
  - `/terms` - Priority: 0.5
  - `/privacy` - Priority: 0.5

**업데이트 주기:**
- 새로운 공개 페이지 추가 시 sitemap.xml 업데이트 필요

### 3. ✅ SEO Meta Tags (index.html)
- Description (향상된 설명)
- Keywords (핵심 키워드)
- Author
- Robots (index, follow)
- Canonical URL
- Language

### 4. ✅ Open Graph Tags (소셜 미디어)
- Facebook, LinkedIn 등 SNS 공유 시 표시
- 제목, 설명, 이미지, URL 포함

### 5. ✅ Twitter Card Tags
- Twitter 공유 시 카드 형태로 표시
- Large image 형식 사용

### 6. ✅ PWA Manifest 개선
- 상세 설명 추가
- Shortcuts 추가 (복습, 콘텐츠 추가, 대시보드)
- Favicon 아이콘 연결

---

## 🚨 추가로 해야 할 작업

### 1. Open Graph 이미지 생성 (필수)
현재 `og-image.png`가 `index.html`에 참조되어 있지만 실제 파일이 없습니다.

**생성 방법:**
1. 1200 x 630 픽셀 이미지 제작
2. Resee 로고 + 슬로건 포함
3. `public/og-image.png`로 저장

**온라인 도구:**
- https://www.canva.com (무료)
- https://www.figma.com (무료)
- https://www.crello.com (무료)

**이미지 예시 내용:**
```
[Resee 로고]
과학적 복습 플랫폼
에빙하우스 망각곡선 기반 스마트 학습
```

### 2. Google Search Console 등록
1. https://search.google.com/search-console 방문
2. 속성 추가: `https://reseeall.com`
3. 소유권 확인:
   - **HTML 태그 방법:** 제공된 메타 태그를 `index.html`의 37번 줄에 추가
   ```html
   <meta name="google-site-verification" content="YOUR_VERIFICATION_CODE" />
   ```
4. Sitemap 제출: `https://reseeall.com/sitemap.xml`

### 3. Naver 검색 어드바이저 (이미 완료)
- ✅ 네이버 사이트 인증 완료 (meta tag 이미 추가됨)
- Sitemap 제출: https://searchadvisor.naver.com
  - 사이트 관리 → 요청 → 사이트맵 제출
  - URL: `https://reseeall.com/sitemap.xml`

### 4. Google Analytics 설정 (선택사항)
이미 GA 스크립트가 `index.html`에 있지만 환경 변수 설정이 필요합니다.

**Vercel 환경 변수 설정:**
```bash
REACT_APP_GA_MEASUREMENT_ID=G-XXXXXXXXXX
```

1. Google Analytics 계정 생성: https://analytics.google.com
2. 속성 추가 → 측정 ID 받기 (G-XXXXXXXXXX)
3. Vercel 대시보드 → Settings → Environment Variables
4. 변수 추가: `REACT_APP_GA_MEASUREMENT_ID`

### 5. 추가 아이콘 생성 (선택사항)
PWA를 위한 다양한 사이즈의 아이콘:
- 192x192 (Android)
- 512x512 (Android)
- 180x180 (iOS)
- 152x152 (iPad)

**생성 도구:**
- https://realfavicongenerator.net
- https://favicon.io

생성 후 `public/icons/` 폴더에 저장하고 `manifest.json` 업데이트

---

## 📊 SEO 성능 확인

### 1. Google PageSpeed Insights
https://pagespeed.web.dev
- URL 입력: `https://reseeall.com`
- 모바일/데스크톱 성능 점수 확인

### 2. Open Graph Preview
https://www.opengraph.xyz
- URL 입력: `https://reseeall.com`
- 소셜 미디어 공유 미리보기 확인

### 3. Twitter Card Validator
https://cards-dev.twitter.com/validator
- URL 입력: `https://reseeall.com`
- 트위터 카드 미리보기 확인

### 4. 구조화된 데이터 테스트
https://search.google.com/test/rich-results
- URL 입력: `https://reseeall.com`
- 구조화된 데이터 오류 확인

---

## 🔍 검색 엔진별 등록 체크리스트

- [ ] Google Search Console 등록
- [ ] Google Analytics 연동
- [x] Naver Search Advisor 등록 (완료)
- [ ] Bing Webmaster Tools 등록 (선택)
- [ ] Open Graph 이미지 제작
- [ ] 각 검색 엔진에 Sitemap 제출

---

## 📝 유지보수

### Sitemap 업데이트 시기
- 새로운 공개 페이지 추가 시
- 주요 페이지 URL 변경 시
- 우선순위(priority) 조정 필요 시

**업데이트 방법:**
```xml
<!-- sitemap.xml에 새 URL 추가 -->
<url>
  <loc>https://reseeall.com/NEW_PAGE</loc>
  <lastmod>YYYY-MM-DD</lastmod>
  <changefreq>weekly</changefreq>
  <priority>0.7</priority>
</url>
```

### 검색 엔진 재색인 요청
Google Search Console에서:
1. URL 검사 도구 사용
2. 색인 생성 요청

---

## 🎯 SEO 최적화 팁

1. **메타 설명 최적화**
   - 현재: "에빙하우스 망각곡선 기반 과학적 복습 플랫폼..."
   - 155자 이하로 유지
   - 핵심 키워드 포함

2. **페이지 제목 최적화**
   - 형식: `페이지명 | Resee - 과학적 복습 플랫폼`
   - 60자 이하 권장

3. **이미지 최적화**
   - Alt 텍스트 추가
   - WebP 포맷 사용
   - 압축하여 용량 최소화

4. **모바일 친화성**
   - 반응형 디자인 확인
   - 터치 타겟 크기 확인
   - 폰트 크기 적정성

5. **페이지 속도**
   - Code splitting 활용 (이미 적용됨)
   - 이미지 lazy loading
   - CDN 활용

---

## 🔗 유용한 링크

- [Google Search Central](https://developers.google.com/search)
- [Naver 검색 최적화 가이드](https://searchadvisor.naver.com/guide)
- [Open Graph Protocol](https://ogp.me/)
- [Twitter Cards](https://developer.twitter.com/en/docs/twitter-for-websites/cards)
- [PWA Checklist](https://web.dev/pwa-checklist/)

---

**마지막 업데이트:** 2025-01-18
