import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { contentAPI } from '../utils/api';
import { CreateContentData } from '../types';
import CreateContentForm from '../components/CreateContentForm';

const EditContentPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { id } = useParams<{ id: string }>();

  // Fetch existing content
  const { data: content, isLoading, error } = useQuery({
    queryKey: ['content', id],
    queryFn: () => contentAPI.getContent(Number(id)),
    enabled: !!id,
  });

  // Update content mutation
  const updateContentMutation = useMutation({
    mutationFn: ({ contentId, data }: { contentId: number; data: CreateContentData }) =>
      contentAPI.updateContent(contentId, data),
    onSuccess: async () => {
      alert('Success: 콘텐츠가 성공적으로 수정되었습니다!');
      await queryClient.invalidateQueries({ queryKey: ['contents'] });
      await queryClient.invalidateQueries({ queryKey: ['content', id] });
      await queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      navigate('/content');
    },
    onError: (error: any) => {
      console.error('콘텐츠 수정 실패:', error);
      alert('Error: 콘텐츠 수정에 실패했습니다.');
    },
  });

  const handleSubmit = (data: CreateContentData) => {
    if (id) {
      updateContentMutation.mutate({ contentId: Number(id), data });
    }
  };

  const handleCancel = () => {
    navigate('/content');
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">콘텐츠를 불러오는 중...</p>
        </div>
      </div>
    );
  }

  if (error || !content) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-4">
            콘텐츠를 찾을 수 없습니다
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            요청하신 콘텐츠가 존재하지 않거나 삭제되었습니다.
          </p>
          <button
            onClick={() => navigate('/content')}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            콘텐츠 목록으로 돌아가기
          </button>
        </div>
      </div>
    );
  }

  return (
    <CreateContentForm
      onSubmit={handleSubmit}
      onCancel={handleCancel}
      isLoading={updateContentMutation.isPending}
      initialData={{
        title: content.title,
        content: content.content,
        category: content.category?.id || undefined,
      }}
    />
  );
};

export default EditContentPage;