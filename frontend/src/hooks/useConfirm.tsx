import { useState, useCallback } from 'react';
import ConfirmDialog from '../components/common/ConfirmDialog';

interface ConfirmOptions {
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  variant?: 'danger' | 'warning' | 'info';
}

interface ConfirmState extends ConfirmOptions {
  isOpen: boolean;
  onConfirm: () => void;
}

export const useConfirm = () => {
  const [confirmState, setConfirmState] = useState<ConfirmState>({
    isOpen: false,
    title: '',
    message: '',
    onConfirm: () => {},
  });

  const confirm = useCallback((options: ConfirmOptions): Promise<boolean> => {
    return new Promise((resolve) => {
      setConfirmState({
        ...options,
        isOpen: true,
        onConfirm: () => {
          setConfirmState((prev) => ({ ...prev, isOpen: false }));
          resolve(true);
        },
      });

      // Store reject callback for cancel
      const handleCancel = () => {
        setConfirmState((prev) => ({ ...prev, isOpen: false }));
        resolve(false);
      };

      // Update state with cancel handler
      setConfirmState((prev) => ({ ...prev, onCancel: handleCancel }));
    });
  }, []);

  const handleCancel = useCallback(() => {
    setConfirmState((prev) => ({ ...prev, isOpen: false }));
  }, []);

  const ConfirmDialogComponent = useCallback(() => {
    if (!confirmState.isOpen) return null;

    return (
      <ConfirmDialog
        isOpen={confirmState.isOpen}
        title={confirmState.title}
        message={confirmState.message}
        confirmText={confirmState.confirmText}
        cancelText={confirmState.cancelText}
        variant={confirmState.variant}
        onConfirm={confirmState.onConfirm}
        onCancel={handleCancel}
      />
    );
  }, [confirmState, handleCancel]);

  return { confirm, ConfirmDialogComponent };
};
