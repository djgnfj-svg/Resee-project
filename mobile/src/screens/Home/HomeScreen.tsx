/**
 * Home Screen
 *
 * Dashboard with today's reviews and statistics
 */

import React, {useEffect} from 'react';
import {View, StyleSheet, ScrollView, RefreshControl} from 'react-native';
import {Card, Text, Button} from 'react-native-paper';
import {useQuery} from '@tanstack/react-query';
import {useNavigation} from '@react-navigation/native';
import {getDashboardStats, getTodayReviews} from '@api/review';
import {useAuth} from '@contexts/AuthContext';

const HomeScreen: React.FC = () => {
  const {user} = useAuth();
  const navigation = useNavigation();

  const {
    data: dashboardData,
    isLoading: dashboardLoading,
    refetch: refetchDashboard,
  } = useQuery({
    queryKey: ['dashboard'],
    queryFn: getDashboardStats,
  });

  const {
    data: todayReviews,
    isLoading: reviewsLoading,
    refetch: refetchReviews,
  } = useQuery({
    queryKey: ['todayReviews'],
    queryFn: getTodayReviews,
  });

  const handleRefresh = async () => {
    await Promise.all([refetchDashboard(), refetchReviews()]);
  };

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl
          refreshing={dashboardLoading || reviewsLoading}
          onRefresh={handleRefresh}
        />
      }>
      <View style={styles.header}>
        <Text variant="headlineSmall">
          안녕하세요, {user?.email?.split('@')[0]}님! 👋
        </Text>
        <Text variant="bodyMedium" style={styles.subtitle}>
          오늘도 열심히 복습해봐요
        </Text>
      </View>

      {/* Stats Cards */}
      <View style={styles.statsContainer}>
        <Card style={styles.statCard}>
          <Card.Content>
            <Text variant="titleLarge" style={styles.statValue}>
              {dashboardData?.today_reviews || 0}
            </Text>
            <Text variant="bodyMedium" style={styles.statLabel}>
              오늘 복습
            </Text>
          </Card.Content>
        </Card>

        <Card style={styles.statCard}>
          <Card.Content>
            <Text variant="titleLarge" style={styles.statValue}>
              {dashboardData?.pending_reviews || 0}
            </Text>
            <Text variant="bodyMedium" style={styles.statLabel}>
              대기 중
            </Text>
          </Card.Content>
        </Card>
      </View>

      <View style={styles.statsContainer}>
        <Card style={styles.statCard}>
          <Card.Content>
            <Text variant="titleLarge" style={styles.statValue}>
              {dashboardData?.total_content || 0}
            </Text>
            <Text variant="bodyMedium" style={styles.statLabel}>
              전체 콘텐츠
            </Text>
          </Card.Content>
        </Card>

        <Card style={styles.statCard}>
          <Card.Content>
            <Text variant="titleLarge" style={styles.statValue}>
              {dashboardData?.success_rate
                ? `${dashboardData.success_rate.toFixed(0)}%`
                : '0%'}
            </Text>
            <Text variant="bodyMedium" style={styles.statLabel}>
              성공률
            </Text>
          </Card.Content>
        </Card>
      </View>

      {/* Today's Reviews */}
      <Card style={styles.reviewCard}>
        <Card.Title title="오늘의 복습" />
        <Card.Content>
          {todayReviews && todayReviews.count > 0 ? (
            <>
              <Text variant="bodyLarge" style={styles.reviewCount}>
                {todayReviews.count}개의 복습이 예정되어 있습니다
              </Text>
              <Button
                mode="contained"
                onPress={() => navigation.navigate('Review' as never)}
                style={styles.reviewButton}>
                복습 시작하기
              </Button>
            </>
          ) : (
            <Text variant="bodyMedium" style={styles.noReviewText}>
              오늘 복습할 콘텐츠가 없습니다 🎉
            </Text>
          )}
        </Card.Content>
      </Card>

      {/* Quick Actions */}
      <Card style={styles.actionCard}>
        <Card.Title title="빠른 실행" />
        <Card.Content>
          <Button
            mode="outlined"
            onPress={() => navigation.navigate('Contents' as never)}
            style={styles.actionButton}>
            새 콘텐츠 작성
          </Button>
          <Button
            mode="outlined"
            onPress={() => navigation.navigate('Stats' as never)}
            style={styles.actionButton}>
            통계 보기
          </Button>
        </Card.Content>
      </Card>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  header: {
    padding: 20,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  subtitle: {
    marginTop: 4,
    color: '#6B7280',
  },
  statsContainer: {
    flexDirection: 'row',
    padding: 16,
    gap: 12,
  },
  statCard: {
    flex: 1,
  },
  statValue: {
    fontWeight: 'bold',
    color: '#3B82F6',
  },
  statLabel: {
    marginTop: 4,
    color: '#6B7280',
  },
  reviewCard: {
    margin: 16,
    marginTop: 8,
  },
  reviewCount: {
    marginBottom: 16,
  },
  reviewButton: {
    marginTop: 8,
  },
  noReviewText: {
    color: '#6B7280',
  },
  actionCard: {
    margin: 16,
    marginTop: 8,
    marginBottom: 32,
  },
  actionButton: {
    marginTop: 8,
  },
});

export default HomeScreen;
