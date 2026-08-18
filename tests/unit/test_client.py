#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Unit tests for tvdinner.core RESTClient.

Runs under plain pytest with ansible installed (pip). The HTTP layer is
mocked at ansible.module_utils.urls.Request so no network is needed.
"""
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import io
import json
import unittest

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

from ansible.module_utils.six.moves.urllib.error import HTTPError

from ansible_collections.tvdinner.core.plugins.module_utils.client import (  # noqa: E402
    AUTH_BEARER,
    AUTH_TOKEN,
    RESTClient,
    TVDinnerError,
    TVDinnerNotFoundError,
)


class FakeResponse(object):
    def __init__(self, status, body=None):
        self.status = status
        self._body = body

    def getcode(self):
        return self.status

    def read(self):
        return self._body


class TestRESTClient(unittest.TestCase):

    def _client(self, **kwargs):
        return RESTClient('https://api.example.com/', 'sekrit', **kwargs)

    def test_base_url_trailing_slash_stripped(self):
        client = self._client()
        self.assertEqual(client.base_url, 'https://api.example.com')

    def test_bearer_auth_headers(self):
        headers = self._client()._auth_headers()
        self.assertEqual(headers, {'Authorization': 'Bearer sekrit'})

    def test_token_auth_headers(self):
        headers = self._client(auth_style=AUTH_TOKEN)._auth_headers()
        self.assertEqual(headers, {'Authorization': 'token sekrit'})

    def test_header_auth_requires_name(self):
        with self.assertRaises(TVDinnerError):
            RESTClient('https://x', 'sekrit', auth_style='header')

    def test_header_auth_custom_name(self):
        client = RESTClient('https://x', 'sekrit', auth_style='header',
                            auth_header_name='X-API-Key')
        self.assertEqual(client._auth_headers(), {'X-API-Key': 'sekrit'})

    def test_no_auth(self):
        client = RESTClient('https://x', auth_style='none')
        self.assertEqual(client._auth_headers(), {})

    @patch('ansible.module_utils.urls.Request.open')
    def test_get_parses_json(self, open_mock):
        open_mock.return_value = FakeResponse(200, json.dumps({'a': 1}).encode())
        result = self._client().request('GET', '/things')
        self.assertEqual(result, {'a': 1})
        kwargs = open_mock.call_args[1]
        self.assertEqual(kwargs['url'], 'https://api.example.com/things')
        self.assertEqual(kwargs['headers']['Authorization'], 'Bearer sekrit')

    @patch('ansible.module_utils.urls.Request.open')
    def test_params_encoded(self, open_mock):
        open_mock.return_value = FakeResponse(200, b'null')
        self._client().request('GET', '/things', params={'page': 2})
        url = open_mock.call_args[1]['url']
        self.assertIn('page=2', url)

    @patch('ansible.module_utils.urls.Request.open')
    def test_params_none_values_dropped(self, open_mock):
        open_mock.return_value = FakeResponse(200, b'[]')
        self._client().request('GET', '/things', params={'a': 'yes', 'b': None})
        url = open_mock.call_args[1]['url']
        self.assertIn('a=yes', url)
        self.assertNotIn('b=', url)

    @patch('ansible.module_utils.urls.Request.open')
    def test_204_returns_none(self, open_mock):
        open_mock.return_value = FakeResponse(204)
        self.assertIsNone(self._client().request('DELETE', '/things/1'))

    @patch('ansible.module_utils.urls.Request.open')
    def test_404_raises_not_found(self, open_mock):
        open_mock.side_effect = HTTPError(
            'url', 404, 'Not Found', {}, io.BytesIO(b'{"message": "nope"}'))
        with self.assertRaises(TVDinnerNotFoundError) as ctx:
            self._client().request('GET', '/things/1')
        self.assertEqual(ctx.exception.status_code, 404)

    @patch('ansible.module_utils.urls.Request.open')
    def test_404_ok_not_found_returns_none(self, open_mock):
        open_mock.side_effect = HTTPError(
            'url', 404, 'Not Found', {}, io.BytesIO(b''))
        self.assertIsNone(self._client().request('GET', '/things/1', ok_not_found=True))

    @patch('ansible.module_utils.urls.Request.open')
    def test_error_message_from_json(self, open_mock):
        open_mock.side_effect = HTTPError(
            'url', 400, 'Bad Request', {}, io.BytesIO(b'{"message": "bad input"}'))
        with self.assertRaises(TVDinnerError) as ctx:
            self._client().request('POST', '/things', data={'x': 1})
        self.assertIn('bad input', str(ctx.exception))
        self.assertEqual(ctx.exception.status_code, 400)

    @patch('ansible.module_utils.urls.Request.open')
    def test_error_message_from_plain_body(self, open_mock):
        open_mock.side_effect = HTTPError(
            'url', 500, 'Server Error', {}, io.BytesIO(b'kaboom'))
        with self.assertRaises(TVDinnerError) as ctx:
            self._client().request('GET', '/things')
        self.assertIn('kaboom', str(ctx.exception))

    @patch('ansible.module_utils.urls.Request.open')
    def test_basic_auth_drops_token_header(self, open_mock):
        open_mock.return_value = FakeResponse(200, b'[]')
        self._client().request('GET', '/tokens', basic_auth=('bob', 'pw'))
        kwargs = open_mock.call_args[1]
        self.assertNotIn('Authorization', kwargs['headers'])
        self.assertEqual(kwargs['url_username'], 'bob')
        self.assertEqual(kwargs['force_basic_auth'], True)

    @patch('ansible.module_utils.urls.Request.open')
    def test_post_encodes_body(self, open_mock):
        open_mock.return_value = FakeResponse(201, b'{"id": 9}')
        self._client().request('POST', '/things', data={'name': 'x'})
        self.assertEqual(json.loads(open_mock.call_args[1]['data']), {'name': 'x'})

    @patch('ansible.module_utils.urls.Request.open')
    def test_extra_headers_merge(self, open_mock):
        open_mock.return_value = FakeResponse(200, b'{}')
        self._client().request('GET', '/x', headers={'X-Custom': '1'})
        headers = open_mock.call_args[1]['headers']
        self.assertEqual(headers['X-Custom'], '1')
        self.assertEqual(headers['Authorization'], 'Bearer sekrit')

    @patch('ansible.module_utils.urls.Request.open')
    def test_list_params_repeat_key(self, open_mock):
        open_mock.return_value = FakeResponse(200, b'[]')
        self._client().request('GET', '/things', params={'labels': ['bug', 'toil']})
        url = open_mock.call_args[1]['url']
        self.assertIn('labels=bug&labels=toil', url)

    @patch('ansible.module_utils.urls.Request.open')
    def test_non_json_success_body_raises_structured_error(self, open_mock):
        open_mock.return_value = FakeResponse(200, b'<html>login</html>')
        with self.assertRaises(TVDinnerError) as ctx:
            self._client().request('GET', '/things')
        self.assertEqual(ctx.exception.status_code, 200)
        self.assertIn('Invalid JSON', str(ctx.exception))

    @patch('ansible.module_utils.urls.Request.open')
    def test_non_utf8_error_body_does_not_crash(self, open_mock):
        open_mock.side_effect = HTTPError(
            'url', 502, 'Bad Gateway', {}, io.BytesIO(b'\xff\xfe bad gateway'))
        with self.assertRaises(TVDinnerError) as ctx:
            self._client().request('GET', '/things')
        self.assertEqual(ctx.exception.status_code, 502)

    @patch('ansible.module_utils.urls.Request.open')
    def test_404_ok_not_found_ignores_unreadable_body(self, open_mock):
        open_mock.side_effect = HTTPError(
            'url', 404, 'Not Found', {}, io.BytesIO(b'\xff\xfe'))
        self.assertIsNone(self._client().request('GET', '/things/1', ok_not_found=True))

    @patch('ansible.module_utils.urls.Request.open')
    def test_error_message_hook_overridable(self, open_mock):
        class Client(RESTClient):
            def _error_message(self, parsed, body, error):
                return parsed['detail']

        open_mock.side_effect = HTTPError(
            'url', 400, 'Bad Request', {}, io.BytesIO(b'{"detail": "custom shape"}'))
        with self.assertRaises(TVDinnerError) as ctx:
            Client('https://x', 't').request('GET', '/things')
        self.assertIn('custom shape', str(ctx.exception))

    def test_auth_style_constants(self):
        self.assertEqual((AUTH_BEARER, AUTH_TOKEN), ('bearer', 'token'))


if __name__ == '__main__':
    unittest.main()
