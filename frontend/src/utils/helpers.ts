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
 * Format date to Korean locale string
 */
export function formatDate(date: string | Date): string {
  return new Date(date).toLocaleDateString('ko-KR');
}

/**
 * Format date and time to Korean locale string
 */
export function formatDateTime(date: string | Date): string {
  return new Date(date).toLocaleString('ko-KR');
}

/**
 * Get priority label and color
 */
export function getPriorityInfo(priority: 'low' | 'medium' | 'high') {
  const priorityMap = {
    high: { label: '높음', color: 'red', emoji: '🔴', className: 'bg-red-100 text-red-700' },
    medium: { label: '보통', color: 'yellow', emoji: '🟡', className: 'bg-yellow-100 text-yellow-700' },
    low: { label: '낮음', color: 'green', emoji: '🟢', className: 'bg-green-100 text-green-700' }
  };
  return priorityMap[priority];
}

/**
 * Truncate text with ellipsis
 */
export function truncateText(text: string, maxLength: number): string {
  return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
}