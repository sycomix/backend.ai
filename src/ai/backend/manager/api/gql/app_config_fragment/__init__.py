"""AppConfigFragment GraphQL API package."""

from .resolver import (
    admin_app_config_fragments,
    admin_bulk_create_app_config_fragments,
    admin_bulk_purge_app_config_fragments,
    admin_bulk_update_app_config_fragments,
    app_config_fragment,
    bulk_create_my_app_config_fragments,
    bulk_update_my_app_config_fragments,
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
    # Queries — scope-bound list belongs on DomainV2 / UserV2 child fields
    "app_config_fragment",
    "admin_app_config_fragments",
    # Bulk mutations
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
