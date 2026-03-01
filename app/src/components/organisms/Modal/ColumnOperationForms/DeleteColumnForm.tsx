/**
 * 列削除確認フォーム
 */
import { useState } from "react";
import { Trans, useTranslation } from "react-i18next";
import { getEconomiconAPI } from "../../../../api/endpoints";
import {
  extractApiErrorMessage,
  getResponseErrorMessage,
} from "../../../../lib/utils/apiError";
import { Button } from "../../../atoms/Button/Button";
import { DangerAlert } from "../../../molecules/Alert/DangerAlert";
import { ErrorAlert } from "../../../molecules/Alert/ErrorAlert";
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
  const [apiError, setApiError] = useState<string | null>(null);

  const handleDelete = async () => {
    setIsSubmitting(true);
    setApiError(null);
    try {
      const response = await getEconomiconAPI().deleteColumn({
        tableName,
        columnName: column.name,
      });
      if (response.code === "OK") {
        const updatedList = await fetchUpdatedColumnList(tableName);
        onSuccess(updatedList);
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
    <div className="space-y-4">
      <DangerAlert>
        <Trans
          i18nKey="DeleteColumnForm.Warning"
          values={{ columnName: column.name }}
          components={{ b: <strong /> }}
        />
      </DangerAlert>

      {apiError && <ErrorAlert message={apiError} />}

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
