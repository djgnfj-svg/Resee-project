# 복습 카운터 로직 문제 분석

## 문제 발견

사용자가 주관식 복습에서 "다음으로" 버튼을 클릭할 때, 상단의 카운터가 제대로 증가하지 않는 문제 발견.

## 현재 카운터 로직 분석

### 1. 정상 동작: 객관식 모드
```typescript
// useReviewLogic.ts:131-141
if (variables.result === 'remembered') {
  setReviewsCompleted(prev => prev + 1);  // ✅ 카운터 증가
  removeCurrentCard();
  queryClient.invalidateQueries({ queryKey: ['dashboard'] });
  if (onShowToast) {
    onShowToast('잘 기억하고 있어요!', 'success');
  }
}
```

### 2. 문제 발견: 주관식 모드

#### Step 1: AI 평가 제출 (정상)
```typescript
// useReviewLogic.ts:120-128
if (variables.descriptive_answer && variables.descriptive_answer.length > 0) {
  setReviewsCompleted(prev => prev + 1);  // ✅ 카운터 증가 (1회)
  queryClient.invalidateQueries({ queryKey: ['dashboard'] });
  return;  // ⚠️ 여기서 종료 - 카드 이동 안함
}
```

#### Step 2: "다음으로" 버튼 클릭 (문제)
```typescript
// ReviewPage.tsx:101-115
const handleNextSubjective = useCallback(() => {
  if (aiEvaluation?.auto_result === 'remembered') {
    removeCurrentCard();  // ❌ reviewsCompleted 증가 없음
    showToast('잘 기억하고 있어요!', 'success');
  } else {
    moveCurrentCardToEnd();  // ❌ reviewsCompleted 증가 없음
    showToast('괜찮아요, 나중에 다시 시도해보세요!', 'info');
  }

  // 상태 초기화만 함
  setAiEvaluation(null);
  setDescriptiveAnswer('');
  setSubmittedAnswer('');
}, [aiEvaluation, removeCurrentCard, moveCurrentCardToEnd, showToast]);
```

### 3. 카운터 계산 로직
```typescript
// useReviewLogic.ts:183-184
const totalTodayReviews = reviews.length + reviewsCompleted;
const progress = totalTodayReviews > 0 ? (reviewsCompleted / totalTodayReviews) * 100 : 0;
```

## 문제 요약

주관식 복습 플로우:
1. 사용자가 답변 제출 → `setReviewsCompleted(prev => prev + 1)` 실행 ✅
2. AI 평가 결과 표시 → 카드 이동 없음 ✅
3. 사용자가 "다음으로" 클릭 → **카운터 증가 없이** 카드 이동/제거만 실행 ❌

**결과**:
- 실제 완료한 복습: N개
- 표시되는 카운터: N-1개 (AI 평가 제출 시점의 카운터에서 멈춤)

## 해결 방법 (제안 - 수정하지 않음)

### Option 1: "다음으로" 버튼에서 카운터 제거
주관식은 AI 평가 제출 시점에 이미 카운터를 증가시켰으므로, "다음으로"에서는 카드 이동만 처리.

**장점**: 로직이 명확함
**단점**: 사용자가 "다음으로" 누를 때 카운터가 안 올라가서 혼란스러울 수 있음

### Option 2: AI 평가 제출 시 카운터 증가 제거
```typescript
// useReviewLogic.ts:120-128 수정
if (variables.descriptive_answer && variables.descriptive_answer.length > 0) {
  // setReviewsCompleted(prev => prev + 1);  // ❌ 제거
  queryClient.invalidateQueries({ queryKey: ['dashboard'] });
  return;
}

// ReviewPage.tsx:101-115 수정
const handleNextSubjective = useCallback(() => {
  if (aiEvaluation?.auto_result === 'remembered') {
    setReviewsCompleted(prev => prev + 1);  // ✅ 여기서 증가
    removeCurrentCard();
    showToast('잘 기억하고 있어요!', 'success');
  } else {
    moveCurrentCardToEnd();
    showToast('괜찮아요, 나중에 다시 시도해보세요!', 'info');
  }
  // ... 상태 초기화
}, [...]);
```

**장점**: 객관식과 동일한 UX (버튼 클릭 시 카운터 증가)
**단점**: "모름" 선택 시 카운터가 증가하지 않음 (의도된 동작이지만 혼란 가능)

### Option 3: 모든 경우에 카운터 증가
```typescript
const handleNextSubjective = useCallback(() => {
  setReviewsCompleted(prev => prev + 1);  // ✅ 무조건 증가

  if (aiEvaluation?.auto_result === 'remembered') {
    removeCurrentCard();
  } else {
    moveCurrentCardToEnd();
  }
  // ... 상태 초기화
}, [...]);

// useReviewLogic.ts에서는 주관식 카운터 증가 제거
```

**장점**: 사용자가 "다음으로" 누를 때마다 카운터 증가 (직관적)
**단점**: "모름" 선택 시에도 카운터가 증가 (실제로는 완료가 아님)

## 권장 해결 방법

**Option 2**를 권장합니다.
- 객관식과 동일한 UX 제공
- "기억함" 선택 시에만 카운터 증가 (논리적으로 올바름)
- "모름" 선택 시 카드가 맨 뒤로 이동하며 카운터는 유지

## 추가 개선사항

### 정답 입력창 크기 확대
```typescript
// ReviewCard.tsx:75 (수정 완료 ✅)
rows={10}  // 6 → 10으로 증가
```

**작성일**: 2025-10-23
**상태**: 분석 완료, 수정 대기
**키워드**: Review Counter, Subjective Mode, UX Bug
