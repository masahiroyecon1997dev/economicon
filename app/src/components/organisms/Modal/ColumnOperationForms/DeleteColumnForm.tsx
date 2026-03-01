/**
 * 列削除確認フォーム
 */
import { AlertTriangle } from "lucide-react";
import { useState } from "react";
import { Trans, useTranslation } from "react-i18next";
import { getEconomiconAPI } from "../../../../api/endpoints";
import { showMessageDialog } from "../../../../lib/dialog/message";
import { Button } from "../../../atoms/Button/Button";
import { fetchUpdatedColumnList } from "./fetchUpdatedColumnList";
import type { ColumnOperationFormPropsType } from "./types";

export const DeleteColumnForm = ({
  tableName,
  column,
  onSuccess,
  onClose,
}: ColumnOperationFormPropsType) => {
  const { t } = useTranslation();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleDelete = async () => {
    setIsSubmitting(true);
    try {
      const response = await getEconomiconAPI().deleteColumn({
        tableName,
        columnName: column.name,
      });
      if (response.code === "OK") {
        const updatedList = await fetchUpdatedColumnList(tableName);
        onSuccess(updatedList);
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
      <div className="flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 p-4">
        <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-red-500" />
        <p className="text-sm text-red-700">
          <Trans
            i18nKey="DeleteColumnForm.Warning"
            values={{ columnName: column.name }}
            components={{ b: <strong /> }}
          />
        </p>
      </div>

      <div className="flex justify-end gap-2 pt-2">
        <Button variant="outline" onClick={onClose} disabled={isSubmitting}>
          {t("Common.Cancel")}
        </Button>
        <button
          type="button"
          onClick={() => void handleDelete()}
          disabled={isSubmitting}
          className="inline-flex items-center justify-center rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isSubmitting ? "..." : t("DeleteColumnForm.Submit")}
        </button>
      </div>
    </div>
  );
};
