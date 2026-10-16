"""Exercise the target-compatible native callbacks in a Mock-only DB."""

import argparse
import importlib
import importlib.util
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dashboard.plugin_api import api


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', type=Path)
    args = parser.parse_args()
    collector = importlib.import_module(api.__package__ + '.collector')
    hooks = importlib.import_module(api.__package__ + '.adapters.hooks')
    with tempfile.TemporaryDirectory(prefix='hum-hook-replay-') as temporary:
        path = args.db or Path(temporary) / 'mock.sqlite3'
        dispatcher = collector.Dispatcher(context_factory=lambda: hooks.HookContext('replay-only', 'p1', str(path)), enabled=True, classifier=lambda name: ('mcp', 'catalog'), source='mock')
        previous = collector.dispatcher
        collector.dispatcher = dispatcher
        registered = {}
        class Context:
            def register_hook(self, name, callback):
                registered[name] = callback
        try:
            spec = importlib.util.spec_from_file_location('hum_hook_replay_entry', ROOT / '__init__.py')
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            module.register(Context())
            base = {'session_id': 'replay-session', 'turn_id': 't1', 'platform': 'feishu', 'provider': 'fixture', 'model': 'fixture-model', 'api_request_id': 'api-1', 'started_at': 1791993600, 'ended_at': 1791993601, 'api_call_count': 1, 'usage': {'input_tokens': 70, 'cache_read_tokens': 30, 'cache_write_tokens': 0, 'prompt_tokens': 100, 'output_tokens': 20}}
            for _ in range(3):
                registered['pre_llm_call'](**base, sender_id='fixture-user', user_message='NOT_RETAINED')
                registered['post_api_request'](**base)
                registered['api_request_error'](**(base | {'api_request_id': 'failed-1', 'status_code': 429}))
                registered['post_tool_call'](**base, tool_call_id='tool-1', tool_name='catalog-search', status='ok', duration_ms=20, args={'sensitive': 'NOT_RETAINED'}, result='NOT_RETAINED')
                registered['on_session_end'](**base)
            dispatcher.close()
            worker = dispatcher.collectors[str(path)]
            if worker.thread and worker.thread.is_alive():
                raise RuntimeError('Replay did not flush within shutdown budget')
            with worker.store.read() as connection:
                requests = connection.execute('SELECT count(*) FROM llm_requests').fetchone()[0]
                tools = connection.execute('SELECT count(*) FROM tool_calls').fetchone()[0]
                assert requests == 2 and tools == 1
                assert not connection.execute("SELECT 1 FROM collection_queue WHERE payload_json LIKE '%NOT_RETAINED%'").fetchone()
                print(f'source=mock; registered_hooks={len(registered)}; repetitions=3; model_requests={requests}; mcp_calls={tools}; no_raw_payload=true')
        finally:
            dispatcher.close()
            collector.dispatcher = previous


if __name__ == '__main__':
    main()
