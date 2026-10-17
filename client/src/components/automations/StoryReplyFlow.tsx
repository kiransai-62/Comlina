// client/src/components/automations/StoryReplyFlow.tsx
'use client';

import React, { useState } from 'react';
import { 
  ArrowLeft, 
  Sparkles, 
  Save, 
  Plus, 
  Trash2, 
  Globe, 
  Flag,
  Send,
  Upload,
  MessageSquare,
  CheckCircle,
  Edit3,
  X
} from 'lucide-react';
import { FlowActionButtons } from './FlowActionButtons';

interface FollowUpMessage {
  id: string;
  hours: number;
  minutes: number;
  seconds: number;
  message: string;
}

interface StoryReplyFlowProps {
  onBack: () => void;
  onSave: (flowData: any) => Promise<void>;
  accountName?: string;
  isSaving?: boolean;
  onPreviewChange?: (previewData: any) => void;
}

const PRESET_KEYWORDS = ['FREE', 'LINK', 'INFO', 'YES'];

const DETAIL_PILLS = [
  'Phone number',
  'Email address',
  'Address',
  'Name',
  'Website / Link'
];

export function StoryReplyFlow({
  onBack,
  onSave,
  accountName = 'yourbrand',
  isSaving = false,
  onPreviewChange,
}: StoryReplyFlowProps) {
  // 1. Reply to All
  const [replyToAll, setReplyToAll] = useState(false);

  // 2. Trigger Keywords
  const [keywordInput, setKeywordInput] = useState('');
  const [keywords, setKeywords] = useState<string[]>(['FREE', 'LINK']);

  // 3. Trigger Response DM
  const [dmResponseText, setDmResponseText] = useState(
    "Hey! 👋 Here's what you asked for...\nYou can also ask me any questions!"
  );

  // 4. Image Attachments (Optional)
  const [imageAttachments, setImageAttachments] = useState<string[]>([]);

  // 5. Follow-up DMs [PRO+]
  const [followUpEnabled, setFollowUpEnabled] = useState(false);
  const [followUpMessages, setFollowUpMessages] = useState<FollowUpMessage[]>([
    {
      id: 'fup_1',
      hours: 2,
      minutes: 0,
      seconds: 0,
      message: 'Hey! Just checking in — did you get a chance to look at what I sent?',
    },
    {
      id: 'fup_2',
      hours: 12,
      minutes: 0,
      seconds: 0,
      message: 'Hey! Just checking in — did you get a chance to look at what I sent?',
    },
  ]);
  const [aiRewritePrompt, setAiRewritePrompt] = useState(
    'e.g. Write in a warm, casual voice. Keep it under 200 chars. Reference the lead by @username when it feels natural.'
  );
  const [stopKeywords, setStopKeywords] = useState('stop, unsubscribe, cancel, no thanks');
  const [selectedDetails, setSelectedDetails] = useState<string[]>([]);
  const [otherDetails, setOtherDetails] = useState('');

  // Synchronize Live Preview Setup
  React.useEffect(() => {
    onPreviewChange?.({
      keywords: replyToAll ? ['ANY STORY REPLY'] : keywords,
      publicReplyEnabled: false,
      openingDmEnabled: true,
      openingDmText: dmResponseText,
      openingDmButtonText: 'View Link',
      deliveryText: dmResponseText,
      followupEnabled: followUpEnabled && followUpMessages.length > 0,
      followupHours: followUpMessages[0]?.hours || 2,
      followupText: followUpMessages[0]?.message || '',
      defaultTab: 'story',
      isStoryFlow: true,
    });
  }, [
    replyToAll,
    keywords,
    dmResponseText,
    followUpEnabled,
    followUpMessages,
    onPreviewChange,
  ]);

  // Handlers for Keywords
  const handleAddKeyword = (kw: string) => {
    const trimmed = kw.trim().toUpperCase();
    if (trimmed && !keywords.includes(trimmed)) {
      setKeywords([...keywords, trimmed]);
    }
    setKeywordInput('');
  };

  const handleRemoveKeyword = (kw: string) => {
    setKeywords(keywords.filter((k) => k !== kw));
  };

  // Handlers for Follow-up messages
  const handleAddFollowUp = () => {
    setFollowUpMessages([
      ...followUpMessages,
      {
        id: `fup_${Date.now()}`,
        hours: 24,
        minutes: 0,
        seconds: 0,
        message: 'Hey! Let me know if you need any help with this! 🙌',
      },
    ]);
  };

  const handleUpdateFollowUp = (id: string, updates: Partial<FollowUpMessage>) => {
    setFollowUpMessages(
      followUpMessages.map((m) => (m.id === id ? { ...m, ...updates } : m))
    );
  };

  const handleRemoveFollowUp = (id: string) => {
    if (followUpMessages.length > 1) {
      setFollowUpMessages(followUpMessages.filter((m) => m.id !== id));
    }
  };

  // Toggle detail pills
  const toggleDetailPill = (detail: string) => {
    if (selectedDetails.includes(detail)) {
      setSelectedDetails(selectedDetails.filter((d) => d !== detail));
    } else {
      setSelectedDetails([...selectedDetails, detail]);
    }
  };

  // Save Flow
  const handleSaveClick = async (status: 'DRAFT' | 'ACTIVE' = 'ACTIVE') => {
    const payload = {
      type: 'STORY_REPLY',
      name: 'Story Reply Flow',
      status,
      trigger: {
        type: 'STORY',
        replyToAll,
        keywords: replyToAll ? [] : keywords,
      },
      dmResponse: {
        text: dmResponseText,
        attachments: imageAttachments,
      },
      followUp: {
        enabled: followUpEnabled,
        messages: followUpMessages,
        aiRewritePrompt,
        stopKeywords: stopKeywords.split(',').map((s) => s.trim()).filter(Boolean),
        stopDetails: {
          selected: selectedDetails,
          custom: otherDetails,
        },
      },
    };

    await onSave(payload);
  };

  const isFormValid = (replyToAll || keywords.length > 0) && !!dmResponseText.trim();

  return (
    <div className="max-w-2xl mx-auto pb-24 text-[#111110] space-y-6">
      
      {/* 1. TOP HEADER */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-[#ECECE8]">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onBack}
            className="p-1 text-[#70706B] hover:text-[#111110] transition-colors cursor-pointer"
            title="Back to Automation Selection"
          >
            <ArrowLeft size={18} />
          </button>
          <div>
            <h1 className="text-xl sm:text-2xl font-black text-[#111110] tracking-tight">
              Story Reply Flow
            </h1>
            <p className="text-xs text-[#70706B] font-normal">
              Auto-reply in DM when someone replies to your story
            </p>
          </div>
        </div>

        <FlowActionButtons
          isValid={isFormValid}
          isSaving={isSaving}
          onSaveDraft={() => handleSaveClick('DRAFT')}
          onPublish={() => handleSaveClick('ACTIVE')}
        />
      </div>

      {/* 2. CARD 1: Reply to All */}
      <div className="bg-[#F0F6FF] border border-[#BFDBFE] rounded-2xl p-5 sm:p-6 shadow-xs space-y-3">
        <div className="flex items-center gap-2 text-[#0066FF]">
          <Globe size={16} />
          <h2 className="text-sm font-bold text-[#111110]">Reply to All</h2>
        </div>

        <div className="flex items-center justify-between gap-4">
          <div>
            <div className="text-xs font-bold text-[#111110]">Enable Reply to All</div>
            <p className="text-xs text-[#70706B] mt-0.5">
              Respond to ALL story replies without keyword matching
            </p>
          </div>
          <label className="relative inline-flex items-center cursor-pointer shrink-0">
            <input
              type="checkbox"
              checked={replyToAll}
              onChange={(e) => setReplyToAll(e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#0066FF]" />
          </label>
        </div>
      </div>

      {/* 3. CARD 2: Trigger Keywords */}
      <div className="bg-white border border-[#ECECE8] rounded-2xl p-5 sm:p-6 shadow-xs space-y-4">
        <div className="flex items-center gap-2 text-[#0066FF]">
          <Flag size={16} />
          <h2 className="text-sm font-bold text-[#111110]">Trigger Keywords</h2>
        </div>

        <div className="space-y-2">
          <label className="block text-xs font-bold text-[#111110]">
            What keywords should their story reply contain?
          </label>
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={keywordInput}
              onChange={(e) => setKeywordInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  handleAddKeyword(keywordInput);
                }
              }}
              placeholder="Type keyword and press Enter"
              className="flex-1 px-4 py-2.5 bg-white border border-[#ECECE8] rounded-xl text-xs text-[#111110] outline-none focus:border-[#0066FF] placeholder:text-[#9E9E96]"
            />
            <button
              type="button"
              onClick={() => handleAddKeyword(keywordInput)}
              className="px-4 py-2.5 border border-[#ECECE8] rounded-xl text-xs font-bold text-[#111110] hover:bg-[#FBFBFA] transition-colors cursor-pointer"
            >
              Add
            </button>
          </div>

          {/* Active Chips */}
          {keywords.length > 0 && (
            <div className="flex flex-wrap gap-2 pt-1">
              {keywords.map((kw) => (
                <span
                  key={kw}
                  className="inline-flex items-center gap-1.5 px-3 py-1 bg-[#F0F6FF] text-[#0066FF] border border-[#BFDBFE] rounded-lg text-xs font-bold"
                >
                  <span>{kw}</span>
                  <button
                    type="button"
                    onClick={() => handleRemoveKeyword(kw)}
                    className="hover:text-red-500 cursor-pointer"
                  >
                    <X size={12} />
                  </button>
                </span>
              ))}
            </div>
          )}

          {/* Suggested Preset Chips */}
          <div className="flex flex-wrap items-center gap-2 pt-1">
            {PRESET_KEYWORDS.map((preset) => {
              const isSelected = keywords.includes(preset);
              return (
                <button
                  key={preset}
                  type="button"
                  onClick={() => (isSelected ? handleRemoveKeyword(preset) : handleAddKeyword(preset))}
                  className={`px-3 py-1 rounded-lg text-xs font-semibold border transition-colors cursor-pointer ${
                    isSelected
                      ? 'bg-[#EBF5FF] text-[#0066FF] border-[#BFDBFE]'
                      : 'bg-white text-[#70706B] border-[#ECECE8] hover:border-gray-400'
                  }`}
                >
                  + {preset}
                </button>
              );
            })}
          </div>

          <p className="text-[11px] text-[#70706B]">
            Users who reply with any of these keywords will trigger the automation
          </p>
        </div>
      </div>

      {/* 4. CARD 3: Trigger Response DM */}
      <div className="bg-white border border-[#ECECE8] rounded-2xl p-5 sm:p-6 shadow-xs space-y-2">
        <div className="flex items-center gap-2 text-[#0066FF]">
          <Send size={16} />
          <h2 className="text-sm font-bold text-[#111110]">Trigger Response DM</h2>
        </div>

        <div className="relative">
          <textarea
            rows={4}
            value={dmResponseText}
            onChange={(e) => setDmResponseText(e.target.value)}
            className="w-full px-4 py-3 bg-white border border-[#ECECE8] rounded-xl text-xs text-[#111110] leading-relaxed outline-none focus:border-[#0066FF] resize-none pr-8"
          />
          <div className="absolute bottom-3 right-3 text-[#9E9E96] pointer-events-none">
            <Edit3 size={15} />
          </div>
        </div>

        <div className="flex items-center justify-between text-[11px] text-[#70706B] pt-0.5">
          <span>This is the first message users receive when they DM your keyword</span>
          <span>{dmResponseText.length}/1000 characters</span>
        </div>
      </div>

      {/* 5. CARD 4: Image Attachments (Optional) */}
      <div className="bg-white border border-[#ECECE8] rounded-2xl p-5 sm:p-6 shadow-xs space-y-3">
        <div className="flex items-center gap-2 text-[#0066FF]">
          <Upload size={16} />
          <h2 className="text-sm font-bold text-[#111110]">Image Attachments (Optional)</h2>
        </div>
        <p className="text-xs text-[#70706B] -mt-1">
          Attach up to 10 images to send along with your DM
        </p>

        <div className="flex items-center gap-3 pt-1">
          <span className="text-xs font-semibold text-[#70706B]">
            Images ({imageAttachments.length}/10)
          </span>
          <button
            type="button"
            onClick={() => {
              if (imageAttachments.length < 10) {
                setImageAttachments([
                  ...imageAttachments,
                  `https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=400&q=80`,
                ]);
              }
            }}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 border border-[#ECECE8] rounded-xl text-xs font-bold text-[#111110] hover:bg-[#FBFBFA] transition-colors cursor-pointer"
          >
            <Upload size={13} />
            <span>Upload Images</span>
          </button>
        </div>

        {imageAttachments.length > 0 && (
          <div className="flex flex-wrap gap-2 pt-2">
            {imageAttachments.map((img, idx) => (
              <div key={idx} className="relative w-16 h-16 rounded-xl border border-[#ECECE8] overflow-hidden group">
                <img src={img} alt="attachment" className="w-full h-full object-cover" />
                <button
                  type="button"
                  onClick={() => setImageAttachments(imageAttachments.filter((_, i) => i !== idx))}
                  className="absolute top-1 right-1 w-4 h-4 rounded-full bg-red-500 text-white flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <X size={10} />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 6. CARD 5: Follow-up DMs [PRO+] */}
      <div className="bg-white border border-[#ECECE8] rounded-2xl p-5 sm:p-6 shadow-xs space-y-4">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="text-[#0066FF]"><MessageSquare size={16} /></span>
            <h2 className="text-sm font-bold text-[#111110]">Follow-up DMs</h2>
            <span className="px-2 py-0.5 bg-[#0066FF] text-white rounded text-[10px] font-black uppercase tracking-wider">
              PRO+
            </span>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-[#70706B] font-medium">Enabled</span>
            <label className="relative inline-flex items-center cursor-pointer shrink-0">
              <input
                type="checkbox"
                checked={followUpEnabled}
                onChange={(e) => setFollowUpEnabled(e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#0066FF]" />
            </label>
          </div>
        </div>

        {followUpEnabled && (
          <div className="space-y-4 pt-1">
            {/* Informational Blue Banner */}
            <div className="bg-[#EFF6FF] border border-[#BFDBFE] rounded-xl p-3.5 text-xs text-[#1D4ED8] leading-relaxed">
              <p>
                <strong className="font-bold">How it works:</strong> After a lead gets your first DM, Comlina sends these follow-up messages at the delays you set — all inside Instagram's 24-hour messaging window. Any customer reply resets the clock. If the lead replies with any stop keyword, all pending follow-ups are canceled instantly.
              </p>
            </div>

            {/* Follow-up messages list */}
            <div className="space-y-3">
              <h3 className="text-xs font-bold text-[#111110]">Follow-up messages</h3>

              {followUpMessages.map((msg, idx) => (
                <div
                  key={msg.id}
                  className="p-4 bg-white border border-[#ECECE8] rounded-xl flex items-start gap-4"
                >
                  {/* Left Column: Delay Inputs */}
                  <div className="shrink-0 space-y-1">
                    <span className="text-[10px] font-bold text-[#70706B] uppercase">AFTER</span>
                    <div className="flex items-center gap-1.5">
                      <div className="text-center">
                        <input
                          type="number"
                          min="0"
                          value={msg.hours}
                          onChange={(e) => handleUpdateFollowUp(msg.id, { hours: Number(e.target.value) })}
                          className="w-11 h-9 bg-white border border-[#ECECE8] rounded-lg text-xs text-center font-bold text-[#111110]"
                        />
                        <span className="block text-[9px] text-[#70706B] mt-0.5">hrs</span>
                      </div>
                      <div className="text-center">
                        <input
                          type="number"
                          min="0"
                          max="59"
                          value={msg.minutes}
                          onChange={(e) => handleUpdateFollowUp(msg.id, { minutes: Number(e.target.value) })}
                          className="w-11 h-9 bg-white border border-[#ECECE8] rounded-lg text-xs text-center font-bold text-[#111110]"
                        />
                        <span className="block text-[9px] text-[#70706B] mt-0.5">min</span>
                      </div>
                      <div className="text-center">
                        <input
                          type="number"
                          min="0"
                          max="59"
                          value={msg.seconds}
                          onChange={(e) => handleUpdateFollowUp(msg.id, { seconds: Number(e.target.value) })}
                          className="w-11 h-9 bg-white border border-[#ECECE8] rounded-lg text-xs text-center font-bold text-[#111110]"
                        />
                        <span className="block text-[9px] text-[#70706B] mt-0.5">sec</span>
                      </div>
                    </div>
                  </div>

                  {/* Right Column: Message Textarea */}
                  <div className="flex-1 space-y-1">
                    <span className="text-[10px] font-bold text-[#70706B] uppercase">MESSAGE</span>
                    <div className="relative">
                      <textarea
                        rows={2}
                        value={msg.message}
                        onChange={(e) => handleUpdateFollowUp(msg.id, { message: e.target.value })}
                        className="w-full px-3 py-2 bg-white border border-[#ECECE8] rounded-lg text-xs text-[#111110] outline-none focus:border-[#0066FF] resize-none pr-8"
                      />
                      <div className="absolute bottom-2.5 right-2.5 text-[#9E9E96] pointer-events-none">
                        <Edit3 size={14} />
                      </div>
                    </div>
                  </div>

                  {/* Trash Icon */}
                  {followUpMessages.length > 1 && (
                    <button
                      type="button"
                      onClick={() => handleRemoveFollowUp(msg.id)}
                      className="p-1.5 text-[#9E9E96] hover:text-red-500 transition-colors cursor-pointer mt-5"
                    >
                      <Trash2 size={16} />
                    </button>
                  )}
                </div>
              ))}

              <button
                type="button"
                onClick={handleAddFollowUp}
                className="inline-flex items-center gap-1.5 px-3.5 py-1.5 border border-[#ECECE8] bg-white rounded-xl text-xs font-bold text-[#111110] hover:bg-[#FBFBFA] transition-colors cursor-pointer"
              >
                <Plus size={14} />
                <span>Add follow-up</span>
              </button>

              <p className="text-[11px] text-[#70706B]">
                Delay is counted from the time the lead last replied. Any customer reply resets the 24h clock automatically.
              </p>
            </div>

            {/* AI Rewrite Prompt */}
            <div className="space-y-1.5 pt-2 border-t border-[#ECECE8]">
              <label className="block text-xs font-bold text-[#111110]">
                AI rewrite prompt <span className="font-normal text-[#70706B]">(optional)</span>
              </label>
              <div className="relative">
                <textarea
                  rows={2}
                  value={aiRewritePrompt}
                  onChange={(e) => setAiRewritePrompt(e.target.value)}
                  className="w-full px-4 py-2.5 bg-white border border-[#ECECE8] rounded-xl text-xs text-[#111110] outline-none focus:border-[#0066FF] resize-none pr-8"
                />
                <div className="absolute bottom-2.5 right-2.5 text-[#9E9E96] pointer-events-none">
                  <Edit3 size={14} />
                </div>
              </div>

              <div className="flex items-center justify-between gap-4 pt-1">
                <p className="text-[11px] text-[#70706B]">
                  If set, each follow-up is rewritten by AI using your instructions before sending. Leave empty to send messages exactly as written.
                </p>
                <button
                  type="button"
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 border border-[#ECECE8] bg-white rounded-xl text-xs font-semibold text-[#111110] hover:bg-[#FBFBFA] transition-colors shrink-0 cursor-pointer"
                >
                  <Sparkles size={13} className="text-[#0066FF]" />
                  <span>Generate messages with AI</span>
                </button>
              </div>
            </div>

            {/* Stop keyword */}
            <div className="space-y-1.5 pt-2 border-t border-[#ECECE8]">
              <label className="block text-xs font-bold text-[#111110]">
                Stop keywords
              </label>
              <input
                type="text"
                value={stopKeywords}
                onChange={(e) => setStopKeywords(e.target.value)}
                className="w-full px-4 py-2.5 bg-white border border-[#ECECE8] rounded-xl text-xs text-[#111110] outline-none focus:border-[#0066FF]"
              />
              <p className="text-[11px] text-[#70706B]">
                Comma-separated. If a lead replies with any of these words, all pending follow-ups are canceled.
              </p>
            </div>

            {/* Stop when you receive these details */}
            <div className="space-y-2 pt-2 border-t border-[#ECECE8]">
              <div className="flex items-center gap-1.5 text-xs font-bold text-[#111110]">
                <CheckCircle size={14} className="text-emerald-500" />
                <span>Stop when you receive these details:</span>
              </div>

              <div className="flex flex-wrap gap-2">
                {DETAIL_PILLS.map((pill) => {
                  const isChecked = selectedDetails.includes(pill);
                  return (
                    <button
                      key={pill}
                      type="button"
                      onClick={() => toggleDetailPill(pill)}
                      className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors cursor-pointer ${
                        isChecked
                          ? 'bg-[#EFF6FF] text-[#0066FF] border-[#BFDBFE]'
                          : 'bg-white text-[#70706B] border-[#ECECE8] hover:border-gray-400'
                      }`}
                    >
                      {pill}
                    </button>
                  );
                })}
              </div>

              <input
                type="text"
                value={otherDetails}
                onChange={(e) => setOtherDetails(e.target.value)}
                placeholder="Other details to look for (comma-separated, e.g. budget, city)"
                className="w-full px-4 py-2.5 bg-white border border-[#ECECE8] rounded-xl text-xs text-[#111110] outline-none focus:border-[#0066FF] placeholder:text-[#9E9E96]"
              />

              <p className="text-[11px] text-[#70706B] leading-relaxed">
                Leave empty to keep sending every follow-up. If selected, follow-ups keep going until the contact has shared all of these — they can arrive across several messages, and only then are the remaining follow-ups cancelled. AI reads each reply to judge whether the detail was really provided, so replies written in words, oddly formatted, or spread across sentences are still detected.
              </p>
            </div>

          </div>
        )}
      </div>

      {/* 7. BOTTOM ACTION BUTTONS */}
      <div className="pt-4 pb-2 flex items-center justify-end gap-3 border-t border-[#ECECE8]">
        <FlowActionButtons
          isValid={isFormValid}
          isSaving={isSaving}
          onSaveDraft={() => handleSaveClick('DRAFT')}
          onPublish={() => handleSaveClick('ACTIVE')}
        />
      </div>

    </div>
  );
}
