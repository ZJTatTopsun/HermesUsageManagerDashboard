import { spawn } from 'node:child_process';
import process from 'node:process';

await import('./build.mjs');
await import('./build-mock.mjs');
const child = spawn(process.env.HUM_PYTHON || 'python', ['-m', 'uvicorn', 'dev.sqlite_api:app',
  '--host', '127.0.0.1', '--port', '8765'], { cwd: '..', stdio: 'inherit' });
child.on('error', (error) => { console.error(error); process.exitCode = 1; });
child.on('exit', (code) => { process.exitCode = code ?? 1; });
process.on('SIGINT', () => child.kill());
process.on('SIGTERM', () => child.kill());
