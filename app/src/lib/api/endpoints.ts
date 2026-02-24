import { invoke } from "@tauri-apps/api/core";
import { API_ENDPOINTS } from "../../constants/api";
import type { FilesType, FileType } from "../../types/commonTypes";
import { client } from "./client";

// Tauri��get_files�R�}���h���Ԃ����X�|���X�^�iRust�̍\���̂ɑΉ��j
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

/**
 * Tauri��get_files�R�}���h���g�p���ăt�@�C���ꗗ���擾����
 * Python�T�[�o�[���o�R�����ARust������OS�̃t�@�C���V�X�e���ɃA�N�Z�X����
 * �G���[���͗�O���X���[����
 */
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
        // modified_time��Unix�^�C���X�^���v(�b)�̂��߁A�~���b�ϊ�����ISO������
        modifiedTime:
          f.modifiedTime != null
            ? new Date(f.modifiedTime * 1000).toISOString()
            : "",
      }),
    ),
  };
};

/**
 * Apache Arrow IPC�`���Ńe�[�u���f�[�^���擾����
 * �o�C�i���f�[�^�̂��߁A�ʏ��JSON�v���L�V�ł͂Ȃ�fetch_binary�R�}���h���g�p����
 */
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
  // Tauri����̃o�C�i���z��(number[])��Uint8Array�ɕϊ�
  return new Uint8Array(response.data);
};
