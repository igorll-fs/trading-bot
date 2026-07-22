const { test, expect } = require('@playwright/test');
const AxeBuilder = require('@axe-core/playwright').default;

const routes = ['/', '/settings', '/trades', '/instructions'];

test.describe('Accessibility smoke checks', () => {
  for (const route of routes) {
    test(`has no serious Axe violations on ${route}`, async ({ page }) => {
      await page.goto(route);
      await page.waitForLoadState('networkidle');

      await page
        .evaluate(() => {
          const overlay = document.querySelector('#webpack-dev-server-client-overlay');
          const overlayDiv = document.querySelector('#webpack-dev-server-client-overlay-div');
          if (overlay) overlay.remove();
          if (overlayDiv) overlayDiv.remove();
        })
        .catch(() => {});

      await page
        .waitForSelector('#webpack-dev-server-client-overlay', { state: 'detached', timeout: 2000 })
        .catch(() => {});

      const results = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa'])
        .analyze();

      const seriousViolations = results.violations.filter((violation) =>
        violation.impact === 'serious' || violation.impact === 'critical'
      );

      expect(
        seriousViolations,
        `Serious accessibility issues on ${route}: ${seriousViolations
          .map((violation) => `${violation.id} (${violation.nodes.length})`)
          .join(', ')}`
      ).toEqual([]);
    });
  }
});
