import { AxiosError } from 'axios';

interface ApiErrorResponse {
  detail?: string;
  non_field_errors?: string[];
  [key: string]: any;
}

/**
 * API 에러 응답을 파싱하여 사용자 친화적인 메시지를 반환합니다.
 * @param error - Axios 에러 객체
 * @param defaultMessage - 기본 에러 메시지
 * @returns 파싱된 에러 메시지
 */
export const parseApiError = (error: unknown, defaultMessage: string = '오류가 발생했습니다.'): string => {
  if (!(error instanceof AxiosError)) {
    return defaultMessage;
  }

  const data = error.response?.data as ApiErrorResponse | undefined;

  if (!data) {
    return defaultMessage;
  }

  // non_field_errors 배열
  if (data.non_field_errors && Array.isArray(data.non_field_errors)) {
    return data.non_field_errors[0];
  }

  // detail 문자열
  if (data.detail) {
    return data.detail;
  }

  // 특정 필드 에러 (배열인 경우)
  for (const key in data) {
    if (Array.isArray(data[key]) && data[key].length > 0) {
      return data[key][0];
    }
  }

  // 문자열로 온 경우
  if (typeof data === 'string') {
    return data;
  }

  return defaultMessage;
};
