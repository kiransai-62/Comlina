// client/src/components/automations/ConditionsSection.tsx
'use client';

import React from 'react';
import { KeywordChipInput } from './KeywordChipInput';
import { MessageSquare, Sparkles } from 'lucide-react';

interface ConditionsSectionProps {
  matchMode: 'specific' | 'any';
  onMatchModeChange: (mode: 'specific' | 'any') => void;
  keywords: string[];
  onKeywordsChange: (keywords: string[]) => void;
}

export function ConditionsSection({
  matchMode,
  onMatchModeChange,
  keywords,
  onKeywordsChange,
}: ConditionsSectionProps) {
  return (
    <section className="bg-white border border-[#ECECE8] rounded-2xl p-6 sm:p-7 shadow-xs space-y-5">
      <div>
        <h2 className="text-xl font-black text-[#111110]">
          Target Keywords
        </h2>
      </div>

      {/* Match Mode Radios */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {/* Specific Words */}
        <div
          onClick={() => onMatchModeChange('specific')}
          className={`p-4 rounded-xl border text-left cursor-pointer transition-all flex items-start gap-3 ${
            matchMode === 'specific'
              ? 'border-[#15803D] bg-[#F0FDF4]/40 ring-1 ring-[#15803D]/20 shadow-xs'
              : 'border-[#ECECE8] bg-white hover:bg-[#FBFBFA]'
          }`}
        >
          <input
            type="radio"
            name="match_mode"
            checked={matchMode === 'specific'}
            onChange={() => onMatchModeChange('specific')}
            className="mt-0.5 text-[#15803D] focus:ring-0 cursor-pointer"
          />
          <div>
            <div className="font-bold text-xs text-[#111110]">
              Specific words or phrases
            </div>
            <div className="text-[11px] text-[#70706B] mt-0.5">
              Only trigger when the comment contains target keywords
            </div>
          </div>
        </div>

        {/* Any Comment */}
        <div
          onClick={() => onMatchModeChange('any')}
          className={`p-4 rounded-xl border text-left cursor-pointer transition-all flex items-start gap-3 ${
            matchMode === 'any'
              ? 'border-[#15803D] bg-[#F0FDF4]/40 ring-1 ring-[#15803D]/20 shadow-xs'
              : 'border-[#ECECE8] bg-white hover:bg-[#FBFBFA]'
          }`}
        >
          <input
            type="radio"
            name="match_mode"
            checked={matchMode === 'any'}
            onChange={() => onMatchModeChange('any')}
            className="mt-0.5 text-[#15803D] focus:ring-0 cursor-pointer"
          />
          <div>
            <div className="font-bold text-xs text-[#111110]">
              Any comment
            </div>
            <div className="text-[11px] text-[#70706B] mt-0.5">
              Trigger on every single comment received
            </div>
          </div>
        </div>
      </div>

      {/* Keyword Chips Input (if specific) */}
      {matchMode === 'specific' ? (
        <div className="space-y-2 pt-1 animate-in fade-in duration-150">
          <label className="block text-xs font-bold text-[#111110]">
            Target Keywords
          </label>
          <KeywordChipInput
            keywords={keywords}
            onChange={onKeywordsChange}
            placeholder="Type a keyword (e.g. GUIDE, PRICE) and press Enter..."
          />
        </div>
      ) : (
        <div className="p-3 bg-[#FBFBFA] border border-[#ECECE8] rounded-xl text-xs text-[#70706B] flex items-center gap-2">
          <Sparkles size={14} className="text-[#15803D]" />
          <span>Universal trigger active: Every comment will receive your configured response.</span>
        </div>
      )}
    </section>
  );
}
