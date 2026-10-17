'use client';

import React, { Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { CheckCircle, ArrowLeft, Shield } from 'lucide-react';
import { BrandLogo } from '@/components/BrandLogo';

function DeletionStatusContent() {
  const searchParams = useSearchParams();
  const code = searchParams.get('code') || 'N/A';

  return (
    <div className="bg-white border border-[#ECECE8] rounded-2xl p-8 max-w-lg w-full shadow-sm text-center space-y-6">
      <div className="w-12 h-12 bg-[#EAF6EE] text-[#15803D] rounded-full flex items-center justify-center mx-auto">
        <CheckCircle size={24} />
      </div>

      <div className="space-y-2">
        <h1 className="text-xl font-bold text-[#111110]">Data Deletion Status</h1>
        <p className="text-sm text-[#70706B] leading-relaxed">
          Your data deletion request was received and completed. Confirmation code: <code className="font-mono font-semibold text-[#111110] bg-[#F4F4F0] px-2 py-0.5 rounded border border-[#ECECE8]">{code}</code>.
        </p>
      </div>

      <div className="p-4 bg-[#FBFBFA] border border-[#ECECE8] rounded-xl text-left text-xs text-[#70706B] space-y-1.5">
        <div className="font-semibold text-[#111110] flex items-center gap-1.5">
          <Shield size={14} className="text-[#15803D]" />
          <span>Meta &amp; Instagram Compliance</span>
        </div>
        <p>
          In accordance with Instagram Platform Terms and GDPR regulations, all stored conversation logs, contact information, and cached profile data associated with this identifier have been permanently purged.
        </p>
      </div>

      <div className="pt-2">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-xs font-semibold text-[#15803D] hover:text-[#0A4A2A] transition-colors"
        >
          <ArrowLeft size={14} />
          <span>Return to Comlina</span>
        </Link>
      </div>
    </div>
  );
}

export default function DataDeletionStatusPage() {
  return (
    <div className="min-h-screen bg-[#FBFBFA] flex flex-col items-center justify-center p-4">
      <div className="mb-6">
        <BrandLogo variant="full" height={32} />
      </div>
      <Suspense fallback={
        <div className="bg-white border border-[#ECECE8] rounded-2xl p-8 max-w-lg w-full shadow-sm text-center">
          <div className="text-xs text-[#70706B]">Loading status...</div>
        </div>
      }>
        <DeletionStatusContent />
      </Suspense>
    </div>
  );
}
