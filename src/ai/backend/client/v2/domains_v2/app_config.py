"""V2 SDK client for the merged AppConfig view (BEP-1052 §5).

Replaces the legacy upsert-style domain/user app-config SDK; the new
surface is bulk-only writes against `USER`-scope fragments plus
merged-view reads.
"""

from __future__ import annotations

from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.app_config.request import (
    SearchAppConfigsInput,
    SearchMyAppConfigsInput,
)
from ai.backend.common.dto.manager.v2.app_config.response import (
    BulkCreateMyAppConfigFragmentsPayload,
    BulkUpdateMyAppConfigFragmentsPayload,
    GetUserAppConfigPayload,
    SearchAppConfigsPayload,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
    BulkCreateMyAppConfigFragmentsInput,
    BulkUpdateMyAppConfigFragmentsInput,
)

_PATH = "/v2/app-configs"
_FRAGMENT_PATH = "/v2/app-config-fragments"


class V2AppConfigClient(BaseDomainClient):
    """SDK client for the merged AppConfig view + self-service writes."""

    async def my_get(self, name: str) -> GetUserAppConfigPayload:
        """Read the caller's own merged AppConfig for `name`."""
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/my/{name}",
            response_model=GetUserAppConfigPayload,
        )

    async def my_search(self, request: SearchMyAppConfigsInput) -> SearchAppConfigsPayload:
        """Paginated merged-view search over the caller's own AppConfigs."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/my/search",
            request=request,
            response_model=SearchAppConfigsPayload,
        )

    async def admin_get(self, user_id: UUID, name: str) -> GetUserAppConfigPayload:
        """Read a specific user's merged AppConfig (admin only)."""
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/{user_id}/{name}",
            response_model=GetUserAppConfigPayload,
        )

    async def admin_search(self, request: SearchAppConfigsInput) -> SearchAppConfigsPayload:
        """Cross-user merged-view search (admin only)."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/search",
            request=request,
            response_model=SearchAppConfigsPayload,
        )

    async def my_bulk_create(
        self, request: BulkCreateMyAppConfigFragmentsInput
    ) -> BulkCreateMyAppConfigFragmentsPayload:
        """Bulk-create USER-scope fragments; returns recomputed merged views."""
        return await self._client.typed_request(
            "POST",
            f"{_FRAGMENT_PATH}/my/bulk-create",
            request=request,
            response_model=BulkCreateMyAppConfigFragmentsPayload,
        )

    async def my_bulk_update(
        self, request: BulkUpdateMyAppConfigFragmentsInput
    ) -> BulkUpdateMyAppConfigFragmentsPayload:
        """Bulk-update USER-scope fragments; returns recomputed merged views."""
        return await self._client.typed_request(
            "POST",
            f"{_FRAGMENT_PATH}/my/bulk-update",
            request=request,
            response_model=BulkUpdateMyAppConfigFragmentsPayload,
        )
