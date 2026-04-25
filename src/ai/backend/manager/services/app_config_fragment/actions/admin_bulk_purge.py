from __future__ import annotations

from dataclasses import dataclass, field
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action.bulk import BaseBulkAction, BaseBulkActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config_fragment.bulk_types import (
    AppConfigFragmentBulkItemError,
)
from ai.backend.manager.data.app_config_fragment.types import AppConfigFragmentKey


@dataclass
class AdminBulkPurgeAppConfigFragmentsAction(BaseBulkAction[AppConfigFragmentKey]):
    """`keys` carries the parsed natural keys.

    `entity_ids` is empty — see
    `AdminBulkCreateAppConfigFragmentsAction` for the convention.
    """

    keys: list[AppConfigFragmentKey] = field(default_factory=list)

    @override
    def typed_entity_ids(self) -> list[AppConfigFragmentKey]:
        return list(self.keys)

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.APP_CONFIG

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE


@dataclass
class AdminBulkPurgeAppConfigFragmentsActionResult(BaseBulkActionResult):
    purged: list[AppConfigFragmentKey]
    failed: list[AppConfigFragmentBulkItemError]

    @override
    def entity_ids(self) -> list[str]:
        return []
