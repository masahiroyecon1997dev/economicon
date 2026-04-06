/**
 * シミュレーション列追加フォーム
 *
 * POST /api/column/add-simulation をコールし、
 * 選択した確率分布からランダム値を持つ列をテーブルに追加する。
 */
import { useForm, useStore } from "@tanstack/react-form";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { z } from "zod";
import { getEconomiconAppAPI } from "@/api/endpoints";
import {
  addSimulationColumnBodySimulationColumnColumnNameMax,
  addSimulationColumnBodySimulationColumnColumnNameRegExp,
} from "@/api/zod/column/column";
import {
  buildDistributionFromParams,
  DIST_PARAM_LABEL_KEYS,
  DIST_PARAM_SCHEMAS,
  DIST_PARAMS,
  DIST_TYPES,
} from "@/constants/simulation";
import { useFormSubmitting } from "@/hooks/useFormSubmitting";
import {
  buildCaughtErrorMessage,
  buildResponseErrorMessage,
} from "@/lib/utils/apiError";
import { extractFieldError } from "@/lib/utils/formHelpers";
import type { DistributionType } from "@/types/commonTypes";
import { InputText } from "@/components/atoms/Input/InputText";
import { ErrorAlert } from "@/components/molecules/Alert/ErrorAlert";
import { RadioTagGroup } from "@/components/molecules/Field/RadioTagGroup";
import { FormField } from "@/components/molecules/Form/FormField";
import { RandomSeedField } from "@/components/molecules/Form/RandomSeedField";
import { fetchUpdatedColumnList } from "@/components/organisms/Dialog/ColumnOperationForms/fetchUpdatedColumnList";
import type { ColumnOperationFormPropsType } from "@/components/organisms/Dialog/ColumnOperationForms/types";

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
        const result = DIST_PARAM_SCHEMAS[param]().safeParse(
          value[param as keyof typeof value],
        );
        if (!result.success) {
          setApiError(
            `${t(DIST_PARAM_LABEL_KEYS[param])}: ${result.error.issues[0]?.message ?? t("Error.UnexpectedError")}`,
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
        const numericParams = Object.fromEntries(
          paramNames.map((p) => [p, Number(value[p as keyof typeof value])]),
        );

        const response = await getEconomiconAppAPI().addSimulationColumn({
          tableName,
          simulationColumn: {
            columnName: value.columnName,
            distribution: buildDistributionFromParams(
              value.distributionType,
              numericParams,
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
            buildResponseErrorMessage(response, t("Error.UnexpectedError"), {
              columnName: t("AddSimulationColumnForm.ColumnName"),
            }),
          );
        }
      } catch (error) {
        setApiError(
          buildCaughtErrorMessage(error, t("Error.UnexpectedError"), {
            columnName: t("AddSimulationColumnForm.ColumnName"),
          }),
        );
      }
    },
  });

  const isSubmitting = useStore(form.store, (s) => s.isSubmitting);
  const distributionType = useStore(
    form.store,
    (s) => s.values.distributionType,
  );
  useFormSubmitting(isSubmitting, onIsSubmittingChange);

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
          <FormField label={t("AddSimulationColumnForm.DistributionType")}>
            <RadioTagGroup
              name="sim-dist-type"
              items={DIST_TYPES.map((dt) => ({
                value: dt,
                label: t(`AddSimulationColumnForm.${dt}`),
              }))}
              value={field.state.value}
              onChange={(v) => field.handleChange(v as DistributionType)}
              disabled={isSubmitting}
            />
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
              label={t(DIST_PARAM_LABEL_KEYS[param])}
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
