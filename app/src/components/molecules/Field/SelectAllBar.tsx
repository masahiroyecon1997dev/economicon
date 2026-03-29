type SelectAllBarProps = {
  selectAllLabel: string;
  deselectAllLabel: string;
  onSelectAll: () => void;
  onDeselectAll: () => void;
  disabled?: boolean;
};

export const SelectAllBar = ({
  selectAllLabel,
  deselectAllLabel,
  onSelectAll,
  onDeselectAll,
  disabled,
}: SelectAllBarProps) => (
  <div className="flex gap-3">
    <button
      type="button"
      onClick={onSelectAll}
      disabled={disabled}
      className="text-xs text-brand-accent hover:underline disabled:opacity-50"
    >
      {selectAllLabel}
    </button>
    <span className="text-xs text-brand-text-sub">/</span>
    <button
      type="button"
      onClick={onDeselectAll}
      disabled={disabled}
      className="text-xs text-brand-accent hover:underline disabled:opacity-50"
    >
      {deselectAllLabel}
    </button>
  </div>
);
