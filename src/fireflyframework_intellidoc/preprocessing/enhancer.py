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

"""Image quality enhancement for document pre-processing.

Provides denoising, contrast adjustment, and sharpening to improve
VLM extraction accuracy on low-quality scans.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


async def enhance_quality(
    image_path: Path,
    *,
    denoise: bool = True,
    contrast: bool = True,
    sharpen: bool = False,
) -> Path:
    """Apply enhancement filters to a document image.

    Modifies the image in-place and returns the same path.
    """
    from PIL import Image, ImageEnhance, ImageFilter

    enhancements: list[str] = []

    with Image.open(image_path) as img:
        if img.mode != "RGB":
            img = img.convert("RGB")

        if denoise:
            img = img.filter(ImageFilter.MedianFilter(size=3))
            enhancements.append("denoise")

        if contrast:
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.3)
            enhancements.append("contrast")

        if sharpen:
            img = img.filter(ImageFilter.SHARPEN)
            enhancements.append("sharpen")

        img.save(str(image_path))

    if enhancements:
        logger.info(
            "Applied enhancements [%s] to %s",
            ", ".join(enhancements),
            image_path.name,
        )
    return image_path
