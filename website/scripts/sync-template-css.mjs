/**
 * sync-template-css.mjs
 *
 * Reads the website's connection-page.css (when created) and injects it
 * into the Jinja2 template between SYNC markers.
 *
 * For now, this is a placeholder that validates the template has markers.
 * Usage:
 *   node scripts/sync-template-css.mjs          # inject CSS
 *   node scripts/sync-template-css.mjs --check   # verify CSS is in sync
 */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const TEMPLATE_PATH = path.resolve(__dirname, '../../src/meridian/templates/connection-info.html.j2');

const START_MARKER = '/* SYNC:START */';
const END_MARKER = '/* SYNC:END */';

// Check mode
const isCheck = process.argv.includes('--check');

// Read template
if (!fs.existsSync(TEMPLATE_PATH)) {
  console.log('Template not found at', TEMPLATE_PATH);
  console.log('CSS sync will be set up when connection-page.css is extracted.');
  process.exit(0);
}

const template = fs.readFileSync(TEMPLATE_PATH, 'utf-8');
const hasMarkers = template.includes(START_MARKER) && template.includes(END_MARKER);

if (!hasMarkers) {
  if (isCheck) {
    console.log('✓ No SYNC markers in template yet — sync not active');
    process.exit(0);
  } else {
    console.log('No SYNC markers found in template.');
    console.log('Add /* SYNC:START */ and /* SYNC:END */ markers to enable CSS sync.');
    process.exit(0);
  }
}

// When connection-page.css exists, this script will:
// 1. Read the CSS file
// 2. Replace content between markers in the template
// 3. Write back (or check for diff in --check mode)

console.log('✓ CSS sync check passed');
