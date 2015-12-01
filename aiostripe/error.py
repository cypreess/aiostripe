# Exceptions
class StripeError(Exception):
    def __init__(self, message=None, http_body=None, http_status=None, json_body=None, headers=None):
        super().__init__(message)

        if http_body and isinstance(http_body, bytes):
            try:
                http_body = http_body.decode('utf8')
            except ValueError:
                http_body = '<Could not decode body as utf-8. Please report to support@stripe.com>'

        self._message = message
        self.http_body = http_body
        self.http_status = http_status
        self.json_body = json_body
        self.headers = headers or {}
        self.request_id = self.headers.get('request-id')

    def __str__(self):
        if self.request_id is not None:
            return 'Request %s: %s' % (self.request_id, self._message)
        else:
            return self._message


class APIError(StripeError):
    pass


class APIConnectionError(StripeError):
    pass


class CardError(StripeError):
    def __init__(self, message, param, code, http_body=None, http_status=None, json_body=None, headers=None):
        super().__init__(message, http_body, http_status, json_body, headers)
        self.param = param
        self.code = code


class InvalidRequestError(StripeError):
    def __init__(self, message, param, http_body=None, http_status=None, json_body=None, headers=None):
        super().__init__(message, http_body, http_status, json_body, headers)
        self.param = param


class AuthenticationError(StripeError):
    pass


class RateLimitError(StripeError):
    pass
