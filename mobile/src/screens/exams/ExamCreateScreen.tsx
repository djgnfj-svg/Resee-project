import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  ScrollView,
} from 'react-native';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigation } from '@react-navigation/native';
import { BottomTabNavigationProp } from '@react-navigation/bottom-tabs';
import { contentAPI, examsAPI } from '../../api';
import { useTheme } from '../../contexts/ThemeContext';
import { Content } from '../../types';
import { MainTabParamList } from '../../navigation/types';
import { LinearGradient } from 'expo-linear-gradient';

type NavigationProp = BottomTabNavigationProp<MainTabParamList, 'ExamsTab'>;

const ExamCreateScreen = () => {
  const { colors } = useTheme();
  const navigation = useNavigation<NavigationProp>();
  const queryClient = useQueryClient();
  const [selectedContentIds, setSelectedContentIds] = useState<number[]>([]);
  const [isCreating, setIsCreating] = useState(false);
  const [creationProgress, setCreationProgress] = useState('');

  const { data: contentData, isLoading } = useQuery({
    queryKey: ['contents'],
    queryFn: () => contentAPI.getContents(),
  });

  const aiValidatedContents = contentData?.results.filter(
    (content) => content.is_ai_validated
  ) || [];

  const toggleContentSelection = (contentId: number) => {
    setSelectedContentIds((prev) => {
      if (prev.includes(contentId)) {
        return prev.filter((id) => id !== contentId);
      }
      if (prev.length >= 10) {
        Alert.alert('선택 제한', '최대 10개까지 선택할 수 있습니다.');
        return prev;
      }
      return [...prev, contentId];
    });
  };

  const pollExamStatus = async (examId: number) => {
    const maxAttempts = 60; // 60 seconds max
    const pollInterval = 1000; // 1 second

    for (let i = 0; i < maxAttempts; i++) {
      try {
        const exam = await examsAPI.checkExamStatus(examId);

        if (exam.status === 'ready') {
          setCreationProgress('시험 생성 완료!');
          queryClient.invalidateQueries({ queryKey: ['exams'] });

          // Navigate to exam detail after a brief delay
          setTimeout(() => {
            setIsCreating(false);
            navigation.navigate('ExamsTab', {
              screen: 'ExamDetail',
              params: { id: examId }
            });
          }, 500);
          return;
        } else if (exam.status === 'failed') {
          throw new Error('시험 생성에 실패했습니다.');
        }

        // Still pending
        const progress = Math.min((i + 1) / maxAttempts * 100, 95);
        setCreationProgress(`AI가 문제를 생성하고 있습니다... (${Math.round(progress)}%)`);

        await new Promise((resolve) => setTimeout(resolve, pollInterval));
      } catch (error) {
        throw error;
      }
    }

    throw new Error('시험 생성 시간이 초과되었습니다. 나중에 다시 시도해주세요.');
  };

  const createExamMutation = useMutation({
    mutationFn: async () => {
      setIsCreating(true);
      setCreationProgress('시험을 준비하고 있습니다...');

      const exam = await examsAPI.createExam({
        content_ids: selectedContentIds,
      });

      await pollExamStatus(exam.id);
      return exam;
    },
    onError: (error: any) => {
      setIsCreating(false);
      setCreationProgress('');
      Alert.alert(
        '생성 실패',
        error.userMessage || '시험 생성에 실패했습니다. 다시 시도해주세요.'
      );
    },
  });

  const handleCreateExam = () => {
    if (selectedContentIds.length < 7) {
      Alert.alert('선택 부족', '최소 7개의 콘텐츠를 선택해주세요.');
      return;
    }

    Alert.alert(
      '시험 생성',
      `선택한 ${selectedContentIds.length}개의 콘텐츠로 주간 시험을 생성하시겠습니까?\n\nAI가 객관식 문제를 자동으로 생성합니다. (약 30-60초 소요)`,
      [
        { text: '취소', style: 'cancel' },
        {
          text: '생성',
          onPress: () => createExamMutation.mutate(),
        },
      ]
    );
  };

  const renderContentItem = ({ item }: { item: Content }) => {
    const isSelected = selectedContentIds.includes(item.id);

    return (
      <TouchableOpacity
        style={[
          styles.contentCard,
          {
            backgroundColor: colors.card,
            borderColor: isSelected ? colors.primary : colors.border,
            borderWidth: isSelected ? 2 : 1,
          }
        ]}
        onPress={() => toggleContentSelection(item.id)}
        activeOpacity={0.7}
        disabled={isCreating}
      >
        <View style={styles.contentHeader}>
          <View style={[
            styles.checkbox,
            {
              backgroundColor: isSelected ? colors.primary : colors.background,
              borderColor: isSelected ? colors.primary : colors.border,
            }
          ]}>
            {isSelected && <Text style={styles.checkmark}>✓</Text>}
          </View>
          <View style={styles.contentInfo}>
            <Text style={[styles.contentTitle, { color: colors.text }]} numberOfLines={2}>
              {item.title}
            </Text>
            {item.category && (
              <View style={[styles.categoryTag, { backgroundColor: colors.primary + '15' }]}>
                <Text style={[styles.categoryText, { color: colors.primary }]}>
                  {item.category.name}
                </Text>
              </View>
            )}
          </View>
        </View>
        <Text style={[styles.contentPreview, { color: colors.textSecondary }]} numberOfLines={2}>
          {item.content}
        </Text>
        <View style={styles.contentMeta}>
          <Text style={[styles.metaText, { color: colors.textSecondary }]}>
            🔄 {item.review_count}회 복습
          </Text>
          {item.ai_validation_score && (
            <Text style={[styles.metaText, { color: colors.success }]}>
              ✓ AI 검증 {item.ai_validation_score}점
            </Text>
          )}
        </View>
      </TouchableOpacity>
    );
  };

  if (isCreating) {
    return (
      <View style={[styles.centerContainer, { backgroundColor: colors.background }]}>
        <LinearGradient
          colors={[colors.gradient.start, colors.gradient.middle, colors.gradient.end]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={styles.progressCard}
        >
          <View style={styles.progressContent}>
            <ActivityIndicator size="large" color="#ffffff" />
            <Text style={styles.progressTitle}>AI 시험 생성 중</Text>
            <Text style={styles.progressText}>{creationProgress}</Text>
            <View style={styles.progressInfoBox}>
              <Text style={styles.progressInfo}>
                • AI가 선택한 콘텐츠를 분석하고 있습니다
              </Text>
              <Text style={styles.progressInfo}>
                • 각 콘텐츠에서 객관식 문제를 생성합니다
              </Text>
              <Text style={styles.progressInfo}>
                • 문제의 난이도와 정답을 검증합니다
              </Text>
            </View>
            <Text style={styles.progressNote}>
              이 작업은 약 30-60초 정도 소요됩니다
            </Text>
          </View>
        </LinearGradient>
      </View>
    );
  }

  if (isLoading) {
    return (
      <View style={[styles.centerContainer, { backgroundColor: colors.background }]}>
        <ActivityIndicator size="large" color={colors.primary} />
        <Text style={[styles.loadingText, { color: colors.textSecondary }]}>
          콘텐츠를 불러오는 중...
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
        <View style={styles.headerContent}>
          <Text style={styles.headerTitle}>📝 시험 콘텐츠 선택</Text>
          <Text style={styles.headerSubtitle}>
            AI 검증된 콘텐츠 중 7-10개를 선택하세요
          </Text>
        </View>
        <View style={styles.selectionInfo}>
          <View style={[styles.selectionBadge, { backgroundColor: 'rgba(255, 255, 255, 0.2)' }]}>
            <Text style={styles.selectionText}>
              선택: {selectedContentIds.length} / 10
            </Text>
          </View>
          <View style={[styles.selectionBadge, { backgroundColor: 'rgba(255, 255, 255, 0.2)' }]}>
            <Text style={styles.selectionText}>
              최소: 7개
            </Text>
          </View>
        </View>
      </LinearGradient>

      {aiValidatedContents.length === 0 ? (
        <ScrollView contentContainerStyle={styles.emptyContainer}>
          <View style={[styles.emptyIconContainer, { backgroundColor: colors.primary + '20' }]}>
            <Text style={styles.emptyIcon}>📝</Text>
          </View>
          <Text style={[styles.emptyTitle, { color: colors.text }]}>
            AI 검증된 콘텐츠가 없습니다
          </Text>
          <Text style={[styles.emptySubtitle, { color: colors.textSecondary }]}>
            시험을 생성하려면 최소 7개의 AI 검증된 콘텐츠가 필요합니다.
            {'\n\n'}
            콘텐츠를 추가한 후 AI 검증을 받아보세요.
          </Text>
        </ScrollView>
      ) : aiValidatedContents.length < 7 ? (
        <ScrollView contentContainerStyle={styles.emptyContainer}>
          <View style={[styles.emptyIconContainer, { backgroundColor: colors.warning + '20' }]}>
            <Text style={styles.emptyIcon}>⚠️</Text>
          </View>
          <Text style={[styles.emptyTitle, { color: colors.text }]}>
            AI 검증된 콘텐츠가 부족합니다
          </Text>
          <Text style={[styles.emptySubtitle, { color: colors.textSecondary }]}>
            현재 {aiValidatedContents.length}개의 AI 검증된 콘텐츠가 있습니다.
            {'\n'}
            시험 생성을 위해서는 최소 7개가 필요합니다.
            {'\n\n'}
            {7 - aiValidatedContents.length}개 더 추가해주세요.
          </Text>
        </ScrollView>
      ) : (
        <>
          <FlatList
            data={aiValidatedContents}
            renderItem={renderContentItem}
            keyExtractor={(item) => item.id.toString()}
            contentContainerStyle={styles.listContent}
            ListHeaderComponent={
              <View style={[styles.infoBox, { backgroundColor: colors.surface }]}>
                <Text style={[styles.infoText, { color: colors.text }]}>
                  💡 선택한 콘텐츠를 바탕으로 AI가 자동으로 객관식 문제를 생성합니다.
                </Text>
              </View>
            }
          />

          {/* Create Button */}
          <View style={[styles.footer, { backgroundColor: colors.card, borderTopColor: colors.border }]}>
            <TouchableOpacity
              style={[
                styles.createButton,
                {
                  backgroundColor: selectedContentIds.length >= 7 && selectedContentIds.length <= 10
                    ? colors.primary
                    : colors.border,
                },
              ]}
              onPress={handleCreateExam}
              disabled={selectedContentIds.length < 7 || selectedContentIds.length > 10 || isCreating}
              activeOpacity={0.8}
            >
              <Text style={[
                styles.createButtonText,
                {
                  color: selectedContentIds.length >= 7 && selectedContentIds.length <= 10
                    ? '#ffffff'
                    : colors.textSecondary,
                },
              ]}>
                {selectedContentIds.length < 7
                  ? `${7 - selectedContentIds.length}개 더 선택하세요`
                  : `시험 생성 (${selectedContentIds.length}개 콘텐츠)`}
              </Text>
            </TouchableOpacity>
          </View>
        </>
      )}
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
  header: {
    paddingHorizontal: 20,
    paddingTop: 24,
    paddingBottom: 20,
    borderBottomLeftRadius: 24,
    borderBottomRightRadius: 24,
  },
  headerContent: {
    marginBottom: 16,
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
    lineHeight: 22,
  },
  selectionInfo: {
    flexDirection: 'row',
    gap: 12,
  },
  selectionBadge: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 12,
  },
  selectionText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#ffffff',
  },
  infoBox: {
    padding: 16,
    borderRadius: 12,
    marginBottom: 16,
  },
  infoText: {
    fontSize: 14,
    lineHeight: 20,
  },
  listContent: {
    padding: 16,
  },
  contentCard: {
    borderRadius: 16,
    padding: 16,
    marginBottom: 14,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 3,
  },
  contentHeader: {
    flexDirection: 'row',
    marginBottom: 12,
  },
  checkbox: {
    width: 24,
    height: 24,
    borderRadius: 6,
    borderWidth: 2,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  checkmark: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  contentInfo: {
    flex: 1,
  },
  contentTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 6,
    lineHeight: 22,
  },
  categoryTag: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
    alignSelf: 'flex-start',
  },
  categoryText: {
    fontSize: 12,
    fontWeight: '600',
  },
  contentPreview: {
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 12,
  },
  contentMeta: {
    flexDirection: 'row',
    gap: 12,
  },
  metaText: {
    fontSize: 12,
    fontWeight: '500',
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
  createButton: {
    paddingVertical: 18,
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
  createButtonText: {
    fontSize: 17,
    fontWeight: 'bold',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  emptyIconContainer: {
    width: 80,
    height: 80,
    borderRadius: 40,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 20,
  },
  emptyIcon: {
    fontSize: 40,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 8,
    textAlign: 'center',
  },
  emptySubtitle: {
    fontSize: 15,
    textAlign: 'center',
    lineHeight: 22,
  },
  progressCard: {
    borderRadius: 24,
    padding: 32,
    margin: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.3,
    shadowRadius: 16,
    elevation: 8,
  },
  progressContent: {
    alignItems: 'center',
  },
  progressTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#ffffff',
    marginTop: 20,
    marginBottom: 12,
  },
  progressText: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.9)',
    textAlign: 'center',
    marginBottom: 24,
  },
  progressInfoBox: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    width: '100%',
  },
  progressInfo: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.9)',
    marginBottom: 8,
    lineHeight: 20,
  },
  progressNote: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.7)',
    textAlign: 'center',
    fontStyle: 'italic',
  },
});

export default ExamCreateScreen;
