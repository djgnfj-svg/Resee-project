import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ExamsStackScreenProps } from '../../navigation/types';
import { examsAPI } from '../../api';
import { useTheme } from '../../contexts/ThemeContext';
import { LinearGradient } from 'expo-linear-gradient';
import { ExamQuestion } from '../../types';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorMessage from '../../components/common/ErrorMessage';

type Props = ExamsStackScreenProps<'ExamDetail'>;

const ExamDetailScreen: React.FC<Props> = ({ route, navigation }) => {
  const { id } = route.params;
  const { colors } = useTheme();
  const queryClient = useQueryClient();

  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState<{ [key: number]: string }>({});
  const [timeRemaining, setTimeRemaining] = useState<number | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    data: exam,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['exam', id],
    queryFn: () => examsAPI.getExam(id),
  });

  const questions = exam?.questions || [];
  const currentQuestion = questions[currentQuestionIndex];

  // Timer effect
  useEffect(() => {
    if (exam?.duration_minutes) {
      setTimeRemaining(exam.duration_minutes * 60); // Convert to seconds
    }
  }, [exam]);

  useEffect(() => {
    if (timeRemaining === null || timeRemaining <= 0) return;

    const timer = setInterval(() => {
      setTimeRemaining((prev) => {
        if (prev === null || prev <= 1) {
          clearInterval(timer);
          handleAutoSubmit();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [timeRemaining]);

  const handleAutoSubmit = () => {
    Alert.alert(
      '시간 종료',
      '시험 시간이 종료되어 자동으로 제출됩니다.',
      [{ text: '확인', onPress: () => handleSubmit() }]
    );
  };

  const submitExamMutation = useMutation({
    mutationFn: async () => {
      const answers = questions.map((q: ExamQuestion) => ({
        question_id: q.id,
        selected_choice: selectedAnswers[q.id] || '',
      }));

      return examsAPI.submitExam({
        exam_id: id,
        answers,
      });
    },
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['examResults'] });
      navigation.navigate('ExamResult', { id: result.id });
    },
    onError: (error: any) => {
      setIsSubmitting(false);
      Alert.alert('제출 실패', error.userMessage || '시험 제출에 실패했습니다.');
    },
  });

  const handleSelectAnswer = (answer: string) => {
    if (!currentQuestion) return;

    setSelectedAnswers((prev) => ({
      ...prev,
      [currentQuestion.id]: answer,
    }));
  };

  const handleNext = () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    }
  };

  const handlePrevious = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1);
    }
  };

  const handleSubmit = () => {
    const unansweredCount = questions.filter(
      (q: ExamQuestion) => !selectedAnswers[q.id]
    ).length;

    if (unansweredCount > 0) {
      Alert.alert(
        '미응답 문제',
        `${unansweredCount}개의 문제에 답하지 않았습니다.\n그래도 제출하시겠습니까?`,
        [
          { text: '취소', style: 'cancel' },
          {
            text: '제출',
            onPress: () => {
              setIsSubmitting(true);
              submitExamMutation.mutate();
            },
          },
        ]
      );
    } else {
      Alert.alert('시험 제출', '답안을 제출하시겠습니까?', [
        { text: '취소', style: 'cancel' },
        {
          text: '제출',
          onPress: () => {
            setIsSubmitting(true);
            submitExamMutation.mutate();
          },
        },
      ]);
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getProgress = () => {
    const answered = questions.filter((q: ExamQuestion) => selectedAnswers[q.id]).length;
    return (answered / questions.length) * 100;
  };

  if (isLoading) {
    return <LoadingSpinner message="시험을 불러오는 중..." />;
  }

  if (error || !exam) {
    return (
      <ErrorMessage
        message={(error as any)?.userMessage || '시험을 불러올 수 없습니다.'}
        onRetry={refetch}
      />
    );
  }

  if (exam.status !== 'ready') {
    return (
      <View style={[styles.centerContainer, { backgroundColor: colors.background }]}>
        <View style={[styles.statusCard, { backgroundColor: colors.card }]}>
          <Text style={styles.statusIcon}>
            {exam.status === 'pending' ? '⏳' : '❌'}
          </Text>
          <Text style={[styles.statusTitle, { color: colors.text }]}>
            {exam.status === 'pending' ? '시험 준비 중' : '시험을 사용할 수 없습니다'}
          </Text>
          <Text style={[styles.statusMessage, { color: colors.textSecondary }]}>
            {exam.status === 'pending'
              ? 'AI가 문제를 생성하고 있습니다. 잠시만 기다려주세요.'
              : '시험 생성에 실패했습니다. 다시 시도해주세요.'}
          </Text>
          <TouchableOpacity
            style={[styles.statusButton, { backgroundColor: colors.primary }]}
            onPress={() => navigation.goBack()}
          >
            <Text style={styles.statusButtonText}>돌아가기</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  if (isSubmitting) {
    return (
      <View style={[styles.centerContainer, { backgroundColor: colors.background }]}>
        <ActivityIndicator size="large" color={colors.primary} />
        <Text style={[styles.loadingText, { color: colors.textSecondary }]}>
          답안을 제출하는 중...
        </Text>
      </View>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      {/* Header */}
      <LinearGradient
        colors={[colors.gradient.start, colors.gradient.middle, colors.gradient.end]}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={styles.header}
      >
        <View style={styles.headerTop}>
          <View>
            <Text style={styles.examTitle}>{exam.title || '주간 시험'}</Text>
            <Text style={styles.questionCounter}>
              문제 {currentQuestionIndex + 1} / {questions.length}
            </Text>
          </View>
          {timeRemaining !== null && (
            <View style={[
              styles.timerBadge,
              {
                backgroundColor: timeRemaining < 300
                  ? 'rgba(239, 68, 68, 0.2)'
                  : 'rgba(255, 255, 255, 0.2)'
              }
            ]}>
              <Text style={[
                styles.timerText,
                { color: timeRemaining < 300 ? '#fef2f2' : '#ffffff' }
              ]}>
                ⏱ {formatTime(timeRemaining)}
              </Text>
            </View>
          )}
        </View>

        {/* Progress Bar */}
        <View style={styles.progressContainer}>
          <View style={[styles.progressBar, { backgroundColor: 'rgba(255, 255, 255, 0.3)' }]}>
            <View
              style={[
                styles.progressFill,
                { width: `${getProgress()}%`, backgroundColor: '#ffffff' }
              ]}
            />
          </View>
          <Text style={styles.progressText}>
            답변: {questions.filter((q: ExamQuestion) => selectedAnswers[q.id]).length} / {questions.length}
          </Text>
        </View>
      </LinearGradient>

      {/* Question Content */}
      <ScrollView style={styles.content} contentContainerStyle={styles.contentContainer}>
        {currentQuestion && (
          <>
            <View style={[styles.questionCard, { backgroundColor: colors.card }]}>
              <Text style={[styles.questionLabel, { color: colors.textSecondary }]}>
                문제 {currentQuestionIndex + 1}
              </Text>
              <Text style={[styles.questionText, { color: colors.text }]}>
                {currentQuestion.question_text}
              </Text>
            </View>

            <View style={styles.choicesContainer}>
              {currentQuestion.choices.map((choice, index) => {
                const isSelected = selectedAnswers[currentQuestion.id] === choice;
                return (
                  <TouchableOpacity
                    key={index}
                    style={[
                      styles.choiceButton,
                      {
                        backgroundColor: isSelected ? colors.primary + '15' : colors.card,
                        borderColor: isSelected ? colors.primary : colors.border,
                        borderWidth: isSelected ? 2 : 1,
                      }
                    ]}
                    onPress={() => handleSelectAnswer(choice)}
                    activeOpacity={0.7}
                  >
                    <View style={[
                      styles.choiceNumber,
                      {
                        backgroundColor: isSelected ? colors.primary : colors.border,
                      }
                    ]}>
                      <Text style={[
                        styles.choiceNumberText,
                        { color: isSelected ? '#ffffff' : colors.textSecondary }
                      ]}>
                        {index + 1}
                      </Text>
                    </View>
                    <Text style={[
                      styles.choiceText,
                      { color: isSelected ? colors.primary : colors.text }
                    ]}>
                      {choice}
                    </Text>
                    {isSelected && (
                      <View style={[styles.selectedBadge, { backgroundColor: colors.primary }]}>
                        <Text style={styles.selectedBadgeText}>✓</Text>
                      </View>
                    )}
                  </TouchableOpacity>
                );
              })}
            </View>
          </>
        )}
      </ScrollView>

      {/* Navigation Footer */}
      <View style={[styles.footer, { backgroundColor: colors.card, borderTopColor: colors.border }]}>
        <View style={styles.navButtons}>
          <TouchableOpacity
            style={[
              styles.navButton,
              {
                backgroundColor: currentQuestionIndex > 0 ? colors.primary : colors.border,
                opacity: currentQuestionIndex > 0 ? 1 : 0.5,
              }
            ]}
            onPress={handlePrevious}
            disabled={currentQuestionIndex === 0}
          >
            <Text style={styles.navButtonText}>◀ 이전</Text>
          </TouchableOpacity>

          {currentQuestionIndex < questions.length - 1 ? (
            <TouchableOpacity
              style={[styles.navButton, { backgroundColor: colors.primary }]}
              onPress={handleNext}
            >
              <Text style={styles.navButtonText}>다음 ▶</Text>
            </TouchableOpacity>
          ) : (
            <TouchableOpacity
              style={[styles.submitButton, { backgroundColor: colors.success }]}
              onPress={handleSubmit}
            >
              <Text style={styles.submitButtonText}>제출하기</Text>
            </TouchableOpacity>
          )}
        </View>
      </View>
    </View>
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
  statusCard: {
    padding: 32,
    borderRadius: 20,
    alignItems: 'center',
    maxWidth: 400,
  },
  statusIcon: {
    fontSize: 64,
    marginBottom: 16,
  },
  statusTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    marginBottom: 12,
    textAlign: 'center',
  },
  statusMessage: {
    fontSize: 15,
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: 24,
  },
  statusButton: {
    paddingHorizontal: 32,
    paddingVertical: 14,
    borderRadius: 12,
  },
  statusButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  header: {
    paddingHorizontal: 20,
    paddingTop: 24,
    paddingBottom: 20,
  },
  headerTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 16,
  },
  examTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 6,
  },
  questionCounter: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.9)',
  },
  timerBadge: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 12,
  },
  timerText: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  progressContainer: {
    marginTop: 8,
  },
  progressBar: {
    height: 8,
    borderRadius: 4,
    overflow: 'hidden',
    marginBottom: 8,
  },
  progressFill: {
    height: '100%',
    borderRadius: 4,
  },
  progressText: {
    fontSize: 13,
    color: 'rgba(255, 255, 255, 0.9)',
    fontWeight: '500',
  },
  content: {
    flex: 1,
  },
  contentContainer: {
    padding: 20,
  },
  questionCard: {
    padding: 20,
    borderRadius: 16,
    marginBottom: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  questionLabel: {
    fontSize: 13,
    fontWeight: '600',
    marginBottom: 12,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  questionText: {
    fontSize: 18,
    lineHeight: 28,
    fontWeight: '500',
  },
  choicesContainer: {
    gap: 12,
  },
  choiceButton: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  choiceNumber: {
    width: 32,
    height: 32,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  choiceNumberText: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  choiceText: {
    flex: 1,
    fontSize: 16,
    lineHeight: 24,
  },
  selectedBadge: {
    width: 28,
    height: 28,
    borderRadius: 14,
    justifyContent: 'center',
    alignItems: 'center',
  },
  selectedBadgeText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  footer: {
    padding: 20,
    borderTopWidth: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 4,
  },
  navButtons: {
    flexDirection: 'row',
    gap: 12,
  },
  navButton: {
    flex: 1,
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 56,
  },
  navButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  submitButton: {
    flex: 1,
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 56,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 3,
  },
  submitButtonText: {
    color: '#ffffff',
    fontSize: 17,
    fontWeight: 'bold',
  },
});

export default ExamDetailScreen;
