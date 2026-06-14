import { getEconomiconAppAPI } from "@/api/endpoints";
import { Select, SelectItem } from "@/components/atoms/Input/Select";
import { BaseDialog } from "@/components/molecules/Dialog/BaseDialog";
import { FormField } from "@/components/molecules/Form/FormField";
import { showMessageDialog } from "@/lib/dialog/message";
import {
  buildCaughtErrorMessage,
  buildResponseErrorMessage,
} from "@/lib/utils/apiError";
import { getTableInfo } from "@/lib/utils/internal";
import { useTableInfosStore } from "@/stores/tableInfos";
import { useTableListStore } from "@/stores/tableList";
import { useWorkspaceTabsStore } from "@/stores/workspaceTabs";
import { useState } from "react";
import { useTranslation } from "react-i18next";

type DiagnosticTarget = "fitted" | "residual" | "both";

type AddDiagnosticColumnsDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  resultId: string;
  defaultTableName: string;
};

const FORM_ID = "add-diagnostic-columns-form";

export const AddDiagnosticColumnsDialog = ({
  open,
  onOpenChange,
  resultId,
  defaultTableName,
}: AddDiagnosticColumnsDialogProps) => {
  const { t } = useTranslation();
  const tableList = useTableListStore((s) => s.tableList);
  const invalidateTable = useTableInfosStore((s) => s.invalidateTable);
  const activateTableInfo = useTableInfosStore((s) => s.activateTableInfo);
  const openDataTab = useWorkspaceTabsStore((s) => s.openDataTab);

  const [tableName, setTableName] = useState(
    tableList.includes(defaultTableName)
      ? defaultTableName
      : (tableList[0] ?? ""),
  );
  const [targets, setTargets] = useState<Set<DiagnosticTarget>>(
    new Set(["residual", "fitted"]),
  );
  const [isSubmitting, setIsSubmitting] = useState(false);

  const toggleTarget = (target: DiagnosticTarget) => {
    setTargets((prev) => {
      const next = new Set(prev);
      if (next.has(target)) {
        next.delete(target);
      } else {
        next.add(target);
      }
      return next;
    });
  };

  const resolveTarget = (): DiagnosticTarget | null => {
    const hasFitted = targets.has("fitted");
    const hasResidual = targets.has("residual");
    if (hasFitted && hasResidual) return "both";
    if (hasFitted) return "fitted";
    if (hasResidual) return "residual";
    return null;
  };

  const handleSubmit = async () => {
    const target = resolveTarget();
    if (!target) {
      await showMessageDialog(
        t("Error.Error"),
        t("AddDiagnosticColumns.ErrorSelectTarget"),
      );
      return;
    }
    if (!tableName) {
      await showMessageDialog(
        t("Error.Error"),
        t("ValidationMessages.DataNameSelect"),
      );
      return;
    }

    setIsSubmitting(true);
    try {
      const api = getEconomiconAppAPI();
      const response = await api.addDiagnosticColumns({
        tableName,
        resultId,
        target,
      });

      if (response.code === "OK" && response.result) {
        // テーブル情報を再取得して更新
        const updatedTableInfo = await getTableInfo(tableName);
        invalidateTable(tableName, {
          columnList: updatedTableInfo.columnList,
        });
        activateTableInfo(tableName);
        onOpenChange(false);
        // 対象テーブルのタブを前面に表示
        openDataTab(tableName);
        await showMessageDialog(
          t("Common.OK"),
          t("AddDiagnosticColumns.SuccessMessage", {
            columns: response.result.addedColumns.join(", "),
          }),
        );
      } else {
        await showMessageDialog(
          t("Error.Error"),
          buildResponseErrorMessage(response, t("Error.UnexpectedError")),
        );
      }
    } catch (error) {
      await showMessageDialog(
        t("Error.Error"),
        buildCaughtErrorMessage(error, t("Error.UnexpectedError")),
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const CHECKBOX_ITEMS: { value: DiagnosticTarget; labelKey: string }[] = [
    { value: "fitted", labelKey: "AddDiagnosticColumns.TargetFitted" },
    { value: "residual", labelKey: "AddDiagnosticColumns.TargetResidual" },
  ];

  return (
    <BaseDialog
      open={open}
      onOpenChange={onOpenChange}
      title={t("AddDiagnosticColumns.Title")}
      subtitle={t("AddDiagnosticColumns.Subtitle")}
      footerVariant="confirm"
      submitLabel={t("AddDiagnosticColumns.Submit")}
      submitFormId={FORM_ID}
      isSubmitting={isSubmitting}
      isSubmitDisabled={targets.size === 0 || !tableName}
    >
      <form
        id={FORM_ID}
        onSubmit={(e) => {
          e.preventDefault();
          e.stopPropagation();
          void handleSubmit();
        }}
        className="space-y-4 py-1"
      >
        {/* 追加先テーブル */}
        <FormField
          label={t("AddDiagnosticColumns.TableName")}
          htmlFor="diagnostic-table-name"
        >
          <Select
            id="diagnostic-table-name"
            value={tableName}
            onValueChange={setTableName}
            disabled={isSubmitting}
          >
            {tableList.map((name) => (
              <SelectItem key={name} value={name}>
                {name}
              </SelectItem>
            ))}
          </Select>
        </FormField>

        {/* 追加する列の種類（チェックボックス） */}
        <div className="space-y-1.5">
          <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
            {t("AddDiagnosticColumns.TargetLabel")}
          </p>
          <div className="space-y-2">
            {CHECKBOX_ITEMS.map(({ value, labelKey }) => (
              <label
                key={value}
                className="flex cursor-pointer items-center gap-2.5 rounded-lg border border-border-color bg-secondary/40 px-3 py-2.5 hover:bg-secondary transition-colors dark:border-gray-600 dark:bg-gray-700/30 dark:hover:bg-gray-700/60"
              >
                <input
                  type="checkbox"
                  className="h-4 w-4 rounded border-gray-300 dark:border-gray-500 text-accent focus:ring-accent"
                  checked={targets.has(value)}
                  onChange={() => toggleTarget(value)}
                  disabled={isSubmitting}
                />
                <span className="text-sm font-medium text-brand-text-main dark:text-gray-200">
                  {t(labelKey)}
                </span>
              </label>
            ))}
          </div>
        </div>
      </form>
    </BaseDialog>
  );
};
