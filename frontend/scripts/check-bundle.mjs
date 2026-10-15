import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { parse } from 'acorn';

const code = await readFile('../dashboard/dist/index.js', 'utf8');
const metadata = JSON.parse(await readFile('../build/plugin-metafile.json', 'utf8'));
const program = parse(code, { ecmaVersion: 'latest', sourceType: 'script' });
const statements = program.body.filter((statement) => statement.directive !== 'use strict');
assert.equal(statements.length, 1, 'Expected one IIFE statement plus optional strict directive');
assert.equal(statements[0].expression.type, 'CallExpression');
assert.equal(statements[0].expression.callee.type, 'ArrowFunctionExpression');
const allowedPackages = new Set(['echarts', 'zrender', 'tslib', 'zod']);
for (const path of Object.keys(metadata.inputs)) {
  const parts = path.replaceAll('\\', '/').split('/node_modules/');
  if (parts.length > 1) assert(allowedPackages.has(parts.at(-1).split('/')[0]), `Unexpected runtime dependency: ${path}`);
}
assert(Object.entries(metadata.outputs).filter(([path]) => path.endsWith('.js')).every(([, output]) => output.imports.length === 0), 'Unresolved JavaScript imports');
assert(!/react-dom|react\.production|react\.development|jsx-runtime|createRoot|__SECRET_INTERNALS/.test(code));
assert(code.includes('__HERMES_PLUGIN_SDK__'));
console.log('PASS: single IIFE, no imports, no bundled React/ReactDOM; metafile checked');
