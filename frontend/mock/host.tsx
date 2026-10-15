import * as React from 'react';
import { createRoot } from 'react-dom/client';

const container = document.getElementById('mock-root');
if (!container) throw new Error('Mock root missing');
const root = createRoot(container);
let Page: React.ComponentType | undefined;
let mounted = true;
let registrations = 0;
window.__HERMES_PLUGIN_SDK__ = {
  React,
  fetchJSON: async (path, init) => {
    const params = new URLSearchParams(window.location.search);
    const headers = new Headers(init?.headers);
    headers.set('x-hum-mock-role', params.get('role') ?? 'admin');
    headers.set('x-hum-mock-scenario', params.get('scenario') ?? 'normal');
    const response = await fetch(path, { ...init, headers });
    if (!response.ok) { const error = await response.json().catch(() => ({})); throw new Error(`HTTP ${response.status} · ${error.error?.message ?? (typeof error.detail === 'string' ? error.detail : '请求失败')}`); }
    return response.json();
  },
};
window.__HERMES_PLUGINS__ = {
  register(name, component) {
    if (name !== 'hermes-usage-manager' || ++registrations !== 1) throw new Error('Invalid registration');
    Page = component;
    container.dataset.registrations = String(registrations);
    root.render(<Page />);
  },
};
const toggle = document.getElementById('toggle');
toggle?.addEventListener('click', () => {
  mounted = !mounted;
  root.render(mounted && Page ? <Page /> : null);
  toggle.textContent = mounted ? '卸载插件' : '挂载插件';
});
const script = document.createElement('script');
script.src = '/dashboard-plugins/hermes-usage-manager/dist/index.js';
document.head.appendChild(script);
for (const name of ['scenario', 'role']) {
  const element = document.getElementById(`mock-${name}`) as HTMLSelectElement;
  element.value = new URLSearchParams(window.location.search).get(name) ?? (name === 'role' ? 'admin' : 'normal');
  element.addEventListener('change', () => { const url = new URL(window.location.href); url.searchParams.set(name, element.value); window.location.href = url.toString(); });
}
