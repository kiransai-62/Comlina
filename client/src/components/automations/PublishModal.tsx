// client/src/components/automations/PublishModal.tsx
'use client';

import React from 'react';
import Link from 'next/link';
import { Check, X, Sparkles, Send, Repeat, ExternalLink, ArrowRight } from 'lucide-react';
import { AutomationDraft } from './AutomationTypes';

interface PublishModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirmPublish: () => void;
  isPublishing: boolean;
  draft: AutomationDraft;
  isSuccess: boolean;
  createdId?: string;
  onResetForAnother: () => void;
}

export function PublishModal({
  isOpen,
  onClose,
  onConfirmPublish,
  isPublishing,
  draft,
  isSuccess,
  createdId,
  onResetForAnother,
}: PublishModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs animate-in fade-in duration-200">
      <div className="w-full max-w-md bg-white border border-[#ECECE8] rounded-3xl p-6 sm:p-7 shadow-2xl relative animate-in zoom-in-95 duration-200">
        
        {/* Close Button */}
        {!isPublishing && (
          <button
            type="button"
            onClick={onClose}
            className="absolute top-5 right-5 p-1.5 rounded-full text-[#70706B] hover:text-[#111110] hover:bg-[#F4F4F0] transition-colors"
          >
            <X size={16} />
          </button>
        )}

        {/* STATE 1: SUCCESS CELEBRATION */}
        {isSuccess ? (
          <div className="text-center space-y-5 py-2">
            <div className="w-14 h-14 bg-[#F0FDF4] border-2 border-[#DCFCE7] text-[#15803D] rounded-full flex items-center justify-center mx-auto shadow-sm animate-in zoom-in-75 duration-300">
              <Check size={28} strokeWidth={3} />
            </div>

            <div>
              <span className="text-xs font-bold text-[#15803D] uppercase tracking-wider">
                Live & Active
              </span>
              <h2 className="text-xl font-black text-[#111110] mt-1">
                Automation Published! 🚀
              </h2>
              <p className="text-xs text-[#70706B] mt-1 max-w-xs mx-auto">
                <strong>{draft.name}</strong> is now monitoring comments and sending automated replies.
              </p>
            </div>

            {/* Quick Action Buttons */}
            <div className="space-y-2 pt-2">
              <Link
                href="/dashboard/automations"
                className="w-full py-2.5 px-4 bg-[#062E1A] hover:bg-[#0A4A2A] text-white font-bold text-xs rounded-xl flex items-center justify-center gap-2 shadow-xs transition-colors"
              >
                <span>View in Automations Dashboard</span>
                <ArrowRight size={14} />
              </Link>

              <button
                type="button"
                onClick={onResetForAnother}
                className="w-full py-2.5 px-4 bg-white border border-[#ECECE8] hover:bg-[#FBFBFA] text-[#111110] font-semibold text-xs rounded-xl transition-colors cursor-pointer"
              >
                Create Another Automation
              </button>
            </div>
          </div>
        ) : (
          /* STATE 2: PRE-PUBLISH CONFIRMATION SUMMARY */
          <div className="space-y-5">
            <div>
              <div className="text-xs font-bold text-[#15803D] uppercase tracking-wider">
                Confirm Activation
              </div>
              <h2 className="text-lg font-black text-[#111110] mt-0.5">
                Publish Automation?
              </h2>
              <p className="text-xs text-[#70706B] mt-0.5">
                Please review the playbook parameters before going live.
              </p>
            </div>

            {/* Summary Box */}
            <div className="bg-[#FBFBFA] border border-[#ECECE8] rounded-2xl p-4 space-y-3 text-xs">
              <div className="flex justify-between border-b border-[#ECECE8] pb-2">
                <span className="text-[#70706B]">Automation Name</span>
                <span className="font-bold text-[#111110] truncate max-w-[200px]">
                  {draft.name}
                </span>
              </div>

              <div className="flex justify-between border-b border-[#ECECE8] pb-2">
                <span className="text-[#70706B]">Trigger</span>
                <span className="font-semibold text-[#111110] capitalize">
                  {draft.trigger.scope} Content ({draft.trigger.type})
                </span>
              </div>

              <div className="flex justify-between border-b border-[#ECECE8] pb-2">
                <span className="text-[#70706B]">Keywords</span>
                <span className="font-mono font-bold text-[#062E1A]">
                  {draft.conditions.matchMode === 'any'
                    ? 'Any comment'
                    : draft.conditions.keywords.join(', ') || 'None'}
                </span>
              </div>

              <div className="space-y-1">
                <span className="text-[#70706B] block">Configured Actions:</span>
                <div className="flex flex-wrap gap-1.5 pt-0.5">
                  {draft.publicReply.enabled && (
                    <span className="px-2 py-0.5 bg-white border border-[#ECECE8] rounded text-[10px] font-semibold">
                      Public Reply
                    </span>
                  )}
                  {draft.privateDm.enabled && (
                    <span className="px-2 py-0.5 bg-white border border-[#ECECE8] rounded text-[10px] font-semibold">
                      Opening DM
                    </span>
                  )}
                  {draft.optionalActions.followerGate && (
                    <span className="px-2 py-0.5 bg-white border border-[#ECECE8] rounded text-[10px] font-semibold">
                      Follower Gate
                    </span>
                  )}
                  {draft.optionalActions.emailCapture && (
                    <span className="px-2 py-0.5 bg-white border border-[#ECECE8] rounded text-[10px] font-semibold">
                      Email Capture
                    </span>
                  )}
                  <span className="px-2 py-0.5 bg-white border border-[#ECECE8] rounded text-[10px] font-semibold text-[#15803D]">
                    Resource Delivery
                  </span>
                  {draft.followUp.enabled && (
                    <span className="px-2 py-0.5 bg-white border border-[#ECECE8] rounded text-[10px] font-semibold">
                      Follow-up Reminder
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Buttons */}
            <div className="flex items-center justify-end gap-2.5 pt-1">
              <button
                type="button"
                onClick={onClose}
                disabled={isPublishing}
                className="px-4 py-2 text-xs font-semibold text-[#70706B] hover:text-[#111110] transition-colors cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={onConfirmPublish}
                disabled={isPublishing}
                className="inline-flex items-center gap-2 px-5 py-2.5 bg-[#062E1A] hover:bg-[#0A4A2A] text-white font-bold text-xs rounded-xl shadow-xs transition-colors cursor-pointer disabled:opacity-50"
              >
                <Sparkles size={14} />
                <span>{isPublishing ? 'Publishing...' : 'Publish'}</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
