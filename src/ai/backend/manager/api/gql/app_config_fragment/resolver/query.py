"""AppConfigFragment GQL query resolvers."""

from __future__ import annotations

from strawberry import Info

from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
    AppConfigFragmentKeyInput,
    SearchAppConfigFragmentsInput,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.types import AppConfigScopeType
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.app_config_fragment.types import (
    AppConfigFragmentFilterGQL,
    AppConfigFragmentGQL,
    AppConfigFragmentOrderByGQL,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_root_field,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only
from ai.backend.manager.data.app_config_fragment.types import (
    AppConfigScopeType as DataAppConfigScopeType,
)


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Get a single app-config fragment by natural key "
            "`(scope_type, scope_id, name)`. Available to any authenticated user "
            "— service-layer authorization gates cross-scope reads."
        ),
    )
)  # type: ignore[misc]
async def app_config_fragment(
    info: Info[StrawberryGQLContext],
    scope_type: AppConfigScopeType,
    scope_id: str,
    name: str,
) -> AppConfigFragmentGQL | None:
    payload = await info.context.adapters.app_config_fragment.get(
        AppConfigFragmentKeyInput(scope_type=scope_type, scope_id=scope_id, name=name)
    )
    if payload.item is None:
        return None
    return AppConfigFragmentGQL.from_pydantic(payload.item)


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Scope-bound app-config fragment list. Caller pins "
            "`(scope_type, scope_id)` so non-admin users only see fragments within "
            "their own scope (BEP-1052 §2)."
        ),
    )
)  # type: ignore[misc]
async def scoped_app_config_fragments(
    info: Info[StrawberryGQLContext],
    scope_type: AppConfigScopeType,
    scope_id: str,
    filter: AppConfigFragmentFilterGQL | None = None,
    order_by: list[AppConfigFragmentOrderByGQL] | None = None,
    first: int | None = None,
    after: str | None = None,
    last: int | None = None,
    before: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> list[AppConfigFragmentGQL]:
    search_input = SearchAppConfigFragmentsInput(
        filter=filter.to_pydantic() if filter else None,
        order=[o.to_pydantic() for o in order_by] if order_by else None,
        first=first,
        after=after,
        last=last,
        before=before,
        limit=limit,
        offset=offset,
    )
    payload = await info.context.adapters.app_config_fragment.search(
        scope_type=DataAppConfigScopeType(scope_type.value),
        scope_id=scope_id,
        input=search_input,
    )
    return [AppConfigFragmentGQL.from_pydantic(node) for node in payload.items]


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Cross-scope admin search across all app-config fragments (admin only).",
    )
)  # type: ignore[misc]
async def admin_app_config_fragments(
    info: Info[StrawberryGQLContext],
    filter: AppConfigFragmentFilterGQL | None = None,
    order_by: list[AppConfigFragmentOrderByGQL] | None = None,
    first: int | None = None,
    after: str | None = None,
    last: int | None = None,
    before: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> list[AppConfigFragmentGQL]:
    check_admin_only()
    payload = await info.context.adapters.app_config_fragment.admin_search(
        SearchAppConfigFragmentsInput(
            filter=filter.to_pydantic() if filter else None,
            order=[o.to_pydantic() for o in order_by] if order_by else None,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
    )
    return [AppConfigFragmentGQL.from_pydantic(node) for node in payload.items]
