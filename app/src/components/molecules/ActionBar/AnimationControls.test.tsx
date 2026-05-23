import { AnimationControls } from "@/components/molecules/ActionBar/AnimationControls";
import type { AnimationSpeed } from "@/hooks/useSimulationAnimation";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}));

const defaultProps = {
  playing: false,
  canPlay: true,
  frame: 0,
  total: 10,
  speed: "normal" as AnimationSpeed,
  onPlay: vi.fn(),
  onPause: vi.fn(),
  onReset: vi.fn(),
  onSpeedChange: vi.fn(),
};

describe("AnimationControls", () => {
  describe("再生 / 一時停止", () => {
    it("test_notPlaying_showsPlayButton", () => {
      render(<AnimationControls {...defaultProps} playing={false} />);
      expect(screen.getByTestId("animation-play-btn")).toBeInTheDocument();
      expect(
        screen.queryByTestId("animation-pause-btn"),
      ).not.toBeInTheDocument();
    });

    it("test_playing_showsPauseButton", () => {
      render(<AnimationControls {...defaultProps} playing={true} />);
      expect(screen.getByTestId("animation-pause-btn")).toBeInTheDocument();
      expect(
        screen.queryByTestId("animation-play-btn"),
      ).not.toBeInTheDocument();
    });

    it("test_playButton_callsOnPlay", async () => {
      const onPlay = vi.fn();
      render(
        <AnimationControls {...defaultProps} playing={false} onPlay={onPlay} />,
      );
      await userEvent.click(screen.getByTestId("animation-play-btn"));
      expect(onPlay).toHaveBeenCalledOnce();
    });

    it("test_pauseButton_callsOnPause", async () => {
      const onPause = vi.fn();
      render(
        <AnimationControls
          {...defaultProps}
          playing={true}
          onPause={onPause}
        />,
      );
      await userEvent.click(screen.getByTestId("animation-pause-btn"));
      expect(onPause).toHaveBeenCalledOnce();
    });

    it("test_playButton_disabled_whenCanPlayFalse", () => {
      render(
        <AnimationControls {...defaultProps} playing={false} canPlay={false} />,
      );
      expect(screen.getByTestId("animation-play-btn")).toBeDisabled();
    });

    it("test_playButton_enabled_whenCanPlayTrue", () => {
      render(
        <AnimationControls {...defaultProps} playing={false} canPlay={true} />,
      );
      expect(screen.getByTestId("animation-play-btn")).toBeEnabled();
    });
  });

  describe("リセット", () => {
    it("test_resetButton_callsOnReset", async () => {
      const onReset = vi.fn();
      render(<AnimationControls {...defaultProps} onReset={onReset} />);
      await userEvent.click(screen.getByTestId("animation-reset-btn"));
      expect(onReset).toHaveBeenCalledOnce();
    });
  });

  describe("速度セレクター", () => {
    it("test_speedButtons_allPresent", () => {
      render(<AnimationControls {...defaultProps} />);
      expect(screen.getByTestId("animation-speed-slow")).toBeInTheDocument();
      expect(screen.getByTestId("animation-speed-normal")).toBeInTheDocument();
      expect(screen.getByTestId("animation-speed-fast")).toBeInTheDocument();
    });

    it("test_speedButton_callsOnSpeedChange", async () => {
      const onSpeedChange = vi.fn();
      render(
        <AnimationControls {...defaultProps} onSpeedChange={onSpeedChange} />,
      );
      await userEvent.click(screen.getByTestId("animation-speed-fast"));
      expect(onSpeedChange).toHaveBeenCalledWith("fast");
    });

    it("test_speedButton_slow_callsOnSpeedChange", async () => {
      const onSpeedChange = vi.fn();
      render(
        <AnimationControls
          {...defaultProps}
          speed="normal"
          onSpeedChange={onSpeedChange}
        />,
      );
      await userEvent.click(screen.getByTestId("animation-speed-slow"));
      expect(onSpeedChange).toHaveBeenCalledWith("slow");
    });
  });

  describe("フレームカウンター", () => {
    it("test_counter_showsFrameAndTotal", () => {
      render(<AnimationControls {...defaultProps} frame={5} total={10} />);
      expect(screen.getByTestId("animation-counter")).toHaveTextContent(
        "5 / 10",
      );
    });

    it("test_counter_showsCustomLabel", () => {
      render(
        <AnimationControls
          {...defaultProps}
          frame={5}
          total={10}
          counterLabel="5 / 10（50.0%）"
        />,
      );
      expect(screen.getByTestId("animation-counter")).toHaveTextContent(
        "5 / 10（50.0%）",
      );
    });

    it("test_counter_customLabel_overridesDefault", () => {
      render(
        <AnimationControls
          {...defaultProps}
          frame={3}
          total={10}
          counterLabel="カスタム表示"
        />,
      );
      const counter = screen.getByTestId("animation-counter");
      expect(counter).toHaveTextContent("カスタム表示");
      expect(counter).not.toHaveTextContent("3 / 10");
    });
  });
});
