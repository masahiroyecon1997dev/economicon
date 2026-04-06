import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { getEconomiconAppAPI } from "@/api/endpoints";
import { showMessageDialog } from "@/lib/dialog/message";
import { useLoadingStore } from "@/stores/loading";
import { useTableInfosStore } from "@/stores/tableInfos";
import type { ColumnType } from "@/types/commonTypes";

type UseTableColumnLoaderOptions = {
  numericOnly?: boolean;
  autoLoadOnMount?: boolean;
};

export const useTableColumnLoader = (
  options: UseTableColumnLoaderOptions = {},
) => {
  const { numericOnly = false, autoLoadOnMount = true } = options;
  const { t } = useTranslation();
  const activeTableName = useTableInfosStore((state) => state.activeTableName);
  const setLoading = useLoadingStore((s) => s.setLoading);
  const clearLoading = useLoadingStore((s) => s.clearLoading);
  // TODO : アクティブなテーブルがなければ、テーブルリストの最初のテーブルをセットする処理を追加する
  const [selectedTableName, setSelectedTableName] = useState<string>(
    activeTableName || "",
  );
  const [columnList, setColumnList] = useState<ColumnType[]>([]);

  useEffect(() => {
    let cancelled = false;
    const loadColumnList = async (tableName: string) => {
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
        } else {
          await showMessageDialog(t("Error.Error"), t("Error.UnexpectedError"));
        }
      } catch {
        if (cancelled) return;
        await showMessageDialog(t("Error.Error"), t("Error.UnexpectedError"));
      } finally {
        if (!cancelled) clearLoading();
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
    setColumnList,
  };
};
