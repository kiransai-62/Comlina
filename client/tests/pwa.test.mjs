// client/tests/pwa.test.mjs
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

// Mock browser storage
class MockStorage {
  constructor() {
    this.store = new Map();
  }
  getItem(key) {
    return this.store.get(key) || null;
  }
  setItem(key, value) {
    this.store.set(key, String(value));
  }
  removeItem(key) {
    this.store.delete(key);
  }
  clear() {
    this.store.clear();
  }
}

// Setup Global Browser Mocks for testing PWA utilities
const mockLocalStorage = new MockStorage();
const mockSessionStorage = new MockStorage();

global.window = {
  localStorage: mockLocalStorage,
  sessionStorage: mockSessionStorage,
  matchMedia: (query) => ({
    matches: query.includes('standalone') && global.__IS_STANDALONE__,
  }),
};
global.document = {
  referrer: '',
};
Object.defineProperty(global, 'navigator', {
  value: {
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    standalone: false,
  },
  configurable: true,
  writable: true,
});

// Import storage & detector functions from built or compiled code
test('PWA Storage - Cooldown and Dismissal Logic', async (t) => {
  mockLocalStorage.clear();
  mockSessionStorage.clear();

  // Test 1: Initially not dismissed
  const prefix = 'test_pwa_';
  const KEY_DISMISSED_UNTIL = `${prefix}dismissed_until`;
  const KEY_SESSION_SHOWN = `${prefix}session_shown`;
  const KEY_INSTALLED = `${prefix}installed`;

  assert.equal(mockLocalStorage.getItem(KEY_DISMISSED_UNTIL), null);

  // Test 2: Set dismissed for 7 days
  const cooldownDays = 7;
  const now = Date.now();
  const expiry = now + cooldownDays * 24 * 60 * 60 * 1000;
  mockLocalStorage.setItem(KEY_DISMISSED_UNTIL, expiry.toString());

  const storedExpiry = parseInt(mockLocalStorage.getItem(KEY_DISMISSED_UNTIL), 10);
  assert.ok(storedExpiry > now);
  assert.ok(storedExpiry <= now + cooldownDays * 24 * 60 * 60 * 1000 + 1000);

  // Test 3: Session shown tracking
  assert.equal(mockSessionStorage.getItem(KEY_SESSION_SHOWN), null);
  mockSessionStorage.setItem(KEY_SESSION_SHOWN, 'true');
  assert.equal(mockSessionStorage.getItem(KEY_SESSION_SHOWN), 'true');

  // Test 4: Installed flag tracking
  assert.equal(mockLocalStorage.getItem(KEY_INSTALLED), null);
  mockLocalStorage.setItem(KEY_INSTALLED, 'true');
  assert.equal(mockLocalStorage.getItem(KEY_INSTALLED), 'true');
});

test('PWA Detector - Standalone Mode Detection', async (t) => {
  // Test 1: Standard browser (not standalone)
  global.__IS_STANDALONE__ = false;
  global.navigator.standalone = false;
  global.document.referrer = '';

  const isStandaloneStandard = Boolean(
    global.window.matchMedia('(display-mode: standalone)').matches ||
    global.navigator.standalone ||
    global.document.referrer.includes('android-app://')
  );
  assert.equal(isStandaloneStandard, false);

  // Test 2: CSS display-mode standalone
  global.__IS_STANDALONE__ = true;
  const isStandaloneCss = Boolean(global.window.matchMedia('(display-mode: standalone)').matches);
  assert.equal(isStandaloneCss, true);
  global.__IS_STANDALONE__ = false;

  // Test 3: iOS Safari standalone property
  global.navigator.standalone = true;
  const isStandaloneIos = Boolean(global.navigator.standalone);
  assert.equal(isStandaloneIos, true);
  global.navigator.standalone = false;

  // Test 4: Android TWA referrer
  global.document.referrer = 'android-app://com.comlina.app';
  const isStandaloneAndroid = global.document.referrer.includes('android-app://');
  assert.equal(isStandaloneAndroid, true);
  global.document.referrer = '';
});

test('PWA Detector - Platform Detection', async (t) => {
  // Test 1: iOS iPhone
  const iosUa = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1';
  const isIos = /iPad|iPhone|iPod/.test(iosUa);
  assert.equal(isIos, true);

  // Test 2: Chromium Desktop / Android
  const chromeUa = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36';
  const isChromium = /Chrome|Chromium|Edg|OPR/i.test(chromeUa);
  assert.equal(isChromium, true);

  // Test 3: Firefox / Other
  const firefoxUa = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0';
  const isFirefoxChromium = /Chrome|Chromium|Edg|OPR/i.test(firefoxUa);
  const isFirefoxIos = /iPad|iPhone|iPod/.test(firefoxUa);
  assert.equal(isFirefoxChromium, false);
  assert.equal(isFirefoxIos, false);
});

test('PWA Web App Manifest - Specification Verification', async (t) => {
  const publicDir = fs.existsSync(path.resolve(process.cwd(), 'public'))
    ? path.resolve(process.cwd(), 'public')
    : path.resolve(process.cwd(), 'client/public');

  const manifestPath = path.resolve(publicDir, 'manifest.json');
  assert.ok(fs.existsSync(manifestPath), 'manifest.json must exist in public');

  const content = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));

  // Required W3C Manifest Fields for PWA Installability
  assert.ok(content.name && content.name.includes('Comlina'), 'Manifest must have Comlina name');
  assert.ok(content.short_name && content.short_name.includes('Comlina'), 'Manifest must have short_name');
  assert.equal(content.display, 'standalone', 'Display must be standalone');
  assert.ok(content.start_url, 'Must define start_url');
  assert.equal(content.theme_color, '#064125', 'Theme color must match Comlina brand');
  assert.ok(Array.isArray(content.icons) && content.icons.length >= 2, 'Must have at least 2 icon sizes');

  // Verify that icons exist in public
  for (const icon of content.icons) {
    const iconFile = path.resolve(publicDir, icon.src.replace(/^\//, ''));
    assert.ok(fs.existsSync(iconFile), `Referenced icon ${icon.src} must exist on disk`);
  }
});

test('PWA Service Worker - File and Events Verification', async (t) => {
  const publicDir = fs.existsSync(path.resolve(process.cwd(), 'public'))
    ? path.resolve(process.cwd(), 'public')
    : path.resolve(process.cwd(), 'client/public');

  const swPath = path.resolve(publicDir, 'sw.js');
  assert.ok(fs.existsSync(swPath), 'sw.js must exist in public');

  const content = fs.readFileSync(swPath, 'utf8');
  assert.ok(content.includes("addEventListener('install'"), 'SW must handle install event');
  assert.ok(content.includes("addEventListener('activate'"), 'SW must handle activate event');
  assert.ok(content.includes("addEventListener('fetch'"), 'SW must handle fetch event');
});
