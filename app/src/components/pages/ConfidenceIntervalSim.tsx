import type { CIBound, ConfidenceIntervalSimRequestBody } from "@/api/model";
import { ConfidenceIntervalSimRequestBodyCiType } from "@/api/model/confidenceIntervalSimRequestBodyCiType";
import { AnimationControls } from "@/components/molecules/ActionBar/AnimationControls";
import { SimParamSlider } from "@/components/molecules/Field/SimParamSlider";
import { PlotPanel } from "@/components/molecules/Loading/PlotPanel";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/organisms/Tab/BaseTab";
import { PageLayout } from "@/components/templates/PageLayout";
import { useConfidenceIntervalSim } from "@/hooks/useConfidenceIntervalSim";
import {
  type AnimationSpeed,
  useSimulationAnimation,
} from "@/hooks/useSimulationAnimation";
import type { Config, Layout } from "plotly.js";
import * as Plotly from "plotly.js-dist-min";
import { useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

type CiType =
  (typeof ConfidenceIntervalSimRequestBodyCiType)[keyof typeof ConfidenceIntervalSimRequestBodyCiType];

const CONFIDENCE_LEVELS = [0.9, 0.95, 0.99] as const;
const MAX_VISIBLE_INTERVALS = 50;

export const ConfidenceIntervalSim = () => {
  const { t } = useTranslation();

  const [ciType, setCiType] = useState<CiType>(
    ConfidenceIntervalSimRequestBodyCiType.mean,
  );
  const [trials, setTrials] = useState(100);
  const [sampleSize, setSampleSize] = useState(30);
  const [confidenceLevel, setConfidenceLevel] = useState<0.9 | 0.95 | 0.99>(
    0.95,
  );
  const [trueMean, setTrueMean] = useState(0.0);
  const [trueVariance, setTrueVariance] = useState(1.0);
  const [speed, setSpeed] = useState<AnimationSpeed>("normal");

  const params = useMemo<ConfidenceIntervalSimRequestBody>(
    () => ({
      ciType,
      trials,
      sampleSize,
      confidenceLevel,
      trueMean,
      trueVariance,
    }),
    [ciType, trials, sampleSize, confidenceLevel, trueMean, trueVariance],
  );

  const { loading, error, result } = useConfidenceIntervalSim(params);

  const totalFrames = result?.intervals.length ?? 0;
  const { frame, playing, play, pause, reset } = useSimulationAnimation(
    totalFrames,
    speed,
  );

  const barPlotRef = useRef<HTMLDivElement>(null);
  const linePlotRef = useRef<HTMLDivElement>(null);

  // 表示する区間（最新 MAX_VISIBLE_INTERVALS 件）
  const visibleIntervals = useMemo<CIBound[]>(
    () =>
      result
        ? result.intervals.slice(
            Math.max(0, frame + 1 - MAX_VISIBLE_INTERVALS),
            frame + 1,
          )
        : [],
    [result, frame],
  );

  // カバレッジ率（累積）
  const coverageRate = useMemo(() => {
    if (!result || frame < 0) return 0;
    const shown = result.intervals.slice(0, frame + 1);
    if (shown.length === 0) return 0;
    return shown.filter((iv) => iv.containsTrue).length / shown.length;
  }, [result, frame]);

  // AnimationControls の counterLabel: "k/M (xx.x%)"
  const counterLabel =
    result != null
      ? `${frame + 1}/${totalFrames} (${(coverageRate * 100).toFixed(1)}%)`
      : undefined;

  // 横棒グラフ用プロットデータ
  const barPlotData = useMemo(() => {
    if (!result || visibleIntervals.length === 0) return [];

    const startIdx = Math.max(0, frame + 1 - MAX_VISIBLE_INTERVALS);
    const greens: { x: number[]; y: number[]; err: number[] } = {
      x: [],
      y: [],
      err: [],
    };
    const reds: { x: number[]; y: number[]; err: number[] } = {
      x: [],
      y: [],
      err: [],
    };

    visibleIntervals.forEach((iv, i) => {
      const center = (iv.lower + iv.upper) / 2;
      const halfWidth = (iv.upper - iv.lower) / 2;
      const yIdx = startIdx + i + 1;
      if (iv.containsTrue) {
        greens.x.push(center);
        greens.y.push(yIdx);
        greens.err.push(halfWidth);
      } else {
        reds.x.push(center);
        reds.y.push(yIdx);
        reds.err.push(halfWidth);
      }
    });

    const traces = [];
    if (greens.x.length > 0) {
      traces.push({
        type: "scatter" as const,
        mode: "markers" as const,
        x: greens.x,
        y: greens.y,
        error_x: {
          type: "data" as const,
          array: greens.err,
          visible: true,
          color: "#22c55e",
        },
        marker: { color: "#22c55e", size: 4 },
        name: t("ConfidenceIntervalSim.ContainsTrue"),
        showlegend: true,
      });
    }
    if (reds.x.length > 0) {
      traces.push({
        type: "scatter" as const,
        mode: "markers" as const,
        x: reds.x,
        y: reds.y,
        error_x: {
          type: "data" as const,
          array: reds.err,
          visible: true,
          color: "#ef4444",
        },
        marker: { color: "#ef4444", size: 4 },
        name: t("ConfidenceIntervalSim.NotContainsTrue"),
        showlegend: true,
      });
    }
    return traces;
  }, [result, visibleIntervals, frame, t]);

  // カバレッジ折れ線プロットデータ
  const linePlotData = useMemo(() => {
    if (!result || frame < 0) return [];
    const xs = Array.from({ length: frame + 1 }, (_, i) => i + 1);
    const ys = xs.map((_, i) => {
      const shown = result.intervals.slice(0, i + 1);
      return shown.filter((iv) => iv.containsTrue).length / shown.length;
    });
    return [
      {
        type: "scatter" as const,
        mode: "lines" as const,
        x: xs,
        y: ys,
        name: t("ConfidenceIntervalSim.CoverageRateLabel"),
        line: { color: "#6366f1", width: 2 },
      },
    ];
  }, [result, frame, t]);

  // 横棒グラフ描画
  useEffect(() => {
    if (!barPlotRef.current) return;
    if (!result || error) {
      Plotly.purge(barPlotRef.current);
      return;
    }

    const startIdx = Math.max(0, frame + 1 - MAX_VISIBLE_INTERVALS);
    const endIdx = frame + 1;

    const layout: Partial<Layout> = {
      autosize: true,
      margin: { t: 10, r: 10, b: 40, l: 50 },
      showlegend: true,
      legend: { orientation: "h", y: -0.2 },
      xaxis: { title: { text: t("ConfidenceIntervalSim.XAxisValue") } },
      yaxis: {
        title: { text: t("ConfidenceIntervalSim.YAxisTrial") },
        range: [startIdx, endIdx + 1],
      },
      shapes: [
        {
          type: "line",
          x0: result.trueValue,
          x1: result.trueValue,
          y0: 0,
          y1: 1,
          yref: "paper" as const,
          line: { color: "#f97316", width: 2 },
        },
      ],
      paper_bgcolor: "transparent",
      plot_bgcolor: "transparent",
      font: { color: "#cbd5e1" },
    };
    const config: Partial<Config> = { displayModeBar: false, responsive: true };
    void Plotly.react(barPlotRef.current, barPlotData, layout, config);
  }, [barPlotData, result, error, frame, t]);

  // カバレッジ折れ線描画
  useEffect(() => {
    if (!linePlotRef.current) return;
    if (!result || error) {
      Plotly.purge(linePlotRef.current);
      return;
    }

    const nominalLevel = result.confidenceLevel;

    const layout: Partial<Layout> = {
      autosize: true,
      margin: { t: 10, r: 10, b: 40, l: 50 },
      showlegend: false,
      xaxis: {
        title: { text: t("ConfidenceIntervalSim.XAxisTrials") },
        range: [1, totalFrames],
      },
      yaxis: {
        title: { text: t("ConfidenceIntervalSim.CoverageRateLabel") },
        range: [0, 1.05],
        tickformat: ".0%",
      },
      shapes: [
        {
          type: "line",
          x0: 0,
          x1: 1,
          xref: "paper" as const,
          y0: nominalLevel,
          y1: nominalLevel,
          line: { color: "#f97316", width: 2, dash: "dash" as const },
        },
      ],
      annotations: [
        {
          x: 1,
          xref: "paper" as const,
          y: nominalLevel,
          text: `${(nominalLevel * 100).toFixed(0)}%`,
          showarrow: false,
          xanchor: "right" as const,
          font: { color: "#f97316", size: 10 },
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
    const bar = barPlotRef.current;
    const line = linePlotRef.current;
    return () => {
      if (bar) Plotly.purge(bar);
      if (line) Plotly.purge(line);
    };
  }, []);

  return (
    <PageLayout
      title={t("ConfidenceIntervalSim.Title")}
      description={t("ConfidenceIntervalSim.Description")}
    >
      <div
        className="grid grid-cols-[300px_1fr] gap-4 h-full min-h-0"
        data-testid="confidence-interval-sim"
      >
        {/* 左ペイン: コントロール */}
        <div className="flex flex-col gap-4 overflow-y-auto pr-1">
          {/* CI タイプ タブ */}
          <Tabs value={ciType} onValueChange={(v) => setCiType(v as CiType)}>
            <TabsList>
              <TabsTrigger value={ConfidenceIntervalSimRequestBodyCiType.mean}>
                {t("ConfidenceIntervalSim.TabMean")}
              </TabsTrigger>
              <TabsTrigger
                value={ConfidenceIntervalSimRequestBodyCiType.variance}
              >
                {t("ConfidenceIntervalSim.TabVariance")}
              </TabsTrigger>
            </TabsList>

            <TabsContent value={ConfidenceIntervalSimRequestBodyCiType.mean}>
              <SimParamSlider
                label={t("ConfidenceIntervalSim.TrueMean")}
                min={-100}
                max={100}
                step={0.5}
                value={trueMean}
                onChange={setTrueMean}
                sliderTestId="true-mean-slider"
                valueTestId="true-mean-value"
              />
            </TabsContent>
            <TabsContent
              value={ConfidenceIntervalSimRequestBodyCiType.variance}
            >
              <SimParamSlider
                label={t("ConfidenceIntervalSim.TrueVariance")}
                min={0.01}
                max={10}
                step={0.01}
                value={trueVariance}
                onChange={setTrueVariance}
                sliderTestId="true-variance-slider"
                valueTestId="true-variance-value"
              />
            </TabsContent>
          </Tabs>

          {/* 信頼水準 */}
          <div>
            <p className="mb-2 text-sm font-medium text-brand-text-main">
              {t("ConfidenceIntervalSim.ConfidenceLevel")}
            </p>
            <div className="flex flex-wrap gap-2">
              {CONFIDENCE_LEVELS.map((level) => (
                <label
                  key={level}
                  className={`flex cursor-pointer items-center gap-2 rounded-md border px-3 py-1.5 text-sm transition-colors ${
                    confidenceLevel === level
                      ? "border-brand-accent bg-brand-accent/5 text-brand-accent"
                      : "border-border-color bg-secondary text-brand-text-main hover:border-brand-accent/50"
                  }`}
                >
                  <input
                    type="radio"
                    name="confidence-level"
                    value={String(level)}
                    checked={confidenceLevel === level}
                    onChange={() =>
                      setConfidenceLevel(level as 0.9 | 0.95 | 0.99)
                    }
                    className="h-3.5 w-3.5 border-gray-300 text-brand-accent focus:ring-brand-accent"
                  />
                  <span>{(level * 100).toFixed(0)}%</span>
                </label>
              ))}
            </div>
          </div>

          {/* 試行回数 M */}
          <SimParamSlider
            label={t("ConfidenceIntervalSim.Trials")}
            min={10}
            max={2000}
            step={10}
            value={trials}
            onChange={setTrials}
            sliderTestId="trials-slider"
            valueTestId="trials-value"
          />

          {/* サンプルサイズ n */}
          <SimParamSlider
            label={t("ConfidenceIntervalSim.SampleSize")}
            min={5}
            max={500}
            step={5}
            value={sampleSize}
            onChange={setSampleSize}
            sliderTestId="sample-size-slider"
            valueTestId="sample-size-value"
          />
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
            counterLabel={counterLabel}
          />

          {/* 横棒グラフ（上）: 各区間の包含/非包含 */}
          <PlotPanel
            plotRef={barPlotRef}
            loading={loading}
            error={error}
            hasData={!!result && !error}
            loadingText={t("ConfidenceIntervalSim.Loading")}
            className="flex-1 min-h-0"
            testId="ci-bar-area"
            plotTestId="ci-bar-plot"
          />

          {/* 折れ線グラフ（下）: カバレッジ率の推移 */}
          <PlotPanel
            plotRef={linePlotRef}
            loading={loading}
            error={null}
            hasData={!!result && !error}
            className="flex-1 min-h-0"
            testId="ci-line-area"
            plotTestId="ci-line-plot"
          />
        </div>
      </div>
    </PageLayout>
  );
};
