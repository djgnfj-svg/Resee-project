import React from 'react';

const EditorHelp: React.FC = () => (
  <div className="px-4 py-3 bg-gray-50 dark:bg-gray-800 border-t border-gray-200 dark:border-gray-600">
    <details className="text-sm">
      <summary className="cursor-pointer text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200">
        마크다운 단축키
      </summary>
      <div className="mt-2 space-y-1 text-gray-700 dark:text-gray-300">
        <p><strong># 제목1</strong> | <strong>## 제목2</strong> | <strong>### 제목3</strong></p>
        <p><strong>**굵게**</strong> | <strong>*기울임*</strong> | <strong>~~취소선~~</strong></p>
        <p><strong>- 목록</strong> | <strong>1. 번호목록</strong> | <strong>{'>'} 인용문</strong></p>
        <p><strong>`코드`</strong> | <strong>```코드블록```</strong></p>
      </div>
    </details>
  </div>
);

export default EditorHelp;