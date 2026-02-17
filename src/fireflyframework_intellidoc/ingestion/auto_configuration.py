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

"""Auto-configuration for file ingestion adapters.

Registers :class:`FileSourcePort` adapters based on configuration
properties and available dependencies.
"""

from __future__ import annotations

from pyfly.container.bean import bean
from pyfly.container.stereotypes import configuration
from pyfly.context.conditions import conditional_on_property

from fireflyframework_intellidoc.config import IntelliDocConfig
from fireflyframework_intellidoc.ingestion.adapters.local import (
    LocalFileSourceAdapter,
)
from fireflyframework_intellidoc.ingestion.adapters.url import (
    UrlFileSourceAdapter,
)
from fireflyframework_intellidoc.ingestion.ports.outbound import FileSourcePort


@configuration
class IngestionAutoConfiguration:
    """Wires file source adapters based on config flags."""

    @bean
    @conditional_on_property(
        "pyfly.intellidoc.ingestion_local_enabled", having_value="true"
    )
    def local_file_source(self) -> FileSourcePort:
        return LocalFileSourceAdapter()

    @bean
    @conditional_on_property(
        "pyfly.intellidoc.ingestion_url_enabled", having_value="true"
    )
    def url_file_source(self, config: IntelliDocConfig) -> FileSourcePort:
        return UrlFileSourceAdapter(
            timeout=float(config.ingestion_timeout),
            temp_dir=config.temp_dir,
        )

    @bean
    @conditional_on_property(
        "pyfly.intellidoc.ingestion_s3_enabled", having_value="true"
    )
    def s3_file_source(self, config: IntelliDocConfig) -> FileSourcePort:
        from fireflyframework_intellidoc.ingestion.adapters.s3 import (
            S3FileSourceAdapter,
        )

        return S3FileSourceAdapter(
            region=config.s3_region,
            access_key=config.s3_access_key,
            secret_key=config.s3_secret_key,
            endpoint_url=config.s3_endpoint_url,
            temp_dir=config.temp_dir,
        )

    @bean
    @conditional_on_property(
        "pyfly.intellidoc.ingestion_azure_enabled", having_value="true"
    )
    def azure_file_source(self, config: IntelliDocConfig) -> FileSourcePort:
        from fireflyframework_intellidoc.ingestion.adapters.azure_blob import (
            AzureBlobFileSourceAdapter,
        )

        return AzureBlobFileSourceAdapter(
            connection_string=config.azure_connection_string,
            account_url=config.azure_account_url,
            temp_dir=config.temp_dir,
        )

    @bean
    @conditional_on_property(
        "pyfly.intellidoc.ingestion_gcs_enabled", having_value="true"
    )
    def gcs_file_source(self, config: IntelliDocConfig) -> FileSourcePort:
        from fireflyframework_intellidoc.ingestion.adapters.gcs import (
            GCSFileSourceAdapter,
        )

        return GCSFileSourceAdapter(
            project_id=config.gcs_project_id,
            credentials_path=config.gcs_credentials_path,
            temp_dir=config.temp_dir,
        )
