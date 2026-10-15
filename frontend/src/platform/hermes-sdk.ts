import type * as ReactTypes from 'react';

export interface HermesSDK {
  React: typeof ReactTypes;
  fetchJSON: (path: string, init?: RequestInit) => Promise<unknown>;
}

declare global {
  interface Window {
    __HERMES_PLUGIN_SDK__?: HermesSDK;
    __HERMES_PLUGINS__?: {
      register: (name: string, component: ReactTypes.ComponentType) => void;
    };
  }
}

export function getSDK(): HermesSDK {
  const sdk = window.__HERMES_PLUGIN_SDK__;
  if (!sdk?.React?.createElement || typeof sdk.fetchJSON !== 'function') {
    throw new Error('Hermes Dashboard Plugin SDK is unavailable or incompatible');
  }
  return sdk;
}
