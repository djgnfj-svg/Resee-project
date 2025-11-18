import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { ExamsStackScreenProps } from '../../navigation/types';
import { examsAPI } from '../../api';
import { useTheme } from '../../contexts/ThemeContext';
import { LinearGradient } from 'expo-linear-gradient';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorMessage from '../../components/common/ErrorMessage';

type Props = ExamsStackScreenProps<'ExamResult'>;

const ExamResultScreen: React.FC<Props> = ({ route, navigation }) => {
  const { id } = route.params;
  const { colors } = useTheme();

  const {
    data: result,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['examResult', id],
    queryFn: () => examsAPI.getExamResult(id),
  });

  const getScoreColor = (percentage: number) => {
    if (percentage >= 80) return colors.success;
    if (percentage >= 60) return colors.warning;
    return colors.error;
  };

  const getGrade = (percentage: number) => {
    if (percentage >= 90) return 'A';
    if (percentage >= 80) return 'B';
    if (percentage >= 70) return 'C';
    if (percentage >= 60) return 'D';
    return 'F';
  };

  const getGradeMessage = (percentage: number) => {
    if (percentage >= 90) return '탁월합니다!';
    if (percentage >= 80) return '우수합니다!';
    if (percentage >= 70) return '양호합니다!';
    if (percentage >= 60) return '노력이 필요합니다.';
    return '더 많은 학습이 필요합니다.';
  };

  if (isLoading) {
    return <LoadingSpinner message="결과를 불러오는 중..." />;
  }

  if (error || !result) {
    return (
      <ErrorMessage
        message={(error as any)?.userMessage || '결과를 불러올 수 없습니다.'}
        onRetry={refetch}
      />
    );
  }

  const percentage = Math.round((result.score / result.total_questions) * 100);
  const scoreColor = getScoreColor(percentage);

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      {/* Header */}
      <LinearGradient
        colors={[colors.gradient.start, colors.gradient.middle, colors.gradient.end]}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={styles.header}
      >
        <View style={styles.headerContent}>
          <Text style={styles.headerTitle}>🎯 시험 결과</Text>
          <Text style={styles.headerSubtitle}>{result.exam.title}</Text>
        </View>
      </LinearGradient>

      <ScrollView style={styles.content} contentContainerStyle={styles.contentContainer}>
        {/* Score Card */}
        <View style={[styles.scoreCard, { backgroundColor: colors.card }]}>
          <View style={[styles.scoreCircle, { borderColor: scoreColor }]}>
            <Text style={[styles.scorePercentage, { color: scoreColor }]}>
              {percentage}%
            </Text>
            <Text style={[styles.scoreGrade, { color: scoreColor }]}>
              {getGrade(percentage)}
            </Text>
          </View>
          <Text style={[styles.scoreMessage, { color: colors.text }]}>
            {getGradeMessage(percentage)}
          </Text>
          <View style={styles.scoreDetails}>
            <View style={styles.scoreDetailItem}>
              <Text style={[styles.scoreDetailLabel, { color: colors.textSecondary }]}>
                정답
              </Text>
              <Text style={[styles.scoreDetailValue, { color: colors.success }]}>
                {result.correct_answers}
              </Text>
            </View>
            <View style={[styles.scoreDetailDivider, { backgroundColor: colors.border }]} />
            <View style={styles.scoreDetailItem}>
              <Text style={[styles.scoreDetailLabel, { color: colors.textSecondary }]}>
                오답
              </Text>
              <Text style={[styles.scoreDetailValue, { color: colors.error }]}>
                {result.total_questions - result.correct_answers}
              </Text>
            </View>
            <View style={[styles.scoreDetailDivider, { backgroundColor: colors.border }]} />
            <View style={styles.scoreDetailItem}>
              <Text style={[styles.scoreDetailLabel, { color: colors.textSecondary }]}>
                총 문제
              </Text>
              <Text style={[styles.scoreDetailValue, { color: colors.text }]}>
                {result.total_questions}
              </Text>
            </View>
          </View>
          {result.time_spent_minutes && (
            <View style={[styles.timeSpent, { backgroundColor: colors.surface }]}>
              <Text style={[styles.timeSpentText, { color: colors.textSecondary }]}>
                ⏱ 소요 시간: {result.time_spent_minutes}분
              </Text>
            </View>
          )}
        </View>

        {/* Answer Review */}
        <View style={styles.reviewSection}>
          <Text style={[styles.reviewTitle, { color: colors.text }]}>
            📝 답안 확인
          </Text>

          {result.answers.map((answer, index) => {
            const question = result.exam.questions?.find(q => q.id === answer.question_id);
            if (!question) return null;

            return (
              <View
                key={answer.question_id}
                style={[
                  styles.answerCard,
                  {
                    backgroundColor: colors.card,
                    borderColor: answer.is_correct ? colors.success : colors.error,
                  }
                ]}
              >
                {/* Question Header */}
                <View style={styles.answerHeader}>
                  <View style={styles.answerHeaderLeft}>
                    <Text style={[styles.answerNumber, { color: colors.textSecondary }]}>
                      문제 {index + 1}
                    </Text>
                    <View style={[
                      styles.answerBadge,
                      { backgroundColor: answer.is_correct ? colors.success : colors.error }
                    ]}>
                      <Text style={styles.answerBadgeText}>
                        {answer.is_correct ? '✓ 정답' : '✗ 오답'}
                      </Text>
                    </View>
                  </View>
                </View>

                {/* Question Text */}
                <Text style={[styles.questionText, { color: colors.text }]}>
                  {question.question_text}
                </Text>

                {/* Choices */}
                <View style={styles.choicesReview}>
                  {question.choices.map((choice, choiceIndex) => {
                    const isUserAnswer = answer.selected_choice === choice;
                    const isCorrectAnswer = answer.correct_answer === choice;

                    let choiceStyle = styles.choiceReview;
                    let choiceBgColor = colors.surface;
                    let choiceTextColor = colors.text;

                    if (isCorrectAnswer) {
                      choiceBgColor = colors.success + '20';
                      choiceTextColor = colors.success;
                    }

                    if (isUserAnswer && !answer.is_correct) {
                      choiceBgColor = colors.error + '20';
                      choiceTextColor = colors.error;
                    }

                    return (
                      <View
                        key={choiceIndex}
                        style={[
                          choiceStyle,
                          {
                            backgroundColor: choiceBgColor,
                            borderColor: isCorrectAnswer
                              ? colors.success
                              : isUserAnswer
                              ? colors.error
                              : colors.border,
                            borderWidth: isCorrectAnswer || isUserAnswer ? 2 : 1,
                          }
                        ]}
                      >
                        <View style={[
                          styles.choiceNumberReview,
                          {
                            backgroundColor: isCorrectAnswer
                              ? colors.success
                              : isUserAnswer
                              ? colors.error
                              : colors.border,
                          }
                        ]}>
                          <Text style={[
                            styles.choiceNumberTextReview,
                            { color: isCorrectAnswer || isUserAnswer ? '#ffffff' : colors.textSecondary }
                          ]}>
                            {choiceIndex + 1}
                          </Text>
                        </View>
                        <Text style={[styles.choiceTextReview, { color: choiceTextColor }]}>
                          {choice}
                        </Text>
                        {isCorrectAnswer && (
                          <Text style={styles.correctIcon}>✓</Text>
                        )}
                        {isUserAnswer && !answer.is_correct && (
                          <Text style={styles.wrongIcon}>✗</Text>
                        )}
                      </View>
                    );
                  })}
                </View>

                {/* Explanation */}
                {question.explanation && (
                  <View style={[styles.explanation, { backgroundColor: colors.surface }]}>
                    <Text style={[styles.explanationLabel, { color: colors.primary }]}>
                      💡 해설
                    </Text>
                    <Text style={[styles.explanationText, { color: colors.text }]}>
                      {question.explanation}
                    </Text>
                  </View>
                )}
              </View>
            );
          })}
        </View>

        {/* Footer Info */}
        <View style={[styles.footerInfo, { backgroundColor: colors.surface }]}>
          <Text style={[styles.footerInfoText, { color: colors.textSecondary }]}>
            제출 시각: {new Date(result.submitted_at).toLocaleString('ko-KR')}
          </Text>
        </View>
      </ScrollView>

      {/* Bottom Actions */}
      <View style={[styles.actions, { backgroundColor: colors.card, borderTopColor: colors.border }]}>
        <TouchableOpacity
          style={[styles.actionButton, { backgroundColor: colors.primary }]}
          onPress={() => navigation.navigate('ExamList')}
        >
          <Text style={styles.actionButtonText}>시험 목록으로</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    paddingHorizontal: 20,
    paddingTop: 24,
    paddingBottom: 20,
    borderBottomLeftRadius: 24,
    borderBottomRightRadius: 24,
  },
  headerContent: {
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 8,
  },
  headerSubtitle: {
    fontSize: 15,
    color: 'rgba(255, 255, 255, 0.9)',
  },
  content: {
    flex: 1,
  },
  contentContainer: {
    padding: 20,
  },
  scoreCard: {
    padding: 32,
    borderRadius: 20,
    alignItems: 'center',
    marginBottom: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 12,
    elevation: 4,
  },
  scoreCircle: {
    width: 160,
    height: 160,
    borderRadius: 80,
    borderWidth: 8,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 20,
  },
  scorePercentage: {
    fontSize: 48,
    fontWeight: 'bold',
  },
  scoreGrade: {
    fontSize: 24,
    fontWeight: 'bold',
    marginTop: 4,
  },
  scoreMessage: {
    fontSize: 20,
    fontWeight: '600',
    marginBottom: 24,
    textAlign: 'center',
  },
  scoreDetails: {
    flexDirection: 'row',
    width: '100%',
    justifyContent: 'space-around',
    alignItems: 'center',
    marginBottom: 16,
  },
  scoreDetailItem: {
    alignItems: 'center',
    flex: 1,
  },
  scoreDetailLabel: {
    fontSize: 13,
    marginBottom: 6,
  },
  scoreDetailValue: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  scoreDetailDivider: {
    width: 1,
    height: 40,
  },
  timeSpent: {
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 12,
  },
  timeSpentText: {
    fontSize: 14,
    fontWeight: '500',
  },
  reviewSection: {
    marginBottom: 20,
  },
  reviewTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  answerCard: {
    padding: 18,
    borderRadius: 16,
    marginBottom: 16,
    borderLeftWidth: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 3,
  },
  answerHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  answerHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  answerNumber: {
    fontSize: 13,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  answerBadge: {
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 8,
  },
  answerBadgeText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: 'bold',
  },
  questionText: {
    fontSize: 16,
    lineHeight: 24,
    marginBottom: 16,
    fontWeight: '500',
  },
  choicesReview: {
    gap: 10,
    marginBottom: 12,
  },
  choiceReview: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    borderRadius: 10,
    borderWidth: 1,
  },
  choiceNumberReview: {
    width: 28,
    height: 28,
    borderRadius: 14,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 10,
  },
  choiceNumberTextReview: {
    fontSize: 14,
    fontWeight: 'bold',
  },
  choiceTextReview: {
    flex: 1,
    fontSize: 15,
    lineHeight: 22,
  },
  correctIcon: {
    color: '#22c55e',
    fontSize: 20,
    fontWeight: 'bold',
  },
  wrongIcon: {
    color: '#ef4444',
    fontSize: 20,
    fontWeight: 'bold',
  },
  explanation: {
    padding: 16,
    borderRadius: 12,
    marginTop: 4,
  },
  explanationLabel: {
    fontSize: 13,
    fontWeight: '600',
    marginBottom: 8,
  },
  explanationText: {
    fontSize: 14,
    lineHeight: 22,
  },
  footerInfo: {
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  footerInfoText: {
    fontSize: 13,
  },
  actions: {
    padding: 20,
    borderTopWidth: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 4,
  },
  actionButton: {
    paddingVertical: 18,
    borderRadius: 12,
    alignItems: 'center',
    minHeight: 56,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 3,
  },
  actionButtonText: {
    color: '#ffffff',
    fontSize: 17,
    fontWeight: 'bold',
  },
});

export default ExamResultScreen;
