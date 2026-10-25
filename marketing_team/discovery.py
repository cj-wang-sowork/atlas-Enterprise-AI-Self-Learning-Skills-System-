"""One fresh, read-only discovery attempt per task; nothing is installed."""
import math
from datetime import datetime, timezone

from .github import DiscoveryError, GitHubClient
from .planner import DOMAINS, _matches, plan_task
from .metadata import validate_repository
from .inspection import inspect_candidate

KNOWN_LICENSES = {'MIT', 'Apache-2.0', 'BSD-2-Clause', 'BSD-3-Clause', 'ISC',
                  'MPL-2.0', 'GPL-2.0', 'GPL-3.0', 'GPL-2.0-only', 'GPL-3.0-only',
                  'GPL-2.0-or-later', 'GPL-3.0-or-later', 'AGPL-3.0', 'AGPL-3.0-only',
                  'AGPL-3.0-or-later', 'LGPL-3.0-only', 'LGPL-2.1-only', 'Unlicense', 'CC0-1.0',
                  'CC-BY-4.0', 'CC-BY-SA-4.0'}


def rank_candidate(item, domains) -> dict:
    """Bound popularity below task relevance; expose every mismatch separately."""
    text = ' '.join([item['full_name'], item.get('description') or '',
                     ' '.join(item.get('topics', []))]).lower()
    terms = sorted({term for domain in domains for term in DOMAINS[domain]['terms']
                    if _matches(text, term)})
    relevance = min(55, len(terms) * 14)
    popularity = min(15, math.log10(item['stargazers_count'] + 1) * 3)
    pushed = datetime.strptime(item['pushed_at'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
    days = max(0, (datetime.now(timezone.utc) - pushed).days)
    recency = 15 if days <= 90 else (8 if days <= 365 else 0)
    mismatches = []
    if not terms:
        mismatches.append('no_domain_relevance')
    if days > 365:
        mismatches.append('stale_push_over_365_days')
    for key in ('archived', 'disabled', 'fork'):
        if item[key]:
            mismatches.append(key)
    license_id = (item.get('license') or {}).get('spdx_id')
    known_license = license_id in KNOWN_LICENSES
    if not known_license:
        mismatches.append('unknown_or_missing_license')
    for domain in domains:
        if not any(_matches(text, term) for term in DOMAINS[domain]['terms']):
            mismatches.append('domain_not_supported:' + domain)
    score = relevance + popularity + recency + (10 if not item['archived'] and not item['disabled'] else -25)
    score += 5 if known_license else -5
    score -= 10 if item['fork'] else 0
    return dict(item, score=round(max(0, min(100, score)), 2),
                reasons=['domain terms: ' + ', '.join(terms),
                         'stars signal (bounded): ' + str(item['stargazers_count']),
                         'days since push: ' + str(days), 'SPDX: ' + (license_id or 'unknown')],
                mismatches=mismatches, relevant=bool(terms), state='DISCOVERED', activated=False,
                trust='UNTRUSTED_DATA',
                review_status='REVIEW_REQUIRED', source_content_reviewed=False,
                license_at_commit_reviewed=False, environment_review_status='NOT_REVIEWED',
                required_followup=['Pin a commit, then review its license text and environment compatibility read-only.'],
                limitations=['Stars are not proof of suitability, quality, or business outcomes.',
                             'Metadata is an untrusted, current API observation; no code has been executed.'])


def discover_task(task, max_results=3, client=None):
    if type(max_results) is not int or not 1 <= max_results <= 10:
        raise ValueError('max_results must be an integer between 1 and 10')
    report = plan_task(task)
    client = client if client is not None else GitHubClient()
    queries = [DOMAINS[domain]['query'] for domain in report['domains'][:3]] or ['marketing workflow']
    candidates = []
    errors = []
    truncated = len(report['domains']) > 3
    for query in queries:
        try:
            result = client.get_json('/search/repositories', {'q': query, 'sort': 'stars',
                                                             'order': 'desc', 'per_page': 10, 'page': 1})
            if (not isinstance(result.get('items'), list) or type(result.get('total_count')) is not int or
                    not 0 <= result['total_count'] <= 10 ** 12 or
                    type(result.get('incomplete_results')) is not bool):
                raise DiscoveryError('INVALID_SEARCH_RESPONSE')
            truncated |= result['incomplete_results'] or result['total_count'] > len(result['items']) or len(result['items']) > 10
            for item in result['items'][:10]:
                try:
                    candidates.append(validate_repository(item))
                except DiscoveryError as error:
                    errors.append({'stage': 'metadata', 'code': error.code})
        except DiscoveryError as error:
            errors.append({'stage': 'search', 'code': error.code})
            break
    candidates = list({item['full_name'].lower(): item for item in reversed(candidates)}.values())
    candidates = sorted([rank_candidate(item, report['domains']) for item in candidates],
                        key=lambda item: (not item['relevant'], -item['score'], item['full_name']))
    truncated |= len(candidates) > max_results
    candidates = candidates[:max_results]
    selected = [item for item in candidates if item['relevant']][:2]
    truncated |= sum(bool(item['relevant']) for item in candidates) > 2
    for item in selected:
        inspect_candidate(item, client, report['domains'])
        if item['state'] == 'INSPECT_FAILED':
            errors.append({'stage': 'inspection', 'repository': item['full_name'], 'code': item['inspection_error']})
        truncated |= item.get('tree_truncated', False) or any(doc['truncated'] for doc in item['documents'])
    status = ('PARTIAL' if errors else 'DISCOVERED') if candidates else ('UNAVAILABLE' if errors else 'NO_CANDIDATES')
    report['discovery'] = {'status': status,
                           'limits': {'queries': 3, 'pages_per_query': 1, 'items_per_page': 10,
                                      'inspected_candidates': 2, 'documents_per_candidate': 2,
                                      'http_requests': 15, 'response_bytes': 524288, 'document_bytes': 65536,
                                      'excerpt_characters': 4000, 'tree_entries': 5000},
                           'availability': 'LIVE_SEARCH_UNAVAILABLE' if status == 'UNAVAILABLE' else ('LIVE_SEARCH_PARTIAL' if errors else 'LIVE_SEARCH_COMPLETED'),
                           'offline_fallback': {'status': 'AVAILABLE' if report['methods'] else 'NEEDS_CLARIFICATION',
                                                'method_ids': list(report['methods']),
                                                'limitation': 'Offline method plan only, not a researched business deliverable or installed capability.'},
                           'counts': {state: sum(item['state'] == state for item in candidates)
                                      for state in ('DISCOVERED', 'USABLE_AS_REFERENCE', 'REVIEW_REQUIRED', 'INSPECT_FAILED')},
                           'errors': errors, 'truncated': bool(truncated),
                           'attempted': True, 'queries': queries, 'candidates': candidates[:max_results],
                           'requests': client.requests}
    return report
