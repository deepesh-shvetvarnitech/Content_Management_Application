from fastapi import status


class AppException(Exception):
    """Base class for application-specific exceptions."""

    def __init__(
        self,
        message: str = "An application error occurred",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        code: str = "APPLICATION_ERROR",
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.code = code
        super().__init__(message)


class UserAlreadyExistsException(AppException):
    def __init__(self, message: str = "User already exists") -> None:
        super().__init__(message, status.HTTP_409_CONFLICT, "USER_ALREADY_EXISTS")


class InvalidCredentialsException(AppException):
    def __init__(self, message: str = "Invalid email or password") -> None:
        super().__init__(message, status.HTTP_401_UNAUTHORIZED, "INVALID_CREDENTIALS")


class UserNotVerifiedException(AppException):
    def __init__(self, message: str = "Email verification required") -> None:
        super().__init__(message, status.HTTP_403_FORBIDDEN, "USER_NOT_VERIFIED")


class UserInactiveException(AppException):
    def __init__(self, message: str = "User account is inactive") -> None:
        super().__init__(message, status.HTTP_403_FORBIDDEN, "USER_INACTIVE")


class BlogNotFoundException(AppException):
    def __init__(self, message: str = "Blog not found") -> None:
        super().__init__(message, status.HTTP_404_NOT_FOUND, "BLOG_NOT_FOUND")


class CategoryNotFoundException(AppException):
    def __init__(self, message: str = "Category not found") -> None:
        super().__init__(message, status.HTTP_404_NOT_FOUND, "CATEGORY_NOT_FOUND")


class CommentNotFoundException(AppException):
    def __init__(self, message: str = "Comment not found") -> None:
        super().__init__(message, status.HTTP_404_NOT_FOUND, "COMMENT_NOT_FOUND")


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Authentication required") -> None:
        super().__init__(message, status.HTTP_401_UNAUTHORIZED, "UNAUTHORIZED")


class ForbiddenException(AppException):
    def __init__(self, message: str = "Permission denied") -> None:
        super().__init__(message, status.HTTP_403_FORBIDDEN, "FORBIDDEN")


class ResourceNotFoundException(AppException):
    def __init__(
        self,
        message: str = "Resource not found",
        code: str = "RESOURCE_NOT_FOUND",
    ) -> None:
        super().__init__(message, status.HTTP_404_NOT_FOUND, code)


class ResourceConflictException(AppException):
    def __init__(
        self,
        message: str = "Resource already exists",
        code: str = "RESOURCE_CONFLICT",
    ) -> None:
        super().__init__(message, status.HTTP_409_CONFLICT, code)


class ServiceUnavailableException(AppException):
    def __init__(
        self,
        message: str = "Service temporarily unavailable",
        code: str = "SERVICE_UNAVAILABLE",
    ) -> None:
        super().__init__(message, status.HTTP_503_SERVICE_UNAVAILABLE, code)
