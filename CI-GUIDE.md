# 🚀 CI 가이드

## 빠른 CI 체크

### 로컬에서 CI 상태 확인
```bash
# 전체 CI 체크 (추천)
./scripts/check-ci.sh

# 개별 체크
cd frontend && npm run ci:quick    # 프론트엔드만
cd backend && python manage.py check --deploy  # 백엔드만
```

### GitHub CI 상태

**Quick Check (2-3분)** ⚡
- ✅ Python 구문 검사
- ✅ Django 설정 검사  
- ✅ TypeScript 컴파일
- ✅ Frontend 빌드 테스트

**Full Test Suite (PR시 또는 `[full-test]` 태그시)** 🔬
- 🧪 Backend 테스트 실행
- 🧪 Frontend 테스트 실행
- 📊 코드 품질 검사
- 🐳 Docker 빌드 테스트

## CI 실패 시 해결 방법

### ❌ Python 구문 오류
```bash
cd backend
python -m py_compile $(find . -name "*.py" | head -10)
```

### ❌ Django 설정 오류  
```bash
cd backend
python manage.py check --deploy
```

### ❌ TypeScript 오류
```bash
cd frontend
npx tsc --noEmit --skipLibCheck
```

### ❌ Frontend 빌드 실패
```bash
cd frontend
npm run build
```

## 커밋 전 체크리스트

- [ ] `./scripts/check-ci.sh` 실행 ✅
- [ ] 새로운 기능은 테스트 추가 🧪
- [ ] 중요한 변경사항은 `[full-test]` 태그 추가
- [ ] PR 제목에 변경사항 명시

## CI 플로우

```
Push/PR → Quick Check (2-3분) → ✅ 성공시 merge 가능
                              → ❌ 실패시 수정 필요

PR 생성 → Full Test Suite (10-15분) → 전체 검증
```

## 팁

- **빠른 피드백**: 일반 push는 Quick Check만 실행
- **상세 검증**: PR은 Full Test Suite 자동 실행  
- **긴급 수정**: `git commit -m "fix: 긴급수정 [skip ci]"` (CI 스킵)
- **전체 테스트**: `git commit -m "feat: 새기능 [full-test]"` (전체 테스트 강제)

---

**문제 발생시**: 
1. 로컬에서 `./scripts/check-ci.sh` 먼저 실행
2. GitHub Actions 탭에서 상세 로그 확인
3. 해결 후 다시 push