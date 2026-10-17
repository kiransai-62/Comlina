// client/src/components/automations/AutomationHeader.tsx
'use client';

import React from 'react';
import Link from 'next/link';
import { ArrowLeft, Sparkles, Eye, CheckCircle, AlertCircle } from 'lucide-react';
import { ConnectedInstagramAccount } from '@/features/instagram/types';

interface AutomationHeaderProps {
  name: string;
  onNameChange: (newName: string) => void;
  accounts: ConnectedInstagramAccount[];
  selectedAccountId: string;
  onAccountChange: (accountId: string) => void;
  isValid: boolean;
  onSaveDraft: () => void;
  onPublishClick: () => void;
  isSaving: boolean;
  onToggleMobilePreview?: () => void;
}

export function AutomationHeader({
  name,
  onNameChange,
  accounts,
  selectedAccountId,
  onAccountChange,
  isValid,
  onSaveDraft,
  onPublishClick,
  isSaving,
  onToggleMobilePreview,
}: AutomationHeaderProps) {
  const activeAccount = accounts.find((a) => a.id === selectedAccountId);

  return (
    <header className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 mb-8 border-b border-[#ECECE8]">
      {/* Left: Back Link & Editable Name */}
      <div className="flex items-center gap-3">
        <Link
          href="/dashboard/automations"
          className="p-2 rounded-xl border border-[#ECECE8] hover:bg-white text-[#70706B] hover:text-[#111110] transition-colors cursor-pointer shrink-0"
          title="Back to Automations"
        >
          <ArrowLeft size={16} />
        </Link>
        <div>
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={name}
              onChange={(e) => onNameChange(e.target.value)}
              className="text-xl sm:text-2xl font-black tracking-tight text-[#111110] bg-transparent border-b border-transparent hover:border-[#ECECE8] focus:border-[#15803D] outline-none max-w-sm sm:max-w-md transition-colors"
              placeholder="Automation Name..."
            />
          </div>
          <div className="flex items-center gap-3 text-xs text-[#70706B] mt-0.5">
            <span>Create Instagram Automation</span>
            {activeAccount && (
              <>
                <span>•</span>
                <span className="font-semibold text-[#15803D]">
                  @{activeAccount.username}
                </span>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Right: Account Selector, Status Pill, Draft, Publish & Mobile Preview */}
      <div className="flex items-center flex-wrap gap-2.5">
        {/* Account Selector (if multiple) */}
        {accounts.length > 1 && (
          <select
            value={selectedAccountId}
            onChange={(e) => onAccountChange(e.target.value)}
            className="text-xs border border-[#ECECE8] rounded-xl px-3 py-2 bg-white text-[#111110] font-medium outline-none focus:border-[#15803D] cursor-pointer shadow-2xs"
          >
            {accounts.map((acc) => (
              <option key={acc.id} value={acc.id}>
                @{acc.username}
              </option>
            ))}
          </select>
        )}

        {/* Readiness Status Indicator */}
        <div className="hidden md:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold bg-[#FEFCE8] text-[#854D0E] border border-[#FEF08A] shadow-2xs">
          <AlertCircle size={14} className="text-[#CA8A04] shrink-0" />
          <span>Draft in progress</span>
        </div>

        {/* Mobile Preview Toggle Button */}
        {onToggleMobilePreview && (
          <button
            type="button"
            onClick={onToggleMobilePreview}
            className="lg:hidden inline-flex items-center gap-1.5 px-3 py-2 border border-[#ECECE8] bg-white hover:bg-[#FBFBFA] text-xs font-semibold rounded-xl text-[#111110] transition-colors cursor-pointer shadow-2xs"
          >
            <Eye size={14} className="text-[#15803D]" />
            <span>Preview</span>
          </button>
        )}

        {/* Save Draft */}
        <button
          type="button"
          onClick={onSaveDraft}
          disabled={isSaving}
          className="px-4 py-2 border border-[#ECECE8] bg-white hover:bg-[#FBFBFA] active:bg-[#F4F4F0] text-xs font-bold rounded-2xl text-[#111110] transition-colors cursor-pointer shadow-2xs disabled:opacity-50"
        >
          {isSaving ? 'Saving...' : 'Save Draft'}
        </button>

        {/* Publish Automation */}
        <button
          type="button"
          onClick={onPublishClick}
          disabled={isSaving}
          className={`inline-flex items-center gap-1.5 px-4.5 py-2 text-xs font-bold rounded-2xl transition-all cursor-pointer shadow-xs ${
            isValid
              ? 'bg-[#E8E8E3] hover:bg-[#062E1A] hover:text-white text-[#52524E]'
              : 'bg-[#E8E8E3] text-[#70706B] opacity-75'
          }`}
          title={isValid ? 'Ready to publish' : 'Complete required fields to publish'}
        >
          <Sparkles size={14} className="shrink-0" />
          <span>{isSaving ? 'Publishing...' : 'Publish Automation'}</span>
        </button>
      </div>
    </header>
  );
}
