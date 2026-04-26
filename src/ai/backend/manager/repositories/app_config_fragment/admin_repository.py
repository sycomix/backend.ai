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
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
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
from ai.backend.manager.repositories.base.querier import BatchQuerier

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


class AppConfigFragmentAdminRepository:
    """Admin-only operations on AppConfigFragment.

    All mutations (`create` / `update` / `purge`) and cross-scope
    reads (`admin_search` raw, `admin_search_app_configs` merged)
    live here — read-side scope-bound operations are on
    `AppConfigFragmentRepository`. Authorization is enforced at the
    service layer before reaching either repository.

    The required-policy invariant is enforced by the service layer;
    the FK on `app_config_fragments.name` is the defense-in-depth
    backstop, translated by the creator spec into
    :class:`AppConfigFragmentPolicyMissing`.
    """

    _db_source: AppConfigFragmentDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = AppConfigFragmentDBSource(db)

    # ── Mutations ─────────────────────────────────────────────────

    @app_config_fragment_admin_repository_resilience.apply()
    async def create(
        self,
        key: AppConfigFragmentKey,
        extra_config: Mapping[str, Any],
    ) -> AppConfigFragmentData:
        creator: Creator[AppConfigFragmentRow] = Creator(
            spec=AppConfigFragmentCreatorSpec(
                scope_type=key.scope_type,
                scope_id=key.scope_id,
                name=key.name,
                extra_config=extra_config,
            ),
        )
        return await self._db_source.create(creator)

    @app_config_fragment_admin_repository_resilience.apply()
    async def update(
        self,
        key: AppConfigFragmentKey,
        extra_config: Mapping[str, Any],
    ) -> AppConfigFragmentData:
        """Update a fragment by natural key. Raises
        ``AppConfigFragmentNotFound`` when missing."""
        spec = AppConfigFragmentUpdaterSpec(extra_config=extra_config)
        return await self._db_source.update(key, spec)

    @app_config_fragment_admin_repository_resilience.apply()
    async def purge(self, key: AppConfigFragmentKey) -> bool:
        return await self._db_source.purge(key)

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
