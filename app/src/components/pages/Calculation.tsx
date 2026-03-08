import { useForm, useStore } from "@tanstack/react-form";
import { CirclePlus, Columns3, Eraser, Info } from "lucide-react";
import { useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { z } from "zod";
import { getEconomiconAPI } from "../../api/endpoints";
import { useTableColumnLoader } from "../../hooks/useTableColumnLoader";
import { showMessageDialog } from "../../lib/dialog/message";
import { getPolarsTypeColor } from "../../lib/utils/columnTypeColor";
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

export const Calculation = () => {
  const { t } = useTranslation();
  const tableList = useTableListStore((state) => state.tableList);
  const setCurrentView = useCurrentPageStore((state) => state.setCurrentView);

  const { selectedTableName, setSelectedTableName, columnList } =
    useTableColumnLoader({
      numericOnly: true,
      autoLoadOnMount: true,
    });

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [filterValue, setFilterValue] = useState<string>("");

  const form = useForm({
    defaultValues: {
      tableName: selectedTableName,
      newColumnName: "",
      calculationExpression: "",
    },
    validators: {
      onSubmit: createCalculationSchema(t),
    },
    onSubmit: async ({ value }) => {
      try {
        const response = await getEconomiconAPI().calculateColumn({
          tableName: value.tableName,
          newColumnName: value.newColumnName,
          addPositionColumn: "",
          calculationExpression: value.calculationExpression,
        });

        if (response.code === "OK") {
          await showMessageDialog(
            t("Common.OK"),
            t("CalculationView.CalculationSuccess"),
          );
          setCurrentView("DataPreview");
        } else {
          await showMessageDialog(t("Error.Error"), t("Error.UnexpectedError"));
        }
      } catch (error) {
        const errorMessage =
          error instanceof Error ? error.message : t("Error.UnexpectedError");
        await showMessageDialog(t("Error.Error"), errorMessage);
      }
    },
  });

  const isSubmitting = useStore(form.store, (s) => s.isSubmitting);

  const handleTableChange = (value: string) => {
    setSelectedTableName(value);
    form.setFieldValue("tableName", value);
    form.setFieldValue("newColumnName", "");
    form.setFieldValue("calculationExpression", "");
  };

  const insertAtCursor = (text: string) => {
    if (textareaRef.current) {
      const start = textareaRef.current.selectionStart;
      const end = textareaRef.current.selectionEnd;
      const current = form.getFieldValue("calculationExpression");
      const newText =
        current.substring(0, start) + text + current.substring(end);
      form.setFieldValue("calculationExpression", newText);

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

  const handleOperatorClick = (operator: string) => insertAtCursor(operator);

  const handleColumnClick = (columnName: string) =>
    insertAtCursor(`{${columnName}}`);

  const handleClearClick = () => {
    form.setFieldValue("calculationExpression", "");
    textareaRef.current?.focus();
  };

  const handleCancel = () => setCurrentView("DataPreview");

  const filteredColumns = columnList.filter((column) =>
    column.name.toLowerCase().includes(filterValue.toLowerCase()),
  );

  return (
    <PageLayout
      title={t("CalculationView.Title")}
      description={t("CalculationView.Description")}
    >
      <form
        onSubmit={(e) => {
          e.preventDefault();
          e.stopPropagation();
          void form.handleSubmit();
        }}
        className="flex flex-col flex-1 min-h-0 gap-4"
      >
        <div className="flex-1 overflow-y-auto min-h-0">
          <div className="bg-surface-light dark:bg-surface-dark rounded-xl shadow-sm border border-border-color overflow-hidden">
            <div className="p-4 border-b border-border-color grid grid-cols-1 md:grid-cols-2 gap-4 bg-neutral-50/50 dark:bg-neutral-800/30">
              {/* テーブル選択 */}
              <form.Field name="tableName">
                {(field) => (
                  <FormField
                    label={t("CalculationView.TargetTable")}
                    htmlFor="target-table"
                    error={field.state.meta.errors[0]?.toString()}
                  >
                    <Select
                      id="target-table"
                      value={field.state.value}
                      onValueChange={handleTableChange}
                      error={field.state.meta.errors[0]?.toString()}
                      placeholder={t("CalculationView.SelectTable")}
                      disabled={isSubmitting}
                    >
                      {tableList.map((table, index) => (
                        <SelectItem key={index} value={table}>
                          {table}
                        </SelectItem>
                      ))}
                    </Select>
                  </FormField>
                )}
              </form.Field>

              {/* 新しい列名 */}
              <form.Field name="newColumnName">
                {(field) => (
                  <FormField
                    label={t("CalculationView.NewColumnName")}
                    htmlFor="new-column-name"
                    error={field.state.meta.errors[0]?.toString()}
                  >
                    <InputText
                      id="new-column-name"
                      value={field.state.value}
                      onChange={(e) => field.handleChange(e.target.value)}
                      onBlur={field.handleBlur}
                      placeholder={t(
                        "CalculationView.NewColumnNamePlaceholder",
                      )}
                      error={field.state.meta.errors[0]?.toString()}
                      disabled={isSubmitting}
                    />
                  </FormField>
                )}
              </form.Field>
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
                    disabled={isSubmitting}
                  >
                    +
                  </ExpressionHelperButton>
                  <ExpressionHelperButton
                    onClick={() => handleOperatorClick("-")}
                    className="min-w-8 px-2 text-sm"
                    title={t("CalculationView.Subtraction")}
                    disabled={isSubmitting}
                  >
                    -
                  </ExpressionHelperButton>
                  <ExpressionHelperButton
                    onClick={() => handleOperatorClick("*")}
                    className="min-w-8 px-2 text-sm"
                    title={t("CalculationView.Multiplication")}
                    disabled={isSubmitting}
                  >
                    *
                  </ExpressionHelperButton>
                  <ExpressionHelperButton
                    onClick={() => handleOperatorClick("/")}
                    className="min-w-8 px-2 text-sm"
                    title={t("CalculationView.Division")}
                    disabled={isSubmitting}
                  >
                    /
                  </ExpressionHelperButton>
                  <div className="w-px h-6 bg-border-color mx-1"></div>
                  <ExpressionHelperButton
                    onClick={() => handleOperatorClick("(")}
                    title={t("CalculationView.OpenParenthesis")}
                    disabled={isSubmitting}
                  >
                    (
                  </ExpressionHelperButton>
                  <ExpressionHelperButton
                    onClick={() => handleOperatorClick(")")}
                    title={t("CalculationView.CloseParenthesis")}
                    disabled={isSubmitting}
                  >
                    )
                  </ExpressionHelperButton>
                  <div className="ml-auto flex items-center gap-2">
                    <button
                      type="button"
                      onClick={handleClearClick}
                      className="text-neutral-400 hover:text-accent transition-colors"
                      title={t("CalculationView.ClearAll")}
                      disabled={isSubmitting}
                    >
                      <span className="material-symbols-outlined text-[20px]">
                        <Eraser />
                      </span>
                    </button>
                  </div>
                </div>

                {/* 数式エディタ */}
                <div className="flex-1 relative bg-white dark:bg-neutral-900">
                  <form.Field name="calculationExpression">
                    {(field) => (
                      <>
                        <textarea
                          ref={textareaRef}
                          className="w-full h-full p-4 font-mono text-sm text-text-main dark:text-neutral-300 bg-transparent border-none resize-none focus:ring-0 leading-relaxed"
                          placeholder={t("CalculationView.FormulaPlaceholder")}
                          value={field.state.value}
                          onChange={(e) => field.handleChange(e.target.value)}
                          onBlur={field.handleBlur}
                          disabled={isSubmitting}
                        />
                        {field.state.meta.errors[0] && (
                          <p className="absolute bottom-12 left-4 text-xs text-red-600">
                            {field.state.meta.errors[0].toString()}
                          </p>
                        )}
                      </>
                    )}
                  </form.Field>
                  <div className="absolute bottom-0 right-0 left-0 px-4 py-2 bg-neutral-50 dark:bg-neutral-800 border-t border-border-color text-xs text-neutral-500 dark:text-neutral-400 flex items-center gap-2">
                    <span className="material-symbols-outlined text-[16px]">
                      <Info />
                    </span>
                    <span>{t("CalculationView.FormulaHelp")}</span>
                  </div>
                </div>
              </div>

              {/* カラムリスト */}
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
                    const typeColor = getPolarsTypeColor(column.type);
                    return (
                      <button
                        key={index}
                        type="button"
                        onClick={() => handleColumnClick(column.name)}
                        className="w-full flex items-center justify-between group p-2 rounded hover:bg-white dark:hover:bg-neutral-800 hover:shadow-sm border border-transparent hover:border-border-color transition-all text-left"
                        disabled={isSubmitting}
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
        </div>

        <ActionButtonBar
          cancelText={t("Common.Cancel")}
          selectText={
            isSubmitting
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
