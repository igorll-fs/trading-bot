import { chromium } from 'playwright';

try {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  page.on('console', (msg) => {
    console.log('[browser console]', msg.type(), msg.text());
  });
  page.on('pageerror', (err) => {
    console.log('[page error]', err.message);
  });
  await page.goto('http://127.0.0.1:3000/', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(2000);
  const overlay = await page.$('#webpack-dev-server-client-overlay-div');
  if (overlay) {
    const text = await overlay.innerText();
    console.log('[overlay]', text);
  } else {
    console.log('Overlay element not found.');
  }
  await browser.close();
} catch (error) {
  console.error('Failed to inspect overlay:', error);
  process.exitCode = 1;
}
