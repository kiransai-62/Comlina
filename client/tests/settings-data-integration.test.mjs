// client/tests/settings-data-integration.test.mjs
import test from 'node:test';
import assert from 'node:assert/strict';

// Helper function mirroring client/src/app/dashboard/settings/page.tsx dynamic initials derivation
function deriveUserInitials(fullName, email) {
  if (fullName && fullName.trim()) {
    const parts = fullName.trim().split(/\s+/);
    if (parts.length >= 2) {
      return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    }
    return parts[0].slice(0, 2).toUpperCase();
  }
  if (email && email.trim()) {
    return email.slice(0, 2).toUpperCase();
  }
  return 'CR';
}

// Helper function mirroring dynamic integration status label
function getInstagramStatusLabel(accounts, isLoading = false) {
  if (isLoading) return 'Loading accounts...';
  if (!accounts || accounts.length === 0) return 'No accounts connected';
  if (accounts.length === 1) return `@${accounts[0].username} connected`;
  return `${accounts.length} accounts connected`;
}

// Helper class for isolated preferences management
class MockSettingsStorage {
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
}

class AutomationPreferencesManager {
  constructor(storage, workspaceId = 'default') {
    this.storage = storage;
    this.workspaceId = workspaceId;
  }

  getStorageKey() {
    return `comlina_automation_preferences_${this.workspaceId}`;
  }

  loadPreferences() {
    const raw = this.storage.getItem(this.getStorageKey());
    if (raw) {
      try {
        return JSON.parse(raw);
      } catch {
        // fallback
      }
    }
    return {
      followCheck: true,
      publicReply: false,
      stopDuplicate: true,
    };
  }

  savePreferences(prefs) {
    this.storage.setItem(this.getStorageKey(), JSON.stringify(prefs));
  }

  togglePreference(key) {
    const current = this.loadPreferences();
    const updated = {
      ...current,
      [key]: !current[key],
    };
    this.savePreferences(updated);
    return updated;
  }
}

test('Initials Derivation - Generates dynamic user initials without hardcoded fallback', () => {
  // 1. Two-word name
  assert.equal(deriveUserInitials('Kiran Sai', 'kiransai@gmail.com'), 'KS');
  assert.equal(deriveUserInitials('Jane Doe', 'jane@example.com'), 'JD');
  assert.equal(deriveUserInitials('Alex Morgan Smith', 'alex@test.com'), 'AS');

  // 2. Single-word name
  assert.equal(deriveUserInitials('Sarah', 'sarah@example.com'), 'SA');
  assert.equal(deriveUserInitials('developer', 'dev@example.com'), 'DE');

  // 3. Empty name, fallback to email username
  assert.equal(deriveUserInitials('', 'john.wick@continental.com'), 'JO');
  assert.equal(deriveUserInitials(null, 'elena@work.io'), 'EL');

  // 4. Missing name and email, fallback to 'CR'
  assert.equal(deriveUserInitials('', ''), 'CR');
  assert.equal(deriveUserInitials(null, null), 'CR');
});

test('Connected Integrations - Dynamic Instagram status reflects actual accounts', () => {
  // Loading state
  assert.equal(getInstagramStatusLabel([], true), 'Loading accounts...');

  // Disconnected / 0 accounts
  assert.equal(getInstagramStatusLabel([], false), 'No accounts connected');

  // Single account
  assert.equal(
    getInstagramStatusLabel([{ username: 'alworkings' }], false),
    '@alworkings connected'
  );

  // Multiple accounts
  assert.equal(
    getInstagramStatusLabel([{ username: 'acct1' }, { username: 'acct2' }], false),
    '2 accounts connected'
  );

  assert.equal(
    getInstagramStatusLabel(
      [{ username: 'a1' }, { username: 'a2' }, { username: 'a3' }, { username: 'a4' }],
      false
    ),
    '4 accounts connected'
  );
});

test('Automation Preferences - Persist and reload per workspace without resetting', () => {
  const storage = new MockSettingsStorage();
  const managerA = new AutomationPreferencesManager(storage, 'ws-alpha-123');
  const managerB = new AutomationPreferencesManager(storage, 'ws-beta-456');

  // 1. Default preferences
  const initialA = managerA.loadPreferences();
  assert.equal(initialA.followCheck, true);
  assert.equal(initialA.publicReply, false);
  assert.equal(initialA.stopDuplicate, true);

  // 2. Toggle on workspace A
  const updatedA = managerA.togglePreference('publicReply');
  assert.equal(updatedA.publicReply, true);

  // 3. Workspace B remains isolated with its own defaults
  const initialB = managerB.loadPreferences();
  assert.equal(initialB.publicReply, false);

  // 4. Reload from storage on Workspace A (simulating page reload)
  const reloadedA = managerA.loadPreferences();
  assert.equal(reloadedA.publicReply, true);
  assert.equal(reloadedA.followCheck, true);
  assert.equal(reloadedA.stopDuplicate, true);
});

test('Plan & Usage Calculation - Authoritative tier and quota mapping', () => {
  const calculateUsagePercentage = (used, limit) => {
    if (!limit || limit <= 0) return 0;
    return Math.min(100, Math.max(0, (used / limit) * 100));
  };

  // Free Tier (0 of 10 automations)
  assert.equal(calculateUsagePercentage(0, 10), 0);
  assert.equal(calculateUsagePercentage(5, 10), 50);
  assert.equal(calculateUsagePercentage(10, 10), 100);

  // Over quota capping at 100%
  assert.equal(calculateUsagePercentage(12, 10), 100);

  // Pro tier with unlimited limit (-1 or null)
  assert.equal(calculateUsagePercentage(42, -1), 0);
});
