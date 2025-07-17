import React from 'react';

interface NotionEditorProps {
  content: string;
  onChange: (content: string) => void;
  placeholder?: string;
  onImageUpload?: (file: File) => Promise<string>;
  className?: string;
}

const NotionEditor: React.FC<NotionEditorProps> = ({
  content,
  onChange,
  placeholder = '여기에 내용을 입력하세요...',
  className = ''
}) => {
  return (
    <div className={className}>
      <textarea
        value={content}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full min-h-[400px] p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
        style={{ fontFamily: 'inherit' }}
      />
    </div>
  );
};

export default NotionEditor;