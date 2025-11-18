import React, { useState, useCallback, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
  Alert,
  Animated,
} from 'react-native';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { reviewAPI } from '../../api/review';
import { useTheme } from '../../contexts/ThemeContext';
import { ReviewSchedule, TodayReviewsResponse } from '../../types';
import MarkdownContent from '../../components/common/MarkdownContent';

const ReviewScreen = () => {
  const { colors } = useTheme();
  const queryClient = useQueryClient();

  // State
  const [localReviews, setLocalReviews] = useState<ReviewSchedule[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [showContent, setShowContent] = useState(false);
  const [isFlipped, setIsFlipped] = useState(false);
  const [startTime, setStartTime] = useState(Date.now());
  const [reviewsCompleted, setReviewsCompleted] = useState(0);
  const [totalSchedules, setTotalSchedules] = useState(0);

  // Review mode state
  const [descriptiveAnswer, setDescriptiveAnswer] = useState('');
  const [selectedChoice, setSelectedChoice] = useState('');
  const [userTitle, setUserTitle] = useState('');
  const [aiEvaluation, setAiEvaluation] = useState<{
    score: number;
    feedback: string;
    auto_result?: 'remembered' | 'forgot';
    is_correct?: boolean;
  } | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Animation
  const flipAnim = useState(new Animated.Value(0))[0];

  // Fetch today's reviews
  const { data: reviewData, isLoading } = useQuery({
    queryKey: ['todayReviews'],
    queryFn: () => reviewAPI.getTodayReviews(''),
  });

  // Extract reviews from response
  useEffect(() => {
    if (reviewData) {
      let reviews: ReviewSchedule[];
      let totalCount = 0;

      if (Array.isArray(reviewData)) {
        reviews = reviewData;
        totalCount = reviewData.length;
      } else if ('results' in reviewData) {
        const response = reviewData as TodayReviewsResponse;
        reviews = response.results;
        totalCount = response.total_count || 0;
      } else {
        reviews = [];
      }

      setLocalReviews([...reviews]);
      setTotalSchedules(totalCount);
      setReviewsCompleted(0);
    }
  }, [reviewData]);

  // Complete review mutation
  const completeReviewMutation = useMutation({
    mutationFn: ({
      scheduleId,
      data,
    }: {
      scheduleId: number;
      data: {
        result?: 'remembered' | 'partial' | 'forgot';
        time_spent?: number;
        descriptive_answer?: string;
        selected_choice?: string;
        user_title?: string;
      };
    }) => reviewAPI.completeReview(scheduleId, data),
  });

  const currentReview = localReviews[currentIndex];
  const remainingReviews = localReviews.length;
  const progress =
    totalSchedules > 0 ? (reviewsCompleted / totalSchedules) * 100 : 0;

  // Reset review state
  const resetReviewState = useCallback(() => {
    setIsFlipped(false);
    setShowContent(false);
    setStartTime(Date.now());
    setDescriptiveAnswer('');
    setSelectedChoice('');
    setUserTitle('');
    setAiEvaluation(null);
    setIsSubmitting(false);
  }, []);

  // Remove current card (remembered)
  const removeCurrentCard = useCallback(() => {
    if (localReviews.length > 0) {
      const newReviews = [...localReviews];
      newReviews.splice(currentIndex, 1);
      setLocalReviews(newReviews);

      if (currentIndex >= newReviews.length && newReviews.length > 0) {
        setCurrentIndex(0);
      }

      resetReviewState();
    }
  }, [localReviews, currentIndex, resetReviewState]);

  // Move current card to end (forgot)
  const moveCurrentCardToEnd = useCallback(() => {
    if (localReviews.length === 1) {
      resetReviewState();
    } else if (localReviews.length > 1) {
      const newReviews = [...localReviews];
      const currentCard = newReviews.splice(currentIndex, 1)[0];
      newReviews.push(currentCard);
      setLocalReviews(newReviews);
      resetReviewState();
    }
  }, [localReviews, currentIndex, resetReviewState]);

  // Flip card animation
  const flipCard = useCallback(() => {
    Animated.timing(flipAnim, {
      toValue: isFlipped ? 0 : 180,
      duration: 300,
      useNativeDriver: true,
    }).start();
    setIsFlipped(!isFlipped);
    setShowContent(!showContent);
  }, [isFlipped, showContent, flipAnim]);

  // Handle complete review
  const handleReviewComplete = useCallback(
    async (
      result: 'remembered' | 'partial' | 'forgot' | null,
      descriptive?: string,
      choice?: string,
      title?: string
    ) => {
      if (!currentReview) return;

      const timeSpent = Math.floor((Date.now() - startTime) / 1000);

      try {
        const response = await completeReviewMutation.mutateAsync({
          scheduleId: currentReview.id,
          data: {
            result: result || undefined,
            time_spent: timeSpent,
            descriptive_answer: descriptive || '',
            selected_choice: choice || '',
            user_title: title || '',
          },
        });

        return response;
      } catch (error) {
        Alert.alert('오류', '복습 완료 처리에 실패했습니다.');
        throw error;
      }
    },
    [currentReview, startTime, completeReviewMutation]
  );

  // 1. Objective mode: 기억 확인
  const handleObjectiveComplete = useCallback(
    async (result: 'remembered' | 'partial' | 'forgot') => {
      try {
        await handleReviewComplete(result, '', '', '');

        if (result === 'remembered') {
          setReviewsCompleted((prev) => prev + 1);
          removeCurrentCard();
          Alert.alert('성공', '잘 기억하고 있어요!');
        } else {
          moveCurrentCardToEnd();
          Alert.alert('알림', '괜찮아요, 나중에 다시 시도해보세요!');
        }
      } catch (error) {
        // Error already handled
      }
    },
    [handleReviewComplete, removeCurrentCard, moveCurrentCardToEnd]
  );

  // 2. Descriptive mode: 제목 보고 내용 작성 → AI 평가
  const handleSubmitDescriptive = useCallback(async () => {
    if (!currentReview || descriptiveAnswer.length < 10) {
      Alert.alert('알림', '답변을 10자 이상 작성해주세요.');
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await handleReviewComplete(
        null,
        descriptiveAnswer,
        '',
        ''
      );

      if (response && response.ai_evaluation) {
        setAiEvaluation(response.ai_evaluation);
        const resultText =
          response.ai_evaluation.auto_result === 'remembered'
            ? '기억함'
            : '모름';
        Alert.alert(
          'AI 평가',
          `${Math.round(response.ai_evaluation.score)}점 - ${resultText}\n\n${response.ai_evaluation.feedback}`
        );
      }

      setIsFlipped(true);
      setShowContent(true);
    } catch (error) {
      // Error already handled
    } finally {
      setIsSubmitting(false);
    }
  }, [currentReview, descriptiveAnswer, handleReviewComplete]);

  // 3. Multiple Choice mode: 내용 보고 제목 선택
  const handleSubmitMultipleChoice = useCallback(async () => {
    if (!currentReview || !selectedChoice) {
      Alert.alert('알림', '답을 선택해주세요.');
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await handleReviewComplete(null, '', selectedChoice, '');

      if (response && response.ai_evaluation) {
        setAiEvaluation(response.ai_evaluation);
        const isCorrect = response.ai_evaluation.score === 100;
        Alert.alert(
          isCorrect ? '정답!' : '오답',
          response.ai_evaluation.feedback
        );
      }

      setIsFlipped(true);
      setShowContent(true);
    } catch (error) {
      // Error already handled
    } finally {
      setIsSubmitting(false);
    }
  }, [currentReview, selectedChoice, handleReviewComplete]);

  // 4. Subjective mode: 내용 보고 제목 유추 → AI 평가
  const handleSubmitSubjective = useCallback(async () => {
    if (!currentReview || userTitle.length < 2) {
      Alert.alert('알림', '제목을 2자 이상 입력해주세요.');
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await handleReviewComplete(null, '', '', userTitle);

      if (response && response.ai_evaluation) {
        setAiEvaluation(response.ai_evaluation);
        const resultText =
          response.ai_evaluation.auto_result === 'remembered'
            ? '기억함'
            : '모름';
        Alert.alert(
          'AI 평가',
          `${Math.round(response.ai_evaluation.score)}점 - ${resultText}\n\n${response.ai_evaluation.feedback}`
        );
      }

      setIsFlipped(true);
      setShowContent(true);
    } catch (error) {
      // Error already handled
    } finally {
      setIsSubmitting(false);
    }
  }, [currentReview, userTitle, handleReviewComplete]);

  // AI 평가 후 다음으로
  const handleNextAfterEvaluation = useCallback(() => {
    if (
      aiEvaluation?.auto_result === 'remembered' ||
      aiEvaluation?.is_correct
    ) {
      setReviewsCompleted((prev) => prev + 1);
      removeCurrentCard();
    } else {
      moveCurrentCardToEnd();
    }
  }, [aiEvaluation, removeCurrentCard, moveCurrentCardToEnd]);

  // Render loading
  if (isLoading) {
    return (
      <View style={[styles.centerContainer, { backgroundColor: colors.background }]}>
        <ActivityIndicator size="large" color={colors.primary} />
        <Text style={[styles.loadingText, { color: colors.textSecondary }]}>
          오늘의 복습을 불러오는 중...
        </Text>
      </View>
    );
  }

  // Render completed
  if (!currentReview) {
    return (
      <View style={[styles.centerContainer, { backgroundColor: colors.background }]}>
        <Text style={styles.emojiText}>🎉</Text>
        <Text style={[styles.completedTitle, { color: colors.text }]}>
          복습 완료!
        </Text>
        <Text style={[styles.completedSubtitle, { color: colors.textSecondary }]}>
          오늘 예정된 모든 복습을 완료했습니다!
        </Text>
      </View>
    );
  }

  const reviewMode = currentReview.content.review_mode;
  const isObjectiveMode = reviewMode === 'objective';
  const isDescriptiveMode = reviewMode === 'descriptive';
  const isMultipleChoiceMode = reviewMode === 'multiple_choice';
  const isSubjectiveMode = reviewMode === 'subjective';

  return (
    <ScrollView style={[styles.container, { backgroundColor: colors.background }]}>
      {/* Header */}
      <View style={[styles.header, { backgroundColor: colors.card, borderBottomColor: colors.border }]}>
        <View style={styles.headerRow}>
          <Text style={[styles.headerTitle, { color: colors.text }]}>
            남은 복습: {remainingReviews}개
          </Text>
          <Text style={[styles.headerProgress, { color: colors.primary }]}>
            {Math.round(progress)}%
          </Text>
        </View>
        <View style={[styles.progressBar, { backgroundColor: colors.border }]}>
          <View
            style={[
              styles.progressFill,
              { backgroundColor: colors.primary, width: `${progress}%` },
            ]}
          />
        </View>
      </View>

      {/* Card */}
      <View style={styles.cardContainer}>
        <TouchableOpacity
          style={[styles.card, { backgroundColor: colors.card, borderColor: colors.border }]}
          onPress={() => {
            if (isObjectiveMode && !isFlipped) {
              flipCard();
            }
          }}
          activeOpacity={isObjectiveMode && !isFlipped ? 0.7 : 1}
        >
          {/* Title (always shown) */}
          {(isObjectiveMode || isDescriptiveMode) && (
            <View style={styles.cardSection}>
              <Text style={[styles.cardLabel, { color: colors.textSecondary }]}>
                제목
              </Text>
              <Text style={[styles.cardText, { color: colors.text }]}>
                {currentReview.content.title}
              </Text>
            </View>
          )}

          {/* Content (shown based on mode and flip state) */}
          {(showContent || isMultipleChoiceMode || isSubjectiveMode) && (
            <View style={styles.cardSection}>
              <Text style={[styles.cardLabel, { color: colors.textSecondary }]}>
                내용
              </Text>
              <MarkdownContent content={currentReview.content.content} />
            </View>
          )}

          {/* Flip indicator for objective mode */}
          {isObjectiveMode && !isFlipped && (
            <Text style={[styles.flipHint, { color: colors.textSecondary }]}>
              탭하여 내용 확인
            </Text>
          )}
        </TouchableOpacity>
      </View>

      {/* Input area based on review mode */}
      <View style={styles.inputContainer}>
        {/* Descriptive mode: 제목 보고 내용 작성 */}
        {isDescriptiveMode && !aiEvaluation && (
          <>
            <Text style={[styles.inputLabel, { color: colors.text }]}>
              제목을 보고 내용을 작성해주세요
            </Text>
            <TextInput
              style={[
                styles.textArea,
                {
                  backgroundColor: colors.surface,
                  borderColor: colors.border,
                  color: colors.text,
                },
              ]}
              placeholder="내용을 작성하세요 (최소 10자)"
              placeholderTextColor={colors.textSecondary}
              multiline
              numberOfLines={6}
              value={descriptiveAnswer}
              onChangeText={setDescriptiveAnswer}
            />
            <TouchableOpacity
              style={[
                styles.submitButton,
                { backgroundColor: colors.primary },
                (isSubmitting || descriptiveAnswer.length < 10) &&
                  styles.disabledButton,
              ]}
              onPress={handleSubmitDescriptive}
              disabled={isSubmitting || descriptiveAnswer.length < 10}
            >
              {isSubmitting ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.submitButtonText}>제출</Text>
              )}
            </TouchableOpacity>
          </>
        )}

        {/* Multiple Choice mode: 내용 보고 제목 선택 */}
        {isMultipleChoiceMode && !aiEvaluation && (
          <>
            <Text style={[styles.inputLabel, { color: colors.text }]}>
              내용에 맞는 제목을 선택하세요
            </Text>
            {currentReview.content.mc_choices?.choices.map((choice, index) => (
              <TouchableOpacity
                key={index}
                style={[
                  styles.choiceButton,
                  {
                    backgroundColor:
                      selectedChoice === choice ? colors.primary : colors.surface,
                    borderColor: colors.border,
                  },
                ]}
                onPress={() => setSelectedChoice(choice)}
              >
                <Text
                  style={[
                    styles.choiceText,
                    {
                      color:
                        selectedChoice === choice ? '#fff' : colors.text,
                    },
                  ]}
                >
                  {choice}
                </Text>
              </TouchableOpacity>
            ))}
            <TouchableOpacity
              style={[
                styles.submitButton,
                { backgroundColor: colors.primary },
                (isSubmitting || !selectedChoice) && styles.disabledButton,
              ]}
              onPress={handleSubmitMultipleChoice}
              disabled={isSubmitting || !selectedChoice}
            >
              {isSubmitting ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.submitButtonText}>제출</Text>
              )}
            </TouchableOpacity>
          </>
        )}

        {/* Subjective mode: 내용 보고 제목 유추 */}
        {isSubjectiveMode && !aiEvaluation && (
          <>
            <Text style={[styles.inputLabel, { color: colors.text }]}>
              내용을 보고 제목을 유추해주세요
            </Text>
            <TextInput
              style={[
                styles.input,
                {
                  backgroundColor: colors.surface,
                  borderColor: colors.border,
                  color: colors.text,
                },
              ]}
              placeholder="제목을 입력하세요 (최소 2자)"
              placeholderTextColor={colors.textSecondary}
              value={userTitle}
              onChangeText={setUserTitle}
            />
            <TouchableOpacity
              style={[
                styles.submitButton,
                { backgroundColor: colors.primary },
                (isSubmitting || userTitle.length < 2) && styles.disabledButton,
              ]}
              onPress={handleSubmitSubjective}
              disabled={isSubmitting || userTitle.length < 2}
            >
              {isSubmitting ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.submitButtonText}>제출</Text>
              )}
            </TouchableOpacity>
          </>
        )}
      </View>

      {/* Action buttons */}
      <View style={styles.actionContainer}>
        {/* Objective mode: 기억함/모름 버튼 */}
        {isObjectiveMode && showContent && (
          <View style={styles.objectiveButtons}>
            <TouchableOpacity
              style={[styles.actionButton, { backgroundColor: colors.error }]}
              onPress={() => handleObjectiveComplete('forgot')}
              disabled={completeReviewMutation.isPending}
            >
              <Text style={styles.actionButtonText}>모름</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.actionButton, { backgroundColor: colors.success }]}
              onPress={() => handleObjectiveComplete('remembered')}
              disabled={completeReviewMutation.isPending}
            >
              <Text style={styles.actionButtonText}>기억함</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* AI 평가 후 다음으로 버튼 */}
        {aiEvaluation && (
          <TouchableOpacity
            style={[styles.nextButton, { backgroundColor: colors.primary }]}
            onPress={handleNextAfterEvaluation}
          >
            <Text style={styles.nextButtonText}>다음으로</Text>
          </TouchableOpacity>
        )}
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  loadingText: {
    marginTop: 12,
    fontSize: 16,
  },
  emojiText: {
    fontSize: 64,
    marginBottom: 16,
  },
  completedTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  completedSubtitle: {
    fontSize: 16,
    textAlign: 'center',
  },
  header: {
    padding: 20,
    paddingTop: 24,
    paddingBottom: 20,
    borderBottomWidth: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '600',
  },
  headerProgress: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  progressBar: {
    height: 8,
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: 4,
  },
  cardContainer: {
    padding: 20,
  },
  card: {
    borderRadius: 20,
    padding: 28,
    borderWidth: 1,
    minHeight: 240,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 12,
    elevation: 4,
  },
  cardSection: {
    marginBottom: 20,
  },
  cardLabel: {
    fontSize: 13,
    fontWeight: '600',
    marginBottom: 12,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  cardText: {
    fontSize: 18,
    lineHeight: 28,
    fontWeight: '500',
  },
  flipHint: {
    fontSize: 15,
    fontStyle: 'italic',
    textAlign: 'center',
    marginTop: 20,
    opacity: 0.7,
  },
  inputContainer: {
    padding: 20,
  },
  inputLabel: {
    fontSize: 17,
    fontWeight: '600',
    marginBottom: 14,
  },
  textArea: {
    borderWidth: 1,
    borderRadius: 12,
    padding: 16,
    fontSize: 16,
    minHeight: 160,
    textAlignVertical: 'top',
    marginBottom: 16,
    lineHeight: 24,
  },
  input: {
    borderWidth: 1,
    borderRadius: 12,
    padding: 16,
    fontSize: 16,
    marginBottom: 16,
  },
  choiceButton: {
    borderWidth: 2,
    borderRadius: 12,
    padding: 18,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 1,
  },
  choiceText: {
    fontSize: 16,
    fontWeight: '500',
  },
  submitButton: {
    borderRadius: 12,
    padding: 18,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 3,
  },
  disabledButton: {
    opacity: 0.5,
  },
  submitButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  actionContainer: {
    padding: 20,
    paddingBottom: 40,
  },
  objectiveButtons: {
    flexDirection: 'row',
    gap: 14,
  },
  actionButton: {
    flex: 1,
    borderRadius: 12,
    padding: 18,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 56,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 3,
  },
  actionButtonText: {
    color: '#fff',
    fontSize: 17,
    fontWeight: 'bold',
  },
  nextButton: {
    borderRadius: 12,
    padding: 18,
    alignItems: 'center',
    minHeight: 56,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 3,
  },
  nextButtonText: {
    color: '#fff',
    fontSize: 17,
    fontWeight: 'bold',
  },
});

export default ReviewScreen;
