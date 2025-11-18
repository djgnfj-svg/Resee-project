/**
 * Review Navigator
 *
 * Stack navigator for review-related screens
 */

import React from 'react';
import {createStackNavigator} from '@react-navigation/stack';
import ReviewListScreen from '@screens/Review/ReviewListScreen';
import ReviewSessionScreen from '@screens/Review/ReviewSessionScreen';
import ReviewResultScreen from '@screens/Review/ReviewResultScreen';
import type {ReviewStackParamList} from '@types/index';

const Stack = createStackNavigator<ReviewStackParamList>();

const ReviewNavigator: React.FC = () => {
  return (
    <Stack.Navigator
      screenOptions={{
        headerStyle: {
          backgroundColor: '#FFFFFF',
          elevation: 0,
          shadowOpacity: 0,
          borderBottomWidth: 1,
          borderBottomColor: '#E5E7EB',
        },
        headerTitleStyle: {
          fontWeight: '600',
          fontSize: 18,
        },
        headerTintColor: '#1F2937',
      }}>
      <Stack.Screen
        name="ReviewList"
        component={ReviewListScreen}
        options={{
          title: '복습 목록',
        }}
      />
      <Stack.Screen
        name="ReviewSession"
        component={ReviewSessionScreen}
        options={{
          title: '복습 진행',
          headerLeft: () => null, // 뒤로가기 버튼 비활성화
        }}
      />
      <Stack.Screen
        name="ReviewResult"
        component={ReviewResultScreen}
        options={{
          title: '복습 결과',
        }}
      />
    </Stack.Navigator>
  );
};

export default ReviewNavigator;
