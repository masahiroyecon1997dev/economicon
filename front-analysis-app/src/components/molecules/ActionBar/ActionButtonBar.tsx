import { Button } from "../../atoms/Button/Button";

type ActionButtonBarProps = {
  cancelText: string;
  selectText: string;
  onCancel: () => void;
  onSelect: () => void;
  onSelectType?: "button" | "submit" | "reset";
};

export function ActionButtonBar({ cancelText, selectText, onCancel, onSelect, onSelectType = "button" }: ActionButtonBarProps) {
  return (
    <div className="pt-2 shrink-0 border-t border-gray-200 dark:border-gray-700">
      <div className="flex justify-end gap-3">
        <Button onClick={onCancel} variant="outline">
          {cancelText}
        </Button>
        <Button onClick={onSelect} variant="primary" type={onSelectType}>
          {selectText}
        </Button>
      </div>
    </div>
  );
}
