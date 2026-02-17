# Copyright 2026 Firefly Software Solutions Inc
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Page extraction — convert PDFs and images to individual page images."""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path

from fireflyframework_intellidoc.exceptions import PageExtractionException
from fireflyframework_intellidoc.types import PageImage

logger = logging.getLogger(__name__)


async def extract_pages(
    file_path: Path,
    *,
    dpi: int = 300,
    fmt: str = "png",
    output_dir: str | None = None,
) -> list[PageImage]:
    """Convert a document file to a list of page images.

    Supports PDF files (via pdf2image/poppler) and standard image
    formats (PNG, JPEG, TIFF, BMP, WebP, GIF).
    """
    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        return await _extract_pdf_pages(file_path, dpi=dpi, fmt=fmt, output_dir=output_dir)
    if suffix in {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp", ".gif"}:
        return await _extract_image_page(file_path, output_dir=output_dir)

    raise PageExtractionException(f"Unsupported file format: {suffix}")


async def _extract_pdf_pages(
    file_path: Path,
    *,
    dpi: int = 300,
    fmt: str = "png",
    output_dir: str | None = None,
) -> list[PageImage]:
    """Convert PDF pages to images using pdf2image."""
    try:
        from pdf2image import convert_from_path
    except ImportError as exc:
        raise PageExtractionException(
            "pdf2image is required for PDF processing. "
            "Install with: pip install fireflyframework-intellidoc[pdf]"
        ) from exc

    dest = Path(output_dir or tempfile.mkdtemp(prefix="intellidoc_pages_"))
    dest.mkdir(parents=True, exist_ok=True)

    try:
        images = convert_from_path(
            str(file_path),
            dpi=dpi,
            fmt=fmt,
            output_folder=str(dest),
        )
    except Exception as exc:
        raise PageExtractionException(str(exc)) from exc

    pages: list[PageImage] = []
    for i, img in enumerate(images, start=1):
        page_path = dest / f"page_{i:04d}.{fmt}"
        img.save(str(page_path), fmt.upper())
        pages.append(
            PageImage(
                page_number=i,
                image_path=page_path,
                width=img.width,
                height=img.height,
                dpi=dpi,
            )
        )

    logger.info("Extracted %d pages from %s", len(pages), file_path.name)
    return pages


async def _extract_image_page(
    file_path: Path,
    *,
    output_dir: str | None = None,
) -> list[PageImage]:
    """Treat a single image file as a one-page document."""
    try:
        from PIL import Image
    except ImportError as exc:
        raise PageExtractionException(
            "Pillow is required for image processing. "
            "Install with: pip install fireflyframework-intellidoc"
        ) from exc

    try:
        with Image.open(file_path) as img:
            width, height = img.size
    except Exception as exc:
        raise PageExtractionException(str(exc)) from exc

    return [
        PageImage(
            page_number=1,
            image_path=file_path,
            width=width,
            height=height,
        )
    ]
