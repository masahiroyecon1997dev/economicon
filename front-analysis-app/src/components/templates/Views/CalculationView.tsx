import { CirclePlus, Columns3, Eraser, Info } from "lucide-react";
import { useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { showMessageDialog } from "../../../functions/messageDialog";
import { calculateColumn } from "../../../functions/restApis";
import { useTableColumnLoader } from "../../../hooks/useTableColumnLoader";
import { useCurrentViewStore } from "../../../stores/useCurrentViewStore";
import { useLoadingStore } from "../../../stores/useLoadingStore";
import { useTableListStore } from "../../../stores/useTableListStore";
import { ExpressionHelperButton } from "../../atoms/Button/ExpressionHelperButton";
import { InputText } from "../../atoms/Input/InputText";
import { Select, SelectItem } from "../../atoms/Input/Select";
import { ActionButtonBar } from "../../molecules/ActionBar/ActionButtonBar";
import { FormField } from "../../molecules/Form/FormField";
import { SearchInput } from "../../molecules/Form/SearchInput";
import { MainViewLayout } from "../Layouts/MainViewLayout";

export const CalculationView = () => {
  const { t } = useTranslation();
  const tableList = useTableListStore((state) => state.tableList);
  const setCurrentView = useCurrentViewStore((state) => state.setCurrentView);
  const { setLoading, clearLoading } = useLoadingStore();

  const { selectedTableName, setSelectedTableName, columnList } = useTableColumnLoader({
    numericOnly: true,
    autoLoadOnMount: true,
  });

  const [newColumnName, setNewColumnName] = useState<string>("");
  const [calculationExpression, setCalculationExpression] = useState<string>("");
  const [filterValue, setFilterValue] = useState<string>("");
  const [errorMessage, setErrorMessage] = useState<{
    tableName?: string;
    newColumnName?: string;
    calculationExpression?: string;
  }>({});

  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleTableChange = (value: string) => {
    setSelectedTableName(value);
    setNewColumnName("");
    setCalculationExpression("");
    setErrorMessage({});
  };

  const insertAtCursor = (text: string) => {
    if (textareaRef.current) {
      const start = textareaRef.current.selectionStart;
      const end = textareaRef.current.selectionEnd;
      const before = calculationExpression.substring(0, start);
      const after = calculationExpression.substring(end);
      const newText = before + text + after;
      setCalculationExpression(newText);

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
    setCalculationExpression("");
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  };

  const validateInput = (): boolean => {
    const errors: {
      tableName?: string;
      newColumnName?: string;
      calculationExpression?: string;
    } = {};

    if (!selectedTableName || selectedTableName.trim() === "") {
      errors.tableName = t("CalculationView.Validation.TableNameRequired");
    }

    if (!newColumnName || newColumnName.trim() === "") {
      errors.newColumnName = t("CalculationView.Validation.NewColumnNameRequired");
    }

    if (!calculationExpression || calculationExpression.trim() === "") {
      errors.calculationExpression = t("CalculationView.Validation.CalculationExpressionRequired");
    }

    setErrorMessage(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validateInput()) {
      return;
    }

    setLoading(true, t("CalculationView.ExecutingCalculation"));

    try {
      const response = await calculateColumn({
        tableName: selectedTableName,
        newColumnName: newColumnName,
        calculationExpression: calculationExpression,
      });

      if (response.code === "OK") {
        await showMessageDialog(t("Common.OK"), t("CalculationView.CalculationSuccess"));
        setCurrentView("DataPreview");
      } else {
        await showMessageDialog(t("Error.Error"), response.message);
      }
    } catch {
      await showMessageDialog(t("Error.Error"), t("Error.UnexpectedError"));
    } finally {
      clearLoading();
    }
  };

  const handleCancel = () => {
    setCurrentView("DataPreview");
  };

  const filteredColumns = columnList.filter((column) =>
    column.name.toLowerCase().includes(filterValue.toLowerCase())
  );

  const getTypeColor = (type: string): { bg: string; text: string; label: string } => {
    if (type.includes("Int") || type.includes("UInt")) {
      return { bg: "bg-blue-100 dark:bg-blue-900/30", text: "text-blue-700 dark:text-blue-300", label: "#" };
    } else if (type.includes("Float")) {
      return { bg: "bg-green-100 dark:bg-green-900/30", text: "text-green-700 dark:text-green-300", label: "1.2" };
    } else if (type.includes("Utf8") || type.includes("String")) {
      return { bg: "bg-purple-100 dark:bg-purple-900/30", text: "text-purple-700 dark:text-purple-300", label: "ABC" };
    } else if (type.includes("Date") || type.includes("Datetime")) {
      return { bg: "bg-orange-100 dark:bg-orange-900/30", text: "text-orange-700 dark:text-orange-300", label: "DATE" };
    } else {
      return { bg: "bg-gray-100 dark:bg-gray-900/30", text: "text-gray-700 dark:text-gray-300", label: "?" };
    }
  };

  return (
    <MainViewLayout
      title={t("CalculationView.Title")}
      description={t("CalculationView.Description")}
    >
      <div className="space-y-4">
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
                error={errorMessage.tableName}
                placeholder={t("CalculationView.SelectTable")}
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
                change={(e) => setNewColumnName(e.target.value)}
                placeholder={t("CalculationView.NewColumnNamePlaceholder")}
                error={errorMessage.newColumnName}
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
                >
                  +
                </ExpressionHelperButton>
                <ExpressionHelperButton
                  onClick={() => handleOperatorClick("-")}
                  className="min-w-8 px-2 text-sm"
                  title={t("CalculationView.Subtraction")}
                >
                  -
                </ExpressionHelperButton>
                <ExpressionHelperButton
                  onClick={() => handleOperatorClick("*")}
                  className="min-w-8 px-2 text-sm"
                  title={t("CalculationView.Multiplication")}
                >
                  *
                </ExpressionHelperButton>
                <ExpressionHelperButton
                  onClick={() => handleOperatorClick("/")}
                  className="min-w-8 px-2 text-sm"
                  title={t("CalculationView.Division")}
                >
                  /
                </ExpressionHelperButton>
                <div className="w-px h-6 bg-border-color mx-1"></div>
                <ExpressionHelperButton
                  onClick={() => handleOperatorClick("(")}
                  title={t("CalculationView.OpenParenthesis")}
                >
                  (
                </ExpressionHelperButton>
                <ExpressionHelperButton
                  onClick={() => handleOperatorClick(")")}
                  title={t("CalculationView.CloseParenthesis")}
                >
                  )
                </ExpressionHelperButton>
                <div className="ml-auto flex items-center gap-2">
                  <button
                    onClick={handleClearClick}
                    className="text-neutral-400 hover:text-accent transition-colors"
                    title={t("CalculationView.ClearAll")}
                  >
                    <span className="material-symbols-outlined text-[20px]"><Eraser /></span>
                  </button>
                </div>
              </div>
              <div className="flex-1 relative bg-white dark:bg-neutral-900">
                <textarea
                  ref={textareaRef}
                  className="w-full h-full p-4 font-mono text-sm text-text-main dark:text-neutral-300 bg-transparent border-none resize-none focus:ring-0 leading-relaxed"
                  placeholder={t("CalculationView.FormulaPlaceholder")}
                  value={calculationExpression}
                  onChange={(e) => setCalculationExpression(e.target.value)}
                ></textarea>
                {errorMessage.calculationExpression && (
                  <p className="absolute bottom-12 left-4 text-xs text-red-600">
                    {errorMessage.calculationExpression}
                  </p>
                )}
                <div className="absolute bottom-0 right-0 left-0 px-4 py-2 bg-neutral-50 dark:bg-neutral-800 border-t border-border-color text-xs text-neutral-500 dark:text-neutral-400 flex items-center gap-2">
                  <span className="material-symbols-outlined text-[16px]"><Info /></span>
                  <span>{t("CalculationView.FormulaHelp")}</span>
                </div>
              </div>
            </div>
            <div className="w-full lg:w-72 flex flex-col bg-neutral-50 dark:bg-surface-dark">
              <div className="p-3 border-b border-border-color">
                <h3 className="text-sm text-gray-700 font-semibold dark:text-white flex items-center gap-2">
                  <span className="material-symbols-outlined text-[18px] text-primary"><Columns3 size={18} strokeWidth={1.2} /></span>
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
                      onClick={() => handleColumnClick(column.name)}
                      className="w-full flex items-center justify-between group p-2 rounded hover:bg-white dark:hover:bg-neutral-800 hover:shadow-sm border border-transparent hover:border-border-color transition-all text-left"
                    >
                      <div className="flex items-center gap-2 overflow-hidden">
                        <span className={`px-1.5 py-0.5 rounded ${typeColor.bg} text-[10px] font-bold ${typeColor.text} font-mono`}>
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
          selectText={t("CalculationView.ExecuteCalculation")}
          onCancel={handleCancel}
          onSelect={handleSubmit}
        />
      </div>
    </MainViewLayout>
  );
};
