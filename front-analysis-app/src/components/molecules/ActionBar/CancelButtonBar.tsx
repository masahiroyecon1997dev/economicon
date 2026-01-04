import { CancelButton } from "../../atoms/Button/CancelButton";

type CancelButtonBarProps = {
  cancelText: string;
  onCancel: () => void;
};

export function CancelButtonBar({ cancelText, onCancel }: CancelButtonBarProps) {
  return (
    <div className="pt-2 shrink-0 border-t border-gray-200 dark:border-gray-700">
      <div className="flex justify-end gap-3">
        <CancelButton cancel={onCancel}>
          {cancelText}
        </CancelButton>
      </div>
    </div>
  );
}
