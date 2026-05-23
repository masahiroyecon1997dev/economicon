import { MainView } from "@/components/pages/MainView";
import type { CurrentPageValue } from "@/stores/currentPage";
import { useCurrentPageStore } from "@/stores/currentPage";
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
    ["SaveData", "page-SaveData"],
    ["Workspace", "page-WorkspaceSurface"],
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
    expect(screen.queryByTestId("page-SaveData")).toBeNull();
    expect(screen.queryByTestId("page-WorkspaceSurface")).toBeNull();
  });
});
