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

"""Rotation detection and correction for document images."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


async def detect_rotation(image_path: Path) -> float:
    """Detect the rotation angle of a document image.

    Uses EXIF orientation data when available, otherwise falls back
    to simple heuristic analysis.  Returns the angle in degrees
    that the image is rotated clockwise (0, 90, 180, or 270).
    """
    from PIL import Image

    with Image.open(image_path) as img:
        exif = img.getexif()
        if exif:
            orientation = exif.get(274)  # EXIF orientation tag
            angle = _orientation_to_angle(orientation)
            if angle != 0.0:
                logger.debug(
                    "Detected rotation %.1f° from EXIF for %s",
                    angle,
                    image_path.name,
                )
                return angle

    return 0.0


async def correct_rotation(image_path: Path, angle: float) -> Path:
    """Correct the rotation of an image by the given angle.

    Rotates the image counter-clockwise by ``angle`` degrees to
    produce an upright document.  Returns the path to the
    corrected image (overwrites the original).
    """
    if angle == 0.0:
        return image_path

    from PIL import Image

    with Image.open(image_path) as img:
        rotated = img.rotate(-angle, expand=True)
        rotated.save(str(image_path))

    logger.info("Corrected rotation by %.1f° for %s", angle, image_path.name)
    return image_path


def _orientation_to_angle(orientation: int | None) -> float:
    """Map EXIF orientation tag to rotation angle."""
    mapping = {
        3: 180.0,
        6: 270.0,
        8: 90.0,
    }
    return mapping.get(orientation or 0, 0.0)
