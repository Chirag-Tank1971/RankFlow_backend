class AppException(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppException):
    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message=message, status_code=404)


class DuplicateTransactionError(AppException):
    def __init__(self, message: str = "Duplicate transaction") -> None:
        super().__init__(message=message, status_code=409)
