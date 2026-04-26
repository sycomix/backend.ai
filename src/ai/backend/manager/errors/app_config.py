from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.manager.errors.common import ObjectNotFound


class AppConfigPolicyConflict(BackendAIError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/app-config-policy-conflict"
    error_title = "An app-config policy with the same config_name already exists."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.CONFLICT,
        )


class AppConfigPolicyNotFound(ObjectNotFound):
    object_name = "app-config policy"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class AppConfigFragmentConflict(BackendAIError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/app-config-fragment-conflict"
    error_title = (
        "An app-config fragment with the same (scope_type, scope_id, name) already exists."
    )

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.CONFLICT,
        )


class AppConfigFragmentNotFound(ObjectNotFound):
    object_name = "app-config fragment"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class AppConfigFragmentPolicyMissing(BackendAIError, web.HTTPConflict):
    """Raised when a fragment references a `name` without a matching policy row.

    Defense-in-depth against the required-policy invariant — normally
    the service layer rejects earlier, but the FK violation surfaces
    here if the service check is bypassed.
    """

    error_type = "https://api.backend.ai/probs/app-config-fragment-policy-missing"
    error_title = "Referenced app-config policy does not exist for this fragment."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.CONFLICT,
        )
