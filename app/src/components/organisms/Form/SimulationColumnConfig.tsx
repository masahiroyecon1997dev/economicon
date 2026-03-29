import { useForm, useStore } from "@tanstack/react-form";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { z } from "zod";
import {
  addSimulationColumnBodySimulationColumnColumnNameMax,
  addSimulationColumnBodySimulationColumnColumnNameRegExp,
} from "../../../api/zod/column/column";
import {
  DIST_PARAM_DEFAULTS,
  DIST_PARAM_LABEL_KEYS,
  DIST_PARAM_SCHEMAS,
  DIST_PARAMS,
  DIST_TYPES,
} from "../../../constants/simulation";
import { extractFieldError } from "../../../lib/utils/formHelpers";
import type {
  DistributionType,
  SimulationColumnSetting,
} from "../../../types/commonTypes";
import { InputText } from "../../atoms/Input/InputText";
import { Select, SelectItem } from "../../atoms/Input/Select";
import { RadioTagGroup } from "../../molecules/Field/RadioTagGroup";
import { FormField } from "../../molecules/Form/FormField";

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
  "scale",
  "loc",
  "shape",
  "a",
  "b",
  "mean",
  "sigma",
  "n",
  "p",
  "lam",
  "populationSize",
  "successCount",
  "sampleSize",
  "value",
][number];

export const SimulationColumnConfig = ({
  formId,
  column,
  onSaved,
  disabled = false,
}: SimulationColumnConfigProps) => {
  const { t } = useTranslation();
  const [paramsError, setParamsError] = useState<Record<string, string>>({});

  const currentDistType = column.distributionType ?? "uniform";

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
      scale: initParam("scale"),
      loc: initParam("loc"),
      shape: initParam("shape"),
      a: initParam("a"),
      b: initParam("b"),
      mean: initParam("mean"),
      sigma: initParam("sigma"),
      n: initParam("n"),
      p: initParam("p"),
      lam: initParam("lam"),
      populationSize: initParam("populationSize"),
      successCount: initParam("successCount"),
      sampleSize: initParam("sampleSize"),
      value:
        column.dataType === "fixed" ? String(column.fixedValue || "0") : "0",
    },
    onSubmit: ({ value }) => {
      setParamsError({});

      if (value.dataType === "distribution") {
        const paramNames =
          DIST_PARAMS[value.distributionType as DistributionType];
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
          distributionType: value.distributionType as DistributionType,
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

  const dataType = useStore(form.store, (s) => s.values.dataType);
  const distributionType = useStore(
    form.store,
    (s) => s.values.distributionType,
  ) as DistributionType;

  const handleDistributionTypeChange = (newType: DistributionType) => {
    form.setFieldValue("distributionType", newType);
    setParamsError({});
    const defaults = DIST_PARAM_DEFAULTS[newType];
    for (const p of DIST_PARAMS[newType]) {
      form.setFieldValue(p as ParamKey, String(defaults[p] ?? "0"));
    }
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
            />
          </FormField>
        )}
      </form.Field>

      {/* データタイプ */}
      <form.Field name="dataType">
        {(field) => (
          <FormField
            label={t("CreateSimulationDataTableView.DataType")}
            htmlFor={`${formId}-data-type`}
          >
            <Select
              id={`${formId}-data-type`}
              value={field.state.value}
              onValueChange={(v) => {
                field.handleChange(v as "distribution" | "fixed");
                setParamsError({});
              }}
              disabled={disabled}
            >
              <SelectItem value="distribution">
                {t("Common.Distribution")}
              </SelectItem>
              <SelectItem value="fixed">{t("Common.Constant")}</SelectItem>
            </Select>
          </FormField>
        )}
      </form.Field>

      {/* 分布の種類（distribution 時のみ） */}
      {dataType === "distribution" && (
        <FormField label={t("CreateSimulationDataTableView.DistributionType")}>
          <RadioTagGroup
            name={`${formId}-dist-type`}
            items={DIST_TYPES.filter((d) => d !== "fixed").map((dt) => ({
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
      )}

      {/* 分布パラメータ（distribution 時） */}
      {dataType === "distribution" &&
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
                    param === "n" ||
                    param === "populationSize" ||
                    param === "successCount" ||
                    param === "sampleSize"
                      ? 1
                      : "any"
                  }
                  error={paramsError[param]}
                />
              </FormField>
            )}
          </form.Field>
        ))}

      {/* 固定値（fixed 時） */}
      {dataType === "fixed" && (
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
