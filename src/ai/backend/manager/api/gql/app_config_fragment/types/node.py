"""AppConfigFragment GQL output type."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from strawberry.scalars import JSON

from ai.backend.common.dto.manager.v2.app_config_fragment.response import AppConfigFragmentNode
from ai.backend.common.dto.manager.v2.app_config_fragment.types import AppConfigScopeType
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_field,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticOutputMixin

# The shared DTO enum is auto-registered by Strawberry the first time it
# is referenced as a typed field. Re-export under the ``GQL`` suffix so
# other modules can write `from ... import AppConfigScopeTypeGQL`. Calling
# `strawberry.enum(...)` here would clash with that auto-registration
# under the same `"AppConfigScopeType"` name.
AppConfigScopeTypeGQL = AppConfigScopeType


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Raw per-scope app-config fragment.",
    ),
    model=AppConfigFragmentNode,
    name="AppConfigFragment",
)
class AppConfigFragmentGQL(PydanticOutputMixin[AppConfigFragmentNode]):
    id: UUID = gql_field(description="Fragment row UUID.")
    scope_type: AppConfigScopeType = gql_field(description="Scope type.")
    scope_id: str = gql_field(description="Scope id.")
    name: str = gql_field(description="Policy name (FK to app_config_policies).")
    config: JSON | None = gql_field(description="Raw configuration payload, or null.")
    created_at: datetime = gql_field(description="Creation timestamp.")
    updated_at: datetime | None = gql_field(description="Last update timestamp.")
