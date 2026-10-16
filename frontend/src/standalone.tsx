import * as React from 'react';
import { createRoot } from 'react-dom/client';
import './theme.css';
import './standalone.css';

let csrf = '';
let expired = () => {};
window.__HERMES_PLUGIN_SDK__ = {
  React,
  fetchJSON: async (path, init) => {
    if (!path.startsWith('/api/plugins/hermes-usage-manager/')) throw new Error('接口路径不受支持');
    const headers = new Headers(init?.headers);
    if (!['GET', 'HEAD'].includes(init?.method?.toUpperCase() ?? 'GET')) headers.set('x-hum-csrf', csrf);
    const response = await fetch(path, { ...init, headers, credentials: 'same-origin' });
    if (response.status === 401) expired();
    const value = await response.json();
    if (!response.ok) throw new Error(`${response.status}: ${JSON.stringify(value)}`);
    return value;
  },
};

async function mount() {
  const { PluginApp } = await import('./App');

  function Standalone() {
    const [authenticated, setAuthenticated] = React.useState(false);
    const [checking, setChecking] = React.useState(true);
    const [password, setPassword] = React.useState('');
    const [pending, setPending] = React.useState(false);
    const [error, setError] = React.useState('');
    expired = () => { csrf = ''; setAuthenticated(false); setPassword(''); };

    React.useEffect(() => {
      const controller = new AbortController();
      fetch('/api/auth/session', { signal: controller.signal, credentials: 'same-origin' }).then(async (response) => {
        if (response.ok) { const value = await response.json(); csrf = value.csrf; setAuthenticated(true); }
        else if (response.status !== 401) setError('无法检查登录状态，请刷新重试');
      }).catch((reason) => { if (reason.name !== 'AbortError') setError('无法连接服务，请刷新重试'); })
        .finally(() => { if (!controller.signal.aborted) setChecking(false); });
      return () => controller.abort();
    }, []);

    async function login(event: React.FormEvent) {
      event.preventDefault();
      setPending(true); setError('');
      try {
        const response = await fetch('/api/auth/login', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ password }) });
        const value = await response.json();
        if (!response.ok) throw new Error(value.error?.message ?? '登录失败');
        csrf = value.csrf; setPassword(''); setAuthenticated(true);
      } catch (reason) { setError(reason instanceof Error ? reason.message : '登录失败'); }
      finally { setPending(false); }
    }

    async function logout() {
      setPending(true); setError('');
      try {
        const response = await fetch('/api/auth/logout', { method: 'POST', credentials: 'same-origin', headers: { 'x-hum-csrf': csrf } });
        if (!response.ok && response.status !== 401) throw new Error('退出失败，请重试');
        expired();
      } catch (reason) { setError(reason instanceof Error ? reason.message : '退出失败'); }
      finally { setPending(false); }
    }

    if (checking) return <main className="hum-login hum-root"><p role="status">正在检查登录状态…</p></main>;
    if (!authenticated) return <main className="hum-login hum-root"><form onSubmit={login}>
      <span className="hum-caption">Hermes Usage Manager</span><h1>用量管理</h1>
      <label htmlFor="hum-password">管理员密码</label>
      <input id="hum-password" type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} maxLength={256} required />
      {error && <p role="alert">{error}</p>}
      <button type="submit" disabled={pending}>{pending ? '正在登录…' : '登录'}</button>
    </form></main>;
    return <><header className="hum-standalone-bar"><span>Hermes Usage Manager</span><button type="button" disabled={pending} onClick={logout}>退出登录</button></header>
      {error && <p className="hum-standalone-error" role="alert">{error}</p>}<PluginApp /></>;
  }

  const container = document.getElementById('hum-standalone');
  if (!container) throw new Error('Standalone root missing');
  createRoot(container).render(<Standalone />);
}

void mount();
