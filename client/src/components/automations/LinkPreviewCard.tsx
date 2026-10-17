'use client';

import React from 'react';
import { ExternalLink, Globe } from 'lucide-react';

interface LinkPreviewCardProps {
  url: string;
  buttonText: string;
  customTitle?: string;
}

export function LinkPreviewCard({
  url,
  buttonText,
  customTitle,
}: LinkPreviewCardProps) {
  let hostname = 'yourdomain.com';
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
    <div className="w-full bg-[#FBFBFA] border border-[#ECECE8] rounded-xl p-3 space-y-2">
      <div className="flex items-center justify-between text-[11px] font-bold text-[#70706B] uppercase tracking-wider">
        <span>DM Link Attachment Preview</span>
        <span className="flex items-center gap-1 text-[#15803D] lowercase font-normal">
          <Globe size={12} />
          {hostname}
        </span>
      </div>

      <div className="bg-white border border-[#ECECE8] rounded-lg p-2.5 flex items-center justify-between gap-3 shadow-xs">
        <div className="min-w-0">
          <div className="text-xs font-semibold text-[#111110] truncate">
            {customTitle || 'Direct Resource Access Link'}
          </div>
          <div className="text-[11px] text-[#70706B] truncate font-mono mt-0.5">
            {url || 'https://comlina.com/playbook'}
          </div>
        </div>

        <div className="shrink-0 px-3 py-1.5 bg-[#062E1A] text-white text-[11px] font-semibold rounded-lg flex items-center gap-1.5 shadow-xs">
          <span>{buttonText || 'View the resource'}</span>
          <ExternalLink size={12} />
        </div>
      </div>
    </div>
  );
}
