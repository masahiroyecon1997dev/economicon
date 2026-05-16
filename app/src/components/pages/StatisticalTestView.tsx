import { getEconomiconAppAPI } from "@/api/endpoints";
import type {
  AlternativeHypothesis,
  SampleInput,
  StatisticalTestRequestBody,
  StatisticalTestType,
} from "@/api/model";
import {
  AlternativeHypothesis as AlternativeHypothesisValues,
  StatisticalTestType as StatisticalTestTypeValues,
} from "@/api/model";
import { StatisticalTestBody } from "@/api/zod/statistics/statistics";
import { InputText } from "@/components/atoms/Input/InputText";
import { Select, SelectItem } from "@/components/atoms/Input/Select";
import { ActionButtonBar } from "@/components/molecules/ActionBar/ActionButtonBar";
import { FormField } from "@/components/molecules/Form/FormField";
import {
  AnalysisEmptyState,
  AnalysisNoTablesState,
} from "@/components/organisms/EmptyState/AnalysisNoTablesState";
import { PageLayout } from "@/components/templates/PageLayout";
import { showMessageDialog } from "@/lib/dialog/message";
import {
  buildCaughtErrorMessage,
  buildResponseErrorMessage,
} from "@/lib/utils/apiError";
import { cn } from "@/lib/utils/helpers";
import { useAnalysisResultsStore } from "@/stores/analysisResults";
import { useCurrentPageStore } from "@/stores/currentPage";
import { useTableInfosStore } from "@/stores/tableInfos";
import { useTableListStore } from "@/stores/tableList";
import type { WorkspaceWorkTab } from "@/stores/workspaceTabs";
import {
  selectWorkTabDraft,
  useWorkspaceTabsStore,
} from "@/stores/workspaceTabs";
import type { ColumnType } from "@/types/commonTypes";
import { useForm, useStore } from "@tanstack/react-form";
import { Loader2, Minus, Plus, SearchX } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { z } from "zod";

type StatisticalTestFormValues = {
  testType: StatisticalTestType;
  samples: SampleInput[];
  options: {
    alternative: AlternativeHypothesis;
    mu: string;
    paired: boolean;
    equalVar: boolean;
    confidenceLevel: string;
  };
};

type StatisticalTestViewProps = {
  workTabId?: `work:StatisticalTestView`;
  onCancel?: () => void | Promise<void>;
};

type ValidationErrors = {
  testType?: string;
  samples?: string;
  sampleRows: Record<
    number,
    {
      tableName?: string;
      columnName?: string;
    }
  >;
  options: {
    mu?: string;
    paired?: string;
    confidenceLevel?: string;
  };
};

const EMPTY_ERRORS: ValidationErrors = {
  sampleRows: {},
  options: {},
};

const statisticalTestDraftSchema = z.object({
  testType: z.enum([
    StatisticalTestTypeValues["t-test"],
    StatisticalTestTypeValues["z-test"],
    StatisticalTestTypeValues["f-test"],
  ]),
  samples: z.array(z.object({ tableName: z.string(), columnName: z.string() })),
  options: z.object({
    alternative: z.enum([
      AlternativeHypothesisValues["two-sided"],
      AlternativeHypothesisValues.larger,
      AlternativeHypothesisValues.smaller,
    ]),
    mu: z.string(),
    paired: z.boolean(),
    equalVar: z.boolean(),
    confidenceLevel: z.string(),
  }),
});

const TEST_TYPE_OPTIONS: StatisticalTestType[] = [
  StatisticalTestTypeValues["t-test"],
  StatisticalTestTypeValues["z-test"],
  StatisticalTestTypeValues["f-test"],
];

const ALTERNATIVE_OPTIONS: AlternativeHypothesis[] = [
  AlternativeHypothesisValues["two-sided"],
  AlternativeHypothesisValues.larger,
  AlternativeHypothesisValues.smaller,
];

const buildDefaultValues = (
  initialTableName: string,
  persistedDraft?: StatisticalTestFormValues,
): StatisticalTestFormValues => ({
  testType: persistedDraft?.testType ?? StatisticalTestTypeValues["t-test"],
  samples:
    persistedDraft?.samples.length && persistedDraft.samples.length > 0
      ? persistedDraft.samples
      : [
          {
            tableName: initialTableName,
            columnName: "",
          },
        ],
  options: {
    alternative:
      persistedDraft?.options.alternative ??
      AlternativeHypothesisValues["two-sided"],
    mu: persistedDraft?.options.mu ?? "",
    paired: persistedDraft?.options.paired ?? false,
    equalVar: persistedDraft?.options.equalVar ?? true,
    confidenceLevel: persistedDraft?.options.confidenceLevel ?? "0.95",
  },
});

const cloneSample = (tableName = ""): SampleInput => ({
  tableName,
  columnName: "",
});

const inferRequestBody = (
  values: StatisticalTestFormValues,
  errors: ValidationErrors,
  t: (_key: string) => string,
): StatisticalTestRequestBody | null => {
  const nextErrors: ValidationErrors = {
    sampleRows: { ...errors.sampleRows },
    options: { ...errors.options },
  };

  const trimmedConfidenceLevel = values.options.confidenceLevel.trim();
  const parsedConfidenceLevel = Number(trimmedConfidenceLevel);
  if (
    trimmedConfidenceLevel === "" ||
    Number.isNaN(parsedConfidenceLevel) ||
    parsedConfidenceLevel <= 0 ||
    parsedConfidenceLevel >= 1
  ) {
    nextErrors.options.confidenceLevel = t(
      "StatisticalTestView.ErrorConfidenceLevelInvalid",
    );
  }

  const isOneSample = values.samples.length === 1;
  let parsedMu: number | null | undefined = undefined;
  if (isOneSample) {
    const trimmedMu = values.options.mu.trim();
    if (trimmedMu !== "") {
      const numericMu = Number(trimmedMu);
      if (Number.isNaN(numericMu)) {
        nextErrors.options.mu = t("StatisticalTestView.ErrorMuInvalid");
      } else {
        parsedMu = numericMu;
      }
    }
  }

  if (nextErrors.options.mu || nextErrors.options.confidenceLevel) {
    Object.assign(errors.options, nextErrors.options);
    return null;
  }

  return {
    testType: values.testType,
    samples: values.samples,
    options: {
      alternative: values.options.alternative,
      mu: parsedMu,
      paired: values.options.paired,
      equalVar: values.options.equalVar,
      confidenceLevel: parsedConfidenceLevel,
    },
  };
};

const mapValidationErrors = (
  requestBody: StatisticalTestRequestBody,
  t: (_key: string) => string,
) => {
  const errors: ValidationErrors = {
    sampleRows: {},
    options: {},
  };

  const parsed = StatisticalTestBody.safeParse(requestBody);
  if (!parsed.success) {
    for (const issue of parsed.error.issues) {
      const [first, second, third] = issue.path;
      if (first === "testType") {
        errors.testType = t("StatisticalTestView.ErrorTestTypeRequired");
      }
      if (
        first === "samples" &&
        typeof second === "number" &&
        third === "tableName"
      ) {
        errors.sampleRows[second] = {
          ...errors.sampleRows[second],
          tableName: t("StatisticalTestView.ErrorDataRequired"),
        };
      }
      if (
        first === "samples" &&
        typeof second === "number" &&
        third === "columnName"
      ) {
        errors.sampleRows[second] = {
          ...errors.sampleRows[second],
          columnName: t("StatisticalTestView.ErrorColumnRequired"),
        };
      }
      if (
        first === "options" &&
        third === undefined &&
        second === "confidenceLevel"
      ) {
        errors.options.confidenceLevel = t(
          "StatisticalTestView.ErrorConfidenceLevelInvalid",
        );
      }
    }
  }

  if (
    requestBody.testType === StatisticalTestTypeValues["f-test"] &&
    requestBody.samples.length < 2
  ) {
    errors.samples = t("StatisticalTestView.ErrorMinimumTwoSamples");
  }

  if (
    (requestBody.testType === StatisticalTestTypeValues["t-test"] ||
      requestBody.testType === StatisticalTestTypeValues["z-test"]) &&
    requestBody.samples.length > 2
  ) {
    errors.samples = t("StatisticalTestView.ErrorMaximumTwoSamples");
  }

  if (
    requestBody.options?.paired &&
    !(
      requestBody.testType === StatisticalTestTypeValues["t-test"] &&
      requestBody.samples.length === 2
    )
  ) {
    errors.options.paired = t(
      "StatisticalTestView.ErrorPairedRequiresTwoSampleTTest",
    );
  }

  return errors;
};

const hasValidationErrors = (errors: ValidationErrors) => {
  if (errors.testType || errors.samples) return true;
  if (
    errors.options.mu ||
    errors.options.paired ||
    errors.options.confidenceLevel
  ) {
    return true;
  }
  return Object.values(errors.sampleRows).some(
    (row) => row.tableName || row.columnName,
  );
};

export const StatisticalTestView = ({
  workTabId,
  onCancel,
}: StatisticalTestViewProps) => {
  const { t } = useTranslation();
  const tableList = useTableListStore((state) => state.tableList);
  const initialTableName =
    useTableInfosStore((state) => state.activeTableName) ?? "";
  const navigateToShell = useCurrentPageStore((state) => state.navigateToShell);
  const navigateToWorkspace = useCurrentPageStore(
    (state) => state.navigateToWorkspace,
  );
  const openResultTab = useWorkspaceTabsStore((state) => state.openResultTab);
  const closeActiveWorkTab = useWorkspaceTabsStore(
    (state) => state.closeActiveWorkTab,
  );
  const ensureWorkTabState = useWorkspaceTabsStore(
    (state) => state.ensureWorkTabState,
  );
  const updateWorkTabDraft = useWorkspaceTabsStore(
    (state) => state.updateWorkTabDraft,
  );
  const commitWorkTab = useWorkspaceTabsStore((state) => state.commitWorkTab);
  const persistedWorkTab = useWorkspaceTabsStore((state) =>
    workTabId
      ? (state.tabs.find(
          (tab): tab is WorkspaceWorkTab =>
            tab.id === workTabId && tab.kind === "work",
        ) ?? null)
      : null,
  );

  const persistedDraft = selectWorkTabDraft(
    persistedWorkTab,
    statisticalTestDraftSchema,
  );

  const form = useForm({
    defaultValues: buildDefaultValues(initialTableName, persistedDraft),
    onSubmit: async () => {},
  });
  const values = useStore(form.store, (state) => state.values);
  const isSubmitting = useStore(form.store, (state) => state.isSubmitting);
  const [errors, setErrors] = useState<ValidationErrors>(EMPTY_ERRORS);
  const [columnsByTable, setColumnsByTable] = useState<
    Record<string, ColumnType[]>
  >({});
  const [loadingTables, setLoadingTables] = useState<Record<string, boolean>>(
    {},
  );

  const isOneSample = values.samples.length === 1;
  const showMu = isOneSample;
  const showPaired =
    values.testType === StatisticalTestTypeValues["t-test"] &&
    values.samples.length === 2;
  const showEqualVar =
    values.testType === StatisticalTestTypeValues["t-test"] &&
    values.samples.length === 2 &&
    !values.options.paired;
  const showConfidenceLevel =
    values.testType !== StatisticalTestTypeValues["f-test"];

  useEffect(() => {
    if (!workTabId) return;
    ensureWorkTabState(workTabId, values);
  }, [ensureWorkTabState, values, workTabId]);

  useEffect(() => {
    if (!workTabId) return;
    updateWorkTabDraft(workTabId, values);
  }, [updateWorkTabDraft, values, workTabId]);

  useEffect(() => {
    const missingTables = values.samples
      .map((sample) => sample.tableName)
      .filter(
        (tableName) =>
          tableName && !columnsByTable[tableName] && !loadingTables[tableName],
      );

    if (missingTables.length === 0) return;

    void Promise.all(
      [...new Set(missingTables)].map(async (tableName) => {
        setLoadingTables((prev) => ({ ...prev, [tableName]: true }));
        try {
          const response = await getEconomiconAppAPI().getColumnList({
            tableName,
            isNumberOnly: true,
          });
          if (response.code === "OK") {
            setColumnsByTable((prev) => ({
              ...prev,
              [tableName]: response.result.columnInfoList,
            }));
            return;
          }
        } catch {
          await showMessageDialog(
            t("Error.Error"),
            t("StatisticalTestView.ErrorLoadingColumns"),
          );
        } finally {
          setLoadingTables((prev) => ({ ...prev, [tableName]: false }));
        }
      }),
    );
  }, [columnsByTable, loadingTables, t, values.samples]);

  const handleCancel = () => {
    if (onCancel) {
      void onCancel();
      return;
    }
    navigateToWorkspace();
  };

  const clearErrors = () => {
    setErrors({
      sampleRows: {},
      options: {},
    });
  };

  const updateSamples = (nextSamples: SampleInput[]) => {
    clearErrors();
    form.setFieldValue("samples", nextSamples);
  };

  const handleTestTypeChange = (nextType: string) => {
    clearErrors();
    const typedNextType = nextType as StatisticalTestType;
    form.setFieldValue("testType", typedNextType);

    let nextSamples = values.samples;
    if (
      typedNextType === StatisticalTestTypeValues["f-test"] &&
      values.samples.length < 2
    ) {
      nextSamples = [
        ...values.samples,
        cloneSample(values.samples[0]?.tableName ?? initialTableName),
      ];
    }

    if (
      (typedNextType === StatisticalTestTypeValues["t-test"] ||
        typedNextType === StatisticalTestTypeValues["z-test"]) &&
      values.samples.length > 2
    ) {
      nextSamples = values.samples.slice(0, 2);
    }

    if (nextSamples !== values.samples) {
      form.setFieldValue("samples", nextSamples);
    }

    if (typedNextType !== StatisticalTestTypeValues["t-test"]) {
      form.setFieldValue("options.paired", false);
    }
  };

  const handleSampleTableChange = (index: number, tableName: string) => {
    const nextSamples = [...values.samples];
    nextSamples[index] = {
      tableName,
      columnName: "",
    };
    updateSamples(nextSamples);
  };

  const handleSampleColumnChange = (index: number, columnName: string) => {
    const nextSamples = [...values.samples];
    nextSamples[index] = {
      ...nextSamples[index],
      columnName,
    };
    updateSamples(nextSamples);
  };

  const addSample = () => {
    if (
      (values.testType === StatisticalTestTypeValues["t-test"] ||
        values.testType === StatisticalTestTypeValues["z-test"]) &&
      values.samples.length >= 2
    ) {
      return;
    }
    updateSamples([
      ...values.samples,
      cloneSample(values.samples.at(-1)?.tableName ?? initialTableName),
    ]);
  };

  const removeSample = (index: number) => {
    const minimumSamples =
      values.testType === StatisticalTestTypeValues["f-test"] ? 2 : 1;
    if (values.samples.length <= minimumSamples) return;
    updateSamples(
      values.samples.filter((_, sampleIndex) => sampleIndex !== index),
    );
  };

  const handleSubmit = async () => {
    clearErrors();

    const nextErrors: ValidationErrors = {
      sampleRows: {},
      options: {},
    };
    const requestBody = inferRequestBody(values, nextErrors, t);
    if (!requestBody) {
      setErrors(nextErrors);
      return;
    }

    const mappedErrors = mapValidationErrors(requestBody, t);
    if (hasValidationErrors(mappedErrors)) {
      setErrors(mappedErrors);
      return;
    }

    try {
      const api = getEconomiconAppAPI();
      const response = await api.statisticalTest(requestBody);
      if (response.code === "OK" && response.result) {
        const detailResponse = await api.getAnalysisResult(
          response.result.resultId,
        );
        if (detailResponse.code === "OK") {
          if (workTabId) {
            commitWorkTab(workTabId, values);
          }
          closeActiveWorkTab();
          openResultTab(detailResponse.result);
          await useAnalysisResultsStore.getState().fetchSummaries();
          return;
        }

        await showMessageDialog(
          t("Error.Error"),
          buildResponseErrorMessage(detailResponse, t("Error.UnexpectedError")),
        );
        return;
      }

      await showMessageDialog(
        t("Error.Error"),
        buildResponseErrorMessage(response, t("Error.UnexpectedError")),
      );
    } catch (error) {
      await showMessageDialog(
        t("Error.Error"),
        buildCaughtErrorMessage(error, t("Error.UnexpectedError")),
      );
    }
  };

  return (
    <PageLayout
      title={t("StatisticalTestView.Title")}
      description={t("StatisticalTestView.Description")}
    >
      {tableList.length === 0 ? (
        <AnalysisNoTablesState
          className="flex-1"
          onCancel={handleCancel}
          onSelect={() => navigateToShell("ImportDataFile")}
        />
      ) : (
        <form
          onSubmit={(event) => {
            event.preventDefault();
            event.stopPropagation();
            void handleSubmit();
          }}
          className="flex min-h-0 flex-1 flex-col gap-3"
        >
          <div className="app-scrollbar flex-1 space-y-3 overflow-y-auto pb-2">
            <section className="rounded-lg border border-border-color bg-white p-3 dark:border-gray-700 dark:bg-gray-800">
              <div className="grid gap-2 md:grid-cols-[minmax(0,1fr)_auto] md:items-end">
                <FormField
                  label={t("StatisticalTestView.TestTypeLabel")}
                  error={errors.testType}
                >
                  <Select
                    value={values.testType}
                    onValueChange={handleTestTypeChange}
                    placeholder={t("StatisticalTestView.TestTypeLabel")}
                  >
                    {TEST_TYPE_OPTIONS.map((testType) => (
                      <SelectItem key={testType} value={testType}>
                        {t(`StatisticalTestView.TestType_${testType}`)}
                      </SelectItem>
                    ))}
                  </Select>
                </FormField>
                <button
                  type="button"
                  onClick={addSample}
                  className={cn(
                    "inline-flex items-center justify-center gap-1 rounded-md border border-gray-300 px-2.5 py-1.5 text-xs font-medium text-gray-700 transition-colors hover:bg-gray-50 dark:border-gray-600 dark:text-gray-200 dark:hover:bg-gray-700 md:min-w-32",
                    (values.testType === StatisticalTestTypeValues["t-test"] ||
                      values.testType ===
                        StatisticalTestTypeValues["z-test"]) &&
                      values.samples.length >= 2 &&
                      "cursor-not-allowed opacity-50",
                  )}
                  disabled={
                    (values.testType === StatisticalTestTypeValues["t-test"] ||
                      values.testType ===
                        StatisticalTestTypeValues["z-test"]) &&
                    values.samples.length >= 2
                  }
                  data-testid="statistical-test-add-sample"
                >
                  <Plus className="h-3.5 w-3.5" />
                  {t("StatisticalTestView.AddSample")}
                </button>
              </div>
              <p className="mt-2 text-xs text-brand-text-sub dark:text-gray-400">
                {t(`StatisticalTestView.SamplesHint_${values.testType}`)}
              </p>
            </section>

            <section className="space-y-2.5 rounded-lg border border-border-color bg-white p-3 dark:border-gray-700 dark:bg-gray-800">
              <div className="flex items-center justify-between gap-3">
                <h3 className="text-sm font-semibold text-brand-text-main dark:text-gray-100">
                  {t("StatisticalTestView.SamplesLabel")}
                </h3>
              </div>

              {values.samples.map((sample, index) => {
                const rowErrors = errors.sampleRows[index] ?? {};
                const numericColumns = columnsByTable[sample.tableName] ?? [];
                const isLoadingColumns =
                  sample.tableName !== "" && loadingTables[sample.tableName];
                const minimumSamples =
                  values.testType === StatisticalTestTypeValues["f-test"]
                    ? 2
                    : 1;

                return (
                  <div
                    key={`${index}:${sample.tableName}:${sample.columnName}`}
                    className="space-y-2 rounded-md border border-gray-200 p-2.5 dark:border-gray-700"
                    data-testid={`statistical-test-sample-${index}`}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <h4 className="text-sm font-medium text-gray-800 dark:text-gray-100">
                        {t("StatisticalTestView.SampleTitle", {
                          number: index + 1,
                        })}
                      </h4>
                      <button
                        type="button"
                        onClick={() => removeSample(index)}
                        disabled={values.samples.length <= minimumSamples}
                        className={cn(
                          "inline-flex items-center gap-1 rounded-md border border-gray-300 px-2 py-1 text-[11px] font-medium text-gray-700 transition-colors hover:bg-gray-50 dark:border-gray-600 dark:text-gray-200 dark:hover:bg-gray-700",
                          values.samples.length <= minimumSamples &&
                            "cursor-not-allowed opacity-50",
                        )}
                        data-testid={`statistical-test-remove-sample-${index}`}
                      >
                        <Minus className="h-3.5 w-3.5" />
                        {t("StatisticalTestView.RemoveSample")}
                      </button>
                    </div>

                    <div className="grid gap-2 md:grid-cols-2">
                      <FormField
                        label={t("StatisticalTestView.DataLabel")}
                        error={rowErrors.tableName}
                      >
                        <Select
                          value={sample.tableName}
                          onValueChange={(value) =>
                            handleSampleTableChange(index, value)
                          }
                          placeholder={t("StatisticalTestView.SelectData")}
                        >
                          {tableList.map((tableName) => (
                            <SelectItem key={tableName} value={tableName}>
                              {tableName}
                            </SelectItem>
                          ))}
                        </Select>
                      </FormField>

                      <FormField
                        label={t("StatisticalTestView.ColumnLabel")}
                        error={rowErrors.columnName}
                      >
                        {sample.tableName !== "" && isLoadingColumns ? (
                          <AnalysisEmptyState
                            compact
                            testId={`statistical-test-loading-columns-state-${index}`}
                            icon={<Loader2 className="h-6 w-6 animate-spin" />}
                            title={t("AnalysisEmptyState.LoadingColumnsTitle")}
                            description={t(
                              "AnalysisEmptyState.LoadingColumnsDescription",
                            )}
                          />
                        ) : sample.tableName !== "" &&
                          numericColumns.length === 0 ? (
                          <AnalysisEmptyState
                            compact
                            testId={`statistical-test-no-columns-state-${index}`}
                            icon={<SearchX className="h-6 w-6" />}
                            title={t(
                              "AnalysisEmptyState.NoEligibleColumnsTitle",
                            )}
                            description={t("StatisticalTestView.NoColumns")}
                            hint={t("AnalysisEmptyState.NoEligibleColumnsHint")}
                          />
                        ) : (
                          <Select
                            value={sample.columnName}
                            onValueChange={(value) =>
                              handleSampleColumnChange(index, value)
                            }
                            placeholder={t("StatisticalTestView.SelectColumn")}
                            disabled={
                              sample.tableName === "" || isLoadingColumns
                            }
                          >
                            {numericColumns.map((column) => (
                              <SelectItem key={column.name} value={column.name}>
                                {column.name}
                              </SelectItem>
                            ))}
                          </Select>
                        )}
                      </FormField>
                    </div>
                  </div>
                );
              })}

              {errors.samples && (
                <p className="text-xs text-red-600 dark:text-red-400">
                  {errors.samples}
                </p>
              )}
            </section>

            <section className="space-y-2.5 rounded-lg border border-border-color bg-white p-3 dark:border-gray-700 dark:bg-gray-800">
              <h3 className="text-sm font-semibold text-brand-text-main dark:text-gray-100">
                {t("StatisticalTestView.OptionsLabel")}
              </h3>

              <div className="grid gap-2 md:grid-cols-2">
                <FormField label={t("StatisticalTestView.AlternativeLabel")}>
                  <Select
                    value={values.options.alternative}
                    onValueChange={(value) => {
                      clearErrors();
                      form.setFieldValue(
                        "options.alternative",
                        value as AlternativeHypothesis,
                      );
                    }}
                  >
                    {ALTERNATIVE_OPTIONS.map((alternative) => (
                      <SelectItem key={alternative} value={alternative}>
                        {t(`StatisticalTestView.Alternative_${alternative}`)}
                      </SelectItem>
                    ))}
                  </Select>
                </FormField>

                {showConfidenceLevel && (
                  <FormField
                    label={t("StatisticalTestView.ConfidenceLevelLabel")}
                    error={errors.options.confidenceLevel}
                  >
                    <InputText
                      value={values.options.confidenceLevel}
                      onChange={(event) => {
                        clearErrors();
                        form.setFieldValue(
                          "options.confidenceLevel",
                          event.target.value,
                        );
                      }}
                      type="number"
                      step="0.01"
                      inputMode="decimal"
                      data-testid="statistical-test-confidence-level"
                    />
                  </FormField>
                )}
              </div>

              {showMu && (
                <FormField
                  label={t("StatisticalTestView.MuLabel")}
                  error={errors.options.mu}
                >
                  <InputText
                    value={values.options.mu}
                    onChange={(event) => {
                      clearErrors();
                      form.setFieldValue("options.mu", event.target.value);
                    }}
                    type="number"
                    step="any"
                    inputMode="decimal"
                    data-testid="statistical-test-mu"
                  />
                  <p className="mt-1 text-xs text-brand-text-sub dark:text-gray-400">
                    {t("StatisticalTestView.MuHint")}
                  </p>
                </FormField>
              )}

              {(showPaired || showEqualVar) && (
                <div className="grid gap-2 md:grid-cols-2">
                  {showPaired && (
                    <div className="space-y-0.5 rounded-md border border-border-color/70 bg-secondary/30 px-3 py-2">
                      <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-200">
                        <input
                          type="checkbox"
                          checked={values.options.paired}
                          onChange={(event) => {
                            clearErrors();
                            form.setFieldValue(
                              "options.paired",
                              event.target.checked,
                            );
                          }}
                          className="h-4 w-4 rounded border-gray-300 accent-brand-accent"
                          data-testid="statistical-test-paired"
                        />
                        {t("StatisticalTestView.PairedLabel")}
                      </label>
                      <p className="text-xs text-brand-text-sub dark:text-gray-400">
                        {errors.options.paired ??
                          t("StatisticalTestView.PairedHint")}
                      </p>
                    </div>
                  )}

                  {showEqualVar && (
                    <div className="space-y-0.5 rounded-md border border-border-color/70 bg-secondary/30 px-3 py-2">
                      <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-200">
                        <input
                          type="checkbox"
                          checked={values.options.equalVar}
                          onChange={(event) => {
                            clearErrors();
                            form.setFieldValue(
                              "options.equalVar",
                              event.target.checked,
                            );
                          }}
                          className="h-4 w-4 rounded border-gray-300 accent-brand-accent"
                          data-testid="statistical-test-equal-var"
                        />
                        {t("StatisticalTestView.EqualVarLabel")}
                      </label>
                      <p className="text-xs text-brand-text-sub dark:text-gray-400">
                        {t("StatisticalTestView.EqualVarHint")}
                      </p>
                    </div>
                  )}
                </div>
              )}
            </section>
          </div>

          <ActionButtonBar
            cancelText={t("Common.Cancel")}
            selectText={
              isSubmitting
                ? t("StatisticalTestView.Processing")
                : t("StatisticalTestView.RunTest")
            }
            onCancel={handleCancel}
            onSelect={() => {}}
            onSelectType="submit"
            isLoading={isSubmitting}
          />
        </form>
      )}
    </PageLayout>
  );
};
