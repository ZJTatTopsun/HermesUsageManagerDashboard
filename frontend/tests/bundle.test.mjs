import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { runInNewContext } from 'node:vm';

const code = await readFile('../dashboard/dist/index.js', 'utf8');
const evaluate = (window) => runInNewContext(code, { window, navigator: { userAgent: '' }, document: { documentElement: { style: {} }, createElement: () => ({ style: {} }) } });

test('ordinary script registers exactly one component with the host React', () => {
  const registrations = [];
  const hostReact = { createElement() {} };
  evaluate({
    __HERMES_PLUGIN_SDK__: { React: hostReact, fetchJSON() {} },
    __HERMES_PLUGINS__: { register: (...args) => registrations.push(args) },
  });
  assert.equal(registrations.length, 1);
  assert.equal(registrations[0][0], 'hermes-usage-manager');
  assert.equal(typeof registrations[0][1], 'function');
});

test('missing or incompatible host fails explicitly', () => {
  for (const window of [{}, { __HERMES_PLUGIN_SDK__: { React: {} } }]) {
    assert.throws(() => evaluate(window), /SDK is unavailable or incompatible/);
  }
});

test('missing registry does not silently create a standalone app', () => {
  assert.throws(() => evaluate({
    __HERMES_PLUGIN_SDK__: { React: { createElement() {} }, fetchJSON() {} },
  }), /registry is unavailable/);
});
