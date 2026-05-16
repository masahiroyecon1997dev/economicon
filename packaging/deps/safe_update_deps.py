#!/usr/bin/env python3
"""safe_update_deps.py -- Safe Dependency Updater

各エコシステムの outdated パッケージを取得し、最新版が --days 日以上経過している
もの（安全）のみをリストアップ、または適用する。

モード:
  outdated (デフォルト)
    安全なパッケージに "SAFE ✔"、リリースが新しすぎるパッケージに "SKIP ⚠" を表示する。
    ファイルは一切変更しない。

  apply
    安全と判定されたパッケージののみを更新し、lock ファイルを再生成する。
    更新後に pnpm / uv / cargo の整合性検証を実行する。

使い方:
    python packaging/deps/safe_update_deps.py --mode outdated --days 7
    python packaging/deps/safe_update_deps.py --mode apply   --days 7
"""

from __future__ import annotations

import io
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from argparse import ArgumentParser
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

# Windows コンソールで日本語を正しく出力するため UTF-8 に統一する
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
APP_DIR = REPO_ROOT / "app"
API_DIR = REPO_ROOT / "api"
TAURI_DIR = APP_DIR / "src-tauri"


def run(
    cmd: list[str], *, cwd: Path, check: bool = True, capture: bool = True
) -> subprocess.CompletedProcess:
    # Windows では shell=True なしでは .cmd スクリプト（pnpm.cmd 等）が見つからない
    return subprocess.run(
        cmd,
        cwd=cwd,
        check=check,
        capture_output=capture,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=(sys.platform == "win32"),
    )


def fetch_json(
    url: str, headers: dict[str, str] | None = None, retries: int = 2
) -> dict | None:
    req = urllib.request.Request(url, headers=headers or {})
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            if exc.code == 429 and attempt < retries:
                wait = 2 ** (attempt + 1)
                print(
                    f"    429 Too Many Requests ({wait}s 待機してリトライ...)",
                    file=sys.stderr,
                )
                time.sleep(wait)
                continue
            print(f"    WARNING: HTTP {exc.code} - {url}", file=sys.stderr)
            return None
        except Exception as exc:  # noqa: BLE001
            if attempt < retries:
                time.sleep(1)
                continue
            print(f"    WARNING: 取得失敗 {url}: {exc}", file=sys.stderr)
            return None
    return None


def release_date_npm(name: str, version: str) -> datetime | None:
    encoded = quote(name, safe="@")
    data = fetch_json(
        f"https://registry.npmjs.org/{encoded}", headers={"Accept": "application/json"}
    )
    if not data:
        return None
    rel = (data.get("time") or {}).get(version)
    if not rel:
        return None
    return datetime.fromisoformat(rel.replace("Z", "+00:00"))


def release_date_pypi(name: str, version: str) -> datetime | None:
    data = fetch_json(f"https://pypi.org/pypi/{name}/{version}/json")
    if not data:
        return None
    urls = data.get("urls") or []
    times: list[datetime] = []
    for u in urls:
        t = u.get("upload_time_iso_8601") or u.get("upload_time")
        if t:
            times.append(datetime.fromisoformat(t.replace("Z", "+00:00")))
    return min(times) if times else None


def _major_version(version: str) -> int | None:
    """バージョン文字列からメジャー番号を返す。パース失敗時は None。"""
    m = re.match(r"(\d+)", version.lstrip("v^~"))
    return int(m.group(1)) if m else None


def release_date_crates(name: str, version: str) -> datetime | None:
    data = fetch_json(
        f"https://crates.io/api/v1/crates/{name}/{version}",
        headers={
            "User-Agent": (
                "economicon-safe-update/1.0 "
                "(https://github.com/masahiroyecon1997dev/economicon)"
            ),
            "Accept": "application/json",
        },
    )
    if not data:
        return None
    created = (data.get("version") or {}).get("created_at")
    if not created:
        return None
    return datetime.fromisoformat(created.replace("Z", "+00:00"))


# ---------------------------------------------------------------------------
# Outdated detection
# ---------------------------------------------------------------------------


def get_outdated_npm() -> list[dict]:
    """pnpm outdated --json から更新候補を返す。"""
    result = run(["pnpm", "outdated", "--json"], cwd=APP_DIR, check=False)
    raw = result.stdout.strip()
    if not raw:
        return []
    try:
        data: dict = json.loads(raw)
    except json.JSONDecodeError:
        return []
    items = []
    for pkg_name, info in data.items():
        current = info.get("current", "")
        latest = info.get("latest", "")
        if current and latest and current != latest:
            items.append(
                {
                    "name": pkg_name,
                    "current": current,
                    "latest": latest,
                    "dep_type": info.get("dependencyType", ""),
                }
            )
    return items


def get_outdated_pypi() -> list[dict]:
    """uv pip list --outdated --format json から更新候補を返す。
    uv.lock に記載された本番パッケージのみを対象にする。"""
    # まず uv.lock から本番パッケージ名を取得する（parse_uv_lock の簡易版）
    uv_lock = API_DIR / "uv.lock"
    prod_names: set[str] = set()
    if uv_lock.exists():
        content = uv_lock.read_text(encoding="utf-8")
        for block in re.split(r"(?=^\[\[package\]\])", content, flags=re.MULTILINE):
            if "[[package]]" not in block:
                continue
            name_m = re.search(r'^name = "([^"]+)"', block, re.MULTILINE)
            src_m = re.search(r"^source = \{[^}]*registry", block, re.MULTILINE)
            if name_m and src_m:
                prod_names.add(name_m.group(1).lower())

    result = run(
        ["uv", "pip", "list", "--outdated", "--format", "json"],
        cwd=API_DIR,
        check=False,
    )
    raw = result.stdout.strip()
    if not raw:
        return []
    try:
        all_items: list[dict] = json.loads(raw)
    except json.JSONDecodeError:
        return []

    items = []
    for entry in all_items:
        name = entry.get("name", "")
        current = entry.get("version", "")
        latest = entry.get("latest_version", "")
        if not (name and current and latest and current != latest):
            continue
        # prod_names が空（uv.lock なし）なら全件対象
        if prod_names and name.lower() not in prod_names:
            continue
        items.append({"name": name, "current": current, "latest": latest})
    return items


def get_outdated_cargo() -> list[dict]:
    """cargo update --dry-run の出力をパースして更新候補を返す。
    cargo-outdated がない環境でも動作する。"""
    result = run(
        ["cargo", "update", "--dry-run"],
        cwd=TAURI_DIR,
        check=False,
    )
    # cargo update --dry-run は stderr に出力する
    output = result.stderr + result.stdout
    items = []
    # "Updating NAME vOLD -> vNEW" パターン
    pattern = re.compile(r"Updating\s+(\S+)\s+v([\d.\-+a-z]+)\s+->\s+v([\d.\-+a-z]+)")
    for m in pattern.finditer(output):
        items.append(
            {
                "name": m.group(1),
                "current": m.group(2),
                "latest": m.group(3),
            }
        )
    return items


# ---------------------------------------------------------------------------
# Freshness check
# ---------------------------------------------------------------------------

# 結果型: (name, current, latest, is_safe, release_date_str, reason)
PackageResult = tuple[str, str, str, bool, str, str]


def check_freshness(
    items: list[dict],
    ecosystem: str,
    threshold: datetime,
) -> list[PackageResult]:
    results: list[PackageResult] = []
    for item in items:
        name = item["name"]
        latest = item["latest"]
        current = item["current"]

        # メジャーバージョンアップは安全でないためスキップ
        cur_major = _major_version(current)
        lat_major = _major_version(latest)
        if cur_major is not None and lat_major is not None and lat_major > cur_major:
            results.append(
                (
                    name,
                    current,
                    latest,
                    False,
                    "unknown",
                    f"メジャーバージョンアップのためスキップ (v{cur_major} → v{lat_major})",
                )
            )
            continue

        if ecosystem == "npm":
            rel = release_date_npm(name, latest)
        elif ecosystem == "pypi":
            rel = release_date_pypi(name, latest)
        else:  # crates
            rel = release_date_crates(name, latest)

        if rel is None:
            results.append(
                (name, current, latest, False, "unknown", "API 取得失敗（スキップ）")
            )
            continue

        date_str = rel.strftime("%Y-%m-%d")
        if rel >= threshold:
            days_ago = (datetime.now(timezone.utc) - rel).days
            results.append(
                (
                    name,
                    current,
                    latest,
                    False,
                    date_str,
                    f"リリースから {days_ago} 日 (閒値未満のためスキップ)",
                )
            )
        else:
            results.append((name, current, latest, True, date_str, ""))
    return results


# ---------------------------------------------------------------------------
# Apply
# ---------------------------------------------------------------------------


def apply_npm(safe_pkgs: list[tuple[str, str, str]]) -> None:
    """pnpm update --latest で安全なパッケージを更新する。"""
    names = [name for name, _, _ in safe_pkgs]
    print(f"\n  [npm] {len(names)} 件を更新中... ({', '.join(names)})")
    run(["pnpm", "update", "--latest", *names], cwd=APP_DIR, capture=False)
    print("  [npm] pnpm-lock.yaml を再生成しました。")


def apply_pypi(safe_pkgs: list[tuple[str, str, str]]) -> None:
    """uv lock --upgrade-package で安全なパッケージのみ更新する。"""
    for name, current, latest in safe_pkgs:
        print(f"  [PyPI] {name}: {current} → {latest}")
        run(["uv", "lock", "--upgrade-package", name], cwd=API_DIR, capture=False)
    print("  [PyPI] uv.lock を更新しました。")


def apply_cargo(safe_pkgs: list[tuple[str, str, str]]) -> None:
    """cargo update -p で安全なパッケージのみ更新する。"""
    for name, current, latest in safe_pkgs:
        print(f"  [Cargo] {name}: {current} → {latest}")
        run(
            ["cargo", "update", "-p", f"{name}@{current}", "--precise", latest],
            cwd=TAURI_DIR,
            capture=False,
        )
    print("  [Cargo] Cargo.lock を更新しました。")


def verify_all() -> bool:
    """lock ファイルの整合性を検証する。エラーがあれば False を返す。"""
    ok = True

    print("\n" + "─" * 60)
    print("  [検証 1/4] pnpm install --frozen-lockfile")
    r = run(
        ["pnpm", "install", "--frozen-lockfile"],
        cwd=APP_DIR,
        check=False,
        capture=False,
    )
    if r.returncode != 0:
        print("  ✘ pnpm: 整合性エラー", file=sys.stderr)
        ok = False
    else:
        print("  ✔ pnpm: OK")

    print("\n  [検証 2/4] uv sync --frozen")
    r = run(["uv", "sync", "--frozen"], cwd=API_DIR, check=False, capture=False)
    if r.returncode != 0:
        print("  ✘ uv sync: 整合性エラー", file=sys.stderr)
        ok = False
    else:
        print("  ✔ uv sync: OK")

    print("\n  [検証 3/4] cargo check")
    r = run(["cargo", "check"], cwd=TAURI_DIR, check=False, capture=False)
    if r.returncode != 0:
        print("  ✘ cargo check: コンパイルエラー", file=sys.stderr)
        ok = False
    else:
        print("  ✔ cargo check: OK")

    print("\n  [検証 4/4] Supply Chain Freshness Check (warn モード)")
    checker = REPO_ROOT / "packaging" / "check_new_packages.py"
    r = run(
        [sys.executable, str(checker), "--base-ref", "HEAD~1", "--mode", "warn"],
        cwd=REPO_ROOT,
        check=False,
        capture=False,
    )
    if r.returncode != 0:
        print("  ⚠ freshness チェックが警告を検出しました。", file=sys.stderr)
        # warn モードなのでビルドは止めない
    else:
        print("  ✔ freshness チェック: OK")

    return ok


# ---------------------------------------------------------------------------
# Print helpers
# ---------------------------------------------------------------------------

W = 50  # 幅


def print_section(title: str) -> None:
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")


def print_result_row(
    ecosystem: str,
    name: str,
    current: str,
    latest: str,
    is_safe: bool,
    date_str: str,
    reason: str,
) -> None:
    if is_safe:
        label = "  SAFE ✔"
    elif reason.startswith("API"):
        label = "  ????  "
    else:
        label = "  SKIP ⚠"
    pkg = f"{name}  {current} → {latest}"
    print(f"    {label}  {date_str}  {pkg}")
    if reason:
        print(f"             ↳ {reason}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = ArgumentParser(description="依存パッケージを安全に更新する")
    parser.add_argument(
        "--mode",
        choices=["outdated", "apply"],
        default="outdated",
        help="outdated=リストのみ / apply=安全なパッケージを実際に更新 (デフォルト: outdated)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="更新を許可するリリース経過日数の最小値 (デフォルト: 7)",
    )
    args = parser.parse_args()

    threshold = datetime.now(timezone.utc) - timedelta(days=args.days)

    print("\n" + "=" * 60)
    print("  Safe Dependency Updater")
    print("=" * 60)
    print(f"  mode      : {args.mode}")
    print(f"  threshold : リリースから {args.days} 日以上経過したもののみ安全と判定")
    print(f"              ({threshold:%Y-%m-%d %H:%M} UTC 以前のリリース)")

    # ---- outdated 収集 ----
    print_section("[1/3] npm (pnpm) - 更新候補を取得中...")
    npm_items = get_outdated_npm()
    print(f"  {len(npm_items)} 件の更新候補を検出")

    print_section("[2/3] PyPI (uv) - 更新候補を取得中...")
    pypi_items = get_outdated_pypi()
    print(f"  {len(pypi_items)} 件の更新候補を検出")

    print_section("[3/3] crates.io (cargo) - 更新候補を取得中...")
    cargo_items = get_outdated_cargo()
    print(f"  {len(cargo_items)} 件の更新候補を検出")

    total = len(npm_items) + len(pypi_items) + len(cargo_items)
    if total == 0:
        print("\n" + "=" * 60)
        print("  ✔ すべての依存パッケージは最新です。")
        print("=" * 60 + "\n")
        sys.exit(0)

    # ---- freshness 判定 ----
    print_section("Freshness チェック (レジストリ API 照会中...)")

    npm_results = check_freshness(npm_items, "npm", threshold)
    pypi_results = check_freshness(pypi_items, "pypi", threshold)
    cargo_results = check_freshness(cargo_items, "crates", threshold)

    print("\n  --- npm ---")
    for name, cur, lat, safe, date, reason in npm_results:
        print_result_row("npm", name, cur, lat, safe, date, reason)

    print("\n  --- PyPI ---")
    for name, cur, lat, safe, date, reason in pypi_results:
        print_result_row("pypi", name, cur, lat, safe, date, reason)

    print("\n  --- crates.io ---")
    for name, cur, lat, safe, date, reason in cargo_results:
        print_result_row("crates", name, cur, lat, safe, date, reason)

    # 安全なパッケージの集計
    safe_npm = [(n, c, lt) for n, c, lt, s, _, _ in npm_results if s]
    safe_pypi = [(n, c, lt) for n, c, lt, s, _, _ in pypi_results if s]
    safe_cargo = [(n, c, lt) for n, c, lt, s, _, _ in cargo_results if s]

    skip_npm = [(n, c, lt) for n, c, lt, s, _, _ in npm_results if not s]
    skip_pypi = [(n, c, lt) for n, c, lt, s, _, _ in pypi_results if not s]
    skip_cargo = [(n, c, lt) for n, c, lt, s, _, _ in cargo_results if not s]

    print("\n" + "=" * 60)
    print("  サマリー")
    print("=" * 60)
    print(f"  SAFE ✔  npm:   {len(safe_npm):3d} 件 / スキップ: {len(skip_npm):3d} 件")
    print(f"  SAFE ✔  PyPI:  {len(safe_pypi):3d} 件 / スキップ: {len(skip_pypi):3d} 件")
    print(
        f"  SAFE ✔  cargo: {len(safe_cargo):3d} 件 / スキップ: {len(skip_cargo):3d} 件"
    )

    safe_total = len(safe_npm) + len(safe_pypi) + len(safe_cargo)
    skip_total = len(skip_npm) + len(skip_pypi) + len(skip_cargo)
    print(f"\n  合計  SAFE: {safe_total} 件  SKIP: {skip_total} 件")

    if args.mode == "outdated":
        print("\n  [outdated モード] ファイルへの変更はありません。")
        print("  更新を適用するには --mode apply で再実行してください。")
        print("=" * 60 + "\n")
        sys.exit(0)

    # ---- apply モード ----
    if safe_total == 0:
        print("\n  安全と判定されたパッケージがありません。更新をスキップします。")
        print("=" * 60 + "\n")
        sys.exit(0)

    print("\n" + "=" * 60)
    print(f"  [apply モード] {safe_total} 件を更新します...")
    print("=" * 60)

    if safe_npm:
        apply_npm(safe_npm)
    if safe_pypi:
        apply_pypi(safe_pypi)
    if safe_cargo:
        apply_cargo(safe_cargo)

    # ---- 検証 ----
    print("\n" + "=" * 60)
    print("  更新後の整合性検証")
    print("=" * 60)
    ok = verify_all()

    print("\n" + "=" * 60)
    if ok:
        print(f"  ✔ {safe_total} 件の更新が正常に完了しました。")
        print("  lock ファイルの整合性を確認済みです。")
        print("=" * 60 + "\n")
        sys.exit(0)
    else:
        print("  ✘ 整合性検証でエラーが検出されました。")
        print("  上記のエラーを確認し、手動で修正してください。")
        print("=" * 60 + "\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
