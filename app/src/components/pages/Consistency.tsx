import type { ConsistencyRequestBody } from "@/api/model";
import { AnimationControls } from "@/components/molecules/ActionBar/AnimationControls";
import { RadioTagGroup } from "@/components/molecules/Field/RadioTagGroup";
import { SimParamSlider } from "@/components/molecules/Field/SimParamSlider";
import { CollapsibleSection } from "@/components/molecules/Layout/CollapsibleSection";
import { PlotPanel } from "@/components/molecules/Loading/PlotPanel";
import { PageLayout } from "@/components/templates/PageLayout";
import { useConsistency } from "@/hooks/useConsistency";
import {
  useSimulationAnimation,
  type AnimationSpeed,
} from "@/hooks/useSimulationAnimation";
import type { Config, Layout } from "plotly.js";
import * as Plotly from "plotly.js-dist-min";
import { useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

const ENDOGENEITY_OPTIONS = [
  { value: "false", labelKey: "Consistency.EndogenousOff" },
  { value: "true", labelKey: "Consistency.EndogenousOn" },
] as const;

export const Consistency = () => {
  const { t } = useTranslation();

  const [nMax, setNMax] = useState(500);
  const [trueBeta, setTrueBeta] = useState(1.0);
  const [errorVariance, setErrorVariance] = useState(1.0);
  const [endogenous, setEndogenous] = useState(false);
  const [endogeneityStrength, setEndogeneityStrength] = useState(1.0);
  const [xMean, setXMean] = useState(0.0);
  const [xVariance, setXVariance] = useState(1.0);
  const [speed, setSpeed] = useState<AnimationSpeed>("normal");

  const params = useMemo<ConsistencyRequestBody>(
    () => ({
      nMax,
      trueBeta,
      errorVariance,
      endogenous,
      ...(endogenous ? { endogeneityStrength } : {}),
      xDistribution: { xMean, xVariance },
    }),
    [
      nMax,
      trueBeta,
      errorVariance,
      endogenous,
      endogeneityStrength,
      xMean,
      xVariance,
    ],
  );

  const { loading, error, result } = useConsistency(params);

  const totalFrames = result ? result.nValues.length + 1 : 0;
  const { frame, playing, play, pause, reset } = useSimulationAnimation(
    totalFrames,
    speed,
  );

  const plotDivRef = useRef<HTMLDivElement>(null);

  const plotData = useMemo(() => {
    if (!result) return [];
    const visibleN = result.nValues.slice(0, frame);
    const visibleBeta = result.betaEstimates.slice(0, frame);
    if (visibleN.length === 0) return [];

    return [
      {
        type: "scatter" as const,
        mode: "lines" as const,
        x: visibleN,
        y: visibleBeta,
        name: t("Consistency.BetaEstimateLabel"),
        line: { color: "#6366f1", width: 2 },
      },
    ];
  }, [result, frame, t]);

  useEffect(() => {
    if (!plotDivRef.current) return;
    if (!result || error) {
      Plotly.purge(plotDivRef.current);
      return;
    }

    const yMin = Math.min(result.trueBeta, result.probabilityLimit) - 0.5;
    const yMax = Math.max(result.trueBeta, result.probabilityLimit) + 0.5;

    const layout: Partial<Layout> = {
      autosize: true,
      margin: { t: 20, r: 20, b: 60, l: 60 },
      showlegend: true,
      legend: { orientation: "h", y: -0.25 },
      xaxis: {
        title: { text: t("Consistency.XAxisLabel") },
        range: [0, result.nValues[result.nValues.length - 1] ?? nMax],
      },
      yaxis: {
        title: { text: "β̂" },
        range: [yMin, yMax],
      },
      shapes: [
        {
          type: "line",
          x0: 0,
          x1: 1,
          xref: "paper" as const,
          y0: result.trueBeta,
          y1: result.trueBeta,
          line: { color: "#ef4444", width: 2, dash: "dash" as const },
        },
        ...(result.probabilityLimit !== result.trueBeta
          ? [
              {
                type: "line" as const,
                x0: 0,
                x1: 1,
                xref: "paper" as const,
                y0: result.probabilityLimit,
                y1: result.probabilityLimit,
                line: { color: "#f97316", width: 2, dash: "dot" as const },
              },
            ]
          : []),
      ],
      annotations: [
        {
          x: 1,
          xref: "paper" as const,
          y: result.trueBeta,
          text: t("Consistency.TrueBetaLabel"),
          showarrow: false,
          xanchor: "right" as const,
          font: { color: "#ef4444", size: 10 },
        },
        ...(result.probabilityLimit !== result.trueBeta
          ? [
              {
                x: 1,
                xref: "paper" as const,
                y: result.probabilityLimit,
                text: t("Consistency.ProbabilityLimitLabel"),
                showarrow: false,
                xanchor: "right" as const,
                font: { color: "#f97316", size: 10 },
              },
            ]
          : []),
      ],
      paper_bgcolor: "transparent",
      plot_bgcolor: "transparent",
      font: { color: "#cbd5e1" },
    };
    const config: Partial<Config> = { displayModeBar: false, responsive: true };
    void Plotly.react(plotDivRef.current, plotData, layout, config);
  }, [plotData, result, error, t, nMax]);

  useEffect(() => {
    const div = plotDivRef.current;
    return () => {
      if (div) Plotly.purge(div);
    };
  }, []);

  return (
    <PageLayout
      title={t("Consistency.Title")}
      description={t("Consistency.Description")}
    >
      <div
        className="grid grid-cols-[300px_1fr] gap-4 h-full min-h-0"
        data-testid="consistency"
      >
        {/* 左ペイン: コントロール */}
        <div className="flex flex-col gap-4 overflow-y-auto pr-1">
          {/* 外生性 / 内生性 */}
          <div>
            <p className="mb-2 text-sm font-medium text-brand-text-main">
              {t("Consistency.EndogenousLabel")}
            </p>
            <RadioTagGroup
              name="endogenous"
              items={ENDOGENEITY_OPTIONS.map((o) => ({
                value: o.value,
                label: t(o.labelKey),
              }))}
              value={String(endogenous)}
              onChange={(v) => setEndogenous(v === "true")}
            />
          </div>

          {/* n_max スライダー */}
          <SimParamSlider
            label={t("Consistency.NMax")}
            min={50}
            max={5000}
            step={50}
            value={nMax}
            onChange={setNMax}
            sliderTestId="n-max-slider"
            valueTestId="n-max-value"
          />

          {/* 真の回帰係数 β */}
          <SimParamSlider
            label={t("Consistency.TrueBeta")}
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
            label={t("Consistency.ErrorVariance")}
            min={0.1}
            max={10}
            step={0.1}
            value={errorVariance}
            onChange={setErrorVariance}
            sliderTestId="error-variance-slider"
            valueTestId="error-variance-value"
          />

          {/* 内生性の強さ γ（内生性あり時のみ） */}
          {endogenous && (
            <SimParamSlider
              label={t("Consistency.EndogeneityStrength")}
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
            title={t("Consistency.AdvancedSettings")}
            defaultOpen={false}
          >
            <div className="flex flex-col gap-3 pt-2">
              <SimParamSlider
                label={t("Consistency.XMean")}
                min={-10}
                max={10}
                step={0.1}
                value={xMean}
                onChange={setXMean}
                sliderTestId="x-mean-slider"
                valueTestId="x-mean-value"
              />
              <SimParamSlider
                label={t("Consistency.XVariance")}
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

        {/* 右ペイン: アニメーション + プロット */}
        <div className="flex flex-col gap-2 min-h-0">
          <AnimationControls
            playing={playing}
            canPlay={!!result && totalFrames > 0}
            frame={frame}
            total={totalFrames}
            speed={speed}
            onPlay={play}
            onPause={pause}
            onReset={reset}
            onSpeedChange={setSpeed}
          />

          <PlotPanel
            plotRef={plotDivRef}
            loading={loading}
            error={error}
            hasData={!!result && !error}
            loadingText={t("Consistency.Loading")}
            className="flex-1 min-h-0"
            testId="consistency-plot-area"
            plotTestId="consistency-plot"
          />
        </div>
      </div>
    </PageLayout>
  );
};
