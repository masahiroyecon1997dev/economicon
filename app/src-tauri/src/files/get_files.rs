use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;
use std::time::SystemTime;
use thiserror::Error;

/// ファイル情報の構造体
#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct FileItem {
    pub name: String,
    pub is_file: bool,
    pub is_symlink: bool,
    pub size: u64,
    pub modified_time: Option<u64>,
}

/// 成功時のレスポンス
#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct GetFilesResponse {
    pub directory_path: String,
    pub files: Vec<FileItem>,
}

/// エラーの種類を識別するEnum（thiserrorを使用）
#[derive(Debug, Error, Serialize)]
#[serde(tag = "errorType", content = "message")]
pub enum FileError {
    #[error("Path is required")]
    PathRequired,

    #[error("Path not found: {0}")]
    PathNotFound(String),

    #[error("Not a directory: {0}")]
    NotADirectory(String),

    #[error("Permission denied: {0}")]
    PermissionDenied(String),

    #[error("Failed to canonicalize path: {0}")]
    CanonicalizationError(String),

    #[error("Unexpected error: {0}")]
    UnexpectedError(String),
}

/// バリデーション処理
fn validate_and_prepare(directory_path: &str) -> Result<PathBuf, FileError> {
    // 必須チェック（空文字専用のエラー）
    if directory_path.trim().is_empty() {
        return Err(FileError::PathRequired);
    }

    let path = PathBuf::from(directory_path);

    // 存在チェック
    if !path.exists() {
        return Err(FileError::PathNotFound(format!(
            "Directory does not exist: {}",
            directory_path
        )));
    }

    // ディレクトリチェック（シンボリックリンクのリンク先もチェック）
    let metadata = match fs::metadata(&path) {
        Ok(m) => m,
        Err(e) if e.kind() == std::io::ErrorKind::PermissionDenied => {
            return Err(FileError::PermissionDenied(format!(
                "Cannot access path: {}",
                directory_path
            )));
        }
        Err(e) => {
            return Err(FileError::UnexpectedError(e.to_string()));
        }
    };

    if !metadata.is_dir() {
        return Err(FileError::NotADirectory(format!(
            "Path is not a directory: {}",
            directory_path
        )));
    }

    // 相対パスを絶対パスに変換（正規化）
    let canonical_path = dunce::canonicalize(path).map_err(|e| {
        FileError::CanonicalizationError(format!(
            "Failed to canonicalize path '{}': {}",
            directory_path, e
        ))
    })?;

    Ok(canonical_path)
}

/// メインロジック
pub fn get_files_internal(directory_path: &str) -> Result<GetFilesResponse, FileError> {
    // バリデーション（正規化された絶対パスを取得）
    let canonical_path = validate_and_prepare(directory_path)?;

    // ディレクトリ内のエントリを読み取り
    let entries = match fs::read_dir(&canonical_path) {
        Ok(entries) => entries,
        Err(e) if e.kind() == std::io::ErrorKind::PermissionDenied => {
            return Err(FileError::PermissionDenied(format!(
                "Permission denied: {}",
                canonical_path.to_string_lossy()
            )));
        }
        Err(e) => {
            return Err(FileError::UnexpectedError(e.to_string()));
        }
    };

    let mut files = Vec::new();

    for entry_result in entries {
        let entry = match entry_result {
            Ok(e) => e,
            Err(_) => continue, // スキップ
        };

        // entry.metadata()を使用（fs::metadataより効率的）
        let metadata = match entry.metadata() {
            Ok(m) => m,
            Err(_) => continue,
        };

        // ファイル名の取得（無効なUTF-8も考慮）
        let name = entry.file_name().to_string_lossy().to_string();

        let is_file = metadata.is_file();
        let is_symlink = metadata.is_symlink();
        let size = if is_file { metadata.len() } else { 0 };

        // 更新日時をUNIXタイムスタンプ（秒）に変換
        let modified_time = metadata.modified().ok().and_then(|time| {
            time.duration_since(SystemTime::UNIX_EPOCH)
                .ok()
                .map(|d| d.as_secs())
        });

        files.push(FileItem {
            name,
            is_file,
            is_symlink,
            size,
            modified_time,
        });
    }

    // ソート: ディレクトリを先に、ファイルを後に、同じ種類の中では名前順
    files.sort_by(|a, b| match (a.is_file, b.is_file) {
        (true, false) => std::cmp::Ordering::Greater, // aがファイル、bがディレクトリ
        (false, true) => std::cmp::Ordering::Less,    // aがディレクトリ、bがファイル
        _ => a.name.cmp(&b.name),                     // 同じ種類なら名前順
    });

    // 正規化されたパスを文字列化（無効なUTF-8も考慮）
    let directory_path_str = canonical_path.to_string_lossy().to_string();

    Ok(GetFilesResponse {
        directory_path: directory_path_str,
        files,
    })
}

/// フォールバック先ディレクトリ候補を優先順に返す
/// ホームディレクトリ → OS固有のルート → 最終的な絶対ルート
fn get_fallback_directories() -> Vec<PathBuf> {
    let mut candidates = Vec::new();

    // ホームディレクトリ（USERPROFILE=Windows / HOME=Unix）
    if let Ok(home) = std::env::var("USERPROFILE").or_else(|_| std::env::var("HOME")) {
        candidates.push(PathBuf::from(home));
    }

    // OS固有のルート（コンパイル時に分岐）
    #[cfg(target_os = "windows")]
    {
        candidates.push(PathBuf::from("C:\\Users"));
        candidates.push(PathBuf::from("C:\\"));
    }
    #[cfg(not(target_os = "windows"))]
    {
        candidates.push(PathBuf::from("/home"));
        candidates.push(PathBuf::from("/"));
    }

    candidates
}

/// パスが無効でも必ず有効な `GetFilesResponse` を返すラッパー。
/// アプリ初期化時や設定が壊れていた場合のフォールバックとして使用する。
/// 優先順: 指定パス → ホームディレクトリ → OS固有ルート → 空レスポンス（最終手段）
pub fn get_files_with_fallback(directory_path: &str) -> GetFilesResponse {
    // まず指定パスを試みる
    if !directory_path.trim().is_empty() {
        if let Ok(res) = get_files_internal(directory_path) {
            return res;
        }
    }

    // フォールバック候補を順に試す
    for fallback in get_fallback_directories() {
        if let Ok(res) = get_files_internal(fallback.to_string_lossy().as_ref()) {
            return res;
        }
    }

    // 全て失敗した場合（実際にはまず発生しない）は空レスポンスを返す
    GetFilesResponse {
        directory_path: String::new(),
        files: Vec::new(),
    }
}
