"""CreatorSpec for AppConfigFragment rows."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.manager.errors.app_config import (
    AppConfigFragmentConflict,
    AppConfigFragmentPolicyMissing,
)
from ai.backend.manager.errors.repository import (
    ForeignKeyViolationError,
    UniqueConstraintViolationError,
)
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.repositories.base.creator import CreatorSpec
from ai.backend.manager.repositories.base.types import IntegrityErrorCheck


@dataclass
class AppConfigFragmentCreatorSpec(CreatorSpec[AppConfigFragmentRow]):
    """CreatorSpec for `app_config_fragments`.

    Maps DB constraint violations onto typed domain errors:
    - ``(scope_type, scope_id, name)`` UNIQUE → :class:`AppConfigFragmentConflict`
    - ``name`` FK to `app_config_policies.config_name` →
      :class:`AppConfigFragmentPolicyMissing` (required-policy invariant
      enforced as defense-in-depth).
    """

    scope_type: str
    scope_id: str
    name: str
    extra_config: Mapping[str, Any]

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                error=AppConfigFragmentConflict(
                    extra_msg=(
                        f"Duplicate fragment for ({self.scope_type}, {self.scope_id}, {self.name})"
                    ),
                ),
            ),
            IntegrityErrorCheck(
                violation_type=ForeignKeyViolationError,
                error=AppConfigFragmentPolicyMissing(
                    extra_msg=f"No app_config_policies row for name={self.name}",
                ),
            ),
        )

    @override
    def build_row(self) -> AppConfigFragmentRow:
        return AppConfigFragmentRow(
            scope_type=self.scope_type,
            scope_id=self.scope_id,
            name=self.name,
            extra_config=dict(self.extra_config),
        )
