import logging

from ai.backend.common.contexts.user import current_user
from ai.backend.common.exception import UnreachableError
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.app_config_fragment.bulk_types import (
    AppConfigFragmentBulkItemError,
)
from ai.backend.manager.data.app_config_fragment.types import (
    AppConfigFragmentKey,
    AppConfigScopeType,
)
from ai.backend.manager.repositories.app_config_fragment.admin_repository import (
    AppConfigFragmentAdminRepository,
)
from ai.backend.manager.repositories.app_config_fragment.repository import (
    AppConfigFragmentRepository,
)
from ai.backend.manager.services.app_config_fragment.actions.admin_bulk_create import (
    AdminBulkCreateAppConfigFragmentsAction,
    AdminBulkCreateAppConfigFragmentsActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.admin_bulk_purge import (
    AdminBulkPurgeAppConfigFragmentsAction,
    AdminBulkPurgeAppConfigFragmentsActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.admin_bulk_update import (
    AdminBulkUpdateAppConfigFragmentsAction,
    AdminBulkUpdateAppConfigFragmentsActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.admin_search import (
    AdminSearchAppConfigFragmentsAction,
    AdminSearchAppConfigFragmentsActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.admin_search_app_configs import (
    AdminSearchAppConfigsAction,
    AdminSearchAppConfigsActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.get import (
    GetAppConfigFragmentAction,
    GetAppConfigFragmentActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.get_user_app_config import (
    GetUserAppConfigAction,
    GetUserAppConfigActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.my_bulk_create import (
    MyBulkCreateAppConfigFragmentsAction,
    MyBulkCreateAppConfigFragmentsActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.my_bulk_update import (
    MyBulkUpdateAppConfigFragmentsAction,
    MyBulkUpdateAppConfigFragmentsActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.search import (
    SearchAppConfigFragmentsAction,
    SearchAppConfigFragmentsActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.search_user_app_configs import (
    SearchUserAppConfigsAction,
    SearchUserAppConfigsActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AppConfigFragmentService:
    _repository: AppConfigFragmentRepository
    _admin_repository: AppConfigFragmentAdminRepository

    def __init__(
        self,
        repository: AppConfigFragmentRepository,
        admin_repository: AppConfigFragmentAdminRepository,
    ) -> None:
        self._repository = repository
        self._admin_repository = admin_repository

    async def get(self, action: GetAppConfigFragmentAction) -> GetAppConfigFragmentActionResult:
        fragment = await self._repository.get(action.key)
        return GetAppConfigFragmentActionResult(fragment=fragment)

    async def search(
        self, action: SearchAppConfigFragmentsAction
    ) -> SearchAppConfigFragmentsActionResult:
        result = await self._repository.search(action.scope, action.querier)
        return SearchAppConfigFragmentsActionResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def admin_search(
        self, action: AdminSearchAppConfigFragmentsAction
    ) -> AdminSearchAppConfigFragmentsActionResult:
        result = await self._admin_repository.admin_search(action.querier)
        return AdminSearchAppConfigFragmentsActionResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    # ── Merged-view reads (AppConfig) ────────────────

    async def get_user_app_config(
        self, action: GetUserAppConfigAction
    ) -> GetUserAppConfigActionResult:
        app_config = await self._repository.app_config(action.user_id, action.config_name)
        return GetUserAppConfigActionResult(app_config=app_config)

    async def search_user_app_configs(
        self, action: SearchUserAppConfigsAction
    ) -> SearchUserAppConfigsActionResult:
        result = await self._repository.search_app_configs(action.scope, action.querier)
        return SearchUserAppConfigsActionResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def admin_search_app_configs(
        self, action: AdminSearchAppConfigsAction
    ) -> AdminSearchAppConfigsActionResult:
        result = await self._admin_repository.admin_search_app_configs(action.querier)
        return AdminSearchAppConfigsActionResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    # ── Bulk mutations ────────

    async def admin_bulk_create(
        self, action: AdminBulkCreateAppConfigFragmentsAction
    ) -> AdminBulkCreateAppConfigFragmentsActionResult:
        """Strict insert across any scope; each item in its own
        transaction so failures are collected per-item."""
        created = []
        failed: list[AppConfigFragmentBulkItemError] = []
        for index, item in enumerate(action.items):
            try:
                fragment = await self._admin_repository.create(item.key, item.config)
                created.append(fragment)
            except Exception as e:
                log.warning("admin_bulk_create item {} failed: {}", index, e)
                failed.append(
                    AppConfigFragmentBulkItemError(
                        index=index,
                        scope_type=item.key.scope_type.value,
                        scope_id=item.key.scope_id,
                        name=item.key.name,
                        message=str(e),
                    )
                )
        return AdminBulkCreateAppConfigFragmentsActionResult(created=created, failed=failed)

    async def admin_bulk_update(
        self, action: AdminBulkUpdateAppConfigFragmentsAction
    ) -> AdminBulkUpdateAppConfigFragmentsActionResult:
        """Wholesale JSON replacement; items without an existing row
        are collected as failures (not auto-inserted)."""
        updated = []
        failed: list[AppConfigFragmentBulkItemError] = []
        for index, item in enumerate(action.items):
            try:
                fragment = await self._admin_repository.update(item.key, item.config)
                updated.append(fragment)
            except Exception as e:
                log.warning("admin_bulk_update item {} failed: {}", index, e)
                failed.append(
                    AppConfigFragmentBulkItemError(
                        index=index,
                        scope_type=item.key.scope_type.value,
                        scope_id=item.key.scope_id,
                        name=item.key.name,
                        message=str(e),
                    )
                )
        return AdminBulkUpdateAppConfigFragmentsActionResult(updated=updated, failed=failed)

    async def admin_bulk_purge(
        self, action: AdminBulkPurgeAppConfigFragmentsAction
    ) -> AdminBulkPurgeAppConfigFragmentsActionResult:
        """Cleanup-only deletion; absent keys are no-oped."""
        purged: list[AppConfigFragmentKey] = []
        failed: list[AppConfigFragmentBulkItemError] = []
        for index, key in enumerate(action.keys):
            try:
                ok = await self._admin_repository.purge(key)
                if ok:
                    purged.append(key)
                # Absent keys are intentionally no-oped (no failure entry).
            except Exception as e:
                log.warning("admin_bulk_purge item {} failed: {}", index, e)
                failed.append(
                    AppConfigFragmentBulkItemError(
                        index=index,
                        scope_type=key.scope_type.value,
                        scope_id=key.scope_id,
                        name=key.name,
                        message=str(e),
                    )
                )
        return AdminBulkPurgeAppConfigFragmentsActionResult(purged=purged, failed=failed)

    async def my_bulk_create(
        self, action: MyBulkCreateAppConfigFragmentsAction
    ) -> MyBulkCreateAppConfigFragmentsActionResult:
        """Self-service bulk create on the caller's `USER` row; each
        success recomputes the merged `AppConfig` view.
        """
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        user_id = me.user_id
        user_id_str = str(user_id)
        created = []
        failed: list[AppConfigFragmentBulkItemError] = []
        for index, item in enumerate(action.items):
            key = AppConfigFragmentKey(
                scope_type=AppConfigScopeType.USER,
                scope_id=user_id_str,
                name=item.name,
            )
            try:
                await self._admin_repository.create(key, item.config)
                merged = await self._repository.app_config(user_id, item.name)
                created.append(merged)
            except Exception as e:
                log.warning("my_bulk_create item {} failed: {}", index, e)
                failed.append(
                    AppConfigFragmentBulkItemError(
                        index=index,
                        scope_type=AppConfigScopeType.USER.value,
                        scope_id=user_id_str,
                        name=item.name,
                        message=str(e),
                    )
                )
        return MyBulkCreateAppConfigFragmentsActionResult(created=created, failed=failed)

    async def my_bulk_update(
        self, action: MyBulkUpdateAppConfigFragmentsAction
    ) -> MyBulkUpdateAppConfigFragmentsActionResult:
        """Self-service bulk update on the caller's `USER` row."""
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        user_id = me.user_id
        user_id_str = str(user_id)
        updated = []
        failed: list[AppConfigFragmentBulkItemError] = []
        for index, item in enumerate(action.items):
            key = AppConfigFragmentKey(
                scope_type=AppConfigScopeType.USER,
                scope_id=user_id_str,
                name=item.name,
            )
            try:
                await self._admin_repository.update(key, item.config)
                merged = await self._repository.app_config(user_id, item.name)
                updated.append(merged)
            except Exception as e:
                log.warning("my_bulk_update item {} failed: {}", index, e)
                failed.append(
                    AppConfigFragmentBulkItemError(
                        index=index,
                        scope_type=AppConfigScopeType.USER.value,
                        scope_id=user_id_str,
                        name=item.name,
                        message=str(e),
                    )
                )
        return MyBulkUpdateAppConfigFragmentsActionResult(updated=updated, failed=failed)
