import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { showMessageDialog } from "../functions/messageDialog";
import { getColumnList } from "../functions/restApis";
import { useLoadingStore } from "../stores/useLoadingStore";
import { useTableInfosStore } from "../stores/useTableInfosStore";
import type { ColumnType } from "../types/commonTypes";

type UseTableColumnLoaderOptions = {
  numericOnly?: boolean;
  autoLoadOnMount?: boolean;
};

export const useTableColumnLoader = (
  options: UseTableColumnLoaderOptions = {}
) => {
  const { numericOnly = false, autoLoadOnMount = true } = options;
  const { t } = useTranslation();
  const activeTableName = useTableInfosStore((state) => state.activeTableName);
  const { setLoading, clearLoading } = useLoadingStore();
  // TODO : アクティブなテーブルがなければ、テーブルリストの最初のテーブルをセットする処理を追加する
  const [selectedTableName, setSelectedTableName] = useState<string>(
    activeTableName || ""
  );
  const [columnList, setColumnList] = useState<ColumnType[]>([]);

  useEffect(() => {
    const loadColumnList = async (tableName: string) => {
      setLoading(true, t("Loading.Loading"));
      try {
        const response = await getColumnList(
          tableName,
          numericOnly ? "true" : undefined
        );
        if (response.code === "OK") {
          setColumnList(response.result.columnInfoList);
        } else {
          await showMessageDialog(t("Error.Error"), response.message);
        }
      } catch {
        await showMessageDialog(t("Error.Error"), t("Error.UnexpectedError"));
      } finally {
        clearLoading();
      }
    };
    if (autoLoadOnMount && selectedTableName) {
      loadColumnList(selectedTableName);
    }
  }, [
    selectedTableName,
    autoLoadOnMount,
    clearLoading,
    numericOnly,
    setLoading,
    t,
  ]);

  return {
    selectedTableName,
    setSelectedTableName,
    columnList,
    setColumnList,
  };
};
