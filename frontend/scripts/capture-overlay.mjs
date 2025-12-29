import { spawn } from 'node:child_process';
import { setTimeout as delay } from 'node:timers/promises';
import { chromium } from 'playwright';

const server = spawn('yarn', ['--cwd', 'frontend', 'start'], {
  shell: true,
  stdio: ['ignore', 'pipe', 'pipe'],
  env: {
    ...process.env,
    PORT: '3300',
    BROWSER: 'none',
  },
});

let serverOutput = '';
let serverReady = false;

server.stdout.on('data', (chunk) => {
  const text = chunk.toString();
  serverOutput += text;
  if (!serverReady && text.includes('Compiled successfully')) {
    serverReady = true;
  }
});

server.stderr.on('data', (chunk) => {
  const text = chunk.toString();
  serverOutput += text;
});

server.on('exit', (code) => {
  if (!serverReady) {
    console.error(`Dev server exited with code ${code}`);
  }
});

async function inspect() {
  for (let i = 0; i < 30; i += 1) {
    if (serverReady) break;
    await delay(1000);
  }

  if (!serverReady) {
    console.error('Dev server did not become ready. Output:\n', serverOutput);
    server.kill('SIGINT');
    process.exit(1);
  }

  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  page.on('console', (msg) => {
    console.log('[console]', msg.type(), msg.text());
  });
  page.on('pageerror', (err) => {
    console.log('[pageerror]', err.message);
  });

  await page.goto('http://127.0.0.1:3300/', { waitUntil: 'domcontentloaded' });
  await delay(2000);

  const overlay = await page.$('#webpack-dev-server-client-overlay-div');
  if (overlay) {
    const text = await overlay.innerText();
    console.log('\n[overlay]\n', text);
  } else {
    console.log('No overlay element detected.');
  }

  await browser.close();

  // give CRA time to print shutdown message
  await delay(1000);
  server.kill('SIGINT');
  await delay(1000);
  process.exit(0);
}

inspect().catch(async (error) => {
  console.error('Failed to capture overlay:', error);
  server.kill('SIGINT');
  await delay(1000);
  process.exit(1);
});
