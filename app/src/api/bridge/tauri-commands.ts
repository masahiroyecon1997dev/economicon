import { invoke } from "@tauri-apps/api/core";
import { API_ENDPOINTS } from "../../constants/api";
import type { FilesType, FileType } from "../../types/commonTypes";
import { client } from "./api-gateway";

// Rust 側の FileError に対応するエラー種別
export type FileErrorType =
  | "PathRequired"
  | "PathNotFound"
  | "NotADirectory"
  | "PermissionDenied"
  | "CanonicalizationError"
  | "UnexpectedError";

// Tauri の get_files コマンドが返す構造化エラー
type FileErrorResponse = {
  errorType: FileErrorType;
  message?: string;
};

/** Tauri の get_files コマンド固有のエラークラス */
export class TauriFileError extends Error {
  constructor(
    public readonly errorType: FileErrorType,
    public readonly originalMessage: string,
  ) {
    super(originalMessage);
    this.name = "TauriFileError";
  }
}

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
  try {
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
  } catch (e: unknown) {
    // Tauri は Err(FileError) を構造化オブジェクトとして throw する
    if (e !== null && typeof e === "object" && "errorType" in e) {
      const err = e as FileErrorResponse;
      throw new TauriFileError(err.errorType, err.message ?? "");
    }
    throw e;
  }
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
