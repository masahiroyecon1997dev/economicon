/**
 * AsymptoticNormality コンポーネントのテスト
 *
 * - n ボタン切り替えで選択値が変わること
 * - コーシー誤差選択時に cauchy-notice が表示されること
 * - 内生性あり選択時に endogenous-notice と γ スライダーが表示されること
 * - 正規誤差時は notice が表示されないこと
 */
import type { AsymptoticNormalityRequestBody } from "@/api/model";
import { AsymptoticNormality } from "@/components/pages/AsymptoticNormality";
import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (key: string) => key }),
}));

const { mockUseAsymptoticNormality } = vi.hoisted(() => ({
  mockUseAsymptoticNormality: vi.fn(
    (_params: AsymptoticNormalityRequestBody) => ({
      loading: false,
      error: null as string | null,
      result: null,
    }),
  ),
}));

vi.mock("@/hooks/useAsymptoticNormality", () => ({
  useAsymptoticNormality: mockUseAsymptoticNormality,
}));

vi.mock("plotly.js-dist-min", () => ({
  react: vi.fn().mockResolvedValue(undefined),
  purge: vi.fn(),
}));

beforeEach(() => {
  mockUseAsymptoticNormality.mockClear();
  mockUseAsymptoticNormality.mockImplementation(
    (_params: AsymptoticNormalityRequestBody) => ({
      loading: false,
      error: null as string | null,
      result: null,
    }),
  );
});

describe("AsymptoticNormality", () => {
  describe("サンプルサイズ選択", () => {
    it("test_sampleSize_initialValue_100: 初期値 n=100 が選択されている", () => {
      render(<AsymptoticNormality />);
      const radio = screen.getByDisplayValue("100");
      expect(radio).toBeChecked();
    });

    it("test_sampleSize_changeToN1000: n=1000 を選択すると 1000 が checked になる", async () => {
      render(<AsymptoticNormality />);

      const radio1000 = screen.getByDisplayValue("1000");
      fireEvent.click(radio1000);

      expect(radio1000).toBeChecked();
      expect(screen.getByDisplayValue("100")).not.toBeChecked();
    });

    it("test_sampleSize_changeToN10: n=10 を選択できる", async () => {
      render(<AsymptoticNormality />);

      const radio10 = screen.getByDisplayValue("10");
      fireEvent.click(radio10);

      expect(radio10).toBeChecked();
    });

    it("test_sampleSize_hookCalledWithNewSampleSize: n=1000 選択後 hook が sampleSize=1000 で呼ばれる", () => {
      render(<AsymptoticNormality />);
      mockUseAsymptoticNormality.mockClear();

      fireEvent.click(screen.getByDisplayValue("1000"));

      expect(mockUseAsymptoticNormality).toHaveBeenCalledWith(
        expect.objectContaining({ sampleSize: 1000 }),
      );
    });
  });

  describe("誤差タイプと通知テキスト", () => {
    it("test_errorType_normal_noNotice: 正規誤差時は notice が表示されない", () => {
      render(<AsymptoticNormality />);
      expect(screen.queryByTestId("cauchy-notice")).not.toBeInTheDocument();
      expect(screen.queryByTestId("endogenous-notice")).not.toBeInTheDocument();
    });

    it("test_errorType_cauchy_showsCauchyNotice: コーシー選択時に cauchy-notice が表示される", async () => {
      render(<AsymptoticNormality />);

      fireEvent.click(screen.getByDisplayValue("cauchy"));

      expect(screen.getByTestId("cauchy-notice")).toBeInTheDocument();
      expect(screen.queryByTestId("endogenous-notice")).not.toBeInTheDocument();
    });

    it("test_errorType_endogenous_showsEndogeneousNotice: 内生性あり選択時に endogenous-notice が表示される", async () => {
      render(<AsymptoticNormality />);

      fireEvent.click(screen.getByDisplayValue("endogenous"));

      expect(screen.getByTestId("endogenous-notice")).toBeInTheDocument();
      expect(screen.queryByTestId("cauchy-notice")).not.toBeInTheDocument();
    });

    it("test_errorType_endogenous_showsGammaSlider: 内生性あり時に γ スライダーが表示される", async () => {
      render(<AsymptoticNormality />);

      expect(
        screen.queryByTestId("endogeneity-strength-slider"),
      ).not.toBeInTheDocument();

      fireEvent.click(screen.getByDisplayValue("endogenous"));

      expect(
        screen.getByTestId("endogeneity-strength-slider"),
      ).toBeInTheDocument();
    });

    it("test_errorType_cauchy_noGammaSlider: コーシー時に γ スライダーが表示されない", async () => {
      render(<AsymptoticNormality />);

      fireEvent.click(screen.getByDisplayValue("cauchy"));

      expect(
        screen.queryByTestId("endogeneity-strength-slider"),
      ).not.toBeInTheDocument();
    });
  });

  describe("hook 呼び出し", () => {
    it("test_hook_calledWithDefaultParams: 初期 params で hook が呼ばれる", () => {
      render(<AsymptoticNormality />);

      expect(mockUseAsymptoticNormality).toHaveBeenCalledWith(
        expect.objectContaining({
          sampleSize: 100,
          trueBeta: 1.0,
          errorVariance: 1.0,
          errorType: "normal",
        }),
      );
    });

    it("test_hook_loadingState_showsPlotPanel: loading=true 時も PlotPanel がレンダリングされる", () => {
      mockUseAsymptoticNormality.mockReturnValue({
        loading: true,
        error: null,
        result: null,
      });

      render(<AsymptoticNormality />);

      expect(
        screen.getByTestId("asymptotic-normality-plot-area"),
      ).toBeInTheDocument();
    });
  });
});
