import ast
import re
from typing import Any

import polars as pl

from economicon.i18n.translation import gettext as _
from economicon.utils.algorithms.config import (
    OP_DISPLAY,
    OPERATOR_MAP,
    SUPPORTED_FUNCTIONS,
)


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


def _op_symbol(op: ast.operator | ast.unaryop) -> str:
    """演算子のシンボル文字列を返す（エラーメッセージ用）"""
    return OP_DISPLAY.get(type(op), type(op).__name__)


def _validate_call_node(node: ast.Call) -> None:
    """Callノードを検証するヘルパー。_validate_ast_node の複雑度削減に使用。"""
    func_name = getattr(node.func, "id", None)
    if func_name is not None and func_name in SUPPORTED_FUNCTIONS:
        if node.keywords:
            raise ValueError(
                _("Unsupported syntax in calculation expression: {}").format(
                    _("keyword arguments in function calls")
                )
            )
        for arg in node.args:
            _validate_ast_node(arg)
        return
    display_name = func_name or ast.unparse(node.func)
    raise ValueError(
        _("Unsupported syntax in calculation expression: {}").format(
            _("function call '{}'").format(display_name)
        )
    )


def _validate_ast_node(node: ast.AST) -> None:
    """ASTノードを再帰的に検証する（純粋バリデーション専用）。

    OPERATOR_MAP と SUPPORTED_FUNCTIONS を参照するため、
    それらに新しいエントリを追加するだけで自動的に許可対象が拡張される。

    Raises:
        ValueError: 許可されていない構文が含まれている場合
    """
    # 数値リテラル（整数・浮動小数点）
    if isinstance(node, ast.Constant):
        return

    # 列参照（正規化後は col_<名前> の Name ノードになる）
    if isinstance(node, ast.Name):
        if not node.id.startswith("col_"):
            raise ValueError(
                _("Unsupported syntax in calculation expression: {}").format(
                    _("invalid variable reference")
                )
            )
        return

    # 二項演算 — OPERATOR_MAP で許可された演算子のみ
    if isinstance(node, ast.BinOp):
        if type(node.op) not in OPERATOR_MAP:
            raise ValueError(
                _("Unsupported syntax in calculation expression: {}").format(
                    _("operator '{}'").format(_op_symbol(node.op))
                )
            )
        _validate_ast_node(node.left)
        _validate_ast_node(node.right)
        return

    # 単項演算 — OPERATOR_MAP で許可された演算子のみ
    if isinstance(node, ast.UnaryOp):
        if type(node.op) not in OPERATOR_MAP:
            raise ValueError(
                _("Unsupported syntax in calculation expression: {}").format(
                    _("operator '{}'").format(_op_symbol(node.op))
                )
            )
        _validate_ast_node(node.operand)
        return

    # 関数呼び出し — SUPPORTED_FUNCTIONS で許可された関数のみ
    if isinstance(node, ast.Call):
        _validate_call_node(node)
        return

    # 属性アクセス（例: col.method）
    if isinstance(node, ast.Attribute):
        raise ValueError(
            _("Unsupported syntax in calculation expression: {}").format(
                _("attribute access")
            )
        )

    # その他の未サポートノード
    raise ValueError(
        _("Unsupported syntax in calculation expression: {}").format(
            _("'{}' syntax").format(type(node).__name__)
        )
    )


def validate_formula_syntax(formula: str) -> None:
    """{col} 形式の計算式を構文検証する。

    1. 正規化（{col} → col_X 置換）してから AST パースを試みる。
       失敗時は SyntaxError メッセージを含む ValueError を送出。
    2. AST ノードを再帰的に走査し、許可されていない構文を
       検出した場合も ValueError を送出。

    Args:
        formula: ユーザー入力の計算式（"{col_name}" 形式）

    Raises:
        ValueError: 構文エラーまたは未サポートの操作が含まれる場合
    """
    normalized = re.sub(r"\{(\w+)\}", r"col_\1", formula)

    try:
        tree = ast.parse(normalized, mode="eval")
    except SyntaxError as e:
        # SyntaxError.msg は Python 3.10+ で安定して利用可能
        msg = getattr(e, "msg", str(e))
        raise ValueError(
            _("Syntax error in calculation expression: {}").format(msg)
        ) from e

    _validate_ast_node(tree.body)


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
        raise ValueError(_("Invalid formula syntax: {}").format(e)) from e
