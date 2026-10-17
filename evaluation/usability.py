"""Local observer-operated usability evidence, not a human-identity verifier."""
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import re
import sqlite3
import stat
import uuid
from statistics import median
from security_checker import SecurityChecker

STEPS = ('download_kit', 'create_project', 'add_instructions', 'attach_brief', 'complete_first_task', 'save_result')


def _label(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,100}', value):
        raise ValueError('use a non-identifying ASCII label')
    if not SecurityChecker().scan_content(value)[0]:
        raise ValueError('study labels must not contain sensitive data')
    return value


def _evidence_digest(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        metadata = os.fstat(fd)
        if not stat.S_ISREG(metadata.st_mode) or not 0 < metadata.st_size <= 1024 * 1024:
            raise ValueError('provide a nonempty bounded plain-text output artifact')
        with os.fdopen(fd, 'rb', closefd=False) as stream:
            content = stream.read(1024 * 1024 + 1)
        if len(content) > 1024 * 1024:
            raise ValueError('output evidence is too large')
        text = content.decode('utf-8')
        if not text.strip() or not SecurityChecker().scan_content(text)[0]:
            raise ValueError('output evidence must be sanitized nonempty text')
        return hashlib.sha256(content).hexdigest()
    finally:
        os.close(fd)


class StudyLog:
    def __init__(self, path, *, clock=None):
        self.path = Path(path)
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
        parent = self.path.parent.lstat()
        if self.path.parent.is_symlink() or parent.st_mode & 0o077:
            raise PermissionError('study storage requires a private owner directory')
        fd = os.open(self.path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
        try:
            mode = os.fstat(fd)
            if not stat.S_ISREG(mode.st_mode) or mode.st_mode & 0o077 or mode.st_uid != os.getuid():
                raise PermissionError('study log must be an owner-only regular file')
        finally:
            os.close(fd)
        with self._transaction() as db:
            db.execute('CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, participant TEXT UNIQUE, kind TEXT, background TEXT, consent INTEGER, runtime TEXT, revision TEXT, started TEXT, observer TEXT, attested INTEGER, ended TEXT, outcome TEXT, evidence_digest TEXT)')
            db.execute('CREATE TABLE IF NOT EXISTS steps (id INTEGER PRIMARY KEY, session TEXT, name TEXT, status TEXT, at TEXT)')

    @contextmanager
    def _transaction(self):
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                connection.execute('BEGIN IMMEDIATE')
                yield connection
        finally:
            connection.close()

    def _stamp(self):
        value = self.clock()
        if not isinstance(value, datetime) or value.tzinfo is None:
            raise ValueError('timezone-aware observer clock is required')
        return value.astimezone(timezone.utc).isoformat()

    def start(self, participant, *, kind, background, consent, runtime, starter_revision, observer=None, attested=False):
        for value in (participant, runtime, starter_revision):
            _label(value)
        if kind not in ('human', 'agent_qa') or background not in ('non_engineer', 'engineer', 'unknown') or type(consent) is not bool:
            raise ValueError('invalid participant declarations')
        if type(attested) is not bool:
            raise ValueError('attestation must be an explicit boolean')
        if kind == 'human' and (not consent or not attested or observer is None):
            raise PermissionError('a human study requires consent and observer attestation')
        if observer is not None:
            _label(observer)
        session = uuid.uuid4().hex
        with self._transaction() as db:
            first = db.execute('SELECT runtime,revision FROM sessions LIMIT 1').fetchone()
            if first is not None and (first['runtime'], first['revision']) != (runtime, starter_revision):
                raise ValueError('use separate logs for different runtimes or starter revisions')
            if db.execute('SELECT 1 FROM sessions WHERE participant=?', (participant,)).fetchone():
                raise ValueError('one first attempt per participant; retries need a separate labelled study')
            db.execute('INSERT INTO sessions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',
                       (session, participant, kind, background, int(consent), runtime, starter_revision, self._stamp(), observer, int(attested), None, None, None))
        return session

    @staticmethod
    def _active(db, session):
        _label(session)
        row = db.execute('SELECT * FROM sessions WHERE id=?', (session,)).fetchone()
        if row is None:
            raise ValueError('unknown study session')
        if row['ended'] is not None:
            raise ValueError('finished sessions cannot be overwritten')
        return row

    @staticmethod
    def _check_time(db, row, stamp):
        last = db.execute('SELECT at FROM steps WHERE session=? ORDER BY id DESC LIMIT 1', (row['id'],)).fetchone()
        previous = last['at'] if last else row['started']
        if datetime.fromisoformat(stamp) < datetime.fromisoformat(previous):
            raise ValueError('observer clock moved backwards')

    def step(self, session, name, *, status):
        if name not in STEPS or status not in ('completed', 'blocked'):
            raise ValueError('unknown study step or status')
        stamp = self._stamp()
        with self._transaction() as db:
            row = self._active(db, session)
            self._check_time(db, row, stamp)
            db.execute('INSERT INTO steps(session,name,status,at) VALUES (?,?,?,?)', (session, name, status, stamp))

    def finish(self, session, *, outcome, evidence=None):
        if outcome not in ('success', 'blocked', 'abandoned'):
            raise ValueError('unknown study outcome')
        stamp = self._stamp()
        with self._transaction() as db:
            row = self._active(db, session)
            self._check_time(db, row, stamp)
            artifact = None
            if outcome == 'success':
                events = db.execute('SELECT name,status FROM steps WHERE session=? ORDER BY id', (session,))
                states = {event['name']: event['status'] for event in events}
                if any(states.get(name) != 'completed' for name in STEPS) or evidence is None:
                    raise ValueError('success requires all steps and sanitized output evidence')
                artifact = _evidence_digest(evidence)
            db.execute('UPDATE sessions SET ended=?,outcome=?,evidence_digest=? WHERE id=?', (stamp, outcome, artifact, session))

    def report(self):
        with self._transaction() as db:
            rows = list(db.execute('SELECT * FROM sessions'))
            events = list(db.execute("SELECT DISTINCT session,name FROM steps WHERE status='blocked'"))
        eligible = [r for r in rows if r['kind'] == 'human' and r['background'] == 'non_engineer'
                    and r['consent'] == 1 and r['attested'] == 1]
        successes = [r for r in eligible if r['outcome'] == 'success']
        durations = [(datetime.fromisoformat(r['ended']) - datetime.fromisoformat(r['started'])).total_seconds() for r in successes]
        within = sum(seconds <= 600 for seconds in durations)
        ids = {r['id'] for r in eligible}
        blocked = {}
        for event in events:
            if event['session'] in ids:
                blocked[event['name']] = blocked.get(event['name'], 0) + 1
        return {'total_sessions': len(rows), 'eligible_humans_started': len(eligible),
                'completed_successfully': len(successes), 'completed_within_600_seconds': within,
                'success_rate': len(successes) / len(eligible) if eligible else None,
                'ten_minute_success_rate': within / len(eligible) if eligible else None,
                'median_success_seconds': median(durations) if durations else None,
                'unfinished_or_failed': len(eligible) - len(successes), 'blocked_steps': blocked,
                'note': 'Observer declarations are not cryptographic human identity proof; agent QA is excluded.'}


def main(argv=None):
    import argparse
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', required=True, help='private observer-controlled SQLite log')
    commands = parser.add_subparsers(dest='command', required=True)
    start = commands.add_parser('start')
    start.add_argument('participant', help='anonymous participant label, never an email/name')
    start.add_argument('--kind', required=True, choices=('human', 'agent_qa'))
    start.add_argument('--background', required=True, choices=('non_engineer', 'engineer', 'unknown'))
    start.add_argument('--runtime', required=True)
    start.add_argument('--starter-revision', required=True)
    start.add_argument('--consent', action='store_true')
    start.add_argument('--observer')
    start.add_argument('--attested', action='store_true')
    step = commands.add_parser('step')
    step.add_argument('session')
    step.add_argument('name', choices=STEPS)
    step.add_argument('--status', required=True, choices=('completed', 'blocked'))
    finish = commands.add_parser('finish')
    finish.add_argument('session')
    finish.add_argument('--outcome', required=True, choices=('success', 'blocked', 'abandoned'))
    finish.add_argument('--evidence')
    commands.add_parser('report')
    args = parser.parse_args(argv)
    try:
        log = StudyLog(args.db)
        if args.command == 'start':
            result = {'session': log.start(args.participant, kind=args.kind, background=args.background,
                consent=args.consent, runtime=args.runtime, starter_revision=args.starter_revision,
                observer=args.observer, attested=args.attested), 'kind': args.kind}
        elif args.command == 'step':
            log.step(args.session, args.name, status=args.status)
            result = {'saved': True, 'step': args.name, 'status': args.status}
        elif args.command == 'finish':
            log.finish(args.session, outcome=args.outcome, evidence=args.evidence)
            result = {'saved': True, 'outcome': args.outcome}
        else:
            result = log.report()
    except (ValueError, PermissionError, OSError, sqlite3.Error):
        parser.exit(2, 'Study operation rejected; check private storage, declarations, steps, time, and sanitized evidence.\n')
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
