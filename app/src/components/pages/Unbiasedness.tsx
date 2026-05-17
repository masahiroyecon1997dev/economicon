import type { UnbiasednessRequestBody } from "@/api/model";
import { AnimationControls } from "@/components/molecules/ActionBar/AnimationControls";
import { SimParamSlider } from "@/components/molecules/Field/SimParamSlider";
import { CollapsibleSection } from "@/components/molecules/Layout/CollapsibleSection";
import { PlotPanel } from "@/components/molecules/Loading/PlotPanel";
import { PageLayout } from "@/components/templates/PageLayout";
import {
  type AnimationSpeed,
  useSimulationAnimation,
} from "@/hooks/useSimulationAnimation";
import { useUnbiasedness } from "@/hooks/useUnbiasedness";
import type { Config, Layout } from "plotly.js";
import * as Plotly from "plotly.js-dist-min";
import { useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

export const Unbiasedness = () => {
  const { t } = useTranslation();

  const [numTrials, setNumTrials] = useState(200);
  const [sampleSize, setSampleSize] = useState(50);
  const [trueBeta, setTrueBeta] = useState(1.0);
  const [errorVariance, setErrorVariance] = useState(1.0);
  const [xMean, setXMean] = useState(0.0);
  const [xVariance, setXVariance] = useState(1.0);
  const [speed, setSpeed] = useState<AnimationSpeed>("normal");

  const params = useMemo<UnbiasednessRequestBody>(
    () => ({
      numTrials,
      sampleSize,
      trueBeta,
      errorVariance,
      xDistribution: { xMean, xVariance },
    }),
    [numTrials, sampleSize, trueBeta, errorVariance, xMean, xVariance],
  );

  const { loading, error, result } = useUnbiasedness(params);

  const totalFrames = result?.betaEstimates.length ?? 0;
  const { frame, playing, play, pause, reset } = useSimulationAnimation(
    totalFrames,
    speed,
  );

  const histPlotRef = useRef<HTMLDivElement>(null);
  const linePlotRef = useRef<HTMLDivElement>(null);

  const visibleEstimates = useMemo(
    () => (result ? result.betaEstimates.slice(0, frame + 1) : []),
    [result, frame],
  );

  // 累積平均（各試行時点での β̂ の平均）
  const runningMean = useMemo(() => {
    if (visibleEstimates.length === 0) return [];
    let sum = 0;
    return visibleEstimates.map((v, i) => {
      sum += v;
      return sum / (i + 1);
    });
  }, [visibleEstimates]);

  // ヒストグラムのプロットデータ
  const histPlotData = useMemo(() => {
    if (!result || visibleEstimates.length === 0) return [];
    return [
      {
        type: "histogram" as const,
        x: visibleEstimates,
        name: "β̂",
        marker: {
          color: "rgba(99, 102, 241, 0.6)",
          line: { color: "#6366f1", width: 1 },
        },
        autobinx: true,
      },
    ];
  }, [result, visibleEstimates]);

  // 累積平均の折れ線プロットデータ
  const linePlotData = useMemo(() => {
    if (!result || runningMean.length === 0) return [];
    return [
      {
        type: "scatter" as const,
        mode: "lines" as const,
        x: Array.from({ length: runningMean.length }, (_, i) => i + 1),
        y: runningMean,
        name: t("Unbiasedness.RunningMeanLabel"),
        line: { color: "#6366f1", width: 2 },
      },
    ];
  }, [result, runningMean, t]);

  // ヒストグラム描画
  useEffect(() => {
    if (!histPlotRef.current) return;
    if (!result || error) {
      Plotly.purge(histPlotRef.current);
      return;
    }

    const layout: Partial<Layout> = {
      autosize: true,
      margin: { t: 10, r: 10, b: 50, l: 50 },
      showlegend: false,
      xaxis: { title: { text: "β̂" } },
      yaxis: { title: { text: t("Unbiasedness.YAxisCount") } },
      shapes: [
        {
          type: "line",
          x0: result.trueBeta,
          x1: result.trueBeta,
          y0: 0,
          y1: 1,
          yref: "paper" as const,
          line: { color: "#ef4444", width: 2, dash: "dash" as const },
        },
      ],
      annotations: [
        {
          x: result.trueBeta,
          y: 1,
          yref: "paper" as const,
          text: t("Unbiasedness.TrueBetaLabel"),
          showarrow: false,
          xanchor: "left" as const,
          font: { color: "#ef4444", size: 10 },
        },
      ],
      paper_bgcolor: "transparent",
      plot_bgcolor: "transparent",
      font: { color: "#cbd5e1" },
    };
    const config: Partial<Config> = { displayModeBar: false, responsive: true };
    void Plotly.react(histPlotRef.current, histPlotData, layout, config);
  }, [histPlotData, result, error, t]);

  // 折れ線グラフ描画
  useEffect(() => {
    if (!linePlotRef.current) return;
    if (!result || error) {
      Plotly.purge(linePlotRef.current);
      return;
    }

    const yPad = 0.5;
    const layout: Partial<Layout> = {
      autosize: true,
      margin: { t: 10, r: 10, b: 50, l: 50 },
      showlegend: false,
      xaxis: {
        title: { text: t("Unbiasedness.XAxisTrials") },
        range: [1, totalFrames],
      },
      yaxis: {
        title: { text: t("Unbiasedness.RunningMeanLabel") },
        range: [result.trueBeta - yPad, result.trueBeta + yPad],
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
      ],
      paper_bgcolor: "transparent",
      plot_bgcolor: "transparent",
      font: { color: "#cbd5e1" },
    };
    const config: Partial<Config> = { displayModeBar: false, responsive: true };
    void Plotly.react(linePlotRef.current, linePlotData, layout, config);
  }, [linePlotData, result, error, t, totalFrames]);

  // クリーンアップ
  useEffect(() => {
    const hist = histPlotRef.current;
    const line = linePlotRef.current;
    return () => {
      if (hist) Plotly.purge(hist);
      if (line) Plotly.purge(line);
    };
  }, []);

  return (
    <PageLayout
      title={t("Unbiasedness.Title")}
      description={t("Unbiasedness.Description")}
    >
      <div
        className="grid grid-cols-[300px_1fr] gap-4 h-full min-h-0"
        data-testid="unbiasedness"
      >
        {/* 左ペイン: コントロール */}
        <div className="flex flex-col gap-4 overflow-y-auto pr-1">
          {/* 試行回数 M */}
          <SimParamSlider
            label={t("Unbiasedness.NumTrials")}
            min={10}
            max={2000}
            step={10}
            value={numTrials}
            onChange={setNumTrials}
            sliderTestId="num-trials-slider"
            valueTestId="num-trials-value"
          />

          {/* サンプルサイズ n */}
          <SimParamSlider
            label={t("Unbiasedness.SampleSize")}
            min={5}
            max={500}
            step={5}
            value={sampleSize}
            onChange={setSampleSize}
            sliderTestId="sample-size-slider"
            valueTestId="sample-size-value"
          />

          {/* 真の回帰係数 β */}
          <SimParamSlider
            label={t("Unbiasedness.TrueBeta")}
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
            label={t("Unbiasedness.ErrorVariance")}
            min={0.1}
            max={10}
            step={0.1}
            value={errorVariance}
            onChange={setErrorVariance}
            sliderTestId="error-variance-slider"
            valueTestId="error-variance-value"
          />

          {/* 詳細設定 */}
          <CollapsibleSection
            title={t("Unbiasedness.AdvancedSettings")}
            defaultOpen={false}
          >
            <div className="flex flex-col gap-3 pt-2">
              <SimParamSlider
                label={t("Unbiasedness.XMean")}
                min={-10}
                max={10}
                step={0.1}
                value={xMean}
                onChange={setXMean}
                sliderTestId="x-mean-slider"
                valueTestId="x-mean-value"
              />
              <SimParamSlider
                label={t("Unbiasedness.XVariance")}
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

        {/* 右ペイン: アニメーション + 2 プロット */}
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

          {/* ヒストグラム（上） */}
          <PlotPanel
            plotRef={histPlotRef}
            loading={loading}
            error={error}
            hasData={!!result && !error}
            loadingText={t("Unbiasedness.Loading")}
            className="flex-1 min-h-0"
            testId="unbiasedness-hist-area"
            plotTestId="unbiasedness-hist-plot"
          />

          {/* 累積平均折れ線（下） */}
          <PlotPanel
            plotRef={linePlotRef}
            loading={loading}
            error={null}
            hasData={!!result && !error}
            className="flex-1 min-h-0"
            testId="unbiasedness-line-area"
            plotTestId="unbiasedness-line-plot"
          />
        </div>
      </div>
    </PageLayout>
  );
};
