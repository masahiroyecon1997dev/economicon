import { Plus, X } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { getEconomiconAPI } from "../../api/endpoints";
import { showMessageDialog } from "../../lib/dialog/message";
import { cn } from "../../lib/utils/helpers";
import { getTableInfo } from "../../lib/utils/internal";
import { useCurrentPageStore } from "../../stores/currentView";
import { useTableInfosStore } from "../../stores/tableInfos";
import { useTableListStore } from "../../stores/tableList";
import type { ColumnType } from "../../types/commonTypes";
import { InputText } from "../atoms/Input/InputText";
import { Select, SelectItem } from "../atoms/Input/Select";
import { ActionButtonBar } from "../molecules/ActionBar/ActionButtonBar";
import { FormField } from "../molecules/Form/FormField";
import { PageLayout } from "../templates/PageLayout";

const generateId = () => Math.random().toString(36).slice(2, 9);

type TableEntry = { id: string; name: string };

type FormErrors = {
  tables?: string;
  columns?: string;
  newTableName?: string;
};

export const UnionTable = () => {
  const { t } = useTranslation();
  const tableList = useTableListStore((s) => s.tableList);
  const addTableName = useTableListStore((s) => s.addTableName);
  const addTableInfo = useTableInfosStore((s) => s.addTableInfo);
  const setCurrentView = useCurrentPageStore((s) => s.setCurrentView);

  const [selectedTables, setSelectedTables] = useState<TableEntry[]>([]);
  const [addingTable, setAddingTable] = useState("");
  const [commonCols, setCommonCols] = useState<string[]>([]);
  const [checkedCols, setCheckedCols] = useState<Set<string>>(new Set());
  const [newTableName, setNewTableName] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<FormErrors>({});

  /* ── Fetch column names for a table ───────────────────────── */

  const fetchColNames = async (tableName: string): Promise<string[]> => {
    try {
      const api = getEconomiconAPI();
      const resp = await api.getColumnList({ tableName });
      if (resp.code === "OK")
        return resp.result.columnInfoList.map((c: ColumnType) => c.name);
    } catch {
      /* no-op */
    }
    return [];
  };

  /* ── Recalculate common columns whenever selectedTables changes ── */

  useEffect(() => {
    const recalc = async () => {
      if (selectedTables.length === 0) {
        setCommonCols([]);
        setCheckedCols(new Set());
        return;
      }
      setIsLoading(true);
      const allColSets = await Promise.all(
        selectedTables.map((t) => fetchColNames(t.name)),
      );
      // intersection: columns that appear in every table
      const intersection = allColSets.reduce((acc, cols) => {
        const colSet = new Set(cols);
        return acc.filter((c) => colSet.has(c));
      });
      setCommonCols(intersection);
      // auto-select all common columns
      setCheckedCols(new Set(intersection));
      setIsLoading(false);
    };
    void recalc();
  }, [selectedTables]);

  /* ── Table list operations ────────────────────────────────── */

  const handleAddTable = () => {
    if (!addingTable) return;
    if (selectedTables.some((t) => t.name === addingTable)) {
      setAddingTable("");
      return;
    }
    const next = [...selectedTables, { id: generateId(), name: addingTable }];
    setSelectedTables(next);
    if (next.length === 1) {
      setNewTableName(`${addingTable}_union`);
    }
    setAddingTable("");
  };

  const handleRemoveTable = (id: string) => {
    setSelectedTables((prev) => prev.filter((t) => t.id !== id));
  };

  /* ── Column checkbox operations ───────────────────────────── */

  const handleToggleCol = (colName: string) => {
    setCheckedCols((prev) => {
      const next = new Set(prev);
      if (next.has(colName)) next.delete(colName);
      else next.add(colName);
      return next;
    });
  };

  const handleSelectAll = () => {
    if (checkedCols.size === commonCols.length) {
      setCheckedCols(new Set());
    } else {
      setCheckedCols(new Set(commonCols));
    }
  };

  /* ── Validation ───────────────────────────────────────────── */

  const validate = (): boolean => {
    const next: FormErrors = {};
    if (selectedTables.length < 2) {
      next.tables = t("UnionTable.ErrorTablesRequired");
    }
    if (checkedCols.size === 0) {
      next.columns = t("UnionTable.ErrorColumnsRequired");
    }
    if (!newTableName.trim()) {
      next.newTableName = t("UnionTable.ErrorNewTableNameRequired");
    }
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  /* ── Submit ───────────────────────────────────────────────── */

  const handleSubmit = async () => {
    if (!validate()) return;
    setIsSubmitting(true);
    try {
      const api = getEconomiconAPI();
      const resp = await api.createUnionTable({
        unionTableName: newTableName.trim(),
        tableNames: selectedTables.map((t) => t.name),
        columnNames: Array.from(checkedCols),
      });
      if (resp.code === "OK") {
        const tableInfo = await getTableInfo(newTableName.trim());
        addTableName(newTableName.trim());
        addTableInfo(tableInfo);
        setCurrentView("DataPreview");
      } else {
        await showMessageDialog(t("Error.Error"), t("Error.UnexpectedError"));
      }
    } catch (error) {
      const msg =
        error instanceof Error ? error.message : t("Error.UnexpectedError");
      await showMessageDialog(t("Error.Error"), msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const isDisabled = isSubmitting || isLoading;
  const availableToAdd = tableList.filter(
    (name) => !selectedTables.some((t) => t.name === name),
  );
  const allChecked =
    commonCols.length > 0 && checkedCols.size === commonCols.length;

  return (
    <PageLayout
      title={t("UnionTable.Title")}
      description={t("UnionTable.Description")}
    >
      <div className="flex flex-col flex-1 min-h-0 gap-4 overflow-y-auto pb-2">
        {/* ── Section 1: 対象テーブル ── */}
        <div className="rounded-xl border border-border-color bg-white p-4 shadow-sm">
          <h2 className="mb-3 text-sm font-bold leading-tight text-text-heading">
            {t("UnionTable.SelectTables")}
          </h2>

          {/* テーブル追加行 */}
          <div className="mb-3 flex gap-2">
            <div className="flex-1">
              <Select
                value={addingTable}
                onValueChange={setAddingTable}
                placeholder={t("UnionTable.SelectTable")}
                disabled={isDisabled || availableToAdd.length === 0}
              >
                {availableToAdd.map((name) => (
                  <SelectItem key={name} value={name}>
                    {name}
                  </SelectItem>
                ))}
              </Select>
            </div>
            <button
              type="button"
              onClick={handleAddTable}
              disabled={!addingTable || isDisabled}
              className={cn(
                "flex shrink-0 items-center gap-1 rounded-md border border-border-color bg-white px-3 py-1.5 text-sm font-medium",
                "transition-colors hover:bg-secondary",
                "disabled:cursor-not-allowed disabled:opacity-40",
              )}
            >
              <Plus className="h-4 w-4" />
              {t("UnionTable.Add")}
            </button>
          </div>

          {/* 選択済みテーブルリスト */}
          {selectedTables.length === 0 ? (
            <p className="rounded-lg border border-dashed border-border-color py-4 text-center text-xs text-brand-text-main/50">
              {t("UnionTable.NoTablesSelected")}
            </p>
          ) : (
            <ul className="flex flex-col gap-1.5">
              {selectedTables.map((entry, idx) => (
                <li
                  key={entry.id}
                  className="flex items-center gap-2 rounded-lg border border-border-color bg-secondary px-3 py-2"
                >
                  <span className="w-5 shrink-0 text-center text-xs font-bold text-brand-text-main/40">
                    {idx + 1}
                  </span>
                  <span className="flex-1 truncate text-sm">{entry.name}</span>
                  <button
                    type="button"
                    onClick={() => handleRemoveTable(entry.id)}
                    disabled={isDisabled}
                    className={cn(
                      "flex items-center justify-center rounded p-1 transition-colors",
                      "text-brand-text-main/40 hover:bg-red-50 hover:text-red-500",
                      "disabled:cursor-not-allowed disabled:opacity-30",
                    )}
                    aria-label={t("UnionTable.RemoveTable")}
                  >
                    <X className="h-4 w-4" />
                  </button>
                </li>
              ))}
            </ul>
          )}

          {errors.tables && (
            <p className="mt-1.5 text-xs text-red-600">{errors.tables}</p>
          )}
        </div>

        {/* ── Section 2: ユニオンする列 ── */}
        <div className="rounded-xl border border-border-color bg-white p-4 shadow-sm">
          <div className="mb-3 flex items-center justify-between">
            <div>
              <h2 className="text-sm font-bold leading-tight text-text-heading">
                {t("UnionTable.SelectColumns")}
              </h2>
              <p className="mt-0.5 text-xs text-brand-text-main/60">
                {t("UnionTable.SelectColumnsDescription")}
              </p>
            </div>
            {commonCols.length > 0 && (
              <button
                type="button"
                onClick={handleSelectAll}
                disabled={isDisabled}
                className="shrink-0 text-xs font-medium text-brand-accent hover:underline disabled:cursor-not-allowed disabled:opacity-50"
              >
                {allChecked
                  ? t("UnionTable.DeselectAll")
                  : t("UnionTable.SelectAll")}
              </button>
            )}
          </div>

          {selectedTables.length < 2 ? (
            <p className="rounded-lg border border-dashed border-border-color py-4 text-center text-xs text-brand-text-main/50">
              {t("UnionTable.SelectTablesFirst")}
            </p>
          ) : isLoading ? (
            <p className="rounded-lg border border-dashed border-border-color py-4 text-center text-xs text-brand-text-main/50">
              {t("UnionTable.LoadingColumns")}
            </p>
          ) : commonCols.length === 0 ? (
            <p className="rounded-lg border border-dashed border-red-200 bg-red-50 py-4 text-center text-xs text-red-500">
              {t("UnionTable.NoCommonColumns")}
            </p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {commonCols.map((col) => {
                const isChecked = checkedCols.has(col);
                return (
                  <label
                    key={col}
                    className={cn(
                      "flex cursor-pointer items-center gap-2 rounded-md border px-3 py-1.5 text-sm transition-colors",
                      isChecked
                        ? "border-brand-accent bg-brand-accent/5 text-brand-accent"
                        : "border-border-color bg-secondary text-brand-text-main hover:border-brand-accent/50",
                      isDisabled && "cursor-not-allowed opacity-50",
                    )}
                  >
                    <input
                      type="checkbox"
                      checked={isChecked}
                      onChange={() => handleToggleCol(col)}
                      disabled={isDisabled}
                      className="h-3.5 w-3.5 rounded border-gray-300 text-brand-accent focus:ring-brand-accent"
                    />
                    <span>{col}</span>
                  </label>
                );
              })}
            </div>
          )}

          {errors.columns && (
            <p className="mt-1.5 text-xs text-red-600">{errors.columns}</p>
          )}
        </div>

        {/* ── Section 3: 出力テーブル名 ── */}
        <div className="rounded-xl border border-border-color bg-white p-4 shadow-sm">
          <h2 className="mb-3 text-sm font-bold leading-tight text-text-heading">
            {t("UnionTable.OutputTable")}
          </h2>
          <FormField
            label={t("UnionTable.NewTableName")}
            htmlFor="union-new-table-name"
            error={errors.newTableName}
          >
            <InputText
              id="union-new-table-name"
              value={newTableName}
              onChange={(e) => setNewTableName(e.target.value)}
              placeholder={t("UnionTable.NewTableNamePlaceholder")}
              disabled={isDisabled}
              error={errors.newTableName}
            />
          </FormField>
        </div>
      </div>

      <ActionButtonBar
        cancelText={t("Common.Cancel")}
        selectText={
          isSubmitting ? t("UnionTable.Processing") : t("UnionTable.RunUnion")
        }
        onCancel={() => setCurrentView("DataPreview")}
        onSelect={handleSubmit}
      />
    </PageLayout>
  );
};
