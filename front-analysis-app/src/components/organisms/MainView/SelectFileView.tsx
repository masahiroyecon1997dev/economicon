import { useState } from "react";
import { showErrorDialog } from "../../../function/errorDialog";
import { getTableInfo } from "../../../function/internalFunctions";
import { getFiles, importCsvByPath, importExcelByPath, importParquetByPath } from "../../../function/restApis";
import { useFilesStore } from "../../../stores/useFilesStore";
import { useLoadingStore } from "../../../stores/useLoadingStore";
import { useSettingsStore } from "../../../stores/useSettingsStore";
import { useTableInfosStore } from "../../../stores/useTableInfosStore";
import type { FileType, SortDirection, SortField } from "../../../types/commonTypes";

import { useTranslation } from "react-i18next";
import { useCurrentViewStore } from "../../../stores/useCurrentViewStore";
import { CancelButtonBar } from "../../molecules/ActionBar/CancelButtonBar";
import { NavigationSearchBar } from "../../molecules/Navigation/NavigationSearchBar";
import { FileListTable } from "../../molecules/Table/FileListTable";

export const SelectFileView = () => {
  const { t } = useTranslation();
  const files = useFilesStore((state) => state.files);
  const directoryPath = useFilesStore((state) => state.directoryPath);
  const setFiles = useFilesStore((state) => state.setFiles);
  const osName = useSettingsStore((state) => state.osName);
  const pathSeparator = useSettingsStore((state) => state.pathSeparator);
  const addTableInfo = useTableInfosStore((state) => state.addTableInfo);
  const setCurrentView = useCurrentViewStore((state) => state.setCurrentView);

  // ローディング状態
  const { setLoading, clearLoading } = useLoadingStore();

  // ローカル状態
  const [searchValue, setSearchValue] = useState("");
  const [sortField, setSortField] = useState<SortField | null>(null);
  const [sortDirection, setSortDirection] = useState<SortDirection>(null);

  // 現在のディレクトリパスを配列に分割してパンくずリストを作成
  const getPathSegments = () => {
    if (!directoryPath) return [];
    const separator = pathSeparator || '/';
    return directoryPath.split(separator).filter(segment => segment.length > 0);
  };

  // 指定したインデックスまでのパスを構築
  const buildPathUpToIndex = (index: number) => {
    const segments = getPathSegments();
    const separator = pathSeparator || '/';

    if (index < 0) {
      // ルートディレクトリの場合
      return separator;
    }

    const selectedSegments = segments.slice(0, index + 1);
    let path = selectedSegments.join(separator);

    // Windowsの場合のドライブレター対応
    if (osName === 'Windows') {
      path += separator;
    } else if (separator === '/') {
      path = '/' + path;
    }

    return path;
  };

  // ディレクトリ変更関数
  const changeDirectory = async (newPath: string) => {
    setLoading(true, t("Loading.Loading"));
    try {
      const response = await getFiles(newPath);
      if (response.code === "OK") {
        setFiles(response.result);
      } else {
        await showErrorDialog(t('Common.Error'), response.message);
      }
    } catch (error) {
      await showErrorDialog(t('Common.Error'), t('Error.UnexpectedError'));
    } finally {
      clearLoading();
    }
  };  // 上位ディレクトリに移動
  const goUpDirectory = async () => {
    const segments = getPathSegments();
    if (segments.length > 0) {
      const parentPath = buildPathUpToIndex(segments.length - 2);
      await changeDirectory(parentPath);
    }
  };

  // パンくずリストのクリックハンドラー
  const handleBreadcrumbClick = async (index: number) => {
    const targetPath = buildPathUpToIndex(index);
    await changeDirectory(targetPath);
  };

  // ファイル/ディレクトリのクリックハンドラー
  const handleFileClick = async (file: FileType) => {
    if (!file.isFile) {
      // ディレクトリの場合は移動
      const separator = pathSeparator || '/';
      const newPath = directoryPath === separator
        ? separator + file.name
        : directoryPath + separator + file.name;

      setLoading(true, t("Loading.Loading"));
      try {
        const response = await getFiles(newPath);
        if (response.code === "OK") {
          setFiles(response.result);
        } else {
          await showErrorDialog(t('Common.Error'), response.message);
          return;
        }
      } catch (error) {
        await showErrorDialog(t('Common.Error'), t('Error.UnexpectedError'));
        return;
      } finally {
        clearLoading();
      }
    } else {
      // ファイルの場合はインポート処理
      setLoading(true, t("Loading.Loading"));
      try {
        let loadTableName = '';
        if (file.name.toLowerCase().endsWith('.csv')) {
          // CSVファイルの場合の処理
          const response = await importCsvByPath({
            filePath: directoryPath + '/' + file.name,
            tableName: file.name.replace('.csv', ''),
            separator: ',',
          });
          if (response.code !== "OK") {
            await showErrorDialog(t('Common.Error'), response.message);
            return;
          }
          loadTableName = response.result.tableName;
        } else if (file.name.toLowerCase().endsWith('.xlsx') || file.name.toLowerCase().endsWith('.xls')) {
          // Excelファイルの場合の処理
          const response = await importExcelByPath({
            filePath: directoryPath + '/' + file.name,
            tableName: file.name.replace(/\.(xlsx|xls)$/, ''),
            sheetName: '',
          });
          if (response.code !== "OK") {
            await showErrorDialog(t('Common.Error'), response.message);
            return;
          }
          loadTableName = response.result.tableName;
        } else if (file.name.toLowerCase().endsWith('.parquet')) {
          // Parquetファイルの場合の処理
          const response = await importParquetByPath({
            filePath: directoryPath + '/' + file.name,
            tableName: file.name.replace('.parquet', ''),
          });
          if (response.code !== "OK") {
            await showErrorDialog(t('Common.Error'), response.message);
            return;
          }
          loadTableName = response.result.tableName;
        }
        const resTableInfo = await getTableInfo(loadTableName);
        addTableInfo(resTableInfo);
        setCurrentView("dataPreview");
      } catch (error) {
        await showErrorDialog(t('Common.Error'), t('Error.UnexpectedError'));
      } finally {
        clearLoading();
      }
    }
  };

  // 検索とフィルターを適用したファイル一覧
  const filteredFiles = files.filter(file => {
    // 検索フィルター
    const matchesSearch = file.name.toLowerCase().includes(searchValue.toLowerCase());
    return matchesSearch;
  });  // ソート処理
  const sortedFiles = [...filteredFiles].sort((a, b) => {
    if (!sortField || !sortDirection) return 0;

    // ディレクトリを常に上に表示
    if (a.isFile !== b.isFile) {
      return a.isFile ? 1 : -1;
    }

    let aValue: string | number = '';
    let bValue: string | number = '';

    switch (sortField) {
      case 'name':
        aValue = a.name.toLowerCase();
        bValue = b.name.toLowerCase();
        break;
      case 'size':
        aValue = a.isFile ? (a.size || 0) : 0;
        bValue = b.isFile ? (b.size || 0) : 0;
        break;
      case 'modifiedTime':
        aValue = a.isFile ? new Date(a.modifiedTime).getTime() : 0;
        bValue = b.isFile ? new Date(b.modifiedTime).getTime() : 0;
        break;
    }

    if (aValue < bValue) {
      return sortDirection === 'asc' ? -1 : 1;
    }
    if (aValue > bValue) {
      return sortDirection === 'asc' ? 1 : -1;
    }
    return 0;
  });

  // ソートハンドラー
  const handleSort = (field: SortField) => {
    if (sortField === field) {
      // 同じフィールドの場合は方向を切り替え
      if (sortDirection === 'asc') {
        setSortDirection('desc');
      } else if (sortDirection === 'desc') {
        setSortField(null);
        setSortDirection(null);
      } else {
        setSortDirection('asc');
      }
    } else {
      // 異なるフィールドの場合は昇順で開始
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const handleCancel = () => {
    setCurrentView("dataPreview");
  };

  return (
    <div className="mx-auto max-w-10xl">
      <div className="flex flex-col gap-8">
        <header>
          <h1 className="text-3xl font-bold text-black">{t("SelectFileView.Title")}</h1>
          <p className="mt-2 text-base text-black/60">{t("SelectFileView.Description")}</p>
        </header>

        <div className="flex flex-col gap-4">
          <NavigationSearchBar
            pathSegments={getPathSegments()}
            searchValue={searchValue}
            searchPlaceholder={t("SelectFileView.SearchPlaceholder")}
            upDirectoryTitle={t('SelectFileView.GoUpDirectory')}
            onUpDirectory={goUpDirectory}
            onBreadcrumbClick={handleBreadcrumbClick}
            onSearchChange={setSearchValue}
          />
          {/* <FileFilterBar
            filters={filterOptions}
            onFilterClick={setActiveFilter}
          /> */}
        </div>

        <FileListTable
          files={sortedFiles}
          onFileClick={handleFileClick}
          fileNameHeader={t('SelectFileView.FileNameHeader')}
          sizeHeader={t('SelectFileView.SizeHeader')}
          lastModifiedHeader={t('SelectFileView.LastModifiedHeader')}
          maxHeight="500px"
          sortField={sortField}
          sortDirection={sortDirection}
          onSort={handleSort}
        />
        <CancelButtonBar
          cancelText={t('Common.Cancel')}
          onCancel={handleCancel}
        />
      </div>
    </div>
  );
}
