#!/usr/bin/env python3
"""Export a local HTML report to PDF and PNG/JPG with server-friendly Python deps.

Preferred dependencies:
  pip install playwright
  python -m playwright install chromium

Optional PDF-first backend:
  pip install weasyprint pymupdf pillow
"""

from __future__ import annotations

import argparse
from pathlib import Path


def require_weasy_deps():
    try:
        import fitz  # type: ignore
        from PIL import Image  # type: ignore
        from weasyprint import HTML  # type: ignore
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Missing dependency. Install with: pip install weasyprint pymupdf pillow"
        ) from exc
    return HTML, fitz, Image


def render_pdf_to_images(fitz, pdf_path: Path, dpi: int):
    doc = fitz.open(pdf_path)
    matrix = fitz.Matrix(dpi / 72, dpi / 72)
    images = []
    for page in doc:
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        images.append((pix.width, pix.height, pix.samples))
    doc.close()
    return images


def save_long_image(Image, page_images, output: Path, fmt: str, gap: int = 24):
    pil_images = [Image.frombytes("RGB", (w, h), samples) for w, h, samples in page_images]
    width = max(img.width for img in pil_images)
    height = sum(img.height for img in pil_images) + gap * (len(pil_images) - 1)
    canvas = Image.new("RGB", (width, height), "white")
    y = 0
    for img in pil_images:
        canvas.paste(img, ((width - img.width) // 2, y))
        y += img.height + gap
    if fmt.lower() in {"jpg", "jpeg"}:
        canvas.save(output, quality=92, optimize=True)
    else:
        canvas.save(output)


def export_with_weasyprint(args) -> list[Path]:
    HTML, fitz, Image = require_weasy_deps()
    html_path = args.html.resolve()
    pdf_path = (args.pdf or html_path.with_suffix(".pdf")).resolve()
    HTML(filename=str(html_path), base_url=str(html_path.parent)).write_pdf(str(pdf_path))
    outputs = [pdf_path]
    if args.png or args.jpg:
        page_images = render_pdf_to_images(fitz, pdf_path, args.dpi)
        if args.png:
            save_long_image(Image, page_images, args.png.resolve(), "png")
            outputs.append(args.png.resolve())
        if args.jpg:
            save_long_image(Image, page_images, args.jpg.resolve(), "jpg")
            outputs.append(args.jpg.resolve())
    return outputs


def export_with_playwright(args) -> list[Path]:
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Missing dependency. Install with: pip install playwright && python -m playwright install chromium"
        ) from exc

    html_path = args.html.resolve()
    pdf_path = (args.pdf or html_path.with_suffix(".pdf")).resolve()
    outputs = []

    with sync_playwright() as p:
        launch_kwargs = {"headless": True}
        if args.browser_executable:
            launch_kwargs["executable_path"] = str(args.browser_executable)
        browser = p.chromium.launch(**launch_kwargs)
        page = browser.new_page(viewport={"width": args.viewport_width, "height": args.viewport_height})
        page.goto(html_path.as_uri(), wait_until="networkidle")
        if args.pdf:
            page.pdf(
                path=str(pdf_path),
                format="A4",
                print_background=True,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            )
            outputs.append(pdf_path)
        if args.png:
            page.screenshot(path=str(args.png.resolve()), full_page=True, type="png")
            outputs.append(args.png.resolve())
        if args.jpg:
            page.screenshot(path=str(args.jpg.resolve()), full_page=True, type="jpeg", quality=92)
            outputs.append(args.jpg.resolve())
        browser.close()
    return outputs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("html", type=Path)
    parser.add_argument("--pdf", type=Path)
    parser.add_argument("--png", type=Path)
    parser.add_argument("--jpg", type=Path)
    parser.add_argument("--dpi", type=int, default=160)
    parser.add_argument("--backend", choices=["auto", "playwright", "weasyprint"], default="auto")
    parser.add_argument("--browser-executable", type=Path)
    parser.add_argument("--viewport-width", type=int, default=1440)
    parser.add_argument("--viewport-height", type=int, default=900)
    args = parser.parse_args()

    if not args.pdf and not args.png and not args.jpg:
        raise SystemExit("Provide at least one output: --pdf, --png, or --jpg")

    outputs: list[Path]
    if args.backend == "playwright":
        outputs = export_with_playwright(args)
    elif args.backend == "weasyprint":
        outputs = export_with_weasyprint(args)
    else:
        try:
            outputs = export_with_weasyprint(args)
        except Exception as weasy_error:
            try:
                outputs = export_with_playwright(args)
            except Exception as playwright_error:
                raise SystemExit(
                    "Both export backends failed.\n"
                    f"WeasyPrint error: {weasy_error}\n"
                    f"Playwright error: {playwright_error}"
                )

    for output in outputs:
        print(output)


if __name__ == "__main__":
    main()
