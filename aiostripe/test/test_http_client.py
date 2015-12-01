import unittest
import warnings

import aiostripe
import aiostripe.api_requestor
import aiostripe.error
import aiostripe.http_client
from aiostripe.test.helper import Mock, AsyncMock, StripeUnitTestCase, deasyncify

VALID_API_METHODS = ('get', 'post', 'delete')


class HttpClientTests(StripeUnitTestCase):
    def setUp(self):
        super().setUp()

        self.original_filters = warnings.filters[:]
        warnings.simplefilter('ignore')

    def tearDown(self):
        warnings.filters = self.original_filters

        super().tearDown()

    def check_default(self, none_libs, expected):
        for lib in none_libs:
            setattr(aiostripe.http_client, lib, None)

        inst = aiostripe.http_client.new_default_http_client()

        self.assertTrue(isinstance(inst, expected))

    def test_new_default_http_client_asyncio(self):
        self.check_default((), aiostripe.http_client.AsyncioClient)


class ClientTestBase:
    request_client = NotImplemented

    @property
    def request_mock(self):
        return self.request_mocks[self.request_client.name]

    @property
    def valid_url(self, path='/foo'):
        return 'https://api.stripe.com%s' % path

    async def make_request(self, method, url, headers, post_data):
        client = self.request_client(verify_ssl_certs=True)
        return await client.request(method, url, headers, post_data)

    def mock_response(self, mock, body, code):
        raise NotImplementedError('You must implement this in your test subclass')

    def mock_error(self, mock):
        raise NotImplementedError('You must implement this in your test subclass')

    def check_call(self, mock, meth, url, post_data, headers):
        raise NotImplementedError('You must implement this in your test subclass')

    @deasyncify
    async def test_request(self):
        self.mock_response(self.request_mock, '{"foo": "baz"}', 200)

        for meth in VALID_API_METHODS:
            abs_url = self.valid_url
            data = ''

            if meth != 'post':
                abs_url = '%s?%s' % (abs_url, data)
                data = None

            headers = {'my-header': 'header val'}

            body, code, _ = await self.make_request(meth, abs_url, headers, data)

            self.assertEqual(200, code)
            self.assertEqual('{"foo": "baz"}', body)

            self.check_call(self.request_mock, meth, abs_url, data, headers)

    @deasyncify
    async def test_exception(self):
        self.mock_error(self.request_mock)

        await self.assertRaisesAsync(aiostripe.error.APIConnectionError, self.make_request,
                                     'get', self.valid_url, {}, None)


class RequestsVerify(object):
    def __eq__(self, other):
        return other and other.endswith('stripe/data/ca-certificates.crt')


class ContextManagerMock(Mock):
    def __enter__(self, *args, **kwargs):
        def default(*args, **kwargs):
            return type(self)(*args, **kwargs)

        return self.__dict__.get('__enter__', default)(*args, **kwargs)

    def __exit__(self, *args, **kwargs):
        def default(*args, **kwargs):
            return None

        return self.__dict__.get('__exit__', default)(*args, **kwargs)


class AsyncContextManagerMock(Mock):
    async def __aenter__(self, *args, **kwargs):
        async def default(*args, **kwargs):
            return type(self)(*args, **kwargs)

        return await self.__dict__.get('__aenter__', default)(*args, **kwargs)

    async def __aexit__(self, *args, **kwargs):
        async def default(*args, **kwargs):
            return None

        return await self.__dict__.get('__aexit__', default)(*args, **kwargs)


class AsyncioClientTests(StripeUnitTestCase, ClientTestBase):
    request_client = aiostripe.http_client.AsyncioClient

    def mock_response(self, mock, body, code):
        mock_response = mock._mock_response = Mock(name='response')
        mock_response.read = AsyncMock(return_value=body)
        mock_response.status = code
        mock_response.headers = {}

        mock_response_ctx = mock._mock_response_ctx = AsyncContextManagerMock(name='response_ctx')
        mock_response_ctx.__aenter__ = AsyncMock(return_value=mock_response)

        mock_session = mock._mock_session = Mock(name='session')
        mock_session.request = Mock(return_value=mock_response_ctx)

        mock_session_ctx = mock._mock_session_ctx = ContextManagerMock(name='ClientSession(...)')
        mock_session_ctx.__enter__ = Mock(return_value=mock_session)

        mock.ClientSession = Mock(name='ClientSession', return_value=mock_session_ctx)

    def mock_error(self, mock):
        mock.exceptions.RequestException = Exception

        mock_response_ctx = mock._mock_response_ctx = AsyncContextManagerMock(name='response_ctx')
        mock_response_ctx.__aenter__ = AsyncMock(side_effect=mock.exceptions.RequestException())

        mock_session = mock._mock_session = Mock(name='session')
        mock_session.request = Mock(return_value=mock_response_ctx)

        mock_session_ctx = mock._mock_session_ctx = ContextManagerMock(name='ClientSession(...)')
        mock_session_ctx.__enter__ = Mock(return_value=mock_session)

        mock.ClientSession = Mock(name='ClientSession', return_value=mock_session_ctx)

    def check_call(self, mock, meth, url, post_data, headers):
        args, kwargs = mock.ClientSession.call_args
        self.assertEqual(HeadersMatcher(kwargs['headers']), headers)
        mock._mock_session.request.assert_called_with(MethMatcher(meth), url, data=DataMatcher(post_data))
        mock._mock_response.read.assert_called_with()


class HeadersMatcher(object):
    def __init__(self, expected):
        self.expected = expected

    @staticmethod
    def transform(headers):
        return {k.lower(): v for k, v in headers.items()}

    def __eq__(self, other):
        return self.transform(self.expected) == self.transform(other)

    def __repr__(self):
        return '<MethMatcher %r>' % self.expected


class MethMatcher(object):
    def __init__(self, expected):
        self.expected = expected

    def __eq__(self, other):
        return self.expected.lower() == other.lower()

    def __repr__(self):
        return '<MethMatcher %r>' % self.expected


class DataMatcher(object):
    def __init__(self, expected):
        self.expected = expected

    @staticmethod
    def maybe_encode(value):
        if isinstance(value, str):
            return value.encode('utf8')

        return value

    def __eq__(self, other):
        return self.maybe_encode(self.expected) == self.maybe_encode(other)

    def __repr__(self):
        return '<DataMatcher %r>' % self.expected


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

        values = [t for t in aiostripe.api_requestor._api_encode(body)]

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

        values = [t for t in aiostripe.api_requestor._api_encode(body)]

        self.assertTrue(('foo[][dob][month]', 1) in values)
        self.assertTrue(('foo[][name]', 'bat') in values)


if __name__ == '__main__':
    unittest.main()
