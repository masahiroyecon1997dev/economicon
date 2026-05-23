/**
 * 列削除確認フォーム
 */
import { useState } from "react";
import { Trans, useTranslation } from "react-i18next";
import { getEconomiconAppAPI } from "@/api/endpoints";
import { useFormSubmitting } from "@/hooks/useFormSubmitting";
import {
  buildCaughtErrorMessage,
  buildResponseErrorMessage,
} from "@/lib/utils/apiError";
import { DangerAlert } from "@/components/molecules/Alert/DangerAlert";
import { ErrorAlert } from "@/components/molecules/Alert/ErrorAlert";
import { fetchUpdatedColumnList } from "@/components/organisms/Dialog/ColumnOperationForms/fetchUpdatedColumnList";
import type { ColumnOperationFormPropsType } from "@/components/organisms/Dialog/ColumnOperationForms/types";

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
  useFormSubmitting(isSubmitting, onIsSubmittingChange);

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
          buildResponseErrorMessage(response, t("Error.UnexpectedError")),
        );
      }
    } catch (error) {
      setApiError(buildCaughtErrorMessage(error, t("Error.UnexpectedError")));
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
