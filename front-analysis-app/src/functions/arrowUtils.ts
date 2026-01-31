/**
 * Apache Arrow関連のユーティリティ関数
 */
import { tableFromIPC } from 'apache-arrow';
import type { Table } from 'apache-arrow';

const API_BASE_URL = '/api/table';

export interface FetchDataToArrowResponse {
  code: string;
  message: string;
  result: {
    tableName: string;
    arrowData: string; // Base64エンコードされたArrow IPC形式データ
    totalRows: number;
    startRow: number;
    endRow: number;
  };
}

/**
 * Apache Arrow形式でテーブルデータを取得
 * 
 * @param tableName テーブル名
 * @param startRow 取得開始行（1-based）
 * @param chunkSize チャンクサイズ（デフォルト500行）
 * @returns Apache Arrowテーブル
 */
export async function fetchDataToArrow(
  tableName: string,
  startRow: number,
  chunkSize: number = 500
): Promise<{ table: Table; totalRows: number; startRow: number; endRow: number }> {
  try {
    const response = await fetch(`${API_BASE_URL}/fetch-data-arrow`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        tableName,
        startRow,
        chunkSize,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || 'Failed to fetch arrow data');
    }

    const data: FetchDataToArrowResponse = await response.json();

    if (data.code !== 'OK') {
      throw new Error(data.message || 'API returned error');
    }

    // Base64デコードしてArrayBufferに変換
    const arrowBytes = base64ToArrayBuffer(data.result.arrowData);

    // Arrow IPCフォーマットからテーブルを復元
    const table = tableFromIPC(arrowBytes);

    return {
      table,
      totalRows: data.result.totalRows,
      startRow: data.result.startRow,
      endRow: data.result.endRow,
    };
  } catch (error) {
    console.error('Error fetching arrow data:', error);
    throw error;
  }
}

/**
 * Base64文字列をArrayBufferに変換
 * 
 * @param base64 Base64エンコードされた文字列
 * @returns ArrayBuffer
 */
function base64ToArrayBuffer(base64: string): ArrayBuffer {
  const binaryString = atob(base64);
  const bytes = new Uint8Array(binaryString.length);
  for (let i = 0; i < binaryString.length; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return bytes.buffer;
}

/**
 * Arrow Tableを行オブジェクトの配列に変換
 * 
 * @param table Apache Arrowテーブル
 * @returns 行データの配列
 */
export function arrowTableToRows(table: Table): Record<string, any>[] {
  const rows: Record<string, any>[] = [];
  const numRows = table.numRows;
  const schema = table.schema;

  for (let i = 0; i < numRows; i++) {
    const row: Record<string, any> = {};
    for (const field of schema.fields) {
      const column = table.getChild(field.name);
      row[field.name] = column?.get(i);
    }
    rows.push(row);
  }

  return rows;
}
