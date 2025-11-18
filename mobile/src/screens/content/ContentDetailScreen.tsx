import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ContentStackScreenProps } from '../../navigation/types';
import { contentAPI } from '../../api';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorMessage from '../../components/common/ErrorMessage';
import { useTheme } from '../../contexts/ThemeContext';

type Props = ContentStackScreenProps<'ContentDetail'>;

const ContentDetailScreen: React.FC<Props> = ({ route, navigation }) => {
  const { id } = route.params;
  const queryClient = useQueryClient();
  const { colors } = useTheme();

  const {
    data: content,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['content', id],
    queryFn: () => contentAPI.getContent(id),
  });

  const deleteMutation = useMutation({
    mutationFn: () => contentAPI.deleteContent(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contents'] });
      navigation.goBack();
    },
    onError: (error: any) => {
      Alert.alert('오류', error.userMessage || '삭제에 실패했습니다.');
    },
  });

  const handleEdit = () => {
    navigation.navigate('ContentEdit', { id });
  };

  const handleDelete = () => {
    Alert.alert('콘텐츠 삭제', '정말로 삭제하시겠습니까?', [
      { text: '취소', style: 'cancel' },
      {
        text: '삭제',
        style: 'destructive',
        onPress: () => deleteMutation.mutate(),
      },
    ]);
  };

  if (isLoading) {
    return <LoadingSpinner message="콘텐츠 불러오는 중..." />;
  }

  if (error || !content) {
    return (
      <ErrorMessage
        message={(error as any)?.userMessage || '콘텐츠를 불러올 수 없습니다.'}
        onRetry={refetch}
      />
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <ScrollView style={styles.content}>
        {/* Header */}
        <View style={[styles.header, { borderBottomColor: colors.border }]}>
          <Text style={[styles.title, { color: colors.text }]}>{content.title}</Text>
          {content.is_ai_validated && (
            <View style={styles.validatedBadge}>
              <Text style={styles.validatedText}>✓ AI 검증됨</Text>
              {content.ai_validation_score && (
                <Text style={styles.scoreText}>
                  ({content.ai_validation_score}점)
                </Text>
              )}
            </View>
          )}
        </View>

        {/* Metadata */}
        <View style={[styles.metadata, { backgroundColor: colors.surface, borderBottomColor: colors.border }]}>
          {content.category && (
            <View style={styles.metaItem}>
              <Text style={[styles.metaLabel, { color: colors.textSecondary }]}>카테고리</Text>
              <View style={styles.categoryTag}>
                <Text style={styles.categoryText}>{content.category.name}</Text>
              </View>
            </View>
          )}

          <View style={styles.metaItem}>
            <Text style={[styles.metaLabel, { color: colors.textSecondary }]}>복습 모드</Text>
            <Text style={[styles.metaValue, { color: colors.text }]}>
              {getReviewModeLabel(content.review_mode)}
            </Text>
          </View>

          <View style={styles.metaItem}>
            <Text style={[styles.metaLabel, { color: colors.textSecondary }]}>복습 횟수</Text>
            <Text style={[styles.metaValue, { color: colors.text }]}>{content.review_count}회</Text>
          </View>

          {content.next_review_date && (
            <View style={styles.metaItem}>
              <Text style={[styles.metaLabel, { color: colors.textSecondary }]}>다음 복습</Text>
              <Text style={[styles.metaValue, { color: colors.text }]}>
                {new Date(content.next_review_date).toLocaleDateString()}
              </Text>
            </View>
          )}
        </View>

        {/* Content */}
        <View style={[styles.section, { borderBottomColor: colors.border }]}>
          <Text style={[styles.sectionTitle, { color: colors.text }]}>내용</Text>
          <Text style={[styles.contentText, { color: colors.textSecondary }]}>{content.content}</Text>
        </View>

        {/* Multiple Choice Options */}
        {content.review_mode === 'multiple_choice' && content.mc_choices && (
          <View style={[styles.section, { borderBottomColor: colors.border }]}>
            <Text style={[styles.sectionTitle, { color: colors.text }]}>객관식 선택지</Text>
            {content.mc_choices.choices.map((choice, index) => (
              <View
                key={index}
                style={[
                  styles.choiceItem,
                  { backgroundColor: colors.surface },
                  choice === content.mc_choices?.correct_answer &&
                    styles.correctChoice,
                ]}
              >
                <Text style={[styles.choiceNumber, { backgroundColor: colors.border, color: colors.textSecondary }]}>{index + 1}</Text>
                <Text style={[styles.choiceText, { color: colors.text }]}>{choice}</Text>
                {choice === content.mc_choices?.correct_answer && (
                  <Text style={[styles.correctBadge, { backgroundColor: colors.background }]}>정답</Text>
                )}
              </View>
            ))}
          </View>
        )}

        {/* AI Validation Result */}
        {content.ai_validation_result && (
          <View style={[styles.section, { borderBottomColor: colors.border }]}>
            <Text style={[styles.sectionTitle, { color: colors.text }]}>AI 검증 결과</Text>

            <View style={[styles.validationCard, { backgroundColor: colors.surface }]}>
              <View style={styles.validationItem}>
                <Text style={[styles.validationLabel, { color: colors.textSecondary }]}>사실 정확성</Text>
                <Text style={[styles.validationScore, { color: colors.primary }]}>
                  {content.ai_validation_result.factual_accuracy.score}/100
                </Text>
              </View>

              <View style={styles.validationItem}>
                <Text style={[styles.validationLabel, { color: colors.textSecondary }]}>논리 일관성</Text>
                <Text style={[styles.validationScore, { color: colors.primary }]}>
                  {content.ai_validation_result.logical_consistency.score}/100
                </Text>
              </View>

              <View style={styles.validationItem}>
                <Text style={[styles.validationLabel, { color: colors.textSecondary }]}>제목 관련성</Text>
                <Text style={[styles.validationScore, { color: colors.primary }]}>
                  {content.ai_validation_result.title_relevance.score}/100
                </Text>
              </View>
            </View>

            {content.ai_validation_result.overall_feedback && (
              <View style={styles.feedbackCard}>
                <Text style={styles.feedbackLabel}>종합 피드백</Text>
                <Text style={[styles.feedbackText, { color: colors.text }]}>
                  {content.ai_validation_result.overall_feedback}
                </Text>
              </View>
            )}
          </View>
        )}

        {/* Timestamps */}
        <View style={styles.timestampsContainer}>
          <Text style={[styles.timestamp, { color: colors.textSecondary }]}>
            생성일: {new Date(content.created_at).toLocaleString()}
          </Text>
          <Text style={[styles.timestamp, { color: colors.textSecondary }]}>
            수정일: {new Date(content.updated_at).toLocaleString()}
          </Text>
        </View>
      </ScrollView>

      {/* Action Buttons */}
      <View style={[styles.actions, { borderTopColor: colors.border }]}>
        <TouchableOpacity
          style={[styles.actionButton, { backgroundColor: colors.primary }]}
          onPress={handleEdit}
        >
          <Text style={styles.editButtonText}>수정</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.actionButton, styles.deleteButton, { backgroundColor: colors.background, borderColor: colors.error }]}
          onPress={handleDelete}
          disabled={deleteMutation.isPending}
        >
          <Text style={[styles.deleteButtonText, { color: colors.error }]}>
            {deleteMutation.isPending ? '삭제 중...' : '삭제'}
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const getReviewModeLabel = (mode: string) => {
  const labels: Record<string, string> = {
    objective: '객관식',
    descriptive: '서술형',
    multiple_choice: '다지선다',
    subjective: '주관식',
  };
  return labels[mode] || mode;
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    flex: 1,
  },
  header: {
    padding: 20,
    borderBottomWidth: 1,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 12,
  },
  validatedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#d1fae5',
    alignSelf: 'flex-start',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
  },
  validatedText: {
    fontSize: 14,
    color: '#065f46',
    fontWeight: '600',
  },
  scoreText: {
    fontSize: 12,
    color: '#065f46',
    marginLeft: 4,
  },
  metadata: {
    padding: 20,
    borderBottomWidth: 1,
  },
  metaItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  metaLabel: {
    fontSize: 14,
    fontWeight: '500',
  },
  metaValue: {
    fontSize: 14,
    fontWeight: '600',
  },
  categoryTag: {
    backgroundColor: '#dbeafe',
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
  },
  categoryText: {
    fontSize: 14,
    color: '#1e40af',
    fontWeight: '600',
  },
  section: {
    padding: 20,
    borderBottomWidth: 1,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 12,
  },
  contentText: {
    fontSize: 16,
    lineHeight: 24,
  },
  choiceItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    borderRadius: 8,
    marginBottom: 8,
  },
  correctChoice: {
    backgroundColor: '#d1fae5',
    borderWidth: 2,
    borderColor: '#10b981',
  },
  choiceNumber: {
    width: 24,
    height: 24,
    borderRadius: 12,
    textAlign: 'center',
    lineHeight: 24,
    marginRight: 12,
    fontSize: 14,
    fontWeight: '600',
  },
  choiceText: {
    flex: 1,
    fontSize: 14,
  },
  correctBadge: {
    fontSize: 12,
    color: '#065f46',
    fontWeight: '600',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
  },
  validationCard: {
    borderRadius: 8,
    padding: 16,
    marginBottom: 12,
  },
  validationItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  validationLabel: {
    fontSize: 14,
  },
  validationScore: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  feedbackCard: {
    backgroundColor: '#eff6ff',
    borderRadius: 8,
    padding: 16,
  },
  feedbackLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1e40af',
    marginBottom: 8,
  },
  feedbackText: {
    fontSize: 14,
    lineHeight: 20,
  },
  timestampsContainer: {
    padding: 20,
  },
  timestamp: {
    fontSize: 12,
    marginBottom: 4,
  },
  actions: {
    flexDirection: 'row',
    padding: 16,
    borderTopWidth: 1,
    gap: 12,
  },
  actionButton: {
    flex: 1,
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  deleteButton: {
    borderWidth: 1,
  },
  editButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  deleteButtonText: {
    fontSize: 16,
    fontWeight: 'bold',
  },
});

export default ContentDetailScreen;
