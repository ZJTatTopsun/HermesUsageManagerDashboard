import { build } from 'esbuild';

await build({ entryPoints: ['mock/host.tsx'], bundle: true, format: 'iife', platform: 'browser',
  outfile: '.mock-dist/host.js', jsx: 'transform', target: 'es2020' });
