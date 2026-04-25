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
class AdminBulkCreateAppConfigFragmentsAction(BaseBulkAction[AppConfigFragmentBulkItem]):
    """Bulk-create rows. `items` carries the per-item payloads.

    `entity_ids` is empty: row ids do not exist at action-creation time
    and we do not substitute the natural key (the natural key is not
    what the framework's RBAC validators expect). Validators that need
    to filter creates would have to operate on `items` directly.
    """

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
        return ActionOperationType.CREATE


@dataclass
class AdminBulkCreateAppConfigFragmentsActionResult(BaseBulkActionResult):
    created: list[AppConfigFragmentData]
    failed: list[AppConfigFragmentBulkItemError]

    @override
    def entity_ids(self) -> list[str]:
        return [str(fragment.id) for fragment in self.created]
