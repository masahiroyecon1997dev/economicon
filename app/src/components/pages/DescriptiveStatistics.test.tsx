import { getEconomiconAppAPI } from "@/api/endpoints";
import { DescriptiveStatisticType } from "@/api/model";
import { DescriptiveStatistics } from "@/components/pages/DescriptiveStatistics";
import { showMessageDialog } from "@/lib/dialog/message";
import { useTableListStore } from "@/stores/tableList";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------
const fixedT = (key: string, opts?: Record<string, string>) => {
  if (!opts) return key;
  return Object.entries(opts).reduce(
    (s, [k, v]) => s.replace(`{{${k}}}`, v),
    key,
  );
};

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: fixedT,
  }),
}));

vi.mock("../../api/endpoints");
vi.mock("../../lib/dialog/message", () => ({
  showMessageDialog: vi.fn().mockResolvedValue(undefined),
}));
vi.mock("../../stores/currentView", () => ({
  useCurrentPageStore: vi.fn(() => ({ setCurrentView: vi.fn() })),
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const COLUMNS = [
  { name: "price", type: "Float64" },
  { name: "quantity", type: "Int64" },
];

const mockApi = {
  getColumnList: vi.fn(),
  descriptiveStatistics: vi.fn(),
  getAnalysisResult: vi.fn(),
  outputResult: vi.fn(),
};

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(getEconomiconAppAPI).mockReturnValue(mockApi as never);
  useTableListStore.setState({ tableList: ["sales"] });
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("DescriptiveStatistics フォーム", () => {
  describe("バリデーション", () => {
    it("テーブル未選択でサブミットするとテーブル選択エラーが表示される", async () => {
      const user = userEvent.setup();
      render(<DescriptiveStatistics />);

      const submitBtn = screen.getByRole("button", {
        name: "DescriptiveStatistics.RunCalculation",
      });
      await user.click(submitBtn);

      await waitFor(() => {
        expect(
          screen.getByText("DescriptiveStatistics.ErrorDataRequired"),
        ).toBeInTheDocument();
      });
    });

    it("列チェックが0件でサブミットするとエラーが表示される", async () => {
      mockApi.getColumnList.mockResolvedValue({
        code: "OK",
        result: { columnInfoList: COLUMNS },
      });
      const user = userEvent.setup();
      render(<DescriptiveStatistics />);

      // テーブルを選択（Select コンポーネント）
      const selectTrigger = screen.getByRole("combobox");
      await user.click(selectTrigger);
      const option = await screen.findByRole("option", { name: "sales" });
      await user.click(option);

      // 列チェックをすべて外す
      await waitFor(() => {
        expect(screen.getByText("price")).toBeInTheDocument();
      });
      const deselectAllBtn = screen.getAllByRole("button", {
        name: /DeselectAll|すべて解除/i,
      })[0];
      await user.click(deselectAllBtn);

      const submitBtn = screen.getByRole("button", {
        name: "DescriptiveStatistics.RunCalculation",
      });
      await user.click(submitBtn);

      await waitFor(() => {
        expect(
          screen.getByText("DescriptiveStatistics.ErrorColumnsRequired"),
        ).toBeInTheDocument();
      });
    });
  });

  describe("API成功時 — 統計値の表示", () => {
    const setupWithResult = async (statistics: Record<string, unknown>) => {
      mockApi.getColumnList.mockResolvedValue({
        code: "OK",
        result: { columnInfoList: [{ name: "price", type: "Float64" }] },
      });
      mockApi.descriptiveStatistics.mockResolvedValue({
        code: "OK",
        result: { resultId: "test-result-id" },
      });
      mockApi.getAnalysisResult.mockResolvedValue({
        code: "OK",
        result: { resultData: { statistics } },
      });

      const user = userEvent.setup();
      render(<DescriptiveStatistics />);

      const selectTrigger = screen.getByRole("combobox");
      await user.click(selectTrigger);
      const option = await screen.findByRole("option", { name: "sales" });
      await user.click(option);

      await waitFor(() =>
        expect(screen.getByText("price")).toBeInTheDocument(),
      );

      const submitBtn = screen.getByRole("button", {
        name: "DescriptiveStatistics.RunCalculation",
      });
      await user.click(submitBtn);

      await waitFor(() =>
        expect(
          screen.getByText("DescriptiveStatistics.ResultTitle"),
        ).toBeInTheDocument(),
      );
    };

    it("数値の平均値が小数点4桁でフォーマットされて表示される", async () => {
      await setupWithResult({
        price: { [DescriptiveStatisticType.mean]: 24.5 },
      });
      expect(screen.getByText("24.5000")).toBeInTheDocument();
    });

    it("null値は '—' として表示される（'null' 文字列は表示されない）", async () => {
      await setupWithResult({
        price: { [DescriptiveStatisticType.mean]: null },
      });
      // null は "—" でレンダリングされる（他の未指定統計量も "—" になるため getAllByText を使用）
      const dashCells = screen.getAllByText("—");
      expect(dashCells.length).toBeGreaterThan(0);
      expect(screen.queryByText("null")).not.toBeInTheDocument();
    });

    it("mode が配列値の場合はカンマ区切りで表示される", async () => {
      await setupWithResult({
        price: { [DescriptiveStatisticType.mode]: [1, 2, 3] },
      });
      expect(screen.getByText("1, 2, 3")).toBeInTheDocument();
    });

    it("整数値はlocale形式（桁区切り）で表示される", async () => {
      await setupWithResult({
        price: { [DescriptiveStatisticType.mean]: 1000 },
      });
      // toLocaleString() の結果（環境により1,000 or 1000）
      const cell = screen.getByText(/1.000|1000/);
      expect(cell).toBeInTheDocument();
    });
  });

  describe("API失敗時", () => {
    it("getColumnList がthrowした場合 → エラーダイアログを表示する", async () => {
      mockApi.getColumnList.mockRejectedValue(new Error("ネットワークエラー"));
      const user = userEvent.setup();
      render(<DescriptiveStatistics />);

      const selectTrigger = screen.getByRole("combobox");
      await user.click(selectTrigger);
      const option = await screen.findByRole("option", { name: "sales" });
      await user.click(option);

      await waitFor(() => {
        expect(vi.mocked(showMessageDialog)).toHaveBeenCalled();
      });
    });

    it("descriptiveStatistics がthrowした場合 → エラーダイアログを表示する", async () => {
      mockApi.getColumnList.mockResolvedValue({
        code: "OK",
        result: { columnInfoList: [{ name: "price", type: "Float64" }] },
      });
      mockApi.descriptiveStatistics.mockRejectedValue(
        new Error("サーバーエラー"),
      );

      const user = userEvent.setup();
      render(<DescriptiveStatistics />);

      const selectTrigger = screen.getByRole("combobox");
      await user.click(selectTrigger);
      const option = await screen.findByRole("option", { name: "sales" });
      await user.click(option);

      await waitFor(() =>
        expect(screen.getByText("price")).toBeInTheDocument(),
      );

      const submitBtn = screen.getByRole("button", {
        name: "DescriptiveStatistics.RunCalculation",
      });
      await user.click(submitBtn);

      await waitFor(() => {
        expect(vi.mocked(showMessageDialog)).toHaveBeenCalled();
      });
    });

    it("getAnalysisResult がthrowした場合 → エラーダイアログを表示する", async () => {
      mockApi.getColumnList.mockResolvedValue({
        code: "OK",
        result: { columnInfoList: [{ name: "price", type: "Float64" }] },
      });
      mockApi.descriptiveStatistics.mockResolvedValue({
        code: "OK",
        result: { resultId: "test-result-id" },
      });
      mockApi.getAnalysisResult.mockRejectedValue(new Error("詳細取得エラー"));

      const user = userEvent.setup();
      render(<DescriptiveStatistics />);

      const selectTrigger = screen.getByRole("combobox");
      await user.click(selectTrigger);
      const option = await screen.findByRole("option", { name: "sales" });
      await user.click(option);

      await waitFor(() =>
        expect(screen.getByText("price")).toBeInTheDocument(),
      );

      const submitBtn = screen.getByRole("button", {
        name: "DescriptiveStatistics.RunCalculation",
      });
      await user.click(submitBtn);

      await waitFor(() => {
        expect(vi.mocked(showMessageDialog)).toHaveBeenCalled();
      });
    });
  });

  describe("出力ボタン", () => {
    const setupWithResult = async () => {
      mockApi.getColumnList.mockResolvedValue({
        code: "OK",
        result: { columnInfoList: [{ name: "price", type: "Float64" }] },
      });
      mockApi.descriptiveStatistics.mockResolvedValue({
        code: "OK",
        result: { resultId: "result-123" },
      });
      mockApi.getAnalysisResult.mockResolvedValue({
        code: "OK",
        result: {
          resultData: {
            statistics: {
              price: { [DescriptiveStatisticType.mean]: 10 },
            },
          },
        },
      });

      const user = userEvent.setup();
      render(<DescriptiveStatistics />);

      const selectTrigger = screen.getByRole("combobox");
      await user.click(selectTrigger);
      const option = await screen.findByRole("option", { name: "sales" });
      await user.click(option);

      await waitFor(() =>
        expect(screen.getByText("price")).toBeInTheDocument(),
      );

      const submitBtn = screen.getByRole("button", {
        name: "DescriptiveStatistics.RunCalculation",
      });
      await user.click(submitBtn);

      await waitFor(() =>
        expect(
          screen.getByText("DescriptiveStatistics.ResultTitle"),
        ).toBeInTheDocument(),
      );

      return user;
    };

    it("計算成功後にクイックコピーボタンと出力ダイアログボタンが表示される", async () => {
      await setupWithResult();
      expect(screen.getByTestId("ds-quick-copy-btn")).toBeInTheDocument();
      expect(screen.getByTestId("ds-output-dialog-btn")).toBeInTheDocument();
    });

    it("クイックコピーボタンクリックで outputResult が markdown 形式で呼ばれる", async () => {
      mockApi.outputResult = vi.fn().mockResolvedValue({
        code: "OK",
        result: { content: "| col | mean |\n|-----|------|\n| price | 10 |" },
      });
      const user = await setupWithResult();

      const writeTextMock = vi.fn().mockResolvedValue(undefined);
      vi.spyOn(navigator.clipboard, "writeText").mockImplementation(
        writeTextMock,
      );

      const copyBtn = screen.getByTestId("ds-quick-copy-btn");
      await user.click(copyBtn);

      await waitFor(() => {
        expect(mockApi.outputResult).toHaveBeenCalledWith(
          expect.objectContaining({
            resultType: "descriptive_statistics",
            resultIds: ["result-123"],
            format: "markdown",
          }),
        );
      });
    });

    it("出力ダイアログボタンクリックでダイアログが開く", async () => {
      mockApi.outputResult = vi.fn().mockResolvedValue({
        code: "OK",
        result: { content: "preview text" },
      });
      const user = await setupWithResult();

      const dialogBtn = screen.getByTestId("ds-output-dialog-btn");
      await user.click(dialogBtn);

      await waitFor(() => {
        expect(
          screen.getByText("OutputResultDialog.Title"),
        ).toBeInTheDocument();
      });
    });
  });
});
