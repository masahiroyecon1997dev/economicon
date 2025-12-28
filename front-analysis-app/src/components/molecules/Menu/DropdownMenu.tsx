import * as RadixDropdownMenu from '@radix-ui/react-dropdown-menu';
import type { ReactNode } from 'react';

type DropdownMenuProps = {
  isOpen: boolean;
  onClose: () => void;
  children: ReactNode;
  position?: 'bottom-left' | 'bottom-right' | 'top-left' | 'top-right';
  triggerElement: ReactNode;
};

export const DropdownMenu = ({
  children,
  position = 'bottom-right',
  triggerElement
}: DropdownMenuProps) => {
  const getSideAndAlign = (): { side: 'top' | 'bottom'; align: 'start' | 'end' } => {
    switch (position) {
      case 'bottom-left':
        return { side: 'bottom', align: 'end' };
      case 'bottom-right':
        return { side: 'bottom', align: 'start' };
      case 'top-left':
        return { side: 'top', align: 'end' };
      case 'top-right':
        return { side: 'top', align: 'start' };
      default:
        return { side: 'bottom', align: 'start' };
    }
  };

  const { side, align } = getSideAndAlign();

  return (
    <RadixDropdownMenu.Root>
      <RadixDropdownMenu.Trigger asChild>
        {triggerElement}
      </RadixDropdownMenu.Trigger>

      <RadixDropdownMenu.Portal>
        <RadixDropdownMenu.Content
          side={side}
          align={align}
          sideOffset={4}
          className="z-50 min-w-[160px] rounded-md bg-white dark:bg-gray-800 shadow-lg border border-gray-200 dark:border-gray-700 py-1 data-[state=open]:animate-fade-in data-[state=closed]:animate-fade-out"
        >
          {children}
        </RadixDropdownMenu.Content>
      </RadixDropdownMenu.Portal>
    </RadixDropdownMenu.Root>
  );
};
