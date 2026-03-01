/**
 * テーブル削除確認フォーム
 */
import { useState } from "react";
import { Trans, useTranslation } from "react-i18next";
import { getEconomiconAPI } from "../../../../api/endpoints";
import { showMessageDialog } from "../../../../lib/dialog/message";
import {
  extractApiErrorMessage,
  getResponseErrorMessage,
} from "../../../../lib/utils/apiError";
import { useCurrentPageStore } from "../../../../stores/currentView";
import { useTableInfosStore } from "../../../../stores/tableInfos";
import { useTableListStore } from "../../../../stores/tableList";
import { Button } from "../../../atoms/Button/Button";
import { DangerAlert } from "../../../molecules/Alert/DangerAlert";

type DeleteTableFormProps = {
  tableName: string;
  onSuccess: () => void;
  onClose: () => void;
};

export const DeleteTableForm = ({
  tableName,
  onSuccess,
  onClose,
}: DeleteTableFormProps) => {
  const { t } = useTranslation();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const setTableList = useTableListStore((s) => s.setTableList);
  const removeTableInfo = useTableInfosStore((s) => s.removeTableInfo);
  const activeTableName = useTableInfosStore((s) => s.activeTableName);
  const setCurrentView = useCurrentPageStore((s) => s.setCurrentView);

  const handleDelete = async () => {
    setIsSubmitting(true);
    try {
      const response = await getEconomiconAPI().deleteTable({ tableName });
      if (response.code === "OK") {
        // テーブル一覧を再取得
        const listRes = await getEconomiconAPI().getTableList();
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
        await showMessageDialog(
          t("Error.Error"),
          getResponseErrorMessage(response, t("Error.UnexpectedError")),
        );
      }
    } catch (error) {
      await showMessageDialog(
        t("Error.Error"),
        extractApiErrorMessage(error, t("Error.UnexpectedError")),
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-4">
      <DangerAlert>
        <Trans
          i18nKey="DeleteTableForm.Warning"
          values={{ tableName }}
          components={{ b: <strong /> }}
        />
      </DangerAlert>

      <div className="flex justify-end gap-2 pt-2">
        <Button variant="outline" onClick={onClose} disabled={isSubmitting}>
          {t("Common.Cancel")}
        </Button>
        <Button
          variant="primary"
          className="bg-red-600 hover:bg-red-700 dark:bg-red-700 dark:hover:bg-red-600 focus-visible:outline-red-600"
          onClick={handleDelete}
          disabled={isSubmitting}
        >
          {isSubmitting ? "..." : t("Common.Delete")}
        </Button>
      </div>
    </div>
  );
};
