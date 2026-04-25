"""AppConfig (merged view) domain adapter — BEP-1052 §5.

Reads the per-user merged AppConfig view and writes the underlying USER
fragments via the same `app_config_fragment` service processors. The
merged-view surface lives on its own adapter (separate from
`AppConfigFragmentAdapter`) so each adapter handles a single domain
DTO surface — convention in this repo.
"""

from __future__ import annotations

from ai.backend.common.contexts.user import current_user
from ai.backend.common.dto.manager.v2.app_config.request import (
    AppConfigFilter,
    AppConfigOrder,
    GetUserAppConfigInput,
    SearchAppConfigsInput,
    SearchMyAppConfigsInput,
)
from ai.backend.common.dto.manager.v2.app_config.response import (
    AppConfigNode,
    BulkCreateMyAppConfigFragmentsPayload,
    BulkUpdateMyAppConfigFragmentsPayload,
    GetUserAppConfigPayload,
    SearchAppConfigsPayload,
)
from ai.backend.common.dto.manager.v2.app_config.types import AppConfigOrderField, OrderDirection
from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
    BulkCreateMyAppConfigFragmentsInput,
    BulkUpdateMyAppConfigFragmentsInput,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.response import (
    AppConfigFragmentBulkError,
    AppConfigFragmentNode,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.types import (
    AppConfigScopeType as DTOAppConfigScopeType,
)
from ai.backend.common.exception import UnreachableError
from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.data.app_config.types import AppConfigData
from ai.backend.manager.data.app_config_fragment.bulk_types import (
    AppConfigFragmentBulkItemError,
    MyAppConfigFragmentBulkItem,
)
from ai.backend.manager.data.app_config_fragment.types import AppConfigFragmentData
from ai.backend.manager.models.app_config_fragment.conditions import AppConfigFragmentConditions
from ai.backend.manager.models.app_config_fragment.orders import AppConfigFragmentOrders
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.repositories.app_config_fragment.types import UserAppConfigSearchScope
from ai.backend.manager.repositories.base import BatchQuerier, QueryCondition, QueryOrder
from ai.backend.manager.services.app_config_fragment.actions.admin_search_app_configs import (
    AdminSearchAppConfigsAction,
)
from ai.backend.manager.services.app_config_fragment.actions.bulk_create_my import (
    BulkCreateMyAppConfigFragmentsAction,
)
from ai.backend.manager.services.app_config_fragment.actions.bulk_update_my import (
    BulkUpdateMyAppConfigFragmentsAction,
)
from ai.backend.manager.services.app_config_fragment.actions.get_user_app_config import (
    GetUserAppConfigAction,
)
from ai.backend.manager.services.app_config_fragment.actions.search_user_app_configs import (
    SearchUserAppConfigsAction,
)

from .base import BaseAdapter


class AppConfigAdapter(BaseAdapter):
    """Adapter for the merged AppConfig view (BEP-1052 §5).

    Backed by the `app_config_fragment` service processors — the merged
    view is computed from raw fragments — but exposed as a separate
    transport-layer surface so the Fragment adapter stays focused on
    raw-row operations.
    """

    # ── Reads ────────────────────────────────────────────────────────

    async def my_app_config(self, name: str) -> GetUserAppConfigPayload:
        """Read the caller's own merged AppConfig for `name`.

        Resolves the current user from the context; there is no way to
        target another user through this method.
        """
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        result = await self._processors.app_config_fragment.get_user_app_config.wait_for_complete(
            GetUserAppConfigAction(user_id=me.user_id, config_name=name)
        )
        return GetUserAppConfigPayload(item=self._data_to_dto(result.app_config))

    async def admin_get_user_app_config(
        self, input: GetUserAppConfigInput
    ) -> GetUserAppConfigPayload:
        """Read a specific user's merged AppConfig (admin only)."""
        result = await self._processors.app_config_fragment.get_user_app_config.wait_for_complete(
            GetUserAppConfigAction(user_id=input.user_id, config_name=input.name)
        )
        return GetUserAppConfigPayload(item=self._data_to_dto(result.app_config))

    async def my_search_app_configs(
        self, input: SearchMyAppConfigsInput
    ) -> SearchAppConfigsPayload:
        """Paginated merged-view search over the caller's own AppConfigs."""
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        querier = self._build_querier_from_input(input)
        result = (
            await self._processors.app_config_fragment.search_user_app_configs.wait_for_complete(
                SearchUserAppConfigsAction(
                    scope=UserAppConfigSearchScope(user_id=me.user_id),
                    querier=querier,
                )
            )
        )
        return SearchAppConfigsPayload(
            items=[self._data_to_dto(item) for item in result.items],
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def admin_search_app_configs(
        self, input: SearchAppConfigsInput
    ) -> SearchAppConfigsPayload:
        """Cross-user merged-view search (admin only).

        `filter.user_id` pins the query to a single user; otherwise
        pagination walks across every user.
        """
        querier = self._build_querier_from_input(input)
        result = (
            await self._processors.app_config_fragment.admin_search_app_configs.wait_for_complete(
                AdminSearchAppConfigsAction(querier=querier)
            )
        )
        return SearchAppConfigsPayload(
            items=[self._data_to_dto(item) for item in result.items],
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    # ── Self-service bulk writes (BEP-1052 §3) ───────────────────────
    #
    # Each bulk processor returns a `BulkProcessResult[T]` whose
    # `.result` field is the underlying `*ActionResult` produced by the
    # service. We discard the validator-decision trail here — RBAC
    # reasons travel back through the per-item `failed` list.

    async def my_bulk_create(
        self, input: BulkCreateMyAppConfigFragmentsInput
    ) -> BulkCreateMyAppConfigFragmentsPayload:
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        items = [
            MyAppConfigFragmentBulkItem(name=item.name, extra_config=dict(item.extra_config))
            for item in input.items
        ]
        wrapper = await self._processors.app_config_fragment.bulk_create_my.wait_for_complete(
            BulkCreateMyAppConfigFragmentsAction(
                entity_ids=[],
                user_id=me.user_id,
                items=items,
            )
        )
        result = wrapper.result
        return BulkCreateMyAppConfigFragmentsPayload(
            created=[self._data_to_dto(item) for item in result.created],
            failed=[self._bulk_error_to_dto(err) for err in result.failed],
        )

    async def my_bulk_update(
        self, input: BulkUpdateMyAppConfigFragmentsInput
    ) -> BulkUpdateMyAppConfigFragmentsPayload:
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        items = [
            MyAppConfigFragmentBulkItem(name=item.name, extra_config=dict(item.extra_config))
            for item in input.items
        ]
        wrapper = await self._processors.app_config_fragment.bulk_update_my.wait_for_complete(
            BulkUpdateMyAppConfigFragmentsAction(
                entity_ids=[],
                user_id=me.user_id,
                items=items,
            )
        )
        result = wrapper.result
        return BulkUpdateMyAppConfigFragmentsPayload(
            updated=[self._data_to_dto(item) for item in result.updated],
            failed=[self._bulk_error_to_dto(err) for err in result.failed],
        )

    # ── Querier / DTO helpers ────────────────────────────────────────

    _PAGINATION_SPEC = PaginationSpec(
        forward_order=AppConfigFragmentOrders.created_at(ascending=False),
        backward_order=AppConfigFragmentOrders.created_at(ascending=True),
        forward_condition_factory=AppConfigFragmentConditions.by_cursor_forward,
        backward_condition_factory=AppConfigFragmentConditions.by_cursor_backward,
        tiebreaker_order=AppConfigFragmentRow.id.asc(),
    )

    def _build_querier_from_input(
        self,
        input: SearchMyAppConfigsInput | SearchAppConfigsInput,
    ) -> BatchQuerier:
        """Querier builder for the merged-view searches.

        The merged-view SQL resolves cursor / order internally via the
        repository layer; this helper forwards only the filter / order /
        pagination fields so cursor tiebreakers stay consistent with
        the raw-fragment querier.
        """
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        return self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=self._PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )

    def _convert_filter(self, filter: AppConfigFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if filter.name is not None:
            condition = self.convert_string_filter(
                filter.name,
                contains_factory=AppConfigFragmentConditions.by_name_contains,
                equals_factory=AppConfigFragmentConditions.by_name_equals,
                starts_with_factory=AppConfigFragmentConditions.by_name_starts_with,
                ends_with_factory=AppConfigFragmentConditions.by_name_ends_with,
                in_factory=AppConfigFragmentConditions.by_name_in,
            )
            if condition is not None:
                conditions.append(condition)
        # `filter.user_id` handling lives inside the merged-view SQL
        # (repository layer) rather than in a BatchQuerier condition —
        # see `AppConfigFragmentDBSource.admin_search_app_configs`.
        return conditions

    @staticmethod
    def _convert_orders(orders: list[AppConfigOrder]) -> list[QueryOrder]:
        result: list[QueryOrder] = []
        for order in orders:
            ascending = order.direction == OrderDirection.ASC
            match order.field:
                case AppConfigOrderField.NAME:
                    result.append(AppConfigFragmentOrders.name(ascending))
                case AppConfigOrderField.USER_ID:
                    # USER_ID ordering is applied inside the merged-view SQL
                    # because the raw `app_config_fragments` row does not
                    # carry a user_id column directly.
                    continue
        return result

    def _data_to_dto(self, data: AppConfigData) -> AppConfigNode:
        return AppConfigNode(
            user_id=data.user_id,
            name=data.name,
            fragments=[self._fragment_data_to_dto(fragment) for fragment in data.fragments],
            config=dict(data.config) if data.config is not None else None,
        )

    @staticmethod
    def _fragment_data_to_dto(data: AppConfigFragmentData) -> AppConfigFragmentNode:
        return AppConfigFragmentNode(
            id=data.id,
            scope_type=DTOAppConfigScopeType(data.scope_type.value),
            scope_id=data.scope_id,
            name=data.name,
            extra_config=dict(data.extra_config) if data.extra_config is not None else None,
            created_at=data.created_at,
            updated_at=data.updated_at,
        )

    @staticmethod
    def _bulk_error_to_dto(
        err: AppConfigFragmentBulkItemError,
    ) -> AppConfigFragmentBulkError:
        return AppConfigFragmentBulkError(
            index=err.index,
            scope_type=DTOAppConfigScopeType(err.scope_type),
            scope_id=err.scope_id,
            name=err.name,
            message=err.message,
        )
