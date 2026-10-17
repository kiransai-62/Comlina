// client/src/features/pwa/usePwaInstall.ts
'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { usePathname } from 'next/navigation';
import {
  BeforeInstallPromptEvent,
  PwaPromptState,
  PwaPlatform,
  PwaConfig,
} from './types';
import {
  isDismissed,
  setDismissed,
  isSessionShown,
  setSessionShown,
  isInstalledFlag,
  setInstalledFlag,
} from './storage';
import { isStandalone, detectPlatform, registerServiceWorker } from './detector';

export function usePwaInstall(config: PwaConfig = {}) {
  const {
    cooldownDays = 7,
    delaySeconds = 30,
    storagePrefix,
    immediate = false,
  } = config;

  const pathname = usePathname();
  const [state, setState] = useState<PwaPromptState>('IDLE');
  const [platform, setPlatform] = useState<PwaPlatform>('other');
  const [canInstall, setCanInstall] = useState(false);

  const deferredPromptRef = useRef<BeforeInstallPromptEvent | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Initialize service worker & platform detection on client mount
  useEffect(() => {
    registerServiceWorker();
    const plat = detectPlatform();
    setPlatform(plat);

    // If app is already standalone, mark state immediately
    if (isStandalone() || isInstalledFlag(storagePrefix)) {
      setState('ALREADY_INSTALLED');
      return;
    }

    // Support debug / QA query parameters (?pwa_prompt=1, ?pwa_state=DEFAULT | MANUAL_INSTRUCTIONS)
    try {
      if (typeof window !== 'undefined') {
        const params = new URLSearchParams(window.location.search);
        if (params.has('pwa_prompt') || params.has('pwa_debug') || params.has('pwa')) {
          const stateParam = params.get('pwa_state') as PwaPromptState;
          setState(stateParam || 'DEFAULT');
        }
      }
    } catch {
      // ignore
    }
  }, [storagePrefix]);

  // Support on-demand trigger via CustomEvent
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const handleManualTrigger = (e: Event) => {
      const customEvent = e as CustomEvent<{ state?: PwaPromptState }>;
      const targetState = customEvent?.detail?.state || 'DEFAULT';
      setState(targetState);
    };

    window.addEventListener('comlina:show-pwa-prompt', handleManualTrigger);
    return () => {
      window.removeEventListener('comlina:show-pwa-prompt', handleManualTrigger);
    };
  }, []);

  // Handle beforeinstallprompt event
  useEffect(() => {
    const handleBeforeInstallPrompt = (e: Event) => {
      e.preventDefault();
      deferredPromptRef.current = e as BeforeInstallPromptEvent;
      setCanInstall(true);
    };

    const handleAppInstalled = () => {
      deferredPromptRef.current = null;
      setCanInstall(false);
      setInstalledFlag(storagePrefix);
      setState('ACCEPTED');
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    window.addEventListener('appinstalled', handleAppInstalled);

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
      window.removeEventListener('appinstalled', handleAppInstalled);
    };
  }, [storagePrefix]);

  // Eligibility verification
  const checkEligibility = useCallback(() => {
    if (typeof window === 'undefined') return false;

    // 1. Not already standalone or recorded as installed
    if (isStandalone() || isInstalledFlag(storagePrefix)) {
      return false;
    }

    // 2. Not in cooldown (7 days)
    if (isDismissed(cooldownDays, storagePrefix)) {
      return false;
    }

    // 3. Not already shown in current session
    if (!immediate && isSessionShown(storagePrefix)) {
      return false;
    }

    // 4. Do not show on auth callbacks or raw data deletion status
    if (pathname && (pathname.startsWith('/auth/callback') || pathname.startsWith('/data-deletion-status'))) {
      return false;
    }

    return true;
  }, [cooldownDays, storagePrefix, immediate, pathname]);

  // Timer scheduling
  useEffect(() => {
    // If already standalone, dismissed, or installing, do not schedule
    if (state === 'ALREADY_INSTALLED' || state === 'DISMISSED' || state === 'ACCEPTED') {
      return;
    }

    if (!checkEligibility()) {
      return;
    }

    const showPrompt = () => {
      if (checkEligibility()) {
        setSessionShown(storagePrefix);
        setState('DEFAULT');
      }
    };

    if (immediate || delaySeconds <= 0) {
      showPrompt();
      return;
    }

    // Start delay timer
    timerRef.current = setTimeout(showPrompt, delaySeconds * 1000);

    // Pause / cancel timer if page becomes hidden or user navigates
    const handleVisibilityChange = () => {
      if (document.hidden && timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [checkEligibility, delaySeconds, immediate, state, storagePrefix]);

  // Action: Trigger Install
  const install = useCallback(async () => {
    const promptEvent = deferredPromptRef.current;

    // 1. Chromium native prompt flow
    if (promptEvent) {
      setState('INSTALLING');
      try {
        await promptEvent.prompt();
        const choice = await promptEvent.userChoice;

        if (choice.outcome === 'accepted') {
          setInstalledFlag(storagePrefix);
          setState('ACCEPTED');
        } else {
          // User cancelled native prompt
          setDismissed(cooldownDays, storagePrefix);
          setState('DISMISSED');
        }
      } catch (err) {
        console.warn('Install prompt error:', err);
        setState('UNAVAILABLE');
      } finally {
        deferredPromptRef.current = null;
        setCanInstall(false);
      }
      return;
    }

    // 2. iOS Safari manual instructions flow
    if (platform === 'ios') {
      setState('MANUAL_INSTRUCTIONS');
      return;
    }

    // 3. Fallback for other browsers
    setState('MANUAL_INSTRUCTIONS');
  }, [cooldownDays, platform, storagePrefix]);

  // Action: Dismiss (Maybe later or close icon)
  const dismiss = useCallback(
    (remember = true) => {
      if (remember) {
        setDismissed(cooldownDays, storagePrefix);
      }
      setSessionShown(storagePrefix);
      setState('DISMISSED');
    },
    [cooldownDays, storagePrefix]
  );

  // Action: Open manual instructions directly
  const showManualInstructions = useCallback(() => {
    setState('MANUAL_INSTRUCTIONS');
  }, []);

  // Action: Close manual instructions or finish success
  const close = useCallback(() => {
    setState('DISMISSED');
  }, []);

  const isPromptVisible = state === 'DEFAULT' || state === 'INSTALLING' || state === 'ACCEPTED' || state === 'MANUAL_INSTRUCTIONS';

  return {
    state,
    platform,
    canInstall,
    isPromptVisible,
    install,
    dismiss,
    close,
    showManualInstructions,
  };
}

export function triggerPwaPrompt(options?: { state?: PwaPromptState }) {
  if (typeof window !== 'undefined') {
    window.dispatchEvent(
      new CustomEvent('comlina:show-pwa-prompt', {
        detail: { state: options?.state || 'DEFAULT' },
      })
    );
  }
}

export default usePwaInstall;
