"""
Request DTOs for AppConfig (merged view) DTO v2 (BEP-1052 §5).
"""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter

from .types import AppConfigOrderField, OrderDirection

__all__ = (
    "AppConfigFilter",
    "AppConfigOrder",
    "GetUserAppConfigInput",
    "SearchAppConfigsInput",
    "SearchMyAppConfigsInput",
)


class GetUserAppConfigInput(BaseRequestModel):
    """Input for reading a single merged AppConfig for a target user
    (admin path — the `my` variant resolves the user internally)."""

    user_id: UUID = Field(description="Target user's UUID.")
    name: str = Field(description="Policy / config name.")


class AppConfigFilter(BaseRequestModel):
    """Filter for AppConfig merged-view search."""

    name: StringFilter | None = Field(default=None, description="Filter by policy name.")
    user_id: UUIDFilter | None = Field(
        default=None,
        description="Filter by target user id (admin cross-user search only).",
    )


class AppConfigOrder(BaseRequestModel):
    """Order specification for AppConfig merged-view results."""

    field: AppConfigOrderField = Field(description="Field to order by.")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction.")


class _AppConfigSearchInputBase(BaseRequestModel):
    filter: AppConfigFilter | None = Field(default=None, description="Filter conditions.")
    order: list[AppConfigOrder] | None = Field(default=None, description="Order specifications.")
    first: int | None = Field(default=None, ge=1, description="Number of items from the start.")
    after: str | None = Field(default=None, description="Cursor to paginate forward from.")
    last: int | None = Field(default=None, ge=1, description="Number of items from the end.")
    before: str | None = Field(default=None, description="Cursor to paginate backward from.")
    limit: int | None = Field(default=None, ge=1, le=1000, description="Maximum items to return.")
    offset: int | None = Field(default=None, ge=0, description="Number of items to skip.")


class SearchMyAppConfigsInput(_AppConfigSearchInputBase):
    """Input for self-service merged-view search (`/v2/app-configs/my/search`).

    The adapter pins the caller as the user scope; no `user_id` argument
    is accepted here (BEP-1052 §5 — `filter.userId` is ignored).
    """


class SearchAppConfigsInput(_AppConfigSearchInputBase):
    """Input for admin cross-user merged-view search.

    Optional `filter.user_id` pins the search to a single user.
    """
