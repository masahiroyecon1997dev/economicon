/**
 * テーブル削除確認フォーム
 */
import { useEffect, useState } from "react";
import { Trans, useTranslation } from "react-i18next";
import { getEconomiconAppAPI } from "@/api/endpoints";
import {
  extractApiErrorMessage,
  getResponseErrorMessage,
} from "@/lib/utils/apiError";
import { useCurrentPageStore } from "@/stores/currentView";
import { useTableInfosStore } from "@/stores/tableInfos";
import { useTableListStore } from "@/stores/tableList";
import { DangerAlert } from "@/components/molecules/Alert/DangerAlert";
import { ErrorAlert } from "@/components/molecules/Alert/ErrorAlert";

type DeleteTableFormProps = {
  tableName: string;
  onSuccess: () => void;
  formId: string;
  onIsSubmittingChange: (isSubmitting: boolean) => void;
};

export const DeleteTableForm = ({
  tableName,
  onSuccess,
  formId,
  onIsSubmittingChange,
}: DeleteTableFormProps) => {
  const { t } = useTranslation();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  useEffect(() => {
    onIsSubmittingChange(isSubmitting);
  }, [isSubmitting, onIsSubmittingChange]);

  const setTableList = useTableListStore((s) => s.setTableList);
  const removeTableInfo = useTableInfosStore((s) => s.removeTableInfo);
  const activeTableName = useTableInfosStore((s) => s.activeTableName);
  const setCurrentView = useCurrentPageStore((s) => s.setCurrentView);

  const handleDelete = async () => {
    setIsSubmitting(true);
    setApiError(null);
    try {
      const response = await getEconomiconAppAPI().deleteTable({ tableName });
      if (response.code === "OK") {
        // テーブル一覧を再取得
        const listRes = await getEconomiconAppAPI().getTableList();
        if (listRes.code === "OK") {
          setTableList(listRes.result.tableNameList);
        }
        // tableInfos から削除
        removeTableInfo(tableName);
        // アクティブなテーブルが削除された場合はファイル選択画面へ
        if (activeTableName === tableName) {
          useTableInfosStore.setState({ activeTableName: null });
          setCurrentView("ImportDataFile");
        }
        onSuccess();
      } else {
        setApiError(
          getResponseErrorMessage(response, t("Error.UnexpectedError")),
        );
      }
    } catch (error) {
      setApiError(extractApiErrorMessage(error, t("Error.UnexpectedError")));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form
      id={formId}
      onSubmit={(e) => {
        e.preventDefault();
        e.stopPropagation();
        void handleDelete();
      }}
      className="space-y-4"
    >
      <DangerAlert>
        <Trans
          i18nKey="DeleteTableForm.Warning"
          values={{ tableName }}
          components={{ b: <strong /> }}
        />
      </DangerAlert>

      {apiError && <ErrorAlert message={apiError} />}
    </form>
  );
};
