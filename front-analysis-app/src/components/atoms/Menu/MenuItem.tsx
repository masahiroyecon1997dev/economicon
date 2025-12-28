import type { IconDefinition } from "@fortawesome/fontawesome-svg-core";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import * as RadixDropdownMenu from '@radix-ui/react-dropdown-menu';

type MenuItemProps = {
  icon?: IconDefinition;
  label: string;
  // onClick: () => void;
  variant?: 'default' | 'danger';
};

export const MenuItem = ({ icon, label, variant = 'default' }: MenuItemProps) => {
  const variantClasses = {
    default: 'text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700',
    danger: 'text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20',
  };

  return (
    <RadixDropdownMenu.Item

      className={`flex items-center gap-3 w-full px-4 py-2 text-left text-sm transition-colors cursor-pointer outline-none ${variantClasses[variant]}`}
    >
      {icon && <FontAwesomeIcon icon={icon} className="w-4" />}
      <span>{label}</span>
    </RadixDropdownMenu.Item>
  );
};
