import { mkdtemp } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import process from 'node:process';

const directory = await mkdtemp(join(tmpdir(), 'hum-m2-browser-'));
process.env.HUM_MOCK_DB_PATH = join(directory, 'mock.sqlite3');
process.env.HUM_MOCK_TESTING = '1';
await import('./dev.mjs');
