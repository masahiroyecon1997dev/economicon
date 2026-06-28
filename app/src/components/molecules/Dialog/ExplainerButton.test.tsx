import { ExplainerButton } from "@/components/molecules/Dialog/ExplainerButton";
import { openExplainerDialog } from "@/stores/explainerDialog";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

vi.mock("@/stores/explainerDialog", () => ({
  openExplainerDialog: vi.fn(),
}));

describe("ExplainerButton", () => {
  it("test_click_opensExplainerDialogWithTriggerRect", async () => {
    const user = userEvent.setup();
    const rect = {
      x: 12,
      y: 16,
      width: 24,
      height: 24,
      top: 16,
      right: 36,
      bottom: 40,
      left: 12,
      toJSON: () => "",
    } as DOMRect;

    render(
      <ExplainerButton explainerKey="mean" aria-label="explainer">
        <span>i</span>
      </ExplainerButton>,
    );

    vi.spyOn(
      screen.getByRole("button", { name: "explainer" }),
      "getBoundingClientRect",
    ).mockReturnValue(rect);

    await user.click(screen.getByRole("button", { name: "explainer" }));

    expect(openExplainerDialog).toHaveBeenCalledWith("mean", rect);
  });
});
