import { useEffect, useRef, useState, type ReactNode } from 'react';

type TooltipPosition = 'top' | 'bottom' | 'left' | 'right';

type TooltipProps = {
  content: string;
  position?: TooltipPosition;
  children: ReactNode;
  delay?: number;
  maxWidth?: number;
};

export const Tooltip = ({
  content,
  position = 'top',
  children,
  delay = 200,
  maxWidth = 300
}: TooltipProps) => {
  const [isVisible, setIsVisible] = useState(false);
  const [adjustedPosition, setAdjustedPosition] = useState<TooltipPosition>(position);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const tooltipRef = useRef<HTMLDivElement | null>(null);
  const wrapperRef = useRef<HTMLDivElement | null>(null);

  const handleMouseEnter = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    timeoutRef.current = setTimeout(() => {
      setIsVisible(true);
    }, delay);
  };

  const handleMouseLeave = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    setIsVisible(false);
  };

  useEffect(() => {
    if (!isVisible || !tooltipRef.current || !wrapperRef.current) return;

    const tooltip = tooltipRef.current;
    const wrapper = wrapperRef.current;
    const tooltipRect = tooltip.getBoundingClientRect();
    const wrapperRect = wrapper.getBoundingClientRect();
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;

    let newPosition = position;

    // 水平方向のチェック
    if (position === 'left' || position === 'right') {
      if (position === 'right' && wrapperRect.right + tooltipRect.width > viewportWidth) {
        newPosition = 'left';
      } else if (position === 'left' && wrapperRect.left - tooltipRect.width < 0) {
        newPosition = 'right';
      }
    }

    // 垂直方向のチェック
    if (position === 'top' || position === 'bottom') {
      if (position === 'top' && wrapperRect.top - tooltipRect.height < 0) {
        newPosition = 'bottom';
      } else if (position === 'bottom' && wrapperRect.bottom + tooltipRect.height > viewportHeight) {
        newPosition = 'top';
      }
    }

    setAdjustedPosition(newPosition);
  }, [isVisible, position]);

  const getPositionClasses = (): string => {
    const baseClasses = 'absolute z-50 pointer-events-none';

    switch (adjustedPosition) {
      case 'top':
        return `${baseClasses} bottom-full left-1/2 -translate-x-1/2 mb-2`;
      case 'bottom':
        return `${baseClasses} top-full left-1/2 -translate-x-1/2 mt-2`;
      case 'left':
        return `${baseClasses} right-full top-1/2 -translate-y-1/2 mr-2`;
      case 'right':
        return `${baseClasses} left-full top-1/2 -translate-y-1/2 ml-2`;
      default:
        return `${baseClasses} bottom-full left-1/2 -translate-x-1/2 mb-2`;
    }
  };

  const getArrowClasses = (): string => {
    const baseArrow = 'absolute w-0 h-0 border-solid pointer-events-none';

    switch (adjustedPosition) {
      case 'top':
        return `${baseArrow} top-full left-1/2 -translate-x-1/2 border-t-[6px] border-t-gray-900 border-x-[6px] border-x-transparent`;
      case 'bottom':
        return `${baseArrow} bottom-full left-1/2 -translate-x-1/2 border-b-[6px] border-b-gray-900 border-x-[6px] border-x-transparent`;
      case 'left':
        return `${baseArrow} left-full top-1/2 -translate-y-1/2 border-l-[6px] border-l-gray-900 border-y-[6px] border-y-transparent`;
      case 'right':
        return `${baseArrow} right-full top-1/2 -translate-y-1/2 border-r-[6px] border-r-gray-900 border-y-[6px] border-y-transparent`;
      default:
        return `${baseArrow} top-full left-1/2 -translate-x-1/2 border-t-[6px] border-t-gray-900 border-x-[6px] border-x-transparent`;
    }
  };

  return (
    <div
      ref={wrapperRef}
      className="relative inline-block"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {children}

      {isVisible && content && (
        <div className={getPositionClasses()}>
          <div
            ref={tooltipRef}
            className="relative bg-gray-900 text-white text-xs rounded px-3 py-1.5 shadow-lg break-words"
            style={{ maxWidth: `${maxWidth}px` }}
          >
            {content}
            <div className={getArrowClasses()} />
          </div>
        </div>
      )}
    </div>
  );
};
