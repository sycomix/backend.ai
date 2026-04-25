"""AppConfig (merged view) GQL output types."""

from __future__ import annotations

from uuid import UUID

from strawberry.scalars import JSON

from ai.backend.common.dto.manager.v2.app_config.response import AppConfigNode
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.app_config_fragment.types.node import AppConfigFragmentGQL
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_field,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticOutputMixin


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Merged per-user AppConfig view. `fragments` are ordered "
            "low → high merge priority; `config` is the deep-merge result and is "
            "null when every contributing fragment is empty."
        ),
    ),
    model=AppConfigNode,
    name="AppConfig",
)
class AppConfigGQL(PydanticOutputMixin[AppConfigNode]):
    user_id: UUID = gql_field(description="Target user's UUID.")
    name: str = gql_field(description="Policy / config name.")
    fragments: list[AppConfigFragmentGQL] = gql_field(
        description="Contributing fragments in merge order (low → high).",
    )
    config: JSON | None = gql_field(
        description="Deep-merged configuration, or null when every fragment is empty.",
    )
