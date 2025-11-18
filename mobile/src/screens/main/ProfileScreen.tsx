import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  Switch,
  Modal,
  TextInput,
  ActivityIndicator,
} from 'react-native';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';
import { authAPI, subscriptionAPI } from '../../api';
import { LinearGradient } from 'expo-linear-gradient';

const ProfileScreen = () => {
  const { user, logout } = useAuth();
  const { themeMode, setThemeMode, colors, isDark } = useTheme();
  const queryClient = useQueryClient();

  // Modal states
  const [profileModalVisible, setProfileModalVisible] = useState(false);
  const [passwordModalVisible, setPasswordModalVisible] = useState(false);
  const [notificationModalVisible, setNotificationModalVisible] = useState(false);
  const [subscriptionModalVisible, setSubscriptionModalVisible] = useState(false);

  // Profile edit form
  const [username, setUsername] = useState(user?.username || '');
  const [email, setEmail] = useState(user?.email || '');

  // Password change form
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newPasswordConfirm, setNewPasswordConfirm] = useState('');

  // Notification preferences
  const { data: notificationPrefs, isLoading: notifLoading } = useQuery({
    queryKey: ['notificationPreferences'],
    queryFn: () => authAPI.getNotificationPreferences(),
  });

  const [emailNotifications, setEmailNotifications] = useState(
    notificationPrefs?.email_notifications ?? true
  );
  const [reviewReminders, setReviewReminders] = useState(
    notificationPrefs?.review_reminders ?? true
  );

  // Subscription data
  const { data: subscription } = useQuery({
    queryKey: ['subscription'],
    queryFn: () => subscriptionAPI.getSubscription(),
  });

  const { data: tiers } = useQuery({
    queryKey: ['subscriptionTiers'],
    queryFn: () => subscriptionAPI.getTiers(),
  });

  // Update profile mutation
  const updateProfileMutation = useMutation({
    mutationFn: () => authAPI.updateProfile({ username, email }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profile'] });
      setProfileModalVisible(false);
      Alert.alert('성공', '프로필이 업데이트되었습니다.');
    },
    onError: (error: any) => {
      Alert.alert('오류', error.userMessage || '프로필 업데이트에 실패했습니다.');
    },
  });

  // Change password mutation
  const changePasswordMutation = useMutation({
    mutationFn: () =>
      authAPI.changePassword({
        current_password: currentPassword,
        new_password: newPassword,
        new_password_confirm: newPasswordConfirm,
      }),
    onSuccess: () => {
      setPasswordModalVisible(false);
      setCurrentPassword('');
      setNewPassword('');
      setNewPasswordConfirm('');
      Alert.alert('성공', '비밀번호가 변경되었습니다.');
    },
    onError: (error: any) => {
      Alert.alert('오류', error.userMessage || '비밀번호 변경에 실패했습니다.');
    },
  });

  // Update notification preferences mutation
  const updateNotificationMutation = useMutation({
    mutationFn: () =>
      authAPI.updateNotificationPreferences({
        email_notifications: emailNotifications,
        review_reminders: reviewReminders,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notificationPreferences'] });
      setNotificationModalVisible(false);
      Alert.alert('성공', '알림 설정이 저장되었습니다.');
    },
    onError: (error: any) => {
      Alert.alert('오류', error.userMessage || '알림 설정 저장에 실패했습니다.');
    },
  });

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

  const handleSaveProfile = () => {
    if (!username.trim() || !email.trim()) {
      Alert.alert('입력 오류', '모든 필드를 입력해주세요.');
      return;
    }
    updateProfileMutation.mutate();
  };

  const handleChangePassword = () => {
    if (!currentPassword || !newPassword || !newPasswordConfirm) {
      Alert.alert('입력 오류', '모든 필드를 입력해주세요.');
      return;
    }
    if (newPassword !== newPasswordConfirm) {
      Alert.alert('입력 오류', '새 비밀번호가 일치하지 않습니다.');
      return;
    }
    if (newPassword.length < 8) {
      Alert.alert('입력 오류', '비밀번호는 최소 8자 이상이어야 합니다.');
      return;
    }
    changePasswordMutation.mutate();
  };

  const handleSaveNotifications = () => {
    updateNotificationMutation.mutate();
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

        <TouchableOpacity
          style={[styles.menuItem, { borderBottomColor: colors.border }]}
          onPress={() => {
            setUsername(user?.username || '');
            setEmail(user?.email || '');
            setProfileModalVisible(true);
          }}
        >
          <Text style={[styles.menuItemText, { color: colors.text }]}>프로필 편집</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.menuItem, { borderBottomColor: colors.border }]}
          onPress={() => setPasswordModalVisible(true)}
        >
          <Text style={[styles.menuItemText, { color: colors.text }]}>비밀번호 변경</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.menuItem, { borderBottomColor: colors.border }]}
          onPress={() => {
            setEmailNotifications(notificationPrefs?.email_notifications ?? true);
            setReviewReminders(notificationPrefs?.review_reminders ?? true);
            setNotificationModalVisible(true);
          }}
        >
          <Text style={[styles.menuItemText, { color: colors.text }]}>알림 설정</Text>
        </TouchableOpacity>
      </View>

      <View style={[styles.section, { backgroundColor: colors.card, borderColor: colors.border }]}>
        <Text style={[styles.sectionTitle, { color: colors.textSecondary }]}>구독</Text>

        <TouchableOpacity
          style={[styles.menuItem, { borderBottomColor: colors.border }]}
          onPress={() => setSubscriptionModalVisible(true)}
        >
          <View style={styles.menuItemRow}>
            <Text style={[styles.menuItemText, { color: colors.text }]}>구독 관리</Text>
            <Text style={[styles.menuItemValue, { color: colors.textSecondary }]}>
              {subscription?.tier_display || 'FREE'}
            </Text>
          </View>
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

      {/* Profile Edit Modal */}
      <Modal
        visible={profileModalVisible}
        animationType="slide"
        transparent
        onRequestClose={() => setProfileModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={[styles.modalContent, { backgroundColor: colors.card }]}>
            <View style={[styles.modalHeader, { borderBottomColor: colors.border }]}>
              <Text style={[styles.modalTitle, { color: colors.text }]}>프로필 편집</Text>
              <TouchableOpacity onPress={() => setProfileModalVisible(false)}>
                <Text style={[styles.modalClose, { color: colors.textSecondary }]}>✕</Text>
              </TouchableOpacity>
            </View>

            <View style={styles.modalBody}>
              <View style={styles.inputGroup}>
                <Text style={[styles.inputLabel, { color: colors.text }]}>사용자명</Text>
                <TextInput
                  style={[styles.input, { backgroundColor: colors.background, color: colors.text, borderColor: colors.border }]}
                  value={username}
                  onChangeText={setUsername}
                  placeholder="사용자명"
                  placeholderTextColor={colors.textSecondary}
                />
              </View>

              <View style={styles.inputGroup}>
                <Text style={[styles.inputLabel, { color: colors.text }]}>이메일</Text>
                <TextInput
                  style={[styles.input, { backgroundColor: colors.background, color: colors.text, borderColor: colors.border }]}
                  value={email}
                  onChangeText={setEmail}
                  placeholder="email@example.com"
                  placeholderTextColor={colors.textSecondary}
                  keyboardType="email-address"
                  autoCapitalize="none"
                />
              </View>
            </View>

            <View style={[styles.modalFooter, { borderTopColor: colors.border }]}>
              <TouchableOpacity
                style={[styles.modalButton, styles.cancelButton, { backgroundColor: colors.surface }]}
                onPress={() => setProfileModalVisible(false)}
              >
                <Text style={[styles.cancelButtonText, { color: colors.text }]}>취소</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.modalButton, styles.saveButton, { backgroundColor: colors.primary }]}
                onPress={handleSaveProfile}
                disabled={updateProfileMutation.isPending}
              >
                {updateProfileMutation.isPending ? (
                  <ActivityIndicator color="#ffffff" />
                ) : (
                  <Text style={styles.saveButtonText}>저장</Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      {/* Password Change Modal */}
      <Modal
        visible={passwordModalVisible}
        animationType="slide"
        transparent
        onRequestClose={() => setPasswordModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={[styles.modalContent, { backgroundColor: colors.card }]}>
            <View style={[styles.modalHeader, { borderBottomColor: colors.border }]}>
              <Text style={[styles.modalTitle, { color: colors.text }]}>비밀번호 변경</Text>
              <TouchableOpacity onPress={() => setPasswordModalVisible(false)}>
                <Text style={[styles.modalClose, { color: colors.textSecondary }]}>✕</Text>
              </TouchableOpacity>
            </View>

            <View style={styles.modalBody}>
              <View style={styles.inputGroup}>
                <Text style={[styles.inputLabel, { color: colors.text }]}>현재 비밀번호</Text>
                <TextInput
                  style={[styles.input, { backgroundColor: colors.background, color: colors.text, borderColor: colors.border }]}
                  value={currentPassword}
                  onChangeText={setCurrentPassword}
                  placeholder="현재 비밀번호"
                  placeholderTextColor={colors.textSecondary}
                  secureTextEntry
                />
              </View>

              <View style={styles.inputGroup}>
                <Text style={[styles.inputLabel, { color: colors.text }]}>새 비밀번호</Text>
                <TextInput
                  style={[styles.input, { backgroundColor: colors.background, color: colors.text, borderColor: colors.border }]}
                  value={newPassword}
                  onChangeText={setNewPassword}
                  placeholder="새 비밀번호 (최소 8자)"
                  placeholderTextColor={colors.textSecondary}
                  secureTextEntry
                />
              </View>

              <View style={styles.inputGroup}>
                <Text style={[styles.inputLabel, { color: colors.text }]}>새 비밀번호 확인</Text>
                <TextInput
                  style={[styles.input, { backgroundColor: colors.background, color: colors.text, borderColor: colors.border }]}
                  value={newPasswordConfirm}
                  onChangeText={setNewPasswordConfirm}
                  placeholder="새 비밀번호 확인"
                  placeholderTextColor={colors.textSecondary}
                  secureTextEntry
                />
              </View>
            </View>

            <View style={[styles.modalFooter, { borderTopColor: colors.border }]}>
              <TouchableOpacity
                style={[styles.modalButton, styles.cancelButton, { backgroundColor: colors.surface }]}
                onPress={() => {
                  setPasswordModalVisible(false);
                  setCurrentPassword('');
                  setNewPassword('');
                  setNewPasswordConfirm('');
                }}
              >
                <Text style={[styles.cancelButtonText, { color: colors.text }]}>취소</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.modalButton, styles.saveButton, { backgroundColor: colors.primary }]}
                onPress={handleChangePassword}
                disabled={changePasswordMutation.isPending}
              >
                {changePasswordMutation.isPending ? (
                  <ActivityIndicator color="#ffffff" />
                ) : (
                  <Text style={styles.saveButtonText}>변경</Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      {/* Notification Settings Modal */}
      <Modal
        visible={notificationModalVisible}
        animationType="slide"
        transparent
        onRequestClose={() => setNotificationModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={[styles.modalContent, { backgroundColor: colors.card }]}>
            <View style={[styles.modalHeader, { borderBottomColor: colors.border }]}>
              <Text style={[styles.modalTitle, { color: colors.text }]}>알림 설정</Text>
              <TouchableOpacity onPress={() => setNotificationModalVisible(false)}>
                <Text style={[styles.modalClose, { color: colors.textSecondary }]}>✕</Text>
              </TouchableOpacity>
            </View>

            <View style={styles.modalBody}>
              <View style={[styles.settingItem, { borderBottomColor: colors.border }]}>
                <View>
                  <Text style={[styles.settingLabel, { color: colors.text }]}>이메일 알림</Text>
                  <Text style={[styles.settingDescription, { color: colors.textSecondary }]}>
                    중요한 업데이트를 이메일로 받습니다
                  </Text>
                </View>
                <Switch
                  value={emailNotifications}
                  onValueChange={setEmailNotifications}
                  trackColor={{ false: '#d1d5db', true: colors.primary }}
                  thumbColor="#fff"
                />
              </View>

              <View style={[styles.settingItem, { borderBottomColor: colors.border }]}>
                <View>
                  <Text style={[styles.settingLabel, { color: colors.text }]}>복습 알림</Text>
                  <Text style={[styles.settingDescription, { color: colors.textSecondary }]}>
                    복습할 시간이 되면 알림을 받습니다
                  </Text>
                </View>
                <Switch
                  value={reviewReminders}
                  onValueChange={setReviewReminders}
                  trackColor={{ false: '#d1d5db', true: colors.primary }}
                  thumbColor="#fff"
                />
              </View>
            </View>

            <View style={[styles.modalFooter, { borderTopColor: colors.border }]}>
              <TouchableOpacity
                style={[styles.modalButton, styles.cancelButton, { backgroundColor: colors.surface }]}
                onPress={() => setNotificationModalVisible(false)}
              >
                <Text style={[styles.cancelButtonText, { color: colors.text }]}>취소</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.modalButton, styles.saveButton, { backgroundColor: colors.primary }]}
                onPress={handleSaveNotifications}
                disabled={updateNotificationMutation.isPending}
              >
                {updateNotificationMutation.isPending ? (
                  <ActivityIndicator color="#ffffff" />
                ) : (
                  <Text style={styles.saveButtonText}>저장</Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      {/* Subscription Management Modal */}
      <Modal
        visible={subscriptionModalVisible}
        animationType="slide"
        transparent
        onRequestClose={() => setSubscriptionModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={[styles.modalContent, { backgroundColor: colors.card }]}>
            <View style={[styles.modalHeader, { borderBottomColor: colors.border }]}>
              <Text style={[styles.modalTitle, { color: colors.text }]}>구독 관리</Text>
              <TouchableOpacity onPress={() => setSubscriptionModalVisible(false)}>
                <Text style={[styles.modalClose, { color: colors.textSecondary }]}>✕</Text>
              </TouchableOpacity>
            </View>

            <ScrollView style={styles.modalBody}>
              {/* Current Subscription */}
              <View style={[styles.currentSubscription, { backgroundColor: colors.surface }]}>
                <Text style={[styles.currentTierLabel, { color: colors.textSecondary }]}>현재 구독</Text>
                <Text style={[styles.currentTier, { color: colors.text }]}>
                  {subscription?.tier_display || 'FREE'}
                </Text>
                {subscription?.end_date && (
                  <Text style={[styles.subscriptionDate, { color: colors.textSecondary }]}>
                    {subscription.is_expired ? '만료됨' : `${subscription.days_remaining}일 남음`}
                  </Text>
                )}
              </View>

              {/* Available Tiers */}
              <Text style={[styles.tiersTitle, { color: colors.text }]}>구독 플랜</Text>
              {tiers?.map((tier) => (
                <View
                  key={tier.name}
                  style={[styles.tierCard, { backgroundColor: colors.surface, borderColor: colors.border }]}
                >
                  <View style={styles.tierHeader}>
                    <Text style={[styles.tierName, { color: colors.text }]}>{tier.display_name}</Text>
                    <Text style={[styles.tierPrice, { color: colors.primary }]}>
                      {typeof tier.price === 'number' ? `₩${tier.price.toLocaleString()}/월` : tier.price}
                    </Text>
                  </View>
                  <View style={styles.tierFeatures}>
                    {tier.features.map((feature, index) => (
                      <Text key={index} style={[styles.tierFeature, { color: colors.textSecondary }]}>
                        • {feature}
                      </Text>
                    ))}
                  </View>
                  {tier.coming_soon && (
                    <View style={[styles.comingSoonBadge, { backgroundColor: colors.warning + '20' }]}>
                      <Text style={[styles.comingSoonText, { color: colors.warning }]}>출시 예정</Text>
                    </View>
                  )}
                </View>
              ))}

              <View style={[styles.infoBox, { backgroundColor: colors.primary + '10', borderColor: colors.primary }]}>
                <Text style={[styles.infoText, { color: colors.text }]}>
                  💡 구독 업그레이드는 웹 사이트에서 가능합니다.
                </Text>
              </View>
            </ScrollView>

            <View style={[styles.modalFooter, { borderTopColor: colors.border }]}>
              <TouchableOpacity
                style={[styles.modalButton, styles.fullButton, { backgroundColor: colors.primary }]}
                onPress={() => setSubscriptionModalVisible(false)}
              >
                <Text style={styles.saveButtonText}>닫기</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
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
  // Modal styles
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  modalContent: {
    width: '100%',
    maxWidth: 500,
    borderRadius: 16,
    maxHeight: '80%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
  },
  modalClose: {
    fontSize: 24,
    fontWeight: '300',
  },
  modalBody: {
    padding: 20,
  },
  modalFooter: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    padding: 20,
    borderTopWidth: 1,
    gap: 12,
  },
  inputGroup: {
    marginBottom: 20,
  },
  inputLabel: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 8,
  },
  input: {
    borderWidth: 1,
    borderRadius: 8,
    padding: 14,
    fontSize: 16,
  },
  settingItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 16,
    borderBottomWidth: 1,
  },
  settingLabel: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  settingDescription: {
    fontSize: 13,
    lineHeight: 18,
  },
  modalButton: {
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
    minWidth: 100,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cancelButton: {
    borderWidth: 1,
    borderColor: 'transparent',
  },
  saveButton: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  fullButton: {
    flex: 1,
  },
  cancelButtonText: {
    fontSize: 16,
    fontWeight: '600',
  },
  saveButtonText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  currentSubscription: {
    padding: 20,
    borderRadius: 12,
    alignItems: 'center',
    marginBottom: 24,
  },
  currentTierLabel: {
    fontSize: 13,
    marginBottom: 8,
  },
  currentTier: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  subscriptionDate: {
    fontSize: 13,
  },
  tiersTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  tierCard: {
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    marginBottom: 12,
  },
  tierHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  tierName: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  tierPrice: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  tierFeatures: {
    gap: 6,
  },
  tierFeature: {
    fontSize: 14,
    lineHeight: 20,
  },
  comingSoonBadge: {
    position: 'absolute',
    top: 12,
    right: 12,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
  },
  comingSoonText: {
    fontSize: 11,
    fontWeight: '600',
  },
  infoBox: {
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    marginTop: 12,
  },
  infoText: {
    fontSize: 14,
    lineHeight: 20,
  },
});

export default ProfileScreen;
