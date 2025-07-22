class VerificationURLError(Exception):
    def __init__(self, status):
        super().__init__(f"Failed to retrieve verification URL with status code {status}")


class TokenHTTPError(Exception):
    def __init__(self, status):
        super().__init__(f"Failed to retrieve token with status code {status}")
