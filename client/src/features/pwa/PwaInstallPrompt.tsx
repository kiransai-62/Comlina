// client/src/features/pwa/PwaInstallPrompt.tsx
'use client';

import React, { useEffect, useRef } from 'react';
import { 
  X, 
  Share2, 
  CheckCircle, 
  Loader2, 
  Download 
} from 'lucide-react';
import { usePwaInstall } from './usePwaInstall';
import { PwaConfig } from './types';
import { BrandLogo } from '@/components/BrandLogo';

function IosShareIcon({ size = 13, className = '' }: { size?: number; className?: string }) {
  return (
    <svg 
      width={size} 
      height={size} 
      viewBox="0 0 24 24" 
      fill="none" 
      stroke="currentColor" 
      strokeWidth="2.5" 
      strokeLinecap="round" 
      strokeLinejoin="round" 
      className={className}
    >
      <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8" />
      <polyline points="16 6 12 2 8 6" />
      <line x1="12" y1="2" x2="12" y2="15" />
    </svg>
  );
}

function IosAddSquareIcon({ size = 13, className = '' }: { size?: number; className?: string }) {
  return (
    <svg 
      width={size} 
      height={size} 
      viewBox="0 0 24 24" 
      fill="none" 
      stroke="currentColor" 
      strokeWidth="2.5" 
      strokeLinecap="round" 
      strokeLinejoin="round" 
      className={className}
    >
      <rect width="18" height="18" x="3" y="3" rx="3" />
      <path d="M8 12h8" />
      <path d="M12 8v8" />
    </svg>
  );
}

export interface PwaInstallPromptProps extends PwaConfig {
  className?: string;
}

export function PwaInstallPrompt(props: PwaInstallPromptProps) {
  const {
    state,
    platform,
    isPromptVisible,
    install,
    dismiss,
    close,
  } = usePwaInstall(props);

  const containerRef = useRef<HTMLDivElement>(null);
  const primaryButtonRef = useRef<HTMLButtonElement>(null);

  // Close on Escape key
  useEffect(() => {
    if (!isPromptVisible) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        dismiss(true);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isPromptVisible, dismiss]);

  // Initial focus management
  useEffect(() => {
    if (isPromptVisible && primaryButtonRef.current) {
      primaryButtonRef.current.focus({ preventScroll: true });
    }
  }, [isPromptVisible]);

  if (!isPromptVisible) {
    return null;
  }

  // ──────────────────────────────────────────
  // INNER POPUP CONTENT BY STATE
  // ──────────────────────────────────────────
  const renderContent = () => {
    // STATE 2: INSTALLATION INITIATED
    if (state === 'INSTALLING') {
      return (
        <div className="flex flex-col items-center justify-center py-6 text-center space-y-4">
          <div className="w-12 h-12 rounded-2xl bg-[#EAF6EE] text-[#064125] flex items-center justify-center animate-pulse">
            <Loader2 size={24} className="animate-spin text-[#064125]" />
          </div>
          <div>
            <h3 className="text-base font-bold text-[#111110]">
              Opening install prompt…
            </h3>
            <p className="text-xs text-[#70706B] mt-1">
              Please follow the on-screen browser prompt to complete installation.
            </p>
          </div>
        </div>
      );
    }

    // STATE 3: INSTALLATION ACCEPTED
    if (state === 'ACCEPTED') {
      return (
        <div className="flex flex-col items-center text-center py-4 space-y-4">
          <div className="w-12 h-12 rounded-2xl bg-[#EAF6EE] text-[#15803D] flex items-center justify-center shadow-2xs">
            <CheckCircle size={26} className="text-[#15803D]" />
          </div>
          <div>
            <h3 className="text-base font-bold text-[#111110]">
              Comlina is ready!
            </h3>
            <p className="text-xs text-[#70706B] mt-1">
              You can now open Comlina directly from your home screen.
            </p>
          </div>
          <button
            ref={primaryButtonRef}
            type="button"
            onClick={close}
            className="w-full py-2.5 px-4 bg-[#064125] hover:bg-[#0A5A34] text-white text-xs font-bold rounded-xl transition-all shadow-xs cursor-pointer focus-visible:ring-2 focus-visible:ring-[#064125] focus-visible:outline-none"
          >
            Done
          </button>
        </div>
      );
    }

    // STATE 5: MANUAL INSTRUCTIONS (iOS Safari or unsupported native prompt)
    if (state === 'MANUAL_INSTRUCTIONS') {
      return (
        <div className="space-y-4">
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-2xl bg-[#FBFBFA] border border-[#ECECE8] p-1.5 flex items-center justify-center shrink-0 shadow-2xs">
                <BrandLogo variant="mark" height={26} />
              </div>
              <div>
                <h3 className="text-sm sm:text-base font-black text-[#111110] tracking-tight">
                  Add Comlina to your home screen
                </h3>
                <p className="text-xs text-[#70706B] font-medium">
                  {platform === 'ios' ? 'Follow these quick steps in Safari:' : 'Manual browser installation:'}
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => dismiss(true)}
              className="p-1.5 rounded-lg text-[#70706B] hover:text-[#111110] hover:bg-[#F4F4F0] transition-colors cursor-pointer"
              aria-label="Close install prompt"
            >
              <X size={18} />
            </button>
          </div>

          <div className="bg-[#FBFBFA] border border-[#ECECE8] rounded-2xl p-4 space-y-3 text-xs text-[#111110]">
            <div className="flex items-center gap-3">
              <div className="w-6 h-6 rounded-lg bg-[#EAF6EE] text-[#064125] font-bold text-xs flex items-center justify-center shrink-0">
                1
              </div>
              <div className="flex items-center gap-1.5 flex-wrap">
                <span>Tap the</span>
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-white border border-[#ECECE8] font-semibold text-[#0066FF]">
                  <IosShareIcon size={13} />
                  <span>Share button</span>
                </span>
                <span>in Safari's toolbar</span>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="w-6 h-6 rounded-lg bg-[#EAF6EE] text-[#064125] font-bold text-xs flex items-center justify-center shrink-0">
                2
              </div>
              <div className="flex items-center gap-1.5 flex-wrap">
                <span>Scroll down and select</span>
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-white border border-[#ECECE8] font-semibold">
                  <IosAddSquareIcon size={13} />
                  <span>Add to Home Screen</span>
                </span>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="w-6 h-6 rounded-lg bg-[#EAF6EE] text-[#064125] font-bold text-xs flex items-center justify-center shrink-0">
                3
              </div>
              <div className="flex items-center gap-1.5 flex-wrap">
                <span>Tap</span>
                <span className="font-bold px-1.5 py-0.5 rounded-md bg-white border border-[#ECECE8]">
                  Add
                </span>
                <span>in the top-right corner</span>
              </div>
            </div>
          </div>

          <button
            ref={primaryButtonRef}
            type="button"
            onClick={close}
            className="w-full py-2.5 px-4 bg-[#064125] hover:bg-[#0A5A34] text-white text-xs font-bold rounded-xl transition-all shadow-xs cursor-pointer focus-visible:ring-2 focus-visible:ring-[#064125] focus-visible:outline-none"
          >
            Got it
          </button>
        </div>
      );
    }

    // STATE 1: DEFAULT PROMPT CONTENT
    return (
      <div className="space-y-4">
        {/* Header Row: Icon + Title + Close Button */}
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-2xl bg-[#FBFBFA] border border-[#ECECE8] p-1.5 flex items-center justify-center shrink-0 shadow-2xs">
              <BrandLogo variant="mark" height={28} />
            </div>
            <div>
              <h3 className="text-sm sm:text-[15px] font-black text-[#111110] tracking-tight">
                Add Comlina to your home screen
              </h3>
              <p className="text-xs text-[#15803D] font-bold">
                Quick access whenever you need it.
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={() => dismiss(true)}
            className="p-1.5 -mr-1 rounded-lg text-[#70706B] hover:text-[#111110] hover:bg-[#F4F4F0] transition-colors cursor-pointer"
            aria-label="Close add to home screen prompt"
          >
            <X size={18} />
          </button>
        </div>

        {/* Description */}
        <p className="text-xs text-[#70706B] leading-relaxed">
          Launch Comlina directly from your home screen for a faster, more convenient experience.
        </p>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row items-center gap-2 pt-1">
          <button
            ref={primaryButtonRef}
            type="button"
            onClick={install}
            className="w-full sm:flex-1 py-2.5 px-4 bg-[#064125] hover:bg-[#0A5A34] active:scale-[0.99] text-white text-xs font-bold rounded-xl transition-all shadow-xs flex items-center justify-center gap-2 cursor-pointer focus-visible:ring-2 focus-visible:ring-[#064125] focus-visible:outline-none"
          >
            <Download size={14} />
            <span>Add to home screen</span>
          </button>

          <button
            type="button"
            onClick={() => dismiss(true)}
            className="w-full sm:w-auto py-2.5 px-4 text-xs font-semibold text-[#70706B] hover:text-[#111110] hover:bg-[#F4F4F0] rounded-xl transition-colors cursor-pointer focus-visible:ring-2 focus-visible:ring-gray-300 focus-visible:outline-none"
          >
            Maybe later
          </button>
        </div>
      </div>
    );
  };

  // ──────────────────────────────────────────
  // RESPONSIVE CONTAINER BY VIEWPORT
  // ──────────────────────────────────────────
  return (
    <>
      {/* ── 1. MOBILE BOTTOM SHEET (< 768px) ── */}
      <div className="md:hidden">
        {/* Soft Backdrop */}
        <div 
          className="fixed inset-0 bg-black/40 backdrop-blur-2xs z-50 animate-in fade-in duration-200"
          onClick={() => dismiss(true)}
        />

        {/* Bottom Sheet Card */}
        <div
          ref={containerRef}
          role="dialog"
          aria-modal="true"
          aria-labelledby="pwa-mobile-title"
          className="fixed inset-x-0 bottom-0 z-50 bg-white rounded-t-3xl border-t border-[#ECECE8] shadow-2xl p-5 pb-[max(env(safe-area-inset-bottom),1.25rem)] animate-in slide-in-from-bottom duration-250 select-none"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Drag Handle Bar */}
          <div className="w-10 h-1 bg-[#ECECE8] rounded-full mx-auto mb-3" />
          <div id="pwa-mobile-title">
            {renderContent()}
          </div>
        </div>
      </div>

      {/* ── 2. TABLET CENTERED MODAL (768px – 1023px) ── */}
      <div className="hidden md:flex lg:hidden fixed inset-0 z-50 items-center justify-center p-4">
        {/* Restrained Backdrop */}
        <div 
          className="fixed inset-0 bg-black/40 backdrop-blur-2xs animate-in fade-in duration-200"
          onClick={() => dismiss(true)}
        />

        {/* Modal Window */}
        <div
          ref={containerRef}
          role="dialog"
          aria-modal="true"
          aria-labelledby="pwa-tablet-title"
          className="relative z-10 max-w-[440px] w-full bg-white rounded-3xl p-6 border border-[#ECECE8] shadow-2xl animate-in zoom-in-95 duration-200 max-h-[90vh] overflow-y-auto select-none"
          onClick={(e) => e.stopPropagation()}
        >
          <div id="pwa-tablet-title">
            {renderContent()}
          </div>
        </div>
      </div>

      {/* ── 3. DESKTOP BOTTOM-RIGHT FLOATING CARD (>= 1024px) ── */}
      <div
        className="hidden lg:block fixed bottom-6 right-6 z-50 select-none animate-in fade-in slide-in-from-bottom-3 duration-250"
        role="region"
        aria-label="Add Comlina to your home screen"
      >
        <div
          ref={containerRef}
          className="w-96 max-w-[calc(100vw-3rem)] bg-white rounded-2xl p-5 border border-[#ECECE8] shadow-xl hover:shadow-2xl transition-shadow"
        >
          {renderContent()}
        </div>
      </div>
    </>
  );
}

export default PwaInstallPrompt;
