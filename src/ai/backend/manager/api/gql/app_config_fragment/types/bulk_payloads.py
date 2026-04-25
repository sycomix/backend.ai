"""AppConfigFragment bulk-mutation GQL payload types (BEP-1052 §3)."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.app_config.response import (
    BulkCreateMyAppConfigFragmentsPayload as BulkCreateMyPayloadDTO,
)
from ai.backend.common.dto.manager.v2.app_config.response import (
    BulkUpdateMyAppConfigFragmentsPayload as BulkUpdateMyPayloadDTO,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.response import (
    AdminBulkCreateAppConfigFragmentsPayload as AdminBulkCreatePayloadDTO,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.response import (
    AdminBulkPurgeAppConfigFragmentsPayload as AdminBulkPurgePayloadDTO,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.response import (
    AdminBulkUpdateAppConfigFragmentsPayload as AdminBulkUpdatePayloadDTO,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.response import (
    AppConfigFragmentBulkError as AppConfigFragmentBulkErrorDTO,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.response import (
    PurgeAppConfigFragmentKey as PurgeAppConfigFragmentKeyDTO,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.types import AppConfigScopeType
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.app_config.types.node import AppConfigGQL
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
        description="Per-item failure info for bulk Fragment mutations.",
    ),
    model=AppConfigFragmentBulkErrorDTO,
    name="AppConfigFragmentBulkError",
)
class AppConfigFragmentBulkErrorGQL(PydanticOutputMixin[AppConfigFragmentBulkErrorDTO]):
    index: int = gql_field(description="Original position in the input list.")
    scope_type: AppConfigScopeType = gql_field(description="Scope type of the failed row.")
    scope_id: str = gql_field(description="Scope id of the failed row.")
    name: str = gql_field(description="Policy name of the failed row.")
    message: str = gql_field(description="Reason for the failure.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Natural key of a purged fragment row.",
    ),
    model=PurgeAppConfigFragmentKeyDTO,
    name="PurgeAppConfigFragmentKey",
)
class PurgeAppConfigFragmentKeyGQL(PydanticOutputMixin[PurgeAppConfigFragmentKeyDTO]):
    scope_type: AppConfigScopeType = gql_field(description="Scope type.")
    scope_id: str = gql_field(description="Scope id.")
    name: str = gql_field(description="Policy name.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for `adminBulkCreateAppConfigFragments`.",
    ),
    model=AdminBulkCreatePayloadDTO,
    name="AdminBulkCreateAppConfigFragmentsPayload",
)
class AdminBulkCreateAppConfigFragmentsPayloadGQL(PydanticOutputMixin[AdminBulkCreatePayloadDTO]):
    created: list[AppConfigFragmentGQL] = gql_field(description="Created fragments.")
    failed: list[AppConfigFragmentBulkErrorGQL] = gql_field(description="Per-item failures.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for `adminBulkUpdateAppConfigFragments`.",
    ),
    model=AdminBulkUpdatePayloadDTO,
    name="AdminBulkUpdateAppConfigFragmentsPayload",
)
class AdminBulkUpdateAppConfigFragmentsPayloadGQL(PydanticOutputMixin[AdminBulkUpdatePayloadDTO]):
    updated: list[AppConfigFragmentGQL] = gql_field(description="Updated fragments.")
    failed: list[AppConfigFragmentBulkErrorGQL] = gql_field(description="Per-item failures.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for `adminBulkPurgeAppConfigFragments`.",
    ),
    model=AdminBulkPurgePayloadDTO,
    name="AdminBulkPurgeAppConfigFragmentsPayload",
)
class AdminBulkPurgeAppConfigFragmentsPayloadGQL(PydanticOutputMixin[AdminBulkPurgePayloadDTO]):
    purged: list[PurgeAppConfigFragmentKeyGQL] = gql_field(
        description="Keys of rows actually removed (absent keys are no-oped).",
    )
    failed: list[AppConfigFragmentBulkErrorGQL] = gql_field(description="Per-item failures.")


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
    failed: list[AppConfigFragmentBulkErrorGQL] = gql_field(description="Per-item failures.")


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
    failed: list[AppConfigFragmentBulkErrorGQL] = gql_field(description="Per-item failures.")
