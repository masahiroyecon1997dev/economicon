import { zodResolver } from "@hookform/resolvers/zod";
import { CirclePlus, Columns3, Eraser, Info } from "lucide-react";
import { startTransition, useActionState, useRef, useState } from "react";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { z } from "zod";
import { getEconomiconAPI } from "../../api/endpoints";
import { useTableColumnLoader } from "../../hooks/useTableColumnLoader";
import { showMessageDialog } from "../../lib/dialog/message";
import { useCurrentPageStore } from "../../stores/currentView";
import { useTableListStore } from "../../stores/tableList";
import { ExpressionHelperButton } from "../atoms/Button/ExpressionHelperButton";
import { InputText } from "../atoms/Input/InputText";
import { Select, SelectItem } from "../atoms/Input/Select";
import { ActionButtonBar } from "../molecules/ActionBar/ActionButtonBar";
import { FormField } from "../molecules/Form/FormField";
import { SearchInput } from "../molecules/Form/SearchInput";
import { PageLayout } from "../templates/PageLayout";

const createCalculationSchema = (t: (key: string) => string) =>
  z.object({
    tableName: z.string().min(1, t("ValidationMessages.TableNameSelect")),
    newColumnName: z
      .string()
      .min(1, t("ValidationMessages.NewColumnNameRequired")),
    calculationExpression: z
      .string()
      .min(1, t("ValidationMessages.CalculationExpressionRequired")),
  });

type CalculationFormData = z.infer<ReturnType<typeof createCalculationSchema>>;

export const Calculation = () => {
  const { t } = useTranslation();
  const tableList = useTableListStore((state) => state.tableList);
  const setCurrentView = useCurrentPageStore((state) => state.setCurrentView);

  const { selectedTableName, setSelectedTableName, columnList } =
    useTableColumnLoader({
      numericOnly: true,
      autoLoadOnMount: true,
    });

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<CalculationFormData>({
    resolver: zodResolver(createCalculationSchema(t)),
    defaultValues: {
      tableName: selectedTableName,
      newColumnName: "",
      calculationExpression: "",
    },
  });

  const newColumnName = watch("newColumnName");
  const calculationExpression = watch("calculationExpression");
  const [filterValue, setFilterValue] = useState<string>("");

  const textareaRef = useRef<HTMLTextAreaElement>(null);

  type ActionState = {
    success: boolean;
  };

  const handleCalculationAction = async (
    _prevState: ActionState,
    formData: FormData,
  ): Promise<ActionState> => {
    const tableName = formData.get("tableName") as string;
    const newColumnName = formData.get("newColumnName") as string;
    const calculationExpression = formData.get(
      "calculationExpression",
    ) as string;

    try {
      const response = await getEconomiconAPI().calculateColumn({
        tableName,
        newColumnName,
        addPositionColumn: "", // 追加位置未指定（末尾に追加）
        calculationExpression,
      });

      if (response.code === "OK") {
        await showMessageDialog(
          t("Common.OK"),
          t("CalculationView.CalculationSuccess"),
        );
        setCurrentView("DataPreview");
        return { success: true };
      } else {
        await showMessageDialog(t("Error.Error"), t("Error.UnexpectedError"));
        return { success: false };
      }
    } catch (error) {
      let errorMessage = t("Error.UnexpectedError");
      if (error instanceof Error) {
        errorMessage = error.message;
      }
      await showMessageDialog(t("Error.Error"), errorMessage);
      return { success: false };
    }
  };

  const [, submitAction, isPending] = useActionState(handleCalculationAction, {
    success: false,
  });

  const handleTableChange = (value: string) => {
    setSelectedTableName(value);
    setValue("tableName", value, { shouldValidate: true });
    setValue("newColumnName", "");
    setValue("calculationExpression", "");
  };

  const insertAtCursor = (text: string) => {
    if (textareaRef.current) {
      const start = textareaRef.current.selectionStart;
      const end = textareaRef.current.selectionEnd;
      const before = calculationExpression.substring(0, start);
      const after = calculationExpression.substring(end);
      const newText = before + text + after;
      setValue("calculationExpression", newText, { shouldValidate: true });

      setTimeout(() => {
        if (textareaRef.current) {
          const newPosition = start + text.length;
          textareaRef.current.selectionStart = newPosition;
          textareaRef.current.selectionEnd = newPosition;
          textareaRef.current.focus();
        }
      }, 0);
    }
  };

  const handleOperatorClick = (operator: string) => {
    insertAtCursor(operator);
  };

  const handleColumnClick = (columnName: string) => {
    insertAtCursor(`pl.col("${columnName}")`);
  };

  const handleClearClick = () => {
    setValue("calculationExpression", "", { shouldValidate: true });
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  };

  const handleCancel = () => {
    setCurrentView("DataPreview");
  };

  const onSubmit = (data: CalculationFormData) => {
    const formData = new FormData();
    formData.append("tableName", data.tableName);
    formData.append("newColumnName", data.newColumnName);
    formData.append("calculationExpression", data.calculationExpression);
    startTransition(() => {
      submitAction(formData);
    });
  };

  const filteredColumns = columnList.filter((column) =>
    column.name.toLowerCase().includes(filterValue.toLowerCase()),
  );

  const getTypeColor = (
    type: string,
  ): { bg: string; text: string; label: string } => {
    if (type.includes("Int") || type.includes("UInt")) {
      return {
        bg: "bg-blue-100 dark:bg-blue-900/30",
        text: "text-blue-700 dark:text-blue-300",
        label: "#",
      };
    } else if (type.includes("Float")) {
      return {
        bg: "bg-green-100 dark:bg-green-900/30",
        text: "text-green-700 dark:text-green-300",
        label: "1.2",
      };
    } else if (type.includes("Utf8") || type.includes("String")) {
      return {
        bg: "bg-purple-100 dark:bg-purple-900/30",
        text: "text-purple-700 dark:text-purple-300",
        label: "ABC",
      };
    } else if (type.includes("Date") || type.includes("Datetime")) {
      return {
        bg: "bg-orange-100 dark:bg-orange-900/30",
        text: "text-orange-700 dark:text-orange-300",
        label: "DATE",
      };
    } else {
      return {
        bg: "bg-gray-100 dark:bg-gray-900/30",
        text: "text-gray-700 dark:text-gray-300",
        label: "?",
      };
    }
  };

  return (
    <PageLayout
      title={t("CalculationView.Title")}
      description={t("CalculationView.Description")}
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {/* Hidden fields for FormData */}
        <input
          type="hidden"
          {...register("tableName")}
          value={selectedTableName}
        />
        <input
          type="hidden"
          {...register("newColumnName")}
          value={newColumnName}
        />
        <input
          type="hidden"
          {...register("calculationExpression")}
          value={calculationExpression}
        />

        <div className="bg-surface-light dark:bg-surface-dark rounded-xl shadow-sm border border-border-color overflow-hidden">
          <div className="p-4 border-b border-border-color grid grid-cols-1 md:grid-cols-2 gap-4 bg-neutral-50/50 dark:bg-neutral-800/30">
            <FormField
              label={t("CalculationView.TargetTable")}
              htmlFor="target-table"
            >
              <Select
                id="target-table"
                value={selectedTableName}
                onValueChange={handleTableChange}
                error={errors.tableName?.message}
                placeholder={t("CalculationView.SelectTable")}
                disabled={isPending}
              >
                {tableList.map((table, index) => (
                  <SelectItem key={index} value={table}>
                    {table}
                  </SelectItem>
                ))}
              </Select>
            </FormField>
            <FormField
              label={t("CalculationView.NewColumnName")}
              htmlFor="new-column-name"
            >
              <InputText
                id="new-column-name"
                value={newColumnName}
                change={(e) =>
                  setValue("newColumnName", e.target.value, {
                    shouldValidate: true,
                  })
                }
                placeholder={t("CalculationView.NewColumnNamePlaceholder")}
                error={errors.newColumnName?.message}
                disabled={isPending}
              />
            </FormField>
          </div>
          <div className="flex flex-col lg:flex-row h-125">
            <div className="flex-1 flex flex-col min-w-0 border-b lg:border-b-0 lg:border-r border-border-color">
              <div className="p-3 bg-neutral-50 dark:bg-neutral-800 border-b border-border-color flex flex-wrap gap-2 items-center">
                <span className="text-xs font-semibold text-neutral-500 uppercase mr-2 tracking-wider">
                  {t("CalculationView.Operators")}
                </span>
                <ExpressionHelperButton
                  onClick={() => handleOperatorClick("+")}
                  className="min-w-8 px-2 text-sm"
                  title={t("CalculationView.Addition")}
                  disabled={isPending}
                >
                  +
                </ExpressionHelperButton>
                <ExpressionHelperButton
                  onClick={() => handleOperatorClick("-")}
                  className="min-w-8 px-2 text-sm"
                  title={t("CalculationView.Subtraction")}
                  disabled={isPending}
                >
                  -
                </ExpressionHelperButton>
                <ExpressionHelperButton
                  onClick={() => handleOperatorClick("*")}
                  className="min-w-8 px-2 text-sm"
                  title={t("CalculationView.Multiplication")}
                  disabled={isPending}
                >
                  *
                </ExpressionHelperButton>
                <ExpressionHelperButton
                  onClick={() => handleOperatorClick("/")}
                  className="min-w-8 px-2 text-sm"
                  title={t("CalculationView.Division")}
                  disabled={isPending}
                >
                  /
                </ExpressionHelperButton>
                <div className="w-px h-6 bg-border-color mx-1"></div>
                <ExpressionHelperButton
                  onClick={() => handleOperatorClick("(")}
                  title={t("CalculationView.OpenParenthesis")}
                  disabled={isPending}
                >
                  (
                </ExpressionHelperButton>
                <ExpressionHelperButton
                  onClick={() => handleOperatorClick(")")}
                  title={t("CalculationView.CloseParenthesis")}
                  disabled={isPending}
                >
                  )
                </ExpressionHelperButton>
                <div className="ml-auto flex items-center gap-2">
                  <button
                    type="button"
                    onClick={handleClearClick}
                    className="text-neutral-400 hover:text-accent transition-colors"
                    title={t("CalculationView.ClearAll")}
                    disabled={isPending}
                  >
                    <span className="material-symbols-outlined text-[20px]">
                      <Eraser />
                    </span>
                  </button>
                </div>
              </div>
              <div className="flex-1 relative bg-white dark:bg-neutral-900">
                <textarea
                  ref={textareaRef}
                  className="w-full h-full p-4 font-mono text-sm text-text-main dark:text-neutral-300 bg-transparent border-none resize-none focus:ring-0 leading-relaxed"
                  placeholder={t("CalculationView.FormulaPlaceholder")}
                  value={calculationExpression}
                  onChange={(e) =>
                    setValue("calculationExpression", e.target.value, {
                      shouldValidate: true,
                    })
                  }
                  disabled={isPending}
                ></textarea>
                {errors.calculationExpression?.message && (
                  <p className="absolute bottom-12 left-4 text-xs text-red-600">
                    {errors.calculationExpression.message}
                  </p>
                )}
                <div className="absolute bottom-0 right-0 left-0 px-4 py-2 bg-neutral-50 dark:bg-neutral-800 border-t border-border-color text-xs text-neutral-500 dark:text-neutral-400 flex items-center gap-2">
                  <span className="material-symbols-outlined text-[16px]">
                    <Info />
                  </span>
                  <span>{t("CalculationView.FormulaHelp")}</span>
                </div>
              </div>
            </div>
            <div className="w-full lg:w-72 flex flex-col bg-neutral-50 dark:bg-surface-dark">
              <div className="p-3 border-b border-border-color">
                <h3 className="text-sm text-gray-700 font-semibold dark:text-white flex items-center gap-2">
                  <span className="material-symbols-outlined text-[18px] text-primary">
                    <Columns3 size={18} strokeWidth={1.2} />
                  </span>
                  {t("CalculationView.AvailableColumns")}
                </h3>
                <div className="mt-2">
                  <SearchInput
                    placeholder={t("CalculationView.FilterColumns")}
                    value={filterValue}
                    onChange={setFilterValue}
                  />
                </div>
              </div>
              <div className="flex-1 overflow-y-auto p-2 space-y-1">
                {filteredColumns.map((column, index) => {
                  const typeColor = getTypeColor(column.type);
                  return (
                    <button
                      key={index}
                      type="button"
                      onClick={() => handleColumnClick(column.name)}
                      className="w-full flex items-center justify-between group p-2 rounded hover:bg-white dark:hover:bg-neutral-800 hover:shadow-sm border border-transparent hover:border-border-color transition-all text-left"
                      disabled={isPending}
                    >
                      <div className="flex items-center gap-2 overflow-hidden">
                        <span
                          className={`px-1.5 py-0.5 rounded ${typeColor.bg} text-[10px] font-bold ${typeColor.text} font-mono`}
                        >
                          {typeColor.label}
                        </span>
                        <span className="text-sm font-medium text-neutral-700 dark:text-neutral-300 font-mono truncate">
                          {column.name}
                        </span>
                      </div>
                      <span className="material-symbols-outlined text-[16px] text-neutral-400 opacity-0 group-hover:opacity-100">
                        <CirclePlus size={16} strokeWidth={1.5} />
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
        <ActionButtonBar
          cancelText={t("Common.Cancel")}
          selectText={
            isPending
              ? t("CalculationView.ExecutingCalculation")
              : t("CalculationView.ExecuteCalculation")
          }
          onCancel={handleCancel}
          onSelect={() => {}}
          onSelectType="submit"
        />
      </form>
    </PageLayout>
  );
};
