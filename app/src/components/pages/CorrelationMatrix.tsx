import { ChevronDown } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { getEconomiconAppAPI } from "../../api/endpoints";
import { CorrelationMethod, MissingHandlingMethod } from "../../api/model";
import { useTableColumnLoader } from "../../hooks/useTableColumnLoader";
import { showMessageDialog } from "../../lib/dialog/message";
import { extractApiErrorMessage } from "../../lib/utils/apiError";
import { cn } from "../../lib/utils/helpers";
import { getTableInfo } from "../../lib/utils/internal";
import { useCurrentPageStore } from "../../stores/currentView";
import { useTableInfosStore } from "../../stores/tableInfos";
import { useTableListStore } from "../../stores/tableList";
import { InputText } from "../atoms/Input/InputText";
import { Select, SelectItem } from "../atoms/Input/Select";
import { ActionButtonBar } from "../molecules/ActionBar/ActionButtonBar";
import { CheckboxTagGroup } from "../molecules/Field/CheckboxTagGroup";
import { FormField } from "../molecules/Form/FormField";
import { PageLayout } from "../templates/PageLayout";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
type FormErrors = {
  table?: string;
  columns?: string;
  newTableName?: string;
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------
export const CorrelationMatrix = () => {
  const { t } = useTranslation();
  const tableList = useTableListStore((s) => s.tableList);
  const addTableInfo = useTableInfosStore((s) => s.addTableInfo);
  const setCurrentView = useCurrentPageStore((s) => s.setCurrentView);

  // Column loader (numeric only)
  const { selectedTableName, setSelectedTableName, columnList, setColumnList } =
    useTableColumnLoader({ numericOnly: true, autoLoadOnMount: true });

  // Form state
  const [checkedCols, setCheckedCols] = useState<Set<string>>(new Set());
  const [newTableName, setNewTableName] = useState("");
  const [method, setMethod] = useState<CorrelationMethod>(
    CorrelationMethod.pearson,
  );
  const [decimalPlaces, setDecimalPlaces] = useState(3);
  const [lowerTriangleOnly, setLowerTriangleOnly] = useState(false);
  const [missingHandling, setMissingHandling] = useState<MissingHandlingMethod>(
    MissingHandlingMethod.pairwise,
  );
  const [optionsOpen, setOptionsOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<FormErrors>({});

  // Sync column list → check all by default
  useEffect(() => {
    setCheckedCols(new Set(columnList.map((c) => c.name)));
  }, [columnList]);

  // Reset columns when table changes
  const handleTableSelect = (value: string) => {
    setSelectedTableName(value);
    if (!value) setColumnList([]);
    setCheckedCols(new Set());
    setErrors({});
  };

  const toggleCol = (name: string) => {
    setCheckedCols((prev) => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      return next;
    });
  };

  // ---------------------------------------------------------------------------
  // Submit
  // ---------------------------------------------------------------------------
  const handleSubmit = async () => {
    const newErrors: FormErrors = {};
    if (!selectedTableName)
      newErrors.table = t("CorrelationMatrix.ErrorDataRequired");
    if (checkedCols.size < 2)
      newErrors.columns = t("CorrelationMatrix.ErrorColumnsRequired");
    if (!newTableName.trim())
      newErrors.newTableName = t("CorrelationMatrix.ErrorOutputNameRequired");

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }
    setErrors({});
    setIsSubmitting(true);
    try {
      const api = getEconomiconAppAPI();
      const orderedCols = columnList
        .map((c) => c.name)
        .filter((n) => checkedCols.has(n));
      const resp = await api.createCorrelationTable({
        tableName: selectedTableName,
        columnNames: orderedCols,
        newTableName: newTableName.trim(),
        method,
        decimalPlaces,
        lowerTriangleOnly,
        missingHandling,
      });
      if (resp.code === "OK") {
        const tableInfo = await getTableInfo(resp.result.tableName);
        addTableInfo(tableInfo);
        setCurrentView("DataPreview");
      } else {
        await showMessageDialog(t("Error.Error"), t("Error.UnexpectedError"));
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

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------
  return (
    <PageLayout
      title={t("CorrelationMatrix.Title")}
      description={t("CorrelationMatrix.Description")}
    >
      <div className="flex min-h-0 flex-1 flex-col gap-3">
        {/* ── TOP: テーブル選択（1行コンパクト）── */}
        <div className="shrink-0 rounded-xl border border-border-color bg-white px-3 py-2 shadow-sm dark:bg-gray-800 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <label className="shrink-0 text-xs font-medium text-brand-text-main">
              {t("CorrelationMatrix.DataLabel")}
            </label>
            <div className="flex-1">
              <Select
                value={selectedTableName}
                onValueChange={handleTableSelect}
                disabled={isSubmitting}
                placeholder={t("CorrelationMatrix.SelectData")}
                error={errors.table}
              >
                {tableList.map((name) => (
                  <SelectItem key={name} value={name}>
                    {name}
                  </SelectItem>
                ))}
              </Select>
            </div>
            {errors.table && (
              <p className="shrink-0 text-xs text-red-600">{errors.table}</p>
            )}
          </div>
        </div>

        {/* ── MIDDLE: 2ペイン（列選択 + オプション）── */}
        <div className="flex min-h-0 flex-1 gap-3">
          {/* 左: 対象列（主役・flex-1）*/}
          <div className="flex min-h-0 flex-1 flex-col rounded-xl border border-border-color bg-white p-3 shadow-sm dark:bg-gray-800 dark:border-gray-700">
            <div className="mb-2 flex shrink-0 items-center justify-between">
              <h2 className="text-sm font-bold leading-tight text-text-heading dark:text-gray-100">
                {t("CorrelationMatrix.ColumnsLabel")}
              </h2>
              {columnList.length > 0 && (
                <div className="flex gap-3">
                  <button
                    type="button"
                    onClick={() =>
                      setCheckedCols(new Set(columnList.map((c) => c.name)))
                    }
                    disabled={isSubmitting}
                    className="text-xs text-brand-accent hover:underline disabled:opacity-50"
                  >
                    {t("CorrelationMatrix.SelectAll")}
                  </button>
                  <span className="text-xs text-brand-text-sub">/</span>
                  <button
                    type="button"
                    onClick={() => setCheckedCols(new Set())}
                    disabled={isSubmitting}
                    className="text-xs text-brand-accent hover:underline disabled:opacity-50"
                  >
                    {t("CorrelationMatrix.DeselectAll")}
                  </button>
                </div>
              )}
            </div>

            <div className="min-h-0 flex-1 overflow-y-auto">
              {!selectedTableName ? (
                <p className="text-sm text-brand-text-sub">
                  {t("CorrelationMatrix.SelectData")}
                </p>
              ) : columnList.length === 0 ? (
                <p className="text-sm text-brand-text-sub">
                  {t("CorrelationMatrix.NoColumns")}
                </p>
              ) : (
                <CheckboxTagGroup
                  items={columnList.map((c) => ({
                    value: c.name,
                    label: c.name,
                  }))}
                  checked={checkedCols}
                  onToggle={toggleCol}
                  disabled={isSubmitting}
                  error={errors.columns}
                />
              )}
            </div>
          </div>

          {/* 右: オプション + 出力名（w-56）*/}
          <div className="flex w-56 shrink-0 flex-col gap-3">
            {/* 出力データ名（常時表示・必須）*/}
            <div className="rounded-xl border border-border-color bg-white p-3 shadow-sm dark:bg-gray-800 dark:border-gray-700">
              <FormField
                label={t("CorrelationMatrix.OutputDataLabel")}
                htmlFor="new-table-name"
                error={errors.newTableName}
              >
                <InputText
                  id="new-table-name"
                  value={newTableName}
                  onChange={(e) => {
                    setNewTableName(e.target.value);
                    if (errors.newTableName)
                      setErrors((prev) => ({ ...prev, newTableName: undefined }));
                  }}
                  placeholder={t("CorrelationMatrix.OutputDataPlaceholder")}
                  disabled={isSubmitting}
                />
              </FormField>
            </div>

            {/* 詳細オプション（accordion）*/}
            <div className="rounded-xl border border-border-color bg-white shadow-sm dark:bg-gray-800 dark:border-gray-700">
              <button
                type="button"
                onClick={() => setOptionsOpen((v) => !v)}
                className="flex w-full items-center justify-between px-3 py-2.5 text-left transition-colors hover:bg-secondary/50 dark:hover:bg-gray-700/50"
              >
                <div className="flex flex-col gap-0.5">
                  <span className="text-sm font-bold text-text-heading dark:text-gray-100">
                    {t("CorrelationMatrix.AdvancedOptions")}
                  </span>
                  <span className="text-xs text-brand-text-main/60 dark:text-gray-400">
                    {t("CorrelationMatrix.AdvancedOptionsSummary", {
                      method: t(`CorrelationMatrix.Method_${method}`),
                      places: decimalPlaces,
                      missing: t(`CorrelationMatrix.Missing_${missingHandling}`),
                    })}
                  </span>
                </div>
                <ChevronDown
                  className={cn(
                    "h-4 w-4 shrink-0 text-brand-text-main/60 transition-transform duration-200",
                    optionsOpen && "rotate-180",
                  )}
                />
              </button>

              {optionsOpen && (
                <div className="border-t border-border-color px-3 pb-4 pt-3 dark:border-gray-700">
                  <div className="flex flex-col gap-3">
                    {/* 計算手法 */}
                    <FormField
                      label={t("CorrelationMatrix.MethodLabel")}
                      htmlFor="correlation-method"
                    >
                      <Select
                        id="correlation-method"
                        value={method}
                        onValueChange={(v) =>
                          setMethod(v as CorrelationMethod)
                        }
                        disabled={isSubmitting}
                      >
                        <SelectItem value={CorrelationMethod.pearson}>
                          {t("CorrelationMatrix.Method_pearson")}
                        </SelectItem>
                        <SelectItem value={CorrelationMethod.spearman}>
                          {t("CorrelationMatrix.Method_spearman")}
                        </SelectItem>
                        <SelectItem value={CorrelationMethod.kendall}>
                          {t("CorrelationMatrix.Method_kendall")}
                        </SelectItem>
                      </Select>
                    </FormField>

                    {/* 丸め桁数 */}
                    <FormField
                      label={t("CorrelationMatrix.DecimalPlacesLabel")}
                      htmlFor="decimal-places"
                    >
                      <InputText
                        id="decimal-places"
                        type="number"
                        value={decimalPlaces.toString()}
                        onChange={(e) => {
                          const v = Math.min(
                            15,
                            Math.max(1, parseInt(e.target.value) || 1),
                          );
                          setDecimalPlaces(v);
                        }}
                        disabled={isSubmitting}
                      />
                    </FormField>

                    {/* 下三角のみ */}
                    <FormField
                      label={t("CorrelationMatrix.LowerTriangleOnly")}
                      htmlFor="lower-triangle"
                    >
                      <Select
                        id="lower-triangle"
                        value={lowerTriangleOnly ? "true" : "false"}
                        onValueChange={(v) =>
                          setLowerTriangleOnly(v === "true")
                        }
                        disabled={isSubmitting}
                      >
                        <SelectItem value="false">
                          {t("CorrelationMatrix.LowerTriangle_false")}
                        </SelectItem>
                        <SelectItem value="true">
                          {t("CorrelationMatrix.LowerTriangle_true")}
                        </SelectItem>
                      </Select>
                    </FormField>

                    {/* 欠損値処理 */}
                    <FormField
                      label={t("CorrelationMatrix.MissingHandlingLabel")}
                      htmlFor="missing-handling"
                    >
                      <Select
                        id="missing-handling"
                        value={missingHandling}
                        onValueChange={(v) =>
                          setMissingHandling(v as MissingHandlingMethod)
                        }
                        disabled={isSubmitting}
                      >
                        <SelectItem value={MissingHandlingMethod.pairwise}>
                          {t("CorrelationMatrix.Missing_pairwise")}
                        </SelectItem>
                        <SelectItem value={MissingHandlingMethod.listwise}>
                          {t("CorrelationMatrix.Missing_listwise")}
                        </SelectItem>
                      </Select>
                    </FormField>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* ── BOTTOM: アクションバー ── */}
        <ActionButtonBar
          cancelText={t("Common.Cancel")}
          selectText={
            isSubmitting
              ? t("CorrelationMatrix.Processing")
              : t("CorrelationMatrix.RunCalculation")
          }
          onCancel={() => setCurrentView("DataPreview")}
          onSelect={handleSubmit}
          disabled={isSubmitting}
        />
      </div>
    </PageLayout>
  );
};
