import React from 'react';
import {View, StyleSheet, ScrollView} from 'react-native';
import {Card, Text, Button, Divider} from 'react-native-paper';
import {useAuth} from '@contexts/AuthContext';

const ProfileScreen: React.FC = () => {
  const {user, logout} = useAuth();

  return (
    <ScrollView style={styles.container}>
      <Card style={styles.card}>
        <Card.Content>
          <Text variant="headlineSmall">프로필</Text>
          <Text style={styles.email}>{user?.email}</Text>
          <Text style={styles.tier}>
            등급: {user?.subscription?.tier_display || 'FREE'}
          </Text>
        </Card.Content>
      </Card>

      <Card style={styles.card}>
        <Card.Content>
          <Text variant="titleMedium">설정</Text>
          <Divider style={styles.divider} />
          <Button mode="outlined" style={styles.button}>
            알림 설정
          </Button>
          <Button mode="outlined" style={styles.button}>
            구독 관리
          </Button>
          <Button mode="outlined" style={styles.button}>
            계정 설정
          </Button>
        </Card.Content>
      </Card>

      <Card style={styles.card}>
        <Card.Content>
          <Button mode="contained" onPress={logout} buttonColor="#EF4444">
            로그아웃
          </Button>
        </Card.Content>
      </Card>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {flex: 1, backgroundColor: '#F9FAFB'},
  card: {margin: 16},
  email: {marginTop: 8, color: '#6B7280'},
  tier: {marginTop: 4, color: '#3B82F6', fontWeight: '600'},
  divider: {marginVertical: 12},
  button: {marginTop: 8},
});

export default ProfileScreen;
