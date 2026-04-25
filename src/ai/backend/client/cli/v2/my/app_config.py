"""Self-service CLI commands for the merged AppConfig view (BEP-1052 §5)."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, cast

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    parse_order_options,
    print_result,
)


@click.group(name="app-config")
def app_config() -> None:
    """Self-service AppConfig commands for the current user."""


@app_config.command()
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@click.option("--name-contains", type=str, default=None, help="Filter `name` by substring.")
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction. Fields: name, user_id.",
)
def search(
    limit: int | None,
    offset: int | None,
    name_contains: str | None,
    order_by: tuple[str, ...],
) -> None:
    """Paginated merged-view search over the caller's own AppConfigs."""
    from ai.backend.common.dto.manager.query import StringFilter
    from ai.backend.common.dto.manager.v2.app_config.request import (
        AppConfigFilter,
        AppConfigOrder,
        SearchMyAppConfigsInput,
    )
    from ai.backend.common.dto.manager.v2.app_config.types import AppConfigOrderField

    filter_dto: AppConfigFilter | None = None
    if name_contains is not None:
        filter_dto = AppConfigFilter(name=StringFilter(contains=name_contains))

    orders = (
        parse_order_options(order_by, AppConfigOrderField, AppConfigOrder) if order_by else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.app_config.my_search(
                SearchMyAppConfigsInput(
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


def _load_items(items_arg: str) -> list[dict[str, Any]]:
    """Accept JSON string or `@file.json` path."""
    if items_arg.startswith("@"):
        return cast("list[dict[str, Any]]", json.loads(Path(items_arg[1:]).read_text()))
    return cast("list[dict[str, Any]]", json.loads(items_arg))


@app_config.command(name="bulk-create")
@click.option(
    "--items",
    required=True,
    help="JSON list of `{name, extra_config}` items, or `@path/to/items.json`.",
)
def bulk_create(items: str) -> None:
    """Bulk-create USER-scope fragments; returns recomputed merged views."""
    from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
        BulkCreateMyAppConfigFragmentsInput,
        MyAppConfigFragmentItemInput,
    )

    parsed = [MyAppConfigFragmentItemInput.model_validate(item) for item in _load_items(items)]

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.app_config.my_bulk_create(
                BulkCreateMyAppConfigFragmentsInput(items=parsed),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@app_config.command(name="bulk-update")
@click.option(
    "--items",
    required=True,
    help="Same shape as `bulk-create`; replaces `extra_config` wholesale.",
)
def bulk_update(items: str) -> None:
    """Bulk-update USER-scope fragments; returns recomputed merged views."""
    from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
        BulkUpdateMyAppConfigFragmentsInput,
        MyAppConfigFragmentItemInput,
    )

    parsed = [MyAppConfigFragmentItemInput.model_validate(item) for item in _load_items(items)]

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.app_config.my_bulk_update(
                BulkUpdateMyAppConfigFragmentsInput(items=parsed),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
