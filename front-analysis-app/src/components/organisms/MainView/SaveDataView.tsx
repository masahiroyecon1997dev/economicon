import { useState } from "react";
import { useTranslation } from "react-i18next";
import { showErrorDialog } from "../../../function/errorDialog";
import { exportCsvByPath, exportExcelByPath, exportParquetByPath, getFiles } from "../../../function/restApis";
import { useCurrentViewStore } from "../../../stores/useCurrentViewStore";
import { useFilesStore } from "../../../stores/useFilesStore";
import { useLoadingStore } from "../../../stores/useLoadingStore";
import { useSettingsStore } from "../../../stores/useSettingsStore";
import { useTableInfosStore } from "../../../stores/useTableInfosStore";
import { useTableListStore } from "../../../stores/useTableListStore";
import type { FileType, SortDirection, SortField } from "../../../types/commonTypes";
import { InputText } from "../../atoms/Input/InputText";
import { Select } from "../../atoms/Input/Select";
import { SelectOption } from "../../atoms/Input/SelectOption";
import { ActionButtonBar } from "../../molecules/ActionBar/ActionButtonBar";
import { CancelButtonBar } from "../../molecules/ActionBar/CancelButtonBar";
import { FormField } from "../../molecules/Form/FormField";
import { NavigationSearchBar } from "../../molecules/Navigation/NavigationSearchBar";
import { FileListTable } from "../../molecules/Table/FileListTable";

type FileFormat = 'csv' | 'excel' | 'parquet';

export const SaveDataView = () => {
  const { t } = useTranslation();
  const files = useFilesStore((state) => state.files);
  const directoryPath = useFilesStore((state) => state.directoryPath);
  const setFiles = useFilesStore((state) => state.setFiles);
  const osName = useSettingsStore((state) => state.osName);
  const pathSeparator = useSettingsStore((state) => state.pathSeparator);
  const activeTableName = useTableInfosStore((state) => state.activeTableName);
  const tableNameList = useTableListStore((state) => state.tableList);
  const setCurrentView = useCurrentViewStore((state) => state.setCurrentView);

  const { setLoading, clearLoading } = useLoadingStore();

  const [selectedTableName, setSelectedTableName] = useState(activeTableName || '');
  const [fileName, setFileName] = useState(activeTableName || '');
  const [fileFormat, setFileFormat] = useState<FileFormat>('csv');
  const [searchValue, setSearchValue] = useState("");
  const [sortField, setSortField] = useState<SortField | null>(null);
  const [sortDirection, setSortDirection] = useState<SortDirection>(null);
  const [errorMessage, setErrorMessage] = useState<{ tableName?: string; fileName?: string }>({});

  const fileFormatOptions = [
    { value: 'csv', label: 'CSV (.csv)' },
    { value: 'excel', label: 'Excel (.xlsx)' },
    { value: 'parquet', label: 'Parquet (.parquet)' },
  ];

  const getPathSegments = () => {
    if (!directoryPath) return [];
    const separator = pathSeparator || '/';
    return directoryPath.split(separator).filter(segment => segment.length > 0);
  };

  const buildPathUpToIndex = (index: number) => {
    const segments = getPathSegments();
    const separator = pathSeparator || '/';

    if (index < 0) {
      return separator;
    }

    const selectedSegments = segments.slice(0, index + 1);
    let path = selectedSegments.join(separator);

    if (osName === 'Windows') {
      path += separator;
    } else if (separator === '/') {
      path = '/' + path;
    }

    return path;
  };

  const changeDirectory = async (newPath: string) => {
    setLoading(true, t("Loading.Loading"));
    try {
      const response = await getFiles(newPath);
      if (response.code === "OK") {
        setFiles(response.result);
      } else {
        await showErrorDialog(t('Error.Error'), response.message);
      }
    } catch (error) {
      await showErrorDialog(t('Error.Error'), t('Error.UnexpectedError'));
    } finally {
      clearLoading();
    }
  };

  const goUpDirectory = async () => {
    const segments = getPathSegments();
    if (segments.length > 0) {
      const parentPath = buildPathUpToIndex(segments.length - 2);
      await changeDirectory(parentPath);
    }
  };

  const handleBreadcrumbClick = async (index: number) => {
    const targetPath = buildPathUpToIndex(index);
    await changeDirectory(targetPath);
  };

  const handleFileClick = async (file: FileType) => {
    if (!file.isFile) {
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
          await showErrorDialog(t('Error.Error'), response.message);
        }
      } catch (error) {
        await showErrorDialog(t('Error.Error'), t('Error.UnexpectedError'));
      } finally {
        clearLoading();
      }
    }
  };

  const validateInput = (): boolean => {
    const errors: { tableName?: string; fileName?: string } = {};

    if (!selectedTableName || selectedTableName.trim() === '') {
      errors.tableName = t('ValidationMessages.TableNameRequired');
    }

    if (!fileName || fileName.trim() === '') {
      errors.fileName = t('ValidationMessages.FileNameRequired');
    }

    setErrorMessage(errors);
    return Object.keys(errors).length === 0;
  };

  const getFileExtension = (): string => {
    switch (fileFormat) {
      case 'csv':
        return '.csv';
      case 'excel':
        return '.xlsx';
      case 'parquet':
        return '.parquet';
      default:
        return '';
    }
  };

  const handleSave = async () => {
    if (!validateInput()) {
      return;
    }

    if (!selectedTableName) {
      await showErrorDialog(t('Error.Error'), t('SaveDataView.NoActiveTable'));
      return;
    }

    setLoading(true, t('SaveDataView.SavingFile'));

    try {
      const fullFileName = fileName.endsWith(getFileExtension())
        ? fileName
        : fileName + getFileExtension();

      let response;

      switch (fileFormat) {
        case 'csv':
          response = await exportCsvByPath({
            tableName: selectedTableName,
            directoryPath: directoryPath,
            fileName: fullFileName,
            separator: ',',
          });
          break;
        case 'excel':
          response = await exportExcelByPath({
            tableName: selectedTableName,
            directoryPath: directoryPath,
            fileName: fullFileName,
            sheetName: 'Sheet1',
          });
          break;
        case 'parquet':
          response = await exportParquetByPath({
            tableName: selectedTableName,
            directoryPath: directoryPath,
            fileName: fullFileName,
          });
          break;
      }

      if (response.code === 'OK') {
        await showErrorDialog(t('Common.OK'), t('SaveDataView.SaveSuccess', { path: response.result.filePath }));
        setCurrentView('DataPreview');
      } else {
        await showErrorDialog(t('Error.Error'), response.message);
      }
    } catch (error) {
      await showErrorDialog(t('Error.Error'), t('Error.UnexpectedError'));
    } finally {
      clearLoading();
    }
  };

  const hadleCancelNoTables = async () => {
    setCurrentView('SelectFile');
  };

  const handleCancel = () => {
    setCurrentView('DataPreview');
  };

  const filteredFiles = files.filter(file => {
    const matchesSearch = file.name.toLowerCase().includes(searchValue.toLowerCase());
    return matchesSearch;
  });

  const sortedFiles = [...filteredFiles].sort((a, b) => {
    if (!sortField || !sortDirection) return 0;

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

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      if (sortDirection === 'asc') {
        setSortDirection('desc');
      } else if (sortDirection === 'desc') {
        setSortField(null);
        setSortDirection(null);
      } else {
        setSortDirection('asc');
      }
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  return (
    <div className="mx-auto w-full max-w-none px-4">
      {tableNameList.length === 0 ? (
        <div className="flex flex-col justify-center h-full gap-6">
          <div className="text-left">
            <h1 className="text-3xl font-bold text-black mb-4">{t("SaveDataView.Title")}</h1>
            <p className="text-lg text-black/60">{t("SaveDataView.NoTablesImported")}</p>
          </div>
          <CancelButtonBar
            cancelText={t('Common.Cancel')}
            onCancel={hadleCancelNoTables}
          />
        </div>
      ) : (
        <div className="flex flex-col gap-8">
          <header>
            <h1 className="text-3xl font-bold text-black">{t("SaveDataView.Title")}</h1>
            <p className="mt-2 text-base text-black/60">{t("SaveDataView.Description")}</p>
          </header>

          <div className="flex flex-col gap-4 flex-1 min-h-0 overflow-y-auto">
            <div className="flex flex-col gap-4">
              <h2 className="text-lg font-bold text-black">{t("SaveDataView.SelectDirectory")}</h2>
              <NavigationSearchBar
                pathSegments={getPathSegments()}
                searchValue={searchValue}
                searchPlaceholder={t("SelectFileView.SearchPlaceholder")}
                upDirectoryTitle={t('SelectFileView.GoUpDirectory')}
                onUpDirectory={goUpDirectory}
                onBreadcrumbClick={handleBreadcrumbClick}
                onSearchChange={setSearchValue}
              />
            </div>

            <div className="flex-1 min-h-0">
              <FileListTable
                files={sortedFiles}
                onFileClick={handleFileClick}
                fileNameHeader={t('SelectFileView.FileNameHeader')}
                sizeHeader={t('SelectFileView.SizeHeader')}
                lastModifiedHeader={t('SelectFileView.LastModifiedHeader')}
                maxHeight="200px"
                sortField={sortField}
                sortDirection={sortDirection}
                onSort={handleSort}
              />
            </div>

            <div className="bg-white dark:bg-gray-800/50 p-4 rounded-lg border border-border-color dark:border-gray-700 flex-shrink-0">
              <h2 className="text-main dark:text-white text-lg font-bold mb-3">{t("SaveDataView.FileSettings")}</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <FormField
                  label={t("SaveDataView.TableName")}
                  htmlFor="table-name"
                >
                  <Select
                    id="table-name"
                    value={selectedTableName}
                    onChange={(e) => {
                      setSelectedTableName(e.target.value);
                      setFileName(e.target.value);
                    }}
                  >
                    {tableNameList.map(tableName => (
                      <SelectOption key={tableName} value={tableName}>
                        {tableName}
                      </SelectOption>
                    ))}
                  </Select>
                </FormField>

                <FormField
                  label={t("SaveDataView.FileName")}
                  htmlFor="file-name"
                >
                  <InputText
                    id="file-name"
                    value={fileName}
                    change={(e) => setFileName(e.target.value)}
                    placeholder={t("SaveDataView.FileNamePlaceholder")}
                    error={errorMessage.fileName}
                  />
                </FormField>

                <FormField
                  label={t("SaveDataView.FileFormat")}
                  htmlFor="file-format"
                >
                  <Select
                    id="file-format"
                    value={fileFormat}
                    onChange={(e) => setFileFormat(e.target.value as FileFormat)}
                  >
                    {fileFormatOptions.map(option => (
                      <SelectOption key={option.value} value={option.value}>
                        {option.label}
                      </SelectOption>
                    ))}
                  </Select>
                </FormField>
              </div>
            </div>
          </div>

          <div className="pt-2 flex-shrink-0 border-t border-gray-200 dark:border-gray-700">
            <ActionButtonBar
              cancelText={t('Common.Cancel')}
              selectText={t('SaveDataView.Save')}
              onCancel={handleCancel}
              onSelect={handleSave}
            />
          </div>
        </div>
      )}
    </div>
  );
};
