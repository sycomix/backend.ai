"""User-facing CLI commands for AppConfigFragment (read-only at this layer)."""

from __future__ import annotations

import asyncio

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    parse_order_options,
    print_result,
)


@click.group(name="app-config-fragment")
def app_config_fragment() -> None:
    """App-config fragment commands (reads + scope-bound search; writes under `admin`)."""


@app_config_fragment.command()
@click.argument("scope_type", type=str)
@click.argument("scope_id", type=str)
@click.argument("name", type=str)
def get(scope_type: str, scope_id: str, name: str) -> None:
    """Get a single fragment by `(scope_type, scope_id, name)`."""
    from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
        AppConfigFragmentKeyInput,
    )
    from ai.backend.common.dto.manager.v2.app_config_fragment.types import AppConfigScopeType

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.app_config_fragment.get(
                AppConfigFragmentKeyInput(
                    scope_type=AppConfigScopeType(scope_type),
                    scope_id=scope_id,
                    name=name,
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@app_config_fragment.command(name="scope-search")
@click.argument("scope_type", type=str)
@click.argument("scope_id", type=str)
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@click.option("--name-contains", type=str, default=None, help="Filter `name` by substring.")
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction. Fields: scope_type, scope_id, name, created_at, updated_at.",
)
def scope_search(
    scope_type: str,
    scope_id: str,
    limit: int | None,
    offset: int | None,
    name_contains: str | None,
    order_by: tuple[str, ...],
) -> None:
    """Scope-bound fragment search — caller pins `(scope_type, scope_id)`."""
    from ai.backend.common.dto.manager.query import StringFilter
    from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
        AppConfigFragmentFilter,
        AppConfigFragmentOrder,
        SearchAppConfigFragmentsInput,
    )
    from ai.backend.common.dto.manager.v2.app_config_fragment.types import (
        AppConfigFragmentOrderField,
    )

    filter_dto: AppConfigFragmentFilter | None = None
    if name_contains is not None:
        filter_dto = AppConfigFragmentFilter(name=StringFilter(contains=name_contains))

    orders = (
        parse_order_options(order_by, AppConfigFragmentOrderField, AppConfigFragmentOrder)
        if order_by
        else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.app_config_fragment.scope_search(
                scope_type=scope_type,
                scope_id=scope_id,
                request=SearchAppConfigFragmentsInput(
                    filter=filter_dto,
                    order=orders,
                    limit=limit,
                    offset=offset,
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
