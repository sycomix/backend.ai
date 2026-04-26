"""REST v2 handler for the AppConfig merged-view domain."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.dto.manager.v2.app_config.request import (
    GetUserAppConfigInput,
    SearchAppConfigsInput,
    SearchMyAppConfigsInput,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.rest.v2.path_params import (
    AppConfigMyNamePathParam,
    AppConfigUserNamePathParam,
)

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.app_config import AppConfigAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class V2AppConfigHandler:
    """REST v2 handler for the merged-view `AppConfig` surface.

    Mounted at `/v2/app-configs/...`. The merged view is computed from
    fragment rows joined against `app_config_policies` and is exposed
    via its own `AppConfigAdapter`.
    """

    def __init__(self, *, adapter: AppConfigAdapter) -> None:
        self._adapter = adapter

    # ── My (self-service) ────────────────────────────────────────

    async def my_get(
        self,
        path: PathParam[AppConfigMyNamePathParam],
    ) -> APIResponse:
        """Read the caller's own merged AppConfig for `name`."""
        result = await self._adapter.my_app_config(path.parsed.name)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def my_search(
        self,
        body: BodyParam[SearchMyAppConfigsInput],
    ) -> APIResponse:
        """Paginated merged-view search over the caller's own AppConfigs."""
        result = await self._adapter.my_search_app_configs(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    # ── Admin ────────────────────────────────────────────────────

    async def admin_get(
        self,
        path: PathParam[AppConfigUserNamePathParam],
    ) -> APIResponse:
        """Read a specific user's merged AppConfig (admin only)."""
        result = await self._adapter.admin_get_user_app_config(
            GetUserAppConfigInput(user_id=path.parsed.user_id, name=path.parsed.name)
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_search(
        self,
        body: BodyParam[SearchAppConfigsInput],
    ) -> APIResponse:
        """Cross-user merged-view search (admin only)."""
        result = await self._adapter.admin_search_app_configs(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
