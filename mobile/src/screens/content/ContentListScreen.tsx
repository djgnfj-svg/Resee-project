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
        <Text style={[styles.contentTitle, { color: colors.text }]} numberOfLines={1}>
          {item.title}
        </Text>
        {item.is_ai_validated && (
          <View style={[styles.validatedBadge, { backgroundColor: colors.success }]}>
            <Text style={styles.validatedText}>✓ 검증됨</Text>
          </View>
        )}
      </View>

      <Text style={[styles.contentPreview, { color: colors.textSecondary }]} numberOfLines={2}>
        {item.content}
      </Text>

      <View style={styles.contentFooter}>
        {item.category && (
          <View style={[styles.categoryTag, { backgroundColor: colors.surface, borderColor: colors.border }]}>
            <Text style={[styles.categoryText, { color: colors.primary }]}>{item.category.name}</Text>
          </View>
        )}
        <View style={styles.contentStats}>
          <Text style={[styles.statsText, { color: colors.textSecondary }]}>복습 {item.review_count}회</Text>
          {item.next_review_date && (
            <Text style={[styles.statsText, { color: colors.textSecondary }]}> • 다음 복습: {new Date(item.next_review_date).toLocaleDateString()}</Text>
          )}
        </View>
      </View>

      <View style={[styles.reviewModeContainer, { backgroundColor: colors.surface }]}>
        <Text style={[styles.reviewModeText, { color: colors.textSecondary }]}>
          모드: {getReviewModeLabel(item.review_mode)}
        </Text>
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
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  contentHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  contentTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#111827',
    flex: 1,
    marginRight: 8,
  },
  validatedBadge: {
    backgroundColor: '#d1fae5',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  validatedText: {
    fontSize: 12,
    color: '#065f46',
    fontWeight: '600',
  },
  contentPreview: {
    fontSize: 14,
    color: '#6b7280',
    lineHeight: 20,
    marginBottom: 12,
  },
  contentFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  categoryTag: {
    backgroundColor: '#dbeafe',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  categoryText: {
    fontSize: 12,
    color: '#1e40af',
    fontWeight: '500',
  },
  contentStats: {
    flexDirection: 'row',
    flex: 1,
    marginLeft: 8,
  },
  statsText: {
    fontSize: 12,
    color: '#9ca3af',
  },
  reviewModeContainer: {
    marginTop: 4,
  },
  reviewModeText: {
    fontSize: 12,
    color: '#6b7280',
  },
  fab: {
    position: 'absolute',
    right: 20,
    bottom: 20,
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#3b82f6',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
    elevation: 8,
  },
  fabText: {
    fontSize: 32,
    color: '#fff',
    fontWeight: '300',
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
