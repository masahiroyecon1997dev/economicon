import { SimulationColumnConfig } from "@/components/organisms/Form/SimulationColumnConfig";
import type { SimulationColumnSetting } from "@/types/commonTypes";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (key: string) => key }),
}));

const submitForm = () => {
  const form = document.getElementById("sim-config-form");
  expect(form).toBeInstanceOf(HTMLFormElement);
  fireEvent.submit(form as HTMLFormElement);
};

const defaultColumn: SimulationColumnSetting = {
  id: "column-1",
  columnName: "sales",
  dataType: "distribution",
  distributionType: "normal",
  distributionParams: {
    mean: 0,
    standardDeviation: 1,
  },
  fixedValue: "",
  errorMessage: {
    columnName: undefined,
    distributionParams: undefined,
    fixedValue: undefined,
  },
};

describe("SimulationColumnConfig", () => {
  const onSaved = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("normal の新命名パラメータを表示する", () => {
    render(
      <SimulationColumnConfig
        formId="sim-config-form"
        column={defaultColumn}
        onSaved={onSaved}
      />,
    );

    expect(screen.getByDisplayValue("sales")).toBeInTheDocument();
    expect(
      screen.getByText("AddSimulationColumnForm.Mean"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("AddSimulationColumnForm.StandardDeviation"),
    ).toBeInTheDocument();
  });

  it("normal を保存すると新命名キーで onSaved を呼ぶ", async () => {
    render(
      <SimulationColumnConfig
        formId="sim-config-form"
        column={defaultColumn}
        onSaved={onSaved}
      />,
    );

    submitForm();

    await waitFor(() => {
      expect(onSaved).toHaveBeenCalledWith({
        columnName: "sales",
        dataType: "distribution",
        distributionType: "normal",
        distributionParams: {
          mean: 0,
          standardDeviation: 1,
        },
        fixedValue: "",
      });
    });
  });

  it("negative_binomial を保存すると targetSuccessCount と successProbability を使う", async () => {
    const user = userEvent.setup();

    render(
      <SimulationColumnConfig
        formId="sim-config-form"
        column={defaultColumn}
        onSaved={onSaved}
      />,
    );

    await user.click(
      screen.getByRole("tab", {
        name: /AddSimulationColumnForm\.TabDiscrete/i,
      }),
    );
    const negativeBinomialRadio = screen.getByRole("radio", {
      name: /AddSimulationColumnForm\.negative_binomial/i,
    });
    fireEvent.click(negativeBinomialRadio);

    await waitFor(() => {
      expect(negativeBinomialRadio).toBeChecked();
    });

    const targetSuccessCountInput = await screen.findByRole("spinbutton", {
      name: /AddSimulationColumnForm\.TargetSuccessCount/i,
    });
    const successProbabilityInput = await screen.findByRole("spinbutton", {
      name: /AddSimulationColumnForm\.SuccessProbability/i,
    });

    await user.clear(targetSuccessCountInput);
    await user.type(targetSuccessCountInput, "7");
    await user.clear(successProbabilityInput);
    await user.type(successProbabilityInput, "0.25");

    submitForm();

    await waitFor(() => {
      expect(onSaved).toHaveBeenCalledWith({
        columnName: "sales",
        dataType: "distribution",
        distributionType: "negative_binomial",
        distributionParams: {
          targetSuccessCount: 7,
          successProbability: 0.25,
        },
        fixedValue: "",
      });
    });
  });

  it("fixed に切り替えて保存すると fixedValue を数値で返す", async () => {
    const user = userEvent.setup();

    render(
      <SimulationColumnConfig
        formId="sim-config-form"
        column={defaultColumn}
        onSaved={onSaved}
      />,
    );

    await user.click(
      screen.getByRole("tab", {
        name: /AddSimulationColumnForm\.TabDeterministic/i,
      }),
    );
    const fixedRadio = screen.getByRole("radio", {
      name: /AddSimulationColumnForm\.fixed/i,
    });
    fireEvent.click(fixedRadio);

    await waitFor(() => {
      expect(fixedRadio).toBeChecked();
    });

    const fixedValueInput = await screen.findByRole("spinbutton", {
      name: /CreateSimulationDataTableView\.FixedValue/i,
    });

    await user.clear(fixedValueInput);
    await user.type(fixedValueInput, "42");

    submitForm();

    await waitFor(() => {
      expect(onSaved).toHaveBeenCalledWith({
        columnName: "sales",
        dataType: "fixed",
        distributionType: undefined,
        distributionParams: undefined,
        fixedValue: 42,
      });
    });
  });

  it("標準偏差が不正なら保存せずエラーを表示する", async () => {
    const user = userEvent.setup();

    render(
      <SimulationColumnConfig
        formId="sim-config-form"
        column={defaultColumn}
        onSaved={onSaved}
      />,
    );

    const standardDeviationInput = document.getElementById(
      "sim-config-form-param-standardDeviation",
    );
    expect(standardDeviationInput).toBeInstanceOf(HTMLInputElement);

    await user.clear(standardDeviationInput as HTMLInputElement);
    await user.type(standardDeviationInput as HTMLInputElement, "0");

    submitForm();

    await waitFor(() => {
      expect(
        screen.getByText("0 より大きい数値を入力してください。"),
      ).toBeInTheDocument();
    });
    expect(onSaved).not.toHaveBeenCalled();
  });
});
