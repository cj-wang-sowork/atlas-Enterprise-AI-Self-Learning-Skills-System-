"""Fail-closed schema validation for untrusted API metadata."""
from datetime import datetime
import re

from .github import DiscoveryError

REPO = re.compile(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?/[A-Za-z0-9][A-Za-z0-9_.-]{0,99}')


def validate_repository(item):
    fail = lambda: DiscoveryError('INVALID_REPOSITORY')
    if not isinstance(item, dict):
        raise fail()
    name = item.get('full_name')
    if not isinstance(name, str) or REPO.fullmatch(name) is None:
        raise fail()
    if item.get('html_url') != 'https://github.com/' + name:
        raise fail()
    for field in ('stargazers_count', 'forks_count', 'open_issues_count'):
        value = item.get(field)
        if type(value) is not int or not 0 <= value <= 10 ** 12:
            raise fail()
    for field in ('archived', 'disabled', 'fork'):
        if type(item.get(field)) is not bool:
            raise fail()
    for field in ('pushed_at', 'updated_at'):
        value = item.get(field)
        if not isinstance(value, str) or re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z', value) is None:
            raise fail()
        try:
            datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ')
        except ValueError:
            raise fail() from None
    description = item.get('description')
    if description is not None and (not isinstance(description, str) or len(description) > 10000):
        raise fail()
    topics = item.get('topics', [])
    if not isinstance(topics, list) or len(topics) > 100 or any(
            not isinstance(topic, str) or len(topic) > 100 for topic in topics):
        raise fail()
    license_data = item.get('license')
    if license_data is not None and (not isinstance(license_data, dict) or (
            license_data.get('spdx_id') is not None and (
                not isinstance(license_data['spdx_id'], str) or
                re.fullmatch(r'[A-Za-z0-9.+-]{1,100}', license_data['spdx_id']) is None))):
        raise fail()
    # Never copy provider URLs, download links, credentials or arbitrary extra fields.
    fields = ('full_name', 'html_url', 'stargazers_count', 'forks_count', 'open_issues_count',
              'archived', 'disabled', 'fork', 'pushed_at', 'updated_at')
    result = {field: item[field] for field in fields}
    result.update(description=(description or '')[:500], topics=topics,
                  license={'spdx_id': license_data.get('spdx_id')} if license_data else None)
    return result
