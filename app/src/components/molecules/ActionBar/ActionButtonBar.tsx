import { Loader2 } from "lucide-react";
import { Button } from "@/components/atoms/Button/Button";

type ActionButtonBarProps = {
  cancelText: string;
  selectText: string;
  onCancel: () => void;
  onSelect: () => void;
  onSelectType?: "button" | "submit" | "reset";
  disabled?: boolean;
  isLoading?: boolean;
};

export const ActionButtonBar = ({
  cancelText,
  selectText,
  onCancel,
  onSelect,
  onSelectType = "button",
  disabled,
  isLoading,
}: ActionButtonBarProps) => {
  return (
    <div className="py-2 shrink-0 border-t border-gray-200 dark:border-gray-700">
      <div className="flex justify-end gap-2">
        <Button
          onClick={onCancel}
          variant="outline"
          className="px-4 py-1.5"
          disabled={disabled || isLoading}
        >
          {cancelText}
        </Button>
        <Button
          onClick={onSelect}
          variant="primary"
          type={onSelectType}
          className="inline-flex items-center px-4 py-1.5"
          disabled={disabled || isLoading}
        >
          {isLoading && (
            <Loader2
              className="mr-1.5 h-3.5 w-3.5 animate-spin"
              aria-hidden="true"
            />
          )}
          {selectText}
        </Button>
      </div>
    </div>
  );
};
