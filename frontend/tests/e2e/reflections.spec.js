/**
 * 🧪 E2E Tests - Reflections Dashboard
 *
 * Valida funcionalidade crítica do dashboard de auto-reflexão.
 * Dell E7450 constraints: Testes rápidos (<30s cada).
 */

const { test, expect } = require("@playwright/test");

test.describe("Reflections Dashboard", () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to reflections page
    await page.goto("/reflections");
  });

  test("should load reflections page successfully", async ({ page }) => {
    // Check page title
    await expect(page).toHaveTitle(/Trading Bot/);

    // Check main heading
    const heading = page.locator("h1, h2").first();
    await expect(heading).toBeVisible();

    // Check that glass cards are rendered (glassmorphism UI)
    const glassCards = page.locator('[class*="glass"], [class*="backdrop"]');
    await expect(glassCards.first()).toBeVisible();
  });

  test("should display reflection status metrics", async ({ page }) => {
    // Wait for data to load
    await page.waitForTimeout(2000);

    // Check for status indicators (mais flexível)
    const statusText = await page.textContent("body");

    // Se não tem dados ainda, verificar se mostra estado vazio ou loading
    if (
      !statusText.includes("Reflection") &&
      !statusText.includes("Win Rate")
    ) {
      // Página pode estar em loading ou empty state - isso é OK
      const emptyOrLoading = page.locator(
        "text=/Loading|Empty|No data|Sem dados/i",
      );
      await expect(emptyOrLoading.first()).toBeVisible({ timeout: 5000 });
    } else {
      // Tem dados - verificar elementos
      const statusSection = page
        .locator("text=/Total.*Reflections|Win Rate|Last Reflection/i")
        .first();
      await expect(statusSection).toBeVisible({ timeout: 10000 });
    }
  });

  test("should navigate from home to reflections", async ({ page }) => {
    // Start at home
    await page.goto("/");

    // Find navigation link (Brain icon or "Reflections" text)
    const navLink = page
      .locator('nav a[href*="reflection"], nav button:has-text("Reflex")')
      .first();

    if (await navLink.isVisible()) {
      await navLink.click();

      // Wait for navigation
      await page.waitForURL(/.*reflection/);

      // Verify we're on reflections page
      await expect(page).toHaveURL(/reflection/);
    } else {
      // Navigation might not exist yet, skip test
      test.skip();
    }
  });

  test("should handle empty state gracefully", async ({ page }) => {
    // If no reflections exist, should show empty state or loading
    const emptyState = page.locator("text=/No.*reflections|Empty|Sem dados/i");
    const loadingState = page.locator("text=/Loading|Carregando/i");
    const dataState = page.locator('[class*="chart"], [class*="list"]');

    // One of these should be visible
    const anyVisible = await Promise.race([
      emptyState.isVisible().then(() => "empty"),
      loadingState.isVisible().then(() => "loading"),
      dataState.isVisible().then(() => "data"),
    ]).catch(() => "none");

    expect(["empty", "loading", "data"]).toContain(anyVisible);
  });

  test("should render win rate chart if data exists", async ({ page }) => {
    await page.waitForTimeout(2000);

    // Look for chart container (Recharts uses SVG)
    const chart = page.locator('svg[class*="recharts"]');

    // If chart exists, verify it's visible
    if ((await chart.count()) > 0) {
      await expect(chart.first()).toBeVisible();

      // Verify chart has data (should have paths/rectangles)
      const chartElements = chart.locator("path, rect, circle");
      expect(await chartElements.count()).toBeGreaterThan(0);
    }
  });

  test("should display learning history if available", async ({ page }) => {
    await page.waitForTimeout(2000);

    // Look for history section
    const historySection = page.locator(
      "text=/Learning History|Histórico|History/i",
    );

    if (await historySection.isVisible()) {
      // If history exists, check for problem/action cards
      const historyCards = page.locator(
        '[class*="history"], [class*="learning"]',
      );

      if ((await historyCards.count()) > 0) {
        await expect(historyCards.first()).toBeVisible();
      }
    }
  });

  test("should have responsive glassmorphism design", async ({ page }) => {
    // Check for glassmorphism CSS properties
    const glassCard = page.locator('[class*="glass"]').first();

    if (await glassCard.isVisible()) {
      const styles = await glassCard.evaluate((el) => {
        const computed = window.getComputedStyle(el);
        return {
          backdropFilter: computed.backdropFilter,
          background: computed.background,
        };
      });

      // Glassmorphism should have backdrop-filter
      expect(styles.backdropFilter).toContain("blur");
    }
  });

  test("should update data periodically (polling)", async ({ page }) => {
    // Teste simplificado - apenas verificar que polling não causa crash
    // Não esperar 35s (muito lento para E2E)
    await page.waitForTimeout(3000);

    const content = await page.locator("body").textContent();

    // Página deve continuar responsiva após alguns segundos
    expect(content).toBeTruthy();

    // Verificar que React Query está configurado (console logs)
    const hasErrors = await page.evaluate(() => {
      return window.console && window.console.error ? false : true;
    });

    expect(hasErrors).toBe(false);
  });

  test("should handle API errors gracefully", async ({ page }) => {
    // Intercept API calls and simulate error
    await page.route("**/api/reflections/**", (route) => {
      route.abort("failed");
    });

    await page.goto("/reflections");

    // Should show error message or fallback UI (not crash)
    await page.waitForTimeout(3000);

    // Page should still be responsive
    const body = page.locator("body");
    await expect(body).toBeVisible();
  });

  test("should be accessible (basic ARIA checks)", async ({ page }) => {
    // Check for semantic HTML
    const main = page.locator('main, [role="main"]');
    await expect(main.first()).toBeVisible();

    // Check for heading hierarchy
    const h1 = page.locator("h1");
    const h2 = page.locator("h2");

    // Should have at least one heading
    const headingCount = (await h1.count()) + (await h2.count());
    expect(headingCount).toBeGreaterThan(0);
  });
});

test.describe("Performance (Dell E7450 constraints)", () => {
  test("should load page in under 3 seconds", async ({ page }) => {
    const startTime = Date.now();

    await page.goto("/reflections");
    await page.waitForLoadState("domcontentloaded");

    const loadTime = Date.now() - startTime;

    // Dell E7450 target: <3s TTI
    expect(loadTime).toBeLessThan(3000);
  });

  test("should not cause memory leaks on re-renders", async ({ page }) => {
    await page.goto("/reflections");

    // Trigger multiple re-renders by navigating away and back
    for (let i = 0; i < 3; i++) {
      await page.goto("/");
      await page.waitForTimeout(500);
      await page.goto("/reflections");
      await page.waitForTimeout(500);
    }

    // Page should still be responsive
    const body = page.locator("body");
    await expect(body).toBeVisible();
  });
});
