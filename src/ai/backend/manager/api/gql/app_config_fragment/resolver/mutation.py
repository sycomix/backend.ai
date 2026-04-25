"""AppConfigFragment GQL mutation resolvers (bulk-only, BEP-1052 §3)."""

from __future__ import annotations

from strawberry import Info

from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.app_config_fragment.types import (
    AdminBulkCreateAppConfigFragmentInputGQL,
    AdminBulkCreateAppConfigFragmentsPayloadGQL,
    AdminBulkPurgeAppConfigFragmentInputGQL,
    AdminBulkPurgeAppConfigFragmentsPayloadGQL,
    AdminBulkUpdateAppConfigFragmentInputGQL,
    AdminBulkUpdateAppConfigFragmentsPayloadGQL,
    BulkCreateMyAppConfigFragmentInputGQL,
    BulkCreateMyAppConfigFragmentsPayloadGQL,
    BulkUpdateMyAppConfigFragmentInputGQL,
    BulkUpdateMyAppConfigFragmentsPayloadGQL,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_mutation,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Strict insert across any scope; each item runs in its own transaction "
            "and failures are collected per-item (admin only)."
        ),
    )
)  # type: ignore[misc]
async def admin_bulk_create_app_config_fragments(
    info: Info[StrawberryGQLContext],
    input: AdminBulkCreateAppConfigFragmentInputGQL,
) -> AdminBulkCreateAppConfigFragmentsPayloadGQL:
    check_admin_only()
    result = await info.context.adapters.app_config_fragment.admin_bulk_create(input.to_pydantic())
    return AdminBulkCreateAppConfigFragmentsPayloadGQL.from_pydantic(result)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Wholesale JSON replacement; items with no existing row are returned as failures "
            "(admin only)."
        ),
    )
)  # type: ignore[misc]
async def admin_bulk_update_app_config_fragments(
    info: Info[StrawberryGQLContext],
    input: AdminBulkUpdateAppConfigFragmentInputGQL,
) -> AdminBulkUpdateAppConfigFragmentsPayloadGQL:
    check_admin_only()
    result = await info.context.adapters.app_config_fragment.admin_bulk_update(input.to_pydantic())
    return AdminBulkUpdateAppConfigFragmentsPayloadGQL.from_pydantic(result)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Cleanup-only deletion; absent keys are no-oped (admin only).",
    )
)  # type: ignore[misc]
async def admin_bulk_purge_app_config_fragments(
    info: Info[StrawberryGQLContext],
    input: AdminBulkPurgeAppConfigFragmentInputGQL,
) -> AdminBulkPurgeAppConfigFragmentsPayloadGQL:
    check_admin_only()
    result = await info.context.adapters.app_config_fragment.admin_bulk_purge(input.to_pydantic())
    return AdminBulkPurgeAppConfigFragmentsPayloadGQL.from_pydantic(result)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Strict insert on the caller's USER row; duplicates fail per-item. "
            "Returns recomputed merged `AppConfig` views."
        ),
    )
)  # type: ignore[misc]
async def bulk_create_my_app_config_fragments(
    info: Info[StrawberryGQLContext],
    input: BulkCreateMyAppConfigFragmentInputGQL,
) -> BulkCreateMyAppConfigFragmentsPayloadGQL:
    result = await info.context.adapters.app_config.my_bulk_create(input.to_pydantic())
    return BulkCreateMyAppConfigFragmentsPayloadGQL.from_pydantic(result)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Wholesale replacement on the caller's USER row; missing rows are returned as "
            "failures. Returns recomputed merged `AppConfig` views."
        ),
    )
)  # type: ignore[misc]
async def bulk_update_my_app_config_fragments(
    info: Info[StrawberryGQLContext],
    input: BulkUpdateMyAppConfigFragmentInputGQL,
) -> BulkUpdateMyAppConfigFragmentsPayloadGQL:
    result = await info.context.adapters.app_config.my_bulk_update(input.to_pydantic())
    return BulkUpdateMyAppConfigFragmentsPayloadGQL.from_pydantic(result)
