; ==============================================================================
;  installer.iss  -  Economicon Windows インストーラー (Inno Setup 6.x)
;  用途: Tauri ビルド済みバイナリ + Embedded Python 環境を
;        1 本の exe インストーラーにまとめる雛形テンプレート。
;
;  前提:
;    1. Inno Setup 6.x がインストール済みであること
;       https://jrsoftware.org/isdl.php
;    2. build.ps1 によって下記が生成済みであること
;          app\src-tauri\target\release\economicon.exe
;          app\src-tauri\resources\python_env\**
;          api\main.py, api\economicon\**
;    3. Inno Setup は "release\" フォルダで実行する想定なので
;       パスはリポジトリルートからの相対パスで記述しています。
;
;  ビルドコマンド（release\ フォルダ内で実行）:
;       iscc installer.iss
; ==============================================================================


#define MyAppName    "Economicon"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "Your Name / Organization"
#define MyAppURL     "https://github.com/MasahiroYamada1997-1/economicon"
#define MyAppExeName "economicon.exe"

; ── ソースルート（このファイルのある場所の 1つ上 = リポジトリルート）─────────
; release\ に .iss を置く想定なので .. でリポジトリルートを指す
#define SrcRoot ".."

[Setup]
; ── アプリ識別子 ──────────────────────────────────────────────────────────────
; 変更する場合は GUID to ツールで新しい値を生成してください
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
AppPublisher={#MyAppPublisher}

; ── インストール先 ─────────────────────────────────────────────────────────────
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=no
DisableProgramGroupPage=yes

; ── インストーラー出力先 ────────────────────────────────────────────────────────
OutputDir={#SrcRoot}\release\installer_output
OutputBaseFilename=economicon-{#MyAppVersion}-setup
SetupIconFile={#SrcRoot}\app\src-tauri\icons\icon.ico

; ── 圧縮 ──────────────────────────────────────────────────────────────────────
Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes

; ── 必要な Windows バージョン（Windows 10 以降を対象）──────────────────────────
MinVersion=10.0.19041

; ── アーキテクチャ ─────────────────────────────────────────────────────────────
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

; ── 管理者権限不要でインストール可能にする場合（任意）─────────────────────────
; PrivilegesRequired=lowest
; PrivilegesRequiredOverridesAllowed=dialog
PrivilegesRequired=admin

; ── アンインストール設定 ────────────────────────────────────────────────────────
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName} {#MyAppVersion}

; ── インストール中のウィザード設定 ────────────────────────────────────────────
WizardStyle=modern
WizardSizePercent=120


[Languages]
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"
Name: "english";  MessagesFile: "compiler:Default.isl"


[Tasks]
; デスクトップショートカット（ユーザーが選択可能）
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; \
    GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked


[Files]
; ── 1. Tauri ビルド済みメインバイナリ ─────────────────────────────────────────
; Tauri v2 は単一の EXE を生成する。WebView2 は OS 内蔵のものを使用。
Source: "{#SrcRoot}\app\src-tauri\target\release\{#MyAppExeName}"; \
    DestDir: "{app}"; Flags: ignoreversion

; ── 2. Embedded Python 環境（FastAPI バックエンド実行用）────────────────────────
; build.ps1 によって app\src-tauri\resources\python_env\ に展開済みのもの。
; インストール先の {app}\python_env\ に同じ構造でコピーする。
; NOTE: Tauri の bundle.resources 経由でバイナリに内包する場合はこのセクションは不要になる。
Source: "{#SrcRoot}\app\src-tauri\resources\python_env\*"; \
    DestDir: "{app}\python_env"; \
    Flags: ignoreversion recursesubdirs createallsubdirs

; ── 3. FastAPI バックエンドコード ────────────────────────────────────────────
; Tauri の bundle.resources 経由でバイナリ内に含める場合はこのセクションも不要。
; 単体インストーラーとして Python ソースも配布する場合は有効にする。
; Source: "{#SrcRoot}\api\main.py"; DestDir: "{app}\api"; Flags: ignoreversion
; Source: "{#SrcRoot}\api\economicon\*"; \
;     DestDir: "{app}\api\economicon"; \
;     Flags: ignoreversion recursesubdirs createallsubdirs

; ── 4. ライセンスファイル（存在する場合）───────────────────────────────────────
; Source: "{#SrcRoot}\LICENSE"; DestDir: "{app}"; Flags: ignoreversion


[Icons]
; スタートメニュー
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; \
    Filename: "{uninstallexe}"

; デスクトップ（Task で選択した場合のみ）
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; \
    Tasks: desktopicon


[Run]
; インストール完了後にアプリを起動するオプション
Filename: "{app}\{#MyAppExeName}"; \
    Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; \
    Flags: nowait postinstall skipifsilent


[UninstallRun]
; アンインストール前にプロセスを終了する（タスクキルが必要な場合）
Filename: "taskkill.exe"; Parameters: "/F /IM {#MyAppExeName}"; Flags: skipifdoesntexist runhidden


[Code]
// ── インストール前の WebView2 Runtim チェック（任意）─────────────────────────
// Tauri v2 は OS 組み込みの WebView2 を使用するため、
// 古い Windows では Runtime がインストールされていないことがある。
// 下記のコードはその場合に警告を表示するサンプルです（必要に応じて有効化）。
(*
function IsWebView2Installed(): Boolean;
var
    Version: String;
begin
    Result := RegQueryStringValue(
        HKLM,
        'SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}',
        'pv',
        Version
    ) and (Version <> '0.0.0.0');
    if not Result then
        Result := RegQueryStringValue(
            HKCU,
            'Software\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}',
            'pv',
            Version
        ) and (Version <> '0.0.0.0');
end;

function InitializeSetup(): Boolean;
begin
    Result := True;
    if not IsWebView2Installed() then begin
        MsgBox(
            'Microsoft Edge WebView2 Runtime が検出されませんでした。' + #13#10 +
            'インストール後に下記からランタイムをインストールしてください:' + #13#10 +
            'https://developer.microsoft.com/ja-jp/microsoft-edge/webview2/',
            mbInformation,
            MB_OK
        );
    end;
end;
*)
