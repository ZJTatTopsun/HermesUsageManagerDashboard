import { getSDK } from '../platform/hermes-sdk';

export interface Health {
  status: 'ok';
  plugin: 'hermes-usage-manager';
  version: '0.4.4';
  milestone: 'M3';
  data_source: 'mock' | 'live';
  capabilities: {
    storage: 'ready' | 'unavailable';
    business_api: boolean;
    collection: 'unavailable' | 'registered' | 'observed' | 'degraded';
    hermes_runtime: 'unverified';
  };
}

export async function getHealth(signal: AbortSignal): Promise<Health> {
  const payload = await getSDK().fetchJSON('/api/plugins/hermes-usage-manager/health', { signal });
  if (!payload || typeof payload !== 'object') throw new Error('Health 响应格式不兼容');
  const health = payload as Partial<Health>;
  if (health.status !== 'ok' || health.plugin !== 'hermes-usage-manager'
    || health.version !== '0.4.4' || health.milestone !== 'M3'
    || !['mock', 'live'].includes(health.data_source ?? '')
    || !['ready', 'unavailable'].includes(health.capabilities?.storage ?? '')
    || typeof health.capabilities?.business_api !== 'boolean'
    || !['unavailable', 'registered', 'observed', 'degraded'].includes(health.capabilities?.collection ?? '')
    || health.capabilities?.hermes_runtime !== 'unverified') {
    throw new Error('Health 响应格式不兼容');
  }
  return health as Health;
}
