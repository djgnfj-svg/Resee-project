import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { useTheme } from '../../contexts/ThemeContext';

const ReviewScreen = () => {
  const { colors } = useTheme();

  return (
    <ScrollView style={[styles.container, { backgroundColor: colors.background }]}>
      <View style={styles.content}>
        <Text style={[styles.title, { color: colors.text }]}>복습</Text>
        <Text style={[styles.subtitle, { color: colors.textSecondary }]}>오늘의 복습을 시작하세요</Text>
        <Text style={[styles.comingSoon, { color: colors.textSecondary }]}>복습 기능이 곧 추가됩니다.</Text>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    padding: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    marginBottom: 20,
  },
  comingSoon: {
    fontSize: 14,
    textAlign: 'center',
    marginTop: 40,
  },
});

export default ReviewScreen;
