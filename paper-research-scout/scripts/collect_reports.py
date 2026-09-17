#!/usr/bin/env python3
"""Read-only local report selection and source indexing. Python 3.9+, no dependencies."""

import argparse
from datetime import date, datetime, timedelta
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit


DEFAULT_REPORTS = Path.home() / "Documents/research idea/Codex_Automated_Paper_Reader/paper-daily/reports"
URL_PATTERN = re.compile(r"https?://[^\s<>\[\]()\"']+")
DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")
ARXIV_PATTERN = re.compile(r"(?:abs|pdf|html)/(?P<id>\d{4}\.\d{4,5}|[a-z.-]+/\d{7})(?:v(?P<version>\d+))?", re.I)


def parse_date(value):
    if not DATE_PATTERN.fullmatch(value):
        raise ValueError("Expected YYYY-MM-DD: " + value)
    return date.fromisoformat(value)


def file_date(path):
    try:
        return parse_date(path.stem)
    except ValueError:
        return None


def arxiv_identity(url):
    parsed = urlsplit(url)
    if parsed.hostname not in ("arxiv.org", "www.arxiv.org", "export.arxiv.org"):
        return None
    path = parsed.path.strip("/")
    if path.endswith(".pdf"):
        path = path[:-4]
    match = ARXIV_PATTERN.fullmatch(path)
    if not match:
        return None
    return {"id": "arxiv:" + match["id"].lower(),
            "version": int(match["version"]) if match["version"] else None}


def missing_ranges(start, end, selected):
    gaps = []
    cursor = start
    for current in sorted(set(selected)):
        if current > cursor:
            gaps.append({"start": cursor.isoformat(), "end": (current - timedelta(days=1)).isoformat()})
        if current == end:
            return gaps
        cursor = current + timedelta(days=1)
    if cursor <= end:
        gaps.append({"start": cursor.isoformat(), "end": end.isoformat()})
    return gaps


def select_reports(args):
    cutoff = args.as_of or date.today()
    selection = {"as_of": cutoff.isoformat(), "missing_ranges": []}
    if args.end and not args.start:
        raise ValueError("--end requires --start")
    if args.report:
        paths = list(dict.fromkeys(Path(value).expanduser().resolve() for value in args.report))
        selection["mode"] = "explicit_paths"
    elif args.date:
        paths = [(Path(args.reports_dir).expanduser() / (args.date.isoformat() + ".md")).resolve()]
        selection.update(mode="exact_date", requested_date=args.date.isoformat())
    else:
        root = Path(args.reports_dir).expanduser().resolve()
        if not root.is_dir():
            raise ValueError("Report directory does not exist: " + str(root))
        dated = sorted((file_date(path), path) for path in root.glob("*.md")
                       if path.is_file() and file_date(path) is not None)
        if args.start:
            if not args.end or args.start > args.end:
                raise ValueError("Use both --start and --end with start <= end")
            chosen = [(day, path) for day, path in dated if args.start <= day <= args.end]
            selection.update(mode="date_range", start=args.start.isoformat(), end=args.end.isoformat(),
                             missing_ranges=missing_ranges(args.start, args.end, [day for day, _ in chosen]))
        else:
            count = args.latest if args.latest is not None else 1
            if count <= 0:
                raise ValueError("--latest must be positive")
            chosen = [(day, path) for day, path in dated if day <= cutoff][-count:]
            selection.update(mode="latest_available", requested_count=count,
                             excluded_future_dates=[day.isoformat() for day, _ in dated if day > cutoff])
        paths = [path for _, path in chosen]
    if not paths:
        raise ValueError("No reports match the requested selection; no older report was substituted")
    for path in paths:
        if not path.is_file():
            raise ValueError("Requested report does not exist: " + str(path))
    return paths, selection


def inventory(paths, selection, include_text=False):
    reports, papers, warnings = [], {}, []
    cutoff = parse_date(selection["as_of"])
    for path in paths:
        raw = path.read_bytes()
        content = raw.decode("utf-8-sig")
        day = file_date(path)
        links = []
        seen_links = set()
        for number, line in enumerate(content.splitlines(), 1):
            for match in URL_PATTERN.finditer(line):
                url = match.group(0).rstrip(".,;:!?，。；：！？】")
                if (number, url) in seen_links:
                    continue
                seen_links.add((number, url))
                identity = arxiv_identity(url)
                links.append({"line": number, "url": url, "paper": identity})
                if identity:
                    paper = papers.setdefault(identity["id"], {"id": identity["id"], "versions": [], "occurrences": []})
                    if identity["version"] not in paper["versions"]:
                        paper["versions"].append(identity["version"])
                    paper["occurrences"].append({"report": str(path), "line": number, "url": url,
                                                 "version": identity["version"]})
        report = {"path": str(path), "report_date": day.isoformat() if day else None,
                  "sha256": hashlib.sha256(raw).hexdigest(), "line_count": len(content.splitlines()),
                  "source_links": links}
        if include_text:
            report["text"] = content
        reports.append(report)
        if day and day > cutoff:
            warnings.append("Explicitly selected future-dated report: " + str(path))
        if not content.strip():
            warnings.append("Empty selected report: " + str(path))
        elif not links:
            warnings.append("No HTTP(S) source links found; read the report before inferring no papers: " + str(path))
    dates = [parse_date(item["report_date"]) for item in reports if item["report_date"]]
    if dates and max(dates) < cutoff:
        warnings.append("Newest selected report is " + max(dates).isoformat()
                        + "; selection as-of date is " + cutoff.isoformat() + ". Local reports do not establish global freshness.")
    if selection["missing_ranges"]:
        warnings.append("Some dates in the requested range have no local report; gaps were not backfilled.")
    for paper in papers.values():
        paper["versions"].sort(key=lambda version: -1 if version is None else version)
    return {"selection": selection, "reports": reports, "papers": sorted(papers.values(), key=lambda p: p["id"]),
            "warnings": warnings,
            "limits": "Link inventory only. Null version means unspecified. Verify paper identity, contents, artifacts and scientific overlap separately."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports-dir", default=str(DEFAULT_REPORTS))
    choice = parser.add_mutually_exclusive_group()
    choice.add_argument("--report", action="append", help="Explicit path; repeat to select multiple files")
    choice.add_argument("--date", type=parse_date, help="Exact filename date in reports directory")
    choice.add_argument("--latest", type=int, help="Select N latest available dated reports; default 1")
    choice.add_argument("--start", type=parse_date, help="Inclusive range start, requires --end")
    parser.add_argument("--end", type=parse_date)
    parser.add_argument("--as-of", type=parse_date)
    parser.add_argument("--include-text", action="store_true")
    args = parser.parse_args()
    try:
        paths, selection = select_reports(args)
        result = inventory(paths, selection, args.include_text)
    except (ValueError, OSError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
