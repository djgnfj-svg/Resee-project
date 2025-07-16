import React, { useCallback, useState } from 'react';
import { motion } from 'framer-motion';

interface ImageUploadDropzoneProps {
  onImageUpload: (file: File) => Promise<string>;
  className?: string;
  children?: React.ReactNode;
}

const ImageUploadDropzone: React.FC<ImageUploadDropzoneProps> = ({
  onImageUpload,
  className = '',
  children
}) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);

    const files = Array.from(e.dataTransfer.files);
    const imageFiles = files.filter(file => file.type.startsWith('image/'));

    if (imageFiles.length === 0) {
      alert('이미지 파일만 업로드할 수 있습니다.');
      return;
    }

    for (const file of imageFiles) {
      try {
        setIsUploading(true);
        await onImageUpload(file);
      } catch (error) {
        console.error('Image upload failed:', error);
        alert('이미지 업로드에 실패했습니다.');
      } finally {
        setIsUploading(false);
      }
    }
  }, [onImageUpload]);

  const handleFileSelect = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    const imageFiles = files.filter(file => file.type.startsWith('image/'));

    for (const file of imageFiles) {
      try {
        setIsUploading(true);
        await onImageUpload(file);
      } catch (error) {
        console.error('Image upload failed:', error);
        alert('이미지 업로드에 실패했습니다.');
      } finally {
        setIsUploading(false);
      }
    }

    // Reset input
    e.target.value = '';
  }, [onImageUpload]);

  return (
    <motion.div
      className={`relative ${className}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {/* Drag overlay */}
      {isDragOver && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="absolute inset-0 z-50 bg-indigo-500/20 backdrop-blur-sm border-2 border-dashed border-indigo-400 rounded-xl flex items-center justify-center"
        >
          <div className="text-center p-8">
            <div className="text-4xl mb-4">📁</div>
            <p className="text-lg font-semibold text-indigo-700">
              이미지를 여기에 놓으세요
            </p>
            <p className="text-sm text-indigo-600 mt-2">
              JPG, PNG, GIF 형식을 지원합니다
            </p>
          </div>
        </motion.div>
      )}

      {/* Upload progress overlay */}
      {isUploading && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="absolute inset-0 z-40 bg-white/80 backdrop-blur-sm rounded-xl flex items-center justify-center"
        >
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto mb-4"></div>
            <p className="text-sm font-medium text-gray-700">
              이미지 업로드 중...
            </p>
          </div>
        </motion.div>
      )}

      {/* Children content */}
      {children}

      {/* Hidden file input */}
      <input
        type="file"
        multiple
        accept="image/*"
        onChange={handleFileSelect}
        className="hidden"
        id="image-upload-input"
      />
    </motion.div>
  );
};

export default ImageUploadDropzone;