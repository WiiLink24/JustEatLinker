from curl_cffi import Response


class VerificationURLError(Exception):
    def __init__(self, status: int):
        super().__init__(
            f"Failed to retrieve verification URL with status code {status}"
        )


class TokenHTTPError(Exception):
    def __init__(self, status: int):
        super().__init__(f"Failed to retrieve token with status code {status}")


class AttributeRetrievalError(Exception):
    def __init__(self, status: int):
        super().__init__(
            f"Failed to retrieve linked consoles with status code {status}"
        )


class JustEatDataError(Exception):
    def __init__(self, status: int):
        super().__init__(f"Failed to get Just Eat login data with status code {status}")


class JustEatLinkError(Exception):
    def __init__(self, status: int):
        super().__init__(
            f"Failed to link Just Eat account to WiiLink account with status code {status}"
        )


class JustEat2FAError(Exception):
    def __init__(self, status: int):
        super().__init__(
            f"Received status code {status}. Make sure to enter the correct 2FA code."
        )


class JustEatResetError(Exception):
    def __init__(self, resp: Response):
        super().__init__(
            f"""Received status code {resp.status_code}.
Message: {resp.text}"""
        )
