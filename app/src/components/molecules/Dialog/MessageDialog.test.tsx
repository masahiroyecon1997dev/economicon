import { MessageDialog } from "@/components/molecules/Dialog/MessageDialog";
import { useMessageDialogStore } from "@/stores/messageDialog";
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}));

describe("MessageDialog", () => {
  beforeEach(() => {
    useMessageDialogStore.setState({
      isOpen: false,
      title: "",
      message: "",
      resolver: null,
    });
  });

  it("長いパスでも折り返し用クラスを付けて表示する", () => {
    const longPath =
      "C:/very/long/path/that/does/not/include/spaces/and/should/wrap/in/the/dialog/output/result/export/file-name.csv";
    useMessageDialogStore.setState({
      isOpen: true,
      title: "Common.OK",
      message: longPath,
    });

    render(<MessageDialog />);

    const message = screen.getByText(longPath);
    expect(message).toHaveClass("whitespace-pre-wrap");
    expect(message).toHaveClass("break-all");
  });
});