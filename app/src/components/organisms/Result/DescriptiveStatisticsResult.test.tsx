import { DescriptiveStatisticsResult } from "@/components/organisms/Result/DescriptiveStatisticsResult";
import { render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}));

vi.mock("@/components/organisms/Dialog/OutputResultDialog", () => ({
  OutputResultDialog: ({ open }: { open: boolean }) =>
    open ? <div data-testid="descriptive-statistics-output-dialog" /> : null,
}));

describe("DescriptiveStatisticsResult", () => {
  it("statisticOrder と columnNameList を優先して表示順を決める", () => {
    const { container } = render(
      <DescriptiveStatisticsResult
        resultId="result-1"
        tableName="sales"
        columnNameList={["B", "A"]}
        statisticOrder={["max", "mean"]}
        statistics={{
          A: { mean: 10, max: 15 },
          B: { mean: 20, max: 25 },
        }}
      />,
    );

    const headerCells = within(container.querySelector("thead")!).getAllByRole(
      "columnheader",
    );
    expect(headerCells.map((cell) => cell.textContent)).toEqual([
      "DescriptiveStatistics.Column",
      "max",
      "mean",
    ]);

    const rowHeaders = Array.from(
      container.querySelectorAll("tbody tr td:first-child"),
    ).map((cell) => cell.textContent);
    expect(rowHeaders).toEqual(["B", "A"]);
  });

  it("旧 resultData では canonical order で既知の統計量を並べる", () => {
    const { container } = render(
      <DescriptiveStatisticsResult
        resultId="result-2"
        tableName="sales"
        statistics={{
          A: { skewness: 0.1, mean: 10, count: 3, max: 15 },
        }}
      />,
    );

    const headerCells = within(container.querySelector("thead")!).getAllByRole(
      "columnheader",
    );
    expect(headerCells.map((cell) => cell.textContent)).toEqual([
      "DescriptiveStatistics.Column",
      "count",
      "mean",
      "max",
      "skewness",
    ]);
  });

  it("未知の統計量キーは raw key をそのまま表示し、末尾に残す", () => {
    render(
      <DescriptiveStatisticsResult
        resultId="result-3"
        tableName="sales"
        statistics={{
          A: { mean: 10, custom_stat: 99 },
        }}
      />,
    );

    expect(
      screen.getByRole("columnheader", { name: "custom_stat" }),
    ).toBeInTheDocument();
  });
});
