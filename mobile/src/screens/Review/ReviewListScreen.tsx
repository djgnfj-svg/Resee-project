import React from 'react';
import {View, StyleSheet, FlatList} from 'react-native';
import {Card, Text, Button} from 'react-native-paper';
import {useQuery} from '@tanstack/react-query';
import {getTodayReviews} from '@api/review';

const ReviewListScreen: React.FC = () => {
  const {data, isLoading} = useQuery({
    queryKey: ['todayReviews'],
    queryFn: getTodayReviews,
  });

  return (
    <View style={styles.container}>
      <FlatList
        data={data?.results || []}
        keyExtractor={item => item.id.toString()}
        renderItem={({item}) => (
          <Card style={styles.card}>
            <Card.Content>
              <Text variant="titleMedium">{item.content.title}</Text>
              <Text variant="bodySmall">
                다음 복습: {new Date(item.next_review_date).toLocaleDateString()}
              </Text>
            </Card.Content>
          </Card>
        )}
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Text>오늘 복습할 콘텐츠가 없습니다 🎉</Text>
          </View>
        }
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {flex: 1, backgroundColor: '#F9FAFB'},
  card: {margin: 8, marginHorizontal: 16},
  emptyContainer: {flex: 1, justifyContent: 'center', alignItems: 'center', padding: 32},
});

export default ReviewListScreen;
