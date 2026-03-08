mod files;
mod os_info;

use reqwest::Client;
use serde::Serialize;
use std::net::TcpListener;
use std::time::Duration;
use tauri::State;
use uuid::Uuid;

use std::sync::Mutex;
use tauri_plugin_shell::ShellExt;
use tauri_plugin_shell::process::CommandChild;

use files::{get_files_internal, get_files_with_fallback, FileError, GetFilesResponse};
use os_info::{get_os_info_internal, OsInfoResponse};

// HTTPクライアントを保持するState
struct ClientState {
    client: Client,
}

// 起動時に生成した認証トークンを保持するState（アプリライフサイクル中にメモリ内で保持）
struct AuthTokenState {
    token: String,
}

// FastAPI サイドカーが listen するポート番号を保持するState
struct PortState {
    port: u16,
}

// 起動したサイドカープロセスを保持するState（終了時に kill するために使用）
struct SidecarState {
    child: Mutex<Option<CommandChild>>,
}

/// 指定ポートから順に TcpListener::bind を試し、最初に確保できたポートを返す。
/// bind に成功した Listener は即 drop し、Python サイドカーが同ポートを取得できるようにする。
fn find_available_port(starting_from: u16) -> u16 {
    for port in starting_from..=65535 {
        if TcpListener::bind(("127.0.0.1", port)).is_ok() {
            return port;
        }
    }
    panic!("No available port found starting from {}", starting_from);
}

// 共通のエラーレスポンス型
#[derive(Debug, Serialize)]
struct ApiError {
    message: String,
}

impl From<reqwest::Error> for ApiError {
    fn from(err: reqwest::Error) -> Self {
        ApiError {
            message: err.to_string(),
        }
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
    port: State<'_, PortState>,
    method: String,
    path: String,
    body: Option<serde_json::Value>,
    query: Option<serde_json::Value>,
) -> Result<serde_json::Value, ApiError> {
    // パス検証: 必ず "/api/" 始まりであることを確認する。
    // これによりフロントエンドが侵害された場合でも
    // "/api/" 以外のエンドポイントへの呼び出しを防ぐ。
    if !path.starts_with("/api/") {
        return Err(ApiError {
            message: format!("Invalid path '{}': must start with '/api/'", path),
        });
    }

    let base_url = format!("http://127.0.0.1:{}", port.port); // PythonサーバーのURL
    let url = format!("{}{}", base_url, path);

    let mut request_builder = match method.to_uppercase().as_str() {
        "GET" => state.client.get(&url),
        "POST" => state.client.post(&url),
        "PUT" => state.client.put(&url),
        "DELETE" => state.client.delete(&url),
        _ => {
            return Err(ApiError {
                message: format!("Unsupported method: {}", method),
            })
        }
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
    port: State<'_, PortState>,
    method: String,
    path: String,
    body: Option<serde_json::Value>,
    query: Option<serde_json::Value>,
) -> Result<Vec<u8>, ApiError> {
    // パス検証: 必ず "/api/" 始まりであることを確認する。
    if !path.starts_with("/api/") {
        return Err(ApiError {
            message: format!("Invalid path '{}': must start with '/api/'", path),
        });
    }

    let base_url = format!("http://127.0.0.1:{}", port.port);
    let url = format!("{}{}", base_url, path);
    let mut request_builder = match method.to_uppercase().as_str() {
        "GET" => state.client.get(&url),
        "POST" => state.client.post(&url),
        "PUT" => state.client.put(&url),
        "DELETE" => state.client.delete(&url),
        _ => {
            return Err(ApiError {
                message: format!("Unsupported method: {}", method),
            })
        }
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

    let bytes = response.bytes().await.map_err(|e| e.to_string())?;

    Ok(bytes.to_vec()) // フロントエンド（JS）へ Uint8Array として渡る
}

// ファイルアップロード用コマンド (マルチパート)
#[tauri::command]
async fn upload_file(
    state: State<'_, ClientState>,
    auth: State<'_, AuthTokenState>,
    port: State<'_, PortState>,
    path: String,
    file_data: Vec<u8>,
    file_name: String,
) -> Result<serde_json::Value, ApiError> {
    // パス検証: 必ず "/api/" 始まりであることを確認する。
    if !path.starts_with("/api/") {
        return Err(ApiError {
            message: format!("Invalid path '{}': must start with '/api/'", path),
        });
    }

    let base_url = format!("http://127.0.0.1:{}", port.port);
    let url = format!("{}{}", base_url, path);

    let part = reqwest::multipart::Part::bytes(file_data).file_name(file_name.clone());

    let form = reqwest::multipart::Form::new().part("file", part); // Python側が "file" キーを期待していると仮定

    // 認証トークンをヘッダーに付与
    let response = state
        .client
        .post(&url)
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

/// FastAPI サイドカーが listen しているポート番号をフロントエンドへ返すコマンド。
#[tauri::command]
fn get_api_port(port: State<'_, PortState>) -> u16 {
    port.port
}

// ファイル一覧取得用コマンド
#[tauri::command]
async fn get_files(directory_path: String) -> Result<GetFilesResponse, FileError> {
    get_files_internal(&directory_path)
}

/// エラーを返さない安全版 get_files。
/// パスが存在しない・空の場合はホームディレクトリ等にフォールバックする。
/// アプリ初期化時（設定に保存されたパスが消えた場合など）に使用する。
#[tauri::command]
fn get_files_safe(directory_path: String) -> GetFilesResponse {
    get_files_with_fallback(&directory_path)
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

    // 8000番から順に空きポートを探す
    let api_port = find_available_port(8000);

    // サイドカー（FastAPI）が環境変数を参照できるよう、現プロセスに設定する
    // Tauriがサイドカーを起動する際、子プロセスは親の環境変数を継承する
    // SAFETY: tauri::Builder::default() .plugin(tauri_plugin_shell::init()) を呼ぶ前に設定することで
    //         マルチスレッド下での競合を回避する
    // NOTE:   set_var は Rust 2024 edition で unsafe に分類された。
    //         マルチスレッド現境で set_var を呼ぶと getenv との竞合で未定義動作になるリスクがあるが、
    //         ここではシングルスレッド段階（Builder 起動前）に限定することで安全を確保している。
    unsafe {
        std::env::set_var("ECONOMICOM_API_AUTH_TOKEN", &auth_token);
        std::env::set_var("ECONOMICOM_API_PORT", api_port.to_string());
    }

    // クライアントの初期化（タイムアウト設定など）
    let client = Client::builder()
        .timeout(Duration::from_secs(300)) // 分析処理など時間がかかる場合を考慮
        .build()
        .expect("Failed to create HTTP client");

    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_opener::init())
        .manage(ClientState { client })
        .manage(AuthTokenState { token: auth_token }) // 生成したトークンをStateとして登録
        .manage(PortState { port: api_port })          // 確保したポート番号をStateとして登録
        .setup(|app| {
            let is_dev_mode = std::env::var("ECONOMICON_DEV_RUN")
                .map(|v| v.to_lowercase() == "true")
                .unwrap_or(false);

            if is_dev_mode {
                log::info!("Dev mode (ECONOMICON_DEV_RUN=true): skipping sidecar startup.");
            } else {
                // "resources/**/*" グロブでバンドルされたファイルは
                // resource_dir() から "resources/<相対パス>" でアクセスできる
                let resource_dir = app.path().resource_dir()?;
                let main_py = resource_dir
                    .join("resources")
                    .join("api")
                    .join("main.py");

                let auth_token = app.state::<AuthTokenState>().token.clone();
                let api_port   = app.state::<PortState>().port;

                let main_py_str = main_py.to_string_lossy().into_owned();
                let (mut rx, child) = app
                    .shell()
                    .sidecar("bin/python")?
                    .args([main_py_str])
                    .env("ECONOMICOM_API_AUTH_TOKEN", &auth_token)
                    .env("ECONOMICOM_API_PORT", api_port.to_string())
                    .env("ECONOMICON_DEV_RUN", "false")
                    .spawn()?;

                app.manage(SidecarState {
                    child: Mutex::new(Some(child)),
                });

                tauri::async_runtime::spawn(async move {
                    use tauri_plugin_shell::process::CommandEvent;
                    while let Some(event) = rx.recv().await {
                        match event {
                            CommandEvent::Stdout(line) => {
                                log::info!("[python] {}", String::from_utf8_lossy(&line));
                            }
                            CommandEvent::Stderr(line) => {
                                log::warn!("[python] {}", String::from_utf8_lossy(&line));
                            }
                            CommandEvent::Error(e) => {
                                log::error!("[python] error: {}", e);
                            }
                            CommandEvent::Terminated(status) => {
                                log::info!("[python] terminated: {:?}", status);
                                break;
                            }
                            _ => {}
                        }
                    }
                });
            }

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            proxy_request,
            fetch_binary,
            upload_file,
            get_files,
            get_files_safe,
            get_os_info,
            get_auth_token,
            get_api_port
        ])
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(|handle, event| {
            // アプリ終了時にサイドカープロセスを kill して孤立プロセスを防ぐ
            if let tauri::RunEvent::Exit = event {
                if let Some(state) = handle.try_state::<SidecarState>() {
                    if let Ok(mut guard) = state.child.lock() {
                        if let Some(child) = guard.take() {
                            let _ = child.kill();
                        }
                    }
                }
            }
        });
}
