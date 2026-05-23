"""
推定結果フォーマット出力サービス

複数の分析結果を LaTeX / Markdown / 固定幅テキストに整形して返す。
"""

from typing import Any, ClassVar

from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _
from economicon.schemas.results import OutputResultRequest
from economicon.services.data.analysis_result_store import AnalysisResultStore
from economicon.utils import ProcessingError, ValidationError

# stat_in_parentheses → regression_output 内のキー名
_STAT_KEY_MAP: dict[str, str] = {
    "se": "standardError",
    "t": "tValue",
    "p": "pValue",
}

# モデル統計量: (regression_output キー, 表示ラベル)
# パネルデータ (FE/RE) は R2Within/Between/Overall を持ち,
# OLS/IV/Logit 等は R2 を持つ。別キーで区別する。
_MODEL_STAT_KEYS: list[tuple[str, str]] = [
    ("nObservations", "N"),
    ("R2", "R\u00b2"),
    ("R2Within", "R\u00b2 (within)"),
    ("R2Between", "R\u00b2 (between)"),
    ("R2Overall", "R\u00b2 (overall)"),
    ("adjustedR2", "Adj. R\u00b2"),
    ("fValue", "F"),
    ("fProbability", "F-prob."),
    ("AIC", "AIC"),
    ("BIC", "BIC"),
    ("logLikelihood", "Log-lik."),
    ("pseudoRSquared", "Pseudo R\u00b2"),
]


def _get_stars(
    p_value: float | None,
    stars: list[dict[str, Any]],
) -> str:
    """p 値に対応する有意性記号を返す（stars は閾値昇順ソート済み前提）。"""
    if p_value is None:
        return ""
    for cfg in stars:
        if p_value <= cfg["threshold"]:
            return cfg["symbol"]
    return ""


def _fmt_num(v: float | None, decimals: int = 4) -> str:
    """数値を小数点以下 decimals 桁に整形する（None は空文字列）。"""
    if v is None:
        return ""
    return f"{v:.{decimals}f}"


class _RegOutput:
    """一つの回帰結果（regression_output）のラッパー。"""

    def __init__(self, regression_output: dict[str, Any]) -> None:
        self.dep_var: str = regression_output["dependentVariable"]
        # variable → パラメータ辞書のマッピング
        self.params: dict[str, dict[str, Any]] = {
            p["variable"]: p for p in regression_output.get("parameters", [])
        }
        self.model_stats: dict[str, Any] = regression_output.get(
            "modelStatistics", {}
        )
        # IV モデルの第一段階 F 統計量
        # diagnostics.firstStage: {内生変数名: {fStatistic, pValue, ...}}
        _diagnostics = regression_output.get("diagnostics", {})
        _first_stage = _diagnostics.get("firstStage", {})
        self.first_stage_f: dict[str, float | None] = {
            var: info.get("fStatistic") for var, info in _first_stage.items()
        }


class _ResultFormatter:
    """
    複数の回帰結果を固定幅テキスト / Markdown / LaTeX に整形するクラス。

    Parameters
    ----------
    outputs:
        _RegOutput のリスト（モデル数分）
    stat_key:
        括弧内に表示する統計量の regression_output 内キー名。
        None の場合は括弧行を出力しない。
    stars:
        有意性記号設定のリスト（{"threshold", "symbol"} 辞書）。
        None の場合は記号を付与しない。
    variable_labels:
        変数名 → 表示ラベルの辞書。未設定は変数名そのまま。
    const_at_bottom:
        True の場合、定数項を変数リストの最後に配置する。
    """

    def __init__(
        self,
        outputs: list[_RegOutput],
        *,
        stat_key: str | None,
        stars: list[dict[str, Any]] | None,
        variable_labels: dict[str, str] | None,
        const_at_bottom: bool,
        variable_order: list[str] | None = None,
    ) -> None:
        self._outputs = outputs
        self._stat_key = stat_key
        # 昇順ソートを __init__ で一度だけ実施し
        # _get_stars での毎回ソートを排除
        self._stars = (
            sorted(stars, key=lambda s: s["threshold"])
            if stars is not None
            else None
        )
        self._labels = variable_labels or {}
        self._const_at_bottom = const_at_bottom
        self._variable_order = variable_order
        self._variables = self._build_variable_order()
        self._first_stage_vars = self._collect_first_stage_vars()

    def _resolve_variable_order(
        self, all_ordered: list[str], all_seen: set[str]
    ) -> list[str]:
        """variable_order 指定がある場合にその優先順序を適用する。"""
        if not self._variable_order:
            return list(all_ordered)
        placed: set[str] = set()
        ordered: list[str] = []
        for var in self._variable_order:
            if var in all_seen and var not in placed:
                placed.add(var)
                ordered.append(var)
        for var in all_ordered:
            if var not in placed:
                ordered.append(var)
        return ordered

    def _build_variable_order(self) -> list[str]:
        """
        全モデルの変数の和集合を順序付きで構築する。

        variable_order が指定された場合はその順序を優先し、
        未指定の変数はその後ろに登場順で追加する。
        定数項は const_at_bottom に応じて先頭または末尾に配置する。
        """
        all_seen: set[str] = set()
        all_ordered: list[str] = []
        const_found = False

        for output in self._outputs:
            for var in output.params:
                if var == "const":
                    const_found = True
                    continue
                if var not in all_seen:
                    all_seen.add(var)
                    all_ordered.append(var)

        ordered = self._resolve_variable_order(all_ordered, all_seen)

        if const_found:
            if self._const_at_bottom:
                ordered.append("const")
            else:
                ordered = ["const"] + ordered

        return ordered

    def _collect_first_stage_vars(self) -> list[str]:
        """
        全モデルを通じて登場する内生変数の和集合を収集する。

        IV モデルが含まれる場合のみ要素が存在する。
        第一段階 F 統計量の行を構築するために使用する。
        """
        seen: set[str] = set()
        ordered: list[str] = []
        for output in self._outputs:
            for var in output.first_stage_f:
                if var not in seen:
                    seen.add(var)
                    ordered.append(var)
        return ordered

    def _first_stage_stat_items(
        self,
    ) -> list[tuple[str, list[str]]]:
        """
        第一段階 F 統計量の（ラベル, モデルごとの値リスト）タプルを返す。

        IV モデルが含まれる場合のみ要素が存在する。
        第二段階の F 統計量（fValue）と区別するため
        ラベルを "1st-F: {内生変数名}" とする。
        """
        rows: list[tuple[str, list[str]]] = []
        for var in self._first_stage_vars:
            label = f"1st-F: {var}"
            vals: list[str] = []
            for o in self._outputs:
                v = o.first_stage_f.get(var)
                vals.append(_fmt_num(v, decimals=3) if v is not None else "")
            rows.append((label, vals))
        return rows

    def _collect_stat_rows(self) -> list[tuple[str, list[str]]]:
        """
        _MODEL_STAT_KEYS を走査し（ラベル, モデルごとの値リスト）タプルの
        リストを返す。全モデルで値が存在しない行はスキップする。
        第一段階 F 統計量行を末尾に結合する。
        to_text / to_markdown / to_latex の統計行生成で共通利用する。
        """
        rows: list[tuple[str, list[str]]] = []
        for stat_key, stat_label in _MODEL_STAT_KEYS:
            vals: list[str] = []
            has_any = False
            for o in self._outputs:
                v = o.model_stats.get(stat_key)
                if v is not None:
                    has_any = True
                    vals.append(
                        str(int(v))
                        if stat_key == "nObservations"
                        else _fmt_num(v)
                    )
                else:
                    vals.append("")
            if has_any:
                rows.append((stat_label, vals))
        rows.extend(self._first_stage_stat_items())
        return rows

    def _get_label(self, var: str) -> str:
        """変数ラベルを返す（未設定は変数名そのまま）。"""
        return self._labels.get(var, var)

    def _get_coef_paren(
        self,
        var: str,
        output: _RegOutput,
        *,
        latex: bool = False,
    ) -> tuple[str, str]:
        """
        係数セル文字列と括弧セル文字列のタプルを返す。

        Parameters
        ----------
        var:
            変数名
        output:
            対象モデルの _RegOutput
        latex:
            True の場合、有意性記号を LaTeX 上付き記法にする。

        Returns
        -------
        (coef_cell, paren_cell)
        """
        param = output.params.get(var)
        if param is None:
            return "", ""

        coef = param.get("coefficient")
        stars_str = ""
        if self._stars is not None:
            raw = _get_stars(param.get("pValue"), self._stars)
            if raw and latex:
                # LaTeX では上付き文字として表現
                stars_str = f"$^{{{raw}}}$"
            else:
                stars_str = raw

        coef_str = _fmt_num(coef) + stars_str

        paren_str = ""
        if self._stat_key is not None:
            stat_val = param.get(self._stat_key)
            if stat_val is not None:
                paren_str = f"({_fmt_num(stat_val)})"
            else:
                # 正則化回帰（LASSO/Ridge）など統計量が None の場合は
                # 括弧行を無言で欠落させず "---" プレースホルダーを表示する
                paren_str = "---"

        return coef_str, paren_str

    # ------------------------------------------------------------------
    # 出力形式別メソッド
    # ------------------------------------------------------------------

    def _text_header(self, label_w: int, col_w: int) -> list[str]:
        """固定幅テキスト用のヘッダー行リストを返す。"""
        n = len(self._outputs)
        total_w = label_w + col_w * n + 2
        sep = "=" * total_w
        mid = "-" * total_w
        row_num = " " * label_w
        for i in range(n):
            row_num += f"({i + 1})".center(col_w)
        row_dep = " " * label_w
        for o in self._outputs:
            row_dep += o.dep_var[: col_w - 2].center(col_w)
        return [sep, row_num, row_dep, mid]

    def _text_variable_rows(self, label_w: int, col_w: int) -> list[str]:
        """固定幅テキスト用の変数行リストを返す。"""
        lines: list[str] = []
        for var in self._variables:
            label = self._get_label(var)[: label_w - 2]
            coef_cells: list[str] = []
            paren_cells: list[str] = []
            for o in self._outputs:
                c, p = self._get_coef_paren(var, o)
                coef_cells.append(c)
                paren_cells.append(p)
            row = label.ljust(label_w)
            for c in coef_cells:
                row += c.center(col_w)
            lines.append(row)
            if any(paren_cells):
                row2 = " " * label_w
                for p in paren_cells:
                    row2 += p.center(col_w)
                lines.append(row2)
        return lines

    def _text_stat_rows(self, label_w: int, col_w: int) -> list[str]:
        """固定幅テキスト用のモデル統計行リストを返す。"""
        return [
            stat_label[: label_w - 2].ljust(label_w)
            + "".join(v.center(col_w) for v in vals)
            for stat_label, vals in self._collect_stat_rows()
        ]

    def to_text(self) -> str:
        """固定幅テキスト形式に整形する。"""
        label_w = 20
        col_w = 14
        total_w = label_w + col_w * len(self._outputs) + 2
        sep = "=" * total_w

        lines: list[str] = []
        lines.extend(self._text_header(label_w, col_w))
        lines.extend(self._text_variable_rows(label_w, col_w))
        lines.append(sep)
        lines.extend(self._text_stat_rows(label_w, col_w))
        lines.append(sep)

        return "\n".join(lines)

    def to_markdown(self) -> str:
        """Markdown テーブル形式に整形する。"""
        n = len(self._outputs)

        # ヘッダー
        num_headers = " | ".join(f"({i + 1})" for i in range(n))
        dep_headers = " | ".join(o.dep_var for o in self._outputs)
        sep_row = "|---|" + "---|" * n

        lines: list[str] = [
            f"| Variable | {num_headers} |",
            f"| | {dep_headers} |",
            sep_row,
        ]

        # 変数行
        for var in self._variables:
            label = self._get_label(var)
            coef_cells: list[str] = []
            paren_cells: list[str] = []
            for o in self._outputs:
                c, p = self._get_coef_paren(var, o)
                coef_cells.append(c)
                paren_cells.append(p)

            lines.append("| " + label + " | " + " | ".join(coef_cells) + " |")
            if any(paren_cells):
                lines.append("| | " + " | ".join(paren_cells) + " |")

        lines.append(sep_row)

        # モデル統計行
        for stat_label, vals in self._collect_stat_rows():
            lines.append("| " + stat_label + " | " + " | ".join(vals) + " |")

        return "\n".join(lines)

    def to_latex(self) -> str:
        """LaTeX tabular 形式に整形する。"""
        n = len(self._outputs)
        col_spec = "l" + "c" * n

        lines: list[str] = [
            r"\begin{table}[htbp]",
            r"\centering",
            r"\footnotesize",
            r"\begin{tabular}{" + col_spec + r"}",
            r"\hline\hline",
        ]

        # ヘッダー行1: モデル番号
        num_cells = " & ".join(f"({i + 1})" for i in range(n))
        lines.append(f" & {num_cells} \\\\")

        # ヘッダー行2: 被説明変数名
        dep_cells = " & ".join(o.dep_var for o in self._outputs)
        lines.append(f" & {dep_cells} \\\\")
        lines.append(r"\hline")

        # 変数行
        for var in self._variables:
            label = self._get_label(var)
            coef_cells: list[str] = []
            paren_cells: list[str] = []
            for o in self._outputs:
                c, p = self._get_coef_paren(var, o, latex=True)
                coef_cells.append(c)
                paren_cells.append(p)

            lines.append(label + " & " + " & ".join(coef_cells) + r" \\")
            if any(paren_cells):
                lines.append(" & " + " & ".join(paren_cells) + r" \\")

        lines.append(r"\hline")

        # モデル統計行
        for stat_label, vals in self._collect_stat_rows():
            lines.append(stat_label + " & " + " & ".join(vals) + r" \\")

        lines.extend(
            [
                r"\hline\hline",
                r"\end{tabular}",
                r"\end{table}",
            ]
        )

        return "\n".join(lines)


class OutputResult:
    """
    推定結果フォーマット出力サービス

    DataOperation Protocol 準拠。

    指定された analysis_result_id のリストから regression_output を取得し、
    指定されたフォーマット（text / markdown / latex）に整形して返す。
    """

    PARAM_NAMES: ClassVar[dict[str, str]] = {
        "result_ids": "resultIds",
    }

    def __init__(
        self,
        body: OutputResultRequest,
        result_store: AnalysisResultStore,
    ) -> None:
        self.result_ids = body.result_ids
        self.output_format = body.format
        # stat_in_parentheses="none" のとき stat_key=None
        self.stat_key = _STAT_KEY_MAP.get(body.stat_in_parentheses)
        # significance_stars=None のときはデフォルト設定を使用
        if body.significance_stars is not None:
            self.stars: list[dict[str, Any]] | None = [
                s.model_dump() for s in body.significance_stars
            ]
        else:
            self.stars = [
                {"threshold": 0.01, "symbol": "***"},
                {"threshold": 0.05, "symbol": "**"},
                {"threshold": 0.1, "symbol": "*"},
            ]
        self.variable_labels = body.variable_labels
        self.variable_order = body.variable_order
        self.const_at_bottom = body.const_at_bottom
        self.result_store = result_store
        # validate() でフェッチした結果をキャッシュし
        # execute() での二重フェッチを避ける
        self._fetched: list | None = None

    def validate(self) -> None:
        """
        バリデーション

        result_ids に含まれる全 ID がストアに存在することを確認する。
        存在する結果はキャッシュして execute() での二重フェッチを避ける。
        """
        missing: list[str] = []
        fetched = []
        for rid in self.result_ids:
            try:
                fetched.append(self.result_store.get_result(rid))
            except KeyError:
                missing.append(rid)

        if missing:
            details = ", ".join(missing)
            raise ValidationError(
                error_code=ErrorCode.DATA_NOT_FOUND,
                message=_(
                    "The following analysis results do not exist: %(details)s"
                )
                % {"details": details},
            )
        self._fetched = fetched

    def execute(self) -> dict[str, Any]:
        """
        指定されたフォーマットで推定結果を整形して返す。

        Returns
        -------
        dict
            {"content": str, "format": str}
        """
        try:
            # validate() でキャッシュ済みの結果を優先使用（二重フェッチ回避）
            results = self._fetched or [
                self.result_store.get_result(rid) for rid in self.result_ids
            ]
            outputs = [_RegOutput(r.result_data) for r in results]

            formatter = _ResultFormatter(
                outputs,
                stat_key=self.stat_key,
                stars=self.stars,
                variable_labels=self.variable_labels,
                const_at_bottom=self.const_at_bottom,
                variable_order=self.variable_order,
            )

            match self.output_format:
                case "latex":
                    content = formatter.to_latex()
                case "markdown":
                    content = formatter.to_markdown()
                case _:
                    content = formatter.to_text()

            return {"content": content, "format": self.output_format}

        except (ValidationError, ProcessingError) as e:
            raise e
        except Exception as e:
            raise ProcessingError(
                error_code=ErrorCode.OUTPUT_RESULT_ERROR,
                message=_(
                    "An unexpected error occurred during outputting results"
                ),
            ) from e
