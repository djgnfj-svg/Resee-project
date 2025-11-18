import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { ExamsStackParamList } from './types';
import { useTheme } from '../contexts/ThemeContext';

// Import screens
import ExamListScreen from '../screens/exams/ExamListScreen';
import ExamDetailScreen from '../screens/exams/ExamDetailScreen';
import ExamCreateScreen from '../screens/exams/ExamCreateScreen';
import ExamResultScreen from '../screens/exams/ExamResultScreen';

const Stack = createNativeStackNavigator<ExamsStackParamList>();

const ExamsNavigator = () => {
  const { colors } = useTheme();

  return (
    <Stack.Navigator
      screenOptions={{
        headerStyle: {
          backgroundColor: colors.card,
        },
        headerTintColor: colors.text,
        headerTitleStyle: {
          fontWeight: 'bold',
        },
      }}
    >
      <Stack.Screen
        name="ExamList"
        component={ExamListScreen}
        options={{ title: 'AI 주간 시험' }}
      />
      <Stack.Screen
        name="ExamDetail"
        component={ExamDetailScreen}
        options={{ title: '시험 풀기' }}
      />
      <Stack.Screen
        name="ExamCreate"
        component={ExamCreateScreen}
        options={{ title: '시험 생성' }}
      />
      <Stack.Screen
        name="ExamResult"
        component={ExamResultScreen}
        options={{ title: '시험 결과' }}
      />
    </Stack.Navigator>
  );
};

export default ExamsNavigator;
