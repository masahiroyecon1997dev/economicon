mod files;
mod os_info;

use tauri::State;
use reqwest::Client;
use serde::{Serialize};
use std::time::Duration;
use uuid::Uuid;

use files::{get_files_internal, GetFilesResponse, FileError};
use os_info::{get_os_info_internal, OsInfoResponse};

// HTTPクライアントを保持するState
struct ClientState {
    client: Client,
}

// 起動時に生成した認証トークンを保持するState（アプリライフサイクル中にメモリ内で保持）
struct AuthTokenState {
    token: String,
}

// 共通のエラーレスポンス型
#[derive(Debug, Serialize)]
struct ApiError {
    message: String,
}

impl From<reqwest::Error> for ApiError {
    fn from(err: reqwest::Error) -> Self {
        ApiError { message: err.to_string() }
    }
}

impl From<String> for ApiError {
    fn from(s: String) -> Self {
        ApiError { message: s }
    }
}

// 通常のJSONリクエスト用コマンド
#[tauri::command]
async fn proxy_request(
    state: State<'_, ClientState>,
    auth: State<'_, AuthTokenState>,
    method: String,
    path: String,
    body: Option<serde_json::Value>,
    query: Option<serde_json::Value>,
) -> Result<serde_json::Value, ApiError> {
    let base_url = "http://127.0.0.1:8000"; // PythonサーバーのURL
    let url = format!("{}{}", base_url, path);

    let mut request_builder = match method.to_uppercase().as_str() {
        "GET" => state.client.get(&url),
        "POST" => state.client.post(&url),
        "PUT" => state.client.put(&url),
        "DELETE" => state.client.delete(&url),
        _ => return Err(ApiError { message: format!("Unsupported method: {}", method) }),
    };

    // 認証トークンをヘッダーに付与
    request_builder = request_builder.header("X-Auth-Token", &auth.token);

    if let Some(q) = query {
        request_builder = request_builder.query(&q);
    }

    if let Some(b) = body {
        request_builder = request_builder.json(&b);
    }

    let response = request_builder.send().await?;

    // エラーレスポンスの場合もJSONとして返す、あるいはエラーにするかは要件次第
    // ここでは成功ステータスでなくてもbodyを返すようにしますが、
    // 必要なら response.error_for_status() を呼んでください。
    let json_response: serde_json::Value = response.json().await?;
    Ok(json_response)
}

#[tauri::command]
async fn fetch_binary(
    state: State<'_, ClientState>,
    auth: State<'_, AuthTokenState>,
    method: String,
    path: String,
    body: Option<serde_json::Value>,
    query: Option<serde_json::Value>,
) -> Result<Vec<u8>, ApiError> {
    let base_url = "http://127.0.0.1:8000";
    let url = format!("{}{}", base_url, path);
    let mut request_builder = match method.to_uppercase().as_str() {
        "GET" => state.client.get(&url),
        "POST" => state.client.post(&url),
        "PUT" => state.client.put(&url),
        "DELETE" => state.client.delete(&url),
        _ => return Err(ApiError { message: format!("Unsupported method: {}", method) }),
    };

    // 認証トークンをヘッダーに付与
    request_builder = request_builder.header("X-Auth-Token", &auth.token);

    if let Some(q) = query {
        request_builder = request_builder.query(&q);
    }

    if let Some(b) = body {
        request_builder = request_builder.json(&b);
    }
    let response = request_builder.send().await?;

    let bytes = response
        .bytes()
        .await
        .map_err(|e| e.to_string())?;

    Ok(bytes.to_vec()) // フロントエンド（JS）へ Uint8Array として渡る
}

// ファイルアップロード用コマンド (マルチパート)
#[tauri::command]
async fn upload_file(
    state: State<'_, ClientState>,
    auth: State<'_, AuthTokenState>,
    path: String,
    file_data: Vec<u8>,
    file_name: String,
) -> Result<serde_json::Value, ApiError> {
    let base_url = "http://127.0.0.1:8000";
    let url = format!("{}{}", base_url, path);

    let part = reqwest::multipart::Part::bytes(file_data)
        .file_name(file_name.clone());

    let form = reqwest::multipart::Form::new()
        .part("file", part); // Python側が "file" キーを期待していると仮定

    // 認証トークンをヘッダーに付与
    let response = state.client.post(&url)
        .header("X-Auth-Token", &auth.token)
        .multipart(form)
        .send()
        .await?;

    let json_response: serde_json::Value = response.json().await?;
    Ok(json_response)
}

/// 起動時に生成した認証トークンをフロントエンドへ返すコマンド。
/// React の初期化フェーズで呼び出し、取得完了まで API リクエストをブロックするために使用する。
#[tauri::command]
fn get_auth_token(auth: State<'_, AuthTokenState>) -> String {
    auth.token.clone()
}

// ファイル一覧取得用コマンド
#[tauri::command]
async fn get_files(directory_path: String) -> Result<GetFilesResponse, FileError> {
    get_files_internal(&directory_path)
}

// OS情報取得コマンド（同期: ファイルシステムアクセス不要）
#[tauri::command]
fn get_os_info() -> OsInfoResponse {
    get_os_info_internal()
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    // 起動時に予測不可能なUUID v4トークンを1回だけ生成する
    // このトークンはプロセスのライフサイクル中メモリ内に保持され、
    // FastAPIサイドカーへは環境変数 ECONOMICOM_API_AUTH_TOKEN として引き継がれる
    let auth_token = Uuid::new_v4().to_string();

    // サイドカー（FastAPI）が環境変数を参照できるよう、現プロセスに設定する
    // Tauriがサイドカーを起動する際、子プロセスは親の環境変数を継承する
    // SAFETY: tauri::Builder::default() を呼ぶ前に設定することで
    //         マルチスレッド下での競合を回避する
    unsafe {
        std::env::set_var("ECONOMICOM_API_AUTH_TOKEN", &auth_token);
    }

    // クライアントの初期化（タイムアウト設定など）
    let client = Client::builder()
        .timeout(Duration::from_secs(300)) // 分析処理など時間がかかる場合を考慮
        .build()
        .expect("Failed to create HTTP client");

    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .manage(ClientState { client })
        .manage(AuthTokenState { token: auth_token }) // 生成したトークンをStateとして登録
        .invoke_handler(tauri::generate_handler![
            proxy_request,
            fetch_binary,
            upload_file,
            get_files,
            get_os_info,
            get_auth_token
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
