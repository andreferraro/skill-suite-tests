import { expect, test } from "@playwright/test";


test("operates by keyboard and announces a delayed API error", async ({ page }) => {
  await page.route("**/api/password-reset", async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 250));
    await route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({ message: "Serviço indisponível" }),
    });
  });

  await page.goto("/");
  await page.keyboard.press("Tab");
  await expect(page.getByRole("textbox", { name: "E-mail" })).toBeFocused();
  await page.getByRole("textbox", { name: "E-mail" }).fill("user@example.com");
  await page.keyboard.press("Tab");
  await page.keyboard.press("Enter");
  await expect(page.getByRole("button", { name: "Enviando..." })).toBeDisabled();
  await expect(page.getByRole("alert")).toHaveText("Serviço indisponível");
});
