from __future__ import annotations

from collections.abc import Mapping
from typing import Any

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


class AppConfigFragmentAdminRepository:
    """Admin-only operations on AppConfigFragment.

    All mutations (`create` / `update` / `purge`) and cross-scope
    reads (`admin_search` raw, `admin_search_app_configs` merged)
    live here — read-side scope-bound operations are on
    `AppConfigFragmentRepository`. Authorization is enforced at the
    service layer before reaching either repository.

    The required-policy invariant from BEP-1052 §1 is enforced by the
    service layer; the FK on `app_config_fragments.name` is the
    defense-in-depth backstop, translated by the creator spec into
    :class:`AppConfigFragmentPolicyMissing`.

    Retry + metric policies are applied at the DB-source layer.
    """

    _db_source: AppConfigFragmentDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = AppConfigFragmentDBSource(db)

    # ── Mutations ─────────────────────────────────────────────────

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

    async def update(
        self,
        key: AppConfigFragmentKey,
        extra_config: Mapping[str, Any],
    ) -> AppConfigFragmentData:
        """Update a fragment by natural key. Raises
        ``AppConfigFragmentNotFound`` when missing."""
        spec = AppConfigFragmentUpdaterSpec(extra_config=extra_config)
        return await self._db_source.update(key, spec)

    async def purge(self, key: AppConfigFragmentKey) -> bool:
        return await self._db_source.purge(key)

    # ── Cross-scope reads ────────────────────────────────────────

    async def admin_search(
        self,
        querier: BatchQuerier,
    ) -> AppConfigFragmentSearchResult:
        return await self._db_source.admin_search(querier)

    async def admin_search_app_configs(
        self,
        querier: BatchQuerier,
    ) -> AppConfigSearchResult:
        return await self._db_source.admin_search_app_configs(querier)
