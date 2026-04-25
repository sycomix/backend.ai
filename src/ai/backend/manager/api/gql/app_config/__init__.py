"""AppConfig (merged view) GraphQL API package (BEP-1052 §5)."""

from .resolver import (
    admin_app_configs,
    my_app_configs,
    public_app_config_fragments,
)
from .types import (
    AppConfigFilterGQL,
    AppConfigGQL,
    AppConfigOrderByGQL,
    AppConfigOrderFieldGQL,
)

__all__ = [
    # Queries
    "my_app_configs",
    "admin_app_configs",
    "public_app_config_fragments",
    # Types
    "AppConfigGQL",
    "AppConfigFilterGQL",
    "AppConfigOrderByGQL",
    "AppConfigOrderFieldGQL",
]
