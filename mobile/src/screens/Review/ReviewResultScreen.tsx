import React from 'react';
import {View, StyleSheet} from 'react-native';
import {Text, Card} from 'react-native-paper';

const ReviewResultScreen: React.FC = () => (
  <View style={styles.container}>
    <Card>
      <Card.Content>
        <Text variant="headlineMedium">복습 결과</Text>
        <Text style={styles.note}>복습 결과 화면은 구현 예정입니다.</Text>
      </Card.Content>
    </Card>
  </View>
);

const styles = StyleSheet.create({
  container: {flex: 1, backgroundColor: '#F9FAFB', padding: 16},
  note: {marginTop: 16, color: '#6B7280'},
});

export default ReviewResultScreen;
