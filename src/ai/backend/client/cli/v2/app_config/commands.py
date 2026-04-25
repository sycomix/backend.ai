"""CLI commands for the merged AppConfig view (BEP-1052 §5).

Public entrypoint exposes only the read paths that any authenticated
user can hit. Self-service writes live under `bai my app-config`;
admin operations live under `bai admin app-config`.
"""

from __future__ import annotations

import asyncio

import click

from ai.backend.client.cli.v2.helpers import create_v2_registry, load_v2_config, print_result


@click.group(name="app-config")
def app_config() -> None:
    """Merged AppConfig commands (per-policy resolved view)."""


@app_config.command(name="my-get")
@click.argument("name", type=str)
def my_get(name: str) -> None:
    """Read the caller's own merged AppConfig for `name`."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.app_config.my_get(name)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
