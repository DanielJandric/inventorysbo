#!/usr/bin/env node
// Lightweight CLI to render a URL or local HTML file to PDF using Puppeteer

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import puppeteer from 'puppeteer';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function parseArgs(argv) {
  const args = { landscape: true, format: 'A4', margin: '14mm', out: '' };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    const n = argv[i + 1];
    switch (a) {
      case '--url':
        args.url = n; i++; break;
      case '--file':
        args.file = n; i++; break;
      case '--out':
        args.out = n; i++; break;
      case '--landscape':
        args.landscape = n === 'true' || n === '1' || n === 'yes'; i++; break;
      case '--format':
        args.format = n || 'A4'; i++; break;
      case '--margin':
        args.margin = n || '14mm'; i++; break;
      case '--wait-until':
        args.waitUntil = n || 'networkidle0'; i++; break;
      case '--timeout':
        args.timeout = Number(n) || 120000; i++; break;
      case '--scale':
        args.scale = Number(n) || 1; i++; break;
      default:
        // ignore unknown
        break;
    }
  }
  return args;
}

function toFileUrl(p) {
  const abs = path.isAbsolute(p) ? p : path.join(process.cwd(), p);
  const normalized = abs.replace(/\\/g, '/');
  return 'file://' + normalized;
}

async function main() {
  const args = parseArgs(process.argv);
  if (!args.url && !args.file) {
    console.error('Usage: puppeteer_print --url https://... | --file path/to/file.html [--out out.pdf] [--landscape true] [--format A4] [--margin 14mm]');
    process.exit(2);
  }

  const targetUrl = args.url ? args.url : toFileUrl(args.file);

  const browser = await puppeteer.launch({
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
    headless: true
  });
  const page = await browser.newPage();

  const waitUntil = args.waitUntil || 'networkidle0';
  const timeout = typeof args.timeout === 'number' ? args.timeout : 120000;
  await page.goto(targetUrl, { waitUntil, timeout });

  // Ensure background colors are printed and CSS @page is honored
  const pdfBuffer = await page.pdf({
    format: args.format || 'A4',
    landscape: !!args.landscape,
    printBackground: true,
    preferCSSPageSize: true,
    margin: { top: args.margin, right: args.margin, bottom: args.margin, left: args.margin },
    scale: args.scale || 1
  });

  await browser.close();

  if (args.out && args.out !== '-') {
    fs.writeFileSync(args.out, pdfBuffer);
  } else {
    // Write to stdout as binary
    process.stdout.write(pdfBuffer);
  }
}

main().catch((err) => {
  console.error('puppeteer_print error:', err && err.stack ? err.stack : String(err));
  process.exit(1);
});


