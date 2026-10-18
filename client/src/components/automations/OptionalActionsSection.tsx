// client/src/components/automations/OptionalActionsSection.tsx
'use client';

import React, { useState } from 'react';
import { Plus, X, ShieldCheck, Mail, Tag, AlertCircle, CheckCircle } from 'lucide-react';

interface OptionalActionsSectionProps {
  followerGate: boolean;
  onFollowerGateToggle: (enabled: boolean) => void;
  followerGateMessage: string;
  onFollowerGateMessageChange: (msg: string) => void;
  emailCapture: boolean;
  onEmailCaptureToggle: (enabled: boolean) => void;
  emailCaptureMessage: string;
  onEmailCaptureMessageChange: (msg: string) => void;
  tagContact: boolean;
  onTagContactToggle: (enabled: boolean) => void;
  tagName: string;
  onTagNameChange: (tag: string) => void;
}

export function OptionalActionsSection({
  followerGate,
  onFollowerGateToggle,
  followerGateMessage,
  onFollowerGateMessageChange,
  emailCapture,
  onEmailCaptureToggle,
  emailCaptureMessage,
  onEmailCaptureMessageChange,
  tagContact,
  onTagContactToggle,
  tagName,
  onTagNameChange,
}: OptionalActionsSectionProps) {
  return (
    <section className="bg-white border border-[#ECECE8] rounded-2xl p-6 sm:p-7 shadow-xs space-y-6">
      <div>
        <h2 className="text-xl font-black text-[#111110]">
          Follower Gate &amp; Lead Collection
        </h2>
      </div>

      {/* Visual Workflow Sequence Diagram */}
      <div className="p-3 bg-[#FBFBFA] border border-[#ECECE8] rounded-xl text-xs text-[#70706B] flex flex-wrap items-center justify-between gap-2">
        <span className="font-semibold text-[#111110]">1. Opening DM</span>
        <span>→</span>
        <span className="font-semibold text-[#111110]">User Taps Button</span>
        <span>→</span>
        <span className="px-2 py-0.5 bg-[#EBF5FF] text-[#0066FF] font-bold rounded-md">
          {followerGate || emailCapture ? 'Optional Gate(s) Active' : 'Direct to Resource'}
        </span>
        <span>→</span>
        <span className="font-semibold text-[#15803D]">Resource Delivered</span>
      </div>

      {/* Expandable Action Chips Toolbar */}
      <div className="flex flex-wrap gap-2.5">
        <button
          type="button"
          onClick={() => onFollowerGateToggle(!followerGate)}
          className={`inline-flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
            followerGate
              ? 'bg-[#062E1A] text-white shadow-xs'
              : 'bg-[#FBFBFA] border border-[#ECECE8] text-[#111110] hover:bg-white'
          }`}
        >
          {followerGate ? <X size={13} /> : <Plus size={13} />}
          <span>{followerGate ? 'Remove Follower Gate' : 'Ask them to follow'}</span>
        </button>

        <button
          type="button"
          onClick={() => onEmailCaptureToggle(!emailCapture)}
          className={`inline-flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
            emailCapture
              ? 'bg-[#062E1A] text-white shadow-xs'
              : 'bg-[#FBFBFA] border border-[#ECECE8] text-[#111110] hover:bg-white'
          }`}
        >
          {emailCapture ? <X size={13} /> : <Plus size={13} />}
          <span>{emailCapture ? 'Remove Email Capture' : 'Collect their email'}</span>
        </button>

        <button
          type="button"
          onClick={() => onTagContactToggle(!tagContact)}
          className={`inline-flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
            tagContact
              ? 'bg-[#062E1A] text-white shadow-xs'
              : 'bg-[#FBFBFA] border border-[#ECECE8] text-[#111110] hover:bg-white'
          }`}
        >
          {tagContact ? <X size={13} /> : <Plus size={13} />}
          <span>{tagContact ? 'Remove Contact Tag' : 'Add contact tag'}</span>
        </button>
      </div>

      {/* 1. FOLLOWER GATE CARD (When Enabled) */}
      {followerGate && (
        <div className="p-5 bg-white border-2 border-[#DCFCE7] rounded-2xl space-y-4 animate-in fade-in duration-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-[#F0FDF4] text-[#15803D] flex items-center justify-center">
                <ShieldCheck size={18} />
              </div>
              <div>
                <h3 className="text-xs font-bold text-[#111110]">
                  Follower Gate
                </h3>
                <p className="text-[11px] text-[#70706B]">
                  User must follow your account before resource link is released
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={() => onFollowerGateToggle(false)}
              className="text-[#70706B] hover:text-[#111110] p-1"
            >
              <X size={14} />
            </button>
          </div>

          {/* Capability State Notice */}
          <div className="p-3 bg-[#F0FDF4] border border-[#DCFCE7] rounded-xl flex items-center justify-between text-xs">
            <div className="flex items-center gap-2 text-[#166534]">
              <CheckCircle size={14} className="text-[#15803D] shrink-0" />
              <span>Follower verification capability: <strong>Supported via 4-State Fallback Gate</strong></span>
            </div>
            <span className="text-[10px] font-semibold text-[#15803D] bg-white px-2 py-0.5 rounded-full">Active</span>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#111110] mb-1">
              Follow Request Message
            </label>
            <input
              type="text"
              value={followerGateMessage}
              onChange={(e) => onFollowerGateMessageChange(e.target.value)}
              placeholder="Follow our account to instantly unlock the direct resource! 🙌"
              className="w-full px-3 py-2 bg-white border border-[#ECECE8] rounded-xl text-xs text-[#111110] outline-none focus:border-[#15803D]"
            />
          </div>
        </div>
      )}

      {/* 2. EMAIL CAPTURE CARD (When Enabled) */}
      {emailCapture && (
        <div className="p-5 bg-white border-2 border-[#DCFCE7] rounded-2xl space-y-4 animate-in fade-in duration-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-[#F0FDF4] text-[#15803D] flex items-center justify-center">
                <Mail size={18} />
              </div>
              <div>
                <h3 className="text-xs font-bold text-[#111110]">
                  Email Capture
                </h3>
                <p className="text-[11px] text-[#70706B]">
                  Collect subscriber email address in DM conversation
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={() => onEmailCaptureToggle(false)}
              className="text-[#70706B] hover:text-[#111110] p-1"
            >
              <X size={14} />
            </button>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#111110] mb-1">
              Email Prompt Message
            </label>
            <input
              type="text"
              value={emailCaptureMessage}
              onChange={(e) => onEmailCaptureMessageChange(e.target.value)}
              placeholder="What is the best email address to send your bonus materials to? 📬"
              className="w-full px-3 py-2 bg-white border border-[#ECECE8] rounded-xl text-xs text-[#111110] outline-none focus:border-[#15803D]"
            />
          </div>
        </div>
      )}

      {/* 3. CONTACT TAG CARD (When Enabled) */}
      {tagContact && (
        <div className="p-5 bg-white border-2 border-[#DCFCE7] rounded-2xl space-y-4 animate-in fade-in duration-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-[#F0FDF4] text-[#15803D] flex items-center justify-center">
                <Tag size={18} />
              </div>
              <div>
                <h3 className="text-xs font-bold text-[#111110]">
                  Audience Tagging
                </h3>
                <p className="text-[11px] text-[#70706B]">
                  Tag this user in Comlina CRM when they complete the interaction
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={() => onTagContactToggle(false)}
              className="text-[#70706B] hover:text-[#111110] p-1"
            >
              <X size={14} />
            </button>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#111110] mb-1">
              Tag Name
            </label>
            <input
              type="text"
              value={tagName}
              onChange={(e) => onTagNameChange(e.target.value)}
              placeholder="e.g. lead, guide_download, vip"
              className="w-full max-w-xs px-3 py-2 bg-white border border-[#ECECE8] rounded-xl text-xs font-mono font-semibold text-[#111110] outline-none focus:border-[#15803D]"
            />
          </div>
        </div>
      )}
    </section>
  );
}
