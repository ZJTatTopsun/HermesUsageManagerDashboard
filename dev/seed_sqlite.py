from pathlib import Path
import importlib

from dashboard.plugin_api import api
from dev.fixtures import make_state

events = importlib.import_module(api.__package__ + '.events')
schemas = importlib.import_module(api.__package__ + '.schemas')
admin = importlib.import_module(api.__package__ + '.admin')
Principal = importlib.import_module(api.__package__ + '.security').Principal
Store = importlib.import_module(api.__package__ + '.db').Store


def seed(store):
    if store.source != 'mock':
        raise ValueError('Fixture seeding is restricted to Mock databases')
    data = make_state()
    principal = Principal('mock-seeder', 'admin')
    with store.transaction() as connection:
        if connection.execute("SELECT 1 FROM plugin_settings WHERE key='fixture_seeded'").fetchone():
            return
        for item in data['departments']:
            connection.execute('INSERT INTO departments(id,name) VALUES(?,?)', (item['id'], item['name']))
        for item in data['users']:
            connection.execute('INSERT INTO users(id,name,external_id,department_id,profile) VALUES(?,?,?,?,?)', (item['id'], item['name'], item['external_id'], item['department_id'], item['profile']))
            connection.execute('INSERT INTO department_membership VALUES(?,?,?,?,NULL)', ('seed-' + item['id'], item['id'], item['department_id'], '2026-09-01T00:00:00+00:00'))
        for item in data['prices']:
            body = {key: round(value, 6) if isinstance(value, float) else value for key, value in item.items() if key != 'id'}
            admin.save_price(connection, principal, schemas.PriceBody(**body), '')
        for item in data['requests']:
            total = item['input'] + item['cached'] if item['input'] is not None and item['cached'] is not None else None
            event = events.ModelEvent(instance_id='mock-instance', profile_id=item['profile'], source_event_id=item['id'], session_id=item['session_id'], api_request_id=item['id'], provider=item['provider'], model=item['model'], user_id=item['user_id'], department_id=item['department_id'], occurred_at=item['time'], status=item['status'], input_total_tokens=total, cached_input_tokens=item['cached'], output_tokens=item['output'], duration_ms=item['duration_ms'])
            events.ingest_model(connection, event)
        profiles = {item['id']: item['profile'] for item in data['users']}
        for item in data['tools']:
            events.ingest_tool(connection, events.ToolEvent(instance_id='mock-instance', profile_id=profiles[item['user_id']], source_event_id=item['id'], session_id=item['session_id'], user_id=item['user_id'], department_id=item['department_id'], tool_id=item['tool_id'], tool_name=item['name'], tool_type='mcp', mcp_server_id=item['server_id'], status='failed' if item['failed'] else 'success', duration_ms=item['duration_ms'], occurred_at=item['time']))
        connection.execute("INSERT INTO plugin_settings VALUES('fixture_seeded','true')")


def mock_runtime(path):
    store = Store(Path(path), 'mock')
    seed(store)

    def timeline(session_id):
        with store.read() as connection:
            tools = [dict(row) for row in connection.execute('SELECT * FROM tool_calls WHERE session_key=? ORDER BY occurred_at,event_key', (session_id,))]
        return [{'id': 'mock-user', 'kind': 'user', 'text': '请分析模拟商品近期趋势。', 'tools': []},
                {'id': 'mock-tools', 'kind': 'tools', 'text': '连续工具调用', 'tools': [{'id': tool['event_key'], 'name': tool['tool_name'], 'success': tool['status'] == 'success', 'args': '{"product_id":"MOCK-001"}', 'result': '模拟结果：虚构商品趋势摘要。'} for tool in tools]},
                {'id': 'mock-assistant', 'kind': 'assistant', 'text': '这是独立的模拟正文 Provider，未读取真实会话。', 'tools': []}]
    return api.Runtime(store, '2026-10-15', timeline)
