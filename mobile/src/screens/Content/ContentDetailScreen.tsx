import React from 'react';
import {View, StyleSheet, ScrollView} from 'react-native';
import {Text, Card, Button} from 'react-native-paper';
import {useRoute} from '@react-navigation/native';

const ContentDetailScreen: React.FC = () => {
  const route = useRoute();
  const {contentId} = route.params as {contentId: number};

  return (
    <ScrollView style={styles.container}>
      <Card>
        <Card.Content>
          <Text variant="headlineMedium">콘텐츠 상세</Text>
          <Text>ID: {contentId}</Text>
          <Text style={styles.note}>콘텐츠 상세 화면은 구현 예정입니다.</Text>
        </Card.Content>
      </Card>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {flex: 1, backgroundColor: '#F9FAFB', padding: 16},
  note: {marginTop: 16, color: '#6B7280'},
});

export default ContentDetailScreen;
