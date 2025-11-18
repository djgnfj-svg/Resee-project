import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { reviewAPI } from '../../api';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';

const DashboardScreen = () => {
  const { user } = useAuth();
  const { colors } = useTheme();

  const { data: dashboardData, isLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => reviewAPI.getDashboard(),
  });

  if (isLoading) {
    return (
      <View style={[styles.loadingContainer, { backgroundColor: colors.background }]}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  return (
    <ScrollView style={[styles.container, { backgroundColor: colors.background }]}>
      <View style={[styles.header, { backgroundColor: colors.card, borderBottomColor: colors.border }]}>
        <Text style={[styles.greeting, { color: colors.text }]}>안녕하세요, {user?.email}님!</Text>
        <Text style={[styles.subtitle, { color: colors.textSecondary }]}>오늘도 학습을 시작해보세요</Text>
      </View>

      <View style={styles.statsContainer}>
        <View style={[styles.statCard, { backgroundColor: colors.card }]}>
          <Text style={[styles.statValue, { color: colors.primary }]}>{dashboardData?.today_reviews || 0}</Text>
          <Text style={[styles.statLabel, { color: colors.textSecondary }]}>오늘의 복습</Text>
        </View>

        <View style={[styles.statCard, { backgroundColor: colors.card }]}>
          <Text style={[styles.statValue, { color: colors.primary }]}>
            {dashboardData?.pending_reviews || 0}
          </Text>
          <Text style={[styles.statLabel, { color: colors.textSecondary }]}>대기 중</Text>
        </View>

        <View style={[styles.statCard, { backgroundColor: colors.card }]}>
          <Text style={[styles.statValue, { color: colors.primary }]}>
            {dashboardData?.total_content || 0}
          </Text>
          <Text style={[styles.statLabel, { color: colors.textSecondary }]}>전체 콘텐츠</Text>
        </View>

        <View style={[styles.statCard, { backgroundColor: colors.card }]}>
          <Text style={[styles.statValue, { color: colors.primary }]}>
            {dashboardData?.success_rate
              ? `${dashboardData.success_rate.toFixed(1)}%`
              : '0%'}
          </Text>
          <Text style={[styles.statLabel, { color: colors.textSecondary }]}>성공률</Text>
        </View>
      </View>

      <View style={styles.section}>
        <Text style={[styles.sectionTitle, { color: colors.text }]}>빠른 실행</Text>

        <TouchableOpacity style={[styles.actionButton, { backgroundColor: colors.primary }]}>
          <Text style={styles.actionButtonText}>오늘의 복습 시작</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.actionButton, styles.actionButtonSecondary, { backgroundColor: colors.card, borderColor: colors.primary }]}
        >
          <Text style={[styles.actionButtonTextSecondary, { color: colors.primary }]}>새 콘텐츠 추가</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.actionButton, styles.actionButtonSecondary, { backgroundColor: colors.card, borderColor: colors.primary }]}
        >
          <Text style={[styles.actionButtonTextSecondary, { color: colors.primary }]}>AI 주간 시험</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.section}>
        <Text style={[styles.sectionTitle, { color: colors.text }]}>최근 활동</Text>
        <Text style={[styles.infoText, { color: colors.textSecondary }]}>
          최근 30일간 {dashboardData?.total_reviews_30_days || 0}번의 복습을
          완료했습니다.
        </Text>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9fafb',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    padding: 20,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  greeting: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#111827',
  },
  subtitle: {
    fontSize: 14,
    color: '#6b7280',
    marginTop: 4,
  },
  statsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: 10,
  },
  statCard: {
    width: '48%',
    backgroundColor: '#fff',
    padding: 20,
    margin: '1%',
    borderRadius: 12,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  statValue: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#3b82f6',
  },
  statLabel: {
    fontSize: 14,
    color: '#6b7280',
    marginTop: 4,
  },
  section: {
    padding: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 12,
  },
  actionButton: {
    backgroundColor: '#3b82f6',
    padding: 16,
    borderRadius: 8,
    marginBottom: 12,
    alignItems: 'center',
  },
  actionButtonSecondary: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#3b82f6',
  },
  actionButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  actionButtonTextSecondary: {
    color: '#3b82f6',
    fontSize: 16,
    fontWeight: 'bold',
  },
  infoText: {
    fontSize: 14,
    color: '#6b7280',
    lineHeight: 20,
  },
});

export default DashboardScreen;
