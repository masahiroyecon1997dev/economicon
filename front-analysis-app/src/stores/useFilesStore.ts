import { create } from "zustand";
import type { FilesType } from "../types/commonTypes";

export type FilesStateType = {
  files: FilesType;
};

export type FilesActions = {
  setFiles: (files: FilesStateType) => void;
}

type FilesStore = FilesStateType & FilesActions;

export const useFilesStore = create<FilesStore>((set) => ({
  files: {
    files: [],
    directoryPath: "",
  },
  setFiles: (files) => set(() => (files)),
}));
