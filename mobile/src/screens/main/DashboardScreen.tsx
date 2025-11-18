import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { useQuery } from '@tanstack/react-query';
import { useNavigation } from '@react-navigation/native';
import { BottomTabNavigationProp } from '@react-navigation/bottom-tabs';
import { reviewAPI } from '../../api';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';
import { MainTabParamList } from '../../navigation/types';

type NavigationProp = BottomTabNavigationProp<MainTabParamList, 'DashboardTab'>;

const DashboardScreen = () => {
  const { user } = useAuth();
  const { colors } = useTheme();
  const navigation = useNavigation<NavigationProp>();

  const { data: dashboardData, isLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => reviewAPI.getDashboard(),
  });

  // Get greeting based on time
  const currentHour = new Date().getHours();
  const greeting =
    currentHour < 12
      ? '좋은 아침이에요'
      : currentHour < 18
      ? '좋은 오후에요'
      : '좋은 저녁이에요';

  const userName = user?.email?.split('@')[0] || '사용자';

  if (isLoading) {
    return (
      <View style={[styles.loadingContainer, { backgroundColor: colors.background }]}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  return (
    <ScrollView style={[styles.container, { backgroundColor: colors.background }]}>
      {/* Hero Section with Gradient */}
      <LinearGradient
        colors={[colors.gradient.start, colors.gradient.middle, colors.gradient.end]}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={styles.heroSection}
      >
        <View style={styles.heroContent}>
          <Text style={styles.heroGreeting}>
            {greeting}, {userName}님! 👋
          </Text>
          <Text style={styles.heroSubtitle}>
            오늘도 꾸준한 학습으로 목표를 향해 나아가세요
          </Text>
        </View>
        {/* Decorative circles */}
        <View style={styles.decorCircle1} />
        <View style={styles.decorCircle2} />
      </LinearGradient>

      {/* Stats Cards */}
      <View style={styles.statsContainer}>
        <View style={[styles.statCard, { backgroundColor: colors.card }]}>
          <View style={[styles.statIconContainer, { backgroundColor: colors.primaryLight + '20' }]}>
            <Text style={styles.statIcon}>📅</Text>
          </View>
          <Text style={[styles.statValue, { color: colors.primary }]}>
            {dashboardData?.today_reviews || 0}
          </Text>
          <Text style={[styles.statLabel, { color: colors.textSecondary }]}>오늘의 복습</Text>
        </View>

        <View style={[styles.statCard, { backgroundColor: colors.card }]}>
          <View style={[styles.statIconContainer, { backgroundColor: colors.warning + '20' }]}>
            <Text style={styles.statIcon}>⏳</Text>
          </View>
          <Text style={[styles.statValue, { color: colors.warning }]}>
            {dashboardData?.pending_reviews || 0}
          </Text>
          <Text style={[styles.statLabel, { color: colors.textSecondary }]}>대기 중</Text>
        </View>

        <View style={[styles.statCard, { backgroundColor: colors.card }]}>
          <View style={[styles.statIconContainer, { backgroundColor: colors.primary + '20' }]}>
            <Text style={styles.statIcon}>📚</Text>
          </View>
          <Text style={[styles.statValue, { color: colors.primary }]}>
            {dashboardData?.total_content || 0}
          </Text>
          <Text style={[styles.statLabel, { color: colors.textSecondary }]}>전체 콘텐츠</Text>
        </View>

        <View style={[styles.statCard, { backgroundColor: colors.card }]}>
          <View style={[styles.statIconContainer, { backgroundColor: colors.success + '20' }]}>
            <Text style={styles.statIcon}>✨</Text>
          </View>
          <Text style={[styles.statValue, { color: colors.success }]}>
            {dashboardData?.success_rate
              ? `${dashboardData.success_rate.toFixed(1)}%`
              : '0%'}
          </Text>
          <Text style={[styles.statLabel, { color: colors.textSecondary }]}>성공률</Text>
        </View>
      </View>

      {/* Action Cards */}
      <View style={styles.actionsSection}>
        <Text style={[styles.sectionTitle, { color: colors.text }]}>빠른 실행</Text>

        <TouchableOpacity
          style={[styles.actionCard, { backgroundColor: colors.card, borderColor: colors.border }]}
          onPress={() => navigation.navigate('ReviewTab')}
          activeOpacity={0.7}
        >
          <LinearGradient
            colors={[colors.gradient.start, colors.gradient.end]}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 0 }}
            style={styles.actionGradient}
          >
            <View style={styles.actionIconContainer}>
              <Text style={styles.actionIcon}>🎯</Text>
            </View>
            <View style={styles.actionContent}>
              <Text style={styles.actionTitle}>오늘의 복습 시작</Text>
              <Text style={styles.actionSubtitle}>
                {dashboardData?.today_reviews || 0}개의 복습 대기 중
              </Text>
            </View>
            <Text style={styles.actionArrow}>→</Text>
          </LinearGradient>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.actionCard, { backgroundColor: colors.card, borderColor: colors.border }]}
          onPress={() => navigation.navigate('ContentTab', { screen: 'ContentCreate' })}
          activeOpacity={0.7}
        >
          <View style={[styles.actionCardContent, { paddingHorizontal: 16, paddingVertical: 20 }]}>
            <View style={[styles.actionIconContainer, { backgroundColor: colors.primary + '15' }]}>
              <Text style={styles.actionIcon}>✏️</Text>
            </View>
            <View style={styles.actionContent}>
              <Text style={[styles.actionTitle, { color: colors.text }]}>새 콘텐츠 추가</Text>
              <Text style={[styles.actionSubtitle, { color: colors.textSecondary }]}>
                학습할 내용을 추가하세요
              </Text>
            </View>
            <Text style={[styles.actionArrow, { color: colors.primary }]}>→</Text>
          </View>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.actionCard, { backgroundColor: colors.card, borderColor: colors.border }]}
          onPress={() => navigation.navigate('ExamsTab', { screen: 'ExamList' })}
          activeOpacity={0.7}
        >
          <View style={[styles.actionCardContent, { paddingHorizontal: 16, paddingVertical: 20 }]}>
            <View style={[styles.actionIconContainer, { backgroundColor: colors.warning + '15' }]}>
              <Text style={styles.actionIcon}>📝</Text>
            </View>
            <View style={styles.actionContent}>
              <Text style={[styles.actionTitle, { color: colors.text }]}>AI 주간 시험</Text>
              <Text style={[styles.actionSubtitle, { color: colors.textSecondary }]}>
                실력을 확인해보세요
              </Text>
            </View>
            <Text style={[styles.actionArrow, { color: colors.primary }]}>→</Text>
          </View>
        </TouchableOpacity>
      </View>

      {/* Recent Activity */}
      <View style={[styles.activitySection, { backgroundColor: colors.card, borderColor: colors.border }]}>
        <View style={styles.activityHeader}>
          <Text style={[styles.activityTitle, { color: colors.text }]}>📊 최근 활동</Text>
        </View>
        <View style={styles.activityContent}>
          <View style={styles.activityItem}>
            <Text style={[styles.activityLabel, { color: colors.textSecondary }]}>최근 30일 복습</Text>
            <Text style={[styles.activityValue, { color: colors.primary }]}>
              {dashboardData?.total_reviews_30_days || 0}회
            </Text>
          </View>
        </View>
      </View>

      {/* Bottom Padding */}
      <View style={{ height: 40 }} />
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },

  // Hero Section
  heroSection: {
    padding: 32,
    borderBottomLeftRadius: 24,
    borderBottomRightRadius: 24,
    overflow: 'hidden',
    position: 'relative',
  },
  heroContent: {
    zIndex: 10,
  },
  heroGreeting: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 8,
  },
  heroSubtitle: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.9)',
    lineHeight: 22,
  },
  decorCircle1: {
    position: 'absolute',
    top: -80,
    right: -80,
    width: 200,
    height: 200,
    borderRadius: 100,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
  },
  decorCircle2: {
    position: 'absolute',
    bottom: -60,
    left: -60,
    width: 150,
    height: 150,
    borderRadius: 75,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
  },

  // Stats Section
  statsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: 16,
    paddingTop: 24,
    gap: 12,
  },
  statCard: {
    width: '48%',
    minWidth: 150,
    padding: 20,
    borderRadius: 16,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  statIconContainer: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  statIcon: {
    fontSize: 24,
  },
  statValue: {
    fontSize: 28,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 13,
    fontWeight: '500',
  },

  // Actions Section
  actionsSection: {
    padding: 16,
    paddingTop: 8,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 16,
    paddingHorizontal: 4,
  },
  actionCard: {
    borderRadius: 16,
    marginBottom: 12,
    overflow: 'hidden',
    borderWidth: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 2,
  },
  actionGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 20,
  },
  actionCardContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  actionIconContainer: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  actionIcon: {
    fontSize: 28,
  },
  actionContent: {
    flex: 1,
  },
  actionTitle: {
    fontSize: 17,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: 4,
  },
  actionSubtitle: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.8)',
  },
  actionArrow: {
    fontSize: 24,
    color: '#ffffff',
    fontWeight: 'bold',
  },

  // Activity Section
  activitySection: {
    margin: 16,
    marginTop: 8,
    padding: 20,
    borderRadius: 16,
    borderWidth: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 2,
  },
  activityHeader: {
    marginBottom: 16,
  },
  activityTitle: {
    fontSize: 18,
    fontWeight: '600',
  },
  activityContent: {
    gap: 12,
  },
  activityItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
  },
  activityLabel: {
    fontSize: 15,
  },
  activityValue: {
    fontSize: 17,
    fontWeight: '600',
  },
});

export default DashboardScreen;
