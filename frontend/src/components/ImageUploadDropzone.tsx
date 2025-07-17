import React, { useCallback } from 'react';

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
  const handleFileChange = useCallback(async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      await onImageUpload(file);
    }
  }, [onImageUpload]);

  return (
    <div className={`border-2 border-dashed border-gray-300 rounded-lg p-6 text-center ${className}`}>
      <input
        type="file"
        accept="image/*"
        onChange={handleFileChange}
        className="hidden"
        id="image-upload"
      />
      <label htmlFor="image-upload" className="cursor-pointer">
        {children || (
          <div className="text-gray-600">
            <div className="mb-2">📷</div>
            <div>이미지를 선택하세요</div>
          </div>
        )}
      </label>
    </div>
  );
};

export default ImageUploadDropzone;