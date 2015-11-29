import calendar
import datetime
import json
import platform
import time
import urllib.parse

from stripe.logger import logger

import stripe
from stripe import error, http_client, version
from stripe.multipart_data_generator import MultipartDataGenerator


def _encode_datetime(dttime):
    if dttime.tzinfo and dttime.tzinfo.utcoffset(dttime) is not None:
        utc_timestamp = calendar.timegm(dttime.utctimetuple())
    else:
        utc_timestamp = time.mktime(dttime.timetuple())

    return int(utc_timestamp)


def _encode_nested_dict(key, data, fmt='%s[%s]'):
    d = {}
    for subkey, subvalue in data.items():
        d[fmt % (key, subkey)] = subvalue
    return d


def _api_encode(data):
    for key, value in data.items():
        if value is None:
            continue
        elif hasattr(value, 'stripe_id'):
            yield (key, value.stripe_id)
        elif isinstance(value, list) or isinstance(value, tuple):
            for sv in value:
                if isinstance(sv, dict):
                    subdict = _encode_nested_dict(key, sv, fmt='%s[][%s]')
                    for k, v in _api_encode(subdict):
                        yield k, v
                else:
                    yield ("%s[]" % key), sv
        elif isinstance(value, dict):
            subdict = _encode_nested_dict(key, value)
            for subkey, subvalue in _api_encode(subdict):
                yield subkey, subvalue
        elif isinstance(value, datetime.datetime):
            yield key, _encode_datetime(value)
        else:
            yield key, value


def _build_api_url(url, query):
    scheme, netloc, path, base_query, fragment = urllib.parse.urlsplit(url)

    if base_query:
        query = '%s&%s' % (base_query, query)

    return urllib.parse.urlunsplit((scheme, netloc, path, query, fragment))


class APIRequestor(object):
    def __init__(self, key=None, client=None, api_base=None, account=None):
        if api_base:
            self.api_base = api_base
        else:
            self.api_base = stripe.api_base
        self.api_key = key
        self.stripe_account = account

        from stripe import verify_ssl_certs as verify

        self._client = client or stripe.default_http_client or \
                       http_client.new_default_http_client(verify_ssl_certs=verify)

    async def request(self, method, url, params=None, headers=None):
        rbody, rcode, rheaders, my_api_key = await self.request_raw(method.lower(), url, params, headers)
        resp = self.interpret_response(rbody, rcode, rheaders)
        return resp, my_api_key

    @staticmethod
    def handle_api_error(rbody, rcode, resp, rheaders):
        try:
            err = resp['error']
        except (KeyError, TypeError):
            raise error.APIError('Invalid response object from API: %r (HTTP response code was %d)' % (rbody, rcode),
                                 rbody, rcode, resp)

        # Rate limits were previously coded as 400's with code 'rate_limit'
        if rcode == 429 or (rcode == 400 and err.get('code') == 'rate_limit'):
            raise error.RateLimitError(err.get('message'), rbody, rcode, resp, rheaders)
        elif rcode in [400, 404]:
            raise error.InvalidRequestError(err.get('message'), err.get('param'), rbody, rcode, resp, rheaders)
        elif rcode == 401:
            raise error.AuthenticationError(err.get('message'), rbody, rcode, resp, rheaders)
        elif rcode == 402:
            raise error.CardError(err.get('message'), err.get('param'), err.get('code'), rbody, rcode, resp, rheaders)
        else:
            raise error.APIError(err.get('message'), rbody, rcode, resp, rheaders)

    async def request_raw(self, method, url, params=None, supplied_headers=None):
        """
        Mechanism for issuing an API call
        """
        from stripe import api_version

        if self.api_key:
            my_api_key = self.api_key
        else:
            from stripe import api_key
            my_api_key = api_key

        if my_api_key is None:
            raise error.AuthenticationError('No API key provided. (HINT: set your API key using '
                                            '"stripe.api_key = <API-KEY>"). You can generate API keys from the Stripe '
                                            'web interface.  See https://stripe.com/api for details, or email '
                                            'support@stripe.com if you have any questions.')

        abs_url = '%s%s' % (self.api_base, url)

        encoded_params = urllib.parse.urlencode(list(_api_encode(params or {})))

        if method == 'get' or method == 'delete':
            if params:
                abs_url = _build_api_url(abs_url, encoded_params)

            post_data = None
        elif method == 'post':
            if supplied_headers is not None and supplied_headers.get('Content-Type') == 'multipart/form-data':
                generator = MultipartDataGenerator()
                generator.add_params(params or {})
                post_data = generator.get_post_data()
                supplied_headers['Content-Type'] = 'multipart/form-data; boundary=%s' % generator.boundary
            else:
                post_data = encoded_params
        else:
            raise error.APIConnectionError('Unrecognized HTTP method %r.  This may indicate a bug in the Stripe '
                                           'bindings.  Please contact support@stripe.com for assistance.' % method)

        ua = {
            'bindings_version': version.VERSION,
            'lang': 'python',
            'publisher': 'stripe',
            'httplib': self._client.name,
        }
        for attr, func in [['lang_version', platform.python_version],
                           ['platform', platform.platform],
                           ['uname', lambda: ' '.join(platform.uname())]]:
            try:
                val = func()
            except Exception as e:
                val = '!! %s' % e

            ua[attr] = val

        headers = {
            'X-Stripe-Client-User-Agent': json.dumps(ua),
            'User-Agent': 'Stripe/v1 PythonBindings/%s' % version.VERSION,
            'Authorization': 'Bearer %s' % my_api_key,
        }

        if self.stripe_account:
            headers['Stripe-Account'] = self.stripe_account

        if method == 'post':
            headers['Content-Type'] = 'application/x-www-form-urlencoded'

        if api_version is not None:
            headers['Stripe-Version'] = api_version

        if supplied_headers is not None:
            for key, value in supplied_headers.items():
                headers[key] = value

        rbody, rcode, rheaders = await self._client.request(method, abs_url, headers, post_data)

        logger.info('%s %s %d', method.upper(), abs_url, rcode)
        logger.debug('API request to %s returned (response code, response body) of (%d, %r)', abs_url, rcode, rbody)

        return rbody, rcode, rheaders, my_api_key

    def interpret_response(self, rbody, rcode, rheaders):
        try:
            if hasattr(rbody, 'decode'):
                rbody = rbody.decode('utf-8')

            resp = json.loads(rbody)
        except Exception:
            raise error.APIError('Invalid response body from API: %s (HTTP response code was %d)' % (rbody, rcode),
                                 rbody, rcode, rheaders)

        if not (200 <= rcode < 300):
            self.handle_api_error(rbody, rcode, resp, rheaders)

        return resp
