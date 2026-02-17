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

"""Master auto-configuration for IntelliDoc.

Registers all core beans when IntelliDoc is enabled via configuration.
Module-specific auto-configurations (ingestion, storage) are registered
separately through their own entry points.
"""

from __future__ import annotations

from pyfly.container.bean import bean
from pyfly.container.stereotypes import configuration
from pyfly.context.conditions import conditional_on_property

from fireflyframework_intellidoc.config import IntelliDocConfig
from fireflyframework_intellidoc.observability.metrics import MetricsCollector
from fireflyframework_intellidoc.splitting.ports.outbound import (
    DocumentSplitterPort,
)
from fireflyframework_intellidoc.splitting.strategies.page_based import (
    PageBasedSplitter,
)
from fireflyframework_intellidoc.splitting.strategies.visual import VisualSplitter
from fireflyframework_intellidoc.validation.engine import ValidationEngine
from fireflyframework_intellidoc.validation.ports.outbound import ValidatorPort
from fireflyframework_intellidoc.validation.validators.business_rule_validators import (
    BusinessRuleValidator,
)
from fireflyframework_intellidoc.validation.validators.completeness_validators import (
    CompletenessValidator,
)
from fireflyframework_intellidoc.validation.validators.cross_field_validators import (
    CrossFieldValidator,
)
from fireflyframework_intellidoc.validation.validators.format_validators import (
    FormatValidator,
)
from fireflyframework_intellidoc.validation.validators.visual_validators import (
    VisualValidator,
)


@configuration
@conditional_on_property(
    "pyfly.intellidoc.enabled", having_value="true"
)
class IntelliDocAutoConfiguration:
    """Master auto-configuration for IntelliDoc."""

    @bean
    def intellidoc_config(self) -> IntelliDocConfig:
        return IntelliDocConfig()

    @bean
    def metrics_collector(self) -> MetricsCollector:
        return MetricsCollector()

    # ── Splitting Strategies ─────────────────────────────────────────

    @bean
    def page_based_splitter(self) -> DocumentSplitterPort:
        return PageBasedSplitter()

    @bean
    def visual_splitter(self, config: IntelliDocConfig) -> DocumentSplitterPort:
        return VisualSplitter(config)

    # ── Validators ───────────────────────────────────────────────────

    @bean
    def format_validator(self) -> ValidatorPort:
        return FormatValidator()

    @bean
    def cross_field_validator(self) -> ValidatorPort:
        return CrossFieldValidator()

    @bean
    def visual_validator(self, config: IntelliDocConfig) -> ValidatorPort:
        return VisualValidator(config)

    @bean
    def business_rule_validator(self) -> ValidatorPort:
        return BusinessRuleValidator()

    @bean
    def completeness_validator(self) -> ValidatorPort:
        return CompletenessValidator()

    @bean
    def validation_engine(
        self, validators: list[ValidatorPort]
    ) -> ValidationEngine:
        return ValidationEngine(validators)
