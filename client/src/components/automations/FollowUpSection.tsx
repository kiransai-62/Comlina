// client/src/components/automations/FollowUpSection.tsx
'use client';

import React from 'react';
import { Clock, CornerDownRight } from 'lucide-react';

interface FollowUpSectionProps {
  enabled: boolean;
  onToggle: (enabled: boolean) => void;
  delayMinutes: number;
  onDelayMinutesChange: (delay: number) => void;
  message: string;
  onMessageChange: (msg: string) => void;
}

const DELAY_OPTIONS = [
  { label: '15 minutes', minutes: 15 },
  { label: '1 hour', minutes: 60 },
  { label: '2 hours', minutes: 120 },
  { label: '6 hours', minutes: 360 },
  { label: '24 hours', minutes: 1440 },
  { label: '48 hours', minutes: 2880 },
];

export function FollowUpSection({
  enabled,
  onToggle,
  delayMinutes,
  onDelayMinutesChange,
  message,
  onMessageChange,
}: FollowUpSectionProps) {
  const activeDelayLabel = DELAY_OPTIONS.find((d) => d.minutes === delayMinutes)?.label || '24 hours';

  return (
    <section className="bg-white border border-[#ECECE8] rounded-2xl p-6 sm:p-7 shadow-xs space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-bold text-[#15803D] uppercase tracking-wider">
            <span>Step 7</span>
            <span>•</span>
            <span>Follow-up</span>
          </div>
          <h2 className="text-xl font-black text-[#111110] mt-1">
            Smart Retargeting Reminder
          </h2>
          <p className="text-xs text-[#70706B] mt-0.5">
            Automatically follow up if the recipient doesn't click your resource link.
          </p>
        </div>

        {/* Toggle */}
        <label className="relative inline-flex items-center cursor-pointer shrink-0 mt-1">
          <input
            type="checkbox"
            checked={enabled}
            onChange={(e) => onToggle(e.target.checked)}
            className="sr-only peer"
          />
          <div className="w-10 h-5 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-[#15803D]" />
        </label>
      </div>

      {enabled && (
        <div className="space-y-4 pt-2 border-t border-[#ECECE8] animate-in fade-in duration-150">
          {/* Visual Workflow Diagram */}
          <div className="p-3.5 bg-[#FBFBFA] border border-[#ECECE8] rounded-xl text-xs space-y-2">
            <div className="font-semibold text-[#111110]">Automated Retargeting Logic:</div>
            <div className="flex flex-col sm:flex-row sm:items-center gap-2 text-[11px] text-[#70706B]">
              <span className="font-medium text-[#111110]">Resource Sent</span>
              <span>→</span>
              <span className="px-2 py-0.5 bg-white border border-[#ECECE8] rounded font-semibold text-[#111110] flex items-center gap-1">
                <Clock size={11} className="text-[#15803D]" />
                Wait {activeDelayLabel}
              </span>
              <span>→</span>
              <span>Link Clicked?</span>
              <div className="flex items-center gap-2 pl-1">
                <span className="text-green-700 font-bold">Yes: Complete</span>
                <span>/</span>
                <span className="text-[#15803D] font-bold">No: Send Follow-up</span>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-semibold text-[#111110] mb-1">
                Wait Time Delay
              </label>
              <select
                value={delayMinutes}
                onChange={(e) => onDelayMinutesChange(Number(e.target.value))}
                className="w-full px-3 py-2 bg-white border border-[#ECECE8] rounded-xl text-xs font-semibold text-[#111110] outline-none focus:border-[#15803D] cursor-pointer"
              >
                {DELAY_OPTIONS.map((d) => (
                  <option key={d.minutes} value={d.minutes}>
                    {d.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="sm:col-span-2">
              <label className="block text-xs font-semibold text-[#111110] mb-1">
                Follow-up Message Copy
              </label>
              <textarea
                rows={2}
                value={message}
                onChange={(e) => onMessageChange(e.target.value)}
                placeholder="Hey! Just wanted to make sure you got the guide? Let me know if you have any questions! 🚀"
                className="w-full px-3.5 py-2 bg-white border border-[#ECECE8] rounded-xl text-xs text-[#111110] leading-relaxed outline-none focus:border-[#15803D]"
              />
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
