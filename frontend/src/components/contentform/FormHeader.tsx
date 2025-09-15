import React from 'react';

interface FormHeaderProps {
  isEdit: boolean;
}

const FormHeader: React.FC<FormHeaderProps> = ({ isEdit }) => {
  return (
    <div className="bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 p-4 sm:p-6 lg:p-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white">
            {isEdit ? '콘텐츠 수정' : '새 콘텐츠 만들기'}
          </h1>
          <p className="text-sm sm:text-base text-indigo-100 dark:text-indigo-200 mt-2">
            정보를 입력하여 학습 콘텐츠를 만들어보세요
          </p>
        </div>
      </div>
    </div>
  );
};

export default FormHeader;