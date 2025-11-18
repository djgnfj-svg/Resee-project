/**
 * Forgot Password Screen
 */

import React from 'react';
import {View, StyleSheet} from 'react-native';
import {Text, Button} from 'react-native-paper';
import {useNavigation} from '@react-navigation/native';

const ForgotPasswordScreen: React.FC = () => {
  const navigation = useNavigation();

  return (
    <View style={styles.container}>
      <Text variant="headlineMedium">비밀번호 찾기</Text>
      <Text style={styles.description}>비밀번호 재설정 기능은 준비 중입니다.</Text>
      <Button mode="contained" onPress={() => navigation.goBack()}>
        로그인으로 돌아가기
      </Button>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
    backgroundColor: '#FFFFFF',
  },
  description: {
    marginVertical: 16,
    textAlign: 'center',
    color: '#6B7280',
  },
});

export default ForgotPasswordScreen;
