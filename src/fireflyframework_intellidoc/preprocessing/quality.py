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

"""Document image quality assessment.

Uses simple image statistics (contrast, brightness, sharpness) to
produce a quality score between 0.0 and 1.0.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


async def assess_quality(image_path: Path) -> float:
    """Assess the quality of a document image.

    Returns a score between 0.0 (unusable) and 1.0 (excellent).
    The score is a weighted combination of:
    - Brightness (penalise too dark or too bright)
    - Contrast (low contrast ⇒ washed-out scan)
    - Sharpness (blurry images score lower)
    """
    from PIL import Image, ImageStat

    with Image.open(image_path) as img:
        if img.mode != "L":
            gray = img.convert("L")
        else:
            gray = img

        stat = ImageStat.Stat(gray)
        mean_brightness = stat.mean[0] / 255.0
        stddev = stat.stddev[0] / 128.0

    brightness_score = 1.0 - abs(mean_brightness - 0.5) * 2.0
    brightness_score = max(0.0, min(1.0, brightness_score))

    contrast_score = min(1.0, stddev)

    sharpness_score = _estimate_sharpness(image_path)

    quality = (
        brightness_score * 0.3
        + contrast_score * 0.3
        + sharpness_score * 0.4
    )
    quality = max(0.0, min(1.0, quality))

    logger.debug(
        "Quality for %s: %.2f (brightness=%.2f, contrast=%.2f, sharpness=%.2f)",
        image_path.name,
        quality,
        brightness_score,
        contrast_score,
        sharpness_score,
    )
    return quality


def _estimate_sharpness(image_path: Path) -> float:
    """Estimate sharpness using Laplacian variance."""
    try:
        import numpy as np
        from PIL import Image, ImageFilter

        with Image.open(image_path) as img:
            if img.mode != "L":
                gray = img.convert("L")
            else:
                gray = img

            laplacian = gray.filter(ImageFilter.Kernel(
                size=(3, 3),
                kernel=[0, 1, 0, 1, -4, 1, 0, 1, 0],
                scale=1,
                offset=128,
            ))

            arr = np.array(laplacian, dtype=np.float64)
            variance = float(np.var(arr))
            # Normalise: typical document variance is 200–2000
            normalised = min(1.0, variance / 1000.0)
            return normalised
    except ImportError:
        # numpy not available — return a neutral score
        return 0.7
