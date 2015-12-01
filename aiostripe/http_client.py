import textwrap

import aiohttp

from aiostripe import error


def new_default_http_client(*args, **kwargs):
    return AsyncioClient(*args, **kwargs)


class HTTPClient(object):
    def __init__(self, verify_ssl_certs=True):
        self._verify_ssl_certs = verify_ssl_certs

    def request(self, method, url, headers, post_data=None):
        raise NotImplementedError('HTTPClient subclasses must implement `request`')


class AsyncioClient(HTTPClient):
    name = 'aiohttp'

    async def request(self, method, url, headers, post_data=None):
        if isinstance(post_data, str):
            post_data = post_data.encode('utf8')

        with aiohttp.ClientSession(headers=headers,
                                   skip_auto_headers=('User-Agent', 'Content-Type', 'Authorization')) as client:
            try:
                async with client.request(method.upper(), url, data=post_data) as res:
                    rbody = await res.read()
                    rstatus = res.status
                    rheaders = {k.lower(): v for k, v in res.headers.items()}
            except Exception as e:
                self._handle_request_error(e)

                assert False, 'unreachable'

        return rbody, rstatus, rheaders

    @staticmethod
    def _handle_request_error(e):
        msg = 'Unexpected error communicating with Stripe. If this problem persists, let me know at ' \
              '<alex@downtownapp.co>.'
        msg = textwrap.fill(msg) + '\n\n(Network error: %r)' % e
        raise error.APIConnectionError(msg) from e
