import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  Switch,
} from 'react-native';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';

const ProfileScreen = () => {
  const { user, logout } = useAuth();
  const { themeMode, setThemeMode, colors, isDark } = useTheme();

  const handleLogout = () => {
    Alert.alert('로그아웃', '로그아웃 하시겠습니까?', [
      { text: '취소', style: 'cancel' },
      {
        text: '로그아웃',
        style: 'destructive',
        onPress: async () => {
          try {
            await logout();
          } catch (error) {
            Alert.alert('오류', '로그아웃에 실패했습니다.');
          }
        },
      },
    ]);
  };

  return (
    <ScrollView style={[styles.container, { backgroundColor: colors.background }]}>
      <View style={[styles.header, { backgroundColor: colors.card, borderBottomColor: colors.border }]}>
        <View style={[styles.avatar, { backgroundColor: colors.primary }]}>
          <Text style={styles.avatarText}>
            {user?.email?.charAt(0).toUpperCase()}
          </Text>
        </View>
        <Text style={[styles.email, { color: colors.text }]}>{user?.email}</Text>
        <Text style={[styles.tier, { color: colors.textSecondary, backgroundColor: colors.surface }]}>
          {user?.subscription?.tier_display || 'FREE'}
        </Text>
      </View>

      <View style={[styles.section, { backgroundColor: colors.card, borderColor: colors.border }]}>
        <Text style={[styles.sectionTitle, { color: colors.textSecondary }]}>외관</Text>

        <View style={[styles.menuItem, { borderBottomColor: colors.border }]}>
          <View style={styles.menuItemRow}>
            <Text style={[styles.menuItemText, { color: colors.text }]}>다크 모드</Text>
            <Switch
              value={isDark}
              onValueChange={(value) => setThemeMode(value ? 'dark' : 'light')}
              trackColor={{ false: '#d1d5db', true: colors.primary }}
              thumbColor="#fff"
            />
          </View>
        </View>

        <TouchableOpacity
          style={[styles.menuItem, { borderBottomColor: colors.border }]}
          onPress={() => {
            Alert.alert(
              '테마 모드',
              '테마 모드를 선택하세요',
              [
                {
                  text: '라이트',
                  onPress: () => setThemeMode('light'),
                },
                {
                  text: '다크',
                  onPress: () => setThemeMode('dark'),
                },
                {
                  text: '시스템 설정',
                  onPress: () => setThemeMode('system'),
                },
                { text: '취소', style: 'cancel' },
              ]
            );
          }}
        >
          <View style={styles.menuItemRow}>
            <Text style={[styles.menuItemText, { color: colors.text }]}>테마 설정</Text>
            <Text style={[styles.menuItemValue, { color: colors.textSecondary }]}>
              {themeMode === 'system' ? '시스템 설정' : themeMode === 'dark' ? '다크' : '라이트'}
            </Text>
          </View>
        </TouchableOpacity>
      </View>

      <View style={[styles.section, { backgroundColor: colors.card, borderColor: colors.border }]}>
        <Text style={[styles.sectionTitle, { color: colors.textSecondary }]}>계정 설정</Text>

        <TouchableOpacity style={[styles.menuItem, { borderBottomColor: colors.border }]}>
          <Text style={[styles.menuItemText, { color: colors.text }]}>프로필 편집</Text>
        </TouchableOpacity>

        <TouchableOpacity style={[styles.menuItem, { borderBottomColor: colors.border }]}>
          <Text style={[styles.menuItemText, { color: colors.text }]}>비밀번호 변경</Text>
        </TouchableOpacity>

        <TouchableOpacity style={[styles.menuItem, { borderBottomColor: colors.border }]}>
          <Text style={[styles.menuItemText, { color: colors.text }]}>알림 설정</Text>
        </TouchableOpacity>
      </View>

      <View style={[styles.section, { backgroundColor: colors.card, borderColor: colors.border }]}>
        <Text style={[styles.sectionTitle, { color: colors.textSecondary }]}>구독</Text>

        <TouchableOpacity style={[styles.menuItem, { borderBottomColor: colors.border }]}>
          <Text style={[styles.menuItemText, { color: colors.text }]}>구독 관리</Text>
        </TouchableOpacity>
      </View>

      <View style={[styles.section, { backgroundColor: 'transparent', borderWidth: 0 }]}>
        <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
          <Text style={styles.logoutButtonText}>로그아웃</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.footer}>
        <Text style={[styles.footerText, { color: colors.textSecondary }]}>Resee v1.0.0</Text>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9fafb',
  },
  header: {
    backgroundColor: '#fff',
    padding: 30,
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  avatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#3b82f6',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  avatarText: {
    color: '#fff',
    fontSize: 32,
    fontWeight: 'bold',
  },
  email: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 4,
  },
  tier: {
    fontSize: 14,
    color: '#6b7280',
    paddingHorizontal: 12,
    paddingVertical: 4,
    backgroundColor: '#f3f4f6',
    borderRadius: 12,
  },
  section: {
    marginTop: 20,
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderBottomWidth: 1,
    borderColor: '#e5e7eb',
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6b7280',
    paddingHorizontal: 20,
    paddingTop: 12,
    paddingBottom: 8,
  },
  menuItem: {
    padding: 16,
    paddingHorizontal: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
  },
  menuItemText: {
    fontSize: 16,
    color: '#111827',
  },
  menuItemRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  menuItemValue: {
    fontSize: 14,
    color: '#6b7280',
  },
  logoutButton: {
    margin: 20,
    padding: 16,
    backgroundColor: '#ef4444',
    borderRadius: 8,
    alignItems: 'center',
  },
  logoutButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  footer: {
    padding: 20,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 12,
    color: '#9ca3af',
  },
});

export default ProfileScreen;
