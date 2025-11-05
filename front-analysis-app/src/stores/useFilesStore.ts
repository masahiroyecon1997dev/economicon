import { create } from "zustand";
import type { FilesType } from "../types/stateTypes";

export type FilesActions = {
  setFiles: (files: FilesType) => void;
}

type FilesStore = FilesType & FilesActions;

const useFilesStore = create<FilesStore>((set) => ({
  files: { files: [], directoryPath: "" },
  setFiles: (files) => set(() => (files)),
}));

export default useFilesStore;
