import { Button } from "../../atoms/button/button";

type ActionButtonBarProps = {
  cancelText: string;
  selectText: string;
  onCancel: () => void;
  onSelect: () => void;
};

export function ActionButtonBar({ cancelText, selectText, onCancel, onSelect }: ActionButtonBarProps) {
  return (
    <div className="pt-2 shrink-0 border-t border-gray-200 dark:border-gray-700">
      <div className="flex justify-end gap-3">
        <Button onClick={onCancel} variant="cancel">
          {cancelText}
        </Button>
        <Button onClick={onSelect} variant="submit">
          {selectText}
        </Button>
      </div>
    </div>
  );
}
