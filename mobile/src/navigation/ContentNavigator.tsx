/**
 * Content Navigator
 *
 * Stack navigator for content-related screens
 */

import React from 'react';
import {createStackNavigator} from '@react-navigation/stack';
import ContentListScreen from '@screens/Content/ContentListScreen';
import ContentDetailScreen from '@screens/Content/ContentDetailScreen';
import ContentCreateScreen from '@screens/Content/ContentCreateScreen';
import ContentEditScreen from '@screens/Content/ContentEditScreen';
import type {ContentStackParamList} from '@types/index';

const Stack = createStackNavigator<ContentStackParamList>();

const ContentNavigator: React.FC = () => {
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
        name="ContentList"
        component={ContentListScreen}
        options={{
          title: '학습 콘텐츠',
        }}
      />
      <Stack.Screen
        name="ContentDetail"
        component={ContentDetailScreen}
        options={{
          title: '콘텐츠 상세',
        }}
      />
      <Stack.Screen
        name="ContentCreate"
        component={ContentCreateScreen}
        options={{
          title: '새 콘텐츠 작성',
        }}
      />
      <Stack.Screen
        name="ContentEdit"
        component={ContentEditScreen}
        options={{
          title: '콘텐츠 수정',
        }}
      />
    </Stack.Navigator>
  );
};

export default ContentNavigator;
