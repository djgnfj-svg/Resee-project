import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { AuthStackScreenProps } from '../../navigation/types';

type Props = AuthStackScreenProps<'VerificationPending'>;

const VerificationPendingScreen: React.FC<Props> = ({ route, navigation }) => {
  const { email } = route.params;

  return (
    <View style={styles.container}>
      <Text style={styles.title}>이메일 인증 필요</Text>
      <Text style={styles.text}>
        {email}로 인증 이메일을 발송했습니다.{'\n'}
        이메일을 확인하여 인증을 완료해주세요.
      </Text>
      <TouchableOpacity
        style={styles.button}
        onPress={() => navigation.navigate('Login')}
      >
        <Text style={styles.buttonText}>로그인으로 돌아가기</Text>
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
    backgroundColor: '#fff',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  text: {
    fontSize: 16,
    color: '#6b7280',
    textAlign: 'center',
    marginBottom: 32,
  },
  button: {
    backgroundColor: '#3b82f6',
    padding: 16,
    borderRadius: 8,
    minWidth: 200,
    alignItems: 'center',
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});

export default VerificationPendingScreen;
