#!/usr/bin/env python3
"""Scrape Rhino SDK docs, diff against context/, and write reports."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from html import unescape
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


BASE_DOCS_URL = "https://rhinohealth.github.io/rhino_sdk_docs/html/"
GITHUB_EXAMPLES_API = (
    "https://api.github.com/repos/RhinoHealth/user-resources/contents/examples/rhino-sdk"
)
DEFAULT_TIMEOUT_SECONDS = 20
USER_AGENT = "rhino-sdk-doc-sync/0.1"


@dataclass
class ScrapeSnapshot:
    sdk_version: str
    modules: list[str]
    endpoint_signatures: dict[str, list[str]]
    metric_signatures: dict[str, list[str]]
    enum_members: dict[str, list[str]]
    example_files: list[str]


@dataclass
class ContextSnapshot:
    sdk_version: str
    sdk_reference_text: str
    metrics_reference_text: str
    examples_index_text: str


@dataclass
class DiffReport:
    current_version: str
    scraped_version: str
    new_modules: list[str]
    changed_signatures: dict[str, list[str]]
    new_metrics: dict[str, list[str]]
    enum_changes: dict[str, list[str]]
    new_examples: list[str]
    removed_examples: list[str]
    staleness: str


def parse_sdk_version(html: str) -> str:
    patterns = [
        r"Rhino SDK\s+(\d+\.\d+\.\d+)\s+documentation",
        r"theme_switcher_version_match\s*=\s*['\"]v?(\d+\.\d+\.\d+)['\"]",
        r"SDK Version:\s*(\d+\.\d+\.\d+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, html, flags=re.IGNORECASE)
        if match:
            return match.group(1)
    return ""


def extract_modules_from_py_modindex(html: str) -> list[str]:
    modules = re.findall(r"#module-([A-Za-z0-9_\.]+)", html)
    return sorted(dict.fromkeys(unescape(module) for module in modules))


def strip_tags(html_fragment: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html_fragment)
    return re.sub(r"\s+", " ", unescape(text)).strip()


def normalize_signature(text: str) -> str:
    text = text.replace(" ( ", "(").replace(" )", ")")
    text = re.sub(r"\s*,\s*", ", ", text)
    text = re.sub(r"\s*=\s*", "=", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_signatures_from_autoapi(html: str) -> list[str]:
    signatures = []
    pattern = re.compile(
        r"<dt[^>]*class=\"[^\"]*\bsig sig-object py\b[^\"]*\"[^>]*>(.*?)</dt>",
        flags=re.DOTALL,
    )
    for fragment in pattern.findall(html):
        signature = normalize_signature(strip_tags(fragment))
        if "(" in signature and ")" in signature and signature not in signatures:
            signatures.append(signature)
    return signatures


def extract_enum_members_from_html(html: str) -> dict[str, list[str]]:
    matches = re.findall(r"id=\"[^\"]*\.([A-Z][A-Za-z0-9]+)\.([A-Z][A-Z0-9_]+)\"", html)
    enums: dict[str, list[str]] = {}
    for enum_name, member in matches:
        enums.setdefault(enum_name, [])
        if member not in enums[enum_name]:
            enums[enum_name].append(member)
    return dict(sorted(enums.items()))


def slug_from_module_path(module_path: str) -> str:
    return module_path.split(".")[-1]


def normalize_example_name(name: str) -> str:
    value = Path(name).stem.replace("-", "_").lower()
    for suffix in ("_example", "_examples"):
        if value.endswith(suffix):
            value = value[: -len(suffix)]
    return value


def load_context_snapshot(repo_root: Path) -> ContextSnapshot:
    context_dir = repo_root / "context"
    sdk_reference_text = (context_dir / "sdk_reference.md").read_text(encoding="utf-8")
    metrics_reference_text = (context_dir / "metrics_reference.md").read_text(encoding="utf-8")
    examples_index_text = (context_dir / "examples" / "INDEX.md").read_text(encoding="utf-8")

    version_match = re.search(r"SDK Version:\s*(\d+\.\d+\.\d+)", sdk_reference_text)
    return ContextSnapshot(
        sdk_version=version_match.group(1) if version_match else "",
        sdk_reference_text=sdk_reference_text,
        metrics_reference_text=metrics_reference_text,
        examples_index_text=examples_index_text,
    )


def module_is_documented(module_path: str, sdk_reference_text: str) -> bool:
    slug = slug_from_module_path(module_path).replace("_", " ")
    haystack = sdk_reference_text.lower()
    return slug in haystack or slug.replace(" ", "") in haystack.replace("_", "")


def build_diff_report(scraped: ScrapeSnapshot, current: ContextSnapshot) -> DiffReport:
    new_modules = [
        module_path
        for module_path in scraped.modules
        if module_path.startswith("rhino_health.lib.endpoints.")
        and module_path.count(".") == 3
        and not module_is_documented(module_path, current.sdk_reference_text)
    ]

    changed_signatures: dict[str, list[str]] = {}
    for section, signatures in scraped.endpoint_signatures.items():
        missing = [
            signature for signature in signatures if signature not in current.sdk_reference_text
        ]
        if missing:
            changed_signatures[section] = missing

    new_metrics: dict[str, list[str]] = {}
    for section, signatures in scraped.metric_signatures.items():
        missing = [
            signature for signature in signatures if signature not in current.metrics_reference_text
        ]
        if missing:
            new_metrics[section] = missing

    enum_changes: dict[str, list[str]] = {}
    for enum_name, members in scraped.enum_members.items():
        missing = [member for member in members if member not in current.sdk_reference_text]
        if missing:
            enum_changes[enum_name] = missing

    current_examples = set(
        normalize_example_name(name)
        for name in re.findall(r"([A-Za-z0-9_\-]+\.(?:py|ipynb))", current.examples_index_text)
    )
    scraped_examples_by_stem = {}
    for name in scraped.example_files:
        if name.lower() == "readme.md":
            continue
        normalized = normalize_example_name(name)
        if normalized:
            scraped_examples_by_stem[normalized] = name
    scraped_example_stems = set(scraped_examples_by_stem)

    new_examples = [
        scraped_examples_by_stem[stem]
        for stem in sorted(scraped_example_stems - current_examples)
    ]
    removed_examples = sorted(current_examples - scraped_example_stems)

    total_changes = (
        len(new_modules)
        + sum(len(values) for values in changed_signatures.values())
        + sum(len(values) for values in new_metrics.values())
        + sum(len(values) for values in enum_changes.values())
        + len(new_examples)
        + len(removed_examples)
        + int(scraped.sdk_version != current.sdk_version)
    )
    if total_changes >= 12:
        staleness = "high"
    elif total_changes >= 4:
        staleness = "medium"
    else:
        staleness = "low"

    return DiffReport(
        current_version=current.sdk_version,
        scraped_version=scraped.sdk_version,
        new_modules=new_modules,
        changed_signatures=changed_signatures,
        new_metrics=new_metrics,
        enum_changes=enum_changes,
        new_examples=new_examples,
        removed_examples=removed_examples,
        staleness=staleness,
    )


def render_report_markdown(report: DiffReport) -> str:
    lines = [
        f"# SDK Doc Sync Report — {date.today().isoformat()}",
        "",
        f"> Current context version: {report.current_version or 'unknown'}",
        f"> Scraped docs version: {report.scraped_version or 'unknown'}",
        f"> Staleness: {report.staleness.upper()}",
        "",
    ]

    if report.current_version != report.scraped_version:
        lines.extend(
            [
                "## Version Change",
                f"SDK version bumped from {report.current_version or 'unknown'} to {report.scraped_version or 'unknown'}",
                "",
            ]
        )

    lines.append("## New Modules")
    if report.new_modules:
        lines.extend(f"- `{module_path}`" for module_path in report.new_modules)
    else:
        lines.append("- None detected")
    lines.append("")

    lines.append("## Changed Signatures")
    if report.changed_signatures:
        for section, signatures in sorted(report.changed_signatures.items()):
            lines.append(f"### {section}")
            lines.extend(f"- `{signature}`" for signature in signatures)
    else:
        lines.append("- None detected")
    lines.append("")

    lines.append("## New Metrics")
    if report.new_metrics:
        for section, signatures in sorted(report.new_metrics.items()):
            lines.append(f"### {section}")
            lines.extend(f"- `{signature}`" for signature in signatures)
    else:
        lines.append("- None detected")
    lines.append("")

    lines.append("## Enum Changes")
    if report.enum_changes:
        for enum_name, members in sorted(report.enum_changes.items()):
            lines.append(f"### {enum_name}")
            lines.extend(f"- `{member}`" for member in members)
    else:
        lines.append("- None detected")
    lines.append("")

    lines.append("## New Examples")
    if report.new_examples:
        lines.extend(f"- `{name}`" for name in report.new_examples)
    else:
        lines.append("- None detected")
    lines.append("")

    lines.append("## Removed / Missing Examples")
    if report.removed_examples:
        lines.extend(f"- `{name}`" for name in report.removed_examples)
    else:
        lines.append("- None detected")
    lines.append("")

    lines.extend(
        [
            "## Suggested Actions",
            "1. Review the affected `context/` sections and update curated summaries.",
            "2. Run `./scripts/sync-context.sh` after updating `context/`.",
            "3. Re-run `doc_sync.py --report` to confirm the remaining diff.",
            "",
        ]
    )
    return "\n".join(lines)


def fetch_text(url: str) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    with urlopen(request, timeout=DEFAULT_TIMEOUT_SECONDS) as response:
        return response.read().decode("utf-8")


def cache_path_for_url(cache_dir: Path, url: str) -> Path:
    parsed = urlparse(url)
    safe_path = parsed.path.lstrip("/") or "index"
    file_path = cache_dir / safe_path
    if not file_path.suffix:
        file_path = file_path / "index.html"
    return file_path


def write_cached_payload(cache_dir: Path, url: str, content: str) -> Path:
    path = cache_path_for_url(cache_dir, url)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def extract_autoapi_page_links(py_modindex_html: str) -> tuple[dict[str, str], dict[str, str]]:
    link_matches = re.findall(r'href="([^"]+)"', py_modindex_html)
    endpoint_pages: dict[str, str] = {}
    metric_pages: dict[str, str] = {}
    for href in link_matches:
        if not href.startswith("autoapi/") or not href.endswith(".html"):
            continue
        absolute = urljoin(BASE_DOCS_URL, href)
        if "/lib/endpoints/" in href and href.endswith("/index.html"):
            endpoint_pages[slug_from_module_path(href.rstrip("/").split("/")[-2])] = absolute
        if "/lib/metrics/" in href and href.endswith("/index.html"):
            metric_pages[slug_from_module_path(href.rstrip("/").split("/")[-2])] = absolute
    return dict(sorted(endpoint_pages.items())), dict(sorted(metric_pages.items()))


def scrape_remote_snapshot(cache_dir: Path) -> ScrapeSnapshot:
    cache_dir.mkdir(parents=True, exist_ok=True)

    index_url = urljoin(BASE_DOCS_URL, "index.html")
    py_modindex_url = urljoin(BASE_DOCS_URL, "py-modindex.html")
    genindex_url = urljoin(BASE_DOCS_URL, "genindex.html")

    index_html = fetch_text(index_url)
    py_modindex_html = fetch_text(py_modindex_url)
    genindex_html = fetch_text(genindex_url)

    write_cached_payload(cache_dir, index_url, index_html)
    write_cached_payload(cache_dir, py_modindex_url, py_modindex_html)
    write_cached_payload(cache_dir, genindex_url, genindex_html)

    sdk_version = parse_sdk_version(index_html)
    modules = extract_modules_from_py_modindex(py_modindex_html)
    endpoint_pages, metric_pages = extract_autoapi_page_links(py_modindex_html)

    endpoint_signatures: dict[str, list[str]] = {}
    metric_signatures: dict[str, list[str]] = {}
    enum_members: dict[str, list[str]] = {}

    for section, url in endpoint_pages.items():
        html = fetch_text(url)
        write_cached_payload(cache_dir, url, html)
        signatures = extract_signatures_from_autoapi(html)
        if signatures:
            endpoint_signatures[section] = signatures
        for enum_name, members in extract_enum_members_from_html(html).items():
            enum_members.setdefault(enum_name, [])
            for member in members:
                if member not in enum_members[enum_name]:
                    enum_members[enum_name].append(member)

    for section, url in metric_pages.items():
        html = fetch_text(url)
        write_cached_payload(cache_dir, url, html)
        signatures = extract_signatures_from_autoapi(html)
        if signatures:
            metric_signatures[section] = signatures

    examples_json = fetch_text(GITHUB_EXAMPLES_API)
    write_cached_payload(cache_dir, GITHUB_EXAMPLES_API, examples_json)
    payload = json.loads(examples_json)
    example_files = sorted(item["name"] for item in payload if isinstance(item, dict) and "name" in item)

    snapshot = ScrapeSnapshot(
        sdk_version=sdk_version,
        modules=modules,
        endpoint_signatures=dict(sorted(endpoint_signatures.items())),
        metric_signatures=dict(sorted(metric_signatures.items())),
        enum_members=dict(sorted(enum_members.items())),
        example_files=example_files,
    )
    write_snapshot_json(cache_dir, snapshot)
    return snapshot


def write_snapshot_json(cache_dir: Path, snapshot: ScrapeSnapshot) -> Path:
    path = cache_dir / "latest-snapshot.json"
    path.write_text(json.dumps(asdict(snapshot), indent=2, sort_keys=True), encoding="utf-8")
    return path


def load_cached_snapshot(cache_dir: Path) -> ScrapeSnapshot:
    path = cache_dir / "latest-snapshot.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    return ScrapeSnapshot(**payload)


def write_report(report: DiffReport, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_report_markdown(report), encoding="utf-8")
    return path


def apply_safe_updates(repo_root: Path, report: DiffReport) -> list[str]:
    touched: list[str] = []
    sdk_reference_path = repo_root / "context" / "sdk_reference.md"
    if sdk_reference_path.exists() and report.scraped_version:
        original = sdk_reference_path.read_text(encoding="utf-8")
        updated = re.sub(
            r"(SDK Version:\s*)(\d+\.\d+\.\d+)",
            rf"\g<1>{report.scraped_version}",
            original,
            count=1,
        )
        if updated != original:
            sdk_reference_path.write_text(updated, encoding="utf-8")
            touched.append(str(sdk_reference_path))

    root_skill_path = repo_root / "SKILL.md"
    if root_skill_path.exists() and report.scraped_version:
        major_minor = ".".join(report.scraped_version.split(".")[:2])
        original = root_skill_path.read_text(encoding="utf-8")
        updated = re.sub(
            r"v\d+\.\d+\.x",
            f"v{major_minor}.x",
            original,
            count=1,
        )
        if updated != original:
            root_skill_path.write_text(updated, encoding="utf-8")
            touched.append(str(root_skill_path))

    return touched


def default_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_cache_dir(repo_root: Path) -> Path:
    return repo_root / "tools" / "doc-sync" / ".cache"


def default_report_path(repo_root: Path) -> Path:
    return repo_root / "tools" / "doc-sync" / "reports" / f"{date.today().isoformat()}.md"


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--scrape", action="store_true", help="Fetch remote docs and cache them")
    mode_group.add_argument("--diff", action="store_true", help="Diff cached docs against context/")
    mode_group.add_argument("--report", action="store_true", help="Scrape, diff, and write a markdown report")
    mode_group.add_argument(
        "--apply",
        action="store_true",
        help="Apply safe metadata updates derived from the cached or freshly scraped report",
    )
    parser.add_argument("--repo-root", type=Path, help="Path to the rhino-sdk repo root")
    parser.add_argument("--cache-dir", type=Path, help="Override the scrape cache directory")
    parser.add_argument("--report-path", type=Path, help="Override the markdown report path")
    return parser.parse_args(list(argv))


def print_json(data: dict[str, object]) -> None:
    print(json.dumps(data, indent=2, sort_keys=True))


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    repo_root = (args.repo_root or default_repo_root()).resolve()
    cache_dir = (args.cache_dir or default_cache_dir(repo_root)).resolve()
    report_path = (args.report_path or default_report_path(repo_root)).resolve()

    try:
        if args.scrape:
            snapshot = scrape_remote_snapshot(cache_dir)
            print_json(
                {
                    "cache_dir": str(cache_dir),
                    "cached_at": datetime.now(timezone.utc).isoformat(),
                    "example_files": len(snapshot.example_files),
                    "metric_sections": len(snapshot.metric_signatures),
                    "modules": len(snapshot.modules),
                    "sdk_version": snapshot.sdk_version,
                }
            )
            return 0

        if args.report:
            snapshot = scrape_remote_snapshot(cache_dir)
            report = build_diff_report(snapshot, load_context_snapshot(repo_root))
            output_path = write_report(report, report_path)
            print_json(
                {
                    "report_path": str(output_path),
                    "scraped_version": report.scraped_version,
                    "staleness": report.staleness,
                }
            )
            return 0

        if args.diff:
            report = build_diff_report(load_cached_snapshot(cache_dir), load_context_snapshot(repo_root))
            print_json(asdict(report))
            return 0

        if args.apply:
            snapshot = (
                load_cached_snapshot(cache_dir)
                if (cache_dir / "latest-snapshot.json").exists()
                else scrape_remote_snapshot(cache_dir)
            )
            report = build_diff_report(snapshot, load_context_snapshot(repo_root))
            touched = apply_safe_updates(repo_root, report)
            print_json(
                {
                    "applied_files": touched,
                    "report_path": str(write_report(report, report_path)),
                    "scraped_version": report.scraped_version,
                }
            )
            return 0
    except FileNotFoundError as exc:
        print(f"ERROR: Missing file: {exc}", file=sys.stderr)
    except (HTTPError, URLError, TimeoutError) as exc:
        print(f"ERROR: Network request failed: {exc}", file=sys.stderr)
    except json.JSONDecodeError as exc:
        print(f"ERROR: Invalid JSON payload: {exc}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
