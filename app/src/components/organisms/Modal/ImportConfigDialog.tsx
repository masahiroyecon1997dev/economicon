import * as RadixDialog from '@radix-ui/react-dialog';
import { X } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

type ImportConfigDialogProps = {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  fileInfo: { path: string; name: string } | null;
  onImport: (settings: { tableName: string; sheetName?: string; separator?: string }) => void;
};

export const ImportConfigDialog = ({
  isOpen,
  onOpenChange,
  fileInfo,
  onImport,
}: ImportConfigDialogProps) => {
  const { t } = useTranslation();
  const [tableName, setTableName] = useState('');
  const [sheetName, setSheetName] = useState('');
  const [separator, setSeparator] = useState(',');

  useEffect(() => {
    if (isOpen && fileInfo) {
      // 初期値設定
      // 拡張子を除いたファイル名をテーブル名とする
      const nameWithoutExt = fileInfo.name.replace(/\.[^/.]+$/, "");
      setTableName(nameWithoutExt);
      setSheetName('');
      setSeparator(',');
    }
  }, [isOpen, fileInfo]);

  const handleImport = () => {
    onImport({
      tableName,
      sheetName: sheetName || undefined,
      separator: separator || undefined,
    });
    onOpenChange(false);
  };

  if (!fileInfo) return null;

  const isExcel = fileInfo.name.toLowerCase().endsWith('.xlsx') || fileInfo.name.toLowerCase().endsWith('.xls');
  const isCsv = fileInfo.name.toLowerCase().endsWith('.csv');

  return (
    <RadixDialog.Root open={isOpen} onOpenChange={onOpenChange}>
      <RadixDialog.Portal>
        <RadixDialog.Overlay className="fixed inset-0 z-50 bg-black/50 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />
        <RadixDialog.Content className="fixed left-[50%] top-[50%] z-50 grid w-full max-w-lg translate-x-[-50%] translate-y-[-50%] gap-4 border bg-white p-6 shadow-lg duration-200 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[state=closed]:slide-out-to-left-1/2 data-[state=closed]:slide-out-to-top-[48%] data-[state=open]:slide-in-from-left-1/2 data-[state=open]:slide-in-from-top-[48%] sm:rounded-lg md:w-full">
          <div className="flex flex-col space-y-1.5 text-center sm:text-left">
            <RadixDialog.Title className="text-lg font-semibold leading-none tracking-tight">
              {t('ImportDataFileView.ImportDialog.Title')}
            </RadixDialog.Title>
            <RadixDialog.Description className="text-sm text-gray-500">
              {fileInfo.path}
            </RadixDialog.Description>
          </div>

          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <label htmlFor="tableName" className="text-right text-sm font-medium">
                {t('ImportDataFileView.ImportDialog.TableName')}
              </label>
              <input
                id="tableName"
                value={tableName}
                onChange={(e) => setTableName(e.target.value)}
                className="col-span-3 flex h-9 w-full rounded-md border border-gray-300 bg-transparent px-3 py-1 text-sm shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-gray-400 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-gray-950 disabled:cursor-not-allowed disabled:opacity-50"
              />
            </div>

            {isExcel && (
              <div className="grid grid-cols-4 items-center gap-4">
                <label htmlFor="sheetName" className="text-right text-sm font-medium">
                  {t('ImportDataFileView.ImportDialog.SheetName')}
                </label>
                <input
                  id="sheetName"
                  value={sheetName}
                  onChange={(e) => setSheetName(e.target.value)}
                  placeholder="Sheet1"
                  className="col-span-3 flex h-9 w-full rounded-md border border-gray-300 bg-transparent px-3 py-1 text-sm shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-gray-400 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-gray-950 disabled:cursor-not-allowed disabled:opacity-50"
                />
              </div>
            )}

            {isCsv && (
              <div className="grid grid-cols-4 items-center gap-4">
                <label htmlFor="separator" className="text-right text-sm font-medium">
                  {t('ImportDataFileView.ImportDialog.Separator')}
                </label>
                <input
                  id="separator"
                  value={separator}
                  onChange={(e) => setSeparator(e.target.value)}
                  className="col-span-3 flex h-9 w-full rounded-md border border-gray-300 bg-transparent px-3 py-1 text-sm shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-gray-400 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-gray-950 disabled:cursor-not-allowed disabled:opacity-50"
                />
              </div>
            )}
          </div>

          <div className="flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2">
            <button
              className="mt-2 inline-flex h-9 items-center justify-center rounded-md border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-900 shadow-sm hover:bg-gray-100 hover:text-gray-900 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-gray-950 disabled:pointer-events-none disabled:opacity-50 sm:mt-0"
              onClick={() => onOpenChange(false)}
            >
              {t('Common.Cancel')}
            </button>
            <button
              className="inline-flex h-9 items-center justify-center rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-gray-50 shadow hover:bg-gray-900/90 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-gray-950 disabled:pointer-events-none disabled:opacity-50"
              onClick={handleImport}
            >
              {t('ImportDataFileView.ImportDialog.Import')}
            </button>
          </div>

          <RadixDialog.Close asChild>
            <button
              className="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-white transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-gray-950 focus:ring-offset-2 disabled:pointer-events-none data-[state=open]:bg-gray-100 data-[state=open]:text-gray-500"
            >
              <X className="h-4 w-4" />
              <span className="sr-only">Close</span>
            </button>
          </RadixDialog.Close>
        </RadixDialog.Content>
      </RadixDialog.Portal>
    </RadixDialog.Root>
  );
};
