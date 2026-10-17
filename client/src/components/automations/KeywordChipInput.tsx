'use client';

import React, { useState, KeyboardEvent } from 'react';
import { X } from 'lucide-react';

interface KeywordChipInputProps {
  keywords: string[];
  onChange: (keywords: string[]) => void;
  placeholder?: string;
  disabled?: boolean;
}

export function KeywordChipInput({
  keywords,
  onChange,
  placeholder = 'Type keyword and press Enter...',
  disabled = false,
}: KeywordChipInputProps) {
  const [inputValue, setInputValue] = useState('');

  const addKeyword = (rawVal: string) => {
    const trimmed = rawVal.trim().toUpperCase();
    if (!trimmed) return;
    
    // Split by commas in case user pasted multiple
    const parts = trimmed
      .split(',')
      .map((p) => p.trim())
      .filter((p) => p.length > 0);

    const updated = [...keywords];
    for (const part of parts) {
      if (!updated.includes(part)) {
        updated.push(part);
      }
    }

    onChange(updated);
    setInputValue('');
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      addKeyword(inputValue);
    } else if (e.key === 'Backspace' && !inputValue && keywords.length > 0) {
      // Remove last keyword on backspace if input is empty
      e.preventDefault();
      onChange(keywords.slice(0, -1));
    }
  };

  const removeKeyword = (indexToRemove: number) => {
    onChange(keywords.filter((_, idx) => idx !== indexToRemove));
  };

  return (
    <div className="w-full space-y-2">
      <div
        className={`min-h-[46px] p-2 bg-white border rounded-xl flex flex-wrap items-center gap-2 transition-all ${
          disabled
            ? 'opacity-60 bg-gray-50 border-[#ECECE8] cursor-not-allowed'
            : 'border-[#ECECE8] focus-within:border-[#15803D] focus-within:ring-2 focus-within:ring-[#15803D]/10'
        }`}
      >
        {keywords.map((kw, idx) => (
          <span
            key={`${kw}-${idx}`}
            className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-[#F0FDF4] border border-[#DCFCE7] text-[#166534] text-xs font-semibold rounded-lg group animate-in fade-in zoom-in-95 duration-150"
          >
            <span className="font-mono tracking-wide">{kw}</span>
            {!disabled && (
              <button
                type="button"
                onClick={() => removeKeyword(idx)}
                className="text-[#166534]/70 hover:text-[#166534] hover:bg-[#DCFCE7] rounded p-0.5 transition-colors cursor-pointer"
                aria-label={`Remove ${kw}`}
              >
                <X size={12} />
              </button>
            )}
          </span>
        ))}

        {!disabled && (
          <div className="flex-1 min-w-[140px] flex items-center">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              onBlur={() => {
                if (inputValue.trim()) {
                  addKeyword(inputValue);
                }
              }}
              placeholder={keywords.length === 0 ? placeholder : 'Add another...'}
              className="w-full text-xs font-medium text-[#111110] placeholder-[#9E9E96] bg-transparent outline-none py-1 px-1"
            />
          </div>
        )}
      </div>

      <div className="flex items-center justify-between text-[11px] text-[#70706B] px-1">
        <span>Press <kbd className="px-1.5 py-0.5 bg-[#F4F4F0] border border-[#ECECE8] rounded text-[10px] font-mono text-[#111110]">Enter</kbd> or use commas to separate multiple keywords</span>
        {keywords.length > 0 && (
          <span>{keywords.length} active keyword{keywords.length > 1 ? 's' : ''}</span>
        )}
      </div>
    </div>
  );
}
