import { beforeEach, describe, expect, it } from "vitest";
import type { FilesType } from "@/types/commonTypes";
import { useFilesStore } from "@/stores/files";

const EMPTY_FILES: FilesType = { files: [], directoryPath: "" };

const SAMPLE_FILES: FilesType = {
  files: [
    {
      name: "sample.csv",
      isFile: true,
      size: 1024,
      modifiedTime: "2026-01-01T00:00:00Z",
    },
    {
      name: "subdir",
      isFile: false,
      size: 0,
      modifiedTime: "2026-01-01T00:00:00Z",
    },
  ],
  directoryPath: "/home/user/data",
};

beforeEach(() => {
  useFilesStore.setState(EMPTY_FILES);
});

describe("useFilesStore", () => {
  describe("initial state", () => {
    it("test_initialState_isEmpty", () => {
      const state = useFilesStore.getState();
      expect(state.files).toEqual([]);
      expect(state.directoryPath).toBe("");
    });
  });

  describe("setFiles", () => {
    it("test_setFiles_updatesFilesAndDirectoryPath", () => {
      const { setFiles } = useFilesStore.getState();
      setFiles(SAMPLE_FILES);

      const state = useFilesStore.getState();
      expect(state.files).toHaveLength(2);
      expect(state.files[0].name).toBe("sample.csv");
      expect(state.directoryPath).toBe("/home/user/data");
    });

    it("test_setFiles_withEmptyFiles_clearsState", () => {
      useFilesStore.setState(SAMPLE_FILES);
      const { setFiles } = useFilesStore.getState();
      setFiles(EMPTY_FILES);

      const state = useFilesStore.getState();
      expect(state.files).toEqual([]);
      expect(state.directoryPath).toBe("");
    });

    it("test_setFiles_preservesAllFileFields", () => {
      const { setFiles } = useFilesStore.getState();
      setFiles(SAMPLE_FILES);

      const file = useFilesStore.getState().files[0];
      expect(file.name).toBe("sample.csv");
      expect(file.isFile).toBe(true);
      expect(file.size).toBe(1024);
      expect(file.modifiedTime).toBe("2026-01-01T00:00:00Z");
    });

    it("test_setFiles_canCallMultipleTimes", () => {
      const { setFiles } = useFilesStore.getState();
      setFiles(SAMPLE_FILES);
      setFiles({ files: [], directoryPath: "/new/path" });

      const state = useFilesStore.getState();
      expect(state.files).toEqual([]);
      expect(state.directoryPath).toBe("/new/path");
    });
  });
});
