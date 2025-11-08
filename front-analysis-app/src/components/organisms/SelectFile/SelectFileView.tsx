import { useState } from "react";
import { showErrorDialog } from "../../../function/errorDialog";
import { getFiles } from "../../../function/restApis";
import { useFilesStore } from "../../../stores/useFilesStore";
import { useSettingsStore } from "../../../stores/useSettingsStore";
import type { FileType } from "../../../types/commonTypes";

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

  // ローカル状態
  const [searchValue, setSearchValue] = useState("");
  const [activeFilter, setActiveFilter] = useState("all");

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
      await changeDirectory(newPath);
    } else {
      if (file.name.toLowerCase().endsWith('.csv')) {
        // CSVファイルの場合の処理

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
          files={filteredFiles}
          onFileClick={handleFileClick}
          fileNameHeader={t('SelectFileView.FileNameHeader')}
          sizeHeader={t('SelectFileView.SizeHeader')}
          lastModifiedHeader={t('SelectFileView.LastModifiedHeader')}
          maxHeight="500px"
        />
        <CancelButtonBar
          cancelText={t('Common.Cancel')}
          onCancel={handleCancel}
        />
      </div>
    </div>
  );
}
