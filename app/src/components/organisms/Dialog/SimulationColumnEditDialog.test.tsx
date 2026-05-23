/**
 * SimulationColumnEditDialog のテスト
 * - フッターに「分布プレビュー」ボタンが表示される
 * - クリックすると DistributionPreview ワークタブが openWorkTab で開かれる
 * - distributionType 未設定の列は normal + デフォルトパラメータで開く
 */
import { SimulationColumnEditDialog } from "@/components/organisms/Dialog/SimulationColumnEditDialog";
import { DIST_PARAM_DEFAULTS } from "@/constants/simulation";
import { useWorkspaceTabsStore } from "@/stores/workspaceTabs";
import type { SimulationColumnSetting } from "@/types/commonTypes";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (key: string) => key }),
}));

vi.mock("../Form/SimulationColumnConfig", () => ({
  SimulationColumnConfig: () => <div data-testid="sim-column-config" />,
}));

const defaultColumn: SimulationColumnSetting = {
  id: "col-1",
  columnName: "sales",
  dataType: "distribution",
  distributionType: "normal",
  distributionParams: { mean: 0, standardDeviation: 1 },
  fixedValue: "",
  errorMessage: {
    columnName: undefined,
    distributionParams: undefined,
    fixedValue: undefined,
  },
};

const defaultProps = {
  isOpen: true,
  column: defaultColumn,
  index: 0,
  onSave: vi.fn(),
  onRemove: vi.fn(),
  onClose: vi.fn(),
  canRemove: true,
};

beforeEach(() => {
  vi.clearAllMocks();
  Object.assign(Element.prototype, {
    setPointerCapture: vi.fn(),
    releasePointerCapture: vi.fn(),
  });
  useWorkspaceTabsStore.setState({ tabs: [], activeTabId: null });
});

describe("SimulationColumnEditDialog", () => {
  describe("分布プレビューボタン", () => {
    it("フッターに「分布プレビュー」ボタンが表示される", () => {
      render(<SimulationColumnEditDialog {...defaultProps} />);
      expect(
        screen.getByTestId("open-distribution-preview-btn"),
      ).toBeInTheDocument();
    });

    it("test_previewButton_opensDistributionPreviewTab", async () => {
      const user = userEvent.setup();
      render(<SimulationColumnEditDialog {...defaultProps} />);

      await user.click(screen.getByTestId("open-distribution-preview-btn"));

      const { tabs, activeTabId } = useWorkspaceTabsStore.getState();
      const tab = tabs.find((t) => t.id === "work:DistributionPreview");
      expect(tab).toBeDefined();
      expect(activeTabId).toBe("work:DistributionPreview");
    });

    it("test_previewButton_passesDraftValues_normal", async () => {
      const user = userEvent.setup();
      render(<SimulationColumnEditDialog {...defaultProps} />);

      await user.click(screen.getByTestId("open-distribution-preview-btn"));

      const { tabs } = useWorkspaceTabsStore.getState();
      const tab = tabs.find((t) => t.id === "work:DistributionPreview");
      expect(tab?.kind).toBe("work");
      if (tab?.kind === "work") {
        const draft = tab.draftValues as {
          distributionType: string;
          distributionParams: Record<string, number>;
        };
        expect(draft.distributionType).toBe("normal");
        expect(draft.distributionParams).toEqual({
          mean: 0,
          standardDeviation: 1,
        });
      }
    });

    it("test_previewButton_fixedColumn_fallsBackToNormalDefault", async () => {
      const user = userEvent.setup();
      const fixedColumn: SimulationColumnSetting = {
        ...defaultColumn,
        dataType: "fixed",
        distributionType: undefined,
        distributionParams: undefined,
      };
      render(
        <SimulationColumnEditDialog {...defaultProps} column={fixedColumn} />,
      );

      await user.click(screen.getByTestId("open-distribution-preview-btn"));

      const { tabs } = useWorkspaceTabsStore.getState();
      const tab = tabs.find((t) => t.id === "work:DistributionPreview");
      expect(tab?.kind).toBe("work");
      if (tab?.kind === "work") {
        const draft = tab.draftValues as {
          distributionType: string;
          distributionParams: Record<string, number>;
        };
        expect(draft.distributionType).toBe("normal");
        expect(draft.distributionParams).toEqual(DIST_PARAM_DEFAULTS["normal"]);
      }
    });
  });
});
