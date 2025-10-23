# React Query Cache Leak Fix

## 문제 (Problem)

사용자가 로그아웃 후 다른 계정으로 로그인했을 때, 이전 사용자의 데이터가 화면에 표시되는 심각한 보안 및 UX 문제가 발생했습니다.

**재현 단계**:
1. testuser1@test.com으로 로그인
2. 프로필 페이지 접속 (React Query 캐시에 testuser1 데이터 저장)
3. 로그아웃
4. testuser2@test.com으로 로그인
5. **문제**: 화면에 testuser1의 이름과 이메일이 표시됨

## 원인 분석 (Root Cause)

### 1. React Query 캐시 키 구조
```typescript
// frontend/src/pages/ProfilePage.tsx:13
const { data: user } = useQuery<User>({
  queryKey: ['profile'],  // ❌ 사용자 ID가 포함되지 않음
  queryFn: authAPI.getProfile,
});
```

- 캐시 키에 사용자 ID가 없어서 **모든 사용자가 같은 캐시를 공유**
- testuser1의 데이터가 캐시에 저장되면, testuser2가 로그인해도 같은 키로 조회

### 2. 로그아웃 시 캐시 미삭제
```typescript
// frontend/src/contexts/AuthContext.tsx:115-119 (수정 전)
const logout = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  setUser(null);
  // ❌ React Query 캐시를 지우지 않음
};
```

### 3. 백엔드는 정상 동작
```bash
# API 호출 결과 (정상)
{
  "id": 8,
  "email": "testuser2@test.com",
  "username": null
}
```
- 백엔드는 JWT 토큰 기반으로 올바른 사용자 데이터 반환
- 문제는 **순수 프론트엔드 캐시 이슈**

## 해결 방법 (Solution)

### 로그아웃 시 React Query 캐시 전체 삭제

```typescript
// frontend/src/contexts/AuthContext.tsx
import { useQueryClient } from '@tanstack/react-query';

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const queryClient = useQueryClient();

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
    // ✅ 모든 React Query 캐시 삭제 (데이터 유출 방지)
    queryClient.clear();
  };
};
```

## 성과 (Impact)

| 항목 | Before | After |
|-----|--------|-------|
| **보안** | 다른 사용자 데이터 노출 | 완전 차단 |
| **UX** | 잘못된 사용자 정보 표시 | 정확한 정보 표시 |
| **캐시 관리** | 수동 무효화 필요 | 자동 정리 |

## 파일 수정 (Files Changed)

- `frontend/src/contexts/AuthContext.tsx`: logout 함수에 `queryClient.clear()` 추가

## 테스트 (Testing)

1. testuser1로 로그인 → 프로필 확인
2. 로그아웃
3. testuser2로 로그인 → 프로필 확인
4. ✅ testuser2의 정보가 정확하게 표시됨

## 관련 이슈 (Related Issues)

- 사용자 보고: "3795로 로그인했는데 8923 이름이 나와요"
- 스크린샷: `.playwright-mcp/cache-bug-testuser2-shows-testuser1.png`

**작성일**: 2025-10-23
**키워드**: React Query, Cache Leak, Security, User Data Isolation
