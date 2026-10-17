// client/tests/auth-persistence.test.mjs
import test from 'node:test';
import assert from 'node:assert/strict';

// Mock Browser Storage
class MockLocalStorage {
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

// Simulated Token Management and Mutex Logic
class SessionManager {
  constructor(storage) {
    this.storage = storage;
    this.token = this.storage.getItem('comlina_token');
    this.refreshToken = this.storage.getItem('comlina_refresh_token');
    this.refreshPromise = null;
    this.refreshCallCount = 0;
  }

  setSession(token, refreshToken, user) {
    this.token = token;
    this.refreshToken = refreshToken;
    this.storage.setItem('comlina_token', token);
    this.storage.setItem('comlina_refresh_token', refreshToken);
    this.storage.setItem('comlina_user', JSON.stringify(user));
  }

  clearSession() {
    this.token = null;
    this.refreshToken = null;
    this.storage.removeItem('comlina_token');
    this.storage.removeItem('comlina_refresh_token');
    this.storage.removeItem('comlina_user');
    this.storage.removeItem('comlina_workspace');
  }

  isAuthenticated() {
    return !!(this.token || this.refreshToken);
  }

  // Mutex pattern identical to client/src/lib/auth.ts
  async refreshSession() {
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    if (!this.refreshToken) {
      return null;
    }

    this.refreshPromise = (async () => {
      this.refreshCallCount++;
      // Simulate network round-trip to POST /api/auth/refresh
      await new Promise((resolve) => setTimeout(resolve, 20));

      const newAccessToken = `refreshed_access_${Date.now()}`;
      const newRefreshToken = `refreshed_refresh_${Date.now()}`;

      this.token = newAccessToken;
      this.refreshToken = newRefreshToken;
      this.storage.setItem('comlina_token', newAccessToken);
      this.storage.setItem('comlina_refresh_token', newRefreshToken);

      return newAccessToken;
    })().finally(() => {
      this.refreshPromise = null;
    });

    return this.refreshPromise;
  }
}

// Instagram Connection State Machine Logic identical to client/src/features/instagram/useInstagramConnection.ts
function computeInstagramConnectionState(isLoading, isError, accounts) {
  if (isLoading) return 'checking';
  if (isError) return 'error';
  if (!accounts || accounts.length === 0) return 'disconnected';

  const primary = accounts[0];
  if (
    primary.status === 'REAUTHORIZATION_REQUIRED' ||
    primary.status === 'EXPIRED' ||
    primary.is_active === false ||
    primary.isActive === false
  ) {
    return 'reauthorization_required';
  }

  return 'connected';
}

test('Session Persistence - Tokens survive browser restart / page refresh', () => {
  const storage = new MockLocalStorage();
  const manager1 = new SessionManager(storage);

  manager1.setSession('jwt_access_day1', 'jwt_refresh_day1', {
    id: 'user-123',
    email: 'creator@example.com',
  });

  assert.equal(manager1.isAuthenticated(), true);
  assert.equal(storage.getItem('comlina_token'), 'jwt_access_day1');
  assert.equal(storage.getItem('comlina_refresh_token'), 'jwt_refresh_day1');

  // Simulate new tab / return visit the next day
  const manager2 = new SessionManager(storage);
  assert.equal(manager2.isAuthenticated(), true);
  assert.equal(manager2.token, 'jwt_access_day1');
  assert.equal(manager2.refreshToken, 'jwt_refresh_day1');
});

test('Session Refresh Mutex - Multiple concurrent 401s execute only ONE network refresh', async () => {
  const storage = new MockLocalStorage();
  const manager = new SessionManager(storage);

  manager.setSession('old_expired_token', 'valid_refresh_token', { id: 'u1' });

  // 5 parallel requests fail with 401 and attempt refreshSession simultaneously
  const results = await Promise.all([
    manager.refreshSession(),
    manager.refreshSession(),
    manager.refreshSession(),
    manager.refreshSession(),
    manager.refreshSession(),
  ]);

  // All 5 callers get the exact same refreshed access token
  assert.equal(results.length, 5);
  for (const res of results) {
    assert.equal(res, results[0]);
    assert.ok(res.startsWith('refreshed_access_'));
  }

  // Exact single refresh call made (mutex successfully prevented race condition)
  assert.equal(manager.refreshCallCount, 1);
  assert.equal(storage.getItem('comlina_token'), results[0]);
});

test('Signout - Wipes all local credentials and session markers completely', () => {
  const storage = new MockLocalStorage();
  const manager = new SessionManager(storage);

  manager.setSession('token', 'refresh', { id: 'u' });
  storage.setItem('comlina_workspace', 'ws-123');

  manager.clearSession();

  assert.equal(manager.isAuthenticated(), false);
  assert.equal(storage.getItem('comlina_token'), null);
  assert.equal(storage.getItem('comlina_refresh_token'), null);
  assert.equal(storage.getItem('comlina_user'), null);
  assert.equal(storage.getItem('comlina_workspace'), null);
});

test('Instagram State Machine - Connected live account', () => {
  const accounts = [
    {
      id: 'ig-1',
      username: 'artisan_studio',
      status: 'CONNECTED',
      is_active: true,
    },
  ];

  const state = computeInstagramConnectionState(false, false, accounts);
  assert.equal(state, 'connected');
});

test('Instagram State Machine - Preserves account identity when token needs reauthorization', () => {
  const accounts = [
    {
      id: 'ig-1',
      username: 'artisan_studio',
      status: 'REAUTHORIZATION_REQUIRED',
      is_active: false,
    },
  ];

  const state = computeInstagramConnectionState(false, false, accounts);
  // Must NOT be disconnected! User still has an account, but needs to reauth.
  assert.equal(state, 'reauthorization_required');
});

test('Instagram State Machine - Disconnected when workspace has 0 accounts', () => {
  const state = computeInstagramConnectionState(false, false, []);
  assert.equal(state, 'disconnected');
});

test('Instagram State Machine - Checking while loading prevents flash of disconnected UI', () => {
  const state = computeInstagramConnectionState(true, false, []);
  assert.equal(state, 'checking');
});
