"""V2 SDK client for the app-config policy domain.

Policies are an admin-only surface — end users observe their effects
through the merged ``AppConfig`` view (``V2AppConfigClient``), not by
reading raw policy rows.
"""

from __future__ import annotations

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.app_config_policy.request import (
    AdminBulkCreateAppConfigPoliciesInput,
    AdminBulkPurgeAppConfigPoliciesInput,
    AdminBulkUpdateAppConfigPoliciesInput,
)
from ai.backend.common.dto.manager.v2.app_config_policy.response import (
    AdminBulkCreateAppConfigPoliciesPayload,
    AdminBulkPurgeAppConfigPoliciesPayload,
    AdminBulkUpdateAppConfigPoliciesPayload,
)

_PATH = "/v2/app-config-policies"


class V2AppConfigPolicyClient(BaseDomainClient):
    """SDK client for AppConfigPolicy admin operations.

    Writes are bulk-only; single-item create / update /
    purge are intentionally absent.
    """

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
