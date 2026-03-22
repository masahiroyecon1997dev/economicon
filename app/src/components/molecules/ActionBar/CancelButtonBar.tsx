import { Button } from "../../atoms/Button/Button";

type CancelButtonBarProps = {
  cancelText: string;
  onCancel: () => void;
};

export const CancelButtonBar = ({
  cancelText,
  onCancel,
}: CancelButtonBarProps) => {
  return (
    <div className="py-2 shrink-0 border-t border-gray-200 dark:border-gray-700">
      <div className="flex justify-end gap-2">
        <Button onClick={onCancel} variant="outline" className="px-4 py-1.5">
          {cancelText}
        </Button>
      </div>
    </div>
  );
};
