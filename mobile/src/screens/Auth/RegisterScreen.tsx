/**
 * Register Screen
 */

import React, {useState} from 'react';
import {
  View,
  StyleSheet,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  Alert,
} from 'react-native';
import {TextInput, Button, Text, HelperText, Checkbox} from 'react-native-paper';
import {useNavigation} from '@react-navigation/native';
import type {StackNavigationProp} from '@react-navigation/stack';
import {useAuth} from '@contexts/AuthContext';
import type {AuthStackParamList} from '@navigation/AuthNavigator';

type RegisterScreenNavigationProp = StackNavigationProp<
  AuthStackParamList,
  'Register'
>;

const RegisterScreen: React.FC = () => {
  const navigation = useNavigation<RegisterScreenNavigationProp>();
  const {register} = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [termsAgreed, setTermsAgreed] = useState(false);
  const [privacyAgreed, setPrivacyAgreed] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState<{[key: string]: string}>({});

  const validateForm = (): boolean => {
    const newErrors: {[key: string]: string} = {};

    if (!email.trim()) {
      newErrors.email = '이메일을 입력해주세요';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      newErrors.email = '올바른 이메일 형식이 아닙니다';
    }

    if (!password) {
      newErrors.password = '비밀번호를 입력해주세요';
    } else if (password.length < 8) {
      newErrors.password = '비밀번호는 최소 8자 이상이어야 합니다';
    }

    if (password !== passwordConfirm) {
      newErrors.passwordConfirm = '비밀번호가 일치하지 않습니다';
    }

    if (!termsAgreed) {
      newErrors.terms = '이용약관에 동의해주세요';
    }

    if (!privacyAgreed) {
      newErrors.privacy = '개인정보 처리방침에 동의해주세요';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleRegister = async () => {
    if (!validateForm()) {
      return;
    }

    setIsLoading(true);
    try {
      await register({
        email,
        password,
        password_confirm: passwordConfirm,
        terms_agreed: termsAgreed,
        privacy_agreed: privacyAgreed,
      });

      Alert.alert(
        '회원가입 완료',
        '회원가입이 완료되었습니다. 로그인해주세요.',
        [
          {
            text: '확인',
            onPress: () => navigation.navigate('Login'),
          },
        ],
      );
    } catch (error: any) {
      Alert.alert('회원가입 실패', error.message || '회원가입에 실패했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.header}>
          <Text variant="headlineMedium" style={styles.title}>
            회원가입
          </Text>
        </View>

        <View style={styles.form}>
          <TextInput
            label="이메일"
            value={email}
            onChangeText={setEmail}
            mode="outlined"
            keyboardType="email-address"
            autoCapitalize="none"
            error={!!errors.email}
            style={styles.input}
          />
          {errors.email && <HelperText type="error">{errors.email}</HelperText>}

          <TextInput
            label="비밀번호"
            value={password}
            onChangeText={setPassword}
            mode="outlined"
            secureTextEntry={!showPassword}
            error={!!errors.password}
            style={styles.input}
            right={
              <TextInput.Icon
                icon={showPassword ? 'eye-off' : 'eye'}
                onPress={() => setShowPassword(!showPassword)}
              />
            }
          />
          {errors.password && (
            <HelperText type="error">{errors.password}</HelperText>
          )}

          <TextInput
            label="비밀번호 확인"
            value={passwordConfirm}
            onChangeText={setPasswordConfirm}
            mode="outlined"
            secureTextEntry={!showPassword}
            error={!!errors.passwordConfirm}
            style={styles.input}
          />
          {errors.passwordConfirm && (
            <HelperText type="error">{errors.passwordConfirm}</HelperText>
          )}

          <View style={styles.checkboxContainer}>
            <Checkbox
              status={termsAgreed ? 'checked' : 'unchecked'}
              onPress={() => setTermsAgreed(!termsAgreed)}
            />
            <Text>이용약관에 동의합니다 (필수)</Text>
          </View>
          {errors.terms && <HelperText type="error">{errors.terms}</HelperText>}

          <View style={styles.checkboxContainer}>
            <Checkbox
              status={privacyAgreed ? 'checked' : 'unchecked'}
              onPress={() => setPrivacyAgreed(!privacyAgreed)}
            />
            <Text>개인정보 처리방침에 동의합니다 (필수)</Text>
          </View>
          {errors.privacy && (
            <HelperText type="error">{errors.privacy}</HelperText>
          )}

          <Button
            mode="contained"
            onPress={handleRegister}
            loading={isLoading}
            disabled={isLoading}
            style={styles.registerButton}>
            회원가입
          </Button>

          <Button
            mode="text"
            onPress={() => navigation.navigate('Login')}
            style={styles.textButton}>
            이미 계정이 있으신가요? 로그인
          </Button>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  scrollContent: {
    flexGrow: 1,
    padding: 24,
  },
  header: {
    marginBottom: 32,
    marginTop: 40,
  },
  title: {
    fontWeight: 'bold',
    color: '#1F2937',
  },
  form: {
    width: '100%',
  },
  input: {
    marginBottom: 4,
  },
  checkboxContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 8,
  },
  registerButton: {
    marginTop: 24,
    paddingVertical: 6,
  },
  textButton: {
    marginTop: 8,
  },
});

export default RegisterScreen;
