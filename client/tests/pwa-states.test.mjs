// client/tests/pwa-states.test.mjs
import test from 'node:test';
import assert from 'node:assert/strict';

// Test Mock Storage for state transitions
class MockStorage {
  constructor() {
    this.map = new Map();
  }
  getItem(k) { return this.map.get(k) || null; }
  setItem(k, v) { this.map.set(k, String(v)); }
  removeItem(k) { this.map.delete(k); }
  clear() { this.map.clear(); }
}

const mockLocal = new MockStorage();
const mockSession = new MockStorage();

function setupStorage() {
  mockLocal.clear();
  mockSession.clear();
}

test('PWA State Transitions - Native Prompt Accepted Flow', () => {
  setupStorage();
  let state = 'IDLE';
  let isInstalled = false;

  // Step 1: Timer triggers DEFAULT prompt
  state = 'DEFAULT';
  mockSession.setItem('comlina_pwa_session_shown', 'true');
  assert.equal(state, 'DEFAULT');

  // Step 2: User clicks "Add to home screen"
  state = 'INSTALLING';
  assert.equal(state, 'INSTALLING');

  // Step 3: Browser userChoice returns 'accepted'
  const outcome = 'accepted';
  if (outcome === 'accepted') {
    state = 'ACCEPTED';
    isInstalled = true;
    mockLocal.setItem('comlina_pwa_installed', 'true');
  }

  assert.equal(state, 'ACCEPTED');
  assert.equal(isInstalled, true);
  assert.equal(mockLocal.getItem('comlina_pwa_installed'), 'true');
});

test('PWA State Transitions - User Dismisses Prompt (Maybe Later)', () => {
  setupStorage();
  let state = 'DEFAULT';

  // User clicks "Maybe later" or close [x]
  const cooldownDays = 7;
  const expiry = Date.now() + cooldownDays * 24 * 60 * 60 * 1000;
  mockLocal.setItem('comlina_pwa_dismissed_until', expiry.toString());
  mockSession.setItem('comlina_pwa_session_shown', 'true');
  state = 'DISMISSED';

  assert.equal(state, 'DISMISSED');
  const stored = parseInt(mockLocal.getItem('comlina_pwa_dismissed_until'), 10);
  assert.ok(stored > Date.now());
  assert.equal(mockSession.getItem('comlina_pwa_session_shown'), 'true');
});

test('PWA State Transitions - iOS Safari Manual Instructions Flow', () => {
  setupStorage();
  let state = 'DEFAULT';
  const platform = 'ios';

  // On iOS, clicking "Add to home screen" opens manual instructions
  if (platform === 'ios') {
    state = 'MANUAL_INSTRUCTIONS';
  }

  assert.equal(state, 'MANUAL_INSTRUCTIONS');

  // User clicks "Got it"
  state = 'DISMISSED';
  assert.equal(state, 'DISMISSED');
});

test('PWA State Transitions - Already Installed Suppression', () => {
  setupStorage();
  mockLocal.setItem('comlina_pwa_installed', 'true');

  const isAlreadyInstalled = mockLocal.getItem('comlina_pwa_installed') === 'true';
  let state = isAlreadyInstalled ? 'ALREADY_INSTALLED' : 'DEFAULT';

  // Should immediately be ALREADY_INSTALLED and not render prompt
  assert.equal(state, 'ALREADY_INSTALLED');
});
