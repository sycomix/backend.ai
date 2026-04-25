from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.app_config.types import AppConfigSearchResult
from ai.backend.manager.data.app_config_fragment.types import (
    AppConfigFragmentData,
    AppConfigFragmentKey,
    AppConfigFragmentSearchResult,
)
from ai.backend.manager.errors.app_config import AppConfigFragmentNotFound
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.app_config_fragment.cache_source import (
    AppConfigFragmentCacheSource,
)
from ai.backend.manager.repositories.app_config_fragment.creators import (
    AppConfigFragmentCreatorSpec,
)
from ai.backend.manager.repositories.app_config_fragment.db_source import (
    AppConfigFragmentDBSource,
)
from ai.backend.manager.repositories.app_config_fragment.updaters import (
    AppConfigFragmentUpdaterSpec,
)
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.purger import Purger
from ai.backend.manager.repositories.base.querier import BatchQuerier
from ai.backend.manager.repositories.base.updater import Updater

app_config_fragment_admin_repository_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(
                domain=DomainType.REPOSITORY,
                layer=LayerType.APP_CONFIG_FRAGMENT_ADMIN_REPOSITORY,
            )
        ),
        RetryPolicy(
            RetryArgs(
                max_retries=5,
                retry_delay=0.1,
                backoff_strategy=BackoffStrategy.FIXED,
                non_retryable_exceptions=(BackendAIError,),
            )
        ),
    ]
)


def _missing(key: AppConfigFragmentKey) -> AppConfigFragmentNotFound:
    return AppConfigFragmentNotFound(
        extra_msg=(
            f"scope_type={key.scope_type.value!r}, scope_id={key.scope_id!r}, name={key.name!r}"
        ),
    )


class AppConfigFragmentAdminRepository:
    """Admin-only operations on AppConfigFragment.

    All mutations (`create` / `update` / `purge`) and cross-scope
    reads (`admin_search` raw, `admin_search_app_configs` merged)
    live here — read-side scope-bound operations are on
    `AppConfigFragmentRepository`. Authorization is enforced at the
    service layer before reaching either repository. The required-
    policy invariant is enforced upstream by the service layer; the
    DB-level FK on ``app_config_fragments.name`` is the defense-in-
    depth backstop and surfaces as a generic integrity error.

    Mutations are routed through the shared Creator / Updater / Purger
    helpers so the same execution / resilience plumbing applies as in
    sister repositories.
    """

    _db_source: AppConfigFragmentDBSource
    _cache_source: AppConfigFragmentCacheSource | None

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        cache_source: AppConfigFragmentCacheSource | None = None,
    ) -> None:
        self._db_source = AppConfigFragmentDBSource(db)
        self._cache_source = cache_source

    # ── Mutations ─────────────────────────────────────────────────

    @app_config_fragment_admin_repository_resilience.apply()
    async def create(
        self,
        key: AppConfigFragmentKey,
        config: Mapping[str, Any],
    ) -> AppConfigFragmentData:
        creator: Creator[AppConfigFragmentRow] = Creator(
            spec=AppConfigFragmentCreatorSpec(
                scope_type=key.scope_type,
                scope_id=key.scope_id,
                name=key.name,
                config=config,
            ),
        )
        result = await self._db_source.create(creator)
        await self._invalidate(key)
        return result

    @app_config_fragment_admin_repository_resilience.apply()
    async def update(
        self,
        key: AppConfigFragmentKey,
        config: Mapping[str, Any],
    ) -> AppConfigFragmentData:
        """Update a fragment by natural key. Raises
        ``AppConfigFragmentNotFound`` when missing."""
        spec = AppConfigFragmentUpdaterSpec(extra_config=extra_config)
        result = await self._db_source.update(key, spec)
        await self._invalidate(key)
        return result

    @app_config_fragment_admin_repository_resilience.apply()
    async def purge(self, key: AppConfigFragmentKey) -> bool:
        result = await self._db_source.purge(key)
        if result:
            await self._invalidate(key)
        return result

    async def _invalidate(self, key: AppConfigFragmentKey) -> None:
        if self._cache_source is None:
            return
        await self._cache_source.invalidate_for_scope(key.scope_type, key.scope_id)

    # ── Cross-scope reads ────────────────────────────────────────

    @app_config_fragment_admin_repository_resilience.apply()
    async def admin_search(
        self,
        querier: BatchQuerier,
    ) -> AppConfigFragmentSearchResult:
        return await self._db_source.admin_search(querier)

    @app_config_fragment_admin_repository_resilience.apply()
    async def admin_search_app_configs(
        self,
        querier: BatchQuerier,
    ) -> AppConfigSearchResult:
        return await self._db_source.admin_search_app_configs(querier)
