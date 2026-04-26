"""UpdaterSpec for AppConfigFragment rows."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override

from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.repositories.base.updater import UpdaterSpec


@dataclass
class AppConfigFragmentUpdaterSpec(UpdaterSpec[AppConfigFragmentRow]):
    """UpdaterSpec for `app_config_fragments`.

    Only `config` is mutable — the ``(scope_type, scope_id, name)``
    natural key is fixed; changing any of those is a new row, not an
    update.
    """

    config: Mapping[str, Any]

    @property
    @override
    def row_class(self) -> type[AppConfigFragmentRow]:
        return AppConfigFragmentRow

    @override
    def build_values(self) -> dict[str, Any]:
        return {"config": dict(self.config)}
