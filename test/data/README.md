# テストデータ (Tests Data Fixtures)

このディレクトリには、`Economicon` の推定エンジンおよびデータ処理ロジックの正確性を検証するためのテストデータが格納されています。

## データ形式

- **.parquet**: 本番の自動テスト用。型情報（Categorical, Float64等）を厳密に保持するために使用。
- **.csv**: デバッグ・目視確認用。Git上での差分確認に使用。

## 採用データセット一覧とテストの目的

| パッケージ     | データ名     | 主なテスト項目         | 選定理由                                                                     |
| :------------- | :----------- | :--------------------- | :--------------------------------------------------------------------------- |
| **wooldridge** | `wage1`      | 基本OLS, 対数変換      | 定番の賃金方程式。対数モデルの計算精度検証。                                 |
| **wooldridge** | `hprice1`    | 重回帰, スケーリング   | 住宅価格データ。変数の単位が多様なため、スケーリング処理のロジックをテスト。 |
| **wooldridge** | `vote1`      | 決定係数 ($R^2$), 相関 | 選挙費用と得票率。高い相関を持つデータでの統計量計算の安定性確認。           |
| **AER**        | `journals`   | WLS / FGLS             | 雑誌価格。不均一分散が顕著なため、重み付け最小二乗法の計算精度を検証。       |
| **AER**        | `fatalities` | パネルデータ, HAC      | 交通事故死者数。時系列＋横断面の処理および堅牢な標準誤差の検証。             |
| **datasets**   | `mtcars`     | 行列演算の正確性       | 全変数数値かつ欠損値なし。逆行列や行列積のピュアな数値精度のテスト用。       |
| **penguins**   | `penguins`   | 欠損値, ダミー変数     | カテゴリ変数と欠損値（NA）を含むため、前処理ロジックの堅牢性を検証。         |

## データの生成・更新方法

データは Python スクリプト `scripts/generate_test_data.py` によって自動生成されます。手動での変更は避け、変更が必要な場合はスクリプトを更新してください。

```bash
# 生成コマンド例
python scripts/generate_test_data.py
```

## ライセンス・出典

これらのデータセットは、教育および研究目的で公開されている以下のパッケージから取得しています。

- [wooldridge](https://pypi.org/project/wooldridge/): MIT License
- [statsmodels (R datasets)](https://www.statsmodels.org/): BSD 3nd-Clause License
- [palmerpenguins](https://github.com/mcnulty/palmerpenguins): CC0 License (Public Domain)
