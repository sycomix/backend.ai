"""AppConfig (merged-view) GQL payloads for self-service bulk mutations."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.app_config.response import (
    BulkCreateMyAppConfigFragmentsPayload as BulkCreateMyPayloadDTO,
)
from ai.backend.common.dto.manager.v2.app_config.response import (
    BulkUpdateMyAppConfigFragmentsPayload as BulkUpdateMyPayloadDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.app_config.types.node import AppConfigGQL
from ai.backend.manager.api.gql.app_config_fragment.types.bulk_payloads import (
    AppConfigFragmentBulkErrorGQL,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_field,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticOutputMixin


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for `bulkCreateMyAppConfigFragments` (recomputed views).",
    ),
    model=BulkCreateMyPayloadDTO,
    name="BulkCreateMyAppConfigFragmentsPayload",
)
class BulkCreateMyAppConfigFragmentsPayloadGQL(PydanticOutputMixin[BulkCreateMyPayloadDTO]):
    created: list[AppConfigGQL] = gql_field(
        description="Recomputed merged AppConfig views for each created USER fragment.",
    )
    failed: list[AppConfigFragmentBulkErrorGQL] = gql_field(
        description="Per-item failures.",
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for `bulkUpdateMyAppConfigFragments` (recomputed views).",
    ),
    model=BulkUpdateMyPayloadDTO,
    name="BulkUpdateMyAppConfigFragmentsPayload",
)
class BulkUpdateMyAppConfigFragmentsPayloadGQL(PydanticOutputMixin[BulkUpdateMyPayloadDTO]):
    updated: list[AppConfigGQL] = gql_field(
        description="Recomputed merged AppConfig views for each updated USER fragment.",
    )
    failed: list[AppConfigFragmentBulkErrorGQL] = gql_field(
        description="Per-item failures.",
    )
