import { PaginatedResponse } from '../types';

/**
 * Extract results from a paginated response or return the array directly
 * This helper handles the case where the API might return either a paginated response
 * or a direct array of results
 */
export function extractResults<T>(data: PaginatedResponse<T> | T[]): T[] {
  return Array.isArray(data) ? data : data.results;
}

/**
 * Format date to absolute format (YYYY. MM. DD)
 */
export function formatAbsoluteDate(date: string | Date): string {
  const d = new Date(date);
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}.${month}.${day}`;
}

/**
 * Format date to localized string (deprecated: use formatAbsoluteDate or formatRelativeDate)
 * @deprecated
 */
export function formatDate(date: string | Date): string {
  return new Date(date).toLocaleDateString('ko-KR');
}

/**
 * Format date and time to localized string
 */
export function formatDateTime(date: string | Date): string {
  return new Date(date).toLocaleString('ko-KR');
}

/**
 * Format date to relative format (오늘, 어제, D-X, X일 전 등)
 * @param dateString - ISO date string
 * @param isFutureDate - true면 미래 기준 (D-X), false면 과거 기준 (X일 전)
 */
export function formatRelativeDate(dateString: string, isFutureDate: boolean = false): string {
  const date = new Date(dateString);
  const now = new Date();

  // 시간을 무시하고 날짜만 비교 (자정 기준)
  const dateOnly = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  const nowOnly = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const diffDays = Math.round((dateOnly.getTime() - nowOnly.getTime()) / (1000 * 60 * 60 * 24));

  // 미래 날짜인 경우 (다음 복습 날짜)
  if (isFutureDate) {
    if (diffDays === 0) return '오늘';
    if (diffDays === 1) return '내일';
    if (diffDays > 0) return `D-${diffDays}`;
    // 과거 날짜인 경우 (복습 기한 지남)
    if (diffDays === -1) return '어제';
    if (diffDays < 0) return `D+${Math.abs(diffDays)}`;
  }

  // 과거 날짜인 경우 (생성 날짜)
  const pastDiffDays = Math.round((nowOnly.getTime() - dateOnly.getTime()) / (1000 * 60 * 60 * 24));
  if (pastDiffDays === 0) return '오늘';
  if (pastDiffDays === 1) return '어제';
  if (pastDiffDays < 7) return `${pastDiffDays}일 전`;
  return date.toLocaleDateString('ko-KR', { year: 'numeric', month: 'short', day: 'numeric' });
}

/**
 * Get priority label and color
 */
export function getPriorityInfo(priority: 'low' | 'medium' | 'high') {
  const priorityMap = {
    high: { label: 'High', color: 'red', emoji: '🔴', className: 'bg-red-100 text-red-700' },
    medium: { label: 'Medium', color: 'yellow', emoji: '🟡', className: 'bg-yellow-100 text-yellow-700' },
    low: { label: 'Low', color: 'green', emoji: '🟢', className: 'bg-green-100 text-green-700' }
  };
  return priorityMap[priority];
}

/**
 * Truncate text with ellipsis
 */
export function truncateText(text: string, maxLength: number): string {
  return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
}

/**
 * Sanitize a number value to prevent NaN and null/undefined issues in charts
 * Returns 0 for invalid numbers
 */
export function sanitizeNumber(value: number | null | undefined): number {
  if (value === null || value === undefined || isNaN(value) || !isFinite(value)) {
    return 0;
  }
  return value;
}