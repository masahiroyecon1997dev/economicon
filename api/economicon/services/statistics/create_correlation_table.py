"""相関係数テーブル作成サービス"""

from typing import ClassVar, cast

import numpy as np
import polars as pl
from scipy import stats

from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _
from economicon.schemas import CreateCorrelationTableRequestBody
from economicon.schemas.enums import CorrelationMethod, MissingHandlingMethod
from economicon.services.data.tables_store import TablesStore
from economicon.utils import ProcessingError
from economicon.utils.validators import (
    validate_existence,
    validate_non_existence,
    validate_numeric_types,
)

# ペア相関計算に必要な最小有効データ数
_MIN_VALID_PAIRS: int = 2


class CreateCorrelationTable:
    """指定されたテーブルの列間の相関係数行列を計算し、
    新しいテーブルとして保存するAPIクラス。

    Pearson / Spearman / Kendall の3手法と、
    pairwise / listwise の2つの欠損値処理に対応する。
    """

    PARAM_NAMES: ClassVar[dict[str, str]] = {
        "table_name": "tableName",
        "column_names": "columnNames",
        "new_table_name": "newTableName",
    }

    def __init__(
        self,
        body: CreateCorrelationTableRequestBody,
        tables_store: TablesStore,
    ):
        self.tables_store = tables_store
        self.table_name = body.table_name
        self.column_names = body.column_names
        self.new_table_name = body.new_table_name
        self.method = body.method
        self.decimal_places = body.decimal_places
        self.lower_triangle_only = body.lower_triangle_only
        self.missing_handling = body.missing_handling

    def validate(self) -> None:
        table_name_list = self.tables_store.get_table_name_list()

        # 元テーブルの存在チェック
        validate_existence(
            value=self.table_name,
            valid_list=table_name_list,
            target=self.PARAM_NAMES["table_name"],
        )
        # 新テーブル名の重複なしチェック
        validate_non_existence(
            value=self.new_table_name,
            existing_list=table_name_list,
            target=self.PARAM_NAMES["new_table_name"],
        )
        # 各列の存在チェック
        column_name_list = self.tables_store.get_column_name_list(
            self.table_name
        )
        validate_existence(
            value=self.column_names,
            valid_list=column_name_list,
            target=self.PARAM_NAMES["column_names"],
        )
        # 各列が数値型であることをチェック
        schema = self.tables_store.get_schema(self.table_name)
        validate_numeric_types(
            schema=schema,
            columns=self.column_names,
            target=self.PARAM_NAMES["column_names"],
        )

    # ------------------------------------------------------------------
    # 内部計算メソッド
    # ------------------------------------------------------------------

    def _pair_corr(self, x: np.ndarray, y: np.ndarray) -> float | None:
        """2配列間の相関係数をペア単位欠損除去で計算する。

        NaN を含む要素はペア単位で除去してから計算する。
        有効データが2行未満の場合は None を返す。
        """
        mask = ~(np.isnan(x) | np.isnan(y))
        xc, yc = x[mask], y[mask]
        if len(xc) < _MIN_VALID_PAIRS:
            return None
        # 型注釈を先置きし、cast で scipy スタブの _T_co@tuple 型推論を回避する
        # （[0] インデックスも .statistic も古い scipy スタブでは型が不正確）
        r: float
        match self.method:
            case CorrelationMethod.PEARSON:
                r = cast(float, stats.pearsonr(xc, yc)[0])
            case CorrelationMethod.SPEARMAN:
                r = cast(float, stats.spearmanr(xc, yc)[0])
            case CorrelationMethod.KENDALL:
                r = cast(float, stats.kendalltau(xc, yc)[0])
            case _:  # 全 Enum を網羅した後の安全弁（到達しない）
                return None
        return r

    def _compute_matrix(
        self, arrays: list[np.ndarray]
    ) -> list[list[float | None]]:
        """列リストから n×n 相関係数行列（入れ子リスト）を計算する。

        listwise の場合は全選択列の欠損行を一括除去してから、
        pairwise の場合はペアごとに除去して計算する。
        いずれも実際の相関計算は _pair_corr に委ねる。
        """
        if self.missing_handling == MissingHandlingMethod.LISTWISE:
            # listwise: 選択列のどれかに欠損がある行をまとめて除去
            stacked = np.column_stack(arrays)
            valid_mask = ~np.any(np.isnan(stacked), axis=1)
            clean = stacked[valid_mask]
            n = len(arrays)
            work_arrays = [clean[:, i] for i in range(n)]
        else:
            # pairwise: _pair_corr がペアごとに欠損除去を行う
            work_arrays = arrays

        n = len(work_arrays)
        # listwise + pearson: BLAS 最適化された np.corrcoef で一括計算する。
        # spearman / kendall は np.corrcoef 非対応のため
        # _pair_corr ループを使う。
        if (
            self.missing_handling == MissingHandlingMethod.LISTWISE
            and self.method == CorrelationMethod.PEARSON
        ):
            corr_np = np.corrcoef(np.column_stack(work_arrays), rowvar=False)
            return [
                [cast(float, corr_np[i, j]) for j in range(n)]
                for i in range(n)
            ]

        # 相関行列は対称行列 (r_ij = r_ji) なので上三角のみ計算し
        # 反転コピーすることで計算量を O(n²) → O(n(n+1)/2) に削減する。
        # 対角成分 (r_ii) は定義上 1.0 であるため直接設定する。
        matrix: list[list[float | None]] = [[None] * n for _ in range(n)]
        for i in range(n):
            matrix[i][i] = 1.0  # 対角: 自己相関は常に 1.0
            for j in range(i + 1, n):
                val = self._pair_corr(work_arrays[i], work_arrays[j])
                matrix[i][j] = val
                matrix[j][i] = val  # 対称コピー
        return matrix

    # ------------------------------------------------------------------
    # メイン実行メソッド
    # ------------------------------------------------------------------

    def execute(self) -> dict:
        try:
            df = self.tables_store.get_table(self.table_name).table

            # 対象列を Float64 の numpy 配列として取得
            arrays: list[np.ndarray] = [
                df[col]
                .cast(pl.Float64)
                .to_numpy(allow_copy=True)
                .astype(np.float64)
                for col in self.column_names
            ]

            matrix = self._compute_matrix(arrays)
            n = len(self.column_names)

            # 丸め処理 & 上三角ヌル化（lower_triangle_only）
            for i in range(n):
                for j in range(n):
                    if self.lower_triangle_only and i < j:
                        # 上三角部分を null に置換（重複情報を排除）
                        matrix[i][j] = None
                    elif (val := matrix[i][j]) is not None:
                        # walrus 演算子でローカル変数に束縛し Pylance の
                        # コンテナ要素ナローイング制限を回避する
                        matrix[i][j] = round(val, self.decimal_places)

            # Polars DataFrame を構築
            # 1列目: variable_name (String) = 選択された変数名
            # 2列目以降: 各変数名の列 (Float64) = 相関係数値
            series_list: list[pl.Series] = [
                pl.Series(
                    "variable_name",
                    self.column_names,
                    dtype=pl.String,
                )
            ] + [
                pl.Series(
                    col,
                    # j 列目は matrix の各行の j 番目の値（縦に並べる）
                    [matrix[i][j] for i in range(n)],
                    dtype=pl.Float64,
                )
                for j, col in enumerate(self.column_names)
            ]

            result_df = pl.DataFrame(series_list)
            self.tables_store.store_table(self.new_table_name, result_df)
            return {"tableName": self.new_table_name}

        except ProcessingError:
            raise
        except Exception as e:
            message = _(
                "An unexpected error occurred during "
                "correlation table creation"
            )
            raise ProcessingError(
                error_code=ErrorCode.CORRELATION_TABLE_CREATION_ERROR,
                message=message,
                detail=str(e),
            ) from e
