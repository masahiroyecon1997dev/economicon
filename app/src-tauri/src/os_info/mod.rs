use serde::Serialize;

/// OS情報レスポンス
#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct OsInfoResponse {
    /// OS名: "Windows" | "macOS" | "Linux"
    pub os_name: String,
    /// パスセパレータ: "\\" (Windows) | "/" (macOS/Linux)
    pub path_separator: String,
}

/// 実行中のOSを判定してOS情報を返す
pub fn get_os_info_internal() -> OsInfoResponse {
    match std::env::consts::OS {
        "windows" => OsInfoResponse {
            os_name: "Windows".into(),
            path_separator: "\\".into(),
        },
        "macos" => OsInfoResponse {
            os_name: "macOS".into(),
            path_separator: "/".into(),
        },
        _ => OsInfoResponse {
            os_name: "Linux".into(),
            path_separator: "/".into(),
        },
    }
}
