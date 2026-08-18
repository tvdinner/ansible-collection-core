# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Joe Stump <joe@joestump.net>
# MIT License (see LICENSE)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import json

from ansible.module_utils.urls import Request
from ansible.module_utils.six.moves.urllib.error import HTTPError, URLError
from ansible.module_utils.six.moves.urllib.parse import urlencode

# Auth styles supported by RESTClient.
AUTH_TOKEN = 'token'      # Authorization: token <value>  (Gitea)
AUTH_BEARER = 'bearer'    # Authorization: Bearer <value> (most APIs)
AUTH_HEADER = 'header'    # custom header name/value pair (e.g. X-API-Key)
AUTH_NONE = 'none'        # no authentication


class TVDinnerError(Exception):
    """Structured API error carrying the HTTP status code and parsed body."""

    def __init__(self, message, status_code=None, response=None):
        super(TVDinnerError, self).__init__(message)
        self.status_code = status_code
        self.response = response


class TVDinnerNotFoundError(TVDinnerError):
    """The requested resource does not exist (HTTP 404)."""


class RESTClient(object):
    """Generic JSON REST client shared by every tvdinner.* collection.

    Consolidates the seven bespoke clients the joestump.* collections each
    shipped: base URL joining, query params, JSON encode/decode, timeout,
    TLS verification, error mapping, and check-mode-safe semantics (modules
    decide when to call; the client never mutates on its own).

    Subclasses add product-specific endpoint methods on top of C(request).
    Override C(_auth_headers) for unusual auth schemes.
    """

    def __init__(self, url, token=None, auth_style=AUTH_BEARER,
                 auth_header_name=None, validate_certs=True, timeout=30):
        self.base_url = url.rstrip('/')
        self.token = token
        self.auth_style = auth_style
        self.auth_header_name = auth_header_name
        self.validate_certs = validate_certs
        self.timeout = timeout
        self._request = Request(use_netrc=False)

    def _auth_headers(self):
        """Return auth headers for the configured auth style."""
        if self.auth_style == AUTH_NONE or not self.token:
            return {}
        if self.auth_style == AUTH_TOKEN:
            return {'Authorization': 'token {0}'.format(self.token)}
        if self.auth_style == AUTH_HEADER:
            if not self.auth_header_name:
                raise TVDinnerError('auth_header_name is required for header auth')
            return {self.auth_header_name: self.token}
        return {'Authorization': 'Bearer {0}'.format(self.token)}

    def request(self, method, endpoint, data=None, params=None,
                basic_auth=None, headers=None, ok_not_found=False):
        """Perform an HTTP request and return the parsed JSON body.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, PATCH).
            endpoint: API path, appended to the base URL.
            data: request body, JSON-encoded when not None.
            params: dict of query-string parameters.
            basic_auth: optional C((user, password)) tuple; switches the
                request to HTTP Basic auth and drops the token header.
            headers: extra headers merged over the default set.
            ok_not_found: when True, a 404 returns None instead of raising.

        Returns:
            Parsed JSON response, or None for 204/empty bodies and 404s
            with C(ok_not_found).

        Raises:
            TVDinnerNotFoundError: on 404 (unless C(ok_not_found)).
            TVDinnerError: on any other API or connection error.
        """
        url = '{0}{1}'.format(self.base_url, endpoint)
        if params:
            params = dict((k, v) for k, v in params.items() if v is not None)
            if params:
                url = '{0}?{1}'.format(url, urlencode(params))

        all_headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        if not basic_auth:
            all_headers.update(self._auth_headers())
        if headers:
            all_headers.update(headers)

        open_kwargs = dict(
            method=method,
            url=url,
            data=json.dumps(data).encode('utf-8') if data is not None else None,
            headers=all_headers,
            validate_certs=self.validate_certs,
            timeout=self.timeout,
        )
        if basic_auth:
            open_kwargs['url_username'] = basic_auth[0]
            open_kwargs['url_password'] = basic_auth[1]
            open_kwargs['force_basic_auth'] = True

        try:
            response = self._request.open(**open_kwargs)
        except HTTPError as e:
            body = e.read()
            parsed = None
            try:
                parsed = json.loads(body) if body else None
            except (ValueError, TypeError):
                parsed = None
            message = None
            if isinstance(parsed, dict):
                message = parsed.get('message') or parsed.get('error') or parsed.get('errors')
            if not message:
                message = body.decode('utf-8') if body else str(e)
            if e.code == 404 and ok_not_found:
                return None
            error_class = TVDinnerNotFoundError if e.code == 404 else TVDinnerError
            raise error_class(
                'API error ({0}): {1}'.format(e.code, message),
                status_code=e.code,
                response=parsed,
            )
        except URLError as e:
            raise TVDinnerError('Connection error: {0}'.format(getattr(e, 'reason', e)))
        except TVDinnerError:
            raise
        except Exception as e:
            raise TVDinnerError('Unexpected error: {0}'.format(str(e)))

        if response.status == 204:
            return None
        content = response.read()
        if content:
            return json.loads(content)
        return None
