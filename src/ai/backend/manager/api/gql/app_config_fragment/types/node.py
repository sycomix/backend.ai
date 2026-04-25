"""AppConfigFragment GQL output type."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from ai.backend.common.dto.manager.v2.app_config_fragment.response import AppConfigFragmentNode
from ai.backend.common.dto.manager.v2.app_config_fragment.types import AppConfigScopeType
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_enum,
    gql_field,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticOutputMixin

# Register the shared DTO enum as a Strawberry type.
AppConfigScopeTypeGQL = gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="App-config scope type (BEP-1052 §1).",
    ),
    AppConfigScopeType,
    name="AppConfigScopeType",
)


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Raw per-scope app-config fragment (BEP-1052 §2).",
    ),
    model=AppConfigFragmentNode,
    name="AppConfigFragment",
)
class AppConfigFragmentGQL(PydanticOutputMixin[AppConfigFragmentNode]):
    id: UUID = gql_field(description="Fragment row UUID.")
    scope_type: AppConfigScopeType = gql_field(description="Scope type.")
    scope_id: str = gql_field(description="Scope id.")
    name: str = gql_field(description="Policy name (FK to app_config_policies).")
    extra_config: dict[str, Any] | None = gql_field(
        description="Raw configuration payload, or null."
    )
    created_at: datetime = gql_field(description="Creation timestamp.")
    updated_at: datetime | None = gql_field(description="Last update timestamp.")
