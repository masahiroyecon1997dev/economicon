import { invoke } from "@tauri-apps/api/core";
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
  public readonly errorType: FileErrorType;
  public readonly originalMessage: string;
  constructor(errorType: FileErrorType, originalMessage: string) {
    super(originalMessage);
    this.errorType = errorType;
    this.originalMessage = originalMessage;
    this.name = "TauriFileError";

    Object.setPrototypeOf(this, TauriFileError.prototype);
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

/** Rust の FileItem → TypeScript の FileType に変換する共通マッパー */
const mapRustFiles = (response: RustGetFilesResponse): FilesType => ({
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
});

export const getFiles = async (path: string): Promise<FilesType> => {
  try {
    const response = await invoke<RustGetFilesResponse>("get_files", {
      directoryPath: path,
    });
    return mapRustFiles(response);
  } catch (e: unknown) {
    // Tauri は Err(FileError) を構造化オブジェクトとして throw する
    if (e !== null && typeof e === "object" && "errorType" in e) {
      const err = e as FileErrorResponse;
      throw new TauriFileError(err.errorType, err.message ?? "");
    }
    throw e;
  }
};

/**
 * エラーを投げない安全版 getFiles。
 * 指定パスが存在しない・空の場合はホームディレクトリ等へ自動フォールバックする。
 * アプリ初期化時（lastOpenedPath が消えた場合など）に使用する。
 */
export const getFilesSafe = async (path: string): Promise<FilesType> => {
  const response = await invoke<RustGetFilesResponse>("get_files_safe", {
    directoryPath: path,
  });
  return mapRustFiles(response);
};

export const getOsInfo = async (): Promise<{
  osName: string;
  pathSeparator: string;
}> => {
  return await invoke<{ osName: string; pathSeparator: string }>("get_os_info");
};

/**
 * Rust 側で起動時に生成された認証トークンを取得する。
 *
 * アプリの初期化フェーズ（App.tsx の useEffect）で呼び出し、
 * このトークン取得が完了するまで API リクエストを発生させないよう制御する。
 * トークン自体は Rust プロキシが X-Auth-Token ヘッダーとして自動付与するため、
 * React 側でヘッダーを手動設定する必要はない。
 */
export const getAuthToken = async (): Promise<string> => {
  return await invoke<string>("get_auth_token");
};

/** FastAPI サイドカーが listen しているポート番号を返す */
export const getApiPort = async (): Promise<number> => {
  return await invoke<number>("get_api_port");
};

/**
 * 指定したフルパスに通常ファイルが存在するか確認する。
 * ファイル一覧キャッシュではなく OS に直接問い合わせるため、
 * 保存直前の上書き確認に使用する。
 */
export const checkFileExists = async (filePath: string): Promise<boolean> => {
  return await invoke<boolean>("check_file_exists", { filePath });
};

export const fetchDataToArrow = async (
  tableName: string,
  startRow: number = 0,
  chunkSize: number = 500,
): Promise<Uint8Array> => {
  const response = await client.fetch_binary<number[]>(
    "POST",
    "/api/table/fetch-data-to-arrow",
    {
      tableName: tableName,
      startRow: startRow,
      chunkSize: chunkSize,
    },
  );
  return new Uint8Array(response.data);
};
