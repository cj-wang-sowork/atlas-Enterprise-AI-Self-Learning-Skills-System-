"""GitHub REST adapter; injectable transport keeps all tests offline."""
from dataclasses import dataclass
from http.client import HTTPException
import json
import os
import re
import time
import urllib.error
import urllib.request
from urllib.parse import quote, unquote, urlencode


@dataclass
class Response:
    status: int
    headers: dict
    body: bytes


class DiscoveryError(Exception):
    """Static messages only: never expose response bodies, URLs or credentials."""
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def valid_path(path):
    if not isinstance(path, str) or len(path) > 6500:
        return False
    contents = re.fullmatch(r'/repos/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/contents/(.+)', path)
    if contents:
        # Decode each component exactly once; only canonical UTF-8 quoting is accepted.
        try:
            parts = [unquote(part, encoding='utf-8', errors='strict')
                     for part in contents.group(1).split('/')]
        except UnicodeError:
            return False
        decoded = '/'.join(parts)
        return (0 < len(decoded) <= 500 and decoded.isprintable() and
                not any(char in decoded for char in '\\%?#:@') and
                all(part not in ('', '.', '..') and '/' not in part for part in parts) and
                quote(decoded, safe='/') == contents.group(1) and
                all(part not in ('', '.', '..') for part in path.split('/')[1:]))
    return (len(path) <= 400 and re.fullmatch(r'/[A-Za-z0-9_./-]+', path) is not None and
            not any(part in ('', '.', '..') for part in path.split('/')[1:]))


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _http_get(url, headers, timeout, max_bytes):
    # Do not use environment proxy credentials or provider-controlled redirect URLs.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect())
    request = urllib.request.Request(url, headers=headers, method='GET')
    try:
        with opener.open(request, timeout=timeout) as result:
            return Response(result.status, dict(result.headers), result.read(max_bytes + 1))
    except urllib.error.HTTPError as error:
        error.close()
        return Response(error.code, dict(error.headers), b'')


class GitHubClient:
    def __init__(self, transport=None):
        self.transport = transport if transport is not None else _http_get
        self.requests = 0
        self.deadline = time.monotonic() + 45

    def get_json(self, path, params=None):
        if self.requests >= 15:
            raise DiscoveryError('REQUEST_BUDGET_EXHAUSTED')
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise DiscoveryError('DEADLINE_EXCEEDED')
        if not valid_path(path):
            raise DiscoveryError('INVALID_TARGET')
        url = 'https://api.github.com' + path
        if params:
            url += '?' + urlencode(params)
        headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'atlas-marketing-team'}
        token = os.environ.get('GITHUB_TOKEN')
        if token:
            headers['Authorization'] = 'Bearer ' + token
        self.requests += 1
        try:
            response = self.transport(url, headers, min(5, remaining), 524288)
        except (OSError, urllib.error.URLError, HTTPException, ValueError):
            raise DiscoveryError('NETWORK_UNAVAILABLE') from None
        if len(response.body) > 524288:
            raise DiscoveryError('RESPONSE_TOO_LARGE')
        if 300 <= response.status < 400:
            raise DiscoveryError('REDIRECT_REJECTED')
        if response.status == 429 or (response.status == 403 and
                any(k.lower() == 'x-ratelimit-remaining' and v == '0'
                    for k, v in response.headers.items())):
            raise DiscoveryError('RATE_LIMITED')
        if not 200 <= response.status < 300:
            raise DiscoveryError('HTTP_UNAVAILABLE')
        try:
            value = json.loads(response.body.decode('utf-8'))
        except (ValueError, UnicodeError, RecursionError):
            raise DiscoveryError('INVALID_JSON') from None
        if not isinstance(value, dict):
            raise DiscoveryError('INVALID_RESPONSE')
        return value
