import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { z } from "zod";
import type { ColumnType } from "../../../types/commonTypes";
import { Select, SelectItem } from "../../atoms/Input/Select";
import { ActionButtonBar } from "../../molecules/ActionBar/ActionButtonBar";
import { VariableSelectorField } from "../../molecules/Field/VariableSelectorField";
import { FormField } from "../../molecules/Form/FormField";

const createRegressionSchema = (t: (key: string) => string) =>
  z.object({
    tableName: z.string().min(1, t("LinearRegressionForm.Validation.TableNameRequired")),
    dependentVariable: z.string().min(1, t("LinearRegressionForm.Validation.DependentVariableRequired")),
    explanatoryVariables: z
      .array(z.string())
      .min(1, t("LinearRegressionForm.Validation.ExplanatoryVariablesRequired")),
  });

type RegressionFormData = z.infer<ReturnType<typeof createRegressionSchema>>;

type LinearRegressionFormProps = {
  tableList: string[];
  selectedTableName: string;
  columns: ColumnType[];
  onTableChange: (tableName: string) => void;
  onSubmit: (data: RegressionFormData) => void;
  onCancel: () => void;
  isPending?: boolean;
};

export const LinearRegressionForm = ({
  tableList,
  selectedTableName,
  columns,
  onTableChange,
  onSubmit,
  onCancel,
  isPending = false,
}: LinearRegressionFormProps) => {
  const { t } = useTranslation();

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<RegressionFormData>({
    resolver: zodResolver(createRegressionSchema(t)),
    defaultValues: {
      tableName: selectedTableName,
      dependentVariable: "",
      explanatoryVariables: [],
    },
  });

  const [dependentVariable, setDependentVariable] = useState("");
  const [explanatoryVariables, setExplanatoryVariables] = useState<string[]>([]);

  const handleDependentChange = (value: string) => {
    setDependentVariable(value);
    setValue("dependentVariable", value, { shouldValidate: true });
  };

  const handleExplanatoryChange = (values: string[]) => {
    setExplanatoryVariables(values);
    setValue("explanatoryVariables", values, { shouldValidate: true });
  };

  const handleTableSelect = (value: string) => {
    setDependentVariable("");
    setExplanatoryVariables([]);
    setValue("tableName", value, { shouldValidate: true });
    setValue("dependentVariable", "");
    setValue("explanatoryVariables", []);
    onTableChange(value);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
      {/* テーブル選択セクション */}
      <div className="rounded-xl border border-border-color bg-white p-3 shadow-sm">
        <h2 className="mb-2 text-sm font-bold leading-tight text-text-heading">
          {t("LinearRegressionForm.SelectDataTable")}
        </h2>
        <FormField label={t("LinearRegressionForm.DataTable")} htmlFor="data-table">
          <Select
            id="data-table"
            {...register("tableName")}
            value={selectedTableName}
            onValueChange={handleTableSelect}
            disabled={isPending}
            error={errors.tableName?.message}
            placeholder={t("LinearRegressionForm.SelectATable")}
          >
            {tableList.map((table, index) => (
              <SelectItem key={index} value={table}>
                {table}
              </SelectItem>
            ))}
          </Select>
        </FormField>
      </div>

      {/* 変数選択セクション */}
      <div className="rounded-xl border border-border-color bg-white p-3 shadow-sm">
        <h2 className="mb-2 text-sm font-bold leading-tight text-text-heading">
          {t("LinearRegressionForm.SelectVariables")}
        </h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <VariableSelectorField
            label={t("LinearRegressionForm.DependentVariable")}
            description={t("LinearRegressionForm.DependentVariableDescription")}
            mode="single"
            columns={columns}
            selectedValue={dependentVariable}
            onSingleChange={handleDependentChange}
            error={errors.dependentVariable?.message}
            disabled={isPending}
            name="dependentVariable"
          />
          <VariableSelectorField
            label={t("LinearRegressionForm.ExplanatoryVariables")}
            description={t("LinearRegressionForm.ExplanatoryVariablesDescription")}
            mode="multiple"
            columns={columns}
            selectedValues={explanatoryVariables}
            onMultipleChange={handleExplanatoryChange}
            error={errors.explanatoryVariables?.message}
            disabled={isPending}
            name="explanatoryVariables"
          />
        </div>
        <div className="mt-4">
          <label className="mb-1.5 block text-xs font-medium text-text-main">
            {t("LinearRegressionForm.SelectedExplanatoryVariables")}
          </label>
          <div className="flex min-h-11 flex-wrap gap-2 rounded-lg border border-border-color bg-secondary p-2">
            {explanatoryVariables.length === 0 ? (
              <span className="text-xs text-text-main/60">
                {t("LinearRegressionForm.NoVariablesSelected")}
              </span>
            ) : (
              explanatoryVariables.map((variable, index) => (
                <span
                  key={index}
                  className="inline-flex items-center rounded-md bg-accent px-2 py-1 text-xs text-white"
                >
                  {variable}
                </span>
              ))
            )}
          </div>
        </div>
      </div>

      <ActionButtonBar
        cancelText={t("Common.Cancel")}
        selectText={
          isPending
            ? t("LinearRegressionForm.Processing")
            : t("LinearRegressionForm.RunAnalysis")
        }
        onCancel={onCancel}
        onSelect={() => { }}
      />
    </form>
  );
};
