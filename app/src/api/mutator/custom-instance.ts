import { client } from "../bridge/api-gateway"; // 既存のclient.tsをインポート

export const customInstance = async <T>(
  config: {
    url: string;
    method: string;
    headers?: Record<string, string>;
    params?: Record<string, unknown>; // クエリパラメータ
    data?: unknown; // リクエストボディ
  },
  _options?: unknown,
): Promise<T> => {
  const { url, method, params, data } = config;
  // 既存の client オブジェクトのメソッドを呼び出す
  // client.get や client.post は { data: T } を返すので、中身だけ抽出して返します
  let response: { data: T };

  switch (method.toUpperCase()) {
    case "GET":
      response = await client.get<T>(url, params);
      break;
    case "POST":
      response = await client.post<T>(url, data);
      break;
    case "PUT":
      response = await client.put<T>(url, data);
      break;
    case "DELETE":
      response = await client.delete<T>(url, params);
      break;
    default:
      throw new Error(`Method ${method} not implemented`);
  }

  return response.data;
};

// Orvalがエラーの型を参照できるように、Errorの型定義も必要であれば追加
export type ErrorType<Error> = Error;
