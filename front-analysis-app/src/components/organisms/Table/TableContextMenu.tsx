type TableContextMenuProps = {
  contextMenu: {
    x: number;
    y: number;
    targetId: string | null;
    type: 'header' | 'row' | 'cell' | null;
  } | null;
  handleCloseContextMenu: () => void;
};

export function TableContextMenu({ contextMenu, handleCloseContextMenu }: TableContextMenuProps) {
  if (!contextMenu) return null;

  return (
    <div
      className="fixed shadow-md bg-white border rounded"
      style={{ top: contextMenu.y, left: contextMenu.x, zIndex: 10 }}
      onClick={handleCloseContextMenu}
    >
      {contextMenu.type === 'header' && (
        <ul>
          <li className="px-4 py-2 hover:bg-gray-100">ヘッダーアクション</li>
        </ul>
      )}
      {contextMenu.type === 'row' && (
        <ul>
          <li className="px-4 py-2 hover:bg-gray-100">行アクション</li>
        </ul>
      )}
      {contextMenu.type === 'cell' && (
        <ul>
          <li className="px-4 py-2 hover:bg-gray-100">セルアクション</li>
        </ul>
      )}
    </div>
  );
}
