import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { MainTabParamList } from './types';
import ContentNavigator from './ContentNavigator';
import ExamsNavigator from './ExamsNavigator';
import { useTheme } from '../contexts/ThemeContext';

// Import screens
import DashboardScreen from '../screens/main/DashboardScreen';
import ReviewScreen from '../screens/main/ReviewScreen';
import ProfileScreen from '../screens/main/ProfileScreen';

const Tab = createBottomTabNavigator<MainTabParamList>();

const MainNavigator = () => {
  const { colors, isDark } = useTheme();

  return (
    <Tab.Navigator
      screenOptions={{
        headerShown: true,
        headerStyle: {
          backgroundColor: colors.card,
        },
        headerTintColor: colors.text,
        headerTitleStyle: {
          fontWeight: 'bold',
        },
        tabBarStyle: {
          paddingBottom: 5,
          paddingTop: 5,
          height: 60,
          backgroundColor: colors.card,
          borderTopColor: colors.border,
        },
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.textSecondary,
      }}
    >
      <Tab.Screen
        name="DashboardTab"
        component={DashboardScreen}
        options={{
          title: '대시보드',
          tabBarLabel: '홈',
        }}
      />
      <Tab.Screen
        name="ContentTab"
        component={ContentNavigator}
        options={{
          title: '학습 콘텐츠',
          tabBarLabel: '콘텐츠',
          headerShown: false,
        }}
      />
      <Tab.Screen
        name="ReviewTab"
        component={ReviewScreen}
        options={{
          title: '복습',
          tabBarLabel: '복습',
        }}
      />
      <Tab.Screen
        name="ExamsTab"
        component={ExamsNavigator}
        options={{
          title: '시험',
          tabBarLabel: '시험',
          headerShown: false,
        }}
      />
      <Tab.Screen
        name="ProfileTab"
        component={ProfileScreen}
        options={{
          title: '프로필',
          tabBarLabel: '내 정보',
        }}
      />
    </Tab.Navigator>
  );
};

export default MainNavigator;
