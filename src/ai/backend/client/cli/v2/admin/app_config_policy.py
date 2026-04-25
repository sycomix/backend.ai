"""Admin CLI commands for AppConfigPolicy (bulk-only writes, BEP-1052 §3)."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, cast

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
        AdminAppConfigPolicyItemInput,
        AdminBulkCreateAppConfigPoliciesInput,
    )

    parsed = [AdminAppConfigPolicyItemInput.model_validate(item) for item in _load_items(items)]

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
    help=(
        "JSON list of `{config_name, scope_sources}` items, "
        "or `@path/to/items.json` to load from file."
    ),
)
def bulk_update(items: str) -> None:
    """Bulk-update policy scope chains (partial-success semantics)."""
    from ai.backend.common.dto.manager.v2.app_config_policy.request import (
        AdminAppConfigPolicyItemInput,
        AdminBulkUpdateAppConfigPoliciesInput,
    )

    parsed = [AdminAppConfigPolicyItemInput.model_validate(item) for item in _load_items(items)]

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
    "--config-names",
    required=True,
    help="Comma-separated `config_name`s, or `@path/to/names.json` for a JSON list.",
)
def bulk_purge(config_names: str) -> None:
    """Bulk-purge policies by `config_name` (partial-success semantics)."""
    from ai.backend.common.dto.manager.v2.app_config_policy.request import (
        AdminBulkPurgeAppConfigPoliciesInput,
    )

    if config_names.startswith("@"):
        names = json.loads(Path(config_names[1:]).read_text())
    else:
        names = [n.strip() for n in config_names.split(",") if n.strip()]

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.app_config_policy.admin_bulk_purge(
                AdminBulkPurgeAppConfigPoliciesInput(config_names=names),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
