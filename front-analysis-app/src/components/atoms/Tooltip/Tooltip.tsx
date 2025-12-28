import * as RadixTooltip from '@radix-ui/react-tooltip';
import type { ReactNode } from 'react';

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
  delay = 500,
  maxWidth = 300
}: TooltipProps) => {
  return (
    <RadixTooltip.Provider delayDuration={delay}>
      <RadixTooltip.Root>
        <RadixTooltip.Trigger asChild>
          {children}
        </RadixTooltip.Trigger>
        <RadixTooltip.Portal>
          <RadixTooltip.Content
            side={position}
            sideOffset={8}
            className="z-50 bg-gray-900 text-white text-xs rounded px-3 py-1.5 shadow-lg break-words"
            style={{ maxWidth: `${maxWidth}px` }}
          >
            {content}
            <RadixTooltip.Arrow className="fill-gray-900" />
          </RadixTooltip.Content>
        </RadixTooltip.Portal>
      </RadixTooltip.Root>
    </RadixTooltip.Provider>
  );
};
