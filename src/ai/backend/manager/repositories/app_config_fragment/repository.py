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
    `AppConfig` view. Mutations and admin cross-scope reads live on
    `AppConfigFragmentAdminRepository`.
    """

    _db_source: AppConfigFragmentDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = AppConfigFragmentDBSource(db)

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
        return await self._db_source.get_user_app_config(user_id, config_name)

    @app_config_fragment_repository_resilience.apply()
    async def search_app_configs(
        self,
        scope: UserAppConfigSearchScope,
        querier: BatchQuerier,
    ) -> AppConfigSearchResult:
        return await self._db_source.search_user_app_configs(scope, querier)
