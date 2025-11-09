import type { TableDataCellType } from '../../../types/commonTypes';

interface CellContentProps {
  value: TableDataCellType;
  onEdit: () => void;
}

export function CellContent({ value, onEdit }: CellContentProps) {
  return (
    <div className="flex items-center justify-between">
      <span onClick={onEdit}>{value}</span>
    </div>
  );
}
