import ast
import operator
from collections.abc import Callable
from typing import Any

# 許可する演算子の定義
# 将来的に関数(log, sum等)を増やす際もここを編集するだけで済む
OPERATOR_MAP: dict[type, Callable[..., Any]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}

# 許可する演算子の表示シンボル（エラーメッセージ用）
# OPERATOR_MAP に含まれない演算子の表示に使用する
OP_DISPLAY: dict[type, str] = {
    ast.FloorDiv: "//",
    ast.Mod: "%",
    ast.MatMult: "@",
    ast.BitAnd: "&",
    ast.BitOr: "|",
    ast.BitXor: "^",
    ast.LShift: "<<",
    ast.RShift: ">>",
    ast.UAdd: "+",
    ast.Invert: "~",
    ast.Not: "not",
}

# 許可する関数がある場合はここに追加（例: {"abs": pl.col().abs} 等）
# キー: 関数名（str）, 値: Polars Expr に変換するファクトリ関数
SUPPORTED_FUNCTIONS: dict[str, Callable[..., Any]] = {}
