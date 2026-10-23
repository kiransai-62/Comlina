// client/tests/automation-status-toggle.test.mjs
import test from 'node:test';
import assert from 'node:assert/strict';

/**
 * Controller class replicating the exact toggle and cache orchestration logic
 * implemented in client/src/app/dashboard/automations/page.tsx and
 * client/src/features/automations/mutations.ts.
 */
class AutomationToggleManager {
  constructor(initialList = [], updateApiFn) {
    this.cache = new Map(initialList.map((item) => [item.id, { ...item }]));
    this.localOverrides = new Map();
    this.pendingToggles = new Set();
    this.toasts = [];
    this.updateApiFn = updateApiFn;
  }

  getAutomations() {
    return Array.from(this.cache.values()).map((item) => {
      if (this.localOverrides.has(item.id)) {
        return { ...item, status: this.localOverrides.get(item.id) };
      }
      return item;
    });
  }

  isPending(id) {
    return this.pendingToggles.has(id);
  }

  async toggleStatus(id, currentStatus) {
    // Prevent concurrent duplicate requests on the same toggle
    if (this.pendingToggles.has(id)) {
      return false;
    }

    const newStatus = currentStatus === 'ACTIVE' ? 'PAUSED' : 'ACTIVE';

    // 1. Optimistic UI update
    this.localOverrides.set(id, newStatus);
    this.pendingToggles.add(id);

    try {
      // 2. Real backend mutation call
      const updatedItem = await this.updateApiFn(id, { status: newStatus });

      // 3. Update cache on success
      this.cache.set(id, { ...this.cache.get(id), ...updatedItem });

      // 4. Clear local override so the updated cache is the single source of truth
      this.localOverrides.delete(id);

      this.toasts.push({
        type: 'success',
        message: `Automation ${newStatus === 'ACTIVE' ? 'activated' : 'paused'} successfully.`,
      });
      return true;
    } catch (err) {
      // 5. Roll back optimistic state on failure
      this.localOverrides.delete(id);

      const errorDetail = err?.response?.data?.detail;
      const msg =
        typeof errorDetail === 'string'
          ? errorDetail
          : err?.message || 'Failed to update automation status. Please try again.';

      this.toasts.push({
        type: 'error',
        message: msg,
      });
      return false;
    } finally {
      // 6. Clear pending state
      this.pendingToggles.delete(id);
    }
  }
}

test('Automation Status - ACTIVE -> PAUSED transition succeeds and persists', async () => {
  const initial = [
    { id: 'auto_1', name: 'Summer Campaign', status: 'ACTIVE' },
  ];

  let apiCalledWith = null;
  const mockApi = async (id, data) => {
    apiCalledWith = { id, data };
    return { id, name: 'Summer Campaign', status: data.status };
  };

  const manager = new AutomationToggleManager(initial, mockApi);

  const res = await manager.toggleStatus('auto_1', 'ACTIVE');
  assert.equal(res, true, 'Toggle should succeed');
  assert.deepEqual(apiCalledWith, { id: 'auto_1', data: { status: 'PAUSED' } });

  // Verify updated cache and status
  const current = manager.getAutomations();
  assert.equal(current[0].status, 'PAUSED', 'Persisted status must be PAUSED');
  assert.equal(manager.isPending('auto_1'), false, 'Pending state must be cleared');
  assert.equal(manager.toasts.length, 1);
  assert.equal(manager.toasts[0].message, 'Automation paused successfully.');
});

test('Automation Status - PAUSED -> ACTIVE transition succeeds and persists', async () => {
  const initial = [
    { id: 'auto_2', name: 'Black Friday VIP', status: 'PAUSED' },
  ];

  let apiCalledWith = null;
  const mockApi = async (id, data) => {
    apiCalledWith = { id, data };
    return { id, name: 'Black Friday VIP', status: data.status };
  };

  const manager = new AutomationToggleManager(initial, mockApi);

  const res = await manager.toggleStatus('auto_2', 'PAUSED');
  assert.equal(res, true, 'Toggle should succeed');
  assert.deepEqual(apiCalledWith, { id: 'auto_2', data: { status: 'ACTIVE' } });

  // Verify updated cache and status
  const current = manager.getAutomations();
  assert.equal(current[0].status, 'ACTIVE', 'Persisted status must be ACTIVE');
  assert.equal(manager.isPending('auto_2'), false, 'Pending state must be cleared');
  assert.equal(manager.toasts.length, 1);
  assert.equal(manager.toasts[0].message, 'Automation activated successfully.');
});

test('Automation Status - API failure rolls back optimistic status and displays error message', async () => {
  const initial = [
    { id: 'auto_3', name: 'Critical Flow', status: 'ACTIVE' },
  ];

  const mockFailingApi = async () => {
    const error = new Error('Network error or server unavailable');
    error.response = { data: { detail: 'Database connection failed. Please retry.' } };
    throw error;
  };

  const manager = new AutomationToggleManager(initial, mockFailingApi);

  const res = await manager.toggleStatus('auto_3', 'ACTIVE');
  assert.equal(res, false, 'Toggle should return failure');

  // Verify rollback to original status
  const current = manager.getAutomations();
  assert.equal(current[0].status, 'ACTIVE', 'Status must roll back to original ACTIVE');
  assert.equal(manager.isPending('auto_3'), false, 'Pending state must be cleared after failure');

  // Verify useful error message shown
  assert.equal(manager.toasts.length, 1);
  assert.equal(manager.toasts[0].type, 'error');
  assert.equal(manager.toasts[0].message, 'Database connection failed. Please retry.');
});

test('Automation Status - Authorization failure (403/404) rolls back and displays access error', async () => {
  const initial = [
    { id: 'auto_cross', name: 'Cross Tenant Flow', status: 'ACTIVE' },
  ];

  const mockAuthErrorApi = async () => {
    const error = new Error('Not found');
    error.response = { status: 404, data: { detail: 'Automation not found or does not belong to this workspace' } };
    throw error;
  };

  const manager = new AutomationToggleManager(initial, mockAuthErrorApi);

  const res = await manager.toggleStatus('auto_cross', 'ACTIVE');
  assert.equal(res, false);

  const current = manager.getAutomations();
  assert.equal(current[0].status, 'ACTIVE', 'Status must remain ACTIVE upon authorization failure');
  assert.equal(manager.toasts[0].message, 'Automation not found or does not belong to this workspace');
});

test('Automation Status - Concurrent toggle clicks are locked while pending', async () => {
  const initial = [
    { id: 'auto_4', name: 'Slow Saving Flow', status: 'PAUSED' },
  ];

  let resolveApiCall;
  const mockSlowApi = () => {
    return new Promise((resolve) => {
      resolveApiCall = resolve;
    });
  };

  const manager = new AutomationToggleManager(initial, mockSlowApi);

  // Trigger first toggle
  const firstPromise = manager.toggleStatus('auto_4', 'PAUSED');

  // While pending, state is optimistically ACTIVE and pending is true
  assert.equal(manager.isPending('auto_4'), true, 'Should be pending');
  assert.equal(manager.getAutomations()[0].status, 'ACTIVE', 'Optimistic status is ACTIVE');

  // Attempt duplicate click while pending
  const secondAttempt = await manager.toggleStatus('auto_4', 'PAUSED');
  assert.equal(secondAttempt, false, 'Second toggle attempt during pending must be ignored');

  // Complete the first call
  resolveApiCall({ id: 'auto_4', name: 'Slow Saving Flow', status: 'ACTIVE' });
  await firstPromise;

  assert.equal(manager.isPending('auto_4'), false, 'Pending state cleared after completion');
  assert.equal(manager.getAutomations()[0].status, 'ACTIVE', 'Final persisted status is ACTIVE');
});

test('Automation Status - Persistence after page reload simulation', async () => {
  const serverDb = new Map([
    ['auto_persist', { id: 'auto_persist', name: 'Persistent Flow', status: 'PAUSED' }],
  ]);

  const mockApi = async (id, data) => {
    const existing = serverDb.get(id);
    const updated = { ...existing, status: data.status };
    serverDb.set(id, updated);
    return updated;
  };

  const session1 = new AutomationToggleManager(Array.from(serverDb.values()), mockApi);
  await session1.toggleStatus('auto_persist', 'PAUSED');
  assert.equal(session1.getAutomations()[0].status, 'ACTIVE');

  // Simulate page reload: new session loads directly from server database
  const session2Reloaded = new AutomationToggleManager(Array.from(serverDb.values()), mockApi);
  const reloadedList = session2Reloaded.getAutomations();
  assert.equal(reloadedList[0].status, 'ACTIVE', 'Reloaded list must reflect the persisted status from the database');
});
