from fastapi import HTTPException, status


class BaseAppException(HTTPException):
    """Base application exception providing standardized JSON error output."""
    def __init__(
        self,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        message: str = "An application error occurred",
        error_code: str = "APP_ERROR",
        field: str | None = None,
        headers: dict[str, str] | None = None,
    ):
        self.message = message
        self.error_code = error_code
        self.field = field
        super().__init__(status_code=status_code, detail=message, headers=headers)


class NotFoundException(BaseAppException):
    def __init__(self, message: str = "Resource not found", field: str | None = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=message,
            error_code="NOT_FOUND",
            field=field,
        )


class UnauthorizedException(BaseAppException):
    def __init__(
        self,
        message: str = "Unauthorized",
        headers: dict[str, str] | None = None,
        error_code: str = "UNAUTHORIZED",
    ):
        auth_headers = {"WWW-Authenticate": 'Bearer error="invalid_token"'}
        if headers:
            auth_headers.update(headers)
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message=message,
            error_code=error_code,
            headers=auth_headers,
        )


class ForbiddenException(BaseAppException):
    def __init__(self, message: str = "Access forbidden"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message=message,
            error_code="FORBIDDEN",
        )


class ConflictException(BaseAppException):
    def __init__(self, message: str = "Data conflict", field: str | None = None):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            message=message,
            error_code="CONFLICT",
            field=field,
        )
