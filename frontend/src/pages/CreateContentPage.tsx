import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { contentAPI } from '../utils/api';
import { CreateContentData } from '../types';
import CreateContentForm from '../components/CreateContentForm';

const CreateContentPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // Create content mutation
  const createContentMutation = useMutation({
    mutationFn: contentAPI.createContent,
    onSuccess: () => {
      alert('Success: 콘텐츠가 성공적으로 생성되었습니다!');
      queryClient.invalidateQueries({ queryKey: ['contents'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      navigate('/content');
    },
    onError: (error: any) => {
      console.error('콘텐츠 생성 실패:', error);
      alert('Error: 콘텐츠 생성에 실패했습니다.');
    },
  });

  const handleSubmit = (data: CreateContentData) => {
    createContentMutation.mutate(data);
  };

  const handleCancel = () => {
    navigate('/content');
  };

  return (
    <CreateContentForm
      onSubmit={handleSubmit}
      onCancel={handleCancel}
      isLoading={createContentMutation.isPending}
    />
  );
};

export default CreateContentPage;