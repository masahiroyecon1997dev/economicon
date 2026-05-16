import {
  addSimulationColumnBodySimulationColumnColumnNameMax,
  addSimulationColumnBodySimulationColumnColumnNameRegExp,
} from "@/api/zod/column/column";
import { InputText } from "@/components/atoms/Input/InputText";
import { RadioTagGroup } from "@/components/molecules/Field/RadioTagGroup";
import { FormField } from "@/components/molecules/Form/FormField";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/organisms/Tab/BaseTab";
import {
  CONTINUOUS_DIST_TYPES,
  DETERMINISTIC_DIST_TYPES,
  DISCRETE_DIST_TYPES,
  DIST_PARAM_DEFAULTS,
  DIST_PARAM_LABEL_KEYS,
  DIST_PARAM_SCHEMAS,
  DIST_PARAMS,
  getDistributionCategory,
} from "@/constants/simulation";
import { extractFieldError } from "@/lib/utils/formHelpers";
import type {
  DistributionType,
  SimulationColumnSetting,
} from "@/types/commonTypes";
import { useForm, useStore } from "@tanstack/react-form";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { z } from "zod";

type SimulationColumnConfigProps = {
  formId: string;
  column: SimulationColumnSetting;
  onSaved: (updates: Partial<SimulationColumnSetting>) => void;
  disabled?: boolean;
};

/** 全分布で使用しうるパラメータキー */
type ParamKey = [
  "low",
  "high",
  "scaleParameter",
  "mean",
  "standardDeviation",
  "shapeParameter",
  "alpha",
  "beta",
  "logMean",
  "logStandardDeviation",
  "trialCount",
  "successProbability",
  "rate",
  "populationSize",
  "successCount",
  "sampleSize",
  "targetSuccessCount",
  "start",
  "step",
  "value",
][number];

type DistributionTab = "continuous" | "discrete" | "deterministic";

const getInitialTab = (distributionType: DistributionType): DistributionTab => {
  switch (getDistributionCategory(distributionType)) {
    case "continuous":
      return "continuous";
    case "discrete":
      return "discrete";
    case "deterministic":
      return "deterministic";
  }
};

export const SimulationColumnConfig = ({
  formId,
  column,
  onSaved,
  disabled = false,
}: SimulationColumnConfigProps) => {
  const { t } = useTranslation();
  const [paramsError, setParamsError] = useState<Record<string, string>>({});

  const currentDistType: DistributionType =
    column.dataType === "fixed"
      ? "fixed"
      : (column.distributionType ?? "uniform");

  const [distributionTab, setDistributionTab] = useState<DistributionTab>(
    getInitialTab(currentDistType),
  );

  const initParam = (key: string): string => {
    if (column.distributionParams?.[key] !== undefined) {
      return String(column.distributionParams[key]);
    }
    const d = DIST_PARAM_DEFAULTS[currentDistType];
    if (d?.[key] !== undefined) return String(d[key]);
    return "0";
  };

  const form = useForm({
    defaultValues: {
      columnName: column.columnName,
      dataType: column.dataType,
      distributionType: currentDistType as DistributionType,
      // 全パラメータをフラット文字列で保持
      low: initParam("low"),
      high: initParam("high"),
      scaleParameter: initParam("scaleParameter"),
      mean: initParam("mean"),
      standardDeviation: initParam("standardDeviation"),
      shapeParameter: initParam("shapeParameter"),
      alpha: initParam("alpha"),
      beta: initParam("beta"),
      logMean: initParam("logMean"),
      logStandardDeviation: initParam("logStandardDeviation"),
      trialCount: initParam("trialCount"),
      successProbability: initParam("successProbability"),
      rate: initParam("rate"),
      populationSize: initParam("populationSize"),
      successCount: initParam("successCount"),
      sampleSize: initParam("sampleSize"),
      targetSuccessCount: initParam("targetSuccessCount"),
      start: initParam("start"),
      step: initParam("step"),
      value:
        column.dataType === "fixed" ? String(column.fixedValue || "0") : "0",
    },
    onSubmit: ({ value }) => {
      setParamsError({});

      const selectedType = value.distributionType as DistributionType;

      if (selectedType !== "fixed") {
        const paramNames = DIST_PARAMS[selectedType];
        const errors: Record<string, string> = {};
        for (const param of paramNames) {
          const result = DIST_PARAM_SCHEMAS[param]().safeParse(
            value[param as keyof typeof value] as string,
          );
          if (!result.success) {
            errors[param] = result.error.issues[0]?.message ?? "";
          }
        }
        if (Object.keys(errors).length > 0) {
          setParamsError(errors);
          return;
        }
        const distributionParams = Object.fromEntries(
          paramNames.map((p) => [p, Number(value[p as keyof typeof value])]),
        );
        onSaved({
          columnName: value.columnName,
          dataType: "distribution",
          distributionType: selectedType,
          distributionParams,
          fixedValue: "",
        });
      } else {
        const result = DIST_PARAM_SCHEMAS["value"]().safeParse(value.value);
        if (!result.success) {
          setParamsError({ value: result.error.issues[0]?.message ?? "" });
          return;
        }
        onSaved({
          columnName: value.columnName,
          dataType: "fixed",
          distributionType: undefined,
          distributionParams: undefined,
          fixedValue: Number(value.value),
        });
      }
    },
  });

  const distributionType = useStore(
    form.store,
    (s) => s.values.distributionType,
  ) as DistributionType;

  const handleDistributionTypeChange = (newType: DistributionType) => {
    form.setFieldValue("distributionType", newType);
    form.setFieldValue(
      "dataType",
      newType === "fixed" ? "fixed" : "distribution",
    );
    setParamsError({});
    const defaults = DIST_PARAM_DEFAULTS[newType];
    for (const p of DIST_PARAMS[newType]) {
      form.setFieldValue(p as ParamKey, String(defaults[p] ?? "0"));
    }
  };

  const handleTabChange = (tab: DistributionTab) => {
    setDistributionTab(tab);
    setParamsError({});
    const typesByTab: Record<DistributionTab, DistributionType[]> = {
      continuous: CONTINUOUS_DIST_TYPES,
      discrete: DISCRETE_DIST_TYPES,
      deterministic: DETERMINISTIC_DIST_TYPES,
    };
    const candidateTypes = typesByTab[tab];
    const nextType = candidateTypes.includes(distributionType)
      ? distributionType
      : candidateTypes[0];

    handleDistributionTypeChange(nextType);
  };

  return (
    <form
      id={formId}
      onSubmit={(e) => {
        e.preventDefault();
        e.stopPropagation();
        void form.handleSubmit();
      }}
      className="space-y-4"
    >
      {/* 列名 */}
      <form.Field
        name="columnName"
        validators={{
          onSubmit: z
            .string()
            .min(1, t("ValidationMessages.ColumnNameRequired"))
            .max(
              addSimulationColumnBodySimulationColumnColumnNameMax,
              t("ValidationMessages.DataNameTooLong"),
            )
            .regex(
              addSimulationColumnBodySimulationColumnColumnNameRegExp,
              t("ValidationMessages.DataNameInvalidChars"),
            ),
        }}
      >
        {(field) => (
          <FormField
            label={t("CreateSimulationDataTableView.ColumnName")}
            htmlFor={`${formId}-column-name`}
            error={extractFieldError(field.state.meta.errors)}
          >
            <InputText
              id={`${formId}-column-name`}
              value={field.state.value}
              onChange={(e) => field.handleChange(e.target.value)}
              onBlur={field.handleBlur}
              disabled={disabled}
              autoFocus
              error={extractFieldError(field.state.meta.errors)}
            />
          </FormField>
        )}
      </form.Field>

      {/* 連続 / 離散 / 決定的系列 タブ */}
      <Tabs
        value={distributionTab}
        onValueChange={(v) => handleTabChange(v as DistributionTab)}
      >
        <TabsList>
          <TabsTrigger value="continuous" disabled={disabled}>
            {t("AddSimulationColumnForm.TabContinuous")}
          </TabsTrigger>
          <TabsTrigger value="discrete" disabled={disabled}>
            {t("AddSimulationColumnForm.TabDiscrete")}
          </TabsTrigger>
          <TabsTrigger value="deterministic" disabled={disabled}>
            {t("AddSimulationColumnForm.TabDeterministic")}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="continuous" className="pt-3">
          <FormField
            label={t("CreateSimulationDataTableView.DistributionType")}
          >
            <RadioTagGroup
              name={`${formId}-dist-type`}
              items={CONTINUOUS_DIST_TYPES.map((dt) => ({
                value: dt,
                label: t(`AddSimulationColumnForm.${dt}`),
              }))}
              value={distributionType}
              onChange={(v) =>
                handleDistributionTypeChange(v as DistributionType)
              }
              disabled={disabled}
            />
          </FormField>
        </TabsContent>

        <TabsContent value="discrete" className="pt-3">
          <FormField
            label={t("CreateSimulationDataTableView.DistributionType")}
          >
            <RadioTagGroup
              name={`${formId}-dist-type`}
              items={DISCRETE_DIST_TYPES.map((dt) => ({
                value: dt,
                label: t(`AddSimulationColumnForm.${dt}`),
              }))}
              value={distributionType}
              onChange={(v) =>
                handleDistributionTypeChange(v as DistributionType)
              }
              disabled={disabled}
            />
          </FormField>
        </TabsContent>

        <TabsContent value="deterministic" className="pt-3">
          <FormField
            label={t("CreateSimulationDataTableView.DistributionType")}
          >
            <RadioTagGroup
              name={`${formId}-dist-type`}
              items={DETERMINISTIC_DIST_TYPES.map((dt) => ({
                value: dt,
                label: t(`AddSimulationColumnForm.${dt}`),
              }))}
              value={distributionType}
              onChange={(v) =>
                handleDistributionTypeChange(v as DistributionType)
              }
              disabled={disabled}
            />
          </FormField>
        </TabsContent>
      </Tabs>

      {/* 分布パラメータ */}
      {distributionType !== "fixed" &&
        DIST_PARAMS[distributionType].map((param) => (
          <form.Field
            key={`${distributionType}-${param}`}
            name={param as ParamKey}
          >
            {(field) => (
              <FormField
                label={t(DIST_PARAM_LABEL_KEYS[param])}
                htmlFor={`${formId}-param-${param}`}
                error={paramsError[param]}
              >
                <InputText
                  id={`${formId}-param-${param}`}
                  type="number"
                  value={field.state.value as string}
                  onChange={(e) => field.handleChange(e.target.value as never)}
                  onBlur={field.handleBlur}
                  disabled={disabled}
                  step={
                    param === "trialCount" ||
                    param === "populationSize" ||
                    param === "successCount" ||
                    param === "sampleSize" ||
                    param === "targetSuccessCount"
                      ? 1
                      : "any"
                  }
                  error={paramsError[param]}
                />
              </FormField>
            )}
          </form.Field>
        ))}

      {/* 固定値 */}
      {distributionType === "fixed" && (
        <form.Field name="value">
          {(field) => (
            <FormField
              label={t("CreateSimulationDataTableView.FixedValue")}
              htmlFor={`${formId}-fixed-value`}
              error={paramsError["value"]}
            >
              <InputText
                id={`${formId}-fixed-value`}
                type="number"
                value={field.state.value as string}
                onChange={(e) => field.handleChange(e.target.value as never)}
                onBlur={field.handleBlur}
                disabled={disabled}
                step="any"
                error={paramsError["value"]}
              />
            </FormField>
          )}
        </form.Field>
      )}
    </form>
  );
};
