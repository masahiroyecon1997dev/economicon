import * as RadixDropdownMenu from '@radix-ui/react-dropdown-menu';
import type { LucideIcon } from 'lucide-react';

import { cn } from '../../../functions/utils';

type MenuItemProps = {
  icon?: LucideIcon;
  label: string;
  handleSelect: () => void;
  variant?: 'default' | 'danger';
  isFirst?: boolean;
  isLast?: boolean;
};

export const MenuItem = ({ icon: Icon, label, handleSelect, variant = 'default', isFirst = false, isLast = false }: MenuItemProps) => {
  const variantClasses = {
    default: 'text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700',
    danger: 'text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20',
  };

  return (
    <RadixDropdownMenu.Item
      className={cn(
        'block items-center gap-3 w-full px-4 py-2 text-left text-sm transition-colors cursor-pointer outline-none',
        variantClasses[variant],
        isFirst && 'rounded-t-md',
        isLast && 'rounded-b-md'
      )}
      onSelect={handleSelect}
    >
      {Icon && <Icon className="w-4 h-4" />}
      <span>{label}</span>
    </RadixDropdownMenu.Item>
  );
};
