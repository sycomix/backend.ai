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
class BulkCreateMyAppConfigFragmentsAction(BaseBulkAction[MyAppConfigFragmentBulkItem]):
    """Self-service bulk create — scope is `USER` / `current_user.user_id`.

    The owning `user_id` is resolved from the request `ContextVar`
    (`current_user()`) inside the service, never carried on the action.
    `entity_ids` carries the per-item `name`s (USER-scope, so name
    alone is unique inside a single user).
    """

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
        return ActionOperationType.CREATE


@dataclass
class BulkCreateMyAppConfigFragmentsActionResult(BaseBulkActionResult):
    """`created` carries the recomputed merged view per successfully
    created fragment; `failed` carries per-item errors.
    """

    created: list[AppConfigData]
    failed: list[AppConfigFragmentBulkItemError]

    @override
    def entity_ids(self) -> list[str]:
        return [item.name for item in self.created]
