import { getEconomiconAppAPI } from "@/api/endpoints";
import type { AnalysisResultDetail } from "@/api/model";
import {
  updateAnalysisResultBodyDescriptionOneMax,
  updateAnalysisResultBodyNameOneMax,
  updateAnalysisResultBodySummaryTextOverrideOneMax,
} from "@/api/zod/analysis/analysis";
import { InputText } from "@/components/atoms/Input/InputText";
import { BaseDialog } from "@/components/molecules/Dialog/BaseDialog";
import { FormField } from "@/components/molecules/Form/FormField";
import { extractApiErrorMessage } from "@/lib/utils/apiError";
import { extractFieldError } from "@/lib/utils/formHelpers";
import { useAnalysisResultsStore } from "@/stores/analysisResults";
import { useWorkspaceTabsStore } from "@/stores/workspaceTabs";
import { useForm, useStore } from "@tanstack/react-form";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { z } from "zod";

// ─── フォームスキーマ（画面固有） ────────────────────────────────────────────

const editResultFormSchema = z.object({
  name: z.string().min(1).max(updateAnalysisResultBodyNameOneMax),
  description: z.string().max(updateAnalysisResultBodyDescriptionOneMax),
  summaryTextOverride: z
    .string()
    .max(updateAnalysisResultBodySummaryTextOverrideOneMax),
});

const FORM_ID = "edit-analysis-result-form";

// ─── Props ───────────────────────────────────────────────────────────────────

type EditAnalysisResultDialogProps = {
  isOpen: boolean;
  detail: AnalysisResultDetail;
  onClose: () => void;
};

// ─── Component ───────────────────────────────────────────────────────────────

export const EditAnalysisResultDialog = ({
  isOpen,
  detail,
  onClose,
}: EditAnalysisResultDialogProps) => {
  const { t } = useTranslation();
  const [apiError, setApiError] = useState<string | null>(null);

  const upsertSummary = useAnalysisResultsStore((s) => s.upsertSummary);
  const setActiveResult = useAnalysisResultsStore((s) => s.setActiveResult);
  const summaries = useAnalysisResultsStore((s) => s.summaries);
  const updateResultTabTitle = useWorkspaceTabsStore(
    (s) => s.updateResultTabTitle,
  );
  const updateResultTabDetail = useWorkspaceTabsStore(
    (s) => s.updateResultTabDetail,
  );

  const currentSummaryText =
    summaries.find((s) => s.id === detail.id)?.summaryText ?? "";

  const form = useForm({
    defaultValues: {
      name: detail.name,
      description: detail.description ?? "",
      summaryTextOverride: "",
    },
    validators: {
      onSubmit: editResultFormSchema,
    },
    onSubmit: async ({ value }) => {
      setApiError(null);
      try {
        const body = {
          name: value.name.trim(),
          description: value.description || null,
          summaryTextOverride: value.summaryTextOverride.trim() || null,
        };
        const response = await getEconomiconAppAPI().updateAnalysisResult(
          detail.id,
          body,
        );
        const { updatedSummary, updatedDetail } = response.result;

        upsertSummary(updatedSummary);
        updateResultTabTitle(detail.id, updatedDetail.name);
        updateResultTabDetail(detail.id, updatedDetail);
        setActiveResult(detail.id, updatedDetail);

        onClose();
      } catch (error) {
        setApiError(extractApiErrorMessage(error, t("Error.UnexpectedError")));
      }
    },
  });

  const isSubmitting = useStore(form.store, (s) => s.isSubmitting);
  const isDirty = useStore(form.store, (s) => s.isDirty);

  const handleOpenChange = (open: boolean) => {
    if (!open) onClose();
  };

  return (
    <BaseDialog
      open={isOpen}
      onOpenChange={handleOpenChange}
      title={t("EditAnalysisResultDialog.Title")}
      subtitle={detail.name}
      footerVariant="confirm"
      submitLabel={t("Common.Save")}
      submitFormId={FORM_ID}
      isSubmitting={isSubmitting}
      isSubmitDisabled={!isDirty}
    >
      <form
        id={FORM_ID}
        onSubmit={(e) => {
          e.preventDefault();
          e.stopPropagation();
          void form.handleSubmit();
        }}
        className="flex flex-col gap-4"
      >
        {/* 結果名 */}
        <form.Field
          name="name"
          validators={{
            onChange: ({ value }) => {
              if (!value.trim()) {
                return t("EditAnalysisResultDialog.NameRequired");
              }
              if (value.length > updateAnalysisResultBodyNameOneMax) {
                return t("EditAnalysisResultDialog.NameMaxLength", {
                  max: updateAnalysisResultBodyNameOneMax,
                });
              }
              return undefined;
            },
          }}
        >
          {(field) => (
            <FormField
              label={t("EditAnalysisResultDialog.NameLabel")}
              htmlFor="edit-result-name"
              error={extractFieldError(field.state.meta.errors)}
            >
              <InputText
                id="edit-result-name"
                value={field.state.value}
                onChange={(e) => field.handleChange(e.target.value)}
                onBlur={field.handleBlur}
                placeholder={t("EditAnalysisResultDialog.NamePlaceholder")}
                error={extractFieldError(field.state.meta.errors)}
                data-testid="edit-result-name-input"
              />
              <span className="sr-only">
                {t("EditAnalysisResultDialog.NameRequired")}
              </span>
            </FormField>
          )}
        </form.Field>

        {/* 説明 */}
        <form.Field
          name="description"
          validators={{
            onChange: ({ value }) => {
              if (value.length > updateAnalysisResultBodyDescriptionOneMax) {
                return t("EditAnalysisResultDialog.DescriptionMaxLength", {
                  max: updateAnalysisResultBodyDescriptionOneMax,
                });
              }
              return undefined;
            },
          }}
        >
          {(field) => (
            <FormField
              label={t("EditAnalysisResultDialog.DescriptionLabel")}
              htmlFor="edit-result-description"
              error={extractFieldError(field.state.meta.errors)}
            >
              <textarea
                id="edit-result-description"
                value={field.state.value}
                onChange={(e) => field.handleChange(e.target.value)}
                onBlur={field.handleBlur}
                placeholder={t(
                  "EditAnalysisResultDialog.DescriptionPlaceholder",
                )}
                rows={3}
                className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-transparent px-3 py-2 text-sm shadow-sm transition-colors placeholder:text-gray-400 dark:placeholder:text-gray-500 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-brand-primary disabled:cursor-not-allowed disabled:opacity-50"
                data-testid="edit-result-description-input"
              />
            </FormField>
          )}
        </form.Field>

        {/* サマリーテキスト上書き */}
        <form.Field
          name="summaryTextOverride"
          validators={{
            onChange: ({ value }) => {
              if (
                value.length > updateAnalysisResultBodySummaryTextOverrideOneMax
              ) {
                return t("EditAnalysisResultDialog.SummaryTextMaxLength", {
                  max: updateAnalysisResultBodySummaryTextOverrideOneMax,
                });
              }
              return undefined;
            },
          }}
        >
          {(field) => (
            <FormField
              label={t("EditAnalysisResultDialog.SummaryTextLabel")}
              htmlFor="edit-result-summary-text"
              error={extractFieldError(field.state.meta.errors)}
            >
              <InputText
                id="edit-result-summary-text"
                value={field.state.value}
                onChange={(e) => field.handleChange(e.target.value)}
                onBlur={field.handleBlur}
                placeholder={
                  currentSummaryText ||
                  t("EditAnalysisResultDialog.SummaryTextPlaceholder")
                }
                error={extractFieldError(field.state.meta.errors)}
                data-testid="edit-result-summary-text-input"
              />
              <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
                {t("EditAnalysisResultDialog.SummaryTextHint")}
              </p>
            </FormField>
          )}
        </form.Field>

        {/* APIエラー表示 */}
        {apiError && (
          <p
            className="rounded-md bg-red-50 dark:bg-red-900/20 px-3 py-2 text-sm text-red-600 dark:text-red-400"
            data-testid="edit-result-api-error"
          >
            {apiError}
          </p>
        )}
      </form>
    </BaseDialog>
  );
};
