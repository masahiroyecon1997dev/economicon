import { useForm, useStore } from "@tanstack/react-form";
import { Edit2, Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { z } from "zod";
import { getEconomiconAPI } from "../../api/endpoints";
import type { SimulationColumnConfig } from "../../api/model";
import { DISTRIBUTION_OPTIONS } from "../../constants/app";
import { showMessageDialog } from "../../lib/dialog/message";
import { getTableInfo } from "../../lib/utils/internal";
import { validateDistributionParam } from "../../lib/utils/validation";
import { useCurrentPageStore } from "../../stores/currentView";
import { useTableInfosStore } from "../../stores/tableInfos";
import { useTableListStore } from "../../stores/tableList";
import type {
  DistributionType,
  SimulationColumnSetting,
} from "../../types/commonTypes";
import { InputText } from "../atoms/Input/InputText";
import { ActionButtonBar } from "../molecules/ActionBar/ActionButtonBar";
import { FormField } from "../molecules/Form/FormField";
import { SimulationColumnEditDialog } from "../organisms/Dialog/SimulationColumnEditDialog";
import { PageLayout } from "../templates/PageLayout";

const createSimulationSchema = (t: (key: string) => string) =>
  z.object({
    tableName: z.string().min(1, t("ValidationMessages.TableNameRequired")),
    numRows: z.number().min(1, t("ValidationMessages.NumRowsMoreThan0")),
  });

export const CreateSimulationDataTable = () => {
  const { t } = useTranslation();
  const setCurrentView = useCurrentPageStore((state) => state.setCurrentView);
  const addTableName = useTableListStore((state) => state.addTableName);
  const addTableInfo = useTableInfosStore((state) => state.addTableInfo);

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

  const [columns, setColumns] = useState<SimulationColumnSetting[]>([
    COLUMN_SETTINGS_DEFAULT,
  ]);

  const [editingColumnId, setEditingColumnId] = useState<string | null>(null);

  const form = useForm({
    defaultValues: {
      tableName: "",
      numRows: 1000,
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
        // SimulationColumnConfig型（分布判別union）にマッピング
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
            // 分布型: distributionTypeが typeフィールドになる
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
                    bigN: p.populationSize,
                    n: p.sampleSize,
                    bigK: p.numberOfSuccesses,
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

        const response = await getEconomiconAPI().createSimulationDataTable({
          tableName: tableName.trim(),
          rowCount: numRows,
          simulationColumns,
        });

        if (response.code === "OK") {
          const resTableInfo = await getTableInfo(response.result.tableName);
          addTableName(response.result.tableName);
          addTableInfo(resTableInfo);
          setCurrentView("DataPreview");
        } else {
          await showMessageDialog(
            t("Error.Error"),
            t("CreateSimulationDataTableView.TableCreationFailed"),
          );
        }
      } catch (error) {
        let errorMessage = t(
          "CreateSimulationDataTableView.TableCreationError",
        );
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

  const getColumnSummary = (column: SimulationColumnSetting): string => {
    if (column.dataType === "fixed") {
      return `${column.columnName || t("CreateSimulationDataTableView.NotSet")} - ${t("Common.Constant")}: ${column.fixedValue || t("CreateSimulationDataTableView.NotSet")}`;
    }

    const distOption = DISTRIBUTION_OPTIONS.find(
      (d) => d.value === column.distributionType,
    );
    if (!distOption) {
      return `${column.columnName || t("CreateSimulationDataTableView.NotSet")} - ${t("Common.Distribution")}`;
    }

    const paramsStr = distOption.params
      .map((param) => `${param}=${column.distributionParams?.[param] ?? "?"}`)
      .join(", ");

    return `${column.columnName || t("CreateSimulationDataTableView.NotSet")} - ${t(distOption.label)} (${paramsStr})`;
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
        className="space-y-6"
      >
        <div className="bg-white dark:bg-gray-800/50 p-4 rounded-lg border border-border-color dark:border-gray-700">
          <h2 className="text-main dark:text-white text-base font-bold leading-tight mb-4">
            {t("CreateSimulationDataTableView.TableSettings")}
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <form.Field name="tableName">
              {(field) => (
                <FormField
                  label={t("CreateSimulationDataTableView.TableName")}
                  htmlFor="table-name"
                  error={field.state.meta.errors[0]?.toString()}
                >
                  <InputText
                    id="table-name"
                    value={field.state.value}
                    onChange={(e) => field.handleChange(e.target.value)}
                    onBlur={field.handleBlur}
                    placeholder={t(
                      "CreateSimulationDataTableView.TableNamePlaceholder",
                    )}
                    error={field.state.meta.errors[0]?.toString()}
                    disabled={isSubmitting}
                  />
                </FormField>
              )}
            </form.Field>

            <form.Field name="numRows">
              {(field) => (
                <FormField
                  label={t("CreateSimulationDataTableView.NumberOfRows")}
                  htmlFor="row-count"
                  error={field.state.meta.errors[0]?.toString()}
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
                    error={field.state.meta.errors[0]?.toString()}
                    disabled={isSubmitting}
                  />
                </FormField>
              )}
            </form.Field>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800/50 p-4 rounded-lg border border-border-color dark:border-gray-700">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-main dark:text-white text-base font-bold leading-tight">
              {t("CreateSimulationDataTableView.ColumnSettings")}
            </h2>
            <button
              type="button"
              onClick={addColumn}
              className="flex items-center gap-2 rounded-md bg-brand-primary text-white px-3 py-1.5 text-sm font-medium hover:bg-brand-primary-light focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand-primary cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={isSubmitting}
            >
              <Plus size={16} />
              {t("CreateSimulationDataTableView.AddColumn")}
            </button>
          </div>
          <div className="space-y-0 max-h-48 overflow-y-auto">
            {columns.map((column, index) => (
              <div
                key={index}
                className="flex items-center justify-between py-2 px-3 border-t border-gray-300 dark:border-gray-600 first:border-t-0"
              >
                <span className="text-sm text-gray-700 dark:text-gray-300 flex-1 mr-4">
                  {getColumnSummary(column)}
                </span>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setEditingColumnId(column.id)}
                    className="flex items-center gap-1 text-blue-500 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                    disabled={isSubmitting}
                    aria-label={t("Common.Edit")}
                  >
                    <Edit2 size={16} />
                    {t("Common.Edit")}
                  </button>
                  {columns.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeColumn(column.id)}
                      className="text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 disabled:opacity-50 disabled:cursor-not-allowed"
                      disabled={isSubmitting}
                      aria-label={t("Common.Delete")}
                    >
                      <Trash2 size={18} />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
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
