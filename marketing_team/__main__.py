"""JSON reports on stdout; help is human-readable. No persistence or execution."""
import argparse
import json

from .discovery import discover_task
from .github import DiscoveryError
from .planner import plan_task


class _Arguments(argparse.ArgumentParser):
    def error(self, message):
        # argparse's message can contain the private task or a supplied credential.
        raise ValueError('INVALID_ARGUMENT')


def main(argv=None):
    parser = _Arguments(description='Rules-based marketing helper: offline planning or read-only GitHub discovery')
    commands = parser.add_subparsers(dest='command', required=True)
    plan = commands.add_parser('plan', help='offline adaptive method plan (no network)')
    plan.add_argument('--task', required=True, help='private local task text; never included in search queries')
    discover = commands.add_parser('discover', help='read-only GitHub search when needed; reuse bundled methods for small revisions')
    discover.add_argument('--task', required=True)
    discover.add_argument('--max-results', type=int, default=3, help='1..10 candidates, at most two inspected (default: 3)')
    discover.add_argument('--force-search', action='store_true', help='search fresh even for a narrow revision')
    try:
        args = parser.parse_args(argv)
        report = (plan_task(args.task) if args.command == 'plan' else
                  discover_task(args.task, max_results=args.max_results, force_search=args.force_search))
    except ValueError:
        print(json.dumps({'status': 'ERROR', 'error': {'code': 'INVALID_ARGUMENT'}}))
        return 2
    except DiscoveryError as error:
        print(json.dumps({'status': 'ERROR', 'error': {'code': error.code}}))
        return 1
    print(json.dumps(report, ensure_ascii=True, allow_nan=False))
    return 1 if report['discovery']['status'] == 'UNAVAILABLE' else 0


if __name__ == '__main__':
    raise SystemExit(main())
