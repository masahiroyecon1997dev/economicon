import { useEffect, useRef, type ReactNode } from 'react';

type DropdownMenuProps = {
  isOpen: boolean;
  onClose: () => void;
  children: ReactNode;
  position?: 'bottom-left' | 'bottom-right' | 'top-left' | 'top-right';
};

export const DropdownMenu = ({
  isOpen,
  onClose,
  children,
  position = 'bottom-right'
}: DropdownMenuProps) => {
  const menuRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!isOpen) return;

    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleEscape);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const getPositionClasses = (): string => {
    switch (position) {
      case 'bottom-left':
        return 'top-full left-0 mt-1';
      case 'bottom-right':
        return 'top-full right-0 mt-1';
      case 'top-left':
        return 'bottom-full left-0 mb-1';
      case 'top-right':
        return 'bottom-full right-0 mb-1';
      default:
        return 'top-full right-0 mt-1';
    }
  };

  return (
    <div
      ref={menuRef}
      className={`absolute z-50 min-w-[160px] rounded-md bg-white dark:bg-gray-800 shadow-lg border border-gray-200 dark:border-gray-700 py-1 ${getPositionClasses()}`}
    >
      {children}
    </div>
  );
};
