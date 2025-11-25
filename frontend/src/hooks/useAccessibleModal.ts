import { useEffect, useCallback, useRef } from 'react';

interface UseAccessibleModalOptions {
  isOpen: boolean;
  onClose: () => void;
  closeOnBackdropClick?: boolean;
  closeOnEscape?: boolean;
}

/**
 * 접근성이 보장된 모달을 위한 커스텀 훅
 * - ESC 키로 닫기
 * - 포커스 트랩
 * - 백드롭 클릭으로 닫기
 */
export const useAccessibleModal = ({
  isOpen,
  onClose,
  closeOnBackdropClick = true,
  closeOnEscape = true,
}: UseAccessibleModalOptions) => {
  const modalRef = useRef<HTMLDivElement>(null);
  const previousActiveElement = useRef<HTMLElement | null>(null);

  // ESC 키로 닫기
  useEffect(() => {
    if (!isOpen || !closeOnEscape) return;

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose, closeOnEscape]);

  // 포커스 트랩
  useEffect(() => {
    if (!isOpen) return;

    // 모달이 열릴 때 이전 포커스 저장
    previousActiveElement.current = document.activeElement as HTMLElement;

    // 모달이 열리면 첫 번째 포커스 가능한 요소로 포커스 이동
    const modalElement = modalRef.current;
    if (modalElement) {
      const focusableElements = modalElement.querySelectorAll<HTMLElement>(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );

      if (focusableElements.length > 0) {
        // 첫 번째 요소로 포커스 (닫기 버튼이 아닌 경우 두 번째 요소)
        const firstElement = focusableElements[0];
        const secondElement = focusableElements[1];

        // 첫 번째 요소가 닫기 버튼이면 두 번째 요소로
        setTimeout(() => {
          if (firstElement.getAttribute('aria-label')?.includes('닫기')) {
            secondElement?.focus();
          } else {
            firstElement?.focus();
          }
        }, 100);
      }

      // 포커스 트랩 구현
      const handleTab = (event: KeyboardEvent) => {
        if (event.key !== 'Tab') return;

        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        if (event.shiftKey) {
          // Shift + Tab
          if (document.activeElement === firstElement) {
            event.preventDefault();
            lastElement?.focus();
          }
        } else {
          // Tab
          if (document.activeElement === lastElement) {
            event.preventDefault();
            firstElement?.focus();
          }
        }
      };

      modalElement.addEventListener('keydown', handleTab as EventListener);
      return () => {
        modalElement.removeEventListener('keydown', handleTab as EventListener);
      };
    }
  }, [isOpen]);

  // 모달이 닫힐 때 이전 포커스로 복귀
  useEffect(() => {
    if (!isOpen && previousActiveElement.current) {
      previousActiveElement.current.focus();
      previousActiveElement.current = null;
    }
  }, [isOpen]);

  // 백드롭 클릭 핸들러
  const handleBackdropClick = useCallback(
    (event: React.MouseEvent<HTMLDivElement>) => {
      if (closeOnBackdropClick && event.target === event.currentTarget) {
        onClose();
      }
    },
    [closeOnBackdropClick, onClose]
  );

  // body 스크롤 방지
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }

    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  return {
    modalRef,
    handleBackdropClick,
  };
};
