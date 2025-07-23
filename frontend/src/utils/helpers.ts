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
 * Format date to localized string
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