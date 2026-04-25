"""AppConfig (merged view) GQL query resolvers (BEP-1052 §5)."""

from __future__ import annotations

from strawberry import Info

from ai.backend.common.dto.manager.v2.app_config.request import (
    SearchAppConfigsInput,
    SearchMyAppConfigsInput,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
    SearchAppConfigFragmentsInput,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.app_config.types import (
    AppConfigFilterGQL,
    AppConfigGQL,
    AppConfigOrderByGQL,
)
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
from ai.backend.manager.data.app_config_fragment.types import AppConfigScopeType


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Caller's own merged AppConfig list (auth required). Chain per policy "
            "(BEP-1052 §5); the adapter pins `(USER, current_user)` internally."
        ),
    )
)  # type: ignore[misc]
async def my_app_configs(
    info: Info[StrawberryGQLContext],
    filter: AppConfigFilterGQL | None = None,
    order_by: list[AppConfigOrderByGQL] | None = None,
    first: int | None = None,
    after: str | None = None,
    last: int | None = None,
    before: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> list[AppConfigGQL]:
    payload = await info.context.adapters.app_config.my_search_app_configs(
        SearchMyAppConfigsInput(
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
    return [AppConfigGQL.from_pydantic(node) for node in payload.items]


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Cross-user merged-view search (admin only). Resolves any user's AppConfig "
            "for audit / support. Pin to a single user with `filter.userId`; otherwise "
            "paginates across all users."
        ),
    )
)  # type: ignore[misc]
async def admin_app_configs(
    info: Info[StrawberryGQLContext],
    filter: AppConfigFilterGQL | None = None,
    order_by: list[AppConfigOrderByGQL] | None = None,
    first: int | None = None,
    after: str | None = None,
    last: int | None = None,
    before: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> list[AppConfigGQL]:
    check_admin_only()
    payload = await info.context.adapters.app_config.admin_search_app_configs(
        SearchAppConfigsInput(
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
    return [AppConfigGQL.from_pydantic(node) for node in payload.items]


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Public (no-auth) `PUBLIC`-scope app-config fragments — the subset of "
            "raw fragments that carry no personally-scoped data (BEP-1052 §3)."
        ),
    )
)  # type: ignore[misc]
async def public_app_config_fragments(
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
    payload = await info.context.adapters.app_config_fragment.search(
        scope_type=AppConfigScopeType.PUBLIC,
        scope_id="public",
        input=SearchAppConfigFragmentsInput(
            filter=filter.to_pydantic() if filter else None,
            order=[o.to_pydantic() for o in order_by] if order_by else None,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
    )
    return [AppConfigFragmentGQL.from_pydantic(node) for node in payload.items]
