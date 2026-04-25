"""User-facing CLI commands for AppConfigPolicy (read-only)."""

from __future__ import annotations

import asyncio

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    parse_order_options,
    print_result,
)


@click.group(name="app-config-policy")
def app_config_policy() -> None:
    """App-config policy commands (read-only; admin writes under `bai admin app-config-policy`)."""


@app_config_policy.command()
@click.argument("config_name", type=str)
def get(config_name: str) -> None:
    """Get a single policy by `config_name`."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.app_config_policy.get(config_name)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@app_config_policy.command()
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@click.option(
    "--config-name-contains", type=str, default=None, help="Filter `config_name` by substring."
)
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., created_at:desc). Fields: config_name, created_at, updated_at.",
)
def search(
    limit: int | None,
    offset: int | None,
    config_name_contains: str | None,
    order_by: tuple[str, ...],
) -> None:
    """Search policies (any authenticated user)."""
    from ai.backend.common.dto.manager.query import StringFilter
    from ai.backend.common.dto.manager.v2.app_config_policy.request import (
        AppConfigPolicyFilter,
        AppConfigPolicyOrder,
        SearchAppConfigPoliciesInput,
    )
    from ai.backend.common.dto.manager.v2.app_config_policy.types import AppConfigPolicyOrderField

    filter_dto: AppConfigPolicyFilter | None = None
    if config_name_contains is not None:
        filter_dto = AppConfigPolicyFilter(
            config_name=StringFilter(contains=config_name_contains),
        )

    orders = (
        parse_order_options(order_by, AppConfigPolicyOrderField, AppConfigPolicyOrder)
        if order_by
        else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.app_config_policy.search(
                SearchAppConfigPoliciesInput(
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
