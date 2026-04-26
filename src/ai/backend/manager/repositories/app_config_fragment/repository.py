from __future__ import annotations

import uuid

from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.app_config.types import AppConfigData, AppConfigSearchResult
from ai.backend.manager.data.app_config_fragment.types import (
    AppConfigFragmentData,
    AppConfigFragmentKey,
    AppConfigFragmentSearchResult,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.app_config_fragment.cache_source import (
    AppConfigFragmentCacheSource,
)
from ai.backend.manager.repositories.app_config_fragment.db_source import (
    AppConfigFragmentDBSource,
)
from ai.backend.manager.repositories.app_config_fragment.types import (
    AppConfigFragmentSearchScope,
    UserAppConfigSearchScope,
)
from ai.backend.manager.repositories.base.querier import BatchQuerier

app_config_fragment_repository_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(
                domain=DomainType.REPOSITORY,
                layer=LayerType.APP_CONFIG_FRAGMENT_REPOSITORY,
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


class AppConfigFragmentRepository:
    """Read-side repository for AppConfigFragment.

    Scope-bound reads on raw fragments plus the per-user merged
    `AppConfig` view. Mutations and admin cross-scope
    reads live on `AppConfigFragmentAdminRepository`. Retry + metric
    policies are applied at the DB-source layer; the merged-view read
    path is fronted by a Valkey cache so repeated WebUI bootstrap
    queries don't hammer the DB.
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

    # ── Raw fragment reads ────────────────────────────────────────

    @app_config_fragment_repository_resilience.apply()
    async def get(self, key: AppConfigFragmentKey) -> AppConfigFragmentData | None:
        return await self._db_source.get(key)

    @app_config_fragment_repository_resilience.apply()
    async def get_by_id(self, id: uuid.UUID) -> AppConfigFragmentData | None:
        return await self._db_source.get_by_id(id)

    @app_config_fragment_repository_resilience.apply()
    async def search(
        self,
        scope: AppConfigFragmentSearchScope,
        querier: BatchQuerier,
    ) -> AppConfigFragmentSearchResult:
        return await self._db_source.search(scope, querier)

    # ── Merged view (AppConfig) ───────────────────────────────────

    @app_config_fragment_repository_resilience.apply()
    async def app_config(
        self,
        user_id: uuid.UUID,
        config_name: str,
    ) -> AppConfigData:
        """Cache-aside read for the per-`(user, name)` merged view.

        Returns a fresh `AppConfigData` whose `config` payload may
        come from cache (fragments still resolve from the DB on
        demand). Cache failures fall through transparently.
        """
        if self._cache_source is not None:
            cached_config = await self._cache_source.get_merged_config(user_id, config_name)
            if cached_config is not None:
                # Re-fetch the fragment list from the DB; only the
                # deep-merged `config` payload is cached. Keeps the
                # response-shape contract unchanged.
                merged = await self._db_source.get_user_app_config(user_id, config_name)
                return AppConfigData(
                    user_id=merged.user_id,
                    name=merged.name,
                    fragments=merged.fragments,
                    config=cached_config,
                )

        merged = await self._db_source.get_user_app_config(user_id, config_name)
        if self._cache_source is not None:
            domain_name = await self._db_source.user_domain_name(user_id)
            await self._cache_source.set_merged_config(merged, domain_name=domain_name)
        return merged

    @app_config_fragment_repository_resilience.apply()
    async def search_app_configs(
        self,
        scope: UserAppConfigSearchScope,
        querier: BatchQuerier,
    ) -> AppConfigSearchResult:
        return await self._db_source.search_user_app_configs(scope, querier)
