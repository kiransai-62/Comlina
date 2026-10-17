// client/src/features/pwa/storage.ts

const DEFAULT_PREFIX = 'comlina_pwa_';
const KEY_DISMISSED_UNTIL = 'dismissed_until';
const KEY_SESSION_SHOWN = 'session_shown';
const KEY_INSTALLED = 'installed';

function getStorage(type: 'local' | 'session'): Storage | null {
  if (typeof window === 'undefined') return null;
  try {
    const s = type === 'local' ? window.localStorage : window.sessionStorage;
    const testKey = '__pwa_test__';
    s.setItem(testKey, testKey);
    s.removeItem(testKey);
    return s;
  } catch {
    return null;
  }
}

export function isDismissed(cooldownDays = 7, prefix = DEFAULT_PREFIX): boolean {
  const s = getStorage('local');
  if (!s) return false;
  try {
    const raw = s.getItem(`${prefix}${KEY_DISMISSED_UNTIL}`);
    if (!raw) return false;
    const expiry = parseInt(raw, 10);
    if (isNaN(expiry)) return false;
    return Date.now() < expiry;
  } catch {
    return false;
  }
}

export function setDismissed(cooldownDays = 7, prefix = DEFAULT_PREFIX): void {
  const s = getStorage('local');
  if (!s) return;
  try {
    const expiry = Date.now() + cooldownDays * 24 * 60 * 60 * 1000;
    s.setItem(`${prefix}${KEY_DISMISSED_UNTIL}`, expiry.toString());
  } catch {
    // Ignore storage quota or access errors
  }
}

export function isSessionShown(prefix = DEFAULT_PREFIX): boolean {
  const s = getStorage('session');
  if (!s) return false;
  try {
    return s.getItem(`${prefix}${KEY_SESSION_SHOWN}`) === 'true';
  } catch {
    return false;
  }
}

export function setSessionShown(prefix = DEFAULT_PREFIX): void {
  const s = getStorage('session');
  if (!s) return;
  try {
    s.setItem(`${prefix}${KEY_SESSION_SHOWN}`, 'true');
  } catch {
    // Ignore storage quota or access errors
  }
}

export function isInstalledFlag(prefix = DEFAULT_PREFIX): boolean {
  const s = getStorage('local');
  if (!s) return false;
  try {
    return s.getItem(`${prefix}${KEY_INSTALLED}`) === 'true';
  } catch {
    return false;
  }
}

export function setInstalledFlag(prefix = DEFAULT_PREFIX): void {
  const s = getStorage('local');
  if (!s) return;
  try {
    s.setItem(`${prefix}${KEY_INSTALLED}`, 'true');
  } catch {
    // Ignore storage quota or access errors
  }
}

export function resetDismissal(prefix = DEFAULT_PREFIX): void {
  const local = getStorage('local');
  const session = getStorage('session');
  try {
    local?.removeItem(`${prefix}${KEY_DISMISSED_UNTIL}`);
    session?.removeItem(`${prefix}${KEY_SESSION_SHOWN}`);
  } catch {
    // Ignore
  }
}
