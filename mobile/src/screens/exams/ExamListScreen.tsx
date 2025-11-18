import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigation } from '@react-navigation/native';
import { BottomTabNavigationProp } from '@react-navigation/bottom-tabs';
import { examsAPI } from '../../api';
import { useTheme } from '../../contexts/ThemeContext';
import { Exam } from '../../types';
import { MainTabParamList } from '../../navigation/types';
import { LinearGradient } from 'expo-linear-gradient';

type NavigationProp = BottomTabNavigationProp<MainTabParamList, 'ExamsTab'>;

const ExamListScreen = () => {
  const { colors } = useTheme();
  const navigation = useNavigation<NavigationProp>();
  const queryClient = useQueryClient();
  const [refreshing, setRefreshing] = useState(false);

  const { data: examsData, isLoading } = useQuery({
    queryKey: ['exams'],
    queryFn: () => examsAPI.getExams(),
  });

  const exams = examsData?.results || [];

  const onRefresh = async () => {
    setRefreshing(true);
    await queryClient.invalidateQueries({ queryKey: ['exams'] });
    setRefreshing(false);
  };

  const handleCreateExam = () => {
    navigation.navigate('ExamsTab', { screen: 'ExamCreate' });
  };

  const handleExamPress = (examId: number) => {
    navigation.navigate('ExamsTab', { screen: 'ExamDetail', params: { id: examId } });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ready':
        return colors.success;
      case 'pending':
        return colors.warning;
      case 'failed':
        return colors.error;
      default:
        return colors.textSecondary;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'ready':
        return '준비 완료';
      case 'pending':
        return '생성 중';
      case 'failed':
        return '실패';
      default:
        return status;
    }
  };

  const renderExamItem = ({ item }: { item: Exam }) => (
    <TouchableOpacity
      style={[styles.examCard, { backgroundColor: colors.card, borderColor: colors.border }]}
      onPress={() => handleExamPress(item.id)}
      activeOpacity={0.7}
      disabled={item.status !== 'ready'}
    >
      <View style={styles.examHeader}>
        <View style={styles.examTitleRow}>
          <Text style={[styles.examTitle, { color: colors.text }]} numberOfLines={1}>
            {item.title || `시험 #${item.id}`}
          </Text>
          <View style={[styles.statusBadge, { backgroundColor: getStatusColor(item.status) + '20' }]}>
            <Text style={[styles.statusText, { color: getStatusColor(item.status) }]}>
              {getStatusText(item.status)}
            </Text>
          </View>
        </View>
        {item.description && (
          <Text style={[styles.examDescription, { color: colors.textSecondary }]} numberOfLines={2}>
            {item.description}
          </Text>
        )}
      </View>

      <View style={styles.examFooter}>
        <View style={styles.examInfo}>
          <View style={styles.infoItem}>
            <Text style={styles.infoIcon}>📝</Text>
            <Text style={[styles.infoText, { color: colors.textSecondary }]}>
              {item.total_questions}문제
            </Text>
          </View>
          {item.duration_minutes && (
            <View style={styles.infoItem}>
              <Text style={styles.infoIcon}>⏱️</Text>
              <Text style={[styles.infoText, { color: colors.textSecondary }]}>
                {item.duration_minutes}분
              </Text>
            </View>
          )}
        </View>
        <Text style={[styles.examDate, { color: colors.textSecondary }]}>
          {new Date(item.created_at).toLocaleDateString('ko-KR', {
            month: 'short',
            day: 'numeric',
          })}
        </Text>
      </View>
    </TouchableOpacity>
  );

  if (isLoading) {
    return (
      <View style={[styles.centerContainer, { backgroundColor: colors.background }]}>
        <ActivityIndicator size="large" color={colors.primary} />
        <Text style={[styles.loadingText, { color: colors.textSecondary }]}>
          시험 목록을 불러오는 중...
        </Text>
      </View>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      {/* Gradient Header */}
      <LinearGradient
        colors={[colors.gradient.start, colors.gradient.middle, colors.gradient.end]}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={styles.header}
      >
        <View style={styles.headerContent}>
          <Text style={styles.headerTitle}>📝 주간 시험</Text>
          <Text style={styles.headerSubtitle}>학습한 내용을 종합적으로 테스트해보세요</Text>
        </View>
        <TouchableOpacity
          style={styles.createButton}
          onPress={handleCreateExam}
          activeOpacity={0.8}
        >
          <Text style={styles.createButtonIcon}>+</Text>
          <Text style={styles.createButtonText}>새 시험 생성</Text>
        </TouchableOpacity>
      </LinearGradient>

      {exams.length === 0 ? (
        <View style={styles.emptyContainer}>
          <View style={[styles.emptyIconContainer, { backgroundColor: colors.primary + '20' }]}>
            <Text style={styles.emptyIcon}>📝</Text>
          </View>
          <Text style={[styles.emptyTitle, { color: colors.text }]}>
            아직 주간 시험이 없습니다
          </Text>
          <Text style={[styles.emptySubtitle, { color: colors.textSecondary }]}>
            새 주간 시험을 생성하여 학습 내용을 점검해보세요
          </Text>
          <TouchableOpacity
            style={[styles.emptyButton, { backgroundColor: colors.primary }]}
            onPress={handleCreateExam}
            activeOpacity={0.8}
          >
            <Text style={styles.emptyButtonText}>첫 시험 만들기</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <FlatList
          data={exams}
          renderItem={renderExamItem}
          keyExtractor={(item) => item.id.toString()}
          contentContainerStyle={styles.listContent}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
        />
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
  createButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#ffffff',
    paddingHorizontal: 20,
    paddingVertical: 14,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 4,
  },
  createButtonIcon: {
    fontSize: 24,
    fontWeight: '300',
    color: '#6366f1',
    marginRight: 8,
  },
  createButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#6366f1',
  },
  listContent: {
    padding: 16,
  },
  examCard: {
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
  examHeader: {
    marginBottom: 12,
  },
  examTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  examTitle: {
    fontSize: 18,
    fontWeight: '600',
    flex: 1,
    marginRight: 12,
  },
  statusBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
  },
  examDescription: {
    fontSize: 14,
    lineHeight: 20,
  },
  examFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  examInfo: {
    flexDirection: 'row',
    gap: 16,
  },
  infoItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  infoIcon: {
    fontSize: 14,
  },
  infoText: {
    fontSize: 13,
    fontWeight: '500',
  },
  examDate: {
    fontSize: 12,
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
    marginBottom: 24,
    lineHeight: 22,
  },
  emptyButton: {
    paddingHorizontal: 24,
    paddingVertical: 14,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 3,
  },
  emptyButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});

export default ExamListScreen;
