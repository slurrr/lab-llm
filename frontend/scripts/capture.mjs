import { chromium } from "playwright";
import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";

const url = process.argv[2] ?? "http://127.0.0.1:8001/";
const output = process.argv[3] ?? path.resolve("artifacts", "latest.png");

await fs.mkdir(path.dirname(output), { recursive: true });
try {
  const stamp = new Date().toISOString().replaceAll(":", "-").replaceAll(".", "-");
  const previous = path.join(path.dirname(output), `history-${stamp}.png`);
  await fs.copyFile(output, previous);
} catch (error) {
  // Ignore missing-file errors on first capture.
}

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1600, height: 1200 } });
await page.goto(url, { waitUntil: "domcontentloaded" });
await page.waitForTimeout(1500);
await page.screenshot({ path: output, fullPage: true });
await browser.close();

console.log(output);
