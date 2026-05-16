import type { DistributionConfig } from "@/api/model";
import { ErrorAlert } from "@/components/molecules/Alert/ErrorAlert";
import { RadioTagGroup } from "@/components/molecules/Field/RadioTagGroup";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/organisms/Tab/BaseTab";
import { PageLayout } from "@/components/templates/PageLayout";
import { DIST_PREVIEW_PARAM_RANGES } from "@/constants/distributionPreview";
import {
  CONTINUOUS_DIST_TYPES,
  DISCRETE_DIST_TYPES,
  DIST_PARAM_DEFAULTS,
  DIST_PARAM_LABEL_KEYS,
  DIST_PARAMS,
} from "@/constants/simulation";
import { useDistributionPreview } from "@/hooks/useDistributionPreview";
import { cn } from "@/lib/utils/helpers";
import { useWorkspaceTabsStore } from "@/stores/workspaceTabs";
import type { DistributionType } from "@/types/commonTypes";
import { Loader2 } from "lucide-react";
import type { Config, Layout } from "plotly.js";
import * as Plotly from "plotly.js-dist-min";
import { useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

type DistCategory = "continuous" | "discrete";
type FunctionTab = "density" | "cumulative";

type DistributionPreviewDraftValues = {
  distributionType: DistributionType;
  distributionParams: Record<string, number>;
};

const isValidDraft = (v: unknown): v is DistributionPreviewDraftValues =>
  typeof v === "object" &&
  v !== null &&
  "distributionType" in v &&
  typeof (v as Record<string, unknown>).distributionType === "string";

const buildDistributionConfig = (
  type: DistributionType,
  params: Record<string, number>,
): DistributionConfig => ({ type, ...params }) as DistributionConfig;

export const DistributionPreview = () => {
  const { t } = useTranslation();

  const activeTab = useWorkspaceTabsStore((s) =>
    s.tabs.find((tab) => tab.id === s.activeTabId),
  );
  const draft = activeTab?.kind === "work" ? activeTab.draftValues : undefined;
  const validDraft = isValidDraft(draft) ? draft : undefined;

  const initCategory: DistCategory =
    validDraft && DISCRETE_DIST_TYPES.includes(validDraft.distributionType)
      ? "discrete"
      : "continuous";
  const initType: DistributionType = validDraft?.distributionType ?? "normal";
  const initParams: Record<string, number> = validDraft?.distributionParams ?? {
    ...DIST_PARAM_DEFAULTS[initType],
  };

  const [category, setCategory] = useState<DistCategory>(initCategory);
  const [selectedType, setSelectedType] = useState<DistributionType>(initType);
  const [params, setParams] = useState<Record<string, number>>(initParams);
  const [functionTab, setFunctionTab] = useState<FunctionTab>("density");

  const distribution = useMemo<DistributionConfig>(
    () => buildDistributionConfig(selectedType, params),
    [selectedType, params],
  );

  const { loading, error, result } = useDistributionPreview(distribution);

  const plotDivRef = useRef<HTMLDivElement>(null);

  const handleCategoryChange = (cat: DistCategory) => {
    setCategory(cat);
    const types =
      cat === "continuous" ? CONTINUOUS_DIST_TYPES : DISCRETE_DIST_TYPES;
    const nextType = types.includes(selectedType) ? selectedType : types[0];
    setSelectedType(nextType);
    setParams({ ...DIST_PARAM_DEFAULTS[nextType] });
  };

  const handleTypeChange = (type: DistributionType) => {
    setSelectedType(type);
    setParams({ ...DIST_PARAM_DEFAULTS[type] });
  };

  const getParamMax = (
    distType: DistributionType,
    paramKey: string,
  ): number => {
    const range = DIST_PREVIEW_PARAM_RANGES[distType]?.[paramKey];
    if (!range) return 100;
    if (
      distType === "hypergeometric" &&
      (paramKey === "successCount" || paramKey === "sampleSize")
    ) {
      return Math.min(params.populationSize ?? 50, range.max);
    }
    return range.max;
  };

  const paramKeys = DIST_PARAMS[selectedType] ?? [];

  const plotData = useMemo(() => {
    if (!result) return [];
    const isDiscrete = result.isDiscrete;
    const yData =
      functionTab === "density" ? result.yDensity : result.yCumulative;
    if (isDiscrete) {
      return [
        {
          type: "bar" as const,
          x: result.x,
          y: yData,
          marker: { color: "#6366f1" },
        },
      ];
    }
    return [
      {
        type: "scatter" as const,
        mode: "lines" as const,
        x: result.x,
        y: yData,
        line: { color: "#6366f1", width: 2 },
      },
    ];
  }, [result, functionTab]);

  const yAxisLabel = result?.isDiscrete
    ? functionTab === "density"
      ? t("DistributionPreview.YAxisProbability")
      : t("DistributionPreview.YAxisCumulative")
    : functionTab === "density"
      ? t("DistributionPreview.YAxisDensity")
      : t("DistributionPreview.YAxisCumulative");

  useEffect(() => {
    if (!plotDivRef.current) return;
    if (!result || error) {
      Plotly.purge(plotDivRef.current);
      return;
    }
    const layout: Partial<Layout> = {
      autosize: true,
      margin: { t: 20, r: 20, b: 60, l: 60 },
      xaxis: { title: { text: t("DistributionPreview.XAxisLabel") } },
      yaxis: { title: { text: yAxisLabel } },
      paper_bgcolor: "transparent",
      plot_bgcolor: "transparent",
      font: { color: "#cbd5e1" },
    };
    const config: Partial<Config> = { displayModeBar: false, responsive: true };
    void Plotly.react(plotDivRef.current, plotData, layout, config);
  }, [plotData, result, error, yAxisLabel, t]);

  useEffect(() => {
    const div = plotDivRef.current;
    return () => {
      if (div) Plotly.purge(div);
    };
  }, []);

  return (
    <PageLayout>
      <div
        className="grid grid-cols-[320px_1fr] gap-4 h-full"
        data-testid="distribution-preview"
      >
        {/* 左ペイン: コントロール */}
        <div className="flex flex-col gap-4 overflow-y-auto pr-1">
          {/* 連続 / 離散 タブ */}
          <Tabs
            value={category}
            onValueChange={(v) => handleCategoryChange(v as DistCategory)}
          >
            <TabsList>
              <TabsTrigger value="continuous">
                {t("DistributionPreview.TabContinuous")}
              </TabsTrigger>
              <TabsTrigger value="discrete">
                {t("DistributionPreview.TabDiscrete")}
              </TabsTrigger>
            </TabsList>

            <TabsContent value="continuous" className="pt-3" forceMount>
              <RadioTagGroup
                name="dist-type-continuous"
                items={CONTINUOUS_DIST_TYPES.map((dt) => ({
                  value: dt,
                  label: t(`AddSimulationColumnForm.${dt}`),
                }))}
                value={selectedType}
                onChange={(v) => handleTypeChange(v as DistributionType)}
              />
            </TabsContent>

            <TabsContent value="discrete" className="pt-3" forceMount>
              <RadioTagGroup
                name="dist-type-discrete"
                items={DISCRETE_DIST_TYPES.map((dt) => ({
                  value: dt,
                  label: t(`AddSimulationColumnForm.${dt}`),
                }))}
                value={selectedType}
                onChange={(v) => handleTypeChange(v as DistributionType)}
              />
            </TabsContent>
          </Tabs>

          {/* パラメータスライダー */}
          <div className="flex flex-col gap-3">
            {paramKeys.map((key) => {
              const range = DIST_PREVIEW_PARAM_RANGES[selectedType]?.[key];
              if (!range) return null;
              const max = getParamMax(selectedType, key);
              const value = params[key] ?? range.default;
              const labelKey = DIST_PARAM_LABEL_KEYS[key];
              const label = labelKey ? t(labelKey) : key;
              return (
                <div key={key} className="flex flex-col gap-1">
                  <div className="flex justify-between text-sm">
                    <span className="text-text-main/80">{label}</span>
                    <span
                      className="font-mono text-brand-accent"
                      data-testid={`param-value-${key}`}
                    >
                      {value}
                    </span>
                  </div>
                  <input
                    type="range"
                    min={range.min}
                    max={max}
                    step={range.step}
                    value={value}
                    className="w-full accent-brand-accent"
                    data-testid={`param-slider-${key}`}
                    onChange={(e) => {
                      const next = parseFloat(e.target.value);
                      setParams((prev) => ({ ...prev, [key]: next }));
                    }}
                  />
                  <div className="flex justify-between text-xs text-text-main/40">
                    <span>{range.min}</span>
                    <span>{max}</span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* PDF/PMF vs CDF/CMF タブ */}
          <Tabs
            value={functionTab}
            onValueChange={(v) => setFunctionTab(v as FunctionTab)}
          >
            <TabsList>
              <TabsTrigger value="density">
                {t("DistributionPreview.TabPdfPmf")}
              </TabsTrigger>
              <TabsTrigger value="cumulative">
                {t("DistributionPreview.TabCdfCmf")}
              </TabsTrigger>
            </TabsList>
          </Tabs>
        </div>

        {/* 右ペイン: グラフ */}
        <div
          className="relative flex items-center justify-center"
          data-testid="distribution-preview-plot-area"
        >
          {loading && (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-bg-base/60 z-10">
              <Loader2 className="h-6 w-6 animate-spin text-brand-accent" />
              <span className="text-sm text-text-main/60">
                {t("DistributionPreview.Loading")}
              </span>
            </div>
          )}

          {error && !loading && (
            <div className="w-full max-w-sm">
              <ErrorAlert message={error} />
            </div>
          )}

          <div
            ref={plotDivRef}
            className={cn(
              "w-full h-full",
              (!result || !!error) && "hidden",
              loading && "opacity-30",
            )}
            data-testid="distribution-preview-plot"
          />
        </div>
      </div>
    </PageLayout>
  );
};
