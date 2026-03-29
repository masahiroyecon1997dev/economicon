import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { CurrentPageValue } from "../../stores/currentView";
import { useCurrentPageStore } from "../../stores/currentView";
import { MainView } from "./MainView";

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
vi.mock("./JoinTable", () => ({
  JoinTable: () => <div data-testid="page-JoinTable" />,
}));
vi.mock("./UnionTable", () => ({
  UnionTable: () => <div data-testid="page-UnionTable" />,
}));
vi.mock("./DescriptiveStatistics", () => ({
  DescriptiveStatistics: () => <div data-testid="page-DescriptiveStatistics" />,
}));
vi.mock("./CorrelationMatrix", () => ({
  CorrelationMatrix: () => <div data-testid="page-CorrelationMatrix" />,
}));
vi.mock("./RegressionView", () => ({
  Regression: () => <div data-testid="page-LinearRegressionForm" />,
}));
vi.mock("./CreateSimulationDataTable", () => ({
  CreateSimulationDataTable: () => (
    <div data-testid="page-CreateSimulationDataTable" />
  ),
}));
vi.mock("./Calculation", () => ({
  Calculation: () => <div data-testid="page-CalculationView" />,
}));
vi.mock("./SaveData", () => ({
  SaveData: () => <div data-testid="page-SaveData" />,
}));
vi.mock("./Table", () => ({
  Table: () => <div data-testid="page-DataPreview" />,
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
    ["JoinTable", "page-JoinTable"],
    ["UnionTable", "page-UnionTable"],
    ["DescriptiveStatistics", "page-DescriptiveStatistics"],
    ["CorrelationMatrix", "page-CorrelationMatrix"],
    ["LinearRegressionForm", "page-LinearRegressionForm"],
    ["CreateSimulationDataTable", "page-CreateSimulationDataTable"],
    ["CalculationView", "page-CalculationView"],
    ["SaveData", "page-SaveData"],
    ["DataPreview", "page-DataPreview"],
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
