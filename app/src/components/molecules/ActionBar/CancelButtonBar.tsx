import { Button } from "../../atoms/Button/Button";

type CancelButtonBarProps = {
  cancelText: string;
  onCancel: () => void;
};

export const CancelButtonBar = ({ cancelText, onCancel }: CancelButtonBarProps) => {
  return (
    <div className="pt-2 shrink-0 border-t border-gray-200 dark:border-gray-700">
      <div className="flex justify-end gap-3">
        <Button onClick={onCancel} variant="outline">
          {cancelText}
        </Button>
      </div>
    </div>
  );
}
