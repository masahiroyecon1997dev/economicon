/**
 * AddSimulationColumnForm のテスト
 * - 列名フィールドのデフォルト値は "sim_price"
 * - デフォルト分布タイプ "normal" のラジオが選択済み
 * - normal のパラメータ (Mean / StandardDeviation) が表示される
 * - 分布タイプ切り替え（全14種）: 対応するパラメータフィールドが表示される
 * - 列名を空にして blur → ValidationMessages.NewColumnNameRequired が表示される
 * - 乱数シードに負数を入力してサブミット → ValidationMessages.RandomSeedRange（ErrorAlert）
 * - 乱数シードに小数を入力してサブミット → ValidationMessages.RandomSeedRange（ErrorAlert）
 * - API成功 → onSuccess が最新 columnList を引数に呼ばれる
 * - API失敗 → ErrorAlert に APIのmessage が表示される
 * - throw → ErrorAlert にエラーメッセージが表示される
 */
import { getEconomiconAppAPI } from "@/api/endpoints";
import { AddSimulationColumnForm } from "@/components/organisms/Dialog/ColumnOperationForms/AddSimulationColumnForm";
import {
  DIST_PARAM_LABEL_KEYS,
  DIST_PARAMS,
  DIST_TYPES,
} from "@/constants/simulation";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

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

const submitForm = () => {
  const form = document.getElementById("sim-col-form");
  expect(form).toBeInstanceOf(HTMLFormElement);
  fireEvent.submit(form as HTMLFormElement);
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

    it("normal のパラメータ (Mean / StandardDeviation) が表示される", () => {
      render(<AddSimulationColumnForm {...defaultProps} />);
      expect(
        screen.getByText("AddSimulationColumnForm.Mean"),
      ).toBeInTheDocument();
      expect(
        screen.getByText("AddSimulationColumnForm.StandardDeviation"),
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
        fireEvent.click(radio);

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
      const user = userEvent.setup();
      render(<AddSimulationColumnForm {...defaultProps} />);

      const seedInput = screen.getByRole("spinbutton", {
        name: /Common\.RandomSeed/i,
      });
      await user.clear(seedInput);
      await user.type(seedInput, "-1");

      submitForm();

      await waitFor(() => {
        expect(
          screen.getByText("ValidationMessages.RandomSeedRange"),
        ).toBeInTheDocument();
      });
    });

    it("乱数シードに小数を入力してサブミット → ErrorAlert に ValidationMessages.RandomSeedRange が表示される", async () => {
      const user = userEvent.setup();
      render(<AddSimulationColumnForm {...defaultProps} />);

      const seedInput = screen.getByRole("spinbutton", {
        name: /Common\.RandomSeed/i,
      });
      await user.clear(seedInput);
      await user.type(seedInput, "1.5");

      submitForm();

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

      submitForm();

      await waitFor(() => {
        expect(defaultProps.onSuccess).toHaveBeenCalledWith([
          { name: "price", type: "Float64" },
          { name: "sim_price", type: "Float64" },
        ]);
      });
    });

    it("distributionType = sequence で start と step を送信できる", async () => {
      const user = userEvent.setup();
      mockApi.addSimulationColumn.mockResolvedValue({ code: "OK", result: {} });

      render(<AddSimulationColumnForm {...defaultProps} />);

      const radio = screen.getByRole("radio", {
        name: /AddSimulationColumnForm\.sequence/i,
      });
      fireEvent.click(radio);

      await waitFor(() => {
        expect(
          screen.getByText("AddSimulationColumnForm.Start"),
        ).toBeInTheDocument();
      });

      const startInput = document.getElementById("sim-param-start");
      const stepInput = document.getElementById("sim-param-step");

      expect(startInput).toBeInstanceOf(HTMLInputElement);
      expect(stepInput).toBeInstanceOf(HTMLInputElement);

      await user.clear(startInput as HTMLInputElement);
      await user.type(startInput as HTMLInputElement, "10");
      await user.clear(stepInput as HTMLInputElement);
      await user.type(stepInput as HTMLInputElement, "-2");

      submitForm();

      await waitFor(() => {
        expect(mockApi.addSimulationColumn).toHaveBeenCalledWith(
          expect.objectContaining({
            simulationColumn: expect.objectContaining({
              distribution: {
                type: "sequence",
                start: 10,
                step: -2,
              },
            }),
          }),
        );
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

      submitForm();

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

      submitForm();

      await waitFor(() => {
        expect(screen.getByText("接続タイムアウト")).toBeInTheDocument();
      });
    });
  });
});
