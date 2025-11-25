import React from 'react';

interface FormHeaderProps {
  isEdit: boolean;
}

const FormHeader: React.FC<FormHeaderProps> = ({ isEdit }) => {
  return (
    <div className="bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 p-2">
    </div>
  );
};

export default FormHeader;