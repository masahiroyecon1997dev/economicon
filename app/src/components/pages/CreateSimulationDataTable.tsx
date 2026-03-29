import { useForm, useStore } from "@tanstack/react-form";
import { AlertCircle, Dices, Edit2, Hash, Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { z } from "zod";
import { getEconomiconAppAPI } from "../../api/endpoints";
import type { SimulationColumnConfig } from "../../api/model";
import { DISTRIBUTION_OPTIONS } from "../../constants/app";
import { showMessageDialog } from "../../lib/dialog/message";
import { extractFieldError } from "../../lib/utils/formHelpers";
import { cn } from "../../lib/utils/helpers";
import { getTableInfo } from "../../lib/utils/internal";
import { validateDistributionParam } from "../../lib/utils/validation";
import { useCurrentPageStore } from "../../stores/currentView";
import { useTableInfosStore } from "../../stores/tableInfos";
import { useTableListStore } from "../../stores/tableList";
import type {
  DistributionType,
  SimulationColumnSetting,
} from "../../types/commonTypes";
import { Button } from "../atoms/Button/Button";
import { InputText } from "../atoms/Input/InputText";
import { ActionButtonBar } from "../molecules/ActionBar/ActionButtonBar";
import { FormField } from "../molecules/Form/FormField";
import { RandomSeedField } from "../molecules/Form/RandomSeedField";
import { SimulationColumnEditDialog } from "../organisms/Dialog/SimulationColumnEditDialog";
import { PageLayout } from "../templates/PageLayout";

const createSimulationSchema = (t: (key: string) => string) =>
  z.object({
    tableName: z.string().min(1, t("ValidationMessages.DataNameRequired")),
    numRows: z.number().min(1, t("ValidationMessages.NumRowsMoreThan0")),
    randomSeed: z
      .string()
      .refine(
        (v) =>
          v === "" ||
          (!isNaN(Number(v)) &&
            Number.isInteger(Number(v)) &&
            Number(v) >= 0 &&
            Number(v) <= 100_000_000),
        t("ValidationMessages.RandomSeedRange"),
      ),
  });

// コンポーネント外に定義してレンダリングごとの再生成を防ぐ
const COLUMN_SETTINGS_DEFAULT: SimulationColumnSetting = {
  id: "1",
  columnName: "",
  dataType: "distribution",
  distributionType: "uniform",
  distributionParams: { low: 0, high: 10 },
  fixedValue: "",
  errorMessage: {
    columnName: undefined,
    distributionParams: undefined,
    fixedValue: undefined,
  },
};

const hasColumnError = (col: SimulationColumnSetting): boolean =>
  !!(
    col.errorMessage.columnName ||
    col.errorMessage.distributionParams ||
    col.errorMessage.fixedValue
  );

export const CreateSimulationDataTable = () => {
  const { t } = useTranslation();
  const setCurrentView = useCurrentPageStore((state) => state.setCurrentView);
  const addTableName = useTableListStore((state) => state.addTableName);
  const addTableInfo = useTableInfosStore((state) => state.addTableInfo);

  const [columns, setColumns] = useState<SimulationColumnSetting[]>([
    { ...COLUMN_SETTINGS_DEFAULT, id: "1" },
  ]);

  const [editingColumnId, setEditingColumnId] = useState<string | null>(null);

  const form = useForm({
    defaultValues: {
      tableName: "",
      numRows: 1000,
      randomSeed: "",
    },
    validators: {
      onSubmit: createSimulationSchema(t),
    },
    onSubmit: async ({ value }) => {
      const tableName = value.tableName;
      const numRows = value.numRows;

      // カラムのバリデーション
      let hasError = false;
      const validatedColumns = columns.map((col) => {
        const errors: {
          columnName: string | undefined;
          distributionParams: Record<string, string | undefined> | undefined;
          fixedValue: string | undefined;
        } = {
          columnName: undefined,
          distributionParams: undefined,
          fixedValue: undefined,
        };

        if (!col.columnName || col.columnName.trim() === "") {
          errors.columnName = t("ValidationMessages.ColumnNameRequired");
          hasError = true;
        }

        if (col.dataType === "distribution") {
          const paramsError = validateDistributionParam(
            col.distributionType,
            col.distributionParams,
          );
          if (paramsError !== undefined) {
            const translatedErrors: Record<string, string | undefined> = {};
            for (const [k, v] of Object.entries(paramsError)) {
              translatedErrors[k] = v ? t(v) : undefined;
            }
            errors.distributionParams = translatedErrors;
            hasError = true;
          }
        }
        return { ...col, errorMessage: errors };
      });

      if (hasError) {
        setColumns(validatedColumns);
        await showMessageDialog(
          t("Error.Error"),
          t("ValidationMessages.FixValidationErrors"),
        );
        return;
      }

      try {
        // SimulationColumnConfig型（種別 union）にマッピング
        const simulationColumns: SimulationColumnConfig[] = columns.map(
          (col) => {
            if (col.dataType === "fixed") {
              return {
                columnName: col.columnName.trim(),
                distribution: {
                  type: "fixed" as const,
                  value: Number(col.fixedValue),
                },
              };
            }
            // 注意: distributionType を type フィールドにマッピング
            const p = col.distributionParams;
            switch (col.distributionType) {
              case "uniform":
                return {
                  columnName: col.columnName.trim(),
                  distribution: {
                    type: "uniform" as const,
                    low: p.low,
                    high: p.high,
                  },
                };
              case "exponential":
                return {
                  columnName: col.columnName.trim(),
                  distribution: { type: "exponential" as const, scale: p.rate },
                };
              case "normal":
                return {
                  columnName: col.columnName.trim(),
                  distribution: {
                    type: "normal" as const,
                    loc: p.mean,
                    scale: p.deviation,
                  },
                };
              case "gamma":
                return {
                  columnName: col.columnName.trim(),
                  distribution: {
                    type: "gamma" as const,
                    shape: p.shape,
                    scale: p.scale,
                  },
                };
              case "beta":
                return {
                  columnName: col.columnName.trim(),
                  distribution: {
                    type: "beta" as const,
                    a: p.alpha,
                    b: p.beta,
                  },
                };
              case "weibull":
                return {
                  columnName: col.columnName.trim(),
                  distribution: {
                    type: "weibull" as const,
                    a: p.shape,
                    scale: p.scale,
                  },
                };
              case "lognormal":
                return {
                  columnName: col.columnName.trim(),
                  distribution: {
                    type: "lognormal" as const,
                    mean: p.logMean,
                    sigma: p.logSD,
                  },
                };
              case "binomial":
                return {
                  columnName: col.columnName.trim(),
                  distribution: {
                    type: "binomial" as const,
                    n: p.trials,
                    p: p.probability,
                  },
                };
              case "bernoulli":
                return {
                  columnName: col.columnName.trim(),
                  distribution: {
                    type: "bernoulli" as const,
                    p: p.probability,
                  },
                };
              case "poisson":
                return {
                  columnName: col.columnName.trim(),
                  distribution: { type: "poisson" as const, lam: p.lambda },
                };
              case "geometric":
                return {
                  columnName: col.columnName.trim(),
                  distribution: {
                    type: "geometric" as const,
                    p: p.probability,
                  },
                };
              case "hypergeometric":
                return {
                  columnName: col.columnName.trim(),
                  distribution: {
                    type: "hypergeometric" as const,
                    populationSize: p.populationSize,
                    successCount: p.numberOfSuccesses,
                    sampleSize: p.sampleSize,
                  },
                };
              default:
                return {
                  columnName: col.columnName.trim(),
                  distribution: { type: "uniform" as const, low: 0, high: 1 },
                };
            }
          },
        );

        const randomSeed =
          value.randomSeed !== "" ? Number(value.randomSeed) : null;

        const response = await getEconomiconAppAPI().createSimulationDataTable({
          tableName: tableName.trim(),
          rowCount: numRows,
          simulationColumns,
          randomSeed,
        });

        if (response.code === "OK") {
          const resTableInfo = await getTableInfo(response.result.tableName);
          addTableName(response.result.tableName);
          addTableInfo(resTableInfo);
          setCurrentView("DataPreview");
        } else {
          await showMessageDialog(
            t("Error.Error"),
            t("CreateSimulationDataTableView.DataCreationFailed"),
          );
        }
      } catch (error) {
        let errorMessage = t("CreateSimulationDataTableView.DataCreationError");
        if (error instanceof Error) {
          errorMessage = error.message;
        }
        await showMessageDialog(t("Error.Error"), errorMessage);
      }
    },
  });

  const isSubmitting = useStore(form.store, (s) => s.isSubmitting);

  const addColumn = () => {
    const newColumn: SimulationColumnSetting = {
      ...COLUMN_SETTINGS_DEFAULT,
      id: Date.now().toString(),
    };
    setColumns([...columns, newColumn]);
  };

  const removeColumn = (id: string) => {
    setColumns(columns.filter((col) => col.id !== id));
  };

  const updateColumn = (
    id: string,
    updates: Partial<SimulationColumnSetting>,
  ) => {
    setColumns(
      columns.map((col) => (col.id === id ? { ...col, ...updates } : col)),
    );
  };

  const handleDataTypeChange = (
    id: string,
    dataType: "distribution" | "fixed",
  ) => {
    const updates: Partial<SimulationColumnSetting> = {
      dataType: dataType,
    };

    if (dataType === "distribution") {
      updates.distributionType = "uniform";
      updates.distributionParams = { low: 0, high: 10 };
      delete updates.fixedValue;
    } else {
      updates.fixedValue = "";
      delete updates.distributionType;
      delete updates.distributionParams;
    }

    updateColumn(id, updates);
  };

  const handleDistributionTypeChange = (
    id: string,
    distributionType: DistributionType,
  ) => {
    const distOption = DISTRIBUTION_OPTIONS.find(
      (d) => d.value === distributionType,
    );
    if (!distOption) return;

    const defaultParams: Record<string, number> = {};
    distOption.params.forEach((param) => {
      switch (param) {
        case "low":
          defaultParams[param] = 0;
          break;
        case "high":
          defaultParams[param] = 10;
          break;
        case "mean":
          defaultParams[param] = 0;
          break;
        case "deviation":
          defaultParams[param] = 1;
          break;
        case "rate":
          defaultParams[param] = 1;
          break;
        case "scale":
          defaultParams[param] = 1;
          break;
        case "alpha":
          defaultParams[param] = 2;
          break;
        case "beta":
          defaultParams[param] = 2;
          break;
        case "logMean":
          defaultParams[param] = 0;
          break;
        case "logSD":
          defaultParams[param] = 1;
          break;
        case "trials":
          defaultParams[param] = 10;
          break;
        case "probability":
          defaultParams[param] = 0.5;
          break;
        case "populationSize":
          defaultParams[param] = 20;
          break;
        case "numberOfSuccesses":
          defaultParams[param] = 5;
          break;
        case "sampleSize":
          defaultParams[param] = 10;
          break;
        default:
          defaultParams[param] = 1;
      }
    });

    updateColumn(id, {
      distributionType: distributionType,
      distributionParams: defaultParams,
    });
  };

  const handleDistributionParamChange = (
    id: string,
    param: string,
    value: number,
  ) => {
    const column = columns.find((col) => col.id === id);
    if (!column?.distributionParams) return;

    updateColumn(id, {
      distributionParams: {
        ...column.distributionParams,
        [param]: value,
      },
    });
  };

  const handleCancel = () => {
    setCurrentView("ImportDataFile");
  };

  return (
    <PageLayout
      title={t("CreateSimulationDataTableView.CreateNewDataTable")}
      description={t(
        "CreateSimulationDataTableView.DefineYourTableNameAndRows",
      )}
    >
      <form
        onSubmit={(e) => {
          e.preventDefault();
          e.stopPropagation();
          void form.handleSubmit();
        }}
        className="flex flex-col h-full min-h-0 gap-4"
      >
        {/* ── スクロール領域 ── */}
        <div className="flex flex-col gap-4 overflow-y-auto min-h-0 pb-2">
          {/* テーブル設定 */}
          <div className="rounded-xl border border-border-color dark:border-gray-700 bg-white dark:bg-gray-800/50 p-4 shadow-sm">
            <h2 className="mb-3 text-sm font-bold leading-tight text-text-heading dark:text-white">
              {t("CreateSimulationDataTableView.DataSettings")}
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <form.Field name="randomSeed">
                {(field) => {
                  const errorMsg = field.state.meta.isTouched
                    ? extractFieldError(field.state.meta.errors)
                    : undefined;
                  return (
                    <RandomSeedField
                      id="sim-table-random-seed"
                      value={field.state.value}
                      onChange={field.handleChange}
                      onBlur={field.handleBlur}
                      disabled={isSubmitting}
                      error={errorMsg}
                    />
                  );
                }}
              </form.Field>

              <form.Field
                name="tableName"
                validators={{
                  onChange: ({ value }) =>
                    !value.trim()
                      ? t("ValidationMessages.DataNameRequired")
                      : undefined,
                }}
              >
                {(field) => {
                  const errorMsg = field.state.meta.isTouched
                    ? extractFieldError(field.state.meta.errors)
                    : undefined;
                  return (
                    <FormField
                      label={t("CreateSimulationDataTableView.DataName")}
                      htmlFor="table-name"
                      error={errorMsg}
                    >
                      <InputText
                        id="table-name"
                        value={field.state.value}
                        onChange={(e) => field.handleChange(e.target.value)}
                        onBlur={field.handleBlur}
                        placeholder={t(
                          "CreateSimulationDataTableView.DataNamePlaceholder",
                        )}
                        error={errorMsg}
                        disabled={isSubmitting}
                      />
                    </FormField>
                  );
                }}
              </form.Field>

              <form.Field
                name="numRows"
                validators={{
                  onChange: ({ value }) =>
                    value < 1
                      ? t("ValidationMessages.NumRowsMoreThan0")
                      : undefined,
                }}
              >
                {(field) => {
                  const errorMsg = field.state.meta.isTouched
                    ? extractFieldError(field.state.meta.errors)
                    : undefined;
                  return (
                    <FormField
                      label={t("CreateSimulationDataTableView.NumberOfRows")}
                      htmlFor="row-count"
                      error={errorMsg}
                    >
                      <InputText
                        id="row-count"
                        type="number"
                        value={field.state.value.toString()}
                        onChange={(e) =>
                          field.handleChange(parseInt(e.target.value) || 0)
                        }
                        onBlur={field.handleBlur}
                        placeholder="1000"
                        error={errorMsg}
                        disabled={isSubmitting}
                      />
                    </FormField>
                  );
                }}
              </form.Field>
            </div>
          </div>

          {/* 列設定 */}
          <div className="rounded-xl border border-border-color dark:border-gray-700 bg-white dark:bg-gray-800/50 p-4 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-bold leading-tight text-text-heading dark:text-white">
                {t("CreateSimulationDataTableView.ColumnSettings")}
              </h2>
              <Button
                type="button"
                variant="outline"
                onClick={addColumn}
                disabled={isSubmitting}
                className="flex items-center gap-1.5 whitespace-nowrap"
              >
                <Plus className="h-3.5 w-3.5" />
                {t("CreateSimulationDataTableView.AddColumn")}
              </Button>
            </div>

            {/* 全列エラー時のサマリー */}
            {columns.some(hasColumnError) && (
              <div className="mb-3 flex items-center gap-1.5 rounded-md bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 px-3 py-2">
                <AlertCircle className="h-4 w-4 shrink-0 text-red-500" />
                <p className="text-xs text-red-600 dark:text-red-400">
                  {t("CreateSimulationDataTableView.ColumnHasErrors")}
                </p>
              </div>
            )}

            <div className="flex flex-col gap-2">
              {columns.map((column) => {
                const colHasError = hasColumnError(column);
                const distOption =
                  column.dataType === "distribution"
                    ? DISTRIBUTION_OPTIONS.find(
                        (d) => d.value === column.distributionType,
                      )
                    : null;

                return (
                  <div
                    key={column.id}
                    className={cn(
                      "flex items-start gap-3 rounded-lg border px-4 py-3 transition-colors",
                      colHasError
                        ? "border-red-300 bg-red-50/40 dark:border-red-700 dark:bg-red-950/20"
                        : "border-gray-200 dark:border-gray-700",
                    )}
                  >
                    {/* アイコン */}
                    <div
                      className={cn(
                        "mt-0.5 rounded-md p-1.5 shrink-0",
                        column.dataType === "fixed"
                          ? "bg-amber-50 dark:bg-amber-900/30 text-amber-500"
                          : "bg-indigo-50 dark:bg-indigo-900/30 text-indigo-500",
                      )}
                    >
                      {column.dataType === "fixed" ? (
                        <Hash className="h-3.5 w-3.5" />
                      ) : (
                        <Dices className="h-3.5 w-3.5" />
                      )}
                    </div>

                    {/* コンテンツ */}
                    <div className="flex-1 min-w-0">
                      <div className="flex flex-wrap items-center gap-1.5">
                        <span
                          className={cn(
                            "text-sm font-medium",
                            column.columnName
                              ? "text-gray-900 dark:text-gray-100"
                              : "text-gray-400 dark:text-gray-500 italic",
                          )}
                        >
                          {column.columnName ||
                            t("CreateSimulationDataTableView.NotSet")}
                        </span>

                        {/* 分布 / 固定値バッジ */}
                        {distOption && (
                          <span className="rounded-full bg-indigo-50 dark:bg-indigo-900/30 px-2 py-0.5 text-xs font-medium text-indigo-600 dark:text-indigo-400">
                            {t(distOption.label)}
                          </span>
                        )}
                        {column.dataType === "fixed" && (
                          <span className="rounded-full bg-amber-50 dark:bg-amber-900/30 px-2 py-0.5 text-xs font-medium text-amber-600 dark:text-amber-400">
                            {t("Common.Constant")}
                          </span>
                        )}

                        {/* エラーバッジ */}
                        {colHasError && (
                          <span className="flex items-center gap-0.5 text-xs font-medium text-red-600 dark:text-red-400">
                            <AlertCircle className="h-3.5 w-3.5 shrink-0" />
                            {t("CreateSimulationDataTableView.HasErrors")}
                          </span>
                        )}
                      </div>

                      {/* パラメータ概要 */}
                      <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400 truncate">
                        {column.dataType === "fixed"
                          ? `${t("Common.Constant")} = ${column.fixedValue || "-"}`
                          : distOption
                            ? distOption.params
                                .map(
                                  (p) =>
                                    `${p} = ${column.distributionParams?.[p] ?? "?"}`,
                                )
                                .join("  /  ")
                            : "-"}
                      </p>

                      {/* columnName エラーをインライン表示 */}
                      {column.errorMessage.columnName && (
                        <p className="mt-1 text-xs text-red-600 dark:text-red-400">
                          {column.errorMessage.columnName}
                        </p>
                      )}
                    </div>

                    {/* アクションボタン */}
                    <div className="flex items-center gap-0.5 shrink-0">
                      <button
                        type="button"
                        onClick={() => setEditingColumnId(column.id)}
                        className="rounded p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-gray-700 dark:hover:text-gray-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        disabled={isSubmitting}
                        aria-label={t("Common.Edit")}
                      >
                        <Edit2 className="h-3.5 w-3.5" />
                      </button>
                      <button
                        type="button"
                        onClick={() => removeColumn(column.id)}
                        className="rounded p-1.5 text-gray-400 hover:bg-red-50 hover:text-red-500 dark:hover:bg-red-950/30 dark:hover:text-red-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        disabled={isSubmitting || columns.length <= 1}
                        aria-label={t("Common.Delete")}
                        title={
                          columns.length <= 1
                            ? t(
                                "CreateSimulationDataTableView.CannotRemoveLastColumn",
                              )
                            : undefined
                        }
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* ── アクションバー（常に最下部固定）── */}
        <ActionButtonBar
          cancelText={t("Common.Cancel")}
          selectText={
            isSubmitting
              ? t("CreateSimulationDataTableView.CreatingTable")
              : t("CreateSimulationDataTableView.Submit")
          }
          onCancel={handleCancel}
          onSelect={() => {}}
          onSelectType="submit"
        />
      </form>

      {editingColumnId && (
        <SimulationColumnEditDialog
          key={editingColumnId}
          isOpen={!!editingColumnId}
          column={columns.find((col) => col.id === editingColumnId)!}
          index={columns.findIndex((col) => col.id === editingColumnId)}
          distributionOptions={DISTRIBUTION_OPTIONS}
          onUpdate={updateColumn}
          onDataTypeChange={handleDataTypeChange}
          onDistributionTypeChange={handleDistributionTypeChange}
          onDistributionParamChange={handleDistributionParamChange}
          onRemove={(id) => {
            removeColumn(id);
            setEditingColumnId(null);
          }}
          onClose={() => setEditingColumnId(null)}
          canRemove={columns.length > 1}
          error={
            columns.find((col) => col.id === editingColumnId)?.errorMessage || {
              columnName: undefined,
              distributionParams: undefined,
              fixedValue: undefined,
            }
          }
          disabled={isSubmitting}
        />
      )}
    </PageLayout>
  );
};
