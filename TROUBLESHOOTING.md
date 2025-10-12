# Resee 트러블슈팅 가이드

이 문서는 Resee 프로젝트에서 발생한 주요 이슈와 해결 방법을 기록합니다.

---

## 목차

1. [React Query 캐시 무효화 타이밍 이슈](#1-react-query-캐시-무효화-타이밍-이슈)

---

## 1. React Query 캐시 무효화 타이밍 이슈

### 증상
- 새 콘텐츠를 생성하거나 편집한 후 콘텐츠 목록 페이지로 돌아가면 방금 생성/수정한 콘텐츠가 보이지 않음
- 페이지를 새로고침하면 정상적으로 표시됨
- 동일한 문제가 콘텐츠 생성과 편집 모두에서 발생

### 근본 원인

**문제 코드** (CreateContentPage.tsx, EditContentPage.tsx):
```typescript
onSuccess: () => {
  alert('Success: 콘텐츠가 성공적으로 생성되었습니다!');
  queryClient.invalidateQueries({ queryKey: ['contents'] });      // await 없음!
  queryClient.invalidateQueries({ queryKey: ['dashboard'] });     // await 없음!
  navigate('/content');  // 즉시 실행됨
}
```

**타이밍 이슈 분석**:
1. `invalidateQueries`는 비동기 함수이지만 `await`하지 않음
2. `navigate('/content')`가 캐시 무효화 완료 전에 즉시 실행됨
3. ContentPage가 mount될 때 아직 무효화되지 않은 캐시 데이터를 읽음
4. 결과: 이전 데이터가 그대로 표시됨

**React Query 동작**:
- `invalidateQueries({ queryKey: ['contents'] })`는 기본적으로 prefix matching 사용
- `['contents']`로 시작하는 모든 쿼리 키를 무효화함
- ContentPage의 `['contents', selectedCategory, sortBy, searchQuery]`도 포함됨
- 하지만 무효화는 비동기로 처리되므로 완료 시점을 보장하려면 `await` 필요

### 해결 방법

**수정된 코드**:
```typescript
onSuccess: async () => {  // async 추가
  alert('Success: 콘텐츠가 성공적으로 생성되었습니다!');
  await queryClient.invalidateQueries({ queryKey: ['contents'] });      // await 추가
  await queryClient.invalidateQueries({ queryKey: ['dashboard'] });     // await 추가
  navigate('/content');  // 캐시 무효화 완료 후 실행
}
```

### 관련 파일
- `frontend/src/pages/CreateContentPage.tsx` (Line 33)
- `frontend/src/pages/EditContentPage.tsx` (Line 24)
- `frontend/src/pages/ContentPage.tsx` (Line 23 - queryKey 정의)

### 재현 방법
1. 로그인 후 콘텐츠 목록 페이지 접속
2. 현재 콘텐츠 개수 확인 (예: 12개)
3. "새 콘텐츠" 클릭
4. 제목과 내용 입력 후 "저장"
5. 콘텐츠 목록 페이지로 리다이렉트
6. **버그 있음**: 새 콘텐츠가 목록에 보이지 않음 (여전히 12개)
7. **수정 후**: 새 콘텐츠가 목록 맨 위에 즉시 표시됨 (13개)

### 검증 방법
```bash
# Playwright를 사용한 자동화 테스트
1. 콘텐츠 목록 페이지 접속
2. 콘텐츠 개수 저장
3. 새 콘텐츠 생성
4. 리다이렉트 후 콘텐츠 목록 확인
5. 새 콘텐츠가 맨 위에 있는지 검증
6. 콘텐츠 개수가 1 증가했는지 검증
```

### 예방 팁

**일반 원칙**:
```typescript
// ❌ 잘못된 패턴
onSuccess: () => {
  queryClient.invalidateQueries({ queryKey: ['data'] });
  navigate('/list');  // 캐시 무효화 전에 이동
}

// ✅ 올바른 패턴
onSuccess: async () => {
  await queryClient.invalidateQueries({ queryKey: ['data'] });
  navigate('/list');  // 캐시 무효화 후 이동
}
```

**체크리스트**:
- [ ] mutation 후 페이지 이동이 있는가?
- [ ] invalidateQueries를 사용하는가?
- [ ] onSuccess가 async로 선언되었는가?
- [ ] invalidateQueries에 await를 사용했는가?
- [ ] 이동한 페이지가 무효화된 쿼리를 사용하는가?

### 참고 자료
- [React Query v4 Invalidation Docs](https://tanstack.com/query/v4/docs/react/guides/query-invalidation)
- [useMutation onSuccess Callback](https://tanstack.com/query/v4/docs/react/reference/useMutation)
- Commit: `10c8ee1` - fix: Await cache invalidation before navigation in content mutations

### 디버깅 팁

**문제 진단**:
```typescript
// 캐시 무효화 로깅 추가
onSuccess: async () => {
  console.log('Before invalidation');
  await queryClient.invalidateQueries({ queryKey: ['contents'] });
  console.log('After invalidation');
  navigate('/content');
  console.log('After navigation');
}
```

**React Query DevTools 사용**:
```bash
# React Query DevTools에서 확인할 사항
1. Query Key 구조 확인
2. Stale Time 및 Cache Time 확인
3. Invalidation 이벤트 타이밍 확인
4. Refetch 트리거 확인
```

---

## 문서 업데이트 가이드

새로운 트러블슈팅 케이스를 추가할 때는 다음 구조를 따라주세요:

```markdown
## N. [이슈 제목]

### 증상
- 사용자가 경험하는 문제 설명

### 근본 원인
- 기술적 원인 분석
- 문제 코드 예시

### 해결 방법
- 수정된 코드
- 단계별 해결 과정

### 관련 파일
- 파일 경로와 라인 번호

### 재현 방법
1. 단계별 재현 방법

### 검증 방법
- 테스트 방법

### 예방 팁
- 유사한 문제 예방 방법

### 참고 자료
- 관련 문서 링크
- Commit 해시
```
