"""AppConfig (merged view) GQL output types."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated
from uuid import UUID

import strawberry
from strawberry.scalars import JSON

from ai.backend.common.dto.manager.v2.app_config.response import AppConfigNode
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_field,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticOutputMixin

if TYPE_CHECKING:
    from ai.backend.manager.api.gql.app_config_fragment.types.node import AppConfigFragmentGQL


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
    # Use `strawberry.lazy()` to break the import cycle between
    # `app_config.types.node` and `app_config_fragment.types.node`:
    # the fragment package's `__init__.py` eagerly loads its resolver,
    # which imports `MyBulkCreate*` payloads back from `app_config.types`.
    fragments: list[
        Annotated[
            AppConfigFragmentGQL,
            strawberry.lazy("ai.backend.manager.api.gql.app_config_fragment.types.node"),
        ]
    ] = gql_field(
        description="Contributing fragments in merge order (low → high).",
    )
    config: JSON | None = gql_field(
        description="Deep-merged configuration, or null when every fragment is empty.",
    )
