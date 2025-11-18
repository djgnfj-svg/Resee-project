import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ContentStackScreenProps } from '../../navigation/types';
import { contentAPI } from '../../api';
import { ReviewMode } from '../../types';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorMessage from '../../components/common/ErrorMessage';
import { useTheme } from '../../contexts/ThemeContext';

type Props = ContentStackScreenProps<'ContentEdit'>;

const ContentEditScreen: React.FC<Props> = ({ route, navigation }) => {
  const { id } = route.params;
  const queryClient = useQueryClient();
  const { colors } = useTheme();

  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<number | undefined>();
  const [reviewMode, setReviewMode] = useState<ReviewMode>('objective');

  const {
    data: contentData,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['content', id],
    queryFn: () => contentAPI.getContent(id),
  });

  const { data: categoriesData } = useQuery({
    queryKey: ['categories'],
    queryFn: () => contentAPI.getCategories(),
  });

  useEffect(() => {
    if (contentData) {
      setTitle(contentData.title);
      setContent(contentData.content);
      setSelectedCategory(contentData.category?.id);
      setReviewMode(contentData.review_mode);
    }
  }, [contentData]);

  const updateMutation = useMutation({
    mutationFn: (data: {
      title?: string;
      content?: string;
      category?: number;
      review_mode?: string;
    }) => contentAPI.updateContent(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contents'] });
      queryClient.invalidateQueries({ queryKey: ['content', id] });
      navigation.goBack();
      // Show success message briefly after navigation
      setTimeout(() => {
        Alert.alert('성공', '콘텐츠가 수정되었습니다.');
      }, 100);
    },
    onError: (error: any) => {
      Alert.alert('오류', error.userMessage || '콘텐츠 수정에 실패했습니다.');
    },
  });

  const handleSubmit = () => {
    if (!title.trim()) {
      Alert.alert('오류', '제목을 입력해주세요.');
      return;
    }

    if (!content.trim()) {
      Alert.alert('오류', '내용을 입력해주세요.');
      return;
    }

    updateMutation.mutate({
      title: title.trim(),
      content: content.trim(),
      category: selectedCategory,
      review_mode: reviewMode,
    });
  };

  if (isLoading) {
    return <LoadingSpinner message="콘텐츠 불러오는 중..." />;
  }

  if (error || !contentData) {
    return (
      <ErrorMessage
        message="콘텐츠를 불러올 수 없습니다."
        onRetry={() => navigation.goBack()}
      />
    );
  }

  const categories = categoriesData?.results || [];

  const reviewModes: { value: ReviewMode; label: string }[] = [
    { value: 'objective', label: '기억 확인' },
    { value: 'descriptive', label: '서술형' },
    { value: 'multiple_choice', label: '객관식' },
  ];

  return (
    <KeyboardAvoidingView
      style={[styles.container, { backgroundColor: colors.background }]}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={100}
    >
      <ScrollView style={styles.scrollView} keyboardShouldPersistTaps="handled">
        <View style={styles.form}>
          {/* Title Input */}
          <View style={styles.formGroup}>
            <Text style={[styles.label, { color: colors.text }]}>제목 *</Text>
            <TextInput
              style={[styles.input, { borderColor: colors.border, color: colors.text, backgroundColor: colors.card }]}
              value={title}
              onChangeText={setTitle}
              placeholder="학습 콘텐츠의 제목을 입력하세요"
              placeholderTextColor={colors.textSecondary}
            />
          </View>

          {/* Content Input */}
          <View style={styles.formGroup}>
            <Text style={[styles.label, { color: colors.text }]}>내용 *</Text>
            <TextInput
              style={[styles.input, styles.textArea, { borderColor: colors.border, color: colors.text, backgroundColor: colors.card }]}
              value={content}
              onChangeText={setContent}
              placeholder="학습할 내용을 입력하세요"
              placeholderTextColor={colors.textSecondary}
              multiline
              numberOfLines={10}
              textAlignVertical="top"
            />
          </View>

          {/* Category Selection */}
          <View style={styles.formGroup}>
            <Text style={[styles.label, { color: colors.text }]}>카테고리</Text>
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              style={styles.categoryScroll}
            >
              <TouchableOpacity
                style={[
                  styles.categoryChip,
                  { borderColor: colors.border, backgroundColor: colors.card },
                  !selectedCategory && { backgroundColor: colors.primary, borderColor: colors.primary },
                ]}
                onPress={() => setSelectedCategory(undefined)}
              >
                <Text
                  style={[
                    styles.categoryChipText,
                    { color: colors.textSecondary },
                    !selectedCategory && styles.categoryChipTextActive,
                  ]}
                >
                  없음
                </Text>
              </TouchableOpacity>

              {categories.map((cat) => (
                <TouchableOpacity
                  key={cat.id}
                  style={[
                    styles.categoryChip,
                    { borderColor: colors.border, backgroundColor: colors.card },
                    selectedCategory === cat.id && { backgroundColor: colors.primary, borderColor: colors.primary },
                  ]}
                  onPress={() => setSelectedCategory(cat.id)}
                >
                  <Text
                    style={[
                      styles.categoryChipText,
                      { color: colors.textSecondary },
                      selectedCategory === cat.id &&
                        styles.categoryChipTextActive,
                    ]}
                  >
                    {cat.name}
                  </Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>

          {/* Review Mode Selection */}
          <View style={styles.formGroup}>
            <Text style={[styles.label, { color: colors.text }]}>복습 모드</Text>
            <View style={styles.reviewModeContainer}>
              {reviewModes.map((mode) => (
                <TouchableOpacity
                  key={mode.value}
                  style={[
                    styles.reviewModeButton,
                    { borderColor: colors.border, backgroundColor: colors.card },
                    reviewMode === mode.value && { backgroundColor: colors.primary, borderColor: colors.primary },
                  ]}
                  onPress={() => setReviewMode(mode.value)}
                >
                  <Text
                    style={[
                      styles.reviewModeText,
                      { color: colors.textSecondary },
                      reviewMode === mode.value && styles.reviewModeTextActive,
                    ]}
                  >
                    {mode.label}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {/* Submit Button */}
          <TouchableOpacity
            style={[
              styles.submitButton,
              { backgroundColor: colors.primary },
              updateMutation.isPending && styles.submitButtonDisabled,
            ]}
            onPress={handleSubmit}
            disabled={updateMutation.isPending}
          >
            <Text style={styles.submitButtonText}>
              {updateMutation.isPending ? '수정 중...' : '콘텐츠 수정'}
            </Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollView: {
    flex: 1,
  },
  form: {
    padding: 20,
  },
  formGroup: {
    marginBottom: 24,
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 8,
  },
  input: {
    borderWidth: 1,
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
  },
  textArea: {
    height: 150,
    paddingTop: 12,
  },
  categoryScroll: {
    flexDirection: 'row',
  },
  categoryChip: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
    marginRight: 8,
  },
  categoryChipText: {
    fontSize: 14,
  },
  categoryChipTextActive: {
    color: '#fff',
    fontWeight: '600',
  },
  reviewModeContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  reviewModeButton: {
    flex: 1,
    minWidth: '45%',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    borderWidth: 1,
    alignItems: 'center',
  },
  reviewModeText: {
    fontSize: 14,
  },
  reviewModeTextActive: {
    color: '#fff',
    fontWeight: '600',
  },
  submitButton: {
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 8,
  },
  submitButtonDisabled: {
    opacity: 0.6,
  },
  submitButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});

export default ContentEditScreen;
