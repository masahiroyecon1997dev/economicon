import type { TableInfoType } from "./commonTypes";

export type SettingsType = { settings: {
  defaultFolderPath: string;
  displayRows: number;
  appLanguage: string;
  encoding: string;
  pathSeparator: string;
}
}
export type FilesType = {
  files: {
    files: {
      name: string;
      isFile: boolean;
      size: number;
      modifiedTime: string;
    }[],
    directoryPath: string;
  },
};
export type TableListType = { tableList: string[] };
export type TableInfosType = { tableInfos: TableInfoType[] };
export type CurrentViewType = { currentView: string };
