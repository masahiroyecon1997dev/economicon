import { MainView } from "@/components/pages/MainView";
import type { CurrentPageValue } from "@/stores/currentView";
import { useCurrentPageStore } from "@/stores/currentView";
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}));

// 各ページコンポーネントをスタブ化して render 対象を限定する
vi.mock("./ImportDataFile", () => ({
  ImportDataFile: () => <div data-testid="page-ImportDataFile" />,
}));
vi.mock("./DescriptiveStatistics", () => ({
  DescriptiveStatistics: () => <div data-testid="page-DescriptiveStatistics" />,
}));
vi.mock("./SaveData", () => ({
  SaveData: () => <div data-testid="page-SaveData" />,
}));
vi.mock("./WorkspaceSurface", () => ({
  WorkspaceSurface: () => <div data-testid="page-WorkspaceSurface" />,
}));

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("MainView コンポーネント", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const PAGE_CASES: Array<[CurrentPageValue, string]> = [
    ["ImportDataFile", "page-ImportDataFile"],
    ["JoinTable", "page-WorkspaceSurface"],
    ["UnionTable", "page-WorkspaceSurface"],
    ["DescriptiveStatistics", "page-DescriptiveStatistics"],
    ["CorrelationMatrix", "page-WorkspaceSurface"],
    ["ConfidenceIntervalView", "page-WorkspaceSurface"],
    ["LinearRegressionForm", "page-WorkspaceSurface"],
    ["CreateSimulationDataTable", "page-WorkspaceSurface"],
    ["CalculationView", "page-WorkspaceSurface"],
    ["SaveData", "page-SaveData"],
    ["AnalysisResultPreview", "page-WorkspaceSurface"],
    ["DataPreview", "page-WorkspaceSurface"],
  ];

  it.each(PAGE_CASES)(
    "currentView = %s のとき %s コンポーネントが表示される",
    (view, testId) => {
      useCurrentPageStore.setState({ currentView: view });
      render(<MainView />);
      expect(screen.getByTestId(testId)).toBeInTheDocument();
    },
  );

  it("表示されるのは currentView に対応したコンポーネント1つのみ", () => {
    useCurrentPageStore.setState({ currentView: "ImportDataFile" });
    render(<MainView />);

    // ImportDataFile のみ表示
    expect(screen.getByTestId("page-ImportDataFile")).toBeInTheDocument();
    // 他のページは表示されない（MainView は currentView に応じて切り替える）
    expect(screen.queryByTestId("page-JoinTable")).toBeNull();
  });
});
