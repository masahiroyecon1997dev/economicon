"""スキーマ横断で使う検証ヘルパー。"""

from economicon.i18n.translation import gettext as _


def _check_group_pair(
    name_a: str,
    cols_a: set[str],
    name_b: str,
    cols_b: set[str],
) -> None:
    """2列グループ間に重複があれば ValueError を送出する。"""
    overlap = cols_a & cols_b
    if not overlap:
        return
    raise ValueError(
        _("{} must not overlap with {}: {}").format(
            name_a, name_b, ", ".join(sorted(overlap))
        )
    )


def check_column_overlap(
    *,
    dependent_variable: str,
    explanatory_variables: list[str],
    reserved_scalars: dict[str, str] | None = None,
    reserved_vectors: dict[str, list[str]] | None = None,
) -> None:
    """列重複チェック（Pydantic model_validator から呼ぶ）。"""
    rs = reserved_scalars or {}
    rv = reserved_vectors or {}
    expl_set = set(explanatory_variables)

    if len(explanatory_variables) != len(expl_set):
        raise ValueError(
            _("explanatoryVariables must not contain duplicate column names.")
        )

    rs_vals = list(rs.values())
    if rs and len(rs_vals) != len(set(rs_vals)):
        raise ValueError(
            _("{} must all be distinct.").format(" / ".join(rs.keys()))
        )

    groups: dict[str, set[str]] = {
        "dependentVariable": {dependent_variable},
        "explanatoryVariables": expl_set,
        **{key: {value} for key, value in rs.items()},
        **{key: set(value) for key, value in rv.items()},
    }
    items = list(groups.items())
    for index, (name_a, cols_a) in enumerate(items):
        for name_b, cols_b in items[index + 1 :]:
            _check_group_pair(name_a, cols_a, name_b, cols_b)
