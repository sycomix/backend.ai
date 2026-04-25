"""Route registration for v2 AppConfig merged-view endpoints (BEP-1052 §5)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required, superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2AppConfigHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_app_config_routes(
    handler: V2AppConfigHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all v2 `/v2/app-configs/*` routes (BEP-1052 §4).

    Read-only surface — writes go through `/v2/app-config-fragments/...`
    (§4). Self-service routes land under the `/my/...` prefix so the
    adapter can pin `(USER, current_user)` internally; admin routes
    allow targeting any user id.
    """
    reg = RouteRegistry.create("app-configs", route_deps.cors_options)

    # Self-service
    reg.add("GET", "/my/{name}", handler.my_get, middlewares=[auth_required])
    reg.add("POST", "/my/search", handler.my_search, middlewares=[auth_required])
    # Admin
    reg.add("POST", "/search", handler.admin_search, middlewares=[superadmin_required])
    reg.add("GET", "/{user_id}/{name}", handler.admin_get, middlewares=[superadmin_required])

    return reg
