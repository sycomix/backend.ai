"""V2 SDK client for the app-config policy domain (BEP-1052 §1)."""

from __future__ import annotations

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.app_config_policy.request import (
    AdminBulkCreateAppConfigPoliciesInput,
    AdminBulkPurgeAppConfigPoliciesInput,
    AdminBulkUpdateAppConfigPoliciesInput,
    SearchAppConfigPoliciesInput,
)
from ai.backend.common.dto.manager.v2.app_config_policy.response import (
    AdminBulkCreateAppConfigPoliciesPayload,
    AdminBulkPurgeAppConfigPoliciesPayload,
    AdminBulkUpdateAppConfigPoliciesPayload,
    GetAppConfigPolicyPayload,
    SearchAppConfigPoliciesPayload,
)

_PATH = "/v2/app-config-policies"


class V2AppConfigPolicyClient(BaseDomainClient):
    """SDK client for AppConfigPolicy operations.

    Writes are bulk-only (BEP-1052 §3); single-item create / update /
    purge are intentionally absent.
    """

    async def get(self, config_name: str) -> GetAppConfigPolicyPayload:
        """Get a single policy by `config_name`."""
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/{config_name}",
            response_model=GetAppConfigPolicyPayload,
        )

    async def search(self, request: SearchAppConfigPoliciesInput) -> SearchAppConfigPoliciesPayload:
        """Paginated policy search (any authenticated user)."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/search",
            request=request,
            response_model=SearchAppConfigPoliciesPayload,
        )

    async def admin_bulk_create(
        self, request: AdminBulkCreateAppConfigPoliciesInput
    ) -> AdminBulkCreateAppConfigPoliciesPayload:
        """Bulk-create policies (admin only, partial-success semantics)."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/bulk-create",
            request=request,
            response_model=AdminBulkCreateAppConfigPoliciesPayload,
        )

    async def admin_bulk_update(
        self, request: AdminBulkUpdateAppConfigPoliciesInput
    ) -> AdminBulkUpdateAppConfigPoliciesPayload:
        """Bulk-update policies (admin only, partial-success semantics)."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/bulk-update",
            request=request,
            response_model=AdminBulkUpdateAppConfigPoliciesPayload,
        )

    async def admin_bulk_purge(
        self, request: AdminBulkPurgeAppConfigPoliciesInput
    ) -> AdminBulkPurgeAppConfigPoliciesPayload:
        """Bulk-purge policies (admin only, partial-success semantics)."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/bulk-purge",
            request=request,
            response_model=AdminBulkPurgeAppConfigPoliciesPayload,
        )
