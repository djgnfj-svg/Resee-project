import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { AuthStackScreenProps } from '../../navigation/types';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';

type Props = AuthStackScreenProps<'Register'>;

const RegisterScreen: React.FC<Props> = ({ navigation }) => {
  const { register } = useAuth();
  const { colors } = useTheme();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [termsAgreed, setTermsAgreed] = useState(false);
  const [privacyAgreed, setPrivacyAgreed] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleRegister = async () => {
    if (!email || !password || !passwordConfirm) {
      Alert.alert('오류', '모든 필드를 입력해주세요.');
      return;
    }

    if (password !== passwordConfirm) {
      Alert.alert('오류', '비밀번호가 일치하지 않습니다.');
      return;
    }

    if (!termsAgreed || !privacyAgreed) {
      Alert.alert('오류', '이용약관과 개인정보처리방침에 동의해주세요.');
      return;
    }

    setIsLoading(true);
    try {
      const response = await register({
        email,
        password,
        password_confirm: passwordConfirm,
        terms_agreed: termsAgreed,
        privacy_agreed: privacyAgreed,
      });

      if (response.data?.requires_email_verification) {
        navigation.replace('VerificationPending', { email });
      }
    } catch (error: any) {
      Alert.alert('회원가입 실패', error.userMessage || '회원가입에 실패했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={[styles.container, { backgroundColor: colors.background }]}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.content}>
          <Text style={[styles.title, { color: colors.text }]}>회원가입</Text>
          <Text style={[styles.subtitle, { color: colors.textSecondary }]}>Resee에 오신 것을 환영합니다</Text>

          <View style={styles.form}>
            <TextInput
              style={[styles.input, {
                backgroundColor: colors.surface,
                borderColor: colors.border,
                color: colors.text,
              }]}
              placeholder="이메일"
              placeholderTextColor={colors.textSecondary}
              value={email}
              onChangeText={setEmail}
              keyboardType="email-address"
              autoCapitalize="none"
              autoCorrect={false}
            />

            <TextInput
              style={[styles.input, {
                backgroundColor: colors.surface,
                borderColor: colors.border,
                color: colors.text,
              }]}
              placeholder="비밀번호 (8자 이상)"
              placeholderTextColor={colors.textSecondary}
              value={password}
              onChangeText={setPassword}
              secureTextEntry
              autoCapitalize="none"
            />

            <TextInput
              style={[styles.input, {
                backgroundColor: colors.surface,
                borderColor: colors.border,
                color: colors.text,
              }]}
              placeholder="비밀번호 확인"
              placeholderTextColor={colors.textSecondary}
              value={passwordConfirm}
              onChangeText={setPasswordConfirm}
              secureTextEntry
              autoCapitalize="none"
            />

            <TouchableOpacity
              style={styles.checkboxContainer}
              onPress={() => setTermsAgreed(!termsAgreed)}
            >
              <View style={[
                styles.checkbox,
                { borderColor: termsAgreed ? colors.primary : colors.border },
                termsAgreed && { backgroundColor: colors.primary }
              ]}>
                {termsAgreed && <Text style={styles.checkboxText}>✓</Text>}
              </View>
              <Text style={[styles.checkboxLabel, { color: colors.text }]}>이용약관에 동의합니다</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.checkboxContainer}
              onPress={() => setPrivacyAgreed(!privacyAgreed)}
            >
              <View style={[
                styles.checkbox,
                { borderColor: privacyAgreed ? colors.primary : colors.border },
                privacyAgreed && { backgroundColor: colors.primary }
              ]}>
                {privacyAgreed && <Text style={styles.checkboxText}>✓</Text>}
              </View>
              <Text style={[styles.checkboxLabel, { color: colors.text }]}>
                개인정보처리방침에 동의합니다
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[
                styles.button,
                { backgroundColor: colors.primary },
                isLoading && styles.buttonDisabled
              ]}
              onPress={handleRegister}
              disabled={isLoading}
            >
              <Text style={styles.buttonText}>
                {isLoading ? '처리 중...' : '회원가입'}
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.linkButton}
              onPress={() => navigation.navigate('Login')}
            >
              <Text style={[styles.linkText, { color: colors.primary }]}>이미 계정이 있으신가요? 로그인</Text>
            </TouchableOpacity>
          </View>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    justifyContent: 'center',
  },
  content: {
    padding: 20,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 10,
  },
  subtitle: {
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 30,
  },
  form: {
    width: '100%',
  },
  input: {
    borderWidth: 1,
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
    fontSize: 16,
  },
  checkboxContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  checkbox: {
    width: 24,
    height: 24,
    borderWidth: 2,
    borderRadius: 4,
    marginRight: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  checkboxText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  checkboxLabel: {
    fontSize: 14,
  },
  button: {
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 16,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  linkButton: {
    marginTop: 16,
    alignItems: 'center',
  },
  linkText: {
    fontSize: 14,
  },
});

export default RegisterScreen;
