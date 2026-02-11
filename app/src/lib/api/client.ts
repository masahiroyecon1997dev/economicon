import { invoke } from "@tauri-apps/api/core";

const BASE_API_PREFIX = "/api";

/**
 * リクエストボディの型定義
 */
type RequestBody = Record<string, unknown> | undefined;

/**
 * Tauri経由でAPIリクエストを行うクライアント
 */
export const client = {
  get: async <T>(path: string, params?: RequestBody): Promise<{ data: T }> => {
    // クエリパラメータがある場合はURLに付加するか、bodyとして送るか
    // Rust側の実装では `proxy_request` は `query` 引数を受け取るようになっているため
    // ここでparamsをqueryとして渡します
    return invokeRequest<T>("GET", path, undefined, params);
  },

  post: async <T>(path: string, data?: RequestBody): Promise<{ data: T }> => {
    return invokeRequest<T>("POST", path, data);
  },

  /**
   * ファイルアップロード用
   * @param path APIのエンドポイント
   * @param file Fileオブジェクト
   */
  upload: async <T>(path: string, file: File): Promise<{ data: T }> => {
    // FileをArrayBufferに変換
    const arrayBuffer = await file.arrayBuffer();
    // Uint8Array (Vec<u8>) に変換
    const uint8Array = new Uint8Array(arrayBuffer);

    // Tauriコマンド呼び出し
    // URLには /api を付与
    const fullPath = `${BASE_API_PREFIX}${path}`;

    // upload_file コマンドの引数仕様に合わせて呼び出し
    const response = await invoke<T>("upload_file", {
      path: fullPath,
      fileData: Array.from(uint8Array), // Rust側で Vec<u8> として受け取るため配列化
      fileName: file.name,
    });

    return { data: response };
  },

  /**
   * テーブルデータ（バイナリ）取得用
   */
  fetch_binary: async <T>(
    method: string,
    path: string,
    body?: RequestBody,
    query?: RequestBody,
  ): Promise<{ data: T }> => {
    return invokeBinaryRequest<T>(method, path, body, query);
  },
};

/**
 * リクエスト処理（共通用）
 */
const invokeRequest = async <T>(
  method: string,
  path: string,
  body?: RequestBody,
  query?: RequestBody,
): Promise<{ data: T }> => {
  const fullPath = `${BASE_API_PREFIX}${path}`;

  try {
    const response = await invoke<T>("proxy_request", {
      method,
      path: fullPath,
      body,
      query,
    });
    return { data: response };
  } catch (error) {
    console.error(`API Request Failed: ${method} ${fullPath}`, error);
    throw error;
  }
};

/**
 * リクエスト処理（バイナリレスポンス用）
 */
const invokeBinaryRequest = async <T>(
  method: string,
  path: string,
  body?: RequestBody,
  query?: RequestBody,
): Promise<{ data: T }> => {
  const fullPath = `${BASE_API_PREFIX}${path}`;

  try {
    const response = await invoke<T>("fetch_binary", {
      method,
      path: fullPath,
      body,
      query,
    });
    return { data: response };
  } catch (error) {
    console.error(`API Request Failed: ${method} ${fullPath}`, error);
    throw error;
  }
};
