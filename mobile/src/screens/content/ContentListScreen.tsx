import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
} from 'react-native';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { ContentStackScreenProps } from '../../navigation/types';
import { contentAPI } from '../../api';
import { Content } from '../../types';
import { useTheme } from '../../contexts/ThemeContext';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorMessage from '../../components/common/ErrorMessage';
import EmptyState from '../../components/common/EmptyState';

type Props = ContentStackScreenProps<'ContentList'>;

const ContentListScreen: React.FC<Props> = ({ navigation }) => {
  const queryClient = useQueryClient();
  const [refreshing, setRefreshing] = useState(false);
  const { colors } = useTheme();

  const {
    data: contentData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['contents'],
    queryFn: () => contentAPI.getContents(),
  });

  const onRefresh = async () => {
    setRefreshing(true);
    await refetch();
    setRefreshing(false);
  };

  const handleContentPress = (id: number) => {
    navigation.navigate('ContentDetail', { id });
  };

  const handleCreatePress = () => {
    navigation.navigate('ContentCreate');
  };

  if (isLoading) {
    return <LoadingSpinner message="콘텐츠 불러오는 중..." />;
  }

  if (error) {
    return (
      <ErrorMessage
        message={(error as any).userMessage || '콘텐츠를 불러올 수 없습니다.'}
        onRetry={refetch}
      />
    );
  }

  const contents = contentData?.results || [];
  const usage = contentData?.usage;

  const renderContentItem = ({ item }: { item: Content }) => (
    <TouchableOpacity
      style={[styles.contentCard, { backgroundColor: colors.card, borderColor: colors.border }]}
      onPress={() => handleContentPress(item.id)}
      activeOpacity={0.7}
    >
      <View style={styles.contentHeader}>
        <View style={styles.titleRow}>
          <Text style={[styles.contentTitle, { color: colors.text }]} numberOfLines={1}>
            {item.title}
          </Text>
          {item.is_ai_validated && (
            <View style={styles.validatedBadge}>
              <Text style={styles.validatedText}>✓</Text>
            </View>
          )}
        </View>
        {item.category && (
          <View style={[styles.categoryTag, { backgroundColor: colors.primary + '15' }]}>
            <Text style={[styles.categoryText, { color: colors.primary }]}>{item.category.name}</Text>
          </View>
        )}
      </View>

      <Text style={[styles.contentPreview, { color: colors.textSecondary }]} numberOfLines={2}>
        {item.content}
      </Text>

      <View style={styles.contentFooter}>
        <View style={[styles.reviewModeBadge, { backgroundColor: colors.surface }]}>
          <Text style={[styles.reviewModeText, { color: colors.text }]}>
            {getReviewModeLabel(item.review_mode)}
          </Text>
        </View>
        <View style={styles.contentStats}>
          <View style={styles.statItem}>
            <Text style={styles.statIcon}>🔄</Text>
            <Text style={[styles.statsText, { color: colors.textSecondary }]}>{item.review_count}</Text>
          </View>
          {item.next_review_date && (
            <View style={styles.statItem}>
              <Text style={styles.statIcon}>📅</Text>
              <Text style={[styles.statsText, { color: colors.textSecondary }]}>
                {new Date(item.next_review_date).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' })}
              </Text>
            </View>
          )}
        </View>
      </View>
    </TouchableOpacity>
  );

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      {/* Usage Bar - Only show for FREE tier */}
      {usage && usage.tier.toLowerCase() === 'free' && (
        <View style={[styles.usageContainer, { backgroundColor: colors.card, borderBottomColor: colors.border }]}>
          <View style={styles.usageHeader}>
            <Text style={[styles.usageText, { color: colors.text }]}>
              {usage.current} / {usage.limit} 콘텐츠
            </Text>
            <Text style={[styles.tierText, { color: colors.textSecondary, backgroundColor: colors.surface }]}>FREE</Text>
          </View>
          <View style={[styles.usageBar, { backgroundColor: colors.border }]}>
            <View
              style={[
                styles.usageProgress,
                {
                  width: `${Math.min(usage.percentage, 100)}%`,
                  backgroundColor:
                    usage.percentage >= 90
                      ? colors.error
                      : usage.percentage >= 70
                      ? colors.warning
                      : colors.success,
                },
              ]}
            />
          </View>
        </View>
      )}

      {contents.length === 0 ? (
        <EmptyState
          title="콘텐츠가 없습니다"
          message="첫 번째 학습 콘텐츠를 추가해보세요!"
          actionText="콘텐츠 추가하기"
          onAction={handleCreatePress}
        />
      ) : (
        <FlatList
          data={contents}
          renderItem={renderContentItem}
          keyExtractor={(item) => item.id.toString()}
          contentContainerStyle={styles.listContent}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
        />
      )}

      {/* Floating Action Button */}
      {usage?.can_create && (
        <TouchableOpacity
          style={[styles.fab, { backgroundColor: colors.primary }]}
          onPress={handleCreatePress}
          activeOpacity={0.8}
        >
          <Text style={styles.fabText}>+</Text>
        </TouchableOpacity>
      )}

      {!usage?.can_create && contents.length > 0 && (
        <View style={[styles.limitWarning, { backgroundColor: colors.error }]}>
          <Text style={styles.limitWarningText}>
            콘텐츠 생성 한도에 도달했습니다. 구독을 업그레이드하세요.
          </Text>
        </View>
      )}
    </View>
  );
};

const getReviewModeLabel = (mode: string) => {
  const labels: Record<string, string> = {
    objective: '기억 확인',
    descriptive: '서술형',
    multiple_choice: '객관식',
    subjective: '주관식',
  };
  return labels[mode] || mode;
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9fafb',
  },
  usageContainer: {
    backgroundColor: '#fff',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  usageHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  usageText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
  },
  tierText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#6b7280',
    backgroundColor: '#f3f4f6',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
  },
  usageBar: {
    height: 6,
    backgroundColor: '#e5e7eb',
    borderRadius: 3,
    overflow: 'hidden',
  },
  usageProgress: {
    height: '100%',
    borderRadius: 3,
  },
  listContent: {
    padding: 16,
  },
  contentCard: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 18,
    marginBottom: 14,
    borderWidth: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 3,
  },
  contentHeader: {
    marginBottom: 12,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  contentTitle: {
    fontSize: 18,
    fontWeight: '600',
    flex: 1,
    marginRight: 8,
  },
  validatedBadge: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: '#22c55e',
    justifyContent: 'center',
    alignItems: 'center',
  },
  validatedText: {
    fontSize: 14,
    color: '#ffffff',
    fontWeight: 'bold',
  },
  categoryTag: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
    alignSelf: 'flex-start',
  },
  categoryText: {
    fontSize: 12,
    fontWeight: '600',
  },
  contentPreview: {
    fontSize: 15,
    lineHeight: 22,
    marginBottom: 14,
  },
  contentFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  reviewModeBadge: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 8,
  },
  reviewModeText: {
    fontSize: 12,
    fontWeight: '500',
  },
  contentStats: {
    flexDirection: 'row',
    gap: 12,
    alignItems: 'center',
  },
  statItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  statIcon: {
    fontSize: 14,
  },
  statsText: {
    fontSize: 13,
    fontWeight: '500',
  },
  fab: {
    position: 'absolute',
    right: 20,
    bottom: 20,
    width: 64,
    height: 64,
    borderRadius: 32,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.25,
    shadowRadius: 12,
    elevation: 10,
  },
  fabText: {
    fontSize: 36,
    color: '#fff',
    fontWeight: '300',
    lineHeight: 36,
  },
  limitWarning: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: '#fef3c7',
    padding: 12,
    borderTopWidth: 1,
    borderTopColor: '#fbbf24',
  },
  limitWarningText: {
    fontSize: 12,
    color: '#92400e',
    textAlign: 'center',
  },
});

export default ContentListScreen;
