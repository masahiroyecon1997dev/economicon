import { SimParamSlider } from "@/components/molecules/Field/SimParamSlider";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

describe("SimParamSlider", () => {
  describe("レンダリング", () => {
    it("test_render_showsLabelAndValue", () => {
      render(
        <SimParamSlider
          label="平均 μ"
          min={-3}
          max={3}
          step={0.1}
          value={1.5}
          onChange={vi.fn()}
          valueTestId="test-value"
        />,
      );
      expect(screen.getByText("平均 μ")).toBeInTheDocument();
      expect(screen.getByTestId("test-value")).toHaveTextContent("1.5");
    });

    it("test_render_showsMinAndMax", () => {
      render(
        <SimParamSlider
          label="σ²"
          min={0.1}
          max={10}
          step={0.1}
          value={1}
          onChange={vi.fn()}
        />,
      );
      expect(screen.getByText("0.1")).toBeInTheDocument();
      expect(screen.getByText("10")).toBeInTheDocument();
    });

    it("test_render_sliderHasCorrectAttributes", () => {
      render(
        <SimParamSlider
          label="テスト"
          min={0}
          max={100}
          step={1}
          value={50}
          onChange={vi.fn()}
          sliderTestId="test-slider"
        />,
      );
      const slider = screen.getByTestId("test-slider");
      expect(slider).toHaveAttribute("type", "range");
      expect(slider).toHaveAttribute("min", "0");
      expect(slider).toHaveAttribute("max", "100");
      expect(slider).toHaveAttribute("step", "1");
      expect(slider).toHaveAttribute("value", "50");
    });
  });

  describe("インタラクション", () => {
    it("test_onChange_calledWithParsedFloat", () => {
      const onChange = vi.fn();
      render(
        <SimParamSlider
          label="β"
          min={-3}
          max={3}
          step={0.1}
          value={0}
          onChange={onChange}
          sliderTestId="beta-slider"
        />,
      );
      fireEvent.change(screen.getByTestId("beta-slider"), {
        target: { value: "2.5" },
      });
      expect(onChange).toHaveBeenCalledWith(2.5);
    });

    it("test_onChange_calledOnce", () => {
      const onChange = vi.fn();
      render(
        <SimParamSlider
          label="β"
          min={0}
          max={10}
          step={1}
          value={0}
          onChange={onChange}
          sliderTestId="slider"
        />,
      );
      fireEvent.change(screen.getByTestId("slider"), {
        target: { value: "7" },
      });
      expect(onChange).toHaveBeenCalledTimes(1);
    });
  });
});
