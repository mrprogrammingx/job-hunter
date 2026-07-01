import { chromium } from 'playwright';

const BASE = 'http://localhost:3000';
const EMAIL = `demo.user.${Date.now()}@gmail.com`;
const PASSWORD = 'DemoPass123!';
const NAME = 'Demo User';

const browser = await chromium.launch({ headless: true });
const ctx = await browser.newContext({ viewport: { width: 1400, height: 900 } });
const page = await ctx.newPage();
page.setDefaultTimeout(15000);

const shot = (name) => page.screenshot({ path: `/tmp/${name}.png` });
page.on('pageerror', err => console.log('Page error:', err.message));

// 1. Root → /auth/login
await page.goto(BASE, { waitUntil: 'networkidle' });
if (!page.url().includes('/auth/login')) throw new Error('Expected /auth/login, got ' + page.url());
console.log('✓ Unauthenticated → /auth/login');
await shot('1_login_page');

// 2. Click "Create one" → /auth/signup
await page.click('text=Create one');
await page.waitForLoadState('networkidle');
console.log('✓ On /auth/signup');
await shot('2_signup_page');

// 3. Fill and submit signup
await page.fill('#name', NAME);
await page.fill('#email', EMAIL);
await page.fill('#password', PASSWORD);
await shot('3_signup_filled');

await page.click('button[type="submit"]');
await page.waitForURL((url) => !url.toString().includes('/auth'), { timeout: 15000 });
console.log('✓ Signup → dashboard:', page.url());
await shot('4_dashboard_after_signup');

// 4. Nav shows user name
await page.waitForTimeout(800);
const navText = await page.locator('nav').innerText();
console.log('✓ Nav:', navText.replace(/\s+/g, ' ').trim());

// 5. Sign out
await page.click('text=Sign out');
await page.waitForURL((url) => url.toString().includes('/auth/login'), { timeout: 8000 });
console.log('✓ Signed out → /auth/login');
await shot('5_after_signout');

// 6. Log back in with correct credentials
await page.fill('#email', EMAIL);
await page.fill('#password', PASSWORD);
await page.click('button[type="submit"]');
await page.waitForURL((url) => !url.toString().includes('/auth'), { timeout: 15000 });
console.log('✓ Login succeeded →', page.url());
await shot('6_dashboard_after_login');

// 7. Wrong password shows error
await page.click('text=Sign out');
await page.waitForURL((url) => url.toString().includes('/auth/login'), { timeout: 8000 });
await page.fill('#email', EMAIL);
await page.fill('#password', 'wrongpassword');
await page.click('button[type="submit"]');
await page.waitForSelector('text=Invalid email or password', { timeout: 8000 });
console.log('✓ Wrong password → error shown');
await shot('7_wrong_password');

await browser.close();
console.log('\n✓ All checks passed');
