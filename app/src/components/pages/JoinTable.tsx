import { ArrowRight, Plus, Sparkles, X } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { getEconomiconAppAPI } from "../../api/endpoints";
import { JoinType } from "../../api/model";
import { showMessageDialog } from "../../lib/dialog/message";
import {
  extractApiErrorMessage,
  getResponseErrorMessage,
} from "../../lib/utils/apiError";
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

type KeyPair = { id: string; left: string; right: string };

const generateId = () => Math.random().toString(36).slice(2, 9);

type FormErrors = {
  tables?: string;
  keyPairs?: string;
  newTableName?: string;
};

export const JoinTable = () => {
  const { t } = useTranslation();
  const tableList = useTableListStore((s) => s.tableList);
  const addTableName = useTableListStore((s) => s.addTableName);
  const addTableInfo = useTableInfosStore((s) => s.addTableInfo);
  const setCurrentView = useCurrentPageStore((s) => s.setCurrentView);

  const [leftTable, setLeftTable] = useState("");
  const [rightTable, setRightTable] = useState("");
  const [leftCols, setLeftCols] = useState<ColumnType[]>([]);
  const [rightCols, setRightCols] = useState<ColumnType[]>([]);
  const [isLoadingLeft, setIsLoadingLeft] = useState(false);
  const [isLoadingRight, setIsLoadingRight] = useState(false);
  const [keyPairs, setKeyPairs] = useState<KeyPair[]>([
    { id: generateId(), left: "", right: "" },
  ]);
  const [joinType, setJoinType] = useState<string>(JoinType.inner);
  const [newTableName, setNewTableName] = useState("");
  const [autoSuggestApplied, setAutoSuggestApplied] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<FormErrors>({});

  /* ── Column loading ───────────────────────────────────────── */

  const fetchCols = async (tableName: string): Promise<ColumnType[]> => {
    if (!tableName) return [];
    try {
      const api = getEconomiconAppAPI();
      const resp = await api.getColumnList({ tableName });
      if (resp.code === "OK") return resp.result.columnInfoList;
    } catch {
      /* no-op */
    }
    return [];
  };

  /* ── Auto-suggest: match same-name columns ────────────────── */

  const applyAutoSuggest = (
    lCols: ColumnType[],
    rCols: ColumnType[],
    lTable: string,
    rTable: string,
  ) => {
    if (!lCols.length || !rCols.length) {
      setAutoSuggestApplied(false);
      return;
    }
    const rNames = new Set(rCols.map((c) => c.name));
    const matched = lCols.filter((c) => rNames.has(c.name));
    if (matched.length > 0) {
      setKeyPairs(
        matched.map((c) => ({ id: generateId(), left: c.name, right: c.name })),
      );
      setAutoSuggestApplied(true);
    } else {
      setKeyPairs([{ id: generateId(), left: "", right: "" }]);
      setAutoSuggestApplied(false);
    }
    if (lTable && rTable && !newTableName) {
      setNewTableName(`${lTable}_${rTable}_joined`);
    }
  };

  /* ── Table select handlers ────────────────────────────────── */

  const handleLeftTableChange = async (value: string) => {
    setLeftTable(value);
    setIsLoadingLeft(true);
    const cols = await fetchCols(value);
    setLeftCols(cols);
    setIsLoadingLeft(false);
    applyAutoSuggest(cols, rightCols, value, rightTable);
    // auto-update table name when both sides are selected
    if (value && rightTable) {
      setNewTableName(`${value}_${rightTable}_joined`);
    }
  };

  const handleRightTableChange = async (value: string) => {
    setRightTable(value);
    setIsLoadingRight(true);
    const cols = await fetchCols(value);
    setRightCols(cols);
    setIsLoadingRight(false);
    applyAutoSuggest(leftCols, cols, leftTable, value);
    if (leftTable && value) {
      setNewTableName(`${leftTable}_${value}_joined`);
    }
  };

  /* ── Key pair operations ──────────────────────────────────── */

  const addKeyPair = () =>
    setKeyPairs((prev) => [...prev, { id: generateId(), left: "", right: "" }]);

  const removeKeyPair = (id: string) =>
    setKeyPairs((prev) => prev.filter((p) => p.id !== id));

  const updateKeyPair = (id: string, side: "left" | "right", value: string) =>
    setKeyPairs((prev) =>
      prev.map((p) => (p.id === id ? { ...p, [side]: value } : p)),
    );

  /* ── Validation ───────────────────────────────────────────── */

  const validate = (): boolean => {
    const next: FormErrors = {};
    if (!leftTable || !rightTable) {
      next.tables = t("JoinTable.ErrorDataRequired");
    }
    if (keyPairs.some((p) => !p.left || !p.right)) {
      next.keyPairs = t("JoinTable.ErrorKeyRequired");
    }
    if (!newTableName.trim()) {
      next.newTableName = t("JoinTable.ErrorNewDataNameRequired");
    }
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  /* ── Submit ───────────────────────────────────────────────── */

  const handleSubmit = async () => {
    if (!validate()) return;
    setIsSubmitting(true);
    try {
      const api = getEconomiconAppAPI();
      const resp = await api.createJoinTable({
        joinTableName: newTableName.trim(),
        leftTableName: leftTable,
        rightTableName: rightTable,
        leftKeyColumnNames: keyPairs.map((p) => p.left),
        rightKeyColumnNames: keyPairs.map((p) => p.right),
        joinType: joinType as JoinType,
      });
      if (resp.code === "OK") {
        const tableInfo = await getTableInfo(newTableName.trim());
        addTableName(newTableName.trim());
        addTableInfo(tableInfo);
        setCurrentView("DataPreview");
      } else {
        await showMessageDialog(
          t("Error.Error"),
          getResponseErrorMessage(resp, t("Error.UnexpectedError")),
        );
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

  const isDisabled = isSubmitting || isLoadingLeft || isLoadingRight;

  return (
    <PageLayout
      title={t("JoinTable.Title")}
      description={t("JoinTable.Description")}
    >
      <div className="flex flex-col flex-1 min-h-0 gap-4 overflow-y-auto pb-2">
        {/* ── Section 1: テーブル・結合タイプ ── */}
        <div className="rounded-xl border border-border-color bg-white p-4 shadow-sm">
          <h2 className="mb-3 text-sm font-bold leading-tight text-text-heading">
            {t("JoinTable.SelectData")}
          </h2>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <FormField
              label={t("JoinTable.LeftData")}
              htmlFor="left-table"
              error={!leftTable ? errors.tables : undefined}
            >
              <Select
                id="left-table"
                value={leftTable}
                onValueChange={handleLeftTableChange}
                placeholder={t("JoinTable.SelectDataItem")}
                disabled={isDisabled}
              >
                {tableList.map((name) => (
                  <SelectItem key={name} value={name}>
                    {name}
                  </SelectItem>
                ))}
              </Select>
            </FormField>

            <FormField
              label={t("JoinTable.RightData")}
              htmlFor="right-table"
              error={!rightTable ? errors.tables : undefined}
            >
              <Select
                id="right-table"
                value={rightTable}
                onValueChange={handleRightTableChange}
                placeholder={t("JoinTable.SelectDataItem")}
                disabled={isDisabled}
              >
                {tableList.map((name) => (
                  <SelectItem key={name} value={name}>
                    {name}
                  </SelectItem>
                ))}
              </Select>
            </FormField>

            <FormField label={t("JoinTable.JoinType")} htmlFor="join-type">
              <Select
                id="join-type"
                value={joinType}
                onValueChange={setJoinType}
                disabled={isDisabled}
              >
                <SelectItem value={JoinType.inner}>
                  {t("JoinTable.JoinType_inner")}
                </SelectItem>
                <SelectItem value={JoinType.left}>
                  {t("JoinTable.JoinType_left")}
                </SelectItem>
                <SelectItem value={JoinType.right}>
                  {t("JoinTable.JoinType_right")}
                </SelectItem>
                <SelectItem value={JoinType.full}>
                  {t("JoinTable.JoinType_full")}
                </SelectItem>
              </Select>
            </FormField>
          </div>
        </div>

        {/* ── Section 2: 結合キーペア ── */}
        <div className="rounded-xl border border-border-color bg-white p-4 shadow-sm">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-bold leading-tight text-text-heading">
              {t("JoinTable.KeyPairs")}
            </h2>
            {autoSuggestApplied && (
              <span className="flex items-center gap-1 rounded-full bg-brand-accent/10 px-2.5 py-0.5 text-xs font-medium text-brand-accent">
                <Sparkles className="h-3 w-3" />
                {t("JoinTable.AutoSuggestApplied")}
              </span>
            )}
          </div>

          {/* ヘッダー行 */}
          <div className="mb-1 grid grid-cols-[1fr_20px_1fr_32px] gap-2 px-0.5">
            <span className="truncate text-xs font-medium text-brand-text-main/60">
              {leftTable ? leftTable : t("JoinTable.LeftData")}
            </span>
            <div />
            <span className="truncate text-xs font-medium text-brand-text-main/60">
              {rightTable ? rightTable : t("JoinTable.RightData")}
            </span>
            <div />
          </div>

          {/* キーペア行 */}
          <div className="flex flex-col gap-2">
            {keyPairs.map((pair) => (
              <div
                key={pair.id}
                className="grid grid-cols-[1fr_20px_1fr_32px] items-center gap-2"
              >
                <Select
                  value={pair.left}
                  onValueChange={(v) => updateKeyPair(pair.id, "left", v)}
                  placeholder={t("JoinTable.SelectColumn")}
                  disabled={!leftTable || isDisabled}
                >
                  {leftCols.map((c) => (
                    <SelectItem key={c.name} value={c.name}>
                      {c.name}
                    </SelectItem>
                  ))}
                </Select>

                <ArrowRight className="h-4 w-4 shrink-0 text-brand-text-main/30" />

                <Select
                  value={pair.right}
                  onValueChange={(v) => updateKeyPair(pair.id, "right", v)}
                  placeholder={t("JoinTable.SelectColumn")}
                  disabled={!rightTable || isDisabled}
                >
                  {rightCols.map((c) => (
                    <SelectItem key={c.name} value={c.name}>
                      {c.name}
                    </SelectItem>
                  ))}
                </Select>

                <button
                  type="button"
                  onClick={() => removeKeyPair(pair.id)}
                  disabled={keyPairs.length === 1 || isDisabled}
                  className={cn(
                    "flex items-center justify-center rounded p-1 transition-colors",
                    "text-brand-text-main/40 hover:bg-red-50 hover:text-red-500",
                    "disabled:cursor-not-allowed disabled:opacity-30",
                  )}
                  aria-label={t("JoinTable.RemoveKeyPair")}
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>

          {errors.keyPairs && (
            <p className="mt-1.5 text-xs text-red-600">{errors.keyPairs}</p>
          )}

          <button
            type="button"
            onClick={addKeyPair}
            disabled={isDisabled}
            className={cn(
              "mt-3 flex items-center gap-1 text-xs font-medium",
              "text-brand-accent hover:underline",
              "disabled:cursor-not-allowed disabled:opacity-50",
            )}
          >
            <Plus className="h-3.5 w-3.5" />
            {t("JoinTable.AddKeyPair")}
          </button>
        </div>

        {/* ── Section 3: 出力テーブル名 ── */}
        <div className="rounded-xl border border-border-color bg-white p-4 shadow-sm">
          <h2 className="mb-3 text-sm font-bold leading-tight text-text-heading">
            {t("JoinTable.OutputData")}
          </h2>
          <FormField
            label={t("JoinTable.NewDataName")}
            htmlFor="new-table-name"
            error={errors.newTableName}
          >
            <InputText
              id="new-table-name"
              value={newTableName}
              onChange={(e) => setNewTableName(e.target.value)}
              placeholder={t("JoinTable.NewDataNamePlaceholder")}
              disabled={isDisabled}
              error={errors.newTableName}
            />
          </FormField>
        </div>
      </div>

      <ActionButtonBar
        cancelText={t("Common.Cancel")}
        selectText={
          isSubmitting ? t("JoinTable.Processing") : t("JoinTable.RunJoin")
        }
        onCancel={() => setCurrentView("DataPreview")}
        onSelect={handleSubmit}
      />
    </PageLayout>
  );
};
