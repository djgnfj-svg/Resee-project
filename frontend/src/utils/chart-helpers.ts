// NaN 값을 안전하게 처리하는 헬퍼 함수 (강화된 버전)
export const sanitizeNumber = (value: any, defaultValue: number = 0): number => {
  // null, undefined, empty string 처리
  if (value === null || value === undefined || value === '') {
    return defaultValue;
  }
  
  // 문자열을 숫자로 변환 시도
  const num = typeof value === 'string' ? parseFloat(value) : Number(value);
  
  // NaN, Infinity, -Infinity 처리
  if (isNaN(num) || !isFinite(num)) {
    return defaultValue;
  }
  
  return num;
};

// 데이터 배열의 모든 수치 값을 안전하게 처리
export const sanitizeChartData = <T extends Record<string, any>>(data: T[]): T[] => {
  if (!Array.isArray(data)) return [];
  
  return data.map(item => {
    if (!item || typeof item !== 'object') return {} as T;
    
    const sanitizedItem = { ...item } as T;
    Object.keys(sanitizedItem).forEach((key: keyof T) => {
      const value = sanitizedItem[key];
      if (typeof value === 'number' || value === null || value === undefined) {
        (sanitizedItem[key] as any) = sanitizeNumber(value, 0);
      }
    });
    return sanitizedItem;
  });
};

// 차트 색상 팔레트
export const chartColors = {
  primary: '#3B82F6', // blue-500
  secondary: '#8B5CF6', // purple-500
  success: '#10B981', // emerald-500
  warning: '#F59E0B', // amber-500
  danger: '#EF4444', // red-500
  info: '#06B6D4', // cyan-500
  gray: '#6B7280', // gray-500
} as const;

// 카테고리별 기본 색상 생성
export const generateCategoryColors = (count: number): string[] => {
  const baseColors = [
    '#3B82F6', '#8B5CF6', '#10B981', '#F59E0B', 
    '#EF4444', '#06B6D4', '#F97316', '#84CC16',
    '#EC4899', '#6366F1', '#14B8A6', '#F43F5E'
  ];
  
  const colors = [];
  for (let i = 0; i < count; i++) {
    colors.push(baseColors[i % baseColors.length]);
  }
  return colors;
};

// 트렌드 아이콘 반환
export const getTrendIcon = (current: number, previous: number) => {
  if (current > previous) return 'up';
  if (current < previous) return 'down';
  return 'stable';
};

// 퍼센티지 포맷터
export const formatPercentage = (value: number): string => {
  return `${sanitizeNumber(value, 0).toFixed(1)}%`;
};

// 숫자 포맷터 (한국어)
export const formatNumber = (value: number): string => {
  const num = sanitizeNumber(value, 0);
  if (num >= 1000000) {
    return `${(num / 1000000).toFixed(1)}M`;
  }
  if (num >= 1000) {
    return `${(num / 1000).toFixed(1)}K`;
  }
  return num.toString();
};