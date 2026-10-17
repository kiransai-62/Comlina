'use client';

import React from 'react';
import { AlertCircle, Sparkles } from 'lucide-react';

export interface FlowActionButtonsProps {
  isValid?: boolean;
  isSaving?: boolean;
  onSaveDraft: () => void | Promise<void>;
  onPublish: () => void | Promise<void>;
  className?: string;
  publishLabel?: string;
  saveDraftLabel?: string;
  showStatusBadge?: boolean;
}

/**
 * Standardized Flow Action Bar matching the Comlina studio design:
 * [(!) Draft in progress]  [Save Draft]  [✨ Publish Automation]
 */
export function FlowActionButtons({
  isValid = true,
  isSaving = false,
  onSaveDraft,
  onPublish,
  className = '',
  publishLabel = 'Publish Automation',
  saveDraftLabel = 'Save Draft',
  showStatusBadge = true,
}: FlowActionButtonsProps) {
  return (
    <div className={`flex flex-wrap items-center gap-2.5 select-none ${className}`}>
      {/* 1. Status Indicator Pill */}
      {showStatusBadge && (
        <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold bg-[#FEFCE8] text-[#854D0E] border border-[#FEF08A] shadow-2xs">
          <AlertCircle size={14} className="text-[#CA8A04] shrink-0" />
          <span>Draft in progress</span>
        </div>
      )}

      {/* 2. Save Draft Button */}
      <button
        type="button"
        onClick={onSaveDraft}
        disabled={isSaving}
        className="px-4 py-2 border border-[#ECECE8] bg-white hover:bg-[#FBFBFA] active:bg-[#F4F4F0] text-xs font-bold rounded-2xl text-[#111110] transition-colors cursor-pointer shadow-2xs disabled:opacity-50"
      >
        {isSaving ? 'Saving...' : saveDraftLabel}
      </button>

      {/* 3. Publish Automation Button */}
      <button
        type="button"
        onClick={onPublish}
        disabled={isSaving || !isValid}
        className={`inline-flex items-center gap-1.5 px-4.5 py-2 text-xs font-bold rounded-2xl transition-all cursor-pointer shadow-xs ${
          isValid
            ? 'bg-[#064125] hover:bg-[#0A5A34] text-white shadow-sm hover:shadow'
            : 'bg-[#E8E8E3] text-[#70706B] opacity-60 cursor-not-allowed'
        }`}
        title={isValid ? 'Ready to publish' : 'Complete required setup to publish'}
      >
        <Sparkles size={14} className="shrink-0" />
        <span>{isSaving ? 'Publishing...' : publishLabel}</span>
      </button>
    </div>
  );
}

export default FlowActionButtons;
