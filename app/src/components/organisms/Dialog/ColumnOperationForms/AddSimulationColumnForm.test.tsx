/**
 * AddSimulationColumnForm のテスト
 * - 列名フィールドのデフォルト値は "sim_price"
 * - デフォルト分布タイプ "normal" のラジオが選択済み
 * - normal のパラメータ (Loc / Scale) が表示される
 * - 分布タイプ切り替え（全14種）: 対応するパラメータフィールドが表示される
 * - 列名を空にして blur → ValidationMessages.NewColumnNameRequired が表示される
 * - 乱数シードに負数を入力してサブミット → ValidationMessages.RandomSeedRange（ErrorAlert）
 * - 乱数シードに小数を入力してサブミット → ValidationMessages.RandomSeedRange（ErrorAlert）
 * - API成功 → onSuccess が最新 columnList を引数に呼ばれる
 * - API失敗 → ErrorAlert に APIのmessage が表示される
 * - throw → ErrorAlert にエラーメッセージが表示される
 */
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { act } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { getEconomiconAppAPI } from "@/api/endpoints";
import {
  DIST_PARAM_LABEL_KEYS,
  DIST_PARAMS,
  DIST_TYPES,
} from "@/constants/simulation";
import { AddSimulationColumnForm } from "@/components/organisms/Dialog/ColumnOperationForms/AddSimulationColumnForm";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------
vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (key: string) => key }),
}));

vi.mock("../../../../api/endpoints");

vi.mock("./fetchUpdatedColumnList", () => ({
  fetchUpdatedColumnList: vi.fn().mockResolvedValue([
    { name: "price", type: "Float64" },
    { name: "sim_price", type: "Float64" },
  ]),
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const mockApi = {
  addSimulationColumn: vi.fn(),
};

const column = { name: "price", type: "Float64" };

const defaultProps = {
  tableName: "sales",
  column,
  formId: "sim-col-form",
  onIsSubmittingChange: vi.fn(),
  onSuccess: vi.fn(),
};

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(getEconomiconAppAPI).mockReturnValue(mockApi as never);
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("AddSimulationColumnForm", () => {
  describe("初期表示", () => {
    it("列名フィールドのデフォルト値は 'sim_price' である", () => {
      render(<AddSimulationColumnForm {...defaultProps} />);
      expect(screen.getByDisplayValue("sim_price")).toBeInTheDocument();
    });

    it("デフォルト分布タイプ 'normal' のラジオが選択されている", () => {
      render(<AddSimulationColumnForm {...defaultProps} />);
      const radio = screen.getByRole("radio", {
        name: /AddSimulationColumnForm\.normal/i,
      });
      expect(radio).toBeChecked();
    });

    it("normal のパラメータ (Loc / Scale) が表示される", () => {
      render(<AddSimulationColumnForm {...defaultProps} />);
      expect(
        screen.getByText("AddSimulationColumnForm.Loc"),
      ).toBeInTheDocument();
      expect(
        screen.getByText("AddSimulationColumnForm.Scale"),
      ).toBeInTheDocument();
    });
  });

  describe("分布タイプ切り替え（全14種）", () => {
    it.each(DIST_TYPES)(
      "distributionType = %s に切り替えると対応するパラメータフィールドが表示される",
      async (distType) => {
        render(<AddSimulationColumnForm {...defaultProps} />);

        const radio = screen.getByRole("radio", {
          name: new RegExp(`AddSimulationColumnForm\\.${distType}`, "i"),
        });
        await act(async () => {
          radio.click();
        });

        for (const param of DIST_PARAMS[distType]) {
          await waitFor(() => {
            expect(
              screen.getByText(DIST_PARAM_LABEL_KEYS[param]),
            ).toBeInTheDocument();
          });
        }
      },
    );
  });

  describe("バリデーション", () => {
    it("列名を空にして blur → ValidationMessages.NewColumnNameRequired が表示される", async () => {
      const user = userEvent.setup();
      render(<AddSimulationColumnForm {...defaultProps} />);

      const nameInput = screen.getByRole("textbox", {
        name: /AddSimulationColumnForm\.ColumnName/i,
      });
      await user.clear(nameInput);
      await user.tab();

      await waitFor(() => {
        expect(
          screen.getByText("ValidationMessages.NewColumnNameRequired"),
        ).toBeInTheDocument();
      });
    });

    it("乱数シードに負数を入力してサブミット → ErrorAlert に ValidationMessages.RandomSeedRange が表示される", async () => {
      render(<AddSimulationColumnForm {...defaultProps} />);

      const seedInput = screen.getByRole("spinbutton", {
        name: /Common\.RandomSeed/i,
      });
      fireEvent.change(seedInput, { target: { value: "-1" } });

      const form = document.getElementById("sim-col-form")!;
      form.dispatchEvent(new Event("submit", { bubbles: true }));

      await waitFor(() => {
        expect(
          screen.getByText("ValidationMessages.RandomSeedRange"),
        ).toBeInTheDocument();
      });
    });

    it("乱数シードに小数を入力してサブミット → ErrorAlert に ValidationMessages.RandomSeedRange が表示される", async () => {
      render(<AddSimulationColumnForm {...defaultProps} />);

      const seedInput = screen.getByRole("spinbutton", {
        name: /Common\.RandomSeed/i,
      });
      fireEvent.change(seedInput, { target: { value: "1.5" } });

      const form = document.getElementById("sim-col-form")!;
      form.dispatchEvent(new Event("submit", { bubbles: true }));

      await waitFor(() => {
        expect(
          screen.getByText("ValidationMessages.RandomSeedRange"),
        ).toBeInTheDocument();
      });
    });
  });

  describe("API成功時", () => {
    it("addSimulationColumn が OK → onSuccess が最新 columnList を引数に呼ばれる", async () => {
      mockApi.addSimulationColumn.mockResolvedValue({ code: "OK", result: {} });

      render(<AddSimulationColumnForm {...defaultProps} />);

      const form = document.getElementById("sim-col-form")!;
      form.dispatchEvent(new Event("submit", { bubbles: true }));

      await waitFor(() => {
        expect(defaultProps.onSuccess).toHaveBeenCalledWith([
          { name: "price", type: "Float64" },
          { name: "sim_price", type: "Float64" },
        ]);
      });
    });
  });

  describe("API失敗時", () => {
    it("code ≠ OK → ErrorAlert に APIのmessage が表示される", async () => {
      mockApi.addSimulationColumn.mockResolvedValue({
        code: "COLUMN_NAME_CONFLICT",
        message: "その列名はすでに存在します",
      });

      render(<AddSimulationColumnForm {...defaultProps} />);

      const form = document.getElementById("sim-col-form")!;
      form.dispatchEvent(new Event("submit", { bubbles: true }));

      await waitFor(() => {
        expect(
          screen.getByText("その列名はすでに存在します"),
        ).toBeInTheDocument();
      });
    });

    it("APIがthrowした場合 → ErrorAlert にエラーメッセージが表示される", async () => {
      mockApi.addSimulationColumn.mockRejectedValue(
        new Error("接続タイムアウト"),
      );

      render(<AddSimulationColumnForm {...defaultProps} />);

      const form = document.getElementById("sim-col-form")!;
      form.dispatchEvent(new Event("submit", { bubbles: true }));

      await waitFor(() => {
        expect(screen.getByText("接続タイムアウト")).toBeInTheDocument();
      });
    });
  });
});
