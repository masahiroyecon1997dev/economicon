import ast
import re
from typing import Any

import polars as pl

from economicon.i18n.translation import gettext as _

from .config import OPERATOR_MAP


def _evaluate_node(node: Any) -> Any:
    """ASTノードを再帰的にPolars Expressionに変換するヘルパー関数"""

    # 数値（1.1, 100など）
    if isinstance(node, ast.Constant):
        return pl.lit(node.value)

    # 変数（col_... 形式を pl.col に戻す）
    if isinstance(node, ast.Name):
        if node.id.startswith("col_"):
            return pl.col(node.id[4:])
        raise ValueError(_("Invalid variable reference: {}").format(node.id))

    # 二項演算（+, -, *, / 等）
    if isinstance(node, ast.BinOp):
        left = _evaluate_node(node.left)
        right = _evaluate_node(node.right)
        op_type = type(node.op)
        if op_type in OPERATOR_MAP:
            return OPERATOR_MAP[op_type](left, right)
        raise ValueError(
            _("Unsupported operator: {}").format(op_type.__name__)
        )

    # 単項演算（負数表現など）
    if isinstance(node, ast.UnaryOp):
        operand = _evaluate_node(node.operand)
        op_type = type(node.op)
        if op_type in OPERATOR_MAP:
            return OPERATOR_MAP[op_type](operand)
        raise ValueError(
            _("Unsupported unary operator: {}").format(op_type.__name__)
        )

    raise ValueError(_("Unsupported syntax: {}").format(type(node).__name__))


def parse_formula_to_expr(formula: str) -> pl.Expr:
    """
    {column} 形式の文字列式を安全に Polars Expr に変換する純粋関数
    """
    # 1. 前処理: {col} を Python の変数名として有効な col_... に置換
    # これにより、ast.parse が数式として正しく認識できる
    normalized = re.sub(r"\{(\w+)\}", r"col_\1", formula)

    try:
        # 2. 抽象構文木(AST)の生成
        tree = ast.parse(normalized, mode="eval")

        # 3. 再帰的評価
        return _evaluate_node(tree.body)
    except SyntaxError as e:
        raise ValueError(_("Invalid formula syntax: {}").format(e))
