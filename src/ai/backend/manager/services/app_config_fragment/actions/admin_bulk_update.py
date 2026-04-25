from __future__ import annotations

from dataclasses import dataclass, field
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action.bulk import BaseBulkAction, BaseBulkActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config_fragment.bulk_types import (
    AppConfigFragmentBulkItem,
    AppConfigFragmentBulkItemError,
)
from ai.backend.manager.data.app_config_fragment.types import AppConfigFragmentData


@dataclass
class AdminBulkUpdateAppConfigFragmentsAction(BaseBulkAction[AppConfigFragmentBulkItem]):
    """See `AdminBulkCreateAppConfigFragmentsAction` for the
    `entity_ids` / `items` convention."""

    items: list[AppConfigFragmentBulkItem] = field(default_factory=list)

    @override
    def typed_entity_ids(self) -> list[AppConfigFragmentBulkItem]:
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
class AdminBulkUpdateAppConfigFragmentsActionResult(BaseBulkActionResult):
    updated: list[AppConfigFragmentData]
    failed: list[AppConfigFragmentBulkItemError]

    @override
    def entity_ids(self) -> list[str]:
        return [str(fragment.id) for fragment in self.updated]
