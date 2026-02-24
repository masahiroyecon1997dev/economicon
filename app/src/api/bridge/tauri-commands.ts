import { invoke } from "@tauri-apps/api/core";
import { API_ENDPOINTS } from "../../constants/api";
import type { FilesType, FileType } from "../../types/commonTypes";
import { client } from "./api-gateway";

type RustFileItem = {
  name: string;
  isFile: boolean;
  isSymlink: boolean;
  size: number;
  modifiedTime: number | null;
};

type RustGetFilesResponse = {
  directoryPath: string;
  files: RustFileItem[];
};

export const getFiles = async (path: string): Promise<FilesType> => {
  const response = await invoke<RustGetFilesResponse>("get_files", {
    directoryPath: path,
  });
  return {
    directoryPath: response.directoryPath,
    files: response.files.map(
      (f): FileType => ({
        name: f.name,
        isFile: f.isFile,
        size: f.size,
        modifiedTime:
          f.modifiedTime != null
            ? new Date(f.modifiedTime * 1000).toISOString()
            : "",
      }),
    ),
  };
};

export const getOsInfo = async (): Promise<{
  osName: string;
  pathSeparator: string;
}> => {
  return await invoke<{ osName: string; pathSeparator: string }>("get_os_info");
};

export const fetchDataToArrow = async (
  tableName: string,
  startRow: number = 0,
  chunk_size: number = 500,
): Promise<Uint8Array> => {
  const response = await client.fetch_binary<number[]>(
    "POST",
    API_ENDPOINTS.TABLE.FETCH_DATA_TO_ARROW,
    {
      tableName: tableName,
      startRow: startRow,
      chunkSize: chunk_size,
    },
  );
  return new Uint8Array(response.data);
};
