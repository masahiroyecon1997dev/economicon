/**
 * AddDummyColumnForm のテスト
 * - 初期 mode="single": targetValue・dummyColumnName フィールドが表示される
 * - 初期 mode="all_except_base": dropBaseValue フィールドが表示されない（初期値はsingle）
 * - API成功 → onSuccess が呼ばれる
 * - API失敗 → ErrorAlert に APIのmessage が表示される
 * - throw → ErrorAlert にエラーメッセージが表示される
 */
import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { getEconomiconAPI } from "../../../../api/endpoints";
import { AddDummyColumnForm } from "./AddDummyColumnForm";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------
vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (key: string) => key }),
}));

vi.mock("../../../../api/endpoints");

vi.mock("./fetchUpdatedColumnList", () => ({
  fetchUpdatedColumnList: vi
    .fn()
    .mockResolvedValue([{ name: "is_price", type: "Boolean" }]),
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const mockApi = {
  addDummyColumn: vi.fn(),
};

const column = { name: "price", type: "Float64" };

const defaultProps = {
  tableName: "sales",
  column,
  formId: "add-dummy-form",
  onIsSubmittingChange: vi.fn(),
  onSuccess: vi.fn(),
};

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(getEconomiconAPI).mockReturnValue(mockApi as never);
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("AddDummyColumnForm", () => {
  describe("初期表示 (mode = single)", () => {
    it("TargetValue フィールドが表示される", () => {
      render(<AddDummyColumnForm {...defaultProps} />);
      // t("AddDummyColumnForm.TargetValue") = "AddDummyColumnForm.TargetValue"
      expect(
        screen.getByText("AddDummyColumnForm.TargetValue"),
      ).toBeInTheDocument();
    });

    it("DummyColumnName フィールドが表示され、デフォルト値は 'is_price' になる", () => {
      render(<AddDummyColumnForm {...defaultProps} />);
      expect(
        screen.getByText("AddDummyColumnForm.DummyColumnName"),
      ).toBeInTheDocument();
      expect(screen.getByDisplayValue("is_price")).toBeInTheDocument();
    });

    it("DropBaseValue フィールドは初期状態では表示されない", () => {
      render(<AddDummyColumnForm {...defaultProps} />);
      expect(
        screen.queryByText("AddDummyColumnForm.DropBaseValue"),
      ).not.toBeInTheDocument();
    });
  });

  describe("API成功時", () => {
    it("addDummyColumn が OK → onSuccess が最新 columnList を引数に呼ばれる", async () => {
      mockApi.addDummyColumn.mockResolvedValue({ code: "OK", result: {} });

      render(<AddDummyColumnForm {...defaultProps} />);

      const form = document.getElementById("add-dummy-form")!;
      form.dispatchEvent(new Event("submit", { bubbles: true }));

      await waitFor(() => {
        expect(defaultProps.onSuccess).toHaveBeenCalledWith([
          { name: "is_price", type: "Boolean" },
        ]);
      });
    });
  });

  describe("API失敗時", () => {
    it("code ≠ OK → ErrorAlert に APIのmessage が表示される", async () => {
      mockApi.addDummyColumn.mockResolvedValue({
        code: "COLUMN_NAME_CONFLICT",
        message: "その列名はすでに存在します",
      });

      render(<AddDummyColumnForm {...defaultProps} />);

      const form = document.getElementById("add-dummy-form")!;
      form.dispatchEvent(new Event("submit", { bubbles: true }));

      await waitFor(() => {
        expect(
          screen.getByText("その列名はすでに存在します"),
        ).toBeInTheDocument();
      });
    });

    it("APIがthrowした場合 → ErrorAlert にエラーメッセージが表示される", async () => {
      mockApi.addDummyColumn.mockRejectedValue(new Error("接続タイムアウト"));

      render(<AddDummyColumnForm {...defaultProps} />);

      const form = document.getElementById("add-dummy-form")!;
      form.dispatchEvent(new Event("submit", { bubbles: true }));

      await waitFor(() => {
        expect(screen.getByText("接続タイムアウト")).toBeInTheDocument();
      });
    });
  });
});
