from __future__ import annotations

from dataclasses import dataclass, field
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action.bulk import BaseBulkAction, BaseBulkActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config.types import AppConfigData
from ai.backend.manager.data.app_config_fragment.bulk_types import (
    AppConfigFragmentBulkItemError,
    MyAppConfigFragmentBulkItem,
)


@dataclass
class MyBulkUpdateAppConfigFragmentsAction(BaseBulkAction[MyAppConfigFragmentBulkItem]):
    """Self-service bulk update — see `MyBulkCreateAppConfigFragmentsAction`."""

    items: list[MyAppConfigFragmentBulkItem] = field(default_factory=list)

    @override
    def typed_entity_ids(self) -> list[MyAppConfigFragmentBulkItem]:
        return list(self.items)

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.APP_CONFIG

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class MyBulkUpdateAppConfigFragmentsActionResult(BaseBulkActionResult):
    updated: list[AppConfigData]
    failed: list[AppConfigFragmentBulkItemError]

    @override
    def entity_ids(self) -> list[str]:
        return [item.name for item in self.updated]
