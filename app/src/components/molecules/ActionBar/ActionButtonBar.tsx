import { Button } from "../../atoms/Button/Button";

type ActionButtonBarProps = {
  cancelText: string;
  selectText: string;
  onCancel: () => void;
  onSelect: () => void;
  onSelectType?: "button" | "submit" | "reset";
  disabled?: boolean;
};

export const ActionButtonBar = ({
  cancelText,
  selectText,
  onCancel,
  onSelect,
  onSelectType = "button",
  disabled,
}: ActionButtonBarProps) => {
  return (
    <div className="py-2 shrink-0 border-t border-gray-200 dark:border-gray-700">
      <div className="flex justify-end gap-2">
        <Button
          onClick={onCancel}
          variant="outline"
          className="px-4 py-1.5"
          disabled={disabled}
        >
          {cancelText}
        </Button>
        <Button
          onClick={onSelect}
          variant="primary"
          type={onSelectType}
          className="px-4 py-1.5"
          disabled={disabled}
        >
          {selectText}
        </Button>
      </div>
    </div>
  );
};
