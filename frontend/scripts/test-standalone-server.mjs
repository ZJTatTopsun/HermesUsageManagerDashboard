import { spawn } from 'node:child_process';
import process from 'node:process';

await import('./build.mjs');
await import('./build-standalone.mjs');
const child = spawn(process.env.HUM_PYTHON || 'python', ['-m', 'uvicorn', 'dev.standalone_test:app', '--host', '127.0.0.1', '--port', '9120', '--no-access-log'], { cwd: '..', stdio: 'inherit' });
child.on('error', (error) => { console.error(error); process.exitCode = 1; });
child.on('exit', (code) => { process.exitCode = code ?? 1; });
process.on('SIGINT', () => child.kill());
process.on('SIGTERM', () => child.kill());
