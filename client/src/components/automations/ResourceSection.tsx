// client/src/components/automations/ResourceSection.tsx
'use client';

import React from 'react';
import { ExternalLink, Globe, FileText } from 'lucide-react';

interface ResourceSectionProps {
  message: string;
  onMessageChange: (msg: string) => void;
  url: string;
  onUrlChange: (url: string) => void;
  buttonText: string;
  onButtonTextChange: (text: string) => void;
  customTitle: string;
  onCustomTitleChange: (title: string) => void;
}

export function ResourceSection({
  message,
  onMessageChange,
  url,
  onUrlChange,
  buttonText,
  onButtonTextChange,
  customTitle,
  onCustomTitleChange,
}: ResourceSectionProps) {
  let hostname = 'comlina.com';
  try {
    if (url && (url.startsWith('http://') || url.startsWith('https://'))) {
      hostname = new URL(url).hostname;
    } else if (url) {
      hostname = url.split('/')[0];
    }
  } catch {
    hostname = 'yourdomain.com';
  }

  return (
    <section className="bg-white border border-[#ECECE8] rounded-2xl p-6 sm:p-7 shadow-xs space-y-6">
      <div>
        <div className="flex items-center gap-2 text-xs font-bold text-[#15803D] uppercase tracking-wider">
          <span>Step 6</span>
          <span>•</span>
          <span>Resource / Link</span>
        </div>
        <h2 className="text-xl font-black text-[#111110] mt-1">
          What should they receive?
        </h2>
        <p className="text-xs text-[#70706B] mt-0.5">
          Configure the final deliverable message and destination link.
        </p>
      </div>

      <div className="space-y-4">
        {/* Message */}
        <div>
          <label className="block text-xs font-semibold text-[#111110] mb-1">
            Delivery DM Message
          </label>
          <textarea
            rows={2}
            value={message}
            onChange={(e) => onMessageChange(e.target.value)}
            placeholder="Here is the direct guide you requested! 🚀 Click below:"
            className="w-full px-3.5 py-2.5 bg-white border border-[#ECECE8] rounded-xl text-xs text-[#111110] leading-relaxed outline-none focus:border-[#15803D]"
          />
        </div>

        {/* Link URL & Button Text */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-semibold text-[#111110] mb-1">
              Destination URL
            </label>
            <input
              type="text"
              value={url}
              onChange={(e) => onUrlChange(e.target.value)}
              placeholder="https://comlina.com/playbook"
              className="w-full px-3.5 py-2.5 bg-white border border-[#ECECE8] rounded-xl text-xs font-mono text-[#111110] outline-none focus:border-[#15803D]"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#111110] mb-1">
              Button Text
            </label>
            <input
              type="text"
              value={buttonText}
              onChange={(e) => onButtonTextChange(e.target.value)}
              placeholder="View the guide"
              className="w-full px-3.5 py-2.5 bg-white border border-[#ECECE8] rounded-xl text-xs font-semibold text-[#111110] outline-none focus:border-[#15803D]"
            />
          </div>
        </div>

        {/* Resource Preview Card */}
        <div className="pt-2">
          <label className="block text-[11px] font-bold text-[#70706B] uppercase tracking-wider mb-2">
            Resource Preview
          </label>
          <div className="bg-[#FBFBFA] border border-[#ECECE8] rounded-xl p-3.5 space-y-2">
            <div className="flex items-center justify-between text-[11px] font-semibold text-[#70706B]">
              <span className="flex items-center gap-1.5">
                <FileText size={14} className="text-[#15803D]" />
                <span>Deliverable Card</span>
              </span>
              <span className="flex items-center gap-1 text-[#15803D] lowercase font-normal">
                <Globe size={12} />
                {hostname}
              </span>
            </div>

            <div className="bg-white border border-[#ECECE8] rounded-lg p-3 flex items-center justify-between gap-3 shadow-2xs">
              <div className="min-w-0">
                <div className="text-xs font-bold text-[#111110] truncate">
                  {customTitle || 'Comlina Direct Resource'}
                </div>
                <div className="text-[11px] text-[#70706B] truncate font-mono mt-0.5">
                  {url || 'https://comlina.com/playbook'}
                </div>
              </div>

              <div className="shrink-0 px-3 py-1.5 bg-[#062E1A] text-white text-[11px] font-semibold rounded-lg flex items-center gap-1.5 shadow-xs">
                <span>{buttonText || 'View the guide'}</span>
                <ExternalLink size={12} />
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
