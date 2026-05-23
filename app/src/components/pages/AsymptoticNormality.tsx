import type { AsymptoticNormalityRequestBody } from "@/api/model";
import { AsymptoticNormalityRequestBodyErrorType } from "@/api/model/asymptoticNormalityRequestBodyErrorType";
import { AsymptoticNormalityRequestBodySampleSize } from "@/api/model/asymptoticNormalityRequestBodySampleSize";
import { RadioTagGroup } from "@/components/molecules/Field/RadioTagGroup";
import { SimParamSlider } from "@/components/molecules/Field/SimParamSlider";
import { CollapsibleSection } from "@/components/molecules/Layout/CollapsibleSection";
import { PlotPanel } from "@/components/molecules/Loading/PlotPanel";
import { PageLayout } from "@/components/templates/PageLayout";
import { useAsymptoticNormality } from "@/hooks/useAsymptoticNormality";
import type { Config, Layout } from "plotly.js";
import * as Plotly from "plotly.js-dist-min";
import { useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

type ErrorType =
  (typeof AsymptoticNormalityRequestBodyErrorType)[keyof typeof AsymptoticNormalityRequestBodyErrorType];

const SAMPLE_SIZE_OPTIONS = Object.values(
  AsymptoticNormalityRequestBodySampleSize,
) as number[];

export const AsymptoticNormality = () => {
  const { t } = useTranslation();

  const [sampleSize, setSampleSize] =
    useState<AsymptoticNormalityRequestBodySampleSize>(
      AsymptoticNormalityRequestBodySampleSize.NUMBER_100,
    );
  const [trueBeta, setTrueBeta] = useState(1.0);
  const [errorVariance, setErrorVariance] = useState(1.0);
  const [errorType, setErrorType] = useState<ErrorType>(
    AsymptoticNormalityRequestBodyErrorType.normal,
  );
  const [endogeneityStrength, setEndogeneityStrength] = useState(1.0);
  const [xMean, setXMean] = useState(0.0);
  const [xVariance, setXVariance] = useState(1.0);

  const isEndogenous =
    errorType === AsymptoticNormalityRequestBodyErrorType.endogenous;
  const isCauchy = errorType === AsymptoticNormalityRequestBodyErrorType.cauchy;

  const params = useMemo<AsymptoticNormalityRequestBody>(
    () => ({
      sampleSize,
      trueBeta,
      errorVariance,
      errorType,
      ...(isEndogenous ? { endogeneityStrength } : {}),
      xDistribution: { xMean, xVariance },
    }),
    [
      sampleSize,
      trueBeta,
      errorVariance,
      errorType,
      endogeneityStrength,
      isEndogenous,
      xMean,
      xVariance,
    ],
  );

  const { loading, error, result } = useAsymptoticNormality(params);

  const plotDivRef = useRef<HTMLDivElement>(null);

  const plotData = useMemo(() => {
    if (!result) return [];

    const histTrace = {
      type: "histogram" as const,
      x: result.betaEstimates,
      histnorm: "probability density" as const,
      name: "β̂",
      marker: {
        color: "rgba(99, 102, 241, 0.6)",
        line: { color: "#6366f1", width: 1 },
      },
      autobinx: true,
    };

    if (
      !result.isAsymptoticallyNormal ||
      result.asymptoticMean === null ||
      result.asymptoticVariance === null
    ) {
      return [histTrace];
    }

    const std = Math.sqrt(result.asymptoticVariance);
    const xMin = result.asymptoticMean - 4 * std;
    const xMax = result.asymptoticMean + 4 * std;
    const N = 200;
    const xs = Array.from(
      { length: N },
      (_, i) => xMin + (i / (N - 1)) * (xMax - xMin),
    );
    const ys = xs.map(
      (x) =>
        (1 / (std * Math.sqrt(2 * Math.PI))) *
        Math.exp(-0.5 * ((x - result.asymptoticMean!) / std) ** 2),
    );

    const normalTrace = {
      type: "scatter" as const,
      mode: "lines" as const,
      x: xs,
      y: ys,
      name: t("AsymptoticNormality.NormalCurveLabel"),
      line: { color: "#f97316", width: 2 },
    };

    return [histTrace, normalTrace];
  }, [result, t]);

  useEffect(() => {
    if (!plotDivRef.current) return;
    if (!result || error) {
      Plotly.purge(plotDivRef.current);
      return;
    }

    const layout: Partial<Layout> = {
      autosize: true,
      margin: { t: 20, r: 20, b: 60, l: 60 },
      showlegend: true,
      legend: { orientation: "h", y: -0.2 },
      xaxis: { title: { text: "β̂" } },
      yaxis: { title: { text: t("AsymptoticNormality.YAxisDensity") } },
      shapes: [
        {
          type: "line",
          x0: result.trueBeta,
          x1: result.trueBeta,
          y0: 0,
          y1: 1,
          yref: "paper" as const,
          line: { color: "#ef4444", width: 2 },
        },
      ],
      annotations: [
        {
          x: result.trueBeta,
          y: 1,
          yref: "paper" as const,
          text: t("AsymptoticNormality.TrueBetaLabel"),
          showarrow: false,
          xanchor: "left" as const,
          font: { color: "#ef4444", size: 10 },
        },
      ],
      paper_bgcolor: "transparent",
      plot_bgcolor: "transparent",
      font: { color: "#cbd5e1" },
      barmode: "overlay",
    };
    const config: Partial<Config> = { displayModeBar: false, responsive: true };
    void Plotly.react(plotDivRef.current, plotData, layout, config);
  }, [plotData, result, error, t]);

  useEffect(() => {
    const div = plotDivRef.current;
    return () => {
      if (div) Plotly.purge(div);
    };
  }, []);

  return (
    <PageLayout
      title={t("AsymptoticNormality.Title")}
      description={t("AsymptoticNormality.Description")}
    >
      <div
        className="grid grid-cols-[300px_1fr] gap-4 h-full min-h-0"
        data-testid="asymptotic-normality"
      >
        {/* 左ペイン: コントロール */}
        <div className="flex flex-col gap-4 overflow-y-auto pr-1">
          {/* サンプルサイズ n */}
          <div>
            <p className="mb-2 text-sm font-medium text-brand-text-main">
              {t("AsymptoticNormality.SampleSize")}
            </p>
            <RadioTagGroup
              name="sample-size"
              items={SAMPLE_SIZE_OPTIONS.map((n) => ({
                value: String(n),
                label: String(n),
              }))}
              value={String(sampleSize)}
              onChange={(v) =>
                setSampleSize(
                  Number(v) as AsymptoticNormalityRequestBodySampleSize,
                )
              }
            />
          </div>

          {/* 真の回帰係数 β */}
          <SimParamSlider
            label={t("AsymptoticNormality.TrueBeta")}
            min={-3}
            max={3}
            step={0.1}
            value={trueBeta}
            onChange={setTrueBeta}
            sliderTestId="true-beta-slider"
            valueTestId="true-beta-value"
          />

          {/* 誤差分散 σ² */}
          <SimParamSlider
            label={t("AsymptoticNormality.ErrorVariance")}
            min={0.1}
            max={10}
            step={0.1}
            value={errorVariance}
            onChange={setErrorVariance}
            sliderTestId="error-variance-slider"
            valueTestId="error-variance-value"
          />

          {/* 誤差タイプ */}
          <div>
            <p className="mb-2 text-sm font-medium text-brand-text-main">
              {t("AsymptoticNormality.ErrorType")}
            </p>
            <RadioTagGroup
              name="error-type"
              items={[
                {
                  value: AsymptoticNormalityRequestBodyErrorType.normal,
                  label: t("AsymptoticNormality.ErrorTypeNormal"),
                },
                {
                  value: AsymptoticNormalityRequestBodyErrorType.cauchy,
                  label: t("AsymptoticNormality.ErrorTypeCauchy"),
                },
                {
                  value: AsymptoticNormalityRequestBodyErrorType.endogenous,
                  label: t("AsymptoticNormality.ErrorTypeEndogenous"),
                },
              ]}
              value={errorType}
              onChange={(v) => setErrorType(v as ErrorType)}
            />
          </div>

          {/* 内生性の強さ γ（endogenous 選択時のみ） */}
          {isEndogenous && (
            <SimParamSlider
              label={t("AsymptoticNormality.EndogeneityStrength")}
              min={0.1}
              max={3.0}
              step={0.1}
              value={endogeneityStrength}
              onChange={setEndogeneityStrength}
              sliderTestId="endogeneity-strength-slider"
              valueTestId="endogeneity-strength-value"
            />
          )}

          {/* 詳細設定 */}
          <CollapsibleSection
            title={t("AsymptoticNormality.AdvancedSettings")}
            defaultOpen={false}
          >
            <div className="flex flex-col gap-3 pt-2">
              <SimParamSlider
                label={t("AsymptoticNormality.XMean")}
                min={-10}
                max={10}
                step={0.1}
                value={xMean}
                onChange={setXMean}
                sliderTestId="x-mean-slider"
                valueTestId="x-mean-value"
              />
              <SimParamSlider
                label={t("AsymptoticNormality.XVariance")}
                min={0.1}
                max={10}
                step={0.1}
                value={xVariance}
                onChange={setXVariance}
                sliderTestId="x-variance-slider"
                valueTestId="x-variance-value"
              />
            </div>
          </CollapsibleSection>
        </div>

        {/* 右ペイン: プロット */}
        <div className="flex flex-col gap-2 min-h-0">
          {isCauchy && (
            <div
              className="rounded-md bg-amber-50 px-3 py-2 text-xs text-amber-800 dark:bg-amber-900/20 dark:text-amber-300"
              data-testid="cauchy-notice"
            >
              {t("AsymptoticNormality.CauchyNotice")}
            </div>
          )}
          {isEndogenous && (
            <div
              className="rounded-md bg-red-50 px-3 py-2 text-xs text-red-800 dark:bg-red-900/20 dark:text-red-300"
              data-testid="endogenous-notice"
            >
              {t("AsymptoticNormality.EndogeneousNotice")}
            </div>
          )}
          <PlotPanel
            plotRef={plotDivRef}
            loading={loading}
            error={error}
            hasData={!!result}
            loadingText={t("AsymptoticNormality.Loading")}
            testId="asymptotic-normality-plot-area"
            plotTestId="asymptotic-normality-plot"
            className="flex-1 min-h-0"
          />
        </div>
      </div>
    </PageLayout>
  );
};
