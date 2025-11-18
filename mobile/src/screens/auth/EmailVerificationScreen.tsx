import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { AuthStackScreenProps } from '../../navigation/types';

type Props = AuthStackScreenProps<'EmailVerification'>;

const EmailVerificationScreen: React.FC<Props> = () => {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>이메일 인증</Text>
      <Text style={styles.text}>이메일 인증 기능이 곧 추가됩니다.</Text>
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
  },
});

export default EmailVerificationScreen;
