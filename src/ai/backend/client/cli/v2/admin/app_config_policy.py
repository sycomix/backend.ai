"""Admin CLI commands for AppConfigPolicy (bulk-only writes)."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, cast
from uuid import UUID

import click

from ai.backend.client.cli.v2.helpers import create_v2_registry, load_v2_config, print_result


@click.group(name="app-config-policy")
def app_config_policy() -> None:
    """Admin AppConfigPolicy commands (bulk-only)."""


def _load_items(items_arg: str) -> list[dict[str, Any]]:
    """Accept JSON string or `@file.json` path."""
    if items_arg.startswith("@"):
        return cast("list[dict[str, Any]]", json.loads(Path(items_arg[1:]).read_text()))
    return cast("list[dict[str, Any]]", json.loads(items_arg))


@app_config_policy.command(name="bulk-create")
@click.option(
    "--items",
    required=True,
    help=(
        "JSON list of `{config_name, scope_sources}` items, "
        "or `@path/to/items.json` to load from file."
    ),
)
def bulk_create(items: str) -> None:
    """Bulk-create policies (partial-success semantics)."""
    from ai.backend.common.dto.manager.v2.app_config_policy.request import (
        AdminAppConfigPolicyCreateItemInput,
        AdminBulkCreateAppConfigPoliciesInput,
    )

    parsed = [
        AdminAppConfigPolicyCreateItemInput.model_validate(item) for item in _load_items(items)
    ]

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.app_config_policy.admin_bulk_create(
                AdminBulkCreateAppConfigPoliciesInput(items=parsed),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@app_config_policy.command(name="bulk-update")
@click.option(
    "--items",
    required=True,
    help=("JSON list of `{id, scope_sources}` items, or `@path/to/items.json` to load from file."),
)
def bulk_update(items: str) -> None:
    """Bulk-update policy scope chains (partial-success semantics)."""
    from ai.backend.common.dto.manager.v2.app_config_policy.request import (
        AdminAppConfigPolicyUpdateItemInput,
        AdminBulkUpdateAppConfigPoliciesInput,
    )

    parsed = [
        AdminAppConfigPolicyUpdateItemInput.model_validate(item) for item in _load_items(items)
    ]

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.app_config_policy.admin_bulk_update(
                AdminBulkUpdateAppConfigPoliciesInput(items=parsed),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@app_config_policy.command(name="bulk-purge")
@click.option(
    "--ids",
    required=True,
    help="Comma-separated policy row UUIDs, or `@path/to/ids.json` for a JSON list.",
)
def bulk_purge(ids: str) -> None:
    """Bulk-purge policies by row id (partial-success semantics)."""
    from ai.backend.common.dto.manager.v2.app_config_policy.request import (
        AdminBulkPurgeAppConfigPoliciesInput,
    )

    if ids.startswith("@"):
        raw_ids = json.loads(Path(ids[1:]).read_text())
    else:
        raw_ids = [s.strip() for s in ids.split(",") if s.strip()]
    parsed_ids = [UUID(s) for s in raw_ids]

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.app_config_policy.admin_bulk_purge(
                AdminBulkPurgeAppConfigPoliciesInput(ids=parsed_ids),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
