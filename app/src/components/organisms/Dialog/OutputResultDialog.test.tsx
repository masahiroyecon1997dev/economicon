import { OutputResultFormat } from "@/api/model/outputResultFormat";
import { OutputResultDialog } from "@/components/organisms/Dialog/OutputResultDialog";
import { render, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const mockFetchOutput = vi.fn();

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}));

vi.mock("@/hooks/useOutputResult", () => ({
  useOutputResult: () => ({
    content: null,
    isLoading: false,
    error: null,
    fetchOutput: mockFetchOutput,
  }),
}));

vi.mock("@/components/molecules/Dialog/BaseDialog", () => ({
  BaseDialog: ({
    open,
    children,
  }: {
    open: boolean;
    children: React.ReactNode;
  }) => (open ? <div>{children}</div> : null),
}));

vi.mock("@/components/atoms/Input/Select", () => ({
  Select: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  SelectItem: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock("@radix-ui/react-dialog", () => ({
  Close: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

const REGRESSION_RESULT = {
  resultId: "reg-1",
  tableName: "sales",
  dependentVariable: "price",
  explanatoryVariables: ["quantity"],
  regressionResult: "OLS",
  parameters: [
    {
      variable: "quantity",
      coefficient: 1.5,
      standardError: 0.1,
      tValue: 15,
      pValue: 0.001,
      confidenceIntervalLower: 1.3,
      confidenceIntervalUpper: 1.7,
    },
  ],
  modelStatistics: {
    nObservations: 10,
    R2: 0.8,
    adjustedR2: 0.75,
    fValue: 12,
    fProbability: 0.01,
  },
};

beforeEach(() => {
  vi.clearAllMocks();
});

describe("OutputResultDialog", () => {
  it("regression は回帰用 payload を fetch する", async () => {
    render(
      <OutputResultDialog
        open
        onOpenChange={vi.fn()}
        resultKind="regression"
        result={REGRESSION_RESULT}
      />,
    );

    await waitFor(() => {
      expect(mockFetchOutput).toHaveBeenCalledWith({
        resultType: "regression",
        resultIds: ["reg-1"],
        format: OutputResultFormat.markdown,
        options: {
          statInParentheses: "se",
          constAtBottom: false,
          variableLabels: undefined,
          variableOrder: ["quantity"],
        },
      });
    });
  });

  it("descriptive_statistics は共通非回帰 payload を fetch する", async () => {
    render(
      <OutputResultDialog
        open
        onOpenChange={vi.fn()}
        resultKind="descriptive_statistics"
        resultId="desc-1"
        title="sales / desc"
      />,
    );

    await waitFor(() => {
      expect(mockFetchOutput).toHaveBeenCalledWith({
        resultType: "descriptive_statistics",
        resultIds: ["desc-1"],
        format: OutputResultFormat.markdown,
        options: {
          includeResultName: false,
          includeTableName: false,
        },
      });
    });
  });

  it("confidence_interval は confidence level を含む payload を fetch する", async () => {
    render(
      <OutputResultDialog
        open
        onOpenChange={vi.fn()}
        resultKind="confidence_interval"
        resultId="ci-1"
        title="sales / ci"
      />,
    );

    await waitFor(() => {
      expect(mockFetchOutput).toHaveBeenCalledWith({
        resultType: "confidence_interval",
        resultIds: ["ci-1"],
        format: OutputResultFormat.markdown,
        options: {
          includeResultName: false,
          includeTableName: false,
          includeConfidenceLevel: true,
        },
      });
    });
  });

  it("statistical_test は追加 option なしで fetch する", async () => {
    render(
      <OutputResultDialog
        open
        onOpenChange={vi.fn()}
        resultKind="statistical_test"
        resultId="test-1"
        title="sales / test"
      />,
    );

    await waitFor(() => {
      expect(mockFetchOutput).toHaveBeenCalledWith({
        resultType: "statistical_test",
        resultIds: ["test-1"],
        format: OutputResultFormat.markdown,
      });
    });
  });
});