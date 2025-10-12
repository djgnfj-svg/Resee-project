import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { contentAPI } from '../utils/api';
import { CreateContentData, ContentUsage } from '../types';
import CreateContentForm from '../components/CreateContentForm';

const CreateContentPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [contentUsage, setContentUsage] = useState<ContentUsage | null>(null);

  // Check content usage and redirect if at limit
  useQuery({
    queryKey: ['contents-usage-check'],
    queryFn: async () => {
      const response = await contentAPI.getContents();
      if (response.usage) {
        setContentUsage(response.usage);
        // If user cannot create content, redirect to content list
        if (!response.usage.can_create) {
          navigate('/content', { replace: true });
          return null;
        }
      }
      return response;
    },
  });

  // Create content mutation
  const createContentMutation = useMutation({
    mutationFn: contentAPI.createContent,
    onSuccess: async () => {
      alert('Success: 콘텐츠가 성공적으로 생성되었습니다!');
      await queryClient.invalidateQueries({ queryKey: ['contents'] });
      await queryClient.invalidateQueries({ queryKey: ['dashboard'] });
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

  // Don't render form if user can't create content
  if (contentUsage && !contentUsage.can_create) {
    return null; // Will redirect via useQuery above
  }

  return (
    <CreateContentForm
      onSubmit={handleSubmit}
      onCancel={handleCancel}
      isLoading={createContentMutation.isPending}
    />
  );
};

export default CreateContentPage;