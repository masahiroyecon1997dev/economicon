import ast
import operator

# 許可する演算子の定義
# 将来的に関数(log, sum等)を増やす際もここを編集するだけで済む
OPERATOR_MAP = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}

# 許可する関数がある場合はここに追加（例: {"abs": pl.col().abs} 等）
SUPPORTED_FUNCTIONS = {}
