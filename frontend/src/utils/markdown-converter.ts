// HTML to Markdown conversion utilities
export const convertToMarkdown = (html: string): string => {
  if (!html) return '';
  
  let markdown = html;
  
  // 제목 변환
  markdown = markdown.replace(/<h1[^>]*>(.*?)<\/h1>/g, '# $1');
  markdown = markdown.replace(/<h2[^>]*>(.*?)<\/h2>/g, '## $1');
  markdown = markdown.replace(/<h3[^>]*>(.*?)<\/h3>/g, '### $1');
  
  // 굵게, 기울임
  markdown = markdown.replace(/<strong[^>]*>(.*?)<\/strong>/g, '**$1**');
  markdown = markdown.replace(/<em[^>]*>(.*?)<\/em>/g, '*$1*');
  
  // 목록
  markdown = markdown.replace(/<ul[^>]*>(.*?)<\/ul>/gs, (match, content) => {
    return content.replace(/<li[^>]*>(.*?)<\/li>/g, '- $1');
  });
  markdown = markdown.replace(/<ol[^>]*>(.*?)<\/ol>/gs, (match, content) => {
    let counter = 1;
    return content.replace(/<li[^>]*>(.*?)<\/li>/g, () => `${counter++}. $1`);
  });
  
  // 인용문
  markdown = markdown.replace(/<blockquote[^>]*>(.*?)<\/blockquote>/gs, '> $1');
  
  // 코드
  markdown = markdown.replace(/<code[^>]*>(.*?)<\/code>/g, '`$1`');
  markdown = markdown.replace(/<pre[^>]*><code[^>]*>(.*?)<\/code><\/pre>/gs, '```\n$1\n```');
  
  // 링크
  markdown = markdown.replace(/<a[^>]*href="([^"]*)"[^>]*>(.*?)<\/a>/g, '[$2]($1)');
  
  // 줄바꿈
  markdown = markdown.replace(/<br\s*\/?>/g, '\n');
  markdown = markdown.replace(/<\/p>\s*<p[^>]*>/g, '\n\n');
  markdown = markdown.replace(/<p[^>]*>/g, '');
  markdown = markdown.replace(/<\/p>/g, '');
  
  // HTML 태그 제거
  markdown = markdown.replace(/<[^>]*>/g, '');
  
  // HTML 엔티티 디코딩
  markdown = markdown.replace(/&amp;/g, '&');
  markdown = markdown.replace(/&lt;/g, '<');
  markdown = markdown.replace(/&gt;/g, '>');
  markdown = markdown.replace(/&quot;/g, '"');
  markdown = markdown.replace(/&#39;/g, "'");
  
  return markdown.trim();
};

// Markdown to HTML conversion utilities
export const convertFromMarkdown = (markdown: string): string => {
  if (!markdown) return '';
  
  let html = markdown;
  
  // 제목 변환
  html = html.replace(/^### (.*$)/gm, '<h3>$1</h3>');
  html = html.replace(/^## (.*$)/gm, '<h2>$1</h2>');
  html = html.replace(/^# (.*$)/gm, '<h1>$1</h1>');
  
  // 굵게, 기울임
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
  
  // 코드
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
  html = html.replace(/```\n([\s\S]*?)\n```/g, '<pre><code>$1</code></pre>');
  
  // 링크
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>');
  
  // 목록 처리 (개선)
  // 불릿 목록
  html = html.replace(/^- (.*$)/gm, '<li>$1</li>');
  html = html.replace(/(<li>.*<\/li>(\n|$))+/g, (match) => {
    return '<ul>' + match.replace(/\n/g, '') + '</ul>';
  });
  
  // 번호 목록
  html = html.replace(/^(\d+)\. (.*$)/gm, '<li>$2</li>');
  html = html.replace(/(<li>.*<\/li>(\n|$))+/g, (match) => {
    // 이미 <ul>로 감싸져 있지 않은 경우에만 <ol>로 감싸기
    if (!match.includes('<ul>')) {
      return '<ol>' + match.replace(/\n/g, '') + '</ol>';
    }
    return match;
  });
  
  // 인용문
  html = html.replace(/^> (.*$)/gm, '<blockquote>$1</blockquote>');
  
  // 줄바꿈
  html = html.replace(/\n/g, '<br>');
  
  return html;
};