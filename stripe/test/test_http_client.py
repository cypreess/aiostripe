import unittest2
from mock import Mock

import stripe
from stripe.test.helper import StripeUnitTestCase, desync

VALID_API_METHODS = ('get', 'post', 'delete')


class HttpClientTests(StripeUnitTestCase):
    def setUp(self):
        super(HttpClientTests, self).setUp()

        self.original_filters = stripe.http_client.warnings.filters[:]
        stripe.http_client.warnings.simplefilter('ignore')

    def tearDown(self):
        stripe.http_client.warnings.filters = self.original_filters

        super(HttpClientTests, self).tearDown()

    def check_default(self, none_libs, expected):
        for lib in none_libs:
            setattr(stripe.http_client, lib, None)

        inst = stripe.http_client.new_default_http_client()

        self.assertTrue(isinstance(inst, expected))

    def test_new_default_http_client_asyncio(self):
        self.check_default((),
                           stripe.http_client.AsyncioClient)


class ClientTestBase():
    @property
    def request_mock(self):
        return self.request_mocks[self.request_client.name]

    @property
    def valid_url(self, path='/foo'):
        return 'https://api.stripe.com%s' % (path,)

    def make_request(self, method, url, headers, post_data):
        client = self.request_client(verify_ssl_certs=True)
        return client.request(method, url, headers, post_data)

    def mock_response(self, body, code):
        raise NotImplementedError(
            'You must implement this in your test subclass')

    def mock_error(self, error):
        raise NotImplementedError(
            'You must implement this in your test subclass')

    def check_call(self, meth, abs_url, headers, params):
        raise NotImplementedError(
            'You must implement this in your test subclass')

    @desync
    async def test_request(self):
        self.mock_response(self.request_mock, '{"foo": "baz"}', 200)

        for meth in VALID_API_METHODS:
            abs_url = self.valid_url
            data = ''

            if meth != 'post':
                abs_url = '%s?%s' % (abs_url, data)
                data = None

            headers = {'my-header': 'header val'}

            body, code, _ = await self.make_request(
                meth, abs_url, headers, data)

            self.assertEqual(200, code)
            self.assertEqual('{"foo": "baz"}', body)

            self.check_call(self.request_mock, meth, abs_url,
                            data, headers)

    def test_exception(self):
        # FIXME: async assert raises?
        self.mock_error(self.request_mock)
        self.assertRaises(stripe.error.APIConnectionError,
                          self.make_request,
                          'get', self.valid_url, {}, None)


class RequestsVerify(object):
    def __eq__(self, other):
        return other and other.endswith('stripe/data/ca-certificates.crt')


class AsyncioClientTests(StripeUnitTestCase, ClientTestBase):
    request_client = stripe.http_client.AsyncioClient

    # FIXME: find the way to mock async aiohttp methods

    def mock_response(self, mock, body, code):
        raise NotImplementedError()

    def mock_error(self, mock):
        raise NotImplementedError()

    def check_call(self, mock, meth, url, post_data, headers):
        raise NotImplementedError()


class APIEncodeTest(StripeUnitTestCase):
    def test_encode_dict(self):
        body = {
            'foo': {
                'dob': {
                    'month': 1,
                },
                'name': 'bat'
            },
        }

        values = [t for t in stripe.api_requestor._api_encode(body)]

        self.assertTrue(('foo[dob][month]', 1) in values)
        self.assertTrue(('foo[name]', 'bat') in values)

    def test_encode_array(self):
        body = {
            'foo': [{
                'dob': {
                    'month': 1,
                },
                'name': 'bat'
            }],
        }

        values = [t for t in stripe.api_requestor._api_encode(body)]

        self.assertTrue(('foo[][dob][month]', 1) in values)
        self.assertTrue(('foo[][name]', 'bat') in values)


if __name__ == '__main__':
    unittest2.main()
