"""分析結果フォーマット出力サービス。"""

from dataclasses import dataclass
from numbers import Integral, Real
from typing import Any, ClassVar, Protocol, cast

from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _
from economicon.schemas.results import (
    ConfidenceIntervalOutputOptions,
    DescriptiveStatisticsOutputOptions,
    OutputResultRequest,
    RegressionOutputOptions,
    StatisticalTestOutputOptions,
)
from economicon.services.data.analysis_result import AnalysisResult
from economicon.services.data.analysis_result_store import AnalysisResultStore
from economicon.utils import ProcessingError, ValidationError

_STAT_KEY_MAP: dict[str, str] = {
    "se": "standardError",
    "t": "tValue",
    "p": "pValue",
}

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
    """p 値に対応する有意性記号を返す。"""
    if p_value is None:
        return ""
    for cfg in stars:
        if p_value <= cfg["threshold"]:
            return cfg["symbol"]
    return ""


def _fmt_num(v: float | None, decimals: int = 4) -> str:
    """数値を decimals 桁で整形する。"""
    if v is None:
        return ""
    return f"{v:.{decimals}f}"


def _format_cell(value: Any) -> str:
    """表セル用に値を文字列化する。"""
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, Integral):
        return str(int(value))
    if isinstance(value, Real):
        return _fmt_num(float(value))
    return str(value)


def _apply_order(
    seen_items: list[str],
    preferred: list[str] | None,
) -> list[str]:
    """優先順を適用し、未指定項目は元の登場順で後ろに付ける。"""
    if not preferred:
        return list(seen_items)

    placed: set[str] = set()
    ordered: list[str] = []
    seen_set = set(seen_items)

    for item in preferred:
        if item in seen_set and item not in placed:
            placed.add(item)
            ordered.append(item)

    for item in seen_items:
        if item not in placed:
            ordered.append(item)

    return ordered


class _OutputFormatter(Protocol):
    def to_text(self) -> str: ...

    def to_markdown(self) -> str: ...

    def to_latex(self) -> str: ...


@dataclass(slots=True)
class _TableData:
    headers: list[str]
    rows: list[list[str]]


class _TableFormatter:
    """一般的な表を text / markdown / latex に描画する。"""

    def __init__(self, table: _TableData) -> None:
        self._table = table

    def to_text(self) -> str:
        widths = [len(h) for h in self._table.headers]
        for row in self._table.rows:
            for index, cell in enumerate(row):
                widths[index] = max(widths[index], len(cell))

        def _row_to_text(row: list[str]) -> str:
            return " | ".join(
                cell.ljust(widths[index]) for index, cell in enumerate(row)
            )

        separator = "-+-".join("-" * width for width in widths)
        lines = [_row_to_text(self._table.headers), separator]
        lines.extend(_row_to_text(row) for row in self._table.rows)
        return "\n".join(lines)

    def to_markdown(self) -> str:
        header = "| " + " | ".join(self._table.headers) + " |"
        separator = (
            "| " + " | ".join("---" for _ in self._table.headers) + " |"
        )
        rows = ["| " + " | ".join(row) + " |" for row in self._table.rows]
        return "\n".join([header, separator, *rows])

    def to_latex(self) -> str:
        col_spec = "l" + "c" * (len(self._table.headers) - 1)
        lines = [
            r"\begin{table}[htbp]",
            r"\centering",
            r"\footnotesize",
            r"\begin{tabular}{" + col_spec + r"}",
            r"\hline\hline",
            " & ".join(self._table.headers) + r" \\",
            r"\hline",
        ]
        lines.extend(" & ".join(row) + r" \\" for row in self._table.rows)
        lines.extend(
            [
                r"\hline\hline",
                r"\end{tabular}",
                r"\end{table}",
            ]
        )
        return "\n".join(lines)


class _RegOutput:
    """一つの回帰結果（regression_output）のラッパー。"""

    def __init__(self, regression_output: dict[str, Any]) -> None:
        self.dep_var: str = regression_output["dependentVariable"]
        self.params: dict[str, dict[str, Any]] = {
            p["variable"]: p for p in regression_output.get("parameters", [])
        }
        self.model_stats: dict[str, Any] = regression_output.get(
            "modelStatistics", {}
        )
        diagnostics = regression_output.get("diagnostics", {})
        first_stage = diagnostics.get("firstStage", {})
        self.first_stage_f: dict[str, float | None] = {
            var: info.get("fStatistic") for var, info in first_stage.items()
        }


class _RegressionFormatter:
    """複数の回帰結果を text / markdown / latex に整形する。"""

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
        seen: set[str] = set()
        ordered: list[str] = []
        for output in self._outputs:
            for var in output.first_stage_f:
                if var not in seen:
                    seen.add(var)
                    ordered.append(var)
        return ordered

    def _first_stage_stat_items(self) -> list[tuple[str, list[str]]]:
        rows: list[tuple[str, list[str]]] = []
        for var in self._first_stage_vars:
            label = f"1st-F: {var}"
            vals: list[str] = []
            for output in self._outputs:
                value = output.first_stage_f.get(var)
                vals.append(
                    _fmt_num(value, decimals=3) if value is not None else ""
                )
            rows.append((label, vals))
        return rows

    def _collect_stat_rows(self) -> list[tuple[str, list[str]]]:
        rows: list[tuple[str, list[str]]] = []
        for stat_key, stat_label in _MODEL_STAT_KEYS:
            vals: list[str] = []
            has_any = False
            for output in self._outputs:
                value = output.model_stats.get(stat_key)
                if value is not None:
                    has_any = True
                    vals.append(
                        str(int(value))
                        if stat_key == "nObservations"
                        else _fmt_num(value)
                    )
                else:
                    vals.append("")
            if has_any:
                rows.append((stat_label, vals))
        rows.extend(self._first_stage_stat_items())
        return rows

    def _get_label(self, var: str) -> str:
        return self._labels.get(var, var)

    def _get_coef_paren(
        self,
        var: str,
        output: _RegOutput,
        *,
        latex: bool = False,
    ) -> tuple[str, str]:
        param = output.params.get(var)
        if param is None:
            return "", ""

        coef = param.get("coefficient")
        stars_str = ""
        if self._stars is not None:
            raw = _get_stars(param.get("pValue"), self._stars)
            if raw and latex:
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
                paren_str = "---"

        return coef_str, paren_str

    def _text_header(self, label_w: int, col_w: int) -> list[str]:
        n = len(self._outputs)
        total_w = label_w + col_w * n + 2
        sep = "=" * total_w
        mid = "-" * total_w
        row_num = " " * label_w
        for index in range(n):
            row_num += f"({index + 1})".center(col_w)
        row_dep = " " * label_w
        for output in self._outputs:
            row_dep += output.dep_var[: col_w - 2].center(col_w)
        return [sep, row_num, row_dep, mid]

    def _text_variable_rows(self, label_w: int, col_w: int) -> list[str]:
        lines: list[str] = []
        for var in self._variables:
            label = self._get_label(var)[: label_w - 2]
            coef_cells: list[str] = []
            paren_cells: list[str] = []
            for output in self._outputs:
                coef, paren = self._get_coef_paren(var, output)
                coef_cells.append(coef)
                paren_cells.append(paren)
            row = label.ljust(label_w)
            for coef in coef_cells:
                row += coef.center(col_w)
            lines.append(row)
            if any(paren_cells):
                row2 = " " * label_w
                for paren in paren_cells:
                    row2 += paren.center(col_w)
                lines.append(row2)
        return lines

    def _text_stat_rows(self, label_w: int, col_w: int) -> list[str]:
        return [
            stat_label[: label_w - 2].ljust(label_w)
            + "".join(value.center(col_w) for value in vals)
            for stat_label, vals in self._collect_stat_rows()
        ]

    def to_text(self) -> str:
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
        n = len(self._outputs)
        num_headers = " | ".join(f"({index + 1})" for index in range(n))
        dep_headers = " | ".join(output.dep_var for output in self._outputs)
        sep_row = "|---|" + "---|" * n

        lines: list[str] = [
            f"| Variable | {num_headers} |",
            f"| | {dep_headers} |",
            sep_row,
        ]

        for var in self._variables:
            label = self._get_label(var)
            coef_cells: list[str] = []
            paren_cells: list[str] = []
            for output in self._outputs:
                coef, paren = self._get_coef_paren(var, output)
                coef_cells.append(coef)
                paren_cells.append(paren)

            lines.append("| " + label + " | " + " | ".join(coef_cells) + " |")
            if any(paren_cells):
                lines.append("| | " + " | ".join(paren_cells) + " |")

        lines.append(sep_row)

        for stat_label, vals in self._collect_stat_rows():
            lines.append("| " + stat_label + " | " + " | ".join(vals) + " |")

        return "\n".join(lines)

    def to_latex(self) -> str:
        n = len(self._outputs)
        col_spec = "l" + "c" * n

        lines: list[str] = [
            r"\begin{table}[htbp]",
            r"\centering",
            r"\footnotesize",
            r"\begin{tabular}{" + col_spec + r"}",
            r"\hline\hline",
        ]

        num_cells = " & ".join(f"({index + 1})" for index in range(n))
        lines.append(f" & {num_cells} \\")

        dep_cells = " & ".join(output.dep_var for output in self._outputs)
        lines.append(f" & {dep_cells} \\")
        lines.append(r"\hline")

        for var in self._variables:
            label = self._get_label(var)
            coef_cells: list[str] = []
            paren_cells: list[str] = []
            for output in self._outputs:
                coef, paren = self._get_coef_paren(var, output, latex=True)
                coef_cells.append(coef)
                paren_cells.append(paren)

            lines.append(label + " & " + " & ".join(coef_cells) + r" \\")
            if any(paren_cells):
                lines.append(" & " + " & ".join(paren_cells) + r" \\")

        lines.append(r"\hline")

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


def _collect_descriptive_stat_keys(
    results: list[AnalysisResult],
) -> list[str]:
    all_stats: list[str] = []
    seen_stats: set[str] = set()
    for result in results:
        for stat_values in result.result_data["statistics"].values():
            for stat in stat_values:
                if stat not in seen_stats:
                    seen_stats.add(stat)
                    all_stats.append(stat)

    return all_stats


def _build_descriptive_headers(
    ordered_stats: list[str],
    options: DescriptiveStatisticsOutputOptions,
) -> list[str]:
    statistic_labels = options.statistic_labels or {}
    headers: list[str] = []
    if options.include_result_name:
        headers.append("Result")
    if options.include_table_name:
        headers.append("Table")
    headers.append("Variable")
    headers.extend(statistic_labels.get(stat, stat) for stat in ordered_stats)
    return headers


def _build_descriptive_rows(
    results: list[AnalysisResult],
    ordered_stats: list[str],
    options: DescriptiveStatisticsOutputOptions,
) -> list[list[str]]:
    variable_labels = options.variable_labels or {}
    rows: list[list[str]] = []

    for result in results:
        stats_map: dict[str, dict[str, Any]] = result.result_data["statistics"]
        ordered_vars = _apply_order(
            list(stats_map.keys()),
            options.variable_order,
        )
        for var in ordered_vars:
            row: list[str] = []
            if options.include_result_name:
                row.append(result.name)
            if options.include_table_name:
                row.append(result.table_name)
            row.append(variable_labels.get(var, var))
            row.extend(
                _format_cell(stats_map[var].get(stat))
                for stat in ordered_stats
            )
            rows.append(row)

    return rows


def _build_descriptive_table(
    results: list[AnalysisResult],
    options: DescriptiveStatisticsOutputOptions,
) -> _TableData:
    all_stats = _collect_descriptive_stat_keys(results)

    ordered_stats = _apply_order(all_stats, options.statistic_order)
    headers = _build_descriptive_headers(ordered_stats, options)
    rows = _build_descriptive_rows(results, ordered_stats, options)
    return _TableData(headers=headers, rows=rows)


def _build_confidence_interval_table(
    results: list[AnalysisResult],
    options: ConfidenceIntervalOutputOptions,
) -> _TableData:
    headers: list[str] = []
    if options.include_result_name:
        headers.append("Result")
    if options.include_table_name:
        headers.append("Table")
    headers.extend(["Column", "Statistic", "Estimate", "CI Lower", "CI Upper"])
    if options.include_confidence_level:
        headers.append("Level")

    rows: list[list[str]] = []
    for result in results:
        data = result.result_data
        row: list[str] = []
        if options.include_result_name:
            row.append(result.name)
        if options.include_table_name:
            row.append(result.table_name)
        row.extend(
            [
                str(data["columnName"]),
                str(data["statistic"]["type"]),
                _format_cell(data["statistic"]["value"]),
                _format_cell(data["confidenceInterval"]["lower"]),
                _format_cell(data["confidenceInterval"]["upper"]),
            ]
        )
        if options.include_confidence_level:
            row.append(_format_cell(data.get("confidenceLevel")))
        rows.append(row)

    return _TableData(headers=headers, rows=rows)


def _build_statistical_test_headers(
    *,
    has_df2: bool,
    has_level: bool,
    options: StatisticalTestOutputOptions,
) -> list[str]:
    headers: list[str] = []
    if options.include_result_name:
        headers.append("Result")
    if options.include_table_name:
        headers.append("Table")
    headers.extend(["Statistic", "p-value", "df"])
    if has_df2:
        headers.append("df2")
    if options.include_confidence_interval:
        headers.extend(["CI Lower", "CI Upper"])
    if options.include_confidence_level and has_level:
        headers.append("Level")
    if options.include_effect_size:
        headers.append("Effect Size")
    return headers


def _build_statistical_test_row(
    result: AnalysisResult,
    *,
    has_df2: bool,
    has_level: bool,
    options: StatisticalTestOutputOptions,
) -> list[str]:
    data = result.result_data
    ci = data.get("confidenceInterval")
    row: list[str] = []

    if options.include_result_name:
        row.append(result.name)
    if options.include_table_name:
        row.append(result.table_name)

    row.extend(
        [
            _format_cell(data.get("statistic")),
            _format_cell(data.get("pValue")),
            _format_cell(data.get("df")),
        ]
    )
    if has_df2:
        row.append(_format_cell(data.get("df2")))
    if options.include_confidence_interval:
        row.extend(
            [
                _format_cell(ci.get("lower") if ci else None),
                _format_cell(ci.get("upper") if ci else None),
            ]
        )
    if options.include_confidence_level and has_level:
        row.append(_format_cell(data.get("confidenceLevel")))
    if options.include_effect_size:
        row.append(_format_cell(data.get("effectSize")))

    return row


def _build_statistical_test_table(
    results: list[AnalysisResult],
    options: StatisticalTestOutputOptions,
) -> _TableData:
    has_df2 = any(
        result.result_data.get("df2") is not None for result in results
    )
    has_level = any(
        result.result_data.get("confidenceLevel") is not None
        for result in results
    )
    headers = _build_statistical_test_headers(
        has_df2=has_df2,
        has_level=has_level,
        options=options,
    )
    rows = [
        _build_statistical_test_row(
            result,
            has_df2=has_df2,
            has_level=has_level,
            options=options,
        )
        for result in results
    ]
    return _TableData(headers=headers, rows=rows)


class OutputResult:
    """分析結果を text / markdown / latex に整形して返す。"""

    PARAM_NAMES: ClassVar[dict[str, str]] = {
        "result_ids": "resultIds",
        "result_type": "resultType",
    }

    def __init__(
        self,
        body: OutputResultRequest,
        result_store: AnalysisResultStore,
    ) -> None:
        self.body = body
        self.result_ids = body.result_ids
        self.result_type = body.result_type
        self.output_format = body.format
        self.options = body.options
        self.result_store = result_store
        self._fetched: list[AnalysisResult] | None = None

    def validate(self) -> None:
        missing: list[str] = []
        fetched: list[AnalysisResult] = []
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

        self._validate_result_types(fetched)
        self._fetched = fetched

    def _validate_result_types(self, results: list[AnalysisResult]) -> None:
        actual_types = {result.result_type for result in results}
        if len(actual_types) != 1:
            raise ValidationError(
                error_code=ErrorCode.VALIDATION_ERROR,
                message=_(
                    "All analysis results must have the same result "
                    "type for output."
                ),
            )

        actual_type = next(iter(actual_types))
        if actual_type != self.result_type:
            raise ValidationError(
                error_code=ErrorCode.VALIDATION_ERROR,
                message=_(
                    "Requested result type '%(requested)s' does not "
                    "match stored analysis result type "
                    "'%(actual)s'."
                )
                % {
                    "requested": self.result_type,
                    "actual": actual_type,
                },
            )

    def _build_regression_formatter(
        self,
        results: list[AnalysisResult],
    ) -> _RegressionFormatter:
        options = cast(RegressionOutputOptions, self.options)
        stat_key = _STAT_KEY_MAP.get(options.stat_in_parentheses)
        if options.significance_stars is not None:
            stars: list[dict[str, Any]] | None = [
                star.model_dump() for star in options.significance_stars
            ]
        else:
            stars = [
                {"threshold": 0.01, "symbol": "***"},
                {"threshold": 0.05, "symbol": "**"},
                {"threshold": 0.1, "symbol": "*"},
            ]

        outputs = [_RegOutput(result.result_data) for result in results]
        return _RegressionFormatter(
            outputs,
            stat_key=stat_key,
            stars=stars,
            variable_labels=options.variable_labels,
            const_at_bottom=options.const_at_bottom,
            variable_order=options.variable_order,
        )

    def _build_formatter(
        self,
        results: list[AnalysisResult],
    ) -> _OutputFormatter:
        match self.result_type:
            case "regression":
                return self._build_regression_formatter(results)
            case "descriptive_statistics":
                options = cast(
                    DescriptiveStatisticsOutputOptions,
                    self.options,
                )
                table = _build_descriptive_table(results, options)
                return _TableFormatter(table)
            case "confidence_interval":
                options = cast(ConfidenceIntervalOutputOptions, self.options)
                table = _build_confidence_interval_table(results, options)
                return _TableFormatter(table)
            case "statistical_test":
                options = cast(StatisticalTestOutputOptions, self.options)
                table = _build_statistical_test_table(results, options)
                return _TableFormatter(table)
            case _:
                raise ValidationError(
                    error_code=ErrorCode.VALIDATION_ERROR,
                    message=_(
                        "Requested result type '%(requested)s' is not "
                        "supported for formatted output."
                    )
                    % {"requested": self.result_type},
                )

    def execute(self) -> dict[str, Any]:
        try:
            results = self._fetched or [
                self.result_store.get_result(rid) for rid in self.result_ids
            ]
            formatter = self._build_formatter(results)

            match self.output_format:
                case "latex":
                    content = formatter.to_latex()
                case "markdown":
                    content = formatter.to_markdown()
                case _:
                    content = formatter.to_text()

            return {"content": content, "format": self.output_format}

        except ValidationError, ProcessingError:
            raise
        except Exception as e:
            raise ProcessingError(
                error_code=ErrorCode.OUTPUT_RESULT_ERROR,
                message=_(
                    "An unexpected error occurred during outputting results"
                ),
            ) from e
