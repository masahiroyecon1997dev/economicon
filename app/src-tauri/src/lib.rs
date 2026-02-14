mod files;

use tauri::State;
use reqwest::Client;
use serde::{Serialize};
use std::time::Duration;

use files::{get_files_internal, GetFilesResponse};

// HTTPクライアントを保持するState
struct ClientState {
    client: Client,
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

    let response = state.client.post(&url)
        .multipart(form)
        .send()
        .await?;

    let json_response: serde_json::Value = response.json().await?;
    Ok(json_response)
}

// ファイル一覧取得用コマンド
#[tauri::command]
async fn get_files(directory_path: String) -> Result<GetFilesResponse, String> {
    get_files_internal(&directory_path).map_err(|e| e.to_string())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    // クライアントの初期化（タイムアウト設定など）
    let client = Client::builder()
        .timeout(Duration::from_secs(300)) // 分析処理など時間がかかる場合を考慮
        .build()
        .expect("Failed to create HTTP client");

    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .manage(ClientState { client }) // Stateを登録
        .invoke_handler(tauri::generate_handler![
            proxy_request,
            fetch_binary,
            upload_file,
            get_files
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
