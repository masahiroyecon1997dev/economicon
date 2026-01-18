import { zodResolver } from "@hookform/resolvers/zod";
import axios from "axios";
import { startTransition, useActionState, useState } from "react";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { z } from "zod";
import { showMessageDialog } from "../../../functions/messageDialog";
import { linearRegression } from "../../../functions/restApis";
import { useTableColumnLoader } from "../../../hooks/useTableColumnLoader";
import { useRegressionResultsStore } from "../../../stores/useRegressionResultsStore";
import { useTableListStore } from "../../../stores/useTableListStore";
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
  onCancel: () => void;
  onAnalysisComplete?: (resultIndex: number) => void;
};

export const LinearRegressionForm = ({
  onCancel,
  onAnalysisComplete,
}: LinearRegressionFormProps) => {
  const { t } = useTranslation();
  const tableList = useTableListStore((state) => state.tableList);
  const { selectedTableName, setSelectedTableName, columnList, setColumnList } =
    useTableColumnLoader({
      numericOnly: false,
      autoLoadOnMount: true,
    });
  const addResult = useRegressionResultsStore((state) => state.addResult);
  const resultsCount = useRegressionResultsStore((state) => state.results.length);

  const handleTableChange = async (value: string) => {
    setSelectedTableName(value);
    if (!value) {
      setColumnList([]);
    }
  };

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

  type ActionState = {
    success: boolean;
  };

  const handleRegressionAction = async (
    _prevState: ActionState,
    formData: FormData
  ): Promise<ActionState> => {
    const tableName = formData.get("tableName") as string;
    const dependentVariable = formData.get("dependentVariable") as string;
    const explanatoryVariablesStr = formData.get("explanatoryVariables") as string;
    const explanatoryVariables = explanatoryVariablesStr
      ? explanatoryVariablesStr.split(",")
      : [];

    try {
      const response = await linearRegression({
        tableName,
        dependentVariable,
        explanatoryVariables,
      });

      if (response.code === "OK" && response.result) {
        addResult(response.result);
        const newResultIndex = resultsCount;
        onAnalysisComplete?.(newResultIndex);
        return { success: true };
      } else {
        await showMessageDialog(
          t("Error.Error"),
          response.message || t("Error.UnexpectedError")
        );
        return { success: false };
      }
    } catch (error) {
      let errorMessage = t("Error.UnexpectedError");
      if (axios.isAxiosError(error)) {
        const serverMessage = error.response?.data?.message;
        if (serverMessage) {
          errorMessage = serverMessage;
        }
      }
      await showMessageDialog(t("Error.Error"), errorMessage);
      return { success: false };
    }
  };

  const [, submitAction, isPending] = useActionState(handleRegressionAction, {
    success: false,
  });

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
    handleTableChange(value);
  };

  const onSubmit = (data: RegressionFormData) => {
    const formData = new FormData();
    formData.append("tableName", data.tableName);
    formData.append("dependentVariable", data.dependentVariable);
    data.explanatoryVariables.forEach(v => formData.append("explanatoryVariables", v));
    // ここで直接 action を叩く
    startTransition(() => {
      submitAction(formData);
    });
  };

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className="flex flex-col gap-4"
    >
      {/* Hidden fields for FormData */}
      <input type="hidden" name="tableName" value={selectedTableName} />
      <input type="hidden" name="dependentVariable" value={dependentVariable} />
      <input
        type="hidden"
        name="explanatoryVariables"
        value={explanatoryVariables.join(",")}
      />

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
            columns={columnList}
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
            columns={columnList}
            selectedValues={explanatoryVariables}
            onMultipleChange={handleExplanatoryChange}
            error={errors.explanatoryVariables?.message}
            disabled={isPending}
            name="explanatoryVariables"
          />
        </div>
        <div className="mt-4">
          <label className="mb-1.5 block text-xs font-medium text-brand-text-main">
            {t("LinearRegressionForm.SelectedExplanatoryVariables")}
          </label>
          <div className="flex min-h-11 flex-wrap gap-2 rounded-lg border border-border-color bg-secondary p-2">
            {explanatoryVariables.length === 0 ? (
              <span className="text-xs text-brand-text-main/60">
                {t("LinearRegressionForm.NoVariablesSelected")}
              </span>
            ) : (
              explanatoryVariables.map((variable, index) => (
                <span
                  key={index}
                  className="inline-flex items-center rounded-md bg-brand-accent px-2 py-1 text-xs text-white"
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
        onSelectType="submit"
      />
    </form>
  );
};
