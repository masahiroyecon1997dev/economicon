/**
 * シミュレーション列追加フォーム
 *
 * POST /api/column/add-simulation をコールし、
 * 選択した確率分布からランダム値を持つ列をテーブルに追加する。
 */
import { useForm, useStore } from "@tanstack/react-form";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { z } from "zod";
import { getEconomiconAppAPI } from "../../../../api/endpoints";
import {
  addSimulationColumnBodySimulationColumnColumnNameMax,
  addSimulationColumnBodySimulationColumnColumnNameRegExp,
} from "../../../../api/zod/column/column";
import {
  extractApiErrorMessage,
  getResponseErrorMessage,
  replaceParamNames,
} from "../../../../lib/utils/apiError";
import { extractFieldError } from "../../../../lib/utils/formHelpers";
import { InputText } from "../../../atoms/Input/InputText";
import { Select, SelectItem } from "../../../atoms/Input/Select";
import { ErrorAlert } from "../../../molecules/Alert/ErrorAlert";
import { FormField } from "../../../molecules/Form/FormField";
import { RandomSeedField } from "../../../molecules/Form/RandomSeedField";
import { fetchUpdatedColumnList } from "./fetchUpdatedColumnList";
import type { ColumnOperationFormPropsType } from "./types";

// -----------------------------------------------------------------------
// 型定義
// -----------------------------------------------------------------------
type DistributionType =
  | "uniform"
  | "exponential"
  | "normal"
  | "gamma"
  | "beta"
  | "weibull"
  | "lognormal"
  | "binomial"
  | "bernoulli"
  | "poisson"
  | "geometric"
  | "hypergeometric"
  | "negative_binomial"
  | "fixed";

const DISTRIBUTION_TYPES: DistributionType[] = [
  "uniform",
  "exponential",
  "normal",
  "gamma",
  "beta",
  "weibull",
  "lognormal",
  "binomial",
  "bernoulli",
  "poisson",
  "geometric",
  "hypergeometric",
  "negative_binomial",
  "fixed",
];

/** 各分布で使用するパラメータ名の一覧 */
const DIST_PARAMS: Record<DistributionType, string[]> = {
  uniform: ["low", "high"],
  exponential: ["scale"],
  normal: ["loc", "scale"],
  gamma: ["shape", "scale"],
  beta: ["a", "b"],
  weibull: ["a", "scale"],
  lognormal: ["mean", "sigma"],
  binomial: ["n", "p"],
  bernoulli: ["p"],
  poisson: ["lam"],
  geometric: ["p"],
  hypergeometric: ["populationSize", "successCount", "sampleSize"],
  negative_binomial: ["n", "p"],
  fixed: ["value"],
};

/** i18n キー名への対応 */
const PARAM_LABEL_KEY: Record<string, string> = {
  low: "AddSimulationColumnForm.Low",
  high: "AddSimulationColumnForm.High",
  scale: "AddSimulationColumnForm.Scale",
  loc: "AddSimulationColumnForm.Loc",
  shape: "AddSimulationColumnForm.Shape",
  a: "AddSimulationColumnForm.A",
  b: "AddSimulationColumnForm.B",
  mean: "AddSimulationColumnForm.Mean",
  sigma: "AddSimulationColumnForm.Sigma",
  n: "AddSimulationColumnForm.N",
  p: "AddSimulationColumnForm.P",
  lam: "AddSimulationColumnForm.Lam",
  populationSize: "AddSimulationColumnForm.PopulationSize",
  successCount: "AddSimulationColumnForm.SuccessCount",
  sampleSize: "AddSimulationColumnForm.SampleSize",
  value: "AddSimulationColumnForm.Value",
};

// -----------------------------------------------------------------------
// バリデーション用ヘルパー
// -----------------------------------------------------------------------
const gtZeroNum = () =>
  z
    .string()
    .refine(
      (v) => !isNaN(Number(v)) && Number(v) > 0,
      "0 より大きい数値を入力してください。",
    );

const probability = () =>
  z
    .string()
    .refine(
      (v) => !isNaN(Number(v)) && Number(v) > 0 && Number(v) <= 1,
      "0 を超え 1 以下の数値を入力してください。",
    );

const anyNum = () =>
  z.string().refine((v) => !isNaN(Number(v)), "数値を入力してください。");

const gtZeroInt = () =>
  z
    .string()
    .refine(
      (v) => !isNaN(Number(v)) && Number(v) > 0 && Number.isInteger(Number(v)),
      "1 以上の整数を入力してください。",
    );

const PARAM_SCHEMAS: Record<string, () => z.ZodTypeAny> = {
  low: anyNum,
  high: anyNum,
  scale: gtZeroNum,
  loc: anyNum,
  shape: gtZeroNum,
  a: gtZeroNum,
  b: gtZeroNum,
  mean: anyNum,
  sigma: gtZeroNum,
  n: gtZeroInt,
  p: probability,
  lam: gtZeroNum,
  populationSize: gtZeroInt,
  successCount: gtZeroInt,
  sampleSize: gtZeroInt,
  value: anyNum,
};

// -----------------------------------------------------------------------
// 分布オブジェクト組み立て
// -----------------------------------------------------------------------
type ParamValues = Record<string, string>;

const buildDistribution = (type: DistributionType, params: ParamValues) => {
  const toNum = (k: string) => Number(params[k]);
  switch (type) {
    case "uniform":
      return { type, low: toNum("low"), high: toNum("high") };
    case "exponential":
      return { type, scale: toNum("scale") };
    case "normal":
      return { type, loc: toNum("loc"), scale: toNum("scale") };
    case "gamma":
      return { type, shape: toNum("shape"), scale: toNum("scale") };
    case "beta":
      return { type, a: toNum("a"), b: toNum("b") };
    case "weibull":
      return { type, a: toNum("a"), scale: toNum("scale") };
    case "lognormal":
      return { type, mean: toNum("mean"), sigma: toNum("sigma") };
    case "binomial":
      return { type, n: toNum("n"), p: toNum("p") };
    case "bernoulli":
      return { type, p: toNum("p") };
    case "poisson":
      return { type, lam: toNum("lam") };
    case "geometric":
      return { type, p: toNum("p") };
    case "hypergeometric":
      return {
        type,
        populationSize: toNum("populationSize"),
        successCount: toNum("successCount"),
        sampleSize: toNum("sampleSize"),
      };
    case "negative_binomial":
      return { type, n: toNum("n"), p: toNum("p") };
    case "fixed":
      return { type, value: toNum("value") };
  }
};

// -----------------------------------------------------------------------
// フォームコンポーネント
// -----------------------------------------------------------------------
export const AddSimulationColumnForm = ({
  tableName,
  column,
  formId,
  onIsSubmittingChange,
  onSuccess,
}: ColumnOperationFormPropsType) => {
  const { t } = useTranslation();
  const [apiError, setApiError] = useState<string | null>(null);

  const form = useForm({
    defaultValues: {
      columnName: `sim_${column.name}`,
      distributionType: "normal" as DistributionType,
      randomSeed: "",
      // 全パラメータをフラットに保持（使わないものはサブミット時に無視）
      low: "0",
      high: "1",
      scale: "1",
      loc: "0",
      shape: "1",
      a: "1",
      b: "1",
      mean: "0",
      sigma: "1",
      n: "10",
      p: "0.5",
      lam: "1",
      populationSize: "100",
      successCount: "50",
      sampleSize: "10",
      value: "0",
    },
    onSubmit: async ({ value }) => {
      setApiError(null);

      // 現在の分布タイプのパラメータのみバリデーション
      const paramNames = DIST_PARAMS[value.distributionType];
      for (const param of paramNames) {
        const result = PARAM_SCHEMAS[param]().safeParse(
          value[param as keyof typeof value],
        );
        if (!result.success) {
          setApiError(
            `${t(PARAM_LABEL_KEY[param])}: ${result.error.issues[0]?.message ?? t("Error.UnexpectedError")}`,
          );
          return;
        }
      }

      // randomSeed バリデーション
      const rawSeed = value.randomSeed;
      if (
        rawSeed !== "" &&
        (isNaN(Number(rawSeed)) ||
          !Number.isInteger(Number(rawSeed)) ||
          Number(rawSeed) < 0 ||
          Number(rawSeed) > 100_000_000)
      ) {
        setApiError(t("ValidationMessages.RandomSeedRange"));
        return;
      }

      try {
        const paramValues: ParamValues = {};
        for (const p of paramNames) {
          paramValues[p] = value[p as keyof typeof value] as string;
        }

        const response = await getEconomiconAppAPI().addSimulationColumn({
          tableName,
          simulationColumn: {
            columnName: value.columnName,
            distribution: buildDistribution(
              value.distributionType,
              paramValues,
            ),
          },
          addPositionColumn: column.name,
          randomSeed: value.randomSeed !== "" ? Number(value.randomSeed) : null,
        });

        if (response.code === "OK") {
          const updatedList = await fetchUpdatedColumnList(tableName);
          onSuccess(updatedList);
        } else {
          setApiError(
            replaceParamNames(
              getResponseErrorMessage(response, t("Error.UnexpectedError")),
              {
                columnName: t("AddSimulationColumnForm.ColumnName"),
              },
            ),
          );
        }
      } catch (error) {
        setApiError(
          replaceParamNames(
            extractApiErrorMessage(error, t("Error.UnexpectedError")),
            {
              columnName: t("AddSimulationColumnForm.ColumnName"),
            },
          ),
        );
      }
    },
  });

  const isSubmitting = useStore(form.store, (s) => s.isSubmitting);
  const distributionType = useStore(
    form.store,
    (s) => s.values.distributionType,
  );
  useEffect(() => {
    onIsSubmittingChange(isSubmitting);
  }, [isSubmitting, onIsSubmittingChange]);

  const currentParams = DIST_PARAMS[distributionType];

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
          onBlur: z
            .string()
            .min(1, t("ValidationMessages.NewColumnNameRequired"))
            .max(addSimulationColumnBodySimulationColumnColumnNameMax)
            .regex(addSimulationColumnBodySimulationColumnColumnNameRegExp),
        }}
      >
        {(field) => (
          <FormField
            label={t("AddSimulationColumnForm.ColumnName")}
            htmlFor="sim-column-name"
            error={extractFieldError(field.state.meta.errors)}
          >
            <InputText
              id="sim-column-name"
              value={field.state.value}
              onChange={(e) => field.handleChange(e.target.value)}
              onBlur={field.handleBlur}
              placeholder={t("AddSimulationColumnForm.ColumnNamePlaceholder")}
              disabled={isSubmitting}
              autoFocus
            />
          </FormField>
        )}
      </form.Field>

      {/* 分布の種類 */}
      <form.Field name="distributionType">
        {(field) => (
          <FormField
            label={t("AddSimulationColumnForm.DistributionType")}
            htmlFor="sim-dist-type"
          >
            <Select
              id="sim-dist-type"
              value={field.state.value}
              onValueChange={(v) => {
                field.handleChange(v as DistributionType);
              }}
              disabled={isSubmitting}
            >
              {DISTRIBUTION_TYPES.map((dt) => (
                <SelectItem key={dt} value={dt}>
                  {t(`AddSimulationColumnForm.${dt}`)}
                </SelectItem>
              ))}
            </Select>
          </FormField>
        )}
      </form.Field>

      {/* 分布パラメータ（動的） */}
      {currentParams.map((param) => (
        <form.Field
          key={`${distributionType}-${param}`}
          name={param as keyof typeof form.state.values}
        >
          {(field) => (
            <FormField
              label={t(PARAM_LABEL_KEY[param])}
              htmlFor={`sim-param-${param}`}
            >
              <InputText
                id={`sim-param-${param}`}
                type="number"
                value={field.state.value as string}
                onChange={(e) => field.handleChange(e.target.value as never)}
                onBlur={field.handleBlur}
                disabled={isSubmitting}
                step={
                  param === "n" ||
                  param === "populationSize" ||
                  param === "successCount" ||
                  param === "sampleSize"
                    ? 1
                    : "any"
                }
              />
            </FormField>
          )}
        </form.Field>
      ))}

      {/* 乱数シード（省略可） */}
      <form.Field name="randomSeed">
        {(field) => (
          <RandomSeedField
            id="sim-col-random-seed"
            value={field.state.value as string}
            onChange={(v) => field.handleChange(v as never)}
            onBlur={field.handleBlur}
            disabled={isSubmitting}
          />
        )}
      </form.Field>

      {apiError && <ErrorAlert message={apiError} />}
    </form>
  );
};
