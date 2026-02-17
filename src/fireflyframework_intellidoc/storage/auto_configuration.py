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

"""Auto-configuration for document storage adapters.

Selects the :class:`DocumentStoragePort` implementation based on the
``pyfly.intellidoc.storage_provider`` configuration property.
"""

from __future__ import annotations

from pyfly.container.bean import bean
from pyfly.container.stereotypes import configuration
from pyfly.context.conditions import conditional_on_missing_bean

from fireflyframework_intellidoc.config import IntelliDocConfig
from fireflyframework_intellidoc.storage.adapters.local import (
    LocalDocumentStorageAdapter,
)
from fireflyframework_intellidoc.storage.ports.outbound import DocumentStoragePort


@configuration
class StorageAutoConfiguration:
    """Wires a document storage adapter based on config."""

    @bean
    @conditional_on_missing_bean(DocumentStoragePort)
    def document_storage(self, config: IntelliDocConfig) -> DocumentStoragePort:
        provider = config.storage_provider

        if provider == "s3":
            from fireflyframework_intellidoc.storage.adapters.s3 import (
                S3DocumentStorageAdapter,
            )

            return S3DocumentStorageAdapter(
                bucket=config.storage_bucket,
                prefix=config.storage_prefix,
                region=config.s3_region,
                access_key=config.s3_access_key,
                secret_key=config.s3_secret_key,
                endpoint_url=config.s3_endpoint_url,
            )

        if provider == "azure_blob":
            from fireflyframework_intellidoc.storage.adapters.azure_blob import (
                AzureBlobDocumentStorageAdapter,
            )

            return AzureBlobDocumentStorageAdapter(
                container_name=config.storage_container,
                connection_string=config.azure_connection_string,
                account_url=config.azure_account_url,
                prefix=config.storage_prefix,
            )

        if provider == "gcs":
            from fireflyframework_intellidoc.storage.adapters.gcs import (
                GCSDocumentStorageAdapter,
            )

            return GCSDocumentStorageAdapter(
                bucket=config.storage_bucket,
                prefix=config.storage_prefix,
            )

        # Default: local storage
        return LocalDocumentStorageAdapter(
            base_path=config.storage_local_path,
        )
