type SortIconProps = {
  direction: 'asc' | 'desc' | null;
};

export function SortIcon({ direction }: SortIconProps) {
  if (direction === 'asc') {
    return <span> ▲</span>;
  } else if (direction === 'desc') {
    return <span> ▼</span>;
  }
  return null;
}
