/**
 * テーブル削除確認フォーム
 */
import { AlertTriangle } from "lucide-react";
import { useState } from "react";
import { Trans, useTranslation } from "react-i18next";
import { getEconomiconAPI } from "../../../../api/endpoints";
import { showMessageDialog } from "../../../../lib/dialog/message";
import { useCurrentPageStore } from "../../../../stores/currentView";
import { useTableInfosStore } from "../../../../stores/tableInfos";
import { useTableListStore } from "../../../../stores/tableList";
import { Button } from "../../../atoms/Button/Button";

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
        await showMessageDialog(t("Error.Error"), t("Error.UnexpectedError"));
      }
    } catch (error) {
      const message =
        error instanceof Error ? error.message : t("Error.UnexpectedError");
      await showMessageDialog(t("Error.Error"), message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* 警告バナー */}
      <div className="flex items-start gap-3 rounded-lg border border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950/30 p-4">
        <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-red-500" />
        <p className="text-sm text-red-700 dark:text-red-400">
          <Trans
            i18nKey="DeleteTableForm.Warning"
            values={{ tableName }}
            components={{ b: <strong /> }}
          />
        </p>
      </div>

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
