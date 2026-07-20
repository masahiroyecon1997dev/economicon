import { RegressionResult } from "@/components/organisms/Result/RegressionResult";
import type { LinearRegressionResultType } from "@/types/commonTypes";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}));

// ---------------------------------------------------------------------------
// Fixture
// ---------------------------------------------------------------------------
const buildResult = (
  overrides: Partial<LinearRegressionResultType> = {},
): LinearRegressionResultType => ({
  resultId: "test-result-id",
  tableName: "sales",
  dependentVariable: "price",
  explanatoryVariables: ["quantity"],
  regressionResult: "OLS",
  parameters: [
    {
      variable: "quantity",
      coefficient: 1.5,
      standardError: 0.12,
      pValue: 0.0003,
      tValue: 12.5,
      confidenceIntervalLower: 1.26,
      confidenceIntervalUpper: 1.74,
    },
  ],
  modelStatistics: {
    nObservations: 100,
    R2: 0.85,
    adjustedR2: 0.849,
    fValue: 156.25,
    fProbability: 0.0,
    AIC: -120.3,
    BIC: -110.2,
    logLikelihood: 62.1,
  },
  ...overrides,
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("RegressionResult — 表示テスト", () => {
  describe("分析概要セクション", () => {
    it("tableName と dependentVariable が表示される", () => {
      render(<RegressionResult result={buildResult()} />);
      expect(screen.getByText("sales")).toBeInTheDocument();
      expect(screen.getByText("price")).toBeInTheDocument();
    });
  });

  describe("係数テーブル", () => {
    it("variable 名が表示される", () => {
      render(<RegressionResult result={buildResult()} />);
      expect(screen.getByText("quantity")).toBeInTheDocument();
    });

    it("coefficient が小数点4桁でフォーマットされる", () => {
      render(<RegressionResult result={buildResult()} />);
      expect(screen.getByText("1.5000")).toBeInTheDocument();
    });

    it("standardError が小数点4桁でフォーマットされる", () => {
      render(<RegressionResult result={buildResult()} />);
      expect(screen.getByText("0.1200")).toBeInTheDocument();
    });

    it("coefficient が null のとき 'RegressionResult.NA' が表示される", () => {
      const result = buildResult({
        parameters: [
          {
            variable: "quantity",
            coefficient: null as unknown as number,
            standardError: null,
            pValue: null,
            tValue: null,
            confidenceIntervalLower: null,
            confidenceIntervalUpper: null,
          },
        ],
      });
      render(<RegressionResult result={result} />);
      // NA が複数表示される（各列がnull）
      const naItems = screen.getAllByText("RegressionResult.NA");
      expect(naItems.length).toBeGreaterThan(0);
    });
  });

  describe("有意水準マーカー", () => {
    it("p < 0.001 → '***' が表示される", () => {
      const result = buildResult({
        parameters: [
          {
            variable: "x1",
            coefficient: 1.0,
            standardError: 0.1,
            pValue: 0.0005,
            tValue: 10.0,
            confidenceIntervalLower: 0.8,
            confidenceIntervalUpper: 1.2,
          },
        ],
      });
      render(<RegressionResult result={result} />);
      expect(screen.getByText("***")).toBeInTheDocument();
    });

    it("p = 0.005 (< 0.01) → '**' が表示される", () => {
      const result = buildResult({
        parameters: [
          {
            variable: "x1",
            coefficient: 1.0,
            standardError: 0.1,
            pValue: 0.005,
            tValue: 10.0,
            confidenceIntervalLower: 0.8,
            confidenceIntervalUpper: 1.2,
          },
        ],
      });
      render(<RegressionResult result={result} />);
      expect(screen.getByText("**")).toBeInTheDocument();
    });

    it("p = 0.03 (< 0.05) → '*' が表示される", () => {
      const result = buildResult({
        parameters: [
          {
            variable: "x1",
            coefficient: 1.0,
            standardError: 0.1,
            pValue: 0.03,
            tValue: 10.0,
            confidenceIntervalLower: 0.8,
            confidenceIntervalUpper: 1.2,
          },
        ],
      });
      render(<RegressionResult result={result} />);
      expect(screen.getByText("*")).toBeInTheDocument();
    });

    it("p = 0.1 (≥ 0.05) → マーカーなし", () => {
      const result = buildResult({
        parameters: [
          {
            variable: "x1",
            coefficient: 1.0,
            standardError: 0.1,
            pValue: 0.1,
            tValue: 10.0,
            confidenceIntervalLower: 0.8,
            confidenceIntervalUpper: 1.2,
          },
        ],
      });
      render(<RegressionResult result={result} />);
      expect(screen.queryByText("*")).not.toBeInTheDocument();
      expect(screen.queryByText("**")).not.toBeInTheDocument();
      expect(screen.queryByText("***")).not.toBeInTheDocument();
    });
  });

  describe("モデル統計量セクション", () => {
    it("R² の値が表示される", () => {
      render(<RegressionResult result={buildResult()} />);
      expect(screen.getByText("0.8500")).toBeInTheDocument();
    });

    it("Adjusted R² の値が表示される", () => {
      render(<RegressionResult result={buildResult()} />);
      expect(screen.getByText("0.8490")).toBeInTheDocument();
    });

    it("F統計量の値が表示される", () => {
      render(<RegressionResult result={buildResult()} />);
      expect(screen.getByText("156.2500")).toBeInTheDocument();
    });
  });

  // =========================================================================
  describe("パネルモデル統計量セクション（FE / RE）", () => {
    it("R2Within が undefined のとき（OLS等）→ パネルセクションが表示されない", () => {
      render(<RegressionResult result={buildResult()} />);
      expect(
        screen.queryByText("RegressionResult.PanelModelStatistics"),
      ).not.toBeInTheDocument();
    });

    it("FE モデル: R2Within / R2Between / R2Overall / nEntities / fPooled が全て表示される", () => {
      const result = buildResult({
        modelType: "fe",
        modelStatistics: {
          nObservations: 100,
          nEntities: 10,
          R2Within: 0.9897,
          R2Between: 0.1215,
          R2Overall: 0.8195,
          fValue: 4246.4,
          fProbability: 0.0,
          fPooled: { statistic: 87.2, pValue: 0.0 },
        },
      });
      render(<RegressionResult result={result} />);

      // セクションタイトル
      expect(
        screen.getByText("RegressionResult.PanelModelStatistics"),
      ).toBeInTheDocument();

      // Within / Between / Overall R²
      expect(screen.getByText("0.9897")).toBeInTheDocument();
      expect(screen.getByText("0.1215")).toBeInTheDocument();
      expect(screen.getByText("0.8195")).toBeInTheDocument();

      // エンティティ数（数値はそのまま表示）
      expect(screen.getByText("10")).toBeInTheDocument();

      // プールドF統計量
      expect(screen.getByText("87.2000")).toBeInTheDocument();
    });

    it("RE モデル: R2Within / R2Between / R2Overall が表示され nEntities は非表示", () => {
      const result = buildResult({
        modelType: "re",
        modelStatistics: {
          nObservations: 100,
          // nEntities は RE では含まれない
          R2Within: 0.9888,
          R2Between: 0.1924,
          R2Overall: 0.8344,
        },
      });
      render(<RegressionResult result={result} />);

      expect(
        screen.getByText("RegressionResult.PanelModelStatistics"),
      ).toBeInTheDocument();

      expect(screen.getByText("0.9888")).toBeInTheDocument();
      expect(screen.getByText("0.1924")).toBeInTheDocument();
      expect(screen.getByText("0.8344")).toBeInTheDocument();

      // nEntities はフォーマット不要（undefined なので StatItem ごと非表示）
      expect(
        screen.queryByText("RegressionResult.NEntities"),
      ).not.toBeInTheDocument();

      // fPooled も非表示
      expect(
        screen.queryByText("RegressionResult.FPooledStatistic"),
      ).not.toBeInTheDocument();
    });
  });
});
