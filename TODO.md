# TODO

## アプリ名

Economicon

## 画面

## **ファイルインポート画面**

- ドラッグ&ドロップでファイルをインポートする画面を作成（Rust側ではファイルパスのみでAPIに渡す）
- 現在のファイル選択画面も存続。ファイルインポート画面はタブでドラッグ&ドロップ画面とファイル選択画面を切り替えられるようにする
- ファイル選択画面は詳細を設定してインポートする画面をモーダルで作成

- **シミュレーションデータ**

- 各ボタンのカーソルをポインターにしたい。
- 設定値があまりにシンプルすぎる。せめて列名、データ形式、分布、パラメータがわかるようにしたい。
- 4列が見えない

**テーブル**

- テーブルにTanStack Table
  TanStack Virtual
  Apache Arrow
  Recharts plotly.js
  React-dropzone Uploadthing
- TanStack TableとTanStack Virtualを使ってページネーションではなく、スクロール方式に変更をするかを検討
- スクロール方式の場合はApache Arrowを使ってバイナリでテーブルデータを取得するとより高速になる？

**モード選択**

- 設定画面にてモード選択ができると良い（）

## REST API, Python API

**新機能・新API**

- ダミー変数を一気に作成するAPI（列の値をuniqueにして）
- 予測値・残差を計算するAPI
- 予測値・残差はシリアライズ化したモデル（statsmodels, linearmodels）をデータとして保存。計算にはそれを取り出して実施。ファイルの場所はanalysis_data_storeにuuid.pklのような感じで保持

**テスト**

- test_sort_empty_columns（空のソート列指定）のエラーメッセージのテストを行う
- from .django*compat import gettext as *を介さないように修正

## その他
