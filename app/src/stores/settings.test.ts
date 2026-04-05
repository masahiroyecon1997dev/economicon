import type { GetSettingsResult } from "@/api/model";
import { beforeEach, describe, expect, it } from "vitest";
import type { OsInfo } from "./settings";
import { useSettingsStore } from "./settings";

const DEFAULT_SETTINGS: GetSettingsResult = {
  language: "",
  lastOpenedPath: "",
  theme: "",
  encoding: "",
  logPath: "",
};

const SAMPLE_SETTINGS: GetSettingsResult = {
  language: "ja",
  lastOpenedPath: "/home/user/data",
  theme: "dark",
  encoding: "utf-8",
  logPath: "/home/user/logs",
};

const SAMPLE_OS_INFO: OsInfo = {
  osName: "Windows",
  pathSeparator: "\\",
};

beforeEach(() => {
  useSettingsStore.setState({
    ...DEFAULT_SETTINGS,
    osName: "",
    pathSeparator: "/",
  });
});

describe("useSettingsStore", () => {
  describe("initial state", () => {
    it("test_initialState_hasEmptyDefaults", () => {
      const state = useSettingsStore.getState();
      expect(state.language).toBe("");
      expect(state.lastOpenedPath).toBe("");
      expect(state.theme).toBe("");
      expect(state.encoding).toBe("");
      expect(state.logPath).toBe("");
      expect(state.osName).toBe("");
      expect(state.pathSeparator).toBe("/");
    });
  });

  describe("setSettings", () => {
    it("test_setSettings_updatesAllSettingsFields", () => {
      const { setSettings } = useSettingsStore.getState();
      setSettings(SAMPLE_SETTINGS);

      const state = useSettingsStore.getState();
      expect(state.language).toBe("ja");
      expect(state.lastOpenedPath).toBe("/home/user/data");
      expect(state.theme).toBe("dark");
      expect(state.encoding).toBe("utf-8");
      expect(state.logPath).toBe("/home/user/logs");
    });

    it("test_setSettings_doesNotClearOsInfo", () => {
      useSettingsStore.setState({ osName: "macOS", pathSeparator: "/" });
      const { setSettings } = useSettingsStore.getState();
      setSettings(SAMPLE_SETTINGS);

      const state = useSettingsStore.getState();
      expect(state.osName).toBe("macOS");
      expect(state.pathSeparator).toBe("/");
    });
  });

  describe("setOsInfo", () => {
    it("test_setOsInfo_updatesOsNameAndPathSeparator", () => {
      const { setOsInfo } = useSettingsStore.getState();
      setOsInfo(SAMPLE_OS_INFO);

      const state = useSettingsStore.getState();
      expect(state.osName).toBe("Windows");
      expect(state.pathSeparator).toBe("\\");
    });

    it("test_setOsInfo_doesNotClearSettingsFields", () => {
      useSettingsStore.setState({ language: "en", theme: "light" });
      const { setOsInfo } = useSettingsStore.getState();
      setOsInfo(SAMPLE_OS_INFO);

      const state = useSettingsStore.getState();
      expect(state.language).toBe("en");
      expect(state.theme).toBe("light");
    });

    it("test_setOsInfo_canSwitchSeparator", () => {
      const { setOsInfo } = useSettingsStore.getState();
      setOsInfo({ osName: "Linux", pathSeparator: "/" });

      expect(useSettingsStore.getState().pathSeparator).toBe("/");
    });
  });
});
