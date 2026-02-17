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

"""Outbound ports for document pre-processing.

:class:`PreProcessorPort` abstracts the image manipulation operations
needed to prepare document pages for VLM analysis.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from fireflyframework_intellidoc.types import PageImage


@runtime_checkable
class PreProcessorPort(Protocol):
    """Port for document pre-processing operations."""

    async def convert_to_images(
        self,
        file_path: Path,
        *,
        dpi: int = 300,
        fmt: str = "png",
    ) -> list[PageImage]:
        """Convert a document file to page images."""
        ...

    async def detect_rotation(self, image_path: Path) -> float:
        """Detect rotation angle in degrees."""
        ...

    async def correct_rotation(self, image_path: Path, angle: float) -> Path:
        """Correct rotation and return the path to the corrected image."""
        ...

    async def enhance_quality(
        self,
        image_path: Path,
        *,
        denoise: bool = True,
        contrast: bool = True,
        sharpen: bool = False,
    ) -> Path:
        """Enhance image quality and return the path to the enhanced image."""
        ...

    async def assess_quality(self, image_path: Path) -> float:
        """Assess image quality, returning a score from 0.0 to 1.0."""
        ...
