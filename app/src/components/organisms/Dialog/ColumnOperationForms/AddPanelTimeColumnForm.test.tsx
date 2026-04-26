import { getEconomiconAppAPI } from "@/api/endpoints";
import { AddPanelTimeColumnForm } from "@/components/organisms/Dialog/ColumnOperationForms/AddPanelTimeColumnForm";
import { useTableInfosStore } from "@/stores/tableInfos";
import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (key: string) => key }),
}));

vi.mock("../../../../api/endpoints");

vi.mock("./fetchUpdatedColumnList", () => ({
  fetchUpdatedColumnList: vi
    .fn()
    .mockResolvedValue([{ name: "time_customer_id", type: "Int64" }]),
}));

const mockApi = {
  addPanelTimeColumn: vi.fn(),
};

const defaultProps = {
  tableName: "sales",
  column: { name: "firm_id", type: "Int64" },
  formId: "add-panel-time-form",
  onIsSubmittingChange: vi.fn(),
  onSuccess: vi.fn(),
};

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(getEconomiconAppAPI).mockReturnValue(mockApi as never);
  useTableInfosStore.setState({
    tableInfos: [
      {
        tableName: "sales",
        columnList: [
          { name: "firm_id", type: "Int64" },
          { name: "customer_id", type: "Int64" },
          { name: "sales", type: "Float64" },
        ],
        totalRows: 3,
        isActive: true,
      },
    ],
    activeTableName: "sales",
  });
});

describe("AddPanelTimeColumnForm", () => {
  it("初期表示で右クリック列が idColumn に入り、新列名が time_列名 になる", () => {
    render(<AddPanelTimeColumnForm {...defaultProps} />);

    expect(
      within(screen.getByTestId("panel-time-id-column")).getByRole("combobox"),
    ).toHaveTextContent("firm_id");
    expect(screen.getByDisplayValue("time_firm_id")).toBeInTheDocument();
  });

  it("idColumn 変更時、列名が既定値のままなら time_選択列名 に更新される", async () => {
    const user = userEvent.setup();
    render(<AddPanelTimeColumnForm {...defaultProps} />);

    const idColumnWrapper = screen.getByTestId("panel-time-id-column");
    const trigger = within(idColumnWrapper).getByRole("combobox");

    await user.click(trigger);
    await user.click(screen.getByRole("option", { name: "customer_id" }));

    await waitFor(() => {
      expect(screen.getByDisplayValue("time_customer_id")).toBeInTheDocument();
    });
  });

  it("idColumn 変更前に列名を編集していれば、自動更新しない", async () => {
    const user = userEvent.setup();
    render(<AddPanelTimeColumnForm {...defaultProps} />);

    const nameInput = screen.getByTestId("panel-time-new-column-name");
    await user.clear(nameInput);
    await user.type(nameInput, "custom_time_name");

    const idColumnWrapper = screen.getByTestId("panel-time-id-column");
    const trigger = within(idColumnWrapper).getByRole("combobox");

    await user.click(trigger);
    await user.click(screen.getByRole("option", { name: "customer_id" }));

    await waitFor(() => {
      expect(screen.getByDisplayValue("custom_time_name")).toBeInTheDocument();
    });
  });

  it("step に 0 を入力して blur すると AddPanelTimeColumnForm.StepError が表示される", async () => {
    const user = userEvent.setup();
    render(<AddPanelTimeColumnForm {...defaultProps} />);

    const stepInput = screen.getByRole("spinbutton", {
      name: /AddPanelTimeColumnForm.Step/i,
    });
    await user.clear(stepInput);
    await user.type(stepInput, "0");
    await user.tab();

    await waitFor(() => {
      expect(
        screen.getByText("AddPanelTimeColumnForm.StepError"),
      ).toBeInTheDocument();
    });
  });

  it("API成功時に addPanelTimeColumn へ期待した payload を渡し、onSuccess を呼ぶ", async () => {
    mockApi.addPanelTimeColumn.mockResolvedValue({ code: "OK", result: {} });

    render(<AddPanelTimeColumnForm {...defaultProps} />);

    const form = document.getElementById("add-panel-time-form");
    form?.dispatchEvent(new Event("submit", { bubbles: true }));

    await waitFor(() => {
      expect(mockApi.addPanelTimeColumn).toHaveBeenCalledWith({
        tableName: "sales",
        idColumn: "firm_id",
        newColumnName: "time_firm_id",
        addPositionColumn: "firm_id",
        startValue: 1,
        step: 1,
      });
      expect(defaultProps.onSuccess).toHaveBeenCalledWith([
        { name: "time_customer_id", type: "Int64" },
      ]);
    });
  });

  it("APIが失敗レスポンスを返した場合は ErrorAlert に message を表示する", async () => {
    mockApi.addPanelTimeColumn.mockResolvedValue({
      code: "COLUMN_NAME_CONFLICT",
      message: "その列名はすでに存在します",
    });

    render(<AddPanelTimeColumnForm {...defaultProps} />);

    const form = document.getElementById("add-panel-time-form");
    form?.dispatchEvent(new Event("submit", { bubbles: true }));

    await waitFor(() => {
      expect(
        screen.getByText("その列名はすでに存在します"),
      ).toBeInTheDocument();
    });
  });

  it("APIが throw した場合は ErrorAlert に message を表示する", async () => {
    mockApi.addPanelTimeColumn.mockRejectedValue(new Error("接続タイムアウト"));

    render(<AddPanelTimeColumnForm {...defaultProps} />);

    const form = document.getElementById("add-panel-time-form");
    fireEvent.submit(form!);

    await waitFor(() => {
      expect(screen.getByText("接続タイムアウト")).toBeInTheDocument();
    });
  });
});
