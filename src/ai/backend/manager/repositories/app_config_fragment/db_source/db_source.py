from __future__ import annotations

import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import sqlalchemy as sa

from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.common.utils import deep_merge
from ai.backend.manager.data.app_config.types import AppConfigData, AppConfigSearchResult
from ai.backend.manager.data.app_config_fragment.types import (
    AppConfigFragmentData,
    AppConfigFragmentKey,
    AppConfigFragmentSearchResult,
    AppConfigScopeType,
)
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.models.app_config_policy.row import AppConfigPolicyRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.app_config_fragment.types import (
    AppConfigFragmentSearchScope,
    UserAppConfigSearchScope,
)
from ai.backend.manager.repositories.base.creator import Creator, execute_creator
from ai.backend.manager.repositories.base.purger import Purger, execute_purger
from ai.backend.manager.repositories.base.querier import BatchQuerier, execute_batch_querier
from ai.backend.manager.repositories.base.updater import Updater, execute_updater

app_config_fragment_db_source_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(
                domain=DomainType.DB_SOURCE,
                layer=LayerType.APP_CONFIG_FRAGMENT_DB_SOURCE,
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


@dataclass(frozen=True, slots=True)
class _MergedChain:
    """Internal return type of `_merge_chain` — the ordered fragments
    that contributed to the merge plus the deep-merged config (or
    `None` when every contributing fragment is empty).

    Re-shaped into `AppConfigData` by callers that also know the
    `(user_id, name)` they were resolving for.
    """

    fragments: list[AppConfigFragmentData]
    config: Mapping[str, Any] | None


class AppConfigFragmentDBSource:
    """Database operations for `app_config_fragments`.

    Two roles:
    1. Raw CRUD on `(scope_type, scope_id, name)` rows.
    2. Merge-side reads that resolve a user's `AppConfig` view by joining
       `app_config_policies` to derive the chain.
    """

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    # ── Raw fragment CRUD ──────────────────────────────────────────

    @app_config_fragment_db_source_resilience.apply()
    async def get(self, key: AppConfigFragmentKey) -> AppConfigFragmentData | None:
        async with self._db.begin_readonly_session() as db_sess:
            row = await db_sess.scalar(
                sa.select(AppConfigFragmentRow).where(
                    AppConfigFragmentRow.scope_type == key.scope_type,
                    AppConfigFragmentRow.scope_id == key.scope_id,
                    AppConfigFragmentRow.name == key.name,
                )
            )
            return row.to_data() if row is not None else None

    @app_config_fragment_db_source_resilience.apply()
    async def get_by_id(self, id: uuid.UUID) -> AppConfigFragmentData | None:
        async with self._db.begin_readonly_session() as db_sess:
            row = await db_sess.scalar(
                sa.select(AppConfigFragmentRow).where(AppConfigFragmentRow.id == id)
            )
            return row.to_data() if row is not None else None

    @app_config_fragment_db_source_resilience.apply()
    async def get_user_domain_name(self, user_id: uuid.UUID) -> str | None:
        """Single-column lookup of a user's `domain_name`.

        Used by the cache layer to tag merged-view entries with their
        owning domain so domain-scoped fragment writes can target a
        bounded user set during invalidation.
        """
        async with self._db.begin_readonly_session() as db_sess:
            domain_name: str | None = await db_sess.scalar(
                sa.select(UserRow.domain_name).where(UserRow.uuid == user_id)
            )
            return domain_name

    @app_config_fragment_db_source_resilience.apply()
    async def create(self, creator: Creator[AppConfigFragmentRow]) -> AppConfigFragmentData:
        """Insert a new fragment via the shared Creator helper.

        The natural-key UNIQUE violation translates to
        :class:`AppConfigFragmentConflict` via the spec's
        ``integrity_error_checks``. The required-policy invariant
        (FK on ``name``) is enforced upstream by the service layer;
        a bypass here surfaces as a generic integrity error.
        """
        async with self._db.begin_session() as db_sess:
            result = await execute_creator(db_sess, creator)
            return result.row.to_data()

    @app_config_fragment_db_source_resilience.apply()
    async def resolve_pk_by_key(
        self,
        key: AppConfigFragmentKey,
    ) -> uuid.UUID | None:
        """Resolve the natural key ``(scope_type, scope_id, name)`` to
        the row's UUID ``id``. Returns ``None`` when no row matches —
        callers translate to a domain-appropriate response."""
        async with self._db.begin_readonly_session() as db_sess:
            pk: uuid.UUID | None = await db_sess.scalar(
                sa.select(AppConfigFragmentRow.id).where(
                    AppConfigFragmentRow.scope_type == key.scope_type,
                    AppConfigFragmentRow.scope_id == key.scope_id,
                    AppConfigFragmentRow.name == key.name,
                )
            )
            return pk

    @app_config_fragment_db_source_resilience.apply()
    async def update(self, updater: Updater[AppConfigFragmentRow]) -> AppConfigFragmentData | None:
        """Apply a pre-built Updater. Returns ``None`` when the row
        vanished between PK resolution and write; the caller maps this
        to :class:`AppConfigFragmentNotFound`."""
        async with self._db.begin_session() as db_sess:
            result = await execute_updater(db_sess, updater)
            return result.row.to_data() if result is not None else None

    @app_config_fragment_db_source_resilience.apply()
    async def purge(self, purger: Purger[AppConfigFragmentRow]) -> bool:
        """Apply a pre-built Purger. Returns ``True`` when a row was
        actually removed (``False`` if the row vanished concurrently)."""
        async with self._db.begin_session() as db_sess:
            result = await execute_purger(db_sess, purger)
            return result is not None

    @app_config_fragment_db_source_resilience.apply()
    async def search(
        self,
        scope: AppConfigFragmentSearchScope,
        querier: BatchQuerier,
    ) -> AppConfigFragmentSearchResult:
        """Scope-bound search (per `(scope_type, scope_id)`)."""
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(AppConfigFragmentRow)
            result = await execute_batch_querier(db_sess, query, querier, scope=scope)
            items = [row.AppConfigFragmentRow.to_data() for row in result.rows]
            return AppConfigFragmentSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    @app_config_fragment_db_source_resilience.apply()
    async def admin_search(
        self,
        querier: BatchQuerier,
    ) -> AppConfigFragmentSearchResult:
        """Cross-scope admin search — no scope binding. Authorization
        is enforced at the service layer before this is reached."""
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(AppConfigFragmentRow)
            result = await execute_batch_querier(db_sess, query, querier)
            items = [row.AppConfigFragmentRow.to_data() for row in result.rows]
            return AppConfigFragmentSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    # ── Merged-view reads (AppConfig) ─────────────────────────────

    @staticmethod
    def _merge_chain(
        rows: Sequence[AppConfigFragmentRow],
        chain: Sequence[str],
    ) -> _MergedChain:
        """Order `rows` by `chain` (low → high) and deep-merge their
        `config` in that order. Empty result projects to `None`.

        Shared by the single-doc and search merge methods so both paths
        produce the same shape.
        """
        by_scope = {row.scope_type: row for row in rows}
        ordered = [
            by_scope[AppConfigScopeType(s)] for s in chain if AppConfigScopeType(s) in by_scope
        ]
        merged: Mapping[str, Any] = {}
        for row in ordered:
            if row.config is None:
                continue
            merged = deep_merge(merged, row.config)
        return _MergedChain(
            fragments=[row.to_data() for row in ordered],
            config=(merged or None),
        )

    @app_config_fragment_db_source_resilience.apply()
    async def get_user_app_config(
        self,
        user_id: uuid.UUID,
        config_name: str,
    ) -> AppConfigData:
        """Resolve a single AppConfig view for `(user_id, config_name)`.

        One SQL: resolves `domain_name` via a `users` subquery, joins
        `app_config_policies` to derive the chain (`scope_sources`), and
        fetches only the scope rows that participate in that chain. The
        natural-key UniqueConstraint bounds the result.
        """
        user_domain_sq = (
            sa.select(UserRow.domain_name).where(UserRow.uuid == user_id).scalar_subquery()
        )
        scope_id_match = sa.case(
            (
                AppConfigFragmentRow.scope_type == AppConfigScopeType.PUBLIC,
                sa.literal("public"),
            ),
            (
                AppConfigFragmentRow.scope_type.in_([
                    AppConfigScopeType.DOMAIN,
                    AppConfigScopeType.DOMAIN_USER_DEFAULTS,
                ]),
                user_domain_sq,
            ),
            (
                AppConfigFragmentRow.scope_type == AppConfigScopeType.USER,
                sa.literal(str(user_id)),
            ),
        )
        query = (
            sa.select(AppConfigFragmentRow, AppConfigPolicyRow.scope_sources)
            .join(
                AppConfigPolicyRow,
                AppConfigPolicyRow.config_name == AppConfigFragmentRow.name,
            )
            .where(
                AppConfigFragmentRow.name == config_name,
                AppConfigFragmentRow.scope_id == scope_id_match,
                sa.cast(AppConfigFragmentRow.scope_type, sa.Text)
                == sa.func.any(AppConfigPolicyRow.scope_sources),
            )
        )
        async with self._db.begin_readonly_session() as db_sess:
            result = (await db_sess.execute(query)).all()

        if not result:
            return AppConfigData(
                user_id=user_id,
                name=config_name,
                fragments=[],
                config=None,
            )

        # `config_name` is UNIQUE and we filtered on a single value, so
        # every result row carries the same `scope_sources`.
        chain = result[0].scope_sources
        rows = [r.AppConfigFragmentRow for r in result]
        merged = self._merge_chain(rows, chain)
        return AppConfigData(
            user_id=user_id,
            name=config_name,
            fragments=merged.fragments,
            config=merged.config,
        )

    @app_config_fragment_db_source_resilience.apply()
    async def search_user_app_configs(
        self,
        scope: UserAppConfigSearchScope,
        querier: BatchQuerier,
    ) -> AppConfigSearchResult:
        """Connection counterpart of `get_user_app_config`. Joins
        `app_config_policies` to derive each `name`'s chain, then
        groups results by `name` and feeds each group through
        `_merge_chain` to produce one `AppConfigData`.

        Pagination is applied in-memory at the distinct-`name` level
        because the natural unit (`AppConfigData`) does not map 1:1
        to a row. The GQL Connection layer that calls this method is
        responsible for wrapping the result in the appropriate cursor
        / offset envelope.
        """
        user_id = scope.user_id
        user_domain_sq = (
            sa.select(UserRow.domain_name).where(UserRow.uuid == user_id).scalar_subquery()
        )
        scope_id_match = sa.case(
            (
                AppConfigFragmentRow.scope_type == AppConfigScopeType.PUBLIC,
                sa.literal("public"),
            ),
            (
                AppConfigFragmentRow.scope_type.in_([
                    AppConfigScopeType.DOMAIN,
                    AppConfigScopeType.DOMAIN_USER_DEFAULTS,
                ]),
                user_domain_sq,
            ),
            (
                AppConfigFragmentRow.scope_type == AppConfigScopeType.USER,
                sa.literal(str(user_id)),
            ),
        )
        query = (
            sa.select(AppConfigFragmentRow, AppConfigPolicyRow.scope_sources)
            .join(
                AppConfigPolicyRow,
                AppConfigPolicyRow.config_name == AppConfigFragmentRow.name,
            )
            .where(
                AppConfigFragmentRow.scope_id == scope_id_match,
                sa.cast(AppConfigFragmentRow.scope_type, sa.Text)
                == sa.func.any(AppConfigPolicyRow.scope_sources),
            )
            .order_by(AppConfigFragmentRow.name)
        )
        async with self._db.begin_readonly_session() as db_sess:
            result_rows = (await db_sess.execute(query)).all()

        groups: dict[str, tuple[Sequence[str], list[AppConfigFragmentRow]]] = {}
        for row in result_rows:
            fragment_row = row.AppConfigFragmentRow
            chain = row.scope_sources
            entry = groups.setdefault(fragment_row.name, (chain, []))
            entry[1].append(fragment_row)

        items: list[AppConfigData] = []
        for name, (chain, rows) in groups.items():
            merged = self._merge_chain(rows, chain)
            items.append(
                AppConfigData(
                    user_id=user_id,
                    name=name,
                    fragments=merged.fragments,
                    config=merged.config,
                )
            )

        total = len(items)
        return AppConfigSearchResult(
            items=items,
            total_count=total,
            has_next_page=False,
            has_previous_page=False,
        )

    @app_config_fragment_db_source_resilience.apply()
    async def admin_search_app_configs(
        self,
        querier: BatchQuerier,
    ) -> AppConfigSearchResult:
        """Cross-user merged search (admin only). Joins `users` so
        each `(user_id, name)` combination is produced; results are
        grouped and merged the same way as `search_user_app_configs`.

        As with the per-user variant, pagination is applied at the
        merged-group level rather than at the row level — the GQL
        Connection that wraps this is responsible for envelope
        construction.
        """
        scope_id_match = sa.case(
            (
                AppConfigFragmentRow.scope_type == AppConfigScopeType.PUBLIC,
                sa.literal("public"),
            ),
            (
                AppConfigFragmentRow.scope_type.in_([
                    AppConfigScopeType.DOMAIN,
                    AppConfigScopeType.DOMAIN_USER_DEFAULTS,
                ]),
                UserRow.domain_name,
            ),
            (
                AppConfigFragmentRow.scope_type == AppConfigScopeType.USER,
                sa.cast(UserRow.uuid, sa.Text),
            ),
        )
        query = (
            sa.select(
                UserRow.uuid.label("user_id"),
                AppConfigFragmentRow,
                AppConfigPolicyRow.scope_sources,
            )
            .select_from(UserRow)
            .join(
                AppConfigFragmentRow,
                AppConfigFragmentRow.scope_id == scope_id_match,
            )
            .join(
                AppConfigPolicyRow,
                AppConfigPolicyRow.config_name == AppConfigFragmentRow.name,
            )
            .where(
                sa.cast(AppConfigFragmentRow.scope_type, sa.Text)
                == sa.func.any(AppConfigPolicyRow.scope_sources),
            )
            .order_by(UserRow.uuid, AppConfigFragmentRow.name)
        )
        async with self._db.begin_readonly_session() as db_sess:
            result_rows = (await db_sess.execute(query)).all()

        groups: dict[tuple[uuid.UUID, str], tuple[Sequence[str], list[AppConfigFragmentRow]]] = {}
        for row in result_rows:
            fragment_row = row.AppConfigFragmentRow
            chain = row.scope_sources
            entry = groups.setdefault((row.user_id, fragment_row.name), (chain, []))
            entry[1].append(fragment_row)

        items: list[AppConfigData] = []
        for (user_id, name), (chain, rows) in groups.items():
            merged = self._merge_chain(rows, chain)
            items.append(
                AppConfigData(
                    user_id=user_id,
                    name=name,
                    fragments=merged.fragments,
                    config=merged.config,
                )
            )

        total = len(items)
        return AppConfigSearchResult(
            items=items,
            total_count=total,
            has_next_page=False,
            has_previous_page=False,
        )
