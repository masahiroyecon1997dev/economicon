import { CancelButton } from "../../atoms/Button/CancelButton";
import { SubmitButton } from "../../atoms/Button/SubmitButton";

type ActionButtonBarProps = {
  cancelText: string;
  selectText: string;
  onCancel: () => void;
  onSelect: () => void;
};

export function ActionButtonBar({ cancelText, selectText, onCancel, onSelect }: ActionButtonBarProps) {
  return (
    <div className="flex justify-end gap-3">
      <CancelButton cancel={onCancel}>
        {cancelText}
      </CancelButton>
      <SubmitButton submit={onSelect}>
        {selectText}
      </SubmitButton>
    </div>
  );
}
