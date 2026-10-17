// client/src/features/pwa/detector.ts
import { PwaPlatform } from './types';

export function isStandalone(): boolean {
  if (typeof window === 'undefined') return false;

  // 1. Standard W3C display-mode media query
  try {
    if (window.matchMedia && window.matchMedia('(display-mode: standalone)').matches) {
      return true;
    }
  } catch {
    // Media query parsing failed or unsupported
  }

  // 2. iOS Safari standalone boolean
  if (typeof navigator !== 'undefined' && (navigator as any).standalone === true) {
    return true;
  }

  // 3. Android TWA (Trusted Web Activity) referrer
  if (typeof document !== 'undefined' && document.referrer && document.referrer.includes('android-app://')) {
    return true;
  }

  return false;
}

export function detectPlatform(): PwaPlatform {
  if (typeof navigator === 'undefined') return 'other';

  const ua = navigator.userAgent || '';

  // iOS detection: iPhone, iPad, iPod
  const isIos = /iPad|iPhone|iPod/.test(ua) && !(typeof window !== 'undefined' && (window as any).MSStream);
  if (isIos) {
    return 'ios';
  }

  // Chromium / Chrome / Edge / Opera / Brave on Android or Desktop
  const isChromium = /Chrome|Chromium|Edg|OPR/i.test(ua);
  if (isChromium) {
    return 'chromium';
  }

  return 'other';
}

export function registerServiceWorker(): void {
  if (typeof window === 'undefined' || !('serviceWorker' in navigator)) {
    return;
  }

  // Register sw on window load to avoid blocking critical page rendering
  const handleLoad = () => {
    navigator.serviceWorker
      .register('/sw.js')
      .then((registration) => {
        // SW successfully registered
      })
      .catch((error) => {
        console.warn('Comlina PWA Service Worker registration skipped or failed:', error);
      });
  };

  if (document.readyState === 'complete') {
    handleLoad();
  } else {
    window.addEventListener('load', handleLoad, { once: true });
  }
}
