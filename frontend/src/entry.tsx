import { PluginApp } from './App';
import './theme.css';

const registry = window.__HERMES_PLUGINS__;
if (!registry || typeof registry.register !== 'function') {
  throw new Error('Hermes Dashboard Plugin registry is unavailable');
}
registry.register('hermes-usage-manager', PluginApp);
