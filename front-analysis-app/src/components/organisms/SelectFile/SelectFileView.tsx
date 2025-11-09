import { useState } from "react";
import { showErrorDialog } from "../../../function/errorDialog";
import { getTableInfo } from "../../../function/internalFunctions";
import { getFiles, importCsvByPath } from "../../../function/restApis";
import { useFilesStore } from "../../../stores/useFilesStore";
import { useSettingsStore } from "../../../stores/useSettingsStore";
import { useTableInfosStore } from "../../../stores/useTableInfosStore";
import type { FileType } from "../../../types/commonTypes";
import type { SortDirection, SortField } from "../../../types/stateTypes";

import { useTranslation } from "react-i18next";
import { CancelButtonBar } from "../../molecules/ActionBar/CancelButtonBar";
import { FileFilterBar } from "../../molecules/Filter/FileFilterBar";
import { NavigationSearchBar } from "../../molecules/Navigation/NavigationSearchBar";
import { FileListTable } from "../../molecules/Table/FileListTable";

export const SelectFileView = () => {
  const { t } = useTranslation();
  const files = useFilesStore((state) => state.files);
  const setFiles = useFilesStore((state) => state.setFiles);
  const settings = useSettingsStore((state) => state.settings);
  const addTableInfos = useTableInfosStore((state) => state.addTableInfo);

  // ローカル状態
  const [searchValue, setSearchValue] = useState("");
  const [activeFilter, setActiveFilter] = useState("all");
  const [sortField, setSortField] = useState<SortField | null>(null);
  const [sortDirection, setSortDirection] = useState<SortDirection>(null);

  // 現在のディレクトリパスを配列に分割してパンくずリストを作成
  const getPathSegments = () => {
    if (!files.directoryPath) return [];
    const separator = settings.pathSeparator || '/';
    return files.directoryPath.split(separator).filter(segment => segment.length > 0);
  };

  // 指定したインデックスまでのパスを構築
  const buildPathUpToIndex = (index: number) => {
    const segments = getPathSegments();
    const separator = settings.pathSeparator || '/';

    if (index < 0) {
      // ルートディレクトリの場合
      return separator;
    }

    const selectedSegments = segments.slice(0, index + 1);
    let path = selectedSegments.join(separator);

    // Windowsの場合のドライブレター対応
    if (separator === '\\' && selectedSegments.length === 1) {
      path += separator;
    } else if (separator === '/') {
      path = '/' + path;
    }

    return path;
  };

  // ディレクトリを変更する関数
  const changeDirectory = async (newPath: string) => {
    try {
      const response = await getFiles(newPath);
      if (response.code === "OK") {
        setFiles({ files: response.result });
      } else {
        await showErrorDialog(t('Common.Error'), response.message);
      }
    } catch (error) {
      await showErrorDialog(t('Common.Error'), t('Common.UnexpectedError'));
    }
  };

  // 上位ディレクトリに移動
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
      const separator = settings.pathSeparator || '/';
      const newPath = files.directoryPath === separator
        ? separator + file.name
        : files.directoryPath + separator + file.name;
      try {
        const response = await getFiles(newPath);
        if (response.code === "OK") {
          setFiles({ files: response.result });
        } else {
          await showErrorDialog(t('Common.Error'), response.message);
          return;
        }
      } catch (error) {
        await showErrorDialog(t('Common.Error'), t('Common.UnexpectedError'));
        return;
      }

    } else {
      if (file.name.toLowerCase().endsWith('.csv')) {
        // CSVファイルの場合の処理
        const response = await importCsvByPath({
          filePath: files.directoryPath + '/' + file.name,
          tableName: file.name.replace('.csv', ''),
          separator: ',',
        });
        if (response.code !== "OK") {
          await showErrorDialog(t('Common.Error'), response.message);
          return;
        }
        const tableInfo = await getTableInfo(response.result.tableName);
        addTableInfos(tableInfo);
      }
    }
  };

  // 検索とフィルターを適用したファイル一覧
  const filteredFiles = files.files.filter(file => {
    // 検索フィルター
    const matchesSearch = file.name.toLowerCase().includes(searchValue.toLowerCase());

    // ファイルタイプフィルター
    let matchesFileType = true;
    if (activeFilter === "csv") {
      matchesFileType = file.isFile && file.name.toLowerCase().endsWith('.csv');
    } else if (activeFilter === "excel") {
      matchesFileType = file.isFile && (
        file.name.toLowerCase().endsWith('.xlsx') ||
        file.name.toLowerCase().endsWith('.xls')
      );
    }

    return matchesSearch && matchesFileType;
  });

  // ソート処理
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

  // フィルターオプション
  const filterOptions = [
    { label: t('SelectFileView.AllFiles'), value: "all", isActive: activeFilter === "all" },
    { label: t('SelectFileView.CsvFiles'), value: "csv", isActive: activeFilter === "csv" },
    { label: t('SelectFileView.ExcelFiles'), value: "excel", isActive: activeFilter === "excel" }
  ];

  // イベントハンドラー
  const handleCancel = () => {
    // キャンセル処理
  };

  const handleSelect = () => {
    // 選択処理
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
          <FileFilterBar
            filters={filterOptions}
            onFilterClick={setActiveFilter}
          />
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
