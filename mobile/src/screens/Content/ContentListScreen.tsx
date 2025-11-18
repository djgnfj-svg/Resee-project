/**
 * Content List Screen
 */

import React from 'react';
import {View, StyleSheet, FlatList} from 'react-native';
import {Card, Text, FAB} from 'react-native-paper';
import {useQuery} from '@tanstack/react-query';
import {useNavigation} from '@react-navigation/native';
import type {StackNavigationProp} from '@react-navigation/stack';
import {getContents} from '@api/content';
import type {ContentStackParamList} from '@types/index';

type ContentListNavigationProp = StackNavigationProp<
  ContentStackParamList,
  'ContentList'
>;

const ContentListScreen: React.FC = () => {
  const navigation = useNavigation<ContentListNavigationProp>();

  const {data, isLoading} = useQuery({
    queryKey: ['contents'],
    queryFn: () => getContents(),
  });

  return (
    <View style={styles.container}>
      <FlatList
        data={data?.results || []}
        keyExtractor={item => item.id.toString()}
        renderItem={({item}) => (
          <Card
            style={styles.card}
            onPress={() =>
              navigation.navigate('ContentDetail', {contentId: item.id})
            }>
            <Card.Content>
              <Text variant="titleMedium">{item.title}</Text>
              <Text variant="bodySmall" style={styles.category}>
                {item.category?.name || '미분류'}
              </Text>
              <Text variant="bodySmall" style={styles.date}>
                복습 횟수: {item.review_count}
              </Text>
            </Card.Content>
          </Card>
        )}
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Text>콘텐츠가 없습니다. 새로 작성해보세요!</Text>
          </View>
        }
      />
      <FAB
        icon="plus"
        style={styles.fab}
        onPress={() => navigation.navigate('ContentCreate')}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  card: {
    margin: 8,
    marginHorizontal: 16,
  },
  category: {
    marginTop: 4,
    color: '#6B7280',
  },
  date: {
    marginTop: 2,
    color: '#9CA3AF',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  fab: {
    position: 'absolute',
    right: 16,
    bottom: 16,
    backgroundColor: '#3B82F6',
  },
});

export default ContentListScreen;
