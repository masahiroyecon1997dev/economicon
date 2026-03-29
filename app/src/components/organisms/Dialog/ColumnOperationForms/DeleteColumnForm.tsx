/**
 * 列削除確認フォーム
 */
import { useEffect, useState } from "react";
import { Trans, useTranslation } from "react-i18next";
import { getEconomiconAppAPI } from "../../../../api/endpoints";
import {
  extractApiErrorMessage,
  getResponseErrorMessage,
} from "../../../../lib/utils/apiError";
import { DangerAlert } from "../../../molecules/Alert/DangerAlert";
import { ErrorAlert } from "../../../molecules/Alert/ErrorAlert";
import { fetchUpdatedColumnList } from "./fetchUpdatedColumnList";
import type { ColumnOperationFormPropsType } from "./types";

export const DeleteColumnForm = ({
  tableName,
  column,
  formId,
  onIsSubmittingChange,
  onSuccess,
}: ColumnOperationFormPropsType) => {
  const { t } = useTranslation();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  useEffect(() => {
    onIsSubmittingChange(isSubmitting);
  }, [isSubmitting, onIsSubmittingChange]);

  const handleDelete = async () => {
    setIsSubmitting(true);
    setApiError(null);
    try {
      const response = await getEconomiconAppAPI().deleteColumn({
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
          i18nKey="DeleteColumnForm.Warning"
          values={{ columnName: column.name }}
          components={{ b: <strong /> }}
        />
      </DangerAlert>

      {apiError && <ErrorAlert message={apiError} />}
    </form>
  );
};
