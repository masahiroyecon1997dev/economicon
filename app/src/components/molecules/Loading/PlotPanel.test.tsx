import { PlotPanel } from "@/components/molecules/Loading/PlotPanel";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

describe("PlotPanel", () => {
  describe("ローディング状態", () => {
    it("test_loading_showsSpinner", () => {
      render(
        <PlotPanel
          plotRef={{ current: null }}
          loading={true}
          error={null}
          hasData={false}
        />,
      );
      // Loader2 は SVG アイコン — animate-spin クラスで検出
      expect(document.querySelector(".animate-spin")).toBeInTheDocument();
    });

    it("test_loading_showsLoadingText", () => {
      render(
        <PlotPanel
          plotRef={{ current: null }}
          loading={true}
          error={null}
          hasData={false}
          loadingText="計算中..."
        />,
      );
      expect(screen.getByText("計算中...")).toBeInTheDocument();
    });

    it("test_loading_false_noSpinner", () => {
      render(
        <PlotPanel
          plotRef={{ current: null }}
          loading={false}
          error={null}
          hasData={false}
        />,
      );
      expect(document.querySelector(".animate-spin")).not.toBeInTheDocument();
    });
  });

  describe("エラー状態", () => {
    it("test_error_showsErrorAlert", () => {
      render(
        <PlotPanel
          plotRef={{ current: null }}
          loading={false}
          error="エラーが発生しました"
          hasData={false}
        />,
      );
      expect(screen.getByText("エラーが発生しました")).toBeInTheDocument();
    });

    it("test_error_withLoading_hidesErrorAlert", () => {
      render(
        <PlotPanel
          plotRef={{ current: null }}
          loading={true}
          error="エラー"
          hasData={false}
        />,
      );
      expect(screen.queryByText("エラー")).not.toBeInTheDocument();
    });
  });

  describe("plot div 表示制御", () => {
    it("test_hasData_showsPlotDiv", () => {
      render(
        <PlotPanel
          plotRef={{ current: null }}
          loading={false}
          error={null}
          hasData={true}
          plotTestId="test-plot"
        />,
      );
      const plotDiv = screen.getByTestId("test-plot");
      expect(plotDiv.className).not.toMatch(/hidden/);
    });

    it("test_noData_hidesPlotDiv", () => {
      render(
        <PlotPanel
          plotRef={{ current: null }}
          loading={false}
          error={null}
          hasData={false}
          plotTestId="test-plot"
        />,
      );
      const plotDiv = screen.getByTestId("test-plot");
      expect(plotDiv.className).toMatch(/hidden/);
    });

    it("test_error_hidesPlotDiv", () => {
      render(
        <PlotPanel
          plotRef={{ current: null }}
          loading={false}
          error="エラー"
          hasData={true}
          plotTestId="test-plot"
        />,
      );
      const plotDiv = screen.getByTestId("test-plot");
      expect(plotDiv.className).toMatch(/hidden/);
    });

    it("test_loading_plotDivHasOpacity", () => {
      render(
        <PlotPanel
          plotRef={{ current: null }}
          loading={true}
          error={null}
          hasData={true}
          plotTestId="test-plot"
        />,
      );
      const plotDiv = screen.getByTestId("test-plot");
      expect(plotDiv.className).toMatch(/opacity-30/);
    });
  });

  describe("testId", () => {
    it("test_testId_setsContainerTestId", () => {
      render(
        <PlotPanel
          plotRef={{ current: null }}
          loading={false}
          error={null}
          hasData={false}
          testId="my-panel"
        />,
      );
      expect(screen.getByTestId("my-panel")).toBeInTheDocument();
    });
  });
});
