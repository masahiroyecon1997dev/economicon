import { getEconomiconAppAPI } from "@/api/endpoints";
import { showMessageDialog } from "@/lib/dialog/message";
import { useLoadingStore } from "@/stores/loading";
import { useTableInfosStore } from "@/stores/tableInfos";
import type { ColumnType } from "@/types/commonTypes";
import { useEffect, useEffectEvent, useState } from "react";
import { useTranslation } from "react-i18next";

type UseTableColumnLoaderOptions = {
  numericOnly?: boolean;
  autoLoadOnMount?: boolean;
  initialSelectedTableName?: string;
  onLoadedColumns?: (columns: ColumnType[]) => void;
};

export const useTableColumnLoader = (
  options: UseTableColumnLoaderOptions = {},
) => {
  const {
    numericOnly = false,
    autoLoadOnMount = true,
    initialSelectedTableName,
    onLoadedColumns,
  } = options;
  const { t } = useTranslation();
  const activeTableName = useTableInfosStore((state) => state.activeTableName);
  const setLoading = useLoadingStore((s) => s.setLoading);
  const clearLoading = useLoadingStore((s) => s.clearLoading);
  // TODO : アクティブなテーブルがなければ、テーブルリストの最初のテーブルをセットする処理を追加する
  const [selectedTableName, setSelectedTableName] = useState<string>(
    initialSelectedTableName ?? activeTableName ?? "",
  );
  const [columnList, setColumnList] = useState<ColumnType[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const notifyLoadedColumns = useEffectEvent((columns: ColumnType[]) => {
    onLoadedColumns?.(columns);
  });

  useEffect(() => {
    let cancelled = false;
    if (!selectedTableName) {
      setColumnList([]);
      setIsLoading(false);
      return () => {
        cancelled = true;
      };
    }

    const loadColumnList = async (tableName: string) => {
      setIsLoading(true);
      setLoading(true, t("Loading.Loading"));
      try {
        const api = getEconomiconAppAPI();
        const response = await api.getColumnList({
          tableName,
          // isNumberOnlyはbooleanに変更（旧APIはstring型"true"/"false"だったが新APIはbool）
          isNumberOnly: numericOnly ? true : undefined,
        });
        if (cancelled) return;
        if (response.code === "OK") {
          setColumnList(response.result.columnInfoList);
          notifyLoadedColumns(response.result.columnInfoList);
        } else {
          await showMessageDialog(t("Error.Error"), t("Error.UnexpectedError"));
        }
      } catch {
        if (cancelled) return;
        await showMessageDialog(t("Error.Error"), t("Error.UnexpectedError"));
      } finally {
        if (!cancelled) {
          setIsLoading(false);
          clearLoading();
        }
      }
    };
    if (autoLoadOnMount && selectedTableName) {
      loadColumnList(selectedTableName);
    }
    return () => {
      cancelled = true;
      clearLoading();
    };
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
    isLoading,
    setColumnList,
  };
};
