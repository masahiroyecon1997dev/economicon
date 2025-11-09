import { CancelButton } from "../../atoms/Button/CancelButton";

type CancelButtonBarProps = {
  cancelText: string;
  onCancel: () => void;
};

export function CancelButtonBar({ cancelText, onCancel }: CancelButtonBarProps) {
  return (
    <div className="flex justify-end gap-3">
      <CancelButton cancel={onCancel}>
        {cancelText}
      </CancelButton>
    </div>
  );
}
