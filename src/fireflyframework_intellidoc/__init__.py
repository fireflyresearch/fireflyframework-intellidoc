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

"""fireflyframework-intellidoc — Intelligent Document Processing framework.

Built on top of pyfly and fireflyframework-genai, this package provides
a VLM-first, catalog-driven document processing pipeline with hexagonal
architecture.

Key components:
    - **Catalog**: Document type, validator, and fields catalog management
    - **Pipeline**: Ingest → Preprocess → Split → Classify → Extract → Validate → Persist
    - **Results**: Job tracking, result retrieval, analytics
    - **Observability**: Domain events, metrics, webhooks
"""

from fireflyframework_intellidoc._version import __version__
from fireflyframework_intellidoc.catalog.domain.catalog_field import (
    CatalogField,
    FieldValidationRule,
)
from fireflyframework_intellidoc.config import IntelliDocConfig
from fireflyframework_intellidoc.results.exposure.schemas import TargetSchema
from fireflyframework_intellidoc.types import (
    DocumentBoundary,
    DocumentConfidence,
    DocumentNature,
    FieldType,
    FileReference,
    JobStatus,
    PageImage,
    ValidatorSeverity,
    ValidatorType,
)

__all__ = [
    "__version__",
    "CatalogField",
    "DocumentBoundary",
    "DocumentConfidence",
    "DocumentNature",
    "FieldType",
    "FieldValidationRule",
    "FileReference",
    "IntelliDocConfig",
    "JobStatus",
    "PageImage",
    "TargetSchema",
    "ValidatorSeverity",
    "ValidatorType",
]
