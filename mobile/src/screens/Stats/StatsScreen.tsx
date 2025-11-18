import React from 'react';
import {View, StyleSheet, ScrollView} from 'react-native';
import {Card, Text} from 'react-native-paper';

const StatsScreen: React.FC = () => (
  <ScrollView style={styles.container}>
    <Card style={styles.card}>
      <Card.Content>
        <Text variant="headlineMedium">학습 통계</Text>
        <Text style={styles.note}>통계 화면은 구현 예정입니다.</Text>
      </Card.Content>
    </Card>
  </ScrollView>
);

const styles = StyleSheet.create({
  container: {flex: 1, backgroundColor: '#F9FAFB'},
  card: {margin: 16},
  note: {marginTop: 16, color: '#6B7280'},
});

export default StatsScreen;
