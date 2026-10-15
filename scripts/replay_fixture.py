"""Replay a deterministic normalized fixture; never connect to Hermes."""

import argparse
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dev.seed_sqlite import Store, events


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', type=Path, help='Absolute Mock-only database outside plugin source')
    parser.add_argument('--repetitions', type=int, default=3, choices=range(1, 101))
    arguments = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='hum-replay-') as directory:
        path = arguments.db or Path(directory) / 'mock.sqlite3'
        store = Store(path, 'mock')
        event = events.ModelEvent(instance_id='replay-demo', profile_id='p1', source_event_id='request-1:attempt-0:success', api_request_id='request-1', session_id='session-1', provider='Fixture', model='demo', occurred_at='2026-10-15T00:00:00+08:00', input_total_tokens=100, cached_input_tokens=30, output_tokens=20)
        inserted = 0
        for _ in range(arguments.repetitions):
            with store.transaction() as connection:
                inserted += events.ingest_model(connection, event)
        with store.read() as connection:
            row = connection.execute("SELECT count(*) AS count,max(total_tokens) AS tokens FROM llm_requests WHERE instance_id='replay-demo'").fetchone()
            assert row['count'] == 1 and row['tokens'] == 120
            print(f'repetitions={arguments.repetitions}; new_rows={inserted}; persisted_rows={row["count"]}; total_tokens={row["tokens"]}; source=mock')


if __name__ == '__main__':
    main()
