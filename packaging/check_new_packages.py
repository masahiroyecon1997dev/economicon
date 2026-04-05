#!/usr/bin/env python3
"""check_new_packages.py — Supply Chain Freshness Checker

pnpm-lock.yaml / uv.lock / Cargo.lock を base-ref と HEAD で比較し、
新規追加・バージョン更新されたパッケージを各レジストリ API に照会する。
リリースから --days 日未満のパッケージが見つかった場合は警告またはエラーを出力する。

使い方:
    python packaging/check_new_packages.py \\
        --base-ref origin/dev \\
        --days 7 \\
        --mode error
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------


def get_file_at_ref(repo_root: Path, ref: str, rel_path: str) -> str:
    """指定 git ref でのファイル内容を返す。存在しない場合は空文字列を返す。"""
    try:
        result = subprocess.run(
            ["git", "show", f"{ref}:{rel_path}"],
            capture_output=True,
            text=True,
            cwd=repo_root,
            check=True,
        )
        return result.stdout
    except subprocess.CalledProcessError:
        return ""


# ---------------------------------------------------------------------------
# Lock-file parsers
# ---------------------------------------------------------------------------


def parse_pnpm_lock(content: str) -> set[tuple[str, str]]:
    """
    pnpm-lock.yaml v9 の `packages:` セクションを解析して {(name, version)} を返す。
    `snapshots:` セクションは重複カウント防止のため除外する。
    """
    packages: set[tuple[str, str]] = set()
    in_packages_section = False

    for line in content.splitlines():
        stripped = line.rstrip()

        # セクション境界の追跡
        if stripped == "packages:":
            in_packages_section = True
            continue
        if stripped == "snapshots:":
            in_packages_section = False
            continue
        if not in_packages_section:
            continue

        # トップレベルのエントリは厳密に 2 スペースインデント
        if len(line) < 3 or line[:2] != "  " or line[2] == " ":
            continue

        entry = line.strip()
        colon = entry.find(":")
        if colon == -1:
            continue

        key = entry[:colon].strip()

        # 引用符を除去: '@scope/pkg@version'  →  @scope/pkg@version
        if len(key) >= 2 and key[0] == "'" and key[-1] == "'":
            key = key[1:-1]

        # peer-dep アノテーションを除去: pkg@ver(peer@v)  →  pkg@ver
        # ネストを含む可能性があるため最初の '(' 以降を切り捨てる
        paren = key.find("(")
        if paren != -1:
            key = key[:paren]

        # name@version を最後の '@' で分割
        last_at = key.rfind("@")
        if last_at <= 0:
            # last_at == 0 は '@' が先頭のみ（スコープ + バージョン区切りなし）→ スキップ
            continue

        name = key[:last_at]
        version = key[last_at + 1 :]

        # バージョンは数字で始まる必要がある
        if not version or not version[0].isdigit():
            continue

        packages.add((name, version))

    return packages


def parse_uv_lock(content: str) -> set[tuple[str, str]]:
    """
    uv.lock を解析して {(name, version)} を返す。
    PyPI レジストリ由来のパッケージのみ対象（ローカル editable / git / path は除外）。
    """
    packages: set[tuple[str, str]] = set()

    for block in re.split(r"(?=^\[\[package\]\])", content, flags=re.MULTILINE):
        if "[[package]]" not in block:
            continue
        name_m = re.search(r'^name = "([^"]+)"', block, re.MULTILINE)
        ver_m = re.search(r'^version = "([^"]+)"', block, re.MULTILINE)
        # source = { registry = "..." } パターンのみ対象
        src_m = re.search(r"^source = \{[^}]*registry", block, re.MULTILINE)
        if name_m and ver_m and src_m:
            packages.add((name_m.group(1), ver_m.group(1)))

    return packages


def parse_cargo_lock(content: str) -> set[tuple[str, str]]:
    """
    Cargo.lock を解析して {(name, version)} を返す。
    crates.io レジストリ由来のパッケージのみ対象（ワークスペースメンバー / git は除外）。
    """
    packages: set[tuple[str, str]] = set()

    for block in re.split(r"(?=^\[\[package\]\])", content, flags=re.MULTILINE):
        if "[[package]]" not in block:
            continue
        name_m = re.search(r'^name = "([^"]+)"', block, re.MULTILINE)
        ver_m = re.search(r'^version = "([^"]+)"', block, re.MULTILINE)
        # source = "registry+https://..." パターンのみ対象
        src_m = re.search(r'^source = "registry\+', block, re.MULTILINE)
        if name_m and ver_m and src_m:
            packages.add((name_m.group(1), ver_m.group(1)))

    return packages


# ---------------------------------------------------------------------------
# Registry API
# ---------------------------------------------------------------------------


def fetch_json(
    url: str,
    headers: dict[str, str] | None = None,
    retries: int = 2,
) -> dict | None:
    """JSON を取得する。レート制限 (429) 時はバックオフリトライ。"""
    req = urllib.request.Request(url, headers=headers or {})
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None  # パッケージが見つからない → スキップ
            if exc.code == 429 and attempt < retries:
                wait = 2 ** (attempt + 1)
                print(f"    429 Too Many Requests. {wait}s 待機してリトライ…", file=sys.stderr)
                time.sleep(wait)
                continue
            print(f"    WARNING: HTTP {exc.code} — {url}", file=sys.stderr)
            return None
        except Exception as exc:  # noqa: BLE001
            if attempt < retries:
                time.sleep(1)
                continue
            print(f"    WARNING: 取得失敗 {url}: {exc}", file=sys.stderr)
            return None
    return None


def check_npm(name: str, version: str, threshold: datetime) -> tuple[bool, str]:
    """npm レジストリでリリース日を確認する。(is_too_fresh, 'YYYY-MM-DD') を返す。"""
    # スコープ付きパッケージ @scope/pkg → @scope%2Fpkg
    encoded = quote(name, safe="@")
    data = fetch_json(
        f"https://registry.npmjs.org/{encoded}",
        headers={"Accept": "application/json"},
    )
    if not data:
        return False, "unknown"

    release_str = (data.get("time") or {}).get(version)
    if not release_str:
        return False, "unknown"

    released = datetime.fromisoformat(release_str.replace("Z", "+00:00"))
    return released >= threshold, released.strftime("%Y-%m-%d")


def check_pypi(name: str, version: str, threshold: datetime) -> tuple[bool, str]:
    """PyPI でリリース日を確認する。(is_too_fresh, 'YYYY-MM-DD') を返す。"""
    data = fetch_json(f"https://pypi.org/pypi/{name}/{version}/json")
    if not data:
        return False, "unknown"

    urls = data.get("urls") or []
    upload_times: list[datetime] = []
    for u in urls:
        t = u.get("upload_time_iso_8601") or u.get("upload_time")
        if t:
            upload_times.append(datetime.fromisoformat(t.replace("Z", "+00:00")))

    if not upload_times:
        return False, "unknown"

    released = min(upload_times)
    return released >= threshold, released.strftime("%Y-%m-%d")


def check_crates(name: str, version: str, threshold: datetime) -> tuple[bool, str]:
    """crates.io でリリース日を確認する。(is_too_fresh, 'YYYY-MM-DD') を返す。"""
    # crates.io は User-Agent ヘッダーが必須
    data = fetch_json(
        f"https://crates.io/api/v1/crates/{name}/{version}",
        headers={
            "User-Agent": (
                "economicon-supply-chain-checker/1.0 "
                "(https://github.com/masahiroyecon1997dev/economicon)"
            ),
            "Accept": "application/json",
        },
    )
    if not data:
        return False, "unknown"

    created_at = (data.get("version") or {}).get("created_at")
    if not created_at:
        return False, "unknown"

    released = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    return released >= threshold, released.strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "新規追加・更新されたパッケージが --days 日以内にリリースされていないか確認する。"
        )
    )
    parser.add_argument(
        "--base-ref",
        default="origin/HEAD",
        help="比較元の git ref (デフォルト: origin/HEAD)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="フラグを立てるリリース経過日数の閾値 (デフォルト: 7)",
    )
    parser.add_argument(
        "--mode",
        choices=["warn", "error"],
        default="error",
        help="warn=exit 0 / error=exit 1  (デフォルト: error)",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="リポジトリルートパス (デフォルト: このスクリプトの 2 階層上)",
    )
    args = parser.parse_args()

    repo_root: Path = args.repo_root or Path(__file__).resolve().parent.parent
    threshold = datetime.now(timezone.utc) - timedelta(days=args.days)
    base_ref = args.base_ref

    print("\n" + "=" * 60)
    print("  Supply Chain Freshness Check")
    print("=" * 60)
    print(f"  base-ref  : {base_ref}")
    print(f"  threshold : リリースから {args.days} 日以内 ({threshold:%Y-%m-%d} 以降)")
    print(f"  mode      : {args.mode}")
    print(f"  repo-root : {repo_root}")

    # ---- 各 lockfile の HEAD と base-ref を比較 ----

    changed: dict[str, list[tuple[str, str]]] = {
        "npm": [],
        "pypi": [],
        "crates": [],
    }

    # npm (pnpm-lock.yaml)
    pnpm_rel = "app/pnpm-lock.yaml"
    pnpm_head = parse_pnpm_lock(get_file_at_ref(repo_root, "HEAD", pnpm_rel))
    pnpm_base = parse_pnpm_lock(get_file_at_ref(repo_root, base_ref, pnpm_rel))
    changed["npm"] = sorted(pnpm_head - pnpm_base)

    # PyPI (uv.lock)
    uv_rel = "api/uv.lock"
    uv_head = parse_uv_lock(get_file_at_ref(repo_root, "HEAD", uv_rel))
    uv_base = parse_uv_lock(get_file_at_ref(repo_root, base_ref, uv_rel))
    changed["pypi"] = sorted(uv_head - uv_base)

    # crates.io (Cargo.lock)
    cargo_rel = "app/src-tauri/Cargo.lock"
    cargo_head = parse_cargo_lock(get_file_at_ref(repo_root, "HEAD", cargo_rel))
    cargo_base = parse_cargo_lock(get_file_at_ref(repo_root, base_ref, cargo_rel))
    changed["crates"] = sorted(cargo_head - cargo_base)

    total = sum(len(v) for v in changed.values())
    print(
        f"\n  変更パッケージ数 — "
        f"npm: {len(changed['npm'])}, "
        f"PyPI: {len(changed['pypi'])}, "
        f"crates.io: {len(changed['crates'])} "
        f"(合計: {total})"
    )

    if total == 0:
        print("\n  lockfile に差分なし。freshness チェックをスキップします。")
        print("=" * 60 + "\n")
        sys.exit(0)

    # ---- 各パッケージをレジストリ API で確認 ----

    flagged: list[str] = []

    if changed["npm"]:
        print(f"\n  [npm] {len(changed['npm'])} 件を確認中...")
        for name, version in changed["npm"]:
            is_fresh, date = check_npm(name, version, threshold)
            label = "⚠ FLAGGED" if is_fresh else "  ok     "
            print(f"    {label}  {date}  {name}@{version}")
            if is_fresh:
                flagged.append(f"npm:{name}@{version}  (リリース日: {date})")

    if changed["pypi"]:
        print(f"\n  [PyPI] {len(changed['pypi'])} 件を確認中...")
        for name, version in changed["pypi"]:
            is_fresh, date = check_pypi(name, version, threshold)
            label = "⚠ FLAGGED" if is_fresh else "  ok     "
            print(f"    {label}  {date}  {name}=={version}")
            if is_fresh:
                flagged.append(f"pypi:{name}=={version}  (リリース日: {date})")

    if changed["crates"]:
        print(f"\n  [crates.io] {len(changed['crates'])} 件を確認中...")
        for name, version in changed["crates"]:
            is_fresh, date = check_crates(name, version, threshold)
            label = "⚠ FLAGGED" if is_fresh else "  ok     "
            print(f"    {label}  {date}  {name} v{version}")
            if is_fresh:
                flagged.append(f"crates:{name} v{version}  (リリース日: {date})")

    # ---- サマリー ----

    print("\n" + "=" * 60)

    if flagged:
        print(f"  ⚠  {len(flagged)} 件のパッケージがリリースから {args.days} 日以内です！")
        print("=" * 60)
        for pkg in flagged:
            print(f"    •  {pkg}")
        print(
            "\n  サプライチェーン攻撃の可能性を排除するため、以下を手動確認してください:\n"
            "    1. パッケージのリリースノートおよび git 履歴\n"
            "    2. メンテナーが正当な人物であること\n"
            "    3. マージ前に一定期間（7 日以上）待機することを検討する\n"
        )
        if args.mode == "error":
            print("  [error モード] フラグ付きパッケージが存在するため終了します。")
            print("=" * 60 + "\n")
            sys.exit(1)
        else:
            print("  [warn モード] 続行しますが、上記パッケージを確認してください。")
            print("=" * 60 + "\n")
    else:
        print(
            f"  ✔  変更された全 {total} 件のパッケージは "
            f"リリースから {args.days} 日以上経過しています。"
        )
        print("  Supply Chain Freshness Check PASSED.")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
