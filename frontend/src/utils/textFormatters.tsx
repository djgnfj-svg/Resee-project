import React from 'react';

export const renderTextWithCode = (text: string): React.ReactNode => {
  const parts: React.ReactNode[] = [];
  let lastIndex = 0;
  const regex = /`([^`]+)`/g;
  let match;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.substring(lastIndex, match.index));
    }

    parts.push(
      <code
        key={match.index}
        className="px-1.5 py-0.5 bg-gray-200 dark:bg-gray-600 text-indigo-600 dark:text-indigo-300 rounded text-sm font-mono"
      >
        {match[1]}
      </code>
    );

    lastIndex = match.index + match[0].length;
  }

  if (lastIndex < text.length) {
    parts.push(text.substring(lastIndex));
  }

  return parts.length > 0 ? parts : text;
};
