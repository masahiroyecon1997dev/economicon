import { getEconomiconAppAPI } from "@/api/endpoints";
import { SettingsDialog } from "@/components/organisms/Dialog/SettingsDialog";
import { showMessageDialog } from "@/lib/dialog/message";
import { useSettingsStore } from "@/stores/settings";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

const { mockChangeLanguage } = vi.hoisted(() => ({
  mockChangeLanguage: vi.fn().mockResolvedValue(undefined),
}));

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    i18n: {
      changeLanguage: mockChangeLanguage,
    },
  }),
}));

vi.mock("@/api/endpoints", () => ({
  getEconomiconAppAPI: vi.fn(),
}));

vi.mock("@/lib/dialog/message", () => ({
  showMessageDialog: vi.fn().mockResolvedValue(undefined),
}));

const mockUpdateSettings = vi.fn();

describe("SettingsDialog", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(getEconomiconAppAPI).mockReturnValue({
      updateSettings: mockUpdateSettings,
    } as never);
    useSettingsStore.setState({
      theme: "light",
      language: "ja",
      encoding: "utf-8",
      logPath: "C:/logs/economicon.log",
    });
    document.documentElement.classList.remove("dark");
  });

  it("初期表示では保存ボタンが無効で、ログタブも表示できる", async () => {
    const user = userEvent.setup();

    render(<SettingsDialog open={true} onOpenChange={vi.fn()} />);

    expect(screen.getByText("SettingsDialog.Title")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "SettingsDialog.Save" }),
    ).toBeDisabled();

    await user.click(
      screen.getByRole("tab", { name: "SettingsDialog.Tabs.Log" }),
    );

    expect(
      screen.getByText("SettingsDialog.LogPath.Label"),
    ).toBeInTheDocument();
    expect(screen.getByText("C:/logs/economicon.log")).toBeInTheDocument();
  });

  it("未保存プレビューをキャンセルするとテーマと言語が元に戻る", async () => {
    const user = userEvent.setup();
    const handleOpenChange = vi.fn();

    render(<SettingsDialog open={true} onOpenChange={handleOpenChange} />);

    await user.click(
      screen.getByRole("button", { name: "SettingsDialog.Theme.Dark" }),
    );
    expect(document.documentElement.classList.contains("dark")).toBe(true);

    await user.click(
      screen.getByRole("tab", { name: "SettingsDialog.Tabs.General" }),
    );
    await user.click(
      screen.getByRole("button", { name: "SettingsDialog.Language.En" }),
    );

    await waitFor(() => {
      expect(mockChangeLanguage).toHaveBeenCalledWith("en");
    });

    await user.click(screen.getByRole("button", { name: "Common.Cancel" }));

    await waitFor(() => {
      expect(handleOpenChange).toHaveBeenCalledWith(false);
      expect(mockChangeLanguage).toHaveBeenLastCalledWith("ja");
    });
    expect(document.documentElement.classList.contains("dark")).toBe(false);
  });

  it("変更を保存すると API 呼び出し後に store を更新して閉じる", async () => {
    const user = userEvent.setup();
    const handleOpenChange = vi.fn();
    mockUpdateSettings.mockResolvedValue({
      code: "OK",
      result: {
        theme: "dark",
        language: "ja",
        encoding: "utf-8",
        logPath: "C:/logs/economicon.log",
        lastOpenedPath: "C:/data",
      },
    });

    render(<SettingsDialog open={true} onOpenChange={handleOpenChange} />);

    await user.click(
      screen.getByRole("button", { name: "SettingsDialog.Theme.Dark" }),
    );
    await user.click(
      screen.getByRole("button", { name: "SettingsDialog.Save" }),
    );

    await waitFor(() => {
      expect(mockUpdateSettings).toHaveBeenCalledWith({
        theme: "dark",
        language: "ja",
        encoding: "utf-8",
      });
      expect(handleOpenChange).toHaveBeenCalledWith(false);
    });

    expect(useSettingsStore.getState().theme).toBe("dark");
    expect(vi.mocked(showMessageDialog)).not.toHaveBeenCalled();
  });
});
