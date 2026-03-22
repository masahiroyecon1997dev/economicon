import { create } from "zustand";
import type { FilesType } from "../types/commonTypes";

export type FilesActions = {
  setFiles: (newFiles: FilesType) => void;
};

type FilesStore = FilesType & FilesActions;

export const useFilesStore = create<FilesStore>((set) => ({
  files: [],
  directoryPath: "",
  setFiles: (newFiles) => {
    set(newFiles);
  },
}));
