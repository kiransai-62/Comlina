// client/src/components/automations/ValidationBar.tsx
'use client';

import React from 'react';
import { CheckCircle, AlertCircle, Sparkles } from 'lucide-react';
import { ValidationItem } from './AutomationTypes';

interface ValidationBarProps {
  isValid: boolean;
  items: ValidationItem[];
  onPublishClick: () => void;
  isSaving: boolean;
}

export function ValidationBar({
  isValid,
  items,
  onPublishClick,
  isSaving,
}: ValidationBarProps) {
  const invalidItems = items.filter((i) => i.status === 'invalid');
  const validItems = items.filter((i) => i.status === 'valid');

  return (
    <section className="bg-white border border-[#ECECE8] rounded-2xl p-6 shadow-xs space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-bold text-[#15803D] uppercase tracking-wider">
            <span>Step 8</span>
            <span>•</span>
            <span>Validation & Health Check</span>
          </div>
          <h3 className="text-base font-black text-[#111110] mt-0.5">
            {isValid ? 'Ready to Publish 🎉' : 'Configuration Checklist'}
          </h3>
          <p className="text-xs text-[#70706B]">
            {isValid
              ? 'All required steps are validated. You can launch your Instagram automation now.'
              : `${invalidItems.length} item${invalidItems.length > 1 ? 's' : ''} require your attention before publishing.`}
          </p>
        </div>

        <button
          type="button"
          onClick={onPublishClick}
          disabled={!isValid || isSaving}
          className={`inline-flex items-center justify-center gap-2 px-6 py-3 text-xs font-bold rounded-xl transition-all shadow-sm ${
            isValid && !isSaving
              ? 'bg-[#062E1A] hover:bg-[#0A4A2A] text-white cursor-pointer hover:shadow-md'
              : 'bg-[#E5E5DF] text-[#70706B] cursor-not-allowed'
          }`}
        >
          <Sparkles size={15} />
          <span>{isSaving ? 'Publishing...' : 'Publish Automation'}</span>
        </button>
      </div>

      {/* Validation Items Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-2 border-t border-[#F4F4F0]">
        {items.map((item) => {
          const isOk = item.status === 'valid';
          return (
            <div
              key={item.id}
              className={`flex items-start gap-2 p-2.5 rounded-xl border text-xs transition-colors ${
                isOk
                  ? 'bg-[#F0FDF4]/30 border-[#DCFCE7] text-[#166534]'
                  : 'bg-[#FEFCE8]/40 border-[#FEF08A] text-[#854D0E]'
              }`}
            >
              {isOk ? (
                <CheckCircle size={14} className="text-[#15803D] shrink-0 mt-0.5" />
              ) : (
                <AlertCircle size={14} className="text-[#CA8A04] shrink-0 mt-0.5" />
              )}
              <div className="min-w-0 flex-1">
                <div className="font-semibold leading-tight">{item.label}</div>
                {item.message && !isOk && (
                  <div className="text-xs text-[#A16207] mt-0.5">
                    {item.message}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
