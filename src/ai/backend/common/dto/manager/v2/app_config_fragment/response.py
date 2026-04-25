"""
Response DTOs for app_config_fragment DTO v2.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

from .types import AppConfigScopeType

__all__ = (
    "AdminBulkCreateAppConfigFragmentsPayload",
    "AdminBulkPurgeAppConfigFragmentsPayload",
    "AdminBulkUpdateAppConfigFragmentsPayload",
    "AppConfigFragmentBulkError",
    "AppConfigFragmentNode",
    "GetAppConfigFragmentPayload",
    "PurgeAppConfigFragmentKey",
    "SearchAppConfigFragmentsPayload",
)


class AppConfigFragmentNode(BaseResponseModel):
    """Node representing a single fragment row (raw per-scope payload)."""

    id: UUID = Field(description="Row ID.")
    scope_type: AppConfigScopeType = Field(description="Scope type.")
    scope_id: str = Field(description="Scope id.")
    name: str = Field(description="Policy name (FK target).")
    extra_config: dict[str, Any] | None = Field(
        default=None, description="Raw configuration payload, or null."
    )
    created_at: datetime = Field(description="Creation timestamp.")
    updated_at: datetime | None = Field(default=None, description="Last update timestamp.")


class GetAppConfigFragmentPayload(BaseResponseModel):
    """Payload returned after reading a single fragment by natural key."""

    item: AppConfigFragmentNode | None = Field(default=None, description="Fragment data, or null.")


class SearchAppConfigFragmentsPayload(BaseResponseModel):
    """Payload for paginated fragment search results."""

    items: list[AppConfigFragmentNode] = Field(description="Fragments matching the filter.")
    total_count: int = Field(description="Total number of fragments matching the filter.")
    has_next_page: bool = Field(default=False, description="Whether there is a next page.")
    has_previous_page: bool = Field(default=False, description="Whether there is a previous page.")


# ── Bulk mutation payloads (BEP-1052 §3, bulk-only writes) ───────


class AppConfigFragmentBulkError(BaseResponseModel):
    """Per-item failure information for bulk Fragment mutations."""

    index: int = Field(description="Original position in the input list.")
    scope_type: AppConfigScopeType = Field(description="Scope type of the failed row.")
    scope_id: str = Field(description="Scope id of the failed row.")
    name: str = Field(description="Policy name of the failed row.")
    message: str = Field(description="Reason for the failure.")


class PurgeAppConfigFragmentKey(BaseResponseModel):
    """Natural-key identifier returned by bulk purge payloads."""

    scope_type: AppConfigScopeType = Field(description="Scope type.")
    scope_id: str = Field(description="Scope id.")
    name: str = Field(description="Policy name.")


class AdminBulkCreateAppConfigFragmentsPayload(BaseResponseModel):
    """Payload for `adminBulkCreateAppConfigFragments`."""

    created: list[AppConfigFragmentNode] = Field(description="Created fragments.")
    failed: list[AppConfigFragmentBulkError] = Field(description="Per-item failures.")


class AdminBulkUpdateAppConfigFragmentsPayload(BaseResponseModel):
    """Payload for `adminBulkUpdateAppConfigFragments`."""

    updated: list[AppConfigFragmentNode] = Field(description="Updated fragments.")
    failed: list[AppConfigFragmentBulkError] = Field(description="Per-item failures.")


class AdminBulkPurgeAppConfigFragmentsPayload(BaseResponseModel):
    """Payload for `adminBulkPurgeAppConfigFragments`."""

    purged: list[PurgeAppConfigFragmentKey] = Field(
        description="Keys of rows actually removed (absent keys are no-oped).",
    )
    failed: list[AppConfigFragmentBulkError] = Field(description="Per-item failures.")


# `BulkCreateMyAppConfigFragmentsPayload` / `BulkUpdateMyAppConfigFragmentsPayload`
# return recomputed merged `AppConfig` views — they live in
# `common/dto/manager/v2/app_config/response.py` (added with the
# merged-view DTO in the GQL/REST layer) to keep `AppConfigNode` as the
# single source of truth and avoid a circular import.
