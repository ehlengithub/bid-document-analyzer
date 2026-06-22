#!/usr/bin/env python3
"""Scan customer-facing bid deliverables for internal service pricing leaks and process wording.

The customer version may mention tender facts such as budget, bid price
requirements, bid bond, agency fee, and payment terms. It must not include the
service price we charge the customer: main-bid/cover-bid pricing, production
fees, add-on ladders, or internal quote tables.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree


DEFAULT_PATTERNS = [
    r"本项目报价结论",
    r"建议报价",
    r"制作报价",
    r"服务报价",
    r"制作费",
    r"标书制作费",
    r"普通主标",
    r"单家公司主标",
    r"常规陪标",
    r"低要求陪标",
    r"高要求陪标",
    r"主标[价费]?",
    r"陪标",
    r"一组[一二三四五六七八九十多]陪",
    r"1\s*主\s*[123一二三四五六七八九十多]\s*陪",
]

CUSTOMER_PROCESS_PATTERNS = [
    r"最新技能",
    r"重跑版",
    r"手机紧凑表格版",
    r"全文检索未见明确要求",
    r"当前日期是\s*\d{4}年\d{1,2}月\d{1,2}日",
    r"客户认知负荷",
]

SERVICE_PRICE_RANGE_PATTERNS = [
    r"900\s*[-–—]\s*1000",
    r"1000\s*[-–—]\s*1200",
    r"1200\s*[-–—]\s*1300",
    r"1200\s*[-–—]\s*1800",
    r"1300\s*[-–—]\s*1800",
    r"1600\s*[-–—]\s*2400",
    r"1600\s*[-–—]\s*2200",
    r"2200\s*[-–—]\s*3000",
    r"300\s*[-–—]\s*600",
    r"1500\+",
]

SERVICE_PRICE_CONTEXT_PATTERNS = [
    r"本项目报价结论",
    r"建议报价",
    r"制作报价",
    r"服务报价",
    r"制作费",
    r"标书制作费",
    r"商务标\s*[+＋/、和及]\s*技术标",
    r"经济标格式整理",
    r"技术标定性资料整理成文",
    r"普通主标",
    r"单家公司主标",
    r"全套主标",
    r"主标[价费]?",
    r"低要求陪标",
    r"常规陪标",
    r"高要求陪标",
    r"陪标",
    r"一组[一二三四五六七八九十多]陪",
    r"1\s*主\s*[123一二三四五六七八九十多]\s*陪",
    r"基础制作",
    r"基础价",
    r"加价项",
]

TEXT_SUFFIXES = {".txt", ".md", ".markdown", ".html", ".htm", ".csv"}
DOCX_SUFFIXES = {".docx"}
PDF_SUFFIXES = {".pdf"}


def pdf_text(path: Path) -> str:
    try:
        result = subprocess.run(
            ["pdftotext", str(path), "-"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("pdftotext is required to scan PDF files") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(exc.stderr.strip() or f"failed to read PDF: {path}") from exc
    return result.stdout


def docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        xml = archive.read("word/document.xml")
    root = ElementTree.fromstring(xml)
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    return "\n".join(node.text or "" for node in root.findall(".//w:t", ns))


def plain_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in PDF_SUFFIXES:
        return pdf_text(path)
    if suffix in DOCX_SUFFIXES:
        return docx_text(path)
    return path.read_text(encoding="utf-8", errors="ignore")


def iter_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    supported = TEXT_SUFFIXES | DOCX_SUFFIXES | PDF_SUFFIXES
    for path in paths:
        if path.is_dir():
            files.extend(p for p in path.rglob("*") if p.is_file() and p.suffix.lower() in supported)
        elif path.is_file() and path.suffix.lower() in supported:
            files.append(path)
    return sorted(set(files))


def has_service_price_context(
    text: str, start: int, end: int, compiled_context: list[re.Pattern[str]], window: int = 80
) -> bool:
    snippet = text[max(0, start - window) : min(len(text), end + window)]
    return any(pattern.search(snippet) for pattern in compiled_context)


def find_leaks(files: list[Path], patterns: list[str]) -> list[tuple[Path, str]]:
    failures: list[tuple[Path, str]] = []
    compiled = [re.compile(pattern) for pattern in patterns]
    compiled_ranges = [re.compile(pattern) for pattern in SERVICE_PRICE_RANGE_PATTERNS]
    compiled_context = [re.compile(pattern) for pattern in SERVICE_PRICE_CONTEXT_PATTERNS]
    for path in files:
        text = plain_text(path)
        for pattern in compiled:
            if pattern.search(text):
                failures.append((path, pattern.pattern))
        for pattern in compiled_ranges:
            for match in pattern.finditer(text):
                if has_service_price_context(text, match.start(), match.end(), compiled_context):
                    failures.append((path, f"{pattern.pattern} near service-pricing context"))
                    break
    return failures


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan customer-facing deliverables for internal service pricing leaks and process wording."
    )
    parser.add_argument("paths", nargs="+", type=Path, help="Customer delivery folders or files")
    parser.add_argument(
        "--pattern",
        action="append",
        default=[],
        help="Additional regex pattern to block. Can be passed multiple times.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    files = iter_files(args.paths)
    failures = find_leaks(files, DEFAULT_PATTERNS + CUSTOMER_PROCESS_PATTERNS + args.pattern)
    if failures:
        print("客户交付版含服务报价或过程话术痕迹：")
        for path, pattern in failures:
            print(f"{path}: {pattern}")
        return 1
    print(f"OK: scanned {len(files)} files; no internal service pricing or process wording found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
