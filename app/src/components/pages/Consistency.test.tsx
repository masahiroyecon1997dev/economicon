/**
 * Consistency コンポーネントのテスト
 *
 * - 外生性成立 / 内生性あり切り替えで γ スライダーの表示が変わること
 * - 初期値（外生性成立）が選択されていること
 * - hook の初期 params が正しいこと
 * - loading 時も PlotPanel がレンダリングされること
 */
import type { ConsistencyRequestBody } from "@/api/model";
import { Consistency } from "@/components/pages/Consistency";
import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (key: string) => key }),
}));

const { mockUseConsistency } = vi.hoisted(() => ({
  mockUseConsistency: vi.fn((_params: ConsistencyRequestBody) => ({
    loading: false,
    error: null as string | null,
    result: null,
  })),
}));

vi.mock("@/hooks/useConsistency", () => ({
  useConsistency: mockUseConsistency,
}));

vi.mock("plotly.js-dist-min", () => ({
  react: vi.fn().mockResolvedValue(undefined),
  purge: vi.fn(),
}));

beforeEach(() => {
  mockUseConsistency.mockClear();
  mockUseConsistency.mockImplementation((_params: ConsistencyRequestBody) => ({
    loading: false,
    error: null as string | null,
    result: null,
  }));
});

describe("Consistency", () => {
  describe("初期レンダリング", () => {
    it("test_render_showsContainer: consistency コンテナが表示される", () => {
      render(<Consistency />);
      expect(screen.getByTestId("consistency")).toBeInTheDocument();
    });

    it("test_render_exogenousSelected: 初期値は外生性成立が選択されている", () => {
      render(<Consistency />);
      expect(screen.getByDisplayValue("false")).toBeChecked();
    });

    it("test_render_gammaSliderHidden: 外生性成立時は γ スライダーが表示されない", () => {
      render(<Consistency />);
      expect(
        screen.queryByTestId("endogeneity-strength-slider"),
      ).not.toBeInTheDocument();
    });
  });

  describe("内生性切り替え", () => {
    it("test_endogenous_on_showsGammaSlider: 内生性あり選択時に γ スライダーが表示される", () => {
      render(<Consistency />);

      fireEvent.click(screen.getByDisplayValue("true"));

      expect(
        screen.getByTestId("endogeneity-strength-slider"),
      ).toBeInTheDocument();
    });

    it("test_endogenous_off_hidesGammaSlider: 外生性に戻すと γ スライダーが消える", () => {
      render(<Consistency />);

      fireEvent.click(screen.getByDisplayValue("true"));
      expect(
        screen.getByTestId("endogeneity-strength-slider"),
      ).toBeInTheDocument();

      fireEvent.click(screen.getByDisplayValue("false"));
      expect(
        screen.queryByTestId("endogeneity-strength-slider"),
      ).not.toBeInTheDocument();
    });
  });

  describe("hook 呼び出し", () => {
    it("test_hook_calledWithDefaultParams: 初期 params で hook が呼ばれる", () => {
      render(<Consistency />);

      expect(mockUseConsistency).toHaveBeenCalledWith(
        expect.objectContaining({
          nMax: 500,
          trueBeta: 1.0,
          errorVariance: 1.0,
          endogenous: false,
        }),
      );
    });

    it("test_hook_loading_showsPlotPanel: loading=true 時も PlotPanel がレンダリングされる", () => {
      mockUseConsistency.mockReturnValue({
        loading: true,
        error: null,
        result: null,
      });

      render(<Consistency />);

      expect(screen.getByTestId("consistency-plot-area")).toBeInTheDocument();
    });
  });
});
