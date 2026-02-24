# API クライアント型生成（OpenAPI & Orval）の自動化について

このプロジェクトでは、バックエンド（FastAPI）のルーティング情報から `openapi.json` を出力し、それを元にフロントエンド（React/Tauri）用の API クライアントや型定義（TypeScript / Zod スキーマ）を自動生成する仕組みを導入しています。

## 概要と仕組み

1. **OpenAPI JSON 生成**
   FastAPI のインスタンスから API のルーティング情報やスキーマを抽出し、JSON ファイル (`app/openapi.json`) として出力します。これは Python スクリプト (`api/gen_openapi.py`) によって行われます。
2. **TypeScript & Zod の生成 (Orval)**
   出力された `openapi.json` を **Orval** が読み込み、事前に設定された `orval.config.ts` に基づいて React 側で利用できる Axios のエンドポイント関数群と Zod のバリデーションスキーマを生成します。

## 実行するタイミング

バックエンドの API コード（エンドポイント、リクエスト・レスポンスの Pydantic モデルなど）を追加・変更し、**フロントエンド側でもその変更された型を利用したいタイミング**で実行してください。

> **Note:**
> ファイル保存時に自動実行する（watchモード）ことも可能ですが、PCリソースの枯渇や「コーディング中でエラーが起きている状態」のスキーマがエクスポートされてフロントエンドの型が一斉に壊れるリスクを防ぐため、**開発者の任意のタイミングで手動トリガーする**（ワンタッチ化する）方針を採用しています。

## API クライアントの生成方法

APIクライアントの生成は、以下のいずれかの方法で簡単に実行できます（仮想環境のアクティベートなどを事前に行う必要はありません）。

### 方法 A: VS Code のタスクを使用する（推奨）

VS Code のタスク機能を利用してワンクリック（またはショートカットキー）で再生成できます。

1. コマンドパレット (`Ctrl+Shift+P` または `Cmd+Shift+P`) を開き、`Tasks: Run Task`（タスクの実行）を選択します。
2. **`Generate API Client (OpenAPI & Types)`** というタスクを選択します。
3. ターミナルが開き、バックエンドの OpenAPI 生成とフロントエンドの型生成が一気に走ります。

> *Tips:* よく使う場合は、キーボードショートカットの設定 (`keybindings.json`) で特定のキーに割り当てておくとさらに便利です。

### 方法 B: ターミナルから CLI コマンドを実行する

手動でコマンドを実行する場合は、`app` ディレクトリで以下のコマンドを叩きます。

```powershell
cd app
pnpm gen:all
```

#### コマンドの裏側の挙動
`pnpm gen:all` は `package.json` に以下のように定義されています：
```json
"gen:all": "cd ../api && .\\.venv\\Scripts\\python.exe gen_openapi.py && cd ../app && pnpm gen:api"
```
*   `.\.venv\Scripts\python.exe gen_openapi.py`: ターミナルが Python の仮想環境に入っていなくても、確実にプロジェクトの仮想環境の Python インタープリタを実行して JSON を出力します。
*   `pnpm gen:api`: `orval` を呼び出し、TypeScript と Zod のコードを再生成します。
