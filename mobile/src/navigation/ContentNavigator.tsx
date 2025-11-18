import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { ContentStackParamList } from './types';
import { useTheme } from '../contexts/ThemeContext';

// Import screens
import ContentListScreen from '../screens/content/ContentListScreen';
import ContentDetailScreen from '../screens/content/ContentDetailScreen';
import ContentCreateScreen from '../screens/content/ContentCreateScreen';
import ContentEditScreen from '../screens/content/ContentEditScreen';

const Stack = createNativeStackNavigator<ContentStackParamList>();

const ContentNavigator = () => {
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
        name="ContentList"
        component={ContentListScreen}
        options={{ title: '학습 콘텐츠' }}
      />
      <Stack.Screen
        name="ContentDetail"
        component={ContentDetailScreen}
        options={{ title: '콘텐츠 상세' }}
      />
      <Stack.Screen
        name="ContentCreate"
        component={ContentCreateScreen}
        options={{ title: '콘텐츠 생성' }}
      />
      <Stack.Screen
        name="ContentEdit"
        component={ContentEditScreen}
        options={{ title: '콘텐츠 수정' }}
      />
    </Stack.Navigator>
  );
};

export default ContentNavigator;
