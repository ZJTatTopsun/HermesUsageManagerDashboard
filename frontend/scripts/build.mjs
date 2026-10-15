import { build } from 'esbuild';
import { mkdir, writeFile, rename, readFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { dirname, join } from 'node:path';

const require = createRequire(import.meta.url);

const result = await build({
  entryPoints: ['src/entry.tsx'], bundle: true, format: 'iife', platform: 'browser',
  target: 'es2020', jsx: 'transform', jsxFactory: 'React.createElement',
  jsxFragment: 'React.Fragment', outfile: '../dashboard/dist/index.js',
  metafile: true, legalComments: 'external', minify: true,
  loader: { '.ttf': 'file' }, assetNames: 'assets/[name]-[hash]',
  plugins: [{ name: 'reject-react-runtime', setup(builder) {
    builder.onResolve({ filter: /^(react|react-dom)(\/.*)?$/ }, (args) => {
      throw new Error(`Production plugin cannot import ${args.path}; use SDK.React`);
    });
  } }],
});
await rename('../dashboard/dist/index.css', '../dashboard/dist/style.css');
await mkdir('../build', { recursive: true });
await writeFile('../build/plugin-metafile.json', JSON.stringify(result.metafile, null, 2));
const notices = [];
for (const name of ['echarts', 'zrender', 'tslib', 'zod']) {
  let packageRoot = dirname(require.resolve(name, { paths: [dirname(require.resolve('echarts/package.json')), process.cwd()] }));
  let metadata;
  while (true) {
    try { metadata = JSON.parse(await readFile(join(packageRoot, 'package.json'), 'utf8')); }
    catch (error) { if (error.code !== 'ENOENT') throw error; }
    if (metadata?.name === name) break;
    const parent = dirname(packageRoot);
    if (parent === packageRoot) throw new Error(`Cannot find package metadata for ${name}`);
    packageRoot = parent;
  }
  let found = false;
  for (const filename of ['LICENSE', 'LICENSE.txt', 'LICENSE.md', 'CopyrightNotice.txt', 'NOTICE']) {
    try { notices.push(`${name}@${metadata.version} / ${filename}\n\n${await readFile(join(packageRoot, filename), 'utf8')}`); found = true; }
    catch (error) { if (error.code !== 'ENOENT') throw error; }
  }
  if (!found) throw new Error(`Missing license text for ${name}`);
}
notices.push(`Google Material Symbols Outlined / Apache-2.0\n\n${await readFile('src/assets/material-symbols.LICENSE.txt', 'utf8')}`);
await writeFile('../dashboard/dist/THIRD_PARTY_NOTICES.txt', notices.join('\n\n--------------------\n\n'));
await import('./check-bundle.mjs');
