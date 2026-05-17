import { CollapsibleSection } from "@/components/molecules/Layout/CollapsibleSection";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

describe("CollapsibleSection", () => {
  describe("初期状態", () => {
    it("test_render_defaultCollapsed_hidesContent", () => {
      render(
        <CollapsibleSection title="詳細設定">
          <div data-testid="inner">コンテンツ</div>
        </CollapsibleSection>,
      );
      expect(
        screen.queryByTestId("collapsible-content"),
      ).not.toBeInTheDocument();
    });

    it("test_render_defaultOpen_showsContent", () => {
      render(
        <CollapsibleSection title="詳細設定" defaultOpen>
          <div>コンテンツ</div>
        </CollapsibleSection>,
      );
      expect(screen.getByTestId("collapsible-content")).toBeInTheDocument();
    });

    it("test_render_showsTitle", () => {
      render(
        <CollapsibleSection title="高度な設定">
          <span />
        </CollapsibleSection>,
      );
      expect(screen.getByText("高度な設定")).toBeInTheDocument();
    });
  });

  describe("インタラクション", () => {
    it("test_click_expandsContent", async () => {
      render(
        <CollapsibleSection title="詳細設定">
          <div>コンテンツ</div>
        </CollapsibleSection>,
      );
      expect(
        screen.queryByTestId("collapsible-content"),
      ).not.toBeInTheDocument();
      await userEvent.click(screen.getByTestId("collapsible-trigger"));
      expect(screen.getByTestId("collapsible-content")).toBeInTheDocument();
    });

    it("test_click_collapses_whenOpen", async () => {
      render(
        <CollapsibleSection title="詳細設定" defaultOpen>
          <div>コンテンツ</div>
        </CollapsibleSection>,
      );
      expect(screen.getByTestId("collapsible-content")).toBeInTheDocument();
      await userEvent.click(screen.getByTestId("collapsible-trigger"));
      expect(
        screen.queryByTestId("collapsible-content"),
      ).not.toBeInTheDocument();
    });

    it("test_click_togglesTwice", async () => {
      render(
        <CollapsibleSection title="詳細設定">
          <div>コンテンツ</div>
        </CollapsibleSection>,
      );
      await userEvent.click(screen.getByTestId("collapsible-trigger"));
      expect(screen.getByTestId("collapsible-content")).toBeInTheDocument();
      await userEvent.click(screen.getByTestId("collapsible-trigger"));
      expect(
        screen.queryByTestId("collapsible-content"),
      ).not.toBeInTheDocument();
    });

    it("test_render_showsChildrenWhenOpen", async () => {
      render(
        <CollapsibleSection title="詳細設定">
          <span data-testid="child-content">子要素</span>
        </CollapsibleSection>,
      );
      await userEvent.click(screen.getByTestId("collapsible-trigger"));
      expect(screen.getByTestId("child-content")).toBeInTheDocument();
    });
  });
});
