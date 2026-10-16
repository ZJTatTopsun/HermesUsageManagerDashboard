import { build } from 'esbuild';
import { createHash } from 'node:crypto';
import { mkdir, readFile, readdir, writeFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const result = await build({ entryPoints: ['src/standalone.tsx'], bundle: true, format: 'iife', platform: 'browser', target: 'es2020', jsx: 'transform', jsxFactory: 'React.createElement', jsxFragment: 'React.Fragment', outfile: '../standalone/dist/app.js', metafile: true, legalComments: 'external', minify: true, define: { 'process.env.NODE_ENV': '"production"' }, loader: { '.ttf': 'file' }, assetNames: 'assets/[name]-[hash]' });
await writeFile('../standalone/dist/index.html', '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>用量管理 · Hermes Usage Manager</title><link rel="stylesheet" href="/standalone-assets/app.css"></head><body><div id="hum-standalone"></div><script src="/standalone-assets/app.js" defer></script></body></html>\n');
const notices = [await readFile('../dashboard/dist/THIRD_PARTY_NOTICES.txt', 'utf8')];
for (const name of ['react', 'react-dom', 'scheduler']) {
  let directory = dirname(require.resolve(name, { paths: [dirname(require.resolve('react-dom/package.json'))] }));
  while (true) {
    try { const record = JSON.parse(await readFile(join(directory, 'package.json'), 'utf8')); if (record.name === name) { notices.push(`${name}@${record.version}\n\n${await readFile(join(directory, 'LICENSE'), 'utf8')}`); break; } }
    catch (error) { if (error.code !== 'ENOENT') throw error; }
    const parent = dirname(directory);
    if (parent === directory) throw new Error(`Missing standalone license: ${name}`);
    directory = parent;
  }
}
await writeFile('../standalone/dist/THIRD_PARTY_NOTICES.txt', notices.join('\n\n--------------------\n\n'));
await mkdir('../build', { recursive: true });
await writeFile('../build/standalone-metafile.json', JSON.stringify(result.metafile, null, 2));
const integrity = { inputs: {}, outputs: {} };
for (const path of [...Object.keys(result.metafile.inputs), 'package.json', 'scripts/build-standalone.mjs', '../plugin.yaml', '../dashboard/manifest.json', '../dashboard/dist/THIRD_PARTY_NOTICES.txt']) integrity.inputs[path] = createHash('sha256').update(await readFile(path)).digest('hex');
for (const path of await readdir('../standalone/dist', { recursive: true })) {
  const full = `../standalone/dist/${path}`;
  try { integrity.outputs[full] = createHash('sha256').update(await readFile(full)).digest('hex'); }
  catch (error) { if (error.code !== 'EISDIR') throw error; }
}
integrity.outputs['../build/standalone-metafile.json'] = createHash('sha256').update(await readFile('../build/standalone-metafile.json')).digest('hex');
await writeFile('../build/standalone-inputs.json', JSON.stringify(integrity, null, 2));
console.log('PASS: independent production entry built; native Dashboard bundle remains separate');
