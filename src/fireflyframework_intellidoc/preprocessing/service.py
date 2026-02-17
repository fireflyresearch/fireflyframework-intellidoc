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

"""Pre-processing application service.

Orchestrates the full pre-processing pipeline: page extraction,
rotation detection/correction, quality enhancement, and quality
assessment.
"""

from __future__ import annotations

import logging

from pyfly.container.stereotypes import service

from fireflyframework_intellidoc.config import IntelliDocConfig
from fireflyframework_intellidoc.exceptions import QualityTooLowException
from fireflyframework_intellidoc.preprocessing.enhancer import enhance_quality
from fireflyframework_intellidoc.preprocessing.models import PreProcessingResult
from fireflyframework_intellidoc.preprocessing.page_extractor import extract_pages
from fireflyframework_intellidoc.preprocessing.quality import assess_quality
from fireflyframework_intellidoc.preprocessing.rotation import (
    correct_rotation,
    detect_rotation,
)
from fireflyframework_intellidoc.types import FileReference

logger = logging.getLogger(__name__)


@service
class PreProcessingService:
    """Orchestrates document pre-processing."""

    def __init__(self, config: IntelliDocConfig) -> None:
        self._config = config

    async def preprocess(self, file_ref: FileReference) -> PreProcessingResult:
        """Run the full pre-processing pipeline on an ingested file.

        Steps:
        1. Extract pages (PDF → images or passthrough for images)
        2. Detect and correct rotation (if enabled)
        3. Enhance quality (if enabled)
        4. Assess quality and reject if below threshold
        """
        if file_ref.content_path is None:
            raise ValueError("FileReference must have a content_path set")

        # 1. Extract pages
        pages = await extract_pages(
            file_ref.content_path,
            dpi=self._config.default_dpi,
        )

        total_rotation = 0.0

        for page in pages:
            # 2. Rotation detection & correction
            if self._config.auto_rotate:
                angle = await detect_rotation(page.image_path)
                if angle != 0.0:
                    await correct_rotation(page.image_path, angle)
                    page.rotation_applied = angle
                    total_rotation = max(total_rotation, abs(angle))

            # 3. Quality enhancement
            if self._config.auto_enhance:
                await enhance_quality(
                    page.image_path,
                    denoise=self._config.auto_denoise,
                    contrast=True,
                )
                page.enhancements_applied.append("auto_enhance")

            # 4. Quality assessment
            quality = await assess_quality(page.image_path)
            page.quality_score = quality

        # Check overall quality
        overall_quality = (
            sum(p.quality_score for p in pages) / len(pages) if pages else 0.0
        )

        if overall_quality < self._config.quality_threshold:
            raise QualityTooLowException(
                overall_quality, self._config.quality_threshold
            )

        file_format = file_ref.content_path.suffix.lstrip(".").lower()
        is_scanned = file_format in {"png", "jpg", "jpeg", "tiff", "tif", "bmp"}

        return PreProcessingResult(
            original_file=file_ref,
            pages=pages,
            total_pages=len(pages),
            file_format=file_format,
            overall_quality=overall_quality,
            rotation_detected=total_rotation,
            is_scanned=is_scanned,
            has_text_layer=file_format == "pdf" and not is_scanned,
        )
