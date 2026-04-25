"""AppConfigFragment GraphQL API package."""

from .resolver import (
    admin_app_config_fragments,
    admin_bulk_create_app_config_fragments,
    admin_bulk_purge_app_config_fragments,
    admin_bulk_update_app_config_fragments,
    app_config_fragment,
    bulk_create_my_app_config_fragments,
    bulk_update_my_app_config_fragments,
    scoped_app_config_fragments,
)
from .types import (
    AppConfigFragmentFilterGQL,
    AppConfigFragmentGQL,
    AppConfigFragmentKeyInputGQL,
    AppConfigFragmentOrderByGQL,
    AppConfigFragmentOrderFieldGQL,
    AppConfigScopeTypeGQL,
)

__all__ = [
    # Queries
    "app_config_fragment",
    "scoped_app_config_fragments",
    "admin_app_config_fragments",
    # Bulk mutations (BEP-1052 §3 — bulk-only)
    "admin_bulk_create_app_config_fragments",
    "admin_bulk_update_app_config_fragments",
    "admin_bulk_purge_app_config_fragments",
    "bulk_create_my_app_config_fragments",
    "bulk_update_my_app_config_fragments",
    # Types
    "AppConfigFragmentGQL",
    "AppConfigScopeTypeGQL",
    "AppConfigFragmentFilterGQL",
    "AppConfigFragmentOrderByGQL",
    "AppConfigFragmentOrderFieldGQL",
    "AppConfigFragmentKeyInputGQL",
]
