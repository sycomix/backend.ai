"""AppConfigFragment domain adapter — Pydantic-in / Pydantic-out transport layer."""

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
from ai.backend.common.dto.manager.v2.app_config.types import (
    AppConfigOrderField,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
    AdminBulkCreateAppConfigFragmentsInput,
    AdminBulkPurgeAppConfigFragmentsInput,
    AdminBulkUpdateAppConfigFragmentsInput,
    AppConfigFragmentFilter,
    AppConfigFragmentKeyInput,
    AppConfigFragmentOrder,
    BulkCreateMyAppConfigFragmentsInput,
    BulkUpdateMyAppConfigFragmentsInput,
    SearchAppConfigFragmentsInput,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.response import (
    AdminBulkCreateAppConfigFragmentsPayload,
    AdminBulkPurgeAppConfigFragmentsPayload,
    AdminBulkUpdateAppConfigFragmentsPayload,
    AppConfigFragmentBulkError,
    AppConfigFragmentNode,
    GetAppConfigFragmentPayload,
    PurgeAppConfigFragmentKey,
    SearchAppConfigFragmentsPayload,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.types import (
    AppConfigFragmentOrderField,
    OrderDirection,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.types import (
    AppConfigScopeType as DTOAppConfigScopeType,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.types import OrderDirection
from ai.backend.common.exception import UnreachableError
from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.data.app_config.types import AppConfigData
from ai.backend.manager.data.app_config_fragment.bulk_types import (
    AppConfigFragmentBulkItem,
    AppConfigFragmentBulkItemError,
    MyAppConfigFragmentBulkItem,
)
from ai.backend.manager.data.app_config_fragment.types import (
    AppConfigFragmentData,
    AppConfigFragmentKey,
    AppConfigScopeType,
)
from ai.backend.manager.models.app_config_fragment.conditions import AppConfigFragmentConditions
from ai.backend.manager.models.app_config_fragment.orders import AppConfigFragmentOrders
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.repositories.app_config_fragment.types import (
    AppConfigFragmentSearchScope,
    UserAppConfigSearchScope,
)
from ai.backend.manager.repositories.base import BatchQuerier, QueryCondition, QueryOrder
from ai.backend.manager.services.app_config_fragment.actions.admin_bulk_create import (
    AdminBulkCreateAppConfigFragmentsAction,
)
from ai.backend.manager.services.app_config_fragment.actions.admin_bulk_purge import (
    AdminBulkPurgeAppConfigFragmentsAction,
)
from ai.backend.manager.services.app_config_fragment.actions.admin_bulk_update import (
    AdminBulkUpdateAppConfigFragmentsAction,
)
from ai.backend.manager.services.app_config_fragment.actions.admin_search import (
    AdminSearchAppConfigFragmentsAction,
)
from ai.backend.manager.services.app_config_fragment.actions.admin_search_app_configs import (
    AdminSearchAppConfigsAction,
)
from ai.backend.manager.services.app_config_fragment.actions.bulk_create_my import (
    BulkCreateMyAppConfigFragmentsAction,
)
from ai.backend.manager.services.app_config_fragment.actions.bulk_update_my import (
    BulkUpdateMyAppConfigFragmentsAction,
)
from ai.backend.manager.services.app_config_fragment.actions.get import GetAppConfigFragmentAction
from ai.backend.manager.services.app_config_fragment.actions.get_user_app_config import (
    GetUserAppConfigAction,
)
from ai.backend.manager.services.app_config_fragment.actions.search import (
    SearchAppConfigFragmentsAction,
)
from ai.backend.manager.services.app_config_fragment.actions.search_user_app_configs import (
    SearchUserAppConfigsAction,
)

from .base import BaseAdapter


class AppConfigFragmentAdapter(BaseAdapter):
    """Adapter for AppConfigFragment domain operations.

    Writes are bulk-only (BEP-1052 §3); single-item create / update /
    purge entry points are intentionally absent.
    """

    async def get(self, key_input: AppConfigFragmentKeyInput) -> GetAppConfigFragmentPayload:
        key = self._input_to_key(key_input)
        result = await self._processors.app_config_fragment.get.wait_for_complete(
            GetAppConfigFragmentAction(key=key)
        )
        return GetAppConfigFragmentPayload(
            item=self._data_to_dto(result.fragment) if result.fragment is not None else None,
        )

    async def search(
        self,
        scope_type: AppConfigScopeType,
        scope_id: str,
        input: SearchAppConfigFragmentsInput,
    ) -> SearchAppConfigFragmentsPayload:
        """Scope-bound search — caller pins `(scope_type, scope_id)` so
        non-admin users only see fragments within their own scope.
        """
        querier = self._build_querier_from_input(input)
        result = await self._processors.app_config_fragment.search.wait_for_complete(
            SearchAppConfigFragmentsAction(
                scope=AppConfigFragmentSearchScope(
                    scope_type=scope_type,
                    scope_id=scope_id,
                ),
                querier=querier,
            )
        )
        return SearchAppConfigFragmentsPayload(
            items=[self._data_to_dto(item) for item in result.items],
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def admin_search(
        self, input: SearchAppConfigFragmentsInput
    ) -> SearchAppConfigFragmentsPayload:
        """Cross-scope admin search — authorization is enforced upstream."""
        querier = self._build_querier_from_input(input)
        result = await self._processors.app_config_fragment.admin_search.wait_for_complete(
            AdminSearchAppConfigFragmentsAction(querier=querier)
        )
        return SearchAppConfigFragmentsPayload(
            items=[self._data_to_dto(item) for item in result.items],
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    _PAGINATION_SPEC = PaginationSpec(
        forward_order=AppConfigFragmentOrders.created_at(ascending=False),
        backward_order=AppConfigFragmentOrders.created_at(ascending=True),
        forward_condition_factory=AppConfigFragmentConditions.by_cursor_forward,
        backward_condition_factory=AppConfigFragmentConditions.by_cursor_backward,
        tiebreaker_order=AppConfigFragmentRow.id.asc(),
    )

    def _build_querier_from_input(self, input: SearchAppConfigFragmentsInput) -> BatchQuerier:
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

    def _convert_filter(self, filter: AppConfigFragmentFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if filter.id is not None:
            condition = self.convert_uuid_filter(
                filter.id,
                equals_factory=AppConfigFragmentConditions.by_id_equals,
                in_factory=AppConfigFragmentConditions.by_id_in,
            )
            if condition is not None:
                conditions.append(condition)
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
        if filter.scope_type is not None:
            conditions.append(
                AppConfigFragmentConditions.by_scope_type_equals(filter.scope_type.value)
            )
        if filter.scope_id is not None:
            condition = self.convert_string_filter(
                filter.scope_id,
                contains_factory=AppConfigFragmentConditions.by_scope_id_contains,
                equals_factory=AppConfigFragmentConditions.by_scope_id_equals,
                starts_with_factory=AppConfigFragmentConditions.by_scope_id_starts_with,
                ends_with_factory=AppConfigFragmentConditions.by_scope_id_ends_with,
                in_factory=AppConfigFragmentConditions.by_scope_id_in,
            )
            if condition is not None:
                conditions.append(condition)
        return conditions

    @staticmethod
    def _convert_orders(orders: list[AppConfigFragmentOrder]) -> list[QueryOrder]:
        result: list[QueryOrder] = []
        for order in orders:
            ascending = order.direction == OrderDirection.ASC
            match order.field:
                case AppConfigFragmentOrderField.SCOPE_TYPE:
                    result.append(AppConfigFragmentOrders.scope_type(ascending))
                case AppConfigFragmentOrderField.SCOPE_ID:
                    result.append(AppConfigFragmentOrders.scope_id(ascending))
                case AppConfigFragmentOrderField.NAME:
                    result.append(AppConfigFragmentOrders.name(ascending))
                case AppConfigFragmentOrderField.CREATED_AT:
                    result.append(AppConfigFragmentOrders.created_at(ascending))
                case AppConfigFragmentOrderField.UPDATED_AT:
                    result.append(AppConfigFragmentOrders.updated_at(ascending))
        return result

    @staticmethod
    def _input_to_key(key_input: AppConfigFragmentKeyInput) -> AppConfigFragmentKey:
        return AppConfigFragmentKey(
            scope_type=AppConfigScopeType(key_input.scope_type.value),
            scope_id=key_input.scope_id,
            name=key_input.name,
        )

    @staticmethod
    def _data_to_dto(data: AppConfigFragmentData) -> AppConfigFragmentNode:
        return AppConfigFragmentNode(
            id=data.id,
            scope_type=DTOAppConfigScopeType(data.scope_type.value),
            scope_id=data.scope_id,
            name=data.name,
            config=dict(data.config) if data.config is not None else None,
            created_at=data.created_at,
            updated_at=data.updated_at,
        )

    # ── Merged-view (AppConfig, BEP-1052 §5) ───────────────────────

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
        return GetUserAppConfigPayload(item=self._app_config_data_to_dto(result.app_config))

    async def admin_get_user_app_config(
        self, input: GetUserAppConfigInput
    ) -> GetUserAppConfigPayload:
        """Read a specific user's merged AppConfig (admin only)."""
        result = await self._processors.app_config_fragment.get_user_app_config.wait_for_complete(
            GetUserAppConfigAction(user_id=input.user_id, config_name=input.name)
        )
        return GetUserAppConfigPayload(item=self._app_config_data_to_dto(result.app_config))

    async def my_search_app_configs(
        self, input: SearchMyAppConfigsInput
    ) -> SearchAppConfigsPayload:
        """Paginated merged-view search over the caller's own AppConfigs."""
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        querier = self._build_app_config_querier(input)
        result = (
            await self._processors.app_config_fragment.search_user_app_configs.wait_for_complete(
                SearchUserAppConfigsAction(
                    scope=UserAppConfigSearchScope(user_id=me.user_id),
                    querier=querier,
                )
            )
        )
        return SearchAppConfigsPayload(
            items=[self._app_config_data_to_dto(item) for item in result.items],
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
        querier = self._build_app_config_querier(input)
        result = (
            await self._processors.app_config_fragment.admin_search_app_configs.wait_for_complete(
                AdminSearchAppConfigsAction(querier=querier)
            )
        )
        return SearchAppConfigsPayload(
            items=[self._app_config_data_to_dto(item) for item in result.items],
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    def _build_app_config_querier(
        self,
        input: SearchMyAppConfigsInput | SearchAppConfigsInput,
    ) -> BatchQuerier:
        """Querier builder shared by `my_search_app_configs` and
        `admin_search_app_configs`.

        The merged-view SQL resolves cursor/order internally via the
        repository layer; this helper forwards only the filter / order /
        pagination fields so cursor tiebreakers stay consistent with
        the raw-fragment querier.
        """
        conditions = self._convert_app_config_filter(input.filter) if input.filter else []
        orders = self._convert_app_config_orders(input.order) if input.order else []
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

    def _convert_app_config_filter(self, filter: AppConfigFilter) -> list[QueryCondition]:
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
    def _convert_app_config_orders(orders: list[AppConfigOrder]) -> list[QueryOrder]:
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

    def _app_config_data_to_dto(self, data: AppConfigData) -> AppConfigNode:
        return AppConfigNode(
            user_id=data.user_id,
            name=data.name,
            fragments=[self._data_to_dto(fragment) for fragment in data.fragments],
            config=dict(data.config) if data.config is not None else None,
        )

    # ── Bulk mutations (BEP-1052 §3) ───────────────────────────────
    #
    # Each bulk processor returns a `BulkProcessResult[T]` whose
    # `.result` field is the underlying `*ActionResult` produced by the
    # service. We discard the validator-decision trail here — RBAC
    # reasons travel back through the per-item `failed` list.

    async def admin_bulk_create(
        self, input: AdminBulkCreateAppConfigFragmentsInput
    ) -> AdminBulkCreateAppConfigFragmentsPayload:
        items = [
            AppConfigFragmentBulkItem(
                key=self._input_to_key(item.key),
                config=dict(item.config),
            )
            for item in input.items
        ]
        wrapper = await self._processors.app_config_fragment.admin_bulk_create.wait_for_complete(
            AdminBulkCreateAppConfigFragmentsAction(entity_ids=[], items=items)
        )
        result = wrapper.result
        return AdminBulkCreateAppConfigFragmentsPayload(
            created=[self._data_to_dto(fragment) for fragment in result.created],
            failed=[self._bulk_error_to_dto(err) for err in result.failed],
        )

    async def admin_bulk_update(
        self, input: AdminBulkUpdateAppConfigFragmentsInput
    ) -> AdminBulkUpdateAppConfigFragmentsPayload:
        items = [
            AppConfigFragmentBulkItem(
                key=self._input_to_key(item.key),
                config=dict(item.config),
            )
            for item in input.items
        ]
        wrapper = await self._processors.app_config_fragment.admin_bulk_update.wait_for_complete(
            AdminBulkUpdateAppConfigFragmentsAction(entity_ids=[], items=items)
        )
        result = wrapper.result
        return AdminBulkUpdateAppConfigFragmentsPayload(
            updated=[self._data_to_dto(fragment) for fragment in result.updated],
            failed=[self._bulk_error_to_dto(err) for err in result.failed],
        )

    async def admin_bulk_purge(
        self, input: AdminBulkPurgeAppConfigFragmentsInput
    ) -> AdminBulkPurgeAppConfigFragmentsPayload:
        keys = [self._input_to_key(key_input) for key_input in input.keys]
        wrapper = await self._processors.app_config_fragment.admin_bulk_purge.wait_for_complete(
            AdminBulkPurgeAppConfigFragmentsAction(entity_ids=[], keys=keys)
        )
        result = wrapper.result
        return AdminBulkPurgeAppConfigFragmentsPayload(
            purged=[
                PurgeAppConfigFragmentKey(
                    scope_type=DTOAppConfigScopeType(key.scope_type.value),
                    scope_id=key.scope_id,
                    name=key.name,
                )
                for key in result.purged
            ],
            failed=[self._bulk_error_to_dto(err) for err in result.failed],
        )

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
                entity_ids=[item.name for item in items],
                user_id=me.user_id,
                items=items,
            )
        )
        result = wrapper.result
        return BulkCreateMyAppConfigFragmentsPayload(
            created=[self._app_config_data_to_dto(item) for item in result.created],
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
                entity_ids=[item.name for item in items],
                user_id=me.user_id,
                items=items,
            )
        )
        result = wrapper.result
        return BulkUpdateMyAppConfigFragmentsPayload(
            updated=[self._app_config_data_to_dto(item) for item in result.updated],
            failed=[self._bulk_error_to_dto(err) for err in result.failed],
        )

    @staticmethod
    def _bulk_error_to_dto(
        err: AppConfigFragmentBulkItemError,
    ) -> AppConfigFragmentBulkError:
        """Convert the service-layer error dataclass to its DTO mirror."""
        return AppConfigFragmentBulkError(
            index=err.index,
            scope_type=DTOAppConfigScopeType(err.scope_type),
            scope_id=err.scope_id,
            name=err.name,
            message=err.message,
        )
