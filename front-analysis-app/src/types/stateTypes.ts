import type { TableInfoType } from "./commonTypes";

export type SettingsType = { settings: {
  defaultFolderPath: string;
  displayRows: number;
  appLanguage: string;
} }
export type TableListType = { tableList: string[] };
export type TableInfosType = { tableInfos: TableInfoType[] };
export type CurrentViewType = string;
